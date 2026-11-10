import os
import re
import json
import time
import random
import threading
from datetime import datetime, timedelta, timezone

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
# "jenis"  = pilihan dropdown instansi (diisi admin)
# "juri"   = data juri + instansinya (digabung, tanpa sheet instansi terpisah)
#            kolom terima_magang berisi "Ya" / "Tidak" / "" (belum diisi)
SCHEMA = {
    "jenis": ["id_jenis", "nama_jenis"],
    "juri": ["id_juri", "nama_juri", "jenis_instansi", "nama_instansi", "terima_magang"],
    "peserta": ["id_peserta", "nama_peserta", "status"],
    "penilaian": ["id", "id_juri", "id_peserta",
                  "k1", "k2", "k3", "k4", "waktu_input", "catatan", "rata_rata"],
    "favorit": ["waktu_input", "id_juri", "id_peserta"],
}
SESSION_KEYS = {
    "jenis": "db_jenis",
    "juri": "db_juri",
    "peserta": "db_peserta",
    "penilaian": "db_penilaian",
    "favorit": "db_favorit",
}

# Cache data Sheet yang DIBAGI ke semua juri/sesi (detik).
# Selama cache masih berlaku, berapa pun jumlah juri, tidak ada request baca ke Google.
SHEET_CACHE_TTL = 30
# Jarak minimal sync per sesi (sync dari cache itu gratis, jadi boleh sering).
SYNC_TTL_DETIK = 20

# ============================ WAKTU INDONESIA (WIB) ============================
# WIB = UTC+7 dan tidak mengenal DST, jadi offset tetap sudah akurat
# (tidak perlu paket tzdata di Windows).
WIB = timezone(timedelta(hours=7))


def now_wib():
    return datetime.now(WIB)


def timestamp_wib():
    """Format yang ditulis ke Sheet, contoh: 2026-11-07 17:03:25 (WIB)."""
    return now_wib().strftime("%Y-%m-%d %H:%M:%S")


# ============================ HELPER DATA ============================
def ensure_cols(df, sheet):
    """Pastikan df punya semua kolom sesuai SCHEMA[sheet] (aman untuk data lama)."""
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame(columns=SCHEMA[sheet])
    df = df.copy()
    for col in SCHEMA[sheet]:
        if col not in df.columns:
            df[col] = ""
    return df


# ============================ HELPER ID ============================
def next_id(df, prefix, col):
    """Buat ID berikutnya, contoh: PST-001, JNS-002, JUR-003."""
    nums = []
    if df is not None and not df.empty and col in df.columns:
        for v in df[col].tolist():
            v = str(v)
            if v.startswith(prefix + "-") and v.split("-")[-1].isdigit():
                nums.append(int(v.split("-")[-1]))
    return f"{prefix}-{(max(nums) if nums else 0) + 1:03d}"


# ============================ RETRY & LOCK ============================
def _is_retryable(e):
    s = str(e)
    return any(k in s for k in ("429", "Quota exceeded", "500", "502", "503", "504"))


def with_retry(fn, *args, tries=5, **kwargs):
    """Jalankan fn; jika kena rate limit (429) / error server sementara,
    tunggu bertahap (+ acak) lalu coba lagi."""
    for i in range(tries):
        try:
            return fn(*args, **kwargs)
        except gspread.exceptions.APIError as e:
            if _is_retryable(e) and i < tries - 1:
                time.sleep(min(2 ** i, 16) + random.random())
                continue
            raise


@st.cache_resource(show_spinner=False)
def get_write_lock():
    """Satu lock untuk seluruh server: penulisan ke Sheet dilakukan satu per satu,
    jadi nomor baris yang sudah dibaca tidak bergeser oleh juri lain."""
    return threading.RLock()


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


@st.cache_resource(show_spinner=False, ttl=3600)
def _get_spreadsheet_cached(creds_key: str):
    """Objek Spreadsheet di-cache 1 jam dan dipakai bersama semua sesi
    (open_by_key = 1 request, tidak perlu diulang tiap rerun)."""
    client = _get_client_cached(creds_key)
    return with_retry(client.open_by_key, SPREADSHEET_ID)


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
    creds_dict, err = _load_credentials_dict()
    if err:
        return None, err
    key = str(creds_dict.get("private_key_id", "")) + str(creds_dict.get("client_email", ""))
    try:
        return _get_spreadsheet_cached(key), None
    except gspread.exceptions.APIError as e:
        return None, (f"APIError: {e}. Pastikan Sheet sudah di-share ke email service account "
                      f"sebagai Editor, dan Google Sheets API + Drive API sudah aktif.")
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


# ============================ WORKSHEET ============================
@st.cache_resource(show_spinner=False, ttl=600)
def _ws_map(_spreadsheet):
    """Daftar worksheet di-cache (tidak memanggil worksheets() berulang)."""
    return {ws.title.strip().lower(): ws for ws in with_retry(_spreadsheet.worksheets)}


def get_ws(spreadsheet, name):
    """Cari worksheet tanpa peduli huruf besar/kecil (dari cache)."""
    key = name.strip().lower()
    ws = _ws_map(spreadsheet).get(key)
    if ws is None:  # mungkin sheet baru dibuat
        _ws_map.clear()
        ws = _ws_map(spreadsheet).get(key)
    if ws is None:
        raise gspread.WorksheetNotFound(name)
    return ws


# ============================ CACHE DATA BERSAMA ============================
@st.cache_data(show_spinner=False, ttl=SHEET_CACHE_TTL)
def _fetch_all(_spreadsheet):
    """Ambil SEMUA sheet dengan 1 request saja. Dipakai bersama oleh semua juri."""
    m = _ws_map(_spreadsheet)
    names = [n for n in [*SCHEMA, "instansi"] if n in m]
    ranges = [f"'{m[n].title}'" for n in names]
    res = with_retry(_spreadsheet.values_batch_get, ranges)
    return {n: vr.get("values", []) for n, vr in zip(names, res.get("valueRanges", []))}


def invalidate_cache():
    """Panggil setelah menulis ke Sheet agar sync berikutnya mengambil data terbaru."""
    _fetch_all.clear()


# ============================ PENULISAN AMAN (LOCK + RETRY) ============================
# Semua fungsi mengembalikan (berhasil: bool, pesan_error: str).
def _no_conn():
    return False, "Koneksi ke Google Sheet tidak tersedia."


def safe_append(spreadsheet, sheet_name, row):
    """Tambah satu baris ke sheet."""
    if not spreadsheet:
        return _no_conn()
    try:
        with get_write_lock():
            ws = get_ws(spreadsheet, sheet_name)
            with_retry(ws.append_row, row, value_input_option="USER_ENTERED")
        invalidate_cache()
        return True, ""
    except Exception as e:
        print(f"Gagal append ke sheet {sheet_name}: {e}")
        return False, f"{type(e).__name__}: {e}"


def _baris_cocok(ws, nilai, kolom):
    """Nomor baris (mulai 1) yang isi kolom-nya persis sama dengan nilai. 1 request baca."""
    isi = with_retry(ws.col_values, kolom)
    return [i for i, v in enumerate(isi, start=1) if i > 1 and v == str(nilai)]


def _hapus_baris_berurutan(ws, nomor_baris):
    """Hapus banyak baris; baris yang berurutan digabung jadi 1 request. Dari bawah ke atas."""
    nomor = sorted(set(nomor_baris), reverse=True)
    i = 0
    while i < len(nomor):
        akhir = nomor[i]
        awal = akhir
        while i + 1 < len(nomor) and nomor[i + 1] == awal - 1:
            awal = nomor[i + 1]
            i += 1
        if awal == akhir:
            with_retry(ws.delete_rows, awal)
        else:
            with_retry(ws.delete_rows, awal, akhir)
        i += 1


def hapus_baris_by_id(spreadsheet, sheet_name, nilai, kolom=1):
    """Hapus semua baris yang kolom-nya sama persis dengan nilai (mis. id_peserta)."""
    if not spreadsheet:
        return _no_conn()
    try:
        with get_write_lock():
            ws = get_ws(spreadsheet, sheet_name)
            _hapus_baris_berurutan(ws, _baris_cocok(ws, nilai, kolom))
        invalidate_cache()
        return True, ""
    except Exception as e:
        print(f"Gagal hapus baris {sheet_name}: {e}")
        return False, f"{type(e).__name__}: {e}"


def ubah_sel_by_id(spreadsheet, sheet_name, id_value, kolom_ubah, nilai_baru, kolom_id=1):
    """Ubah satu sel pada baris yang ID-nya cocok. Kolom dihitung mulai 1."""
    if not spreadsheet:
        return _no_conn()
    try:
        with get_write_lock():
            ws = get_ws(spreadsheet, sheet_name)
            baris = _baris_cocok(ws, id_value, kolom_id)
            if not baris:
                return False, "ID tidak ditemukan di Sheet."
            with_retry(ws.update_cell, baris[0], kolom_ubah, nilai_baru)
        invalidate_cache()
        return True, ""
    except Exception as e:
        print(f"Gagal ubah sel {sheet_name}: {e}")
        return False, f"{type(e).__name__}: {e}"


def update_juri_magang(spreadsheet, id_juri, status):
    """Simpan status terima magang ("Ya"/"Tidak") ke kolom E sheet 'juri'."""
    kolom = SCHEMA["juri"].index("terima_magang") + 1  # = 5 (kolom E)
    return ubah_sel_by_id(spreadsheet, "juri", id_juri, kolom, status)


def simpan_penilaian_sheet(spreadsheet, juri_id, peserta_id, baris):
    """Simpan baru / perbarui penilaian satu juri untuk satu peserta."""
    if not spreadsheet:
        return _no_conn()
    try:
        with get_write_lock():
            ws = get_ws(spreadsheet, "penilaian")
            semua = with_retry(ws.get_all_values)
            baris_lama = [
                i for i, r in enumerate(semua[1:], start=2)
                if len(r) > 2 and r[1] == str(juri_id) and r[2] == str(peserta_id)
            ]
            if baris_lama:
                with_retry(ws.update, values=[baris], range_name=f"A{baris_lama[0]}")
                if len(baris_lama) > 1:
                    _hapus_baris_berurutan(ws, baris_lama[1:])
            else:
                with_retry(ws.append_row, baris, value_input_option="RAW")
        invalidate_cache()
        return True, ""
    except Exception as e:
        print(f"Gagal simpan penilaian ke Sheet: {e}")
        return False, f"{type(e).__name__}: {e}"


def ganti_favorit_sheet(spreadsheet, juri_id, baris_baru):
    """Ganti seluruh pilihan favorit satu juri dengan baris_baru."""
    if not spreadsheet:
        return _no_conn()
    try:
        with get_write_lock():
            ws = get_ws(spreadsheet, "favorit")
            semua = with_retry(ws.get_all_values)
            baris_lama = [
                i for i, r in enumerate(semua[1:], start=2)
                if len(r) > 1 and r[1] == str(juri_id)
            ]
            if baris_lama:
                _hapus_baris_berurutan(ws, baris_lama)
            with_retry(ws.append_rows, baris_baru, value_input_option="RAW")
        invalidate_cache()
        return True, ""
    except Exception as e:
        print(f"Gagal simpan favorit ke Sheet: {e}")
        return False, f"{type(e).__name__}: {e}"


# ============================ INISIALISASI SHEET ============================
def ensure_worksheets(spreadsheet):
    """Buat sheet (huruf kecil) yang belum ada & perbaiki header yang tidak sesuai skema."""
    if not spreadsheet:
        return False
    try:
        with get_write_lock():
            existing = dict(_ws_map(spreadsheet))
            for nama, header in SCHEMA.items():
                ws = existing.get(nama)
                if ws is None:
                    ws = with_retry(spreadsheet.add_worksheet,
                                    title=nama, rows=500, cols=max(10, len(header)))
                    with_retry(ws.append_row, header)
                    continue
                row1 = [c.strip() for c in with_retry(ws.row_values, 1)]
                if row1 != header:
                    # padding kosong menghapus sisa header lama
                    sisa = [""] * max(0, len(row1) - len(header))
                    with_retry(ws.update, values=[header + sisa], range_name="A1")
        _ws_map.clear()
        return True
    except Exception as e:
        print(f"Error ensuring worksheets: {e}")
        return False


# ============================ PERBAIKAN DATA LAMA ============================
_POLA_TANGGAL = re.compile(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}")


def _angka(v):
    v = str(v).strip().replace(",", ".")
    if not v:
        return False
    try:
        float(v)
        return True
    except ValueError:
        return False


def perbaiki_urutan_penilaian(spreadsheet):
    """
    Perbaikan satu kali untuk baris lama sheet penilaian:
    [.., k4, rata_rata, waktu_input, catatan]  ->  [.., k4, waktu_input, catatan, rata_rata]
    Hanya baris yang berpola urutan lama yang diubah, jadi aman dijalankan berulang.
    Return jumlah baris yang diperbaiki.
    """
    try:
        with get_write_lock():
            ws = get_ws(spreadsheet, "penilaian")
            semua = with_retry(ws.get_all_values)
            data = []
            for no, r in enumerate(semua[1:], start=2):
                r = list(r) + [""] * (10 - len(r))
                if _angka(r[7]) and ":" in r[8] and _POLA_TANGGAL.search(r[8]):
                    baru = r[:7] + [r[8], r[9], r[7]]
                    data.append({"range": f"A{no}", "values": [baru]})
            if data:
                with_retry(ws.batch_update, data)
        return len(data)
    except Exception as e:
        print(f"Gagal memperbaiki urutan kolom penilaian: {e}")
        return 0


@st.cache_resource(show_spinner=False)
def _init_sheets_once(_spreadsheet):
    """Dijalankan SEKALI per server (bukan per sesi juri).
    Jika gagal, exception dilempar sehingga tidak ikut ter-cache dan dicoba lagi nanti."""
    if not ensure_worksheets(_spreadsheet):
        raise RuntimeError("ensure_worksheets gagal")
    perbaiki_urutan_penilaian(_spreadsheet)
    _ws_map.clear()
    invalidate_cache()
    return True


# ============================ NAMA ASLI INSTANSI (DATA LAMA) ============================
# Data juri lama menyimpan kode (INS-001 / JNS-001), bukan nama. Kode diterjemahkan
# memakai sheet lama "instansi" (jika masih ada) dan sheet "jenis".
_POLA_KODE = re.compile(r"^(INS|JNS)-\d+$", re.IGNORECASE)


def _peta_instansi_dari_data(data):
    """Ubah isi sheet lama 'instansi' (list of rows) -> {KODE: {"nama": ..., "jenis": ...}}."""
    peta = {}
    if len(data) < 2:
        return peta
    header = [h.strip().lower() for h in data[0]]

    def cari(*kata):
        for i, h in enumerate(header):
            if any(k in h for k in kata):
                return i
        return None

    i_id = cari("id")
    i_nama = cari("nama")
    i_jenis = cari("jenis", "tipe", "kategori")
    i_id = 0 if i_id is None else i_id
    i_nama = 1 if i_nama is None else i_nama

    for r in data[1:]:
        r = list(r) + [""] * (len(header) - len(r))
        kode = r[i_id].strip()
        if kode:
            peta[kode.upper()] = {
                "nama": r[i_nama].strip(),
                "jenis": r[i_jenis].strip() if i_jenis is not None else "",
            }
    return peta


def _peta_jenis():
    df = ensure_cols(st.session_state.get("db_jenis"), "jenis")
    return {str(r["id_jenis"]).strip().upper(): str(r["nama_jenis"]).strip()
            for _, r in df.iterrows() if str(r["id_jenis"]).strip()}


def resolve_instansi(jenis, nama):
    """Ubah (jenis, nama) yang mungkin berisi kode menjadi nama asli. Return (jenis, nama)."""
    peta_inst = st.session_state.get("_peta_instansi_lama", {})
    peta_jenis = _peta_jenis()
    jenis = str(jenis or "").strip()
    nama = str(nama or "").strip()

    def ke_jenis(v):
        return peta_jenis.get(v.upper(), v)

    info = peta_inst.get(jenis.upper())
    if info:  # kolom jenis_instansi ternyata berisi kode instansi lama (INS-xxx)
        if not nama:
            nama = info["nama"]
        jenis = ke_jenis(info["jenis"]) if info["jenis"] else ""
    else:
        jenis = ke_jenis(jenis)

    info2 = peta_inst.get(nama.upper())
    if info2:
        nama = info2["nama"]
    return jenis, nama


def tampilkan_nama_juri(df):
    """DataFrame juri dengan kolom jenis_instansi & nama_instansi berisi nama asli (untuk tampilan)."""
    df = ensure_cols(df, "juri").copy()
    hasil = [resolve_instansi(j, n) for j, n in zip(df["jenis_instansi"], df["nama_instansi"])]
    df["jenis_instansi"] = [h[0] for h in hasil]
    df["nama_instansi"] = [h[1] for h in hasil]
    for c in ["jenis_instansi", "nama_instansi"]:
        df[c] = df[c].apply(
            lambda v: f"⚠️ data lama ({v})" if _POLA_KODE.match(str(v).strip())
            else (v if str(v).strip() else "-")
        )
    return df


def rapikan_data_juri(spreadsheet):
    """Tulis nama asli instansi ke sheet 'juri' menggantikan kode lama. Return (jumlah_baris, error)."""
    if not spreadsheet:
        return 0, "Koneksi ke Google Sheet tidak tersedia."
    try:
        with get_write_lock():
            ws = get_ws(spreadsheet, "juri")
            semua = with_retry(ws.get_all_values)
            data = []
            for no, r in enumerate(semua[1:], start=2):
                r = list(r) + [""] * (5 - len(r))
                j, n = resolve_instansi(r[2], r[3])
                if _POLA_KODE.match(j) or _POLA_KODE.match(n) or not n:
                    continue  # belum bisa diterjemahkan, biarkan apa adanya
                if (j, n) != (r[2].strip(), r[3].strip()):
                    data.append({"range": f"C{no}:D{no}", "values": [[j, n]]})
            if data:
                with_retry(ws.batch_update, data)
        invalidate_cache()
        return len(data), ""
    except Exception as e:
        print(f"Gagal merapikan data juri: {e}")
        return 0, f"{type(e).__name__}: {e}"


# ============================ SESSION STATE ============================
def init_session_db():
    for nama, key in SESSION_KEYS.items():
        if key not in st.session_state:
            st.session_state[key] = pd.DataFrame(columns=SCHEMA[nama])


def _data_ke_df(data, nama):
    """Ubah list of rows dari Sheet menjadi DataFrame bersih."""
    if len(data) <= 1:
        return pd.DataFrame(columns=SCHEMA[nama])
    header = [h.strip() for h in data[0]]
    rows = [(list(r) + [""] * len(header))[:len(header)] for r in data[1:]]
    df = pd.DataFrame(rows, columns=header)
    df = df.loc[:, [c != "" for c in df.columns]]   # buang kolom tanpa nama
    df = df.loc[:, ~df.columns.duplicated()]        # buang nama kolom ganda
    df = df[df.apply(lambda r: any(str(v).strip() for v in r), axis=1)]
    return df.reset_index(drop=True)


def sync_data_from_sheets(spreadsheet_obj, force=False):
    """Tarik data (dari cache bersama) ke session state. Return (berhasil, pesan_error)."""
    if not spreadsheet_obj:
        return False, "Tidak terhubung."
    try:
        if force:
            invalidate_cache()
        raw = _fetch_all(spreadsheet_obj)
        for nama, key in SESSION_KEYS.items():
            st.session_state[key] = _data_ke_df(raw.get(nama, []), nama)
        try:
            st.session_state["_peta_instansi_lama"] = _peta_instansi_dari_data(raw.get("instansi", []))
        except Exception as e:
            print(f"Gagal membaca sheet instansi lama: {e}")
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

    try:
        _init_sheets_once(spreadsheet_obj)
    except Exception as e:
        print(f"Init sheets gagal: {e}")

    terakhir = st.session_state.get("_last_sync", 0)
    if force or (time.time() - terakhir) > SYNC_TTL_DETIK:
        ok, serr = sync_data_from_sheets(spreadsheet_obj, force=force)
        if not ok:
            # Data sesi sebelumnya masih ada -> jangan tampilkan error menakutkan ke juri
            if st.session_state.get("_last_sync"):
                return spreadsheet_obj, None
            return spreadsheet_obj, f"Terhubung, tetapi gagal membaca data: {serr}"
    return spreadsheet_obj, None


def get_current_date_indonesia():
    hari = {0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis", 4: "Jumat", 5: "Sabtu", 6: "Minggu"}
    bulan = {1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
             7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"}
    now = now_wib()
    return f"{hari[now.weekday()]}, {now.day} {bulan[now.month]} {now.year}"