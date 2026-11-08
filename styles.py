"""
styles.py - CSS terpusat + menu sidebar berbasis tombol (mendukung otomatis Light/Dark Mode Chrome + Ukuran Font Lebih Besar).
Sudah termasuk hamburger menu kustom untuk tampilan HP.
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

/* KUNCI KE SKEMA TERANG PERMANEN (Mencegah Chrome memaksa dark mode pada input) */
:root {
    color-scheme: light !important;
}

html, body, .stApp {
    color-scheme: light !important;
}

html, body, .stApp, .stApp p, .stApp div, .stApp label, .stApp input,
.stApp button, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp textarea {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Memperbesar ukuran font dasar secara keseluruhan di seluruh elemen teks */
.stApp, .stApp p, .stApp span, .stApp label, .stApp input, .stApp textarea {
    font-size: 1.05rem !important;
}

/* Memperbesar ukuran font pada heading agar lebih proporsional */
.stApp h1 { font-size: 2.3rem !important; }
.stApp h2 { font-size: 1.8rem !important; }
.stApp h3 { font-size: 1.4rem !important; }

%STAGE%

/* ================= KOTAK INPUT (TERANG PERMANEN & KEBAL DARK MODE) ================= */
input, textarea, select, 
[data-baseweb="input"],
[data-baseweb="input"] input,
[data-testid="stTextInputField"],
[data-testid="stPasswordInput"] input {
    background-color: #ffffff !important;
    background: #ffffff !important;
    color: #112250 !important;
    -webkit-text-fill-color: #112250 !important;
    border-color: %CHAMPAGNE% !important;
    color-scheme: light !important;
}

[data-baseweb="input"], 
div[data-baseweb="input"] {
    background-color: #ffffff !important;
    background: #ffffff !important;
}

input:focus, textarea:focus, select:focus,
[data-baseweb="input"]:focus-within {
    background-color: #ffffff !important;
    background: #ffffff !important;
    color: #112250 !important;
    -webkit-text-fill-color: #112250 !important;
    border-color: %NAVY% !important;
    box-shadow: 0 0 0 2px rgba(17, 34, 80, 0.15) !important;
    color-scheme: light !important;
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

    /* beri ruang atas supaya konten tidak tertutup hamburger */
    [data-testid="stMain"] .block-container,
    .stApp section.main .block-container { padding-top: 4.2rem !important; }

    /* tombol tutup bawaan di dalam sidebar tidak diperlukan (pakai ✕ kustom) */
    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* ruang atas di dalam sidebar agar tidak menabrak tombol ✕ */
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] > div:last-child { padding-top: 3.4rem !important; }
}

/* Tombol hamburger disembunyikan bila sidebar tidak punya menu (mis. halaman login) */
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
    font-size: 1rem !important;
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
    padding: 12px 20px !important;
    width: 100% !important;
    font-size: 1.05rem !important;
}
[data-testid="stMain"] .stButton > button p,
[data-testid="stFormSubmitButton"] > button p { color: inherit !important; }
[data-testid="stMain"] .stButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    background-color: %NAVY_2% !important;
    color: %CHAMPAGNE% !important;
}

/* ================= FORM = KARTU (Adaptif Terang/Gelap) ================= */
[data-testid="stForm"]:not([data-testid*="form_login_admin"]) {
    background: var(--card-bg, #ffffff);
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

/* ================= PERBAIKAN STYLING DATAFRAME / TABEL ================= */
[data-testid="stDataFrame"] {
    background-color: #ffffff !important;
    color-scheme: light !important;
    border-radius: 12px !important;
    border: 1px solid #E7E2CE !important;
    box-shadow: 0 4px 12px rgba(17, 34, 80, 0.05) !important;
}

/* Header tabel */
[data-testid="stDataFrame"] th {
    background-color: #F5F4F0 !important;
    color: #112250 !important;
    font-weight: 700 !important;
}

/* Sel data tabel agar tetap kontras dan terbaca jelas */
[data-testid="stDataFrame"] td {
    background-color: #ffffff !important;
    color: #112250 !important;
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
    background: var(--card-bg, #fff);
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

_STAGE_AUTO = """
@media (prefers-color-scheme: dark) {
    .stApp { background: linear-gradient(135deg, #0b1736 0%, #112250 50%, #1a3375 100%) !important; color: #F5F4F0 !important; }
    :root { --card-bg: #162a5c; --text-color: #F5F4F0; }
}
@media (prefers-color-scheme: light) {
    .stApp { background: %IVORY% !important; color: %NAVY% !important; }
    :root { --card-bg: #ffffff; --text-color: %NAVY%; }
}
"""

_STAGE_DARK = ".stApp { background: linear-gradient(135deg, #0b1736 0%, #112250 50%, #1a3375 100%) !important; color: #F5F4F0 !important; } :root { --card-bg: #162a5c; --text-color: #F5F4F0; }"
_STAGE_LIGHT = ".stApp { background: %IVORY% !important; color: %NAVY% !important; } :root { --card-bg: #ffffff; --text-color: %NAVY%; }"

_NAV_JS = """
<script>
(function () {
    try {
        var p = window.parent;
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
    if dark_stage is True:
        stage_css = _STAGE_DARK
    elif dark_stage is False:
        stage_css = _STAGE_LIGHT
    else:
        stage_css = _STAGE_LIGHT

    css = _CSS.replace("%STAGE%", stage_css)
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