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
# - URL: http://localhost:8502/            -> Halaman Sisi Juri (Default)
# - URL: http://localhost:8502/admin_masuk -> Halaman Sisi Admin (Tanpa tanda "/")
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
        url_path="admin_masuk"  # <-- PERBAIKAN: Gunakan underscore (_) tanpa garis miring (/)
    )

    # Tangkap parameter URL untuk memaksa pindah ke admin jika diakses via /admin_masuk
    qp = st.query_params
    query_str = str(qp).lower()
    page_val = str(qp.get("page", "")).lower()

    if "admin" in page_val or "admin_masuk" in query_str or "admin" in query_str:
        # Jika mengakses URL admin, jalankan fungsi render admin secara langsung
        admin_view.render_admin_portal()
    else:
        # Jalankan routing normal Streamlit
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