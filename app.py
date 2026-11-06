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

# ==============================================================================
# NATIVE ROUTING STREAMLIT DENGAN url_path KHUSUS:
# - URL: https://penilaianjuri.streamlit.app/           -> Halaman Sisi Juri (Default)
# - URL: https://penilaianjuri.streamlit.app/admin_masuk -> Halaman Sisi Admin
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
        url_path="admin_masuk"  # Mengatur endpoint URL menjadi /admin_masuk
    )

    # Biarkan st.navigation yang mengatur perpindahan halaman berdasarkan URL secara otomatis
    pg = st.navigation([page_juri, page_admin], position="hidden")
    pg.run()

else:
    # Fallback untuk versi Streamlit legacy (< 1.36)
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