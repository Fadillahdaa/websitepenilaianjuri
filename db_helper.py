import os
import json
import time
from datetime import datetime

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

# ID Google Spreadsheet
SPREADSHEET_ID = "1RsQ4RLGVcqghM3LlFVDTu1OIuYokwC6if_CpWrPUrPk"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Nama sheet (SEMUA HURUF KECIL) -> header kolom
SCHEMA = {
    "instansi": ["id_instansi", "nama_instansi", "jenis_instansi"],
    "juri": ["id_juri", "nama_juri", "id_instansi"],
    "peserta": ["id_peserta", "nama_peserta", "status"],
    "penilaian": ["id", "id_juri", "id_instansi", "id_peserta",
                  "k1", "k2", "k3", "k4", "waktu_input", "catatan"],
    "favorit": ["waktu_input", "id_juri", "id_instansi", "id_peserta"],
}
SESSION_KEYS = {
    "instansi": "db_instansi",
    "juri": "db_juri",
    "peserta": "db_peserta",
    "penilaian": "db_penilaian",
    "favorit": "db_favorit",
}

SYNC_TTL_DETIK = 15  # jarak minimal antar sync otomatis (hindari rate limit Google)


# ============================ HELPER DATA INSTANSI ============================
def ensure_instansi_cols(df):
    """Pastikan df instansi punya kolom lengkap (aman untuk data lama)."""
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame(columns=SCHEMA["instansi"])
    df = df.copy()
    for col in SCHEMA["instansi"]:
        if col not in df.columns:
            df[col] = ""
    return df


# ============================ HELPER ID ============================
def next_id(df, prefix, col):
    """Buat ID berikutnya, contoh: PST-001, INS-002, JUR-003."""
    nums = []
    if df is not None and not df.empty and col in df.columns:
        for v in df[col].tolist():
            v = str(v)
            if v.startswith(prefix + "-") and v.split("-")[-1].isdigit():
                nums.append(int(v.split("-")[-1]))
    return f"{prefix}-{(max(nums) if nums else 0) + 1:03d}"


# ============================ KONEKSI ============================
def _load_credentials_dict():
    """Ambil kredensial dari credentials.json (lokal) atau st.secrets (deploy)."""
    base = os.path.dirname(os.path.abspath(__file__))
    for path in ["credentials.json", "credential.json",
                 os.path.join(base, "credentials.json"),
                 os.path.join(base, "credential.json")]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f), None

    try:
        if "gcp_service_account" in st.secrets:
            return dict(st.secrets["gcp_service_account"]), None
    except Exception as e:
        return None, f"Gagal membaca st.secrets: {e}"

    return None, "credentials.json atau st.secrets['gcp_service_account'] tidak ditemukan."


@st.cache_resource(show_spinner=False)
def _get_client_cached(creds_key: str):
    """Client gspread di-cache. creds_key hanya pemicu cache."""
    creds_dict, err = _load_credentials_dict()
    if err:
        raise RuntimeError(err)
    pk = creds_dict.get("private_key", "")
    creds_dict["private_key"] = pk.replace("\\n", "\n")
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def get_gspread_client():
    creds_dict, err = _load_credentials_dict()
    if err:
        return None, err
    try:
        key = str(creds_dict.get("private_key_id", "")) + str(creds_dict.get("client_email", ""))
        return _get_client_cached(key), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def get_connected_spreadsheet():
    client, err = get_gspread_client()
    if err:
        return None, err
    try:
        return client.open_by_key(SPREADSHEET_ID), None
    except gspread.exceptions.APIError as e:
        return None, (f"APIError: {e}. Pastikan Sheet sudah di-share ke email service account "
                      f"sebagai Editor, dan Google Sheets API + Drive API sudah aktif.")
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


# ============================ WORKSHEET ============================
def get_ws(spreadsheet, name):
    """Cari worksheet tanpa peduli huruf besar/kecil."""
    for ws in spreadsheet.worksheets():
        if ws.title.strip().lower() == name.strip().lower():
            return ws
    raise gspread.WorksheetNotFound(name)


def safe_append(spreadsheet, sheet_name, row):
    """Tambah baris ke sheet. Return (berhasil, pesan_error)."""
    if not spreadsheet:
        return False, "Koneksi ke Google Sheet tidak tersedia."
    try:
        get_ws(spreadsheet, sheet_name).append_row(row, value_input_option="USER_ENTERED")
        return True, ""
    except Exception as e:
        print(f"Gagal append ke sheet {sheet_name}: {e}")
        return False, f"{type(e).__name__}: {e}"


def ensure_worksheets(spreadsheet):
    """Buat sheet (huruf kecil) yang belum ada & perbaiki header yang tidak sesuai skema."""
    if not spreadsheet:
        return False
    try:
        existing = {ws.title.strip().lower(): ws for ws in spreadsheet.worksheets()}
        for nama, header in SCHEMA.items():
            ws = existing.get(nama)
            if ws is None:
                ws = spreadsheet.add_worksheet(title=nama, rows=500, cols=max(10, len(header)))
                ws.append_row(header)
                continue
            row1 = [c.strip() for c in ws.row_values(1)]
            if row1 != header:
                ws.update(values=[header], range_name="A1")
        return True
    except Exception as e:
        print(f"Error ensuring worksheets: {e}")
        return False


# ============================ SESSION STATE ============================
def init_session_db():
    for nama, key in SESSION_KEYS.items():
        if key not in st.session_state:
            st.session_state[key] = pd.DataFrame(columns=SCHEMA[nama])


def sync_data_from_sheets(spreadsheet_obj):
    """Tarik data dari Sheet ke session state. Return (berhasil, pesan_error)."""
    if not spreadsheet_obj:
        return False, "Tidak terhubung."
    try:
        existing = {ws.title.strip().lower(): ws for ws in spreadsheet_obj.worksheets()}
        for nama, key in SESSION_KEYS.items():
            ws = existing.get(nama)
            if ws is None:
                continue
            data = ws.get_all_values()
            if len(data) > 1:
                header = [h.strip() for h in data[0]]
                df = pd.DataFrame(data[1:], columns=header)
                df = df[df.apply(lambda r: any(str(v).strip() for v in r), axis=1)]
                st.session_state[key] = df.reset_index(drop=True)
            else:
                st.session_state[key] = pd.DataFrame(columns=SCHEMA[nama])
        st.session_state["_last_sync"] = time.time()
        return True, ""
    except Exception as e:
        print(f"Error sync from sheets: {e}")
        return False, f"{type(e).__name__}: {e}"


def auto_connect_and_sync(force=False):
    """
    Hubungkan ke Sheet, pastikan struktur ada, dan sync (dibatasi TTL).
    Return (spreadsheet_obj, error_message).
    """
    init_session_db()
    spreadsheet_obj, err = get_connected_spreadsheet()
    if not spreadsheet_obj:
        return None, err

    if not st.session_state.get("_ws_ready"):
        if ensure_worksheets(spreadsheet_obj):
            st.session_state["_ws_ready"] = True

    terakhir = st.session_state.get("_last_sync", 0)
    if force or (time.time() - terakhir) > SYNC_TTL_DETIK:
        ok, serr = sync_data_from_sheets(spreadsheet_obj)
        if not ok:
            return spreadsheet_obj, f"Terhubung, tetapi gagal membaca data: {serr}"
    return spreadsheet_obj, None


def get_current_date_indonesia():
    hari = {0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis", 4: "Jumat", 5: "Sabtu", 6: "Minggu"}
    bulan = {1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
             7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"}
    now = datetime.now()
    return f"{hari[now.weekday()]}, {now.day} {bulan[now.month]} {now.year}"