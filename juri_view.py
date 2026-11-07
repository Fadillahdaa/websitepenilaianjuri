import time
import uuid

import streamlit as st
import pandas as pd
import db_helper
import styles

_dialog = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
if _dialog is None:
    raise RuntimeError("Fitur popup butuh Streamlit >= 1.34. Jalankan: pip install -U streamlit")

# Setelah menekan OK pada popup "berhasil", juri dikembalikan ke halaman utama (Dashboard).
# Ubah ke False bila ingin tetap berada di halaman yang sedang dibuka.
KEMBALI_KE_DASHBOARD = True
MENU_DASHBOARD = "🏠 Dashboard"

KRITERIA = [
    "1. Riset & Relevansi Industri",
    "2. Inovasi & Kualitas Solusi",
    "3. Pemanfaatan & Etika AI",
    "4. Presentasi & Komunikasi",
]

_JURI_CSS = """
<style>
    [data-testid="stDialog"] h1, [data-testid="stDialog"] h2,
    [data-testid="stDialog"] h3, [data-testid="stDialog"] h4,
    [data-testid="stDialog"] p, [data-testid="stDialog"] label p,
    [data-testid="stDialog"] li { color: #112250 !important; }
    [data-testid="stDialog"] .stButton > button {
        background-color: #112250 !important; color: #ffffff !important;
        border: none !important; border-radius: 10px !important;
        font-weight: 700 !important; width: 100% !important; padding: 10px 20px !important;
    }
    [data-testid="stDialog"] .stButton > button:hover {
        background-color: #1a3375 !important; color: #3BF07D !important;
    }
</style>
"""


# ============================ HELPER ============================
def _auth_kosong():
    return {"is_logged_in": False, "id_juri": "", "nama": "", "jenis": "", "instansi": ""}


def _ke_int(v, default=80):
    try:
        return max(0, min(100, int(float(v))))
    except (ValueError, TypeError):
        return default


def _hitung_rata(row):
    """Rata-rata = jumlah seluruh nilai / jumlah kriteria (4)."""
    vals = []
    for i in range(1, 5):
        v = pd.to_numeric(row.get(f"k{i}"), errors="coerce")
        vals.append(0 if pd.isna(v) else v)
    return round(sum(vals) / len(KRITERIA), 2)


def _input_nilai(prefix, defaults):
    """Input 4 kriteria (batas keras 0-100) + kartu rata-rata yang langsung berubah."""
    skor = []
    for i, (label, d) in enumerate(zip(KRITERIA, defaults), start=1):
        skor.append(int(st.number_input(
            f"{label} (60 - 100)",
            min_value=0, max_value=100, value=d, step=1, key=f"{prefix}_k{i}",
        )))
    total = sum(skor)
    rata = round(total / len(KRITERIA), 2)
    st.markdown(f"""
        <div style="background: white; border: 2px solid #3B507D; border-radius: 12px; padding: 14px; margin: 12px 0; text-align: center;">
            <div style="color: #6B7280; font-size: 0.82rem; font-weight: 600;">
                Total nilai {total} ÷ {len(KRITERIA)} kriteria
            </div>
            <div style="margin-top: 4px;">
                <span style="color: #6B7280; font-weight: 600;">Rata-rata / Skor Akhir:</span>
                <span style="font-size: 1.7rem; font-weight: 800; color: #112250; margin-left: 10px;">{rata:.2f}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    return skor, total, rata


def _simpan_nilai(spreadsheet_obj, juri_id, peserta_id, skor, catatan):
    """Simpan baru / perbarui penilaian (aplikasi + Sheet). Return dict hasil."""
    total = sum(skor)
    rata = round(total / len(skor), 2)
    ts = db_helper.timestamp_wib()

    df_pen = db_helper.ensure_cols(st.session_state.db_penilaian, "penilaian")
    mask_lama = ((df_pen["id_juri"].astype(str) == str(juri_id)) &
                 (df_pen["id_peserta"].astype(str) == str(peserta_id)))
    id_lama = str(df_pen[mask_lama]["id"].iloc[-1]) if mask_lama.any() else ""
    penilaian_id = id_lama or f"PEN-{int(time.time())}-{uuid.uuid4().hex[:4]}"

    baris = [penilaian_id, juri_id, peserta_id, *skor, rata, ts, catatan]
    row_dict = dict(zip(db_helper.SCHEMA["penilaian"], baris))
    st.session_state.db_penilaian = pd.concat(
        [df_pen[~mask_lama], pd.DataFrame([row_dict])], ignore_index=True
    )

    gagal, detail = False, ""
    if spreadsheet_obj:
        try:
            ws = db_helper.get_ws(spreadsheet_obj, "penilaian")
            semua = ws.get_all_values()
            baris_lama = [
                i for i, r in enumerate(semua[1:], start=2)
                if len(r) > 2 and r[1] == str(juri_id) and r[2] == str(peserta_id)
            ]
            if baris_lama:
                ws.update(values=[baris], range_name=f"A{baris_lama[0]}")
                for n in sorted(baris_lama[1:], reverse=True):
                    ws.delete_rows(n)
            else:
                ws.append_row(baris, value_input_option="USER_ENTERED")
        except Exception as e:
            gagal, detail = True, f"{type(e).__name__}: {e}"
            print(f"Gagal simpan penilaian ke Sheet: {detail}")
    else:
        gagal, detail = True, "Koneksi ke Google Sheet tidak tersedia."

    return {"total": total, "rata": rata, "waktu": ts, "gagal": gagal, "detail": detail}


def _simpan_favorit(spreadsheet_obj, juri_id, peserta_id):
    """Satu juri = satu favorit. Ganti pilihan lama bila ada. Return (gagal, detail)."""
    ts = db_helper.timestamp_wib()
    df_fav = db_helper.ensure_cols(st.session_state.db_favorit, "favorit")
    df_fav = df_fav[df_fav["id_juri"].astype(str) != str(juri_id)]
    baris = [ts, juri_id, peserta_id]
    st.session_state.db_favorit = pd.concat(
        [df_fav, pd.DataFrame([dict(zip(db_helper.SCHEMA["favorit"], baris))])], ignore_index=True
    )

    if not spreadsheet_obj:
        return True, "Koneksi ke Google Sheet tidak tersedia."
    try:
        # get_ws tidak peduli huruf besar/kecil (tab di Sheet bernama "Favorit")
        ws = db_helper.get_ws(spreadsheet_obj, "favorit")
        semua = ws.get_all_values()
        baris_lama = [
            i for i, r in enumerate(semua[1:], start=2)
            if len(r) > 1 and r[1] == str(juri_id)
        ]
        if baris_lama:
            ws.update(values=[baris], range_name=f"A{baris_lama[0]}")
            for n in sorted(baris_lama[1:], reverse=True):
                ws.delete_rows(n)
        else:
            ws.append_row(baris, value_input_option="USER_ENTERED")
        return False, ""
    except Exception as e:
        detail = f"{type(e).__name__}: {e}"
        print(f"Gagal simpan favorit ke Sheet: {detail}")
        return True, detail


def _popup(tipe, judul, pesan):
    st.session_state["popup"] = {"tipe": tipe, "judul": judul, "pesan": pesan}


def _popup_nilai(nama, hasil, diperbarui):
    aksi = "diperbarui" if diperbarui else "disimpan"
    if hasil["gagal"]:
        _popup("warning", "Belum masuk ke database",
               f"Nilai untuk **{nama}** {aksi} di aplikasi, tetapi **gagal ditulis ke Google Sheet**.\n\n`{hasil['detail']}`")
    else:
        _popup("success", f"Nilai berhasil {aksi}",
               f"Nilai untuk **{nama}** berhasil {aksi}.\n\n"
               f"- Total nilai: **{hasil['total']}**\n"
               f"- Rata-rata (skor akhir): **{hasil['rata']:.2f}**\n"
               f"- Waktu input: {hasil['waktu']} WIB")


# ============================ POPUP ============================
@_dialog("🔔 Notifikasi")
def dialog_notif(tipe, judul, pesan):
    ikon = {"success": "✅", "warning": "⚠️", "error": "❌"}.get(tipe, "ℹ️")
    st.markdown(f"### {ikon} {judul}")
    st.markdown(pesan)
    if st.button("OK", key="notif_ok"):
        if KEMBALI_KE_DASHBOARD and tipe == "success":
            st.session_state["menu_juri_state"] = MENU_DASHBOARD
        st.rerun()


@_dialog("✏️ Edit Nilai")
def dialog_edit_nilai(peserta_id, peserta_nama, spreadsheet_obj, juri_id):
    df_pen = db_helper.ensure_cols(st.session_state.db_penilaian, "penilaian")
    cur = df_pen[(df_pen["id_juri"].astype(str) == str(juri_id)) &
                 (df_pen["id_peserta"].astype(str) == str(peserta_id))]
    if cur.empty:
        st.error("Data penilaian tidak ditemukan.")
        return
    prev = cur.iloc[-1]

    st.markdown(f"#### {peserta_nama}")
    skor, total, rata = _input_nilai(
        f"edit_{peserta_id}", [_ke_int(prev.get(f"k{i}")) for i in range(1, 5)]
    )
    catatan = st.text_area(
        "Catatan Juri (opsional)", value=str(prev.get("catatan", "") or ""),
        max_chars=500, key=f"edit_catatan_{peserta_id}",
    )

    if st.button("💾 Simpan Perubahan", key=f"edit_simpan_{peserta_id}"):
        if not all(0 <= s <= 100 for s in skor):
            st.error("Nilai harus berada pada rentang 0 - 100.")
        else:
            hasil = _simpan_nilai(spreadsheet_obj, juri_id, peserta_id, skor, catatan.strip())
            _popup_nilai(peserta_nama, hasil, diperbarui=True)
            st.rerun()


# ============================ HALAMAN JURI ============================
def render_juri_portal():
    spreadsheet_obj, conn_err = db_helper.auto_connect_and_sync()
    tanggal_format = db_helper.get_current_date_indonesia()

    if "juri_auth" not in st.session_state:
        st.session_state.juri_auth = _auth_kosong()

    styles.inject(dark_stage=not st.session_state.juri_auth["is_logged_in"])

    # ==============================================================================
    # 1. HALAMAN LOGIN / CHECK-IN DEWAN JURI
    # ==============================================================================
    if not st.session_state.juri_auth["is_logged_in"]:

        st.markdown("""
        <style>
            .block-container { padding-top: 2rem !important; }

            /* Halaman login: sembunyikan sidebar kosong (menimpa aturan di styles.py) */
            html body section[data-testid="stSidebar"],
            html body section[data-testid="stSidebar"][aria-expanded="false"],
            html body [data-testid="stSidebarCollapsedControl"],
            html body [data-testid="stExpandSidebarButton"],
            html body #custom-hamburger,
            html body #nav-backdrop {
                display: none !important;
                width: 0 !important;
                min-width: 0 !important;
            }

            .login-brand { display:flex; align-items:center; gap:14px; margin-bottom:22px; }
            .login-brand .mark {
                width:54px; height:54px; border-radius:14px; font-size:28px;
                display:flex; align-items:center; justify-content:center;
                background:rgba(231,226,206,.12); border:1px solid rgba(231,226,206,.30);
            }
            .login-brand .name { font-size:.95rem; font-weight:800; letter-spacing:1.5px; color:#E7E2CE; }
            .login-title { font-size:2.5rem; font-weight:800; line-height:1.1; color:#ffffff; margin:0 0 12px 0; }
            .login-tagline { color:#BEB7A7; font-style:italic; font-size:.95rem; margin:0 0 30px 0; }
            .login-info {
                background:rgba(255,255,255,.06);
                border:1px solid rgba(231,226,206,.18);
                border-left:4px solid #E7E2CE;
                border-radius:14px; padding:22px 24px;
            }
            .login-info .t { color:#E7E2CE; font-weight:700; font-size:1rem; margin-bottom:6px; }
            .login-info .d { color:#CFCAB8; font-size:.88rem; line-height:1.65; }

            .login-head { text-align:center; margin-bottom:20px; }
            .login-head .h { color:#112250 !important; font-size:1.7rem; font-weight:800; margin:0 0 6px 0; }
            .login-head .s { color:#5B6B8C !important; font-size:.9rem; margin:0; }
            .login-foot {
                text-align:center; margin-top:16px; padding-top:12px;
                border-top:1px solid #E7E2CE; color:#8A93A8; font-size:.72rem; letter-spacing:.3px;
            }

            /* Styling Kotak Form Putih Solid */
            [data-testid="stForm"] {
                background: #ffffff !important;
                border: 1px solid #E7E2CE !important;
                border-radius: 20px !important;
                padding: 35px 30px !important;
                box-shadow: 0 15px 35px rgba(17, 34, 80, 0.15) !important;
                width: 100% !important;
            }

            /* Warna Label Input di Dalam Form */
            [data-testid="stForm"] label, 
            [data-testid="stForm"] label p {
                color: #112250 !important;
                font-weight: 700 !important;
                font-size: 0.88rem !important;
            }

            /* Field Input & Selectbox */
            [data-testid="stForm"] [data-baseweb="input"],
            [data-testid="stForm"] [data-baseweb="select"] > div {
                background:#F5F4F0 !important;
                border:1px solid #E7E2CE !important;
                border-radius:10px !important;
            }
            [data-testid="stForm"] [data-baseweb="input"]:focus-within,
            [data-testid="stForm"] [data-baseweb="select"] > div:focus-within {
                border-color:#112250 !important;
            }
            [data-testid="stForm"] input,
            [data-testid="stForm"] [data-baseweb="select"] * { color:#112250 !important; }
            [data-testid="stForm"] input::placeholder { color:#8A93A8 !important; }

            /* Tombol Submit Login Juri */
            [data-testid="stForm"] .stButton > button {
                background-color: #112250 !important;
                color: #ffffff !important;
                border-radius: 12px !important;
                padding: 12px 20px !important;
                font-weight: 700 !important;
                font-size: 1rem !important;
                border: none !important;
                box-shadow: 0 4px 12px rgba(17, 34, 80, 0.25) !important;
                margin-top: 10px !important;
                transition: all 0.2s ease-in-out !important;
            }
            [data-testid="stForm"] .stButton > button:hover {
                background-color: #1a3375 !important;
                color: #3BF07D !important;
                box-shadow: 0 6px 16px rgba(17, 34, 80, 0.35) !important;
            }
        </style>
        """, unsafe_allow_html=True)

        if conn_err:
            st.error(f"❌ Google Sheet bermasalah: {conn_err}")

        col_banner, col_form = st.columns([1.15, 1], gap="large", vertical_alignment="center")

        with col_banner:
            st.markdown("""
                <div style="padding: 8px 12px 8px 0;">
                    <div class="login-brand">
                        <div class="mark">🏆</div>
                        <div class="name">FINAL PROJECT PBK DIGITAL AI</div>
                    </div>
                    <div class="login-title">AI WORK EXHIBITION</div>
                    <div class="login-tagline">"Innovating with AI, Building a Smarter Future"</div>
                    <div class="login-info">
                        <div class="t">Portal Penilaian Resmi Dewan Juri</div>
                        <div class="d">Masukkan nama lengkap dan pilih instansi Anda untuk mulai memberikan
                        penilaian yang objektif dan terintegrasi secara realtime.</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col_form:
            # Pilihan dropdown diisi oleh admin (sheet "jenis")
            df_jenis = db_helper.ensure_cols(st.session_state.get("db_jenis"), "jenis")
            daftar_jenis = sorted({str(x).strip() for x in df_jenis["nama_jenis"] if str(x).strip()})
            PLACEHOLDER = "-- Pilih Instansi dari Daftar --"

            with st.form("form_login_juri"):
                st.markdown("""
                    <div class="login-head">
                        <div class="h">Selamat Datang</div>
                        <p class="s">Silakan masukkan nama dan pilih instansi Anda</p>
                    </div>
                """, unsafe_allow_html=True)

                input_nama_juri = st.text_input("Nama Lengkap*", placeholder="Contoh: Ahmad Subarjo")
                jenis_dipilih = st.selectbox("Pilih Instansi Asal*", options=[PLACEHOLDER] + daftar_jenis)
                nama_instansi_input = st.text_input(
                    "Nama Instansi*", placeholder="Contoh: Dinas Pendidikan Kota Madiun"
                )

                if not daftar_jenis:
                    st.info("Pilihan instansi belum tersedia. Silakan hubungi administrator.")

                _, btn_col, _ = st.columns([0.2, 2, 0.2])
                with btn_col:
                    btn_masuk = st.form_submit_button(
                        "Masuk ke Sistem Penilaian",
                        use_container_width=True,
                        disabled=not daftar_jenis,
                    )

                st.markdown('<div class="login-foot">FINAL PROJECT PBK DIGITAL AI WORK EXHIBITION</div>',
                            unsafe_allow_html=True)

                if btn_masuk:
                    nama_final = input_nama_juri.strip()
                    instansi_nama = nama_instansi_input.strip()

                    if not nama_final:
                        st.error("Nama lengkap juri wajib diisi!")
                    elif jenis_dipilih == PLACEHOLDER:
                        st.error("Silakan pilih instansi asal dari daftar.")
                    elif not instansi_nama:
                        st.error("Nama instansi wajib diisi!")
                    else:
                        # Juri dikenali dari kombinasi nama + instansi asal + nama instansi
                        df_juri = db_helper.ensure_cols(st.session_state.db_juri, "juri")
                        existing = df_juri[
                            (df_juri["nama_juri"].astype(str).str.lower() == nama_final.lower())
                            & (df_juri["jenis_instansi"].astype(str).str.lower() == jenis_dipilih.lower())
                            & (df_juri["nama_instansi"].astype(str).str.lower() == instansi_nama.lower())
                        ]

                        if not existing.empty:
                            juri_id_final = existing.iloc[0]["id_juri"]
                        else:
                            juri_id_final = db_helper.next_id(df_juri, "JUR", "id_juri")
                            new_row = {
                                "id_juri": juri_id_final,
                                "nama_juri": nama_final,
                                "jenis_instansi": jenis_dipilih,
                                "nama_instansi": instansi_nama,
                            }
                            st.session_state.db_juri = pd.concat(
                                [df_juri, pd.DataFrame([new_row])], ignore_index=True
                            )
                            ok, serr = db_helper.safe_append(
                                spreadsheet_obj, "juri",
                                [juri_id_final, nama_final, jenis_dipilih, instansi_nama]
                            )
                            if not ok:
                                st.warning(f"Data juri gagal ditulis ke Google Sheet: {serr}")

                        st.session_state.juri_auth = {
                            "is_logged_in": True,
                            "id_juri": juri_id_final,
                            "nama": nama_final,
                            "jenis": jenis_dipilih,
                            "instansi": instansi_nama,
                        }
                        st.session_state["menu_juri_state"] = MENU_DASHBOARD
                        st.rerun()

    # ==============================================================================
    # 2. DASHBOARD & MENU UTAMA JURI SETELAH LOGIN
    # ==============================================================================
    else:
        st.markdown(_JURI_CSS, unsafe_allow_html=True)

        auth = st.session_state.juri_auth
        juri_id_aktif = auth["id_juri"]
        nama_juri_aktif = auth["nama"]
        instansi_label = f"{auth['jenis']} · {auth['instansi']}" if auth.get("jenis") else auth.get("instansi", "")

        df_pen_all = db_helper.ensure_cols(st.session_state.db_penilaian, "penilaian")
        df_pen_saya = df_pen_all[df_pen_all["id_juri"].astype(str) == str(juri_id_aktif)]

        total_peserta_count = len(st.session_state.db_peserta)
        dinilai_juri_ini = df_pen_saya["id_peserta"].nunique() if not df_pen_saya.empty else 0
        sisa_peserta = max(0, total_peserta_count - dinilai_juri_ini)
        persen_progress = int(dinilai_juri_ini / total_peserta_count * 100) if total_peserta_count > 0 else 0

        with st.sidebar:
            st.markdown(f"""
                <div style="background: white; border: 1px solid #E7E2CE; border-radius: 12px; padding: 16px; margin-bottom: 20px; text-align: center; color: #112250;">
                    <div style="font-size: 32px;">👨‍⚖️</div>
                    <div style="font-weight: 800; font-size: 1.05rem; color: #112250; margin-top: 4px;">{nama_juri_aktif}</div>
                    <div style="font-size: 0.82rem; color: #6B7280; font-weight: 600;">{instansi_label}</div>
                </div>
            """, unsafe_allow_html=True)

            menu_juri = styles.sidebar_menu(
                [MENU_DASHBOARD, "📝 Penilaian Peserta", "⭐ Peserta Favorit",
                 "📋 Riwayat Penilaian", "🚪 Logout"],
                key="menu_juri_state",
                divider_before="🚪 Logout",
            )

            if menu_juri == "🚪 Logout":
                st.session_state.juri_auth = _auth_kosong()
                st.session_state["menu_juri_state"] = MENU_DASHBOARD
                st.rerun()

        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #112250 0%, #3B507D 100%); border-radius: 16px; padding: 24px 30px; color: white; margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="color: #E7E2CE; font-size: 1.2rem; font-weight: 800;">Dewan Juri Portal</div>
                    <div style="font-size: 0.9rem; color: rgba(255,255,255,0.85); margin-top: 2px;">Selamat datang, {nama_juri_aktif}. Berikut informasi penilaian Anda.</div>
                </div>
                <div style="background: rgba(255,255,255,0.12); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem;">
                    📅 {tanggal_format}
                </div>
            </div>
        """, unsafe_allow_html=True)

        if conn_err:
            st.error(f"❌ Google Sheet bermasalah: {conn_err}")

        # Popup notifikasi (dibuka sekali, lalu dihapus dari session)
        popup = st.session_state.pop("popup", None)
        if popup:
            dialog_notif(popup["tipe"], popup["judul"], popup["pesan"])

        # ---------------- DASHBOARD ----------------
        if menu_juri == MENU_DASHBOARD:
            st.markdown("### 🏠 Dashboard Penilaian")

            c_m1, c_m2, c_m3 = st.columns(3)
            with c_m1:
                st.markdown(f"""
                    <div class="metric-card-juri">
                        <div style="font-size: 28px;">👥</div>
                        <h2 style="color: #112250; margin: 4px 0;">{total_peserta_count}</h2>
                        <p style="color: #666; font-size: 0.85rem; margin: 0;">Total Peserta</p>
                    </div>
                """, unsafe_allow_html=True)
            with c_m2:
                st.markdown(f"""
                    <div class="metric-card-juri">
                        <div style="font-size: 28px;">✅</div>
                        <h2 style="color: #0b7337; margin: 4px 0;">{dinilai_juri_ini}</h2>
                        <p style="color: #666; font-size: 0.85rem; margin: 0;">Sudah Dinilai</p>
                    </div>
                """, unsafe_allow_html=True)
            with c_m3:
                st.markdown(f"""
                    <div class="metric-card-juri">
                        <div style="font-size: 28px;">⏳</div>
                        <h2 style="color: #d97706; margin: 4px 0;">{sisa_peserta}</h2>
                        <p style="color: #666; font-size: 0.85rem; margin: 0;">Belum Dinilai</p>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
                <div class="content-card">
                    <h4 style="color: #112250; margin-top: 0;">Progres Penilaian</h4>
                    <p style="color: #666; font-size: 0.9rem;">{dinilai_juri_ini} dari {total_peserta_count} peserta telah dinilai ({persen_progress}%)</p>
                    <div style="background: #E5E7EB; border-radius: 10px; height: 12px; width: 100%; overflow: hidden;">
                        <div style="background: #3B507D; width: {persen_progress}%; height: 100%; border-radius: 10px;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # ---------------- PENILAIAN PESERTA ----------------
        elif menu_juri == "📝 Penilaian Peserta":
            st.markdown("### 📝 Form Penilaian Karya Peserta")
            st.markdown("<p style='color: #666; font-size: 0.9rem;'>Berikan nilai pada setiap kriteria dengan rentang 60 - 100. Rata-rata dihitung dari jumlah seluruh nilai dibagi jumlah kriteria.</p>", unsafe_allow_html=True)

            df_peserta = st.session_state.db_peserta
            if df_peserta.empty:
                st.warning("⚠️ Belum ada data peserta yang dimasukkan oleh Administrator.")
            else:
                sudah_dinilai = set(df_pen_saya["id_peserta"].astype(str))

                label_map = {}
                for _, row in df_peserta.iterrows():
                    pid = row["id_peserta"]
                    status = "✅ (Sudah Dinilai)" if str(pid) in sudah_dinilai else "⏳ (Belum Dinilai)"
                    label_map[pid] = f"{row['nama_peserta']} [{pid}] {status}"

                # Opsi memakai ID (stabil) agar pilihan tidak loncat ke atas setelah menyimpan
                peserta_id = st.selectbox(
                    "Pilih Peserta:", options=list(label_map.keys()),
                    format_func=lambda x: label_map[x],
                )
                peserta_nama = df_peserta.loc[df_peserta["id_peserta"] == peserta_id, "nama_peserta"].iloc[0]

                st.markdown(f"""
                    <div style="padding-top: 10px;">
                        <span style="background: #112250; color: #3BF07D; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">Kandidat Terpilih</span>
                        <h2 style="color: #112250; margin: 10px 0 4px 0;">{peserta_nama}</h2>
                        <p style="color: #666; font-size: 0.9rem;">ID Peserta: <b>{peserta_id}</b></p>
                    </div>
                """, unsafe_allow_html=True)

                default_scores = [80] * 4
                default_catatan = ""
                sudah_pernah = str(peserta_id) in sudah_dinilai
                if sudah_pernah:
                    prev = df_pen_saya[df_pen_saya["id_peserta"].astype(str) == str(peserta_id)].iloc[-1]
                    default_scores = [_ke_int(prev.get(f"k{i}")) for i in range(1, 5)]
                    default_catatan = str(prev.get("catatan", "") or "")
                    st.info("ℹ️ Anda sudah pernah menilai peserta ini. Menyimpan lagi akan memperbarui nilai Anda.")

                st.markdown("<h4 style='margin-top: 14px;'>4 Kriteria Penilaian (Rentang 60 - 100)</h4>", unsafe_allow_html=True)
                with st.container(border=True):
                    skor, total, rata = _input_nilai(f"nilai_{peserta_id}", default_scores)
                    catatan = st.text_area(
                        "Catatan Juri (opsional)",
                        value=default_catatan,
                        placeholder="Tulis komentar atau masukan untuk peserta ini...",
                        max_chars=500,
                        key=f"catatan_{peserta_id}",
                    )

                    if st.button("💾 Simpan Nilai ➔", key=f"simpan_nilai_{peserta_id}"):
                        if not all(0 <= s <= 100 for s in skor):
                            st.error("Nilai harus berada pada rentang 0 - 100.")
                        else:
                            hasil = _simpan_nilai(spreadsheet_obj, juri_id_aktif, peserta_id, skor, catatan.strip())
                            _popup_nilai(peserta_nama, hasil, diperbarui=sudah_pernah)
                            st.rerun()

        # ---------------- PESERTA FAVORIT ----------------
        elif menu_juri == "⭐ Peserta Favorit":
            st.markdown("### ⭐ Peserta Favorit Pilihan Anda")
            st.markdown("<p style='color: #666; font-size: 0.9rem;'>Pilih 1 peserta favorit Anda dari daftar berikut. Pilihan ini akan menjadi bagian dari hasil akhir penilaian.</p>", unsafe_allow_html=True)

            df_peserta = st.session_state.db_peserta
            if df_peserta.empty:
                st.warning("⚠️ Belum ada data peserta yang tersedia.")
            else:
                df_fav = db_helper.ensure_cols(st.session_state.db_favorit, "favorit")
                fav_saya = df_fav[df_fav["id_juri"].astype(str) == str(juri_id_aktif)]
                current_fav_id = fav_saya.iloc[-1]["id_peserta"] if not fav_saya.empty else None

                list_id = df_peserta["id_peserta"].tolist()
                label_map = {
                    row["id_peserta"]: f"{row['nama_peserta']} [{row['id_peserta']}]"
                    for _, row in df_peserta.iterrows()
                }
                idx_def = list_id.index(current_fav_id) if current_fav_id in list_id else 0

                if current_fav_id in label_map:
                    st.info(f"Favorit Anda saat ini: **{label_map[current_fav_id]}**")

                with st.form("form_voting_favorit"):
                    pilih_fav_id = st.radio(
                        "Daftar Kandidat Peserta:",
                        options=list_id,
                        index=idx_def,
                        format_func=lambda x: label_map[x],
                    )
                    st.markdown("<br>", unsafe_allow_html=True)

                    if st.form_submit_button("⭐ Simpan Pilihan Favorit"):
                        gagal, detail = _simpan_favorit(spreadsheet_obj, juri_id_aktif, pilih_fav_id)
                        if gagal:
                            _popup("warning", "Belum masuk ke database",
                                   f"Pilihan favorit tersimpan di aplikasi, tetapi **gagal ditulis ke Google Sheet**.\n\n`{detail}`")
                        else:
                            _popup("success", "Favorit berhasil disimpan",
                                   f"Peserta favorit Anda: **{label_map[pilih_fav_id]}**.")
                        st.rerun()

        # ---------------- RIWAYAT + EDIT NILAI ----------------
        elif menu_juri == "📋 Riwayat Penilaian":
            st.markdown(f"### 📋 Riwayat Penilaian oleh {nama_juri_aktif}")
            st.caption("Klik **Edit** untuk mengubah nilai yang sudah Anda kirim.")

            if df_pen_saya.empty:
                st.info("Anda belum menilai peserta manapun.")
            else:
                df_peserta = st.session_state.db_peserta
                nama_map = dict(zip(df_peserta["id_peserta"].astype(str), df_peserta["nama_peserta"]))

                lebar = [0.4, 2.6, 0.7, 0.7, 0.7, 0.7, 1.0, 1.0]
                head = st.columns(lebar, vertical_alignment="center")
                for kolom, judul in zip(head, ["No", "Peserta", "K1", "K2", "K3", "K4", "Rata-rata", ""]):
                    kolom.markdown(f"**{judul}**" if judul else "")

                for no, (_, r) in enumerate(df_pen_saya.iterrows(), start=1):
                    pid = str(r["id_peserta"])
                    nama_p = nama_map.get(pid, pid)
                    with st.container(border=True):
                        c = st.columns(lebar, vertical_alignment="center")
                        c[0].write(no)
                        c[1].markdown(
                            f"**{nama_p}**  \n<span style='color:#6B7280; font-size:.78rem;'>{r['waktu_input']} WIB</span>",
                            unsafe_allow_html=True,
                        )
                        for i in range(1, 5):
                            c[1 + i].write(r.get(f"k{i}", "-"))
                        c[6].write(f"**{_hitung_rata(r):.2f}**")
                        if c[7].button("✏️ Edit", key=f"edit_nilai_{pid}"):
                            dialog_edit_nilai(pid, nama_p, spreadsheet_obj, juri_id_aktif)

    st.markdown("""
        <div style="text-align: center; margin-top: 50px; padding: 20px; border-top: 1px solid #E7E2CE; color: #BEB7A7; font-size: 0.8rem;">
            FINAL PROJECT DIGITAL AI WORK EXHIBITION • Portal Dewan Juri
        </div>
    """, unsafe_allow_html=True)