import os
import re
import time
import uuid
import random
import threading
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from google.api_core import exceptions as gexc
from google.cloud.firestore_v1.base_query import FieldFilter

# ============================ SKEMA ============================
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

# Cache data yang dibagi ke semua sesi (detik). Firestore menagih per dokumen yang dibaca.
SHEET_CACHE_TTL = 30
SYNC_TTL_DETIK = 20

# ============================ WAKTU INDONESIA (WIB) ============================
WIB = timezone(timedelta(hours=7))


def now_wib():
    return datetime.now(WIB)


def timestamp_wib():
    return now_wib().strftime("%Y-%m-%d %H:%M:%S")


# ============================ RETRY & LOCK ============================
_RETRYABLE = (gexc.ResourceExhausted, gexc.ServiceUnavailable,
              gexc.InternalServerError, gexc.DeadlineExceeded, gexc.Aborted)


def with_retry(fn, *args, tries=5, **kwargs):
    for i in range(tries):
        try:
            return fn(*args, **kwargs)
        except _RETRYABLE:
            if i < tries - 1:
                time.sleep(min(2 ** i, 16) + random.random())
                continue
            raise


@st.cache_resource(show_spinner=False)
def get_write_lock():
    return threading.RLock()


# ============================ KONEKSI FIREBASE ============================
@st.cache_resource(show_spinner=False)
def get_firebase_client():
    """Inisialisasi Firestore sekali untuk semua sesi."""
    if not firebase_admin._apps:
        base = os.path.dirname(os.path.abspath(__file__))
        cred_path = None
        for nama in ["firebase_credentials.json", "credentials.json", "credential.json"]:
            for path in [nama, os.path.join(base, nama)]:
                if os.path.exists(path):
                    cred_path = path
                    break
            if cred_path:
                break

        if cred_path:
            firebase_admin.initialize_app(credentials.Certificate(cred_path))
        else:
            try:
                key = "firebase" if "firebase" in st.secrets else "gcp_service_account"
                creds_dict = dict(st.secrets[key])
            except Exception as e:
                raise RuntimeError(f"Kredensial Firebase tidak ditemukan: {e}")
            creds_dict["private_key"] = creds_dict.get("private_key", "").replace("\\n", "\n")
            firebase_admin.initialize_app(credentials.Certificate(creds_dict))
    return firestore.client()


def get_connected_spreadsheet():
    """Nama lama dipertahankan. Return (client, error)."""
    try:
        return get_firebase_client(), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


# ============================ HELPER DATA ============================
def ensure_cols(df, sheet):
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame(columns=SCHEMA[sheet])
    df = df.copy()
    for col in SCHEMA[sheet]:
        if col not in df.columns:
            df[col] = ""
    return df


def next_id(df, prefix, col):
    nums = []
    if df is not None and not df.empty and col in df.columns:
        for v in df[col].tolist():
            v = str(v)
            if v.startswith(prefix + "-") and v.split("-")[-1].isdigit():
                nums.append(int(v.split("-")[-1]))
    return f"{prefix}-{(max(nums) if nums else 0) + 1:03d}"


def _row_to_dict(sheet, row):
    """list (urutan SCHEMA) atau dict -> dict berisi string untuk semua kolom skema."""
    header = SCHEMA[sheet]
    if isinstance(row, dict):
        return {h: ("" if row.get(h) is None else str(row.get(h))) for h in header}
    row = list(row) + [""] * (len(header) - len(row))
    return {h: ("" if v is None else str(v)) for h, v in zip(header, row)}


def _doc_id(sheet, d):
    """ID dokumen deterministik. penilaian/favorit = juri__peserta (sama dengan skrip migrasi)."""
    if sheet == "jenis":
        raw = d.get("id_jenis")
    elif sheet == "juri":
        raw = d.get("id_juri")
    elif sheet == "peserta":
        raw = d.get("id_peserta")
    else:
        raw = f"{d.get('id_juri', '')}__{d.get('id_peserta', '')}"
    raw = str(raw or "").strip().replace("/", "_")
    return raw if raw and raw != "__" else uuid.uuid4().hex


def _nama_field(sheet, kolom, default=1):
    """kolom bisa angka (mulai 1, seperti nomor kolom Sheet) atau nama field."""
    cols = SCHEMA[sheet]
    if isinstance(kolom, int):
        idx = kolom if kolom >= 1 else default
        return cols[idx - 1]
    return str(kolom)


def _cari_docs(db, sheet, field, nilai):
    q = db.collection(sheet).where(filter=FieldFilter(field, "==", str(nilai)))
    return with_retry(lambda: list(q.stream()))


def _hapus_docs(db, docs):
    batch, n = db.batch(), 0
    for d in docs:
        batch.delete(d.reference)
        n += 1
        if n % 400 == 0:
            with_retry(batch.commit)
            batch = db.batch()
    if n % 400 != 0:
        with_retry(batch.commit)


# ============================ CACHE & SYNC ============================
@st.cache_data(show_spinner=False, ttl=SHEET_CACHE_TTL)
def _fetch_all(_db):
    """Inisialisasi Firestore dengan aman tanpa error duplikat app."""
    hasil = {}
    try:
        for nama in SCHEMA:
            docs = list(_db.collection(nama).stream())
            rows = []
            for d in docs:
                data = d.to_dict() or {}
                if nama == "penilaian" and not data.get("id"):
                    data["id"] = d.id
                rows.append(data)
            hasil[nama] = rows
    except Exception as e:
        print(f"ERROR SAAT STREAM FIRESTORE: {e}")
    return hasil

def init_session_db():
    for nama, key in SESSION_KEYS.items():
        if key not in st.session_state:
            st.session_state[key] = pd.DataFrame(columns=SCHEMA[nama])


def _data_ke_df(data, nama):
    if not data:
        return pd.DataFrame(columns=SCHEMA[nama])
    df = pd.DataFrame(data)
    for col in SCHEMA[nama]:
        if col not in df.columns:
            df[col] = ""
    df = df[SCHEMA[nama]].fillna("").astype(str)
    urut = "waktu_input" if nama in ("penilaian", "favorit") else SCHEMA[nama][0]
    return df.sort_values(urut, kind="stable").reset_index(drop=True)


def sync_data_from_sheets(spreadsheet_obj=None, force=False):
    """Tarik data (dari cache bersama) ke session_state. Return (berhasil, error)."""
    try:
        db = spreadsheet_obj or get_firebase_client()
        if force:
            invalidate_cache()
        raw = _fetch_all(db)
        for nama, key in SESSION_KEYS.items():
            st.session_state[key] = _data_ke_df(raw.get(nama, []), nama)
        st.session_state["_peta_instansi_lama"] = {}
        st.session_state["_last_sync"] = time.time()
        return True, ""
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def auto_connect_and_sync(force=False):
    """Hubungkan + sync dibatasi TTL. Return (client, error)."""
    init_session_db()
    db, err = get_connected_spreadsheet()
    if not db:
        return None, err

    terakhir = st.session_state.get("_last_sync", 0)
    if force or (time.time() - terakhir) > SYNC_TTL_DETIK:
        ok, serr = sync_data_from_sheets(db, force=force)
        if not ok:
            if st.session_state.get("_last_sync"):
                return db, None
            return db, f"Terhubung, tetapi gagal membaca data: {serr}"
    return db, None


# ============================ PENULISAN ============================
def _no_conn():
    return False, "Koneksi ke Firebase tidak tersedia."


def safe_append(db_client, sheet_name, row_dict_or_list):
    try:
        db = db_client or get_firebase_client()
        d = _row_to_dict(sheet_name, row_dict_or_list)
        with get_write_lock():
            with_retry(db.collection(sheet_name).document(_doc_id(sheet_name, d)).set, d)
        invalidate_cache()
        return True, ""
    except Exception as e:
        return False, f"Gagal menambah data: {e}"


def hapus_baris_by_id(db_client, sheet_name, nilai_id, kolom=1):
    """Hapus SEMUA dokumen yang field-nya (kolom ke-N / nama field) sama dengan nilai."""
    try:
        db = db_client or get_firebase_client()
        field = _nama_field(sheet_name, kolom)
        with get_write_lock():
            _hapus_docs(db, _cari_docs(db, sheet_name, field, nilai_id))
        invalidate_cache()
        return True, ""
    except Exception as e:
        return False, f"Gagal menghapus data: {e}"


def ubah_sel_by_id(db_client, sheet_name, id_value, kolom_ubah, nilai_baru, kolom_id=1):
    try:
        db = db_client or get_firebase_client()
        field_ubah = _nama_field(sheet_name, kolom_ubah)
        field_id = _nama_field(sheet_name, kolom_id)
        with get_write_lock():
            docs = _cari_docs(db, sheet_name, field_id, id_value)
            if not docs:
                return False, "ID tidak ditemukan di database."
            with_retry(docs[0].reference.update, {field_ubah: str(nilai_baru)})
        invalidate_cache()
        return True, ""
    except Exception as e:
        return False, f"Gagal mengubah data: {e}"


def update_juri_magang(db_client, id_juri, status):
    return ubah_sel_by_id(db_client, "juri", id_juri, "terima_magang", status)


def simpan_penilaian_sheet(db_client, juri_id, peserta_id, baris_list):
    try:
        db = db_client or get_firebase_client()
        d = _row_to_dict("penilaian", baris_list)
        d["id_juri"], d["id_peserta"] = str(juri_id), str(peserta_id)
        doc_id = _doc_id("penilaian", d)
        if not d.get("id"):
            d["id"] = doc_id
        with get_write_lock():
            with_retry(db.collection("penilaian").document(doc_id).set, d)
        invalidate_cache()
        return True, ""
    except Exception as e:
        return False, f"Gagal menyimpan penilaian: {e}"


def ganti_favorit_sheet(db_client, juri_id, baris_baru_list):
    try:
        db = db_client or get_firebase_client()
        with get_write_lock():
            _hapus_docs(db, _cari_docs(db, "favorit", "id_juri", juri_id))
            batch = db.batch()
            for r in baris_baru_list:
                d = _row_to_dict("favorit", r)
                batch.set(db.collection("favorit").document(_doc_id("favorit", d)), d)
            with_retry(batch.commit)
        invalidate_cache()
        return True, ""
    except Exception as e:
        return False, f"Gagal menyimpan favorit: {e}"


# ============================ KOMPATIBILITAS (VIEW LAMA) ============================
_POLA_KODE = re.compile(r"^(INS|JNS)-\d+$", re.IGNORECASE)


def ensure_worksheets(spreadsheet=None):
    return True


def perbaiki_urutan_penilaian(spreadsheet=None):
    return 0


def _peta_jenis():
    df = ensure_cols(st.session_state.get("db_jenis"), "jenis")
    return {str(r["id_jenis"]).strip().upper(): str(r["nama_jenis"]).strip()
            for _, r in df.iterrows() if str(r["id_jenis"]).strip()}


def resolve_instansi(jenis, nama):
    jenis = str(jenis or "").strip()
    nama = str(nama or "").strip()
    return _peta_jenis().get(jenis.upper(), jenis), nama


def tampilkan_nama_juri(df):
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


def rapikan_data_juri(db_client=None):
    """Ganti kode jenis (JNS-xxx) pada dokumen juri dengan nama asli. Return (jumlah, error)."""
    try:
        db = db_client or get_firebase_client()
        n = 0
        for d in with_retry(lambda: list(db.collection("juri").stream())):
            r = d.to_dict() or {}
            j, nm = resolve_instansi(r.get("jenis_instansi", ""), r.get("nama_instansi", ""))
            if _POLA_KODE.match(j) or not nm:
                continue
            if (j, nm) != (str(r.get("jenis_instansi", "")).strip(), str(r.get("nama_instansi", "")).strip()):
                with_retry(d.reference.update, {"jenis_instansi": j, "nama_instansi": nm})
                n += 1
        invalidate_cache()
        return n, ""
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


def get_current_date_indonesia():
    hari = {0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis", 4: "Jumat", 5: "Sabtu", 6: "Minggu"}
    bulan = {1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
             7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"}
    now = now_wib()
    return f"{hari[now.weekday()]}, {now.day} {bulan[now.month]} {now.year}"