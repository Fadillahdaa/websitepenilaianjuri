import os
import pandas as pd
from datetime import datetime
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ID Google Spreadsheet Anda yang tersambung secara permanen
SPREADSHEET_ID = "1RsQ4RLGVcqghM3LlFVDTu1OIuYokwC6if_CpWrPUrPk"

def get_gspread_client():
    """Otomatisasi otentikasi Google Sheets API tanpa cache statis untuk mencegah bentrok koneksi"""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    possible_cred_paths = [
        "credentials.json",
        "credential.json",
        os.path.join(os.path.dirname(__file__), "credentials.json"),
        os.path.join(os.path.dirname(__file__), "credential.json")
    ]
    cred_file = None
    for path in possible_cred_paths:
        if os.path.exists(path):
            cred_file = path
            break
            
    try:
        if cred_file:
            creds = ServiceAccountCredentials.from_json_keyfile_name(cred_file, scope)
        elif "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            return None, "File credentials.json atau st.secrets['gcp_service_account'] tidak ditemukan."

        client = gspread.authorize(creds)
        return client, None
    except Exception as e:
        return None, str(e)

def get_connected_spreadsheet():
    """Membuka spreadsheet secara otomatis menggunakan ID permanen"""
    client, err = get_gspread_client()
    if err:
        return None, err
    try:
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        return spreadsheet, None
    except Exception as e:
        return None, str(e)

def auto_connect_and_sync():
    """Fungsi utama otomatis: menghubungkan, mengecek worksheet, dan menarik data"""
    init_session_db()
    spreadsheet_obj, err = get_connected_spreadsheet()
    if spreadsheet_obj:
        ensure_worksheets(spreadsheet_obj)
        sync_data_from_sheets(spreadsheet_obj)
        return spreadsheet_obj, None
    return None, err

def ensure_worksheets(spreadsheet):
    """Menyiapkan struktur sheet jika belum ada dengan penanganan error aman per lembar (Tanpa data dummy)"""
    if not spreadsheet:
        return False
    try:
        existing_titles = {ws.title.lower(): ws for ws in spreadsheet.worksheets()}
        
        # 1. Sheet instansi
        if "instansi" not in existing_titles:
            try:
                ws_instansi = spreadsheet.add_worksheet(title="instansi", rows=100, cols=5)
                ws_instansi.append_row(["id_instansi", "nama_instansi"])
            except Exception:
                pass
        
        # 2. Sheet Juri
        if "juri" not in existing_titles:
            try:
                ws_juri = spreadsheet.add_worksheet(title="Juri", rows=100, cols=10)
                ws_juri.append_row(["id_juri", "nama_juri", "id_instansi"])
            except Exception:
                pass
                
        # 3. Sheet peserta
        if "peserta" not in existing_titles:
            try:
                ws_peserta = spreadsheet.add_worksheet(title="Peserta", rows=100, cols=10)
                ws_peserta.append_row(["id_peserta", "nama_peserta", "status"])
            except Exception:
                pass
                
        # 4. Sheet penilaian
        if "penilaian" not in existing_titles:
            try:
                ws_penilaian = spreadsheet.add_worksheet(title="Penilaian", rows=500, cols=15)
                ws_penilaian.append_row([
                    "id", "nama_juri", "instansi_id",
                    "k1", "k2", "k3", "k4", "waktu_input", "catatan"
                ])
            except Exception:
                pass
            
        # 5. Sheet favorit
        if "favorit" not in existing_titles:
            try:
                ws_favorit = spreadsheet.add_worksheet(title="Favorit", rows=200, cols=5)
                ws_favorit.append_row(["waktu_input", "id_juri", "id_instansi", "id_peserta"])
            except Exception:
                pass
            
        return True
    except Exception as e:
        print(f"Error ensuring worksheets: {e}")
        return False

def init_session_db():
    """Inisialisasi session state lokal dengan skema kolom terbaru"""
    if "db_instansi" not in st.session_state:
        st.session_state.db_instansi = pd.DataFrame(columns=["id_instansi", "nama_instansi"])
    if "db_juri" not in st.session_state:
        st.session_state.db_juri = pd.DataFrame(columns=["id_juri", "nama_juri", "id_instansi"])
    if "db_peserta" not in st.session_state:
        st.session_state.db_peserta = pd.DataFrame(columns=["id_peserta", "nama_peserta", "status"])
    if "db_penilaian" not in st.session_state:
        st.session_state.db_penilaian = pd.DataFrame(columns=[
            "id", "id_juri", "id_instansi", "id_peserta",
            "k1", "k2", "k3", "k4", "waktu_input", "catatan"
        ])
    if "db_favorit" not in st.session_state:
        st.session_state.db_favorit = pd.DataFrame(columns=[
            "waktu_input", "id_juri", "id_instansi", "id_peserta"
        ])

def sync_data_from_sheets(spreadsheet_obj):
    """Sinkronisasi data otomatis dari Google Sheets ke session state"""
    if not spreadsheet_obj:
        return
    try:
        worksheets = spreadsheet_obj.worksheets()
        existing_titles = {ws.title.lower(): ws for ws in worksheets}
        
        # 1. Sync Instansi
        if "instansi" in existing_titles:
            ws = existing_titles["instansi"]
            data = ws.get_all_values()
            if len(data) > 1:
                st.session_state.db_instansi = pd.DataFrame(data[1:], columns=data[0])
            else:
                st.session_state.db_instansi = pd.DataFrame(columns=["id_instansi", "nama_instansi"])
                
        # 2. Sync Juri
        if "juri" in existing_titles:
            ws = existing_titles["juri"]
            data = ws.get_all_values()
            if len(data) > 1:
                st.session_state.db_juri = pd.DataFrame(data[1:], columns=data[0])
            else:
                st.session_state.db_juri = pd.DataFrame(columns=["id_juri", "nama_juri", "id_instansi"])
            
        # 3. Sync Peserta
        if "peserta" in existing_titles:
            ws = existing_titles["peserta"]
            data = ws.get_all_values()
            if len(data) > 1:
                st.session_state.db_peserta = pd.DataFrame(data[1:], columns=data[0])
            else:
                st.session_state.db_peserta = pd.DataFrame(columns=["id_peserta", "nama_peserta", "status"])
            
        # 4. Sync Penilaian
        if "penilaian" in existing_titles:
            ws = existing_titles["penilaian"]
            data = ws.get_all_values()
            if len(data) > 1:
                st.session_state.db_penilaian = pd.DataFrame(data[1:], columns=data[0])
            else:
                st.session_state.db_penilaian = pd.DataFrame(columns=[
                    "id", "id_juri", "id_instansi", "id_peserta",
                    "k1", "k2", "k3", "k4", "waktu_input", "catatan"
                ])
            
        # 5. Sync Favorit
        if "favorit" in existing_titles:
            ws = existing_titles["favorit"]
            data = ws.get_all_values()
            if len(data) > 1:
                st.session_state.db_favorit = pd.DataFrame(data[1:], columns=data[0])
            else:
                st.session_state.db_favorit = pd.DataFrame(columns=[
                    "waktu_input", "id_juri", "id_instansi", "id_peserta"
                ])
    except Exception as e:
        print(f"Error sync from sheets: {e}")

def get_current_date_indonesia():
    hari_indonesia = {0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis", 4: "Jumat", 5: "Sabtu", 6: "Minggu"}
    bulan_indonesia = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
        7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    now = datetime.now()
    return f"{hari_indonesia[now.weekday()]}, {now.day} {bulan_indonesia[now.month]} {now.year}"