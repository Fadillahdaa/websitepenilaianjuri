import streamlit as st
import db_helper
import juri_view
import admin_view

# ==============================================================================
# KONFIGURASI HALAMAN UTAMA (HANYA SEKALI DI AWAL RUN)
# ==============================================================================
st.set_page_config(
    page_title="PBK DIGITAL AI - Sistem Penilaian",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

db_helper.init_session_db()
db_client, conn_err = db_helper.auto_connect_and_sync()

# --- SEMBUNYIKAN TOOLBAR / TOMBOL EDIT ---
hide_streamlit_style = """
    <style>
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- INISIALISASI SESSION STATE GLOBAL & PEMULIHAN SESI JURI DARI URL ---
if "juri_auth" not in st.session_state:
    st.session_state.juri_auth = {"is_logged_in": False, "id_juri": "", "nama": "", "jenis": "", "instansi": ""}

# Jika session juri di RAM kosong tapi ada parameter juri_id di URL (setelah refresh), pulihkan otomatis!
if not st.session_state.juri_auth["is_logged_in"] and "juri_id" in st.query_params:
    saved_juri_id = st.query_params["juri_id"]
    if "db_juri" not in st.session_state:
        _, _ = db_helper.auto_connect_and_sync()
        
    df_juri = db_helper.ensure_cols(st.session_state.get("db_juri"), "juri")
    match_juri = df_juri[df_juri["id_juri"].astype(str) == str(saved_juri_id)]
    
    if not match_juri.empty:
        row_j = match_juri.iloc[0]
        st.session_state.juri_auth = {
            "is_logged_in": True,
            "id_juri": row_j["id_juri"],
            "nama": row_j["nama_juri"],
            "jenis": row_j["jenis_instansi"],
            "instansi": row_j["nama_instansi"],
        }

# --- INISIALISASI SESSION STATE ADMIN GLOBAL ---
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "admin_login_time" not in st.session_state:
    st.session_state.admin_login_time = 0.0

# ==============================================================================
# NATIVE ROUTING STREAMLIT
# ==============================================================================
if hasattr(st, "navigation") and hasattr(st, "Page"):
    page_juri = st.Page(
        juri_view.render_juri_portal,
        title="Portal Dewan Juri",
        icon="🏆",
        default=True,
        url_path=""
    )

    page_admin = st.Page(
        admin_view.render_admin_portal,
        title="Panel Administrator",
        icon="⚙️",
        url_path="admin_masuk"
    )

    pg = st.navigation([page_juri, page_admin], position="hidden")
    pg.run()

else:
    qp = st.query_params
    is_admin = False
    if "admin" in str(qp.get("page", "")).lower() or "admin_masuk" in str(qp).lower():
        is_admin = True
    for key in list(qp.keys()):
        if "admin_masuk" in str(key).lower() or str(key).lower() == "admin":
            is_admin = True

    if is_admin:
        admin_view.render_admin_portal()
    else:
        juri_view.render_juri_portal()