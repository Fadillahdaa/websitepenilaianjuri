"""
styles.py - CSS terpusat + menu sidebar berbasis tombol (tema Navy-Champagne).
Sudah termasuk hamburger menu kustom untuk tampilan HP.
Tampilan DIKUNCI ke tema terang: tidak mengikuti mode gelap browser / device.
Tampilan HP: konten berada di TENGAH layar (rata tengah).
"""
import streamlit as st
import streamlit.components.v1 as components

NAVY = "#112250"
NAVY_2 = "#3B507D"
CHAMPAGNE = "#E7E2CE"
IVORY = "#F5F4F0"
SAND = "#BEB7A7"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* Kunci tampilan ke TERANG. Browser/device mode gelap tidak boleh mengubah warna. */
:root, html, body {
    color-scheme: only light !important;
}
html, body { background-color: %IVORY%; }

html, body, .stApp, .stApp p, .stApp div, .stApp label, .stApp input,
.stApp button, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp textarea {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

%STAGE%

/* Field input tetap terang walau device mode gelap */
.stApp input, .stApp textarea {
    color-scheme: only light !important;
}
[data-testid="stMain"] [data-baseweb="input"],
[data-testid="stMain"] [data-baseweb="textarea"],
[data-testid="stMain"] [data-baseweb="select"] > div {
    background-color: #ffffff !important;
}
[data-testid="stMain"] input,
[data-testid="stMain"] textarea {
    color: %NAVY% !important;
    -webkit-text-fill-color: %NAVY% !important;
    background-color: transparent !important;
}
[data-testid="stMain"] label p,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] h1,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] h3,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] h4 {
    color: %NAVY%;
}

/* Popup (dialog) tetap putih */
[data-testid="stDialog"] [role="dialog"],
[data-testid="stDialog"] > div > div {
    background-color: #ffffff !important;
    color-scheme: only light !important;
}

/* ================= HEADER STREAMLIT (TETAP TAMPIL) ================= */
[data-testid="stHeader"] { background: transparent !important; }

/* Sembunyikan hanya navigasi multipage bawaan (menu sidebar buatan sendiri tetap tampil) */
[data-testid="stSidebarNav"], [data-testid="stSidebarNavItems"] { display: none !important; }

/* Iframe pembantu (script hamburger) tidak boleh memakan ruang */
[data-testid="stElementContainer"]:has(iframe[height="0"]),
.element-container:has(iframe[height="0"]) {
    position: absolute !important;
    height: 0 !important;
    width: 0 !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* ================= LAPTOP: SIDEBAR SELALU TERBUKA ================= */
@media (min-width: 769px) {
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"][aria-expanded="false"] {
        display: block !important;
        visibility: visible !important;
        transform: none !important;
        margin-left: 0 !important;
        min-width: 300px !important;
        width: 300px !important;
        opacity: 1 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] { display: none !important; }
    #custom-hamburger, #nav-backdrop { display: none !important; }
}

/* ================= HP: HAMBURGER KUSTOM + SIDEBAR GESER ================= */
#custom-hamburger {
    display: none;
    position: fixed;
    top: 10px;
    left: 10px;
    width: 46px;
    height: 46px;
    align-items: center;
    justify-content: center;
    background: %NAVY%;
    color: %CHAMPAGNE%;
    border: 1px solid %NAVY_2%;
    border-radius: 12px;
    box-shadow: 0 4px 14px rgba(17, 34, 80, .35);
    font-size: 24px;
    line-height: 1;
    padding: 0;
    cursor: pointer;
    z-index: 1000002;
}
#nav-backdrop {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(11, 23, 54, .55);
    z-index: 999998;
}

@media (max-width: 768px) {
    #custom-hamburger { display: flex; }

    /* sembunyikan tombol buka bawaan Streamlit agar tidak dobel */
    [data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] { display: none !important; }

    /* sidebar: default tertutup (di luar layar) */
    section[data-testid="stSidebar"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        height: 100% !important;
        width: 82vw !important;
        max-width: 320px !important;
        min-width: 0 !important;
        margin-left: 0 !important;
        transform: translateX(-110%) !important;
        visibility: visible !important;
        display: block !important;
        transition: transform .25s ease !important;
        z-index: 999999 !important;
        overflow-y: auto !important;
    }
    /* sidebar terbuka */
    body.nav-open section[data-testid="stSidebar"] {
        transform: translateX(0) !important;
        box-shadow: 8px 0 30px rgba(0, 0, 0, .35) !important;
    }
    body.nav-open #nav-backdrop { display: block; }

    /* ================= KONTEN UTAMA DI TENGAH (HP) ================= */
    /* Wadah utama: lebar penuh, ditengahkan, ruang atas untuk hamburger */
    [data-testid="stMain"],
    [data-testid="stMain"] > div,
    [data-testid="stAppViewContainer"] > section.main {
        width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }
    [data-testid="stMain"] .block-container,
    [data-testid="stMainBlockContainer"],
    .stApp section.main .block-container {
        padding-top: 4.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-bottom: 2rem !important;
        width: 100% !important;
        max-width: 560px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* Semua elemen di dalam wadah ikut penuh dan ditengahkan */
    [data-testid="stMain"] [data-testid="stVerticalBlock"] {
        width: 100% !important;
        align-items: stretch !important;
    }
    [data-testid="stMain"] [data-testid="stElementContainer"],
    [data-testid="stMain"] .element-container {
        width: 100% !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* Judul, teks, dan keterangan rata tengah */
    [data-testid="stMain"] [data-testid="stMarkdownContainer"],
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stMain"] [data-testid="stCaptionContainer"],
    [data-testid="stMain"] [data-testid="stCaptionContainer"] p {
        text-align: center !important;
    }

    /* Label isian ikut tengah */
    [data-testid="stMain"] [data-testid="stWidgetLabel"],
    [data-testid="stMain"] [data-testid="stWidgetLabel"] p {
        text-align: center !important;
        justify-content: center !important;
    }

    /* Gambar / logo di tengah */
    [data-testid="stMain"] [data-testid="stImage"],
    [data-testid="stMain"] [data-testid="stImageContainer"] {
        display: flex !important;
        justify-content: center !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* Kartu kustom: isi di tengah */
    .brand-header-admin,
    .metric-card,
    .metric-card-juri,
    .content-card {
        text-align: center !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* Tombol di tengah, lebar penuh */
    [data-testid="stMain"] .stButton,
    [data-testid="stMain"] [data-testid="stFormSubmitButton"] {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }

    /* tombol tutup bawaan di dalam sidebar tidak diperlukan */
    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* ruang atas di dalam sidebar agar tidak menabrak tombol ✕ */
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] > div:last-child { padding-top: 3.4rem !important; }

    /* ================= PENYESUAIAN TATA LETAK KHUSUS HP (TETAP TANPA UBAH WARNA) ================= */
    /* Ubah kolom sejajar (columns) menjadi tumpukan vertikal agar tidak sempit di HP */
    [data-testid="stHorizontalBlock"],
    [data-testid="column"] {
        flex-direction: column !important;
        width: 100% !important;
        min-width: 100% !important;
        flex: 1 1 100% !important;
        gap: 0.5rem !important;
    }

    /* Perbesar area sentuh tombol di HP agar mudah diklik jari */
    .stApp .stButton > button {
        min-height: 46px !important;
        font-size: 0.95rem !important;
        padding: 10px 14px !important;
    }

    /* Padding kartu form di HP lebih rapat agar pas di layar kecil */
    [data-testid="stForm"]:not([data-testid*="form_login_admin"]) {
        padding: 20px 16px !important;
        border-radius: 16px !important;
    }

    /* ===== ANTI OVERFLOW HORIZONTAL (penyebab konten bergeser ke kiri) ===== */
    html, body, .stApp, [data-testid="stApp"],
    [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        width: 100% !important;
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }
    [data-testid="stMain"] *, [data-testid="stForm"] * {
        box-sizing: border-box !important;
    }
    [data-testid="stMain"] .block-container > *,
    [data-testid="stMain"] [data-testid="stVerticalBlock"] > *,
    [data-testid="stMain"] [data-testid="stElementContainer"] > * {
        max-width: 100% !important;
    }
    [data-testid="stHorizontalBlock"] {
        width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }
    [data-testid="stColumn"], [data-testid="column"] {
        min-width: 0 !important;
        max-width: 100% !important;
        width: 100% !important;
    }
    [data-testid="stForm"],
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stMain"] [data-baseweb="input"],
    [data-testid="stMain"] [data-baseweb="select"],
    [data-testid="stMain"] [data-baseweb="textarea"],
    .content-card, .metric-card, .metric-card-juri, .brand-header-admin {
        width: 100% !important;
        max-width: 100% !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* Tabel / dataframe agar bisa digeser horizontal jika datanya panjang */
    [data-testid="stTable"], [data-testid="stDataFrame"] {
        font-size: 0.82rem !important;
        overflow-x: auto !important;
    }
}

/* Tombol hamburger disembunyikan bila sidebar tidak punya menu */
body:not(:has(section[data-testid="stSidebar"] .stButton)) #custom-hamburger { display: none !important; }

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
    .brand-header-admin {
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        gap: 12px;
        padding: 16px;
    }
}

/* ================= INPUT SELALU PUTIH, TULISAN HITAM (anti dark mode) ================= */
html body [data-baseweb="input"],
html body [data-baseweb="input"] > div,
html body [data-baseweb="base-input"],
html body [data-baseweb="textarea"],
html body [data-baseweb="textarea"] > div,
html body [data-baseweb="select"] > div,
html body [data-baseweb="select"] > div > div {
    background-color: #ffffff !important;
    border-color: #CFCAB8 !important;
    color: #000000 !important;
}

html body [data-testid="stMain"] input,
html body [data-testid="stMain"] textarea,
html body [data-testid="stForm"] input,
html body [data-testid="stForm"] textarea,
html body [data-testid="stDialog"] input,
html body [data-testid="stDialog"] textarea {
    background-color: #ffffff !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    caret-color: #000000 !important;
    color-scheme: only light !important;
}

/* Placeholder abu-abu agar terbaca di latar putih */
html body input::placeholder,
html body textarea::placeholder {
    color: #6B7280 !important;
    -webkit-text-fill-color: #6B7280 !important;
    opacity: 1 !important;
}

/* Teks dropdown (selectbox) hitam */
html body [data-testid="stForm"] [data-baseweb="select"] *,
html body [data-testid="stMain"] [data-baseweb="select"] * {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}

/* Daftar pilihan dropdown (muncul di luar form, jadi dipisah) */
html body [data-baseweb="popover"] [role="listbox"],
html body [data-baseweb="popover"] ul,
html body [data-baseweb="popover"] li,
html body [data-baseweb="menu"] {
    background-color: #ffffff !important;
    color: #000000 !important;
}
html body [data-baseweb="popover"] li:hover,
html body [data-baseweb="popover"] [aria-selected="true"] {
    background-color: %CHAMPAGNE% !important;
}

/* Isian otomatis Chrome (autofill) tetap putih */
html body input:-webkit-autofill {
    -webkit-box-shadow: 0 0 0 1000px #ffffff inset !important;
    -webkit-text-fill-color: #000000 !important;
}

/* ================= SEMUA KOMPONEN FORM: PUTIH + TULISAN NAVY (anti dark mode) ================= */

/* ---- Radio ---- */
html body [data-testid="stRadio"] label,
html body [data-testid="stRadio"] label p,
html body [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p,
html body div[role="radiogroup"] label p {
    color: #112250 !important;
    -webkit-text-fill-color: #112250 !important;
}
html body [data-baseweb="radio"] > div:first-child {
    background-color: #ffffff !important;
    border: 2px solid #112250 !important;
}
html body [data-baseweb="radio"]:has(input:checked) > div:first-child {
    background-color: #112250 !important;
    border-color: #112250 !important;
}
html body [data-baseweb="radio"]:has(input:checked) > div:first-child > div {
    background-color: #ffffff !important;
}

/* ---- Checkbox / centang ---- */
html body [data-testid="stCheckbox"] label,
html body [data-testid="stCheckbox"] label p,
html body [data-baseweb="checkbox"] {
    color: #112250 !important;
    -webkit-text-fill-color: #112250 !important;
}
html body [data-baseweb="checkbox"] > div:first-child {
    background-color: #ffffff !important;
    border: 2px solid #112250 !important;
}
html body [data-baseweb="checkbox"]:has(input:checked) > div:first-child {
    background-color: #112250 !important;
    border-color: #112250 !important;
}
html body [data-baseweb="checkbox"]:has(input:checked) svg,
html body [data-baseweb="checkbox"]:has(input:checked) svg path {
    fill: #ffffff !important;
    stroke: #ffffff !important;
    color: #ffffff !important;
}
html body [data-baseweb="checkbox"]:has(input:disabled) > div:first-child {
    background-color: #ffffff !important;
}
html body [data-testid="stCheckbox"]:has(input:disabled) label p { opacity: .55; }

/* ---- Dropdown / selectbox ---- */
html body [data-baseweb="select"] svg,
html body [data-baseweb="select"] svg path {
    fill: #112250 !important;
    color: #112250 !important;
}
html body [data-baseweb="select"] input,
html body [data-baseweb="select"] [class*="singleValue"],
html body [data-baseweb="select"] div {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}
html body [data-baseweb="popover"],
html body [data-baseweb="popover"] > div,
html body [data-baseweb="popover"] [data-baseweb="menu"],
html body [data-baseweb="popover"] [role="listbox"],
html body [data-baseweb="popover"] [role="option"],
html body [data-baseweb="popover"] ul,
html body [data-baseweb="popover"] li {
    background-color: #ffffff !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}
html body [data-baseweb="popover"] [role="option"] *,
html body [data-baseweb="popover"] li * {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}
html body [data-baseweb="popover"] [role="option"]:hover,
html body [data-baseweb="popover"] [aria-selected="true"] {
    background-color: #E7E2CE !important;
}

/* ---- Textarea, number input, stepper ---- */
html body [data-testid="stNumberInput"] button {
    background-color: #ffffff !important;
    color: #112250 !important;
}
html body [data-testid="stNumberInput"] button svg { fill: #112250 !important; }

/* ---- Container berborder, expander, dialog ---- */
html body [data-testid="stVerticalBlockBorderWrapper"],
html body [data-testid="stExpander"],
html body [data-testid="stExpander"] details,
html body [data-testid="stExpander"] summary {
    background-color: #ffffff !important;
    color: #112250 !important;
}
html body [data-testid="stExpander"] summary p,
html body [data-testid="stExpander"] summary svg {
    color: #112250 !important;
    fill: #112250 !important;
}
html body [data-testid="stDialog"] [role="dialog"],
html body [data-testid="stDialog"] [role="dialog"] * {
    color-scheme: only light !important;
}

/* ---- Teks bantu (caption, label, markdown) di area utama ---- */
html body [data-testid="stMain"] [data-testid="stCaptionContainer"],
html body [data-testid="stMain"] [data-testid="stCaptionContainer"] p {
    color: #6B7280 !important;
    -webkit-text-fill-color: #6B7280 !important;
}
html body [data-testid="stMain"] [data-testid="stWidgetLabel"] p {
    color: #112250 !important;
    -webkit-text-fill-color: #112250 !important;
}

/* ---- Tabs (menu Database Google Sheet) ---- */
html body [data-baseweb="tab-list"] { background-color: transparent !important; }
html body [data-baseweb="tab"] { color: #112250 !important; background-color: transparent !important; }
</style>
"""

_STAGE_DARK = ".stApp { background: linear-gradient(135deg, #0b1736 0%, #112250 50%, #1a3375 100%) !important; }"
_STAGE_LIGHT = ".stApp { background: %IVORY% !important; color: %NAVY% !important; }"

_NAV_JS = """
<script>
(function () {
    try {
        var p = window.parent;

        try {
            var d = p.document;
            var m = d.querySelector('meta[name="color-scheme"]');
            if (!m) {
                m = d.createElement('meta');
                m.setAttribute('name', 'color-scheme');
                d.head.appendChild(m);
            }
            m.setAttribute('content', 'only light');
            d.documentElement.style.colorScheme = 'only light';

            /* Pastikan viewport HP pas dengan lebar layar (konten tidak bergeser ke kiri) */
            var v = d.querySelector('meta[name="viewport"]');
            if (v) {
                v.setAttribute('content', 'width=device-width, initial-scale=1, viewport-fit=cover');
            }
        } catch (e) {}

        if (p.__navInit) { return; }
        p.__navInit = true;

        var init = function () {
            var b = document.createElement('button');
            b.id = 'custom-hamburger';
            b.type = 'button';
            b.setAttribute('aria-label', 'Menu');
            b.textContent = '\\u2630';

            var bd = document.createElement('div');
            bd.id = 'nav-backdrop';

            document.body.appendChild(bd);
            document.body.appendChild(b);

            function setOpen(open) {
                document.body.classList.toggle('nav-open', open);
                b.textContent = open ? '\\u2715' : '\\u2630';
            }
            b.addEventListener('click', function () {
                setOpen(!document.body.classList.contains('nav-open'));
            });
            bd.addEventListener('click', function () { setOpen(false); });

            document.addEventListener('click', function (e) {
                if (!document.body.classList.contains('nav-open')) { return; }
                var t = e.target;
                if (t.closest && t.closest('section[data-testid="stSidebar"]') && t.closest('button')) {
                    setTimeout(function () { setOpen(false); }, 250);
                }
            });
        };

        new p.Function('(' + init.toString() + ')()')();
    } catch (err) { console.log('nav init gagal', err); }
})();
</script>
"""


def inject(dark_stage: bool = False) -> None:
    css = _CSS.replace("%STAGE%", _STAGE_DARK if dark_stage else _STAGE_LIGHT)
    for token, value in {
        "%NAVY_2%": NAVY_2, "%NAVY%": NAVY, "%CHAMPAGNE%": CHAMPAGNE,
        "%IVORY%": IVORY, "%SAND%": SAND,
    }.items():
        css = css.replace(token, value)
    st.markdown(css, unsafe_allow_html=True)
    components.html(_NAV_JS, height=0)


def sidebar_menu(items, key, divider_before=None):
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