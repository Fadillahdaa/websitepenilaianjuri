"""
styles.py - CSS terpusat + menu sidebar berbasis tombol (tema Navy-Champagne).
"""
import streamlit as st

NAVY = "#112250"
NAVY_2 = "#3B507D"
CHAMPAGNE = "#E7E2CE"
IVORY = "#F5F4F0"
SAND = "#BEB7A7"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* Mencegah browser memaksa auto dark mode */
:root {
    color-scheme: light dark;
}

html, body, .stApp, .stApp p, .stApp div, .stApp label, .stApp input,
.stApp button, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp textarea {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

%STAGE%

/* ================= HEADER STREAMLIT (TETAP TAMPIL) =================
   Header & toolbar tidak disembunyikan agar tombol buka/tutup sidebar
   selalu tersedia. Latar dibuat transparan supaya menyatu dengan tema. */
[data-testid="stHeader"] { background: transparent !important; }

/* Sembunyikan hanya navigasi multipage bawaan (menu sidebar buatan sendiri tetap tampil) */
[data-testid="stSidebarNav"], [data-testid="stSidebarNavItems"] { display: none !important; }

/* ================= SIDEBAR ================= */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
    background-color: %NAVY% !important;
}
section[data-testid="stSidebar"] { border-right: 1px solid %NAVY_2%; }
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: %SAND% !important;
}

/* ---- Menu = tombol bergaya kartu (tanpa lingkaran radio) ---- */
section[data-testid="stSidebar"] .stButton > button,
section[data-testid="stSidebar"] button[kind],
section[data-testid="stSidebar"] [data-testid^="stBaseButton"] {
    background-color: transparent !important;
    color: %CHAMPAGNE% !important;
    border: 1px solid transparent !important;
    border-radius: 12px !important;
    box-shadow: none !important;
    width: 100% !important;
    padding: 12px 16px !important;
    justify-content: flex-start !important;
    text-align: left !important;
    transition: background-color .2s ease, border-color .2s ease !important;
}
section[data-testid="stSidebar"] .stButton > button *,
section[data-testid="stSidebar"] [data-testid^="stBaseButton"] * {
    color: inherit !important;
    justify-content: flex-start !important;
    text-align: left !important;
    margin: 0 !important;
    font-size: .92rem !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] .stButton > button:hover,
section[data-testid="stSidebar"] [data-testid^="stBaseButton"]:hover {
    background-color: rgba(231, 226, 206, .14) !important;
    border-color: rgba(231, 226, 206, .25) !important;
    color: %CHAMPAGNE% !important;
}
section[data-testid="stSidebar"] button[kind="primary"],
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"],
section[data-testid="stSidebar"] button[kind="primary"]:hover,
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover {
    background-color: %CHAMPAGNE% !important;
    border-color: %CHAMPAGNE% !important;
    color: %NAVY% !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, .18) !important;
}
section[data-testid="stSidebar"] button[kind="primary"] *,
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] * {
    color: %NAVY% !important;
    font-weight: 800 !important;
}
section[data-testid="stSidebar"] [data-testid="stElementContainer"],
section[data-testid="stSidebar"] .element-container { margin-bottom: 0 !important; }
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .4rem !important; }

/* ================= TOMBOL AREA UTAMA ================= */
.stApp section.main .stButton > button,
[data-testid="stMain"] .stButton > button,
[data-testid="stFormSubmitButton"] > button {
    background-color: %NAVY% !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 10px 20px !important;
    width: 100% !important;
}
[data-testid="stMain"] .stButton > button p,
[data-testid="stFormSubmitButton"] > button p { color: inherit !important; }
[data-testid="stMain"] .stButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    background-color: %NAVY_2% !important;
    color: %CHAMPAGNE% !important;
}

/* ================= FORM = KARTU PUTIH (Kecuali Form Login Admin) ================= */
[data-testid="stForm"]:not([data-testid*="form_login_admin"]) {
    background: #ffffff;
    border: 1px solid %CHAMPAGNE% !important;
    border-radius: 20px;
    padding: 28px 26px;
    box-shadow: 0 12px 30px rgba(17, 34, 80, .10);
}

/* Khusus Form Login Admin agar transparan dan menyatu sempurna di dalam kotak kanan */
[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    box-shadow: none !important;
    width: 100% !important;
}

[data-testid="stForm"] label p,
[data-testid="stForm"] h1, [data-testid="stForm"] h2, [data-testid="stForm"] h3 {
    color: %NAVY% !important;
}

/* ================= KOMPONEN KUSTOM ================= */
.brand-header-admin {
    background: linear-gradient(135deg, %NAVY% 0%, %NAVY_2% 100%);
    border-radius: 16px;
    padding: 24px 30px;
    color: #fff;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px rgba(17, 34, 80, .12);
    display: flex; align-items: center; justify-content: space-between;
    border: 1px solid %NAVY_2%;
}
.metric-card, .metric-card-juri, .content-card {
    background: #fff;
    border-radius: 16px;
    padding: 24px;
    border: 1px solid %CHAMPAGNE%;
    box-shadow: 0 6px 18px rgba(17, 34, 80, .05);
}
.metric-card, .metric-card-juri { text-align: center; }
.content-card { margin-bottom: 20px; }

@media (max-width: 768px) {
    .brand-header-admin { flex-direction: column; text-align: center; gap: 12px; padding: 16px; }
}
@media (max-width: 640px) {
    [data-testid="stColumn"], [data-testid="column"] {
        min-width: 100% !important;
        flex: 1 1 100% !important;
    }
}
</style>
"""

_STAGE_DARK = ".stApp { background: linear-gradient(135deg, #0b1736 0%, #112250 50%, #1a3375 100%) !important; }"
_STAGE_LIGHT = ".stApp { background: %IVORY% !important; color: %NAVY% !important; }"


def inject(dark_stage: bool = False) -> None:
    """Suntikkan CSS. Panggil sekali di awal setiap render halaman."""
    css = _CSS.replace("%STAGE%", _STAGE_DARK if dark_stage else _STAGE_LIGHT)
    for token, value in {
        "%NAVY_2%": NAVY_2, "%NAVY%": NAVY, "%CHAMPAGNE%": CHAMPAGNE,
        "%IVORY%": IVORY, "%SAND%": SAND,
    }.items():
        css = css.replace(token, value)
    st.markdown(css, unsafe_allow_html=True)


def sidebar_menu(items, key, divider_before=None):
    """
    Menu sidebar bergaya kartu. Panggil di dalam `with st.sidebar:`.
    Mengembalikan label menu yang sedang aktif.
    """
    if st.session_state.get(key) not in items:
        st.session_state[key] = items[0]

    for i, label in enumerate(items):
        if divider_before and label == divider_before:
            st.markdown("<hr style='border-color:#3B507D; opacity:.5; margin:10px 0;'>",
                        unsafe_allow_html=True)
        aktif = st.session_state[key] == label
        if st.button(label, key=f"{key}_btn_{i}",
                     type="primary" if aktif else "secondary",
                     use_container_width=True):
            st.session_state[key] = label
            st.rerun()
    return st.session_state[key]
