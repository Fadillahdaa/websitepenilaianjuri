import io
import base64
import streamlit as st
import pandas as pd
from PIL import Image, ImageOps
import db_helper
import styles

_dialog = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
if _dialog is None:
    raise RuntimeError("Fitur popup butuh Streamlit >= 1.34. Jalankan: pip install -U streamlit")

_ADMIN_CSS = """
<style>
    .stApp {
        background-color: #F5F4F0;
    }
    
    /* Layout Split Screen Utama */
    .split-login-wrapper {
        display: flex;
        flex-direction: row;
        width: 100%;
        min-height: 82vh;
        background: #ffffff;
        border-radius: 24px;
        overflow: hidden;
        margin-top: 2vh;
        box-shadow: 0 20px 40px rgba(17, 34, 80, 0.08);
        border: 1px solid #E7E2CE;
    }

    /* Bagian Kiri (Banner Gradasi) */
    .login-left-banner {
        flex: 1.2;
        background: linear-gradient(135deg, #112250 0%, #3B507D 50%, #3BF07D 100%);
        padding: 60px 50px;
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .login-left-banner h1 {
        color: #ffffff !important;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 16px;
        letter-spacing: -0.5px;
    }

    .login-left-banner p {
        color: #E7E2CE;
        font-size: 1rem;
        line-height: 1.6;
        max-width: 450px;
    }

    /* Bagian Kanan (Area Putih) */
    .login-right-container {
        flex: 1;
        background: #ffffff;
        padding: 50px 45px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    .login-box-content {
        width: 100%;
        max-width: 380px;
    }

    .login-box-title {
        color: #112250;
        font-size: 1.75rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 4px;
    }
    
    .login-box-subtitle {
        color: #8A93A8;
        font-size: 0.82rem;
        text-align: center;
        margin-bottom: 24px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Membungkus st.form agar menyatu rapi di dalam kotak kanan */
    [data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
        box-shadow: none !important;
        background: transparent !important;
        width: 100% !important;
    }

    [data-testid="stForm"] label p {
        color: #112250 !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
    }
    
    /* Tombol Login */
    [data-testid="stForm"] .stButton > button {
        background-color: #112250 !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        padding: 12px 20px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(17, 34, 80, 0.25) !important;
        margin-top: 15px !important;
        width: 100% !important;
        transition: all 0.2s ease-in-out !important;
    }
    [data-testid="stForm"] .stButton > button:hover {
        background-color: #1a3375 !important;
        color: #3BF07D !important;
        box-shadow: 0 6px 16px rgba(17, 34, 80, 0.35) !important;
    }

    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff; border-color: #E7E2CE !important; border-radius: 14px !important;
    }
    [data-testid="stMain"] div[class*="st-key-edit_"] .stButton > button,
    [data-testid="stMain"] div[class*="st-key-del_"] .stButton > button {
        padding: 6px 10px !important; font-size: .85rem !important;
    }
    [data-testid="stMain"] div[class*="st-key-del_"] .stButton > button {
        background-color: #dc3545 !important; color: #ffffff !important;
    }
    [data-testid="stMain"] div[class*="st-key-del_"] .stButton > button:hover { background-color: #b02a37 !important; }

    div[class*="st-key-confirm_yes"] .stButton > button {
        background-color: #dc3545 !important; color: #ffffff !important;
        border: none !important; font-weight: 700 !important; width: 100% !important; border-radius: 10px !important;
    }
    div[class*="st-key-confirm_no"] .stButton > button {
        background-color: #E7E2CE !important; color: #112250 !important;
        border: 1px solid #BEB7A7 !important; font-weight: 700 !important; width: 100% !important; border-radius: 10px !important;
    }

    [data-testid="stDialog"] label p,
    [data-testid="stDialog"] h1, [data-testid="stDialog"] h4 { color: #112250 !important; }
    [data-testid="stDialog"] [data-testid="stForm"] { border: none !important; box-shadow: none !important; padding: 0 !important; }

    @media(max-width: 768px) {
        .split-login-wrapper { flex-direction: column; }
        .login-left-banner { padding: 30px 20px; text-align: center; }
        .login-right-container { padding: 30px 20px; }
    }
</style>
"""


# ============================ HELPER ============================
def _exact_cells(ws, value, col):
    return [c for c in ws.findall(str(value), in_column=col) if c.value == str(value)]


def _show_flash(key):
    flash = st.session_state.pop(key, None)
    if flash:
        (st.success if flash[0] == "success" else st.warning)(flash[1])


@_dialog("✏️ Edit Peserta")
def dialog_edit_peserta(id_peserta, spreadsheet_obj):
    df = st.session_state.db_peserta
    cur = df[df["id_peserta"] == id_peserta]
    if cur.empty:
        st.error("Data peserta tidak ditemukan.")
        return
    cur = cur.iloc[0]

    with st.form(f"form_edit_{id_peserta}"):
        nama_baru = st.text_input("Nama Peserta / Proyek*", value=cur["nama_peserta"])
        simpan = st.form_submit_button("💾 Simpan Perubahan")

    if simpan:
        nama_baru = nama_baru.strip()
        if not nama_baru:
            st.error("Nama peserta wajib diisi!")
            return
        duplikat = df[(df["nama_peserta"].str.lower() == nama_baru.lower()) & (df["id_peserta"] != id_peserta)]
        if not duplikat.empty:
            st.error("Nama tersebut sudah dipakai peserta lain.")
            return

        idx = df.index[df["id_peserta"] == id_peserta][0]
        st.session_state.db_peserta.at[idx, "nama_peserta"] = nama_baru

        gagal, detail = False, ""
        if spreadsheet_obj:
            try:
                ws = db_helper.get_ws(spreadsheet_obj, "peserta")
                cells = _exact_cells(ws, id_peserta, 1)
                if cells:
                    ws.update_cell(cells[0].row, 2, nama_baru)
                else:
                    gagal, detail = True, "ID peserta tidak ditemukan di Sheet."
            except Exception as e:
                gagal, detail = True, f"{type(e).__name__}: {e}"
        else:
            gagal, detail = True, "Koneksi ke Google Sheet tidak tersedia."

        st.session_state["flash_peserta"] = (
            ("warning", f"Peserta diperbarui di aplikasi, tetapi gagal ke Google Sheet. ({detail})")
            if gagal else ("success", f"Data peserta **{nama_baru}** berhasil diperbarui.")
        )
        st.rerun()


@_dialog("🗑️ Hapus Peserta")
def dialog_hapus_peserta(id_peserta, nama, spreadsheet_obj):
    st.markdown(f"#### Yakin hapus peserta **{nama}**?")
    c1, c2 = st.columns(2)
    with c1:
        ya = st.button("Ya, hapus", key="confirm_yes")
    with c2:
        tidak = st.button("Tidak", key="confirm_no")

    if tidak:
        st.rerun()

    if ya:
        df = st.session_state.db_peserta
        st.session_state.db_peserta = df[df["id_peserta"] != id_peserta].reset_index(drop=True)

        gagal, detail = False, ""
        if spreadsheet_obj:
            try:
                ws = db_helper.get_ws(spreadsheet_obj, "peserta")
                for r in sorted({c.row for c in _exact_cells(ws, id_peserta, 1)}, reverse=True):
                    ws.delete_rows(r)
            except Exception as e:
                gagal, detail = True, f"{type(e).__name__}: {e}"
        else:
            gagal, detail = True, "Koneksi ke Google Sheet tidak tersedia."

        st.session_state["flash_peserta"] = (
            ("warning", f"Peserta dihapus dari aplikasi, tetapi gagal menghapus di Google Sheet. ({detail})")
            if gagal else ("success", f"Peserta **{nama}** berhasil dihapus.")
        )
        st.rerun()


# ============================ HALAMAN ADMIN ============================
def render_admin_portal():
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    # ================= FORM LOGIN ADMIN (LAYOUT SPLIT-SCREEN) =================
    if not st.session_state.admin_logged_in:
        styles.inject(dark_stage=True)
        st.markdown(_ADMIN_CSS, unsafe_allow_html=True)
        
        # Membuka pembungkus utama split-screen
        st.markdown("""
            <div class="split-login-wrapper">
                <div class="login-left-banner">
                    <div style="font-size: 3rem; margin-bottom: 12px;">👋</div>
                    <h1>Selamat Datang Admin</h1>
                    <p>Silakan masuk menggunakan kredensial akun administrator Anda untuk mengelola seluruh data peserta, instansi, serta memantau hasil penilaian pameran secara real-time.</p>
                </div>
                <div class="login-right-container">
                    <div class="login-box-content">
        """, unsafe_allow_html=True)

        # Form login membungkus judul, input, dan tombol secara utuh di dalam kotak kanan
        with st.form("form_login_admin"):
            st.markdown("""
                <div class="login-box-title">ADMIN LOGIN</div>
                <div class="login-box-subtitle">PORTAL MANAJEMEN EKSIBISI</div>
            """, unsafe_allow_html=True)

            username_input = st.text_input("Username", placeholder="Masukkan username admin")
            password_input = st.text_input("Password", type="password", placeholder="Masukkan password admin")
            btn_login = st.form_submit_button("Masuk Panel Admin ➔")

            if btn_login:
                if username_input == "superadmin" and password_input == "adminsuper*3#12":
                    st.session_state.admin_logged_in = True
                    st.success("Login berhasil! Memuat sistem...")
                    st.rerun()
                else:
                    st.error("Username atau password salah!")

        # Menutup pembungkus kontainer kanan dan wrapper utama
        st.markdown("""
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        return

    # ================= PANEL UTAMA ADMIN SETELAH LOGIN =================
    styles.inject()
    st.markdown(_ADMIN_CSS, unsafe_allow_html=True)

    spreadsheet_obj, conn_err = db_helper.auto_connect_and_sync()
    tanggal_format = db_helper.get_current_date_indonesia()

    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 10px 0 20px 0; border-bottom: 1px solid #3B507D; margin-bottom: 10px;">
                <div style="font-size: 28px; margin-bottom: 4px;">🏆</div>
                <div style="font-size: 0.78rem; font-weight: 800; color: #E7E2CE; letter-spacing: 1px;">FINAL PROJECT PBK</div>
                <div style="font-size: 0.65rem; color: #BEB7A7; font-weight: 600;">DIGITAL AI WORK EXHIBITION</div>
            </div>
        """, unsafe_allow_html=True)

        if spreadsheet_obj:
            st.markdown(f"""
                <div style="margin: 10px 0 16px 0; padding: 10px 12px; background: rgba(59,240,125,0.12); border: 1px solid #3B507D; border-radius: 8px; font-size: 0.75rem; color: #E7E2CE; font-weight: 600; text-align: center;">
                    🟢 <b>DB Tersambung</b><br>{spreadsheet_obj.title}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="margin: 10px 0 16px 0; padding: 10px 12px; background: rgba(220,53,69,0.15); border: 1px solid #dc3545; border-radius: 8px; font-size: 0.75rem; color: #E7E2CE; font-weight: 600; text-align: center;">
                    🔴 <b>DB Tidak Tersambung</b>
                </div>
            """, unsafe_allow_html=True)

        menu_admin = styles.sidebar_menu(
            ["📊 Dashboard", "📁 Kelola Peserta", "👥 Kelola Instansi",
             "🏆 Ranking & Nilai", "⭐ Peserta Favorit", "📑 Database Google Sheet", "🚪 Logout Admin"],
            key="menu_admin_state",
        )
        
        if menu_admin == "🚪 Logout Admin":
            st.session_state.admin_logged_in = False
            st.session_state["menu_admin_state"] = "📊 Dashboard"
            st.rerun()

        st.markdown("<br><hr style='border-color: #3B507D; opacity: 0.4;'>", unsafe_allow_html=True)
        st.caption("📍 URL Akses: `/admin_masuk`")

    st.markdown(f"""
        <div class="brand-header-admin">
            <div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #ffffff;">ADMIN CONTROL PANEL</div>
                <div style="font-size: 0.9rem; color: #E7E2CE; margin-top: 4px;">Kelola Data Peserta, Instansi Asal, & Pantau Seluruh Nilai Pameran</div>
            </div>
            <div style="text-align: right; font-size: 0.85rem; background: rgba(255,255,255,0.1); padding: 6px 14px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.15);">
                📅 {tanggal_format}
            </div>
        </div>
    """, unsafe_allow_html=True)

    if conn_err:
        st.error(f"❌ Google Sheet bermasalah: {conn_err}")

    # ---------------- 1. DASHBOARD ----------------
    if menu_admin == "📊 Dashboard":
        st.markdown("#### 📊 Ringkasan Kegiatan Pameran")
        total_peserta = len(st.session_state.db_peserta)
        total_juri = len(st.session_state.db_juri)
        total_penilaian = len(st.session_state.db_penilaian)

        c1, c2, c3 = st.columns(3)
        for col, angka, label in [(c1, total_peserta, "Total Peserta"),
                                 (c2, total_juri, "Juri Terdaftar"),
                                 (c3, total_penilaian, "Penilaian Masuk")]:
            with col:
                st.markdown(f"""<div class="metric-card"><h2 style="color:#112250; font-size: 2rem; margin:0;">{angka}</h2><p style="color:#6B7280; font-size:0.9rem; font-weight:600; margin:6px 0 0 0;">{label}</p></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_rank, col_fav = st.columns([1.5, 1])
        df_penilaian = st.session_state.db_penilaian.copy()
        df_peserta = st.session_state.db_peserta

        with col_rank:
            st.markdown("#### 🏆 Top 3 Ranking Sementara")
            if not df_penilaian.empty and not df_peserta.empty and "id_peserta" in df_penilaian.columns:
                k_cols = [c for c in ["k1", "k2", "k3", "k4"] if c in df_penilaian.columns]
                if k_cols:
                    for col in k_cols:
                        df_penilaian[col] = pd.to_numeric(df_penilaian[col], errors="coerce").fillna(0)
                    df_penilaian["nilai_rata"] = df_penilaian[k_cols].mean(axis=1)
                    df_rank = df_penilaian.groupby("id_peserta")["nilai_rata"].mean().reset_index()
                    df_rank = df_rank.merge(df_peserta[["id_peserta", "nama_peserta"]], on="id_peserta", how="left")
                    df_rank = df_rank[["nama_peserta", "nilai_rata"]]
                    df_rank.columns = ["Nama Peserta", "Nilai Rata-rata"]
                    df_rank = df_rank.sort_values("Nilai Rata-rata", ascending=False).reset_index(drop=True)
                    df_rank.index = df_rank.index + 1
                    st.dataframe(df_rank.head(3).style.format({"Nilai Rata-rata": "{:.2f}"}), use_container_width=True)
            else:
                st.info("Belum ada data penilaian.")

        with col_fav:
            st.markdown("#### ⭐ Peserta Favorit Teratas")
            df_fav = st.session_state.db_favorit
            if not df_fav.empty and not df_peserta.empty and "id_peserta" in df_fav.columns:
                fav_counts = df_fav["id_peserta"].value_counts().reset_index()
                fav_counts.columns = ["id_peserta", "Total Vote"]
                fav_counts = fav_counts.merge(df_peserta[["id_peserta", "nama_peserta"]], on="id_peserta", how="left")
                top_name = fav_counts.iloc[0]["nama_peserta"]
                top_votes = fav_counts.iloc[0]["Total Vote"]
                st.markdown(f"""
                    <div class="content-card" style="text-align: center; border-top: 4px solid #3B507D;">
                        <div style="font-size: 38px; margin-bottom: 6px;">🌟</div>
                        <h3 style="color: #112250; margin: 0; font-size: 1.25rem;">{top_name}</h3>
                        <p style="color: #3B507D; font-weight: 700; margin-top: 8px; font-size: 0.9rem;">Terpilih dari {top_votes} Vote Juri</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Belum ada vote favorit.")

    # ---------------- 2. KELOLA PESERTA ----------------
    elif menu_admin == "📁 Kelola Peserta":
        st.markdown("#### 📁 Kelola Data Peserta")
        _show_flash("flash_peserta")

        with st.expander("➕ Tambah Peserta Baru", expanded=False):
            with st.form("form_tambah_peserta", clear_on_submit=True):
                p_nama = st.text_input("Nama Lengkap Peserta / Proyek*")

                if st.form_submit_button("Simpan Peserta ➔"):
                    df_p = st.session_state.db_peserta
                    if not p_nama.strip():
                        st.error("Nama peserta wajib diisi!")
                    elif not df_p.empty and p_nama.strip().lower() in df_p["nama_peserta"].str.lower().tolist():
                        st.error("Peserta dengan nama tersebut sudah terdaftar.")
                    else:
                        new_id = db_helper.next_id(df_p, "PST", "id_peserta")
                        new_row = {
                            "id_peserta": new_id,
                            "nama_peserta": p_nama.strip(),
                            "status": "Belum Lengkap",
                        }
                        st.session_state.db_peserta = pd.concat([df_p, pd.DataFrame([new_row])], ignore_index=True)

                        ok, serr = db_helper.safe_append(
                            spreadsheet_obj, "peserta", [new_id, p_nama.strip(), "Belum Lengkap"]
                        )
                        st.session_state["flash_peserta"] = (
                            ("success", f"Peserta **{p_nama.strip()}** berhasil ditambahkan!") if ok
                            else ("warning", f"Peserta **{p_nama.strip()}** tersimpan di aplikasi, tetapi gagal menulis ke Google Sheet. ({serr})")
                        )
                        st.rerun()

        st.markdown("##### Daftar Peserta Terdaftar")
        df_p = st.session_state.db_peserta
        if df_p.empty:
            st.info("Belum ada data peserta.")
        else:
            lebar = [0.5, 3.5, 1.6, 1.0, 1.1]
            head = st.columns(lebar, vertical_alignment="center")
            for kolom, judul in zip(head, ["No", "Nama Peserta", "Status", "", ""]):
                kolom.markdown(f"**{judul}**" if judul else "")

            for no, (_, r) in enumerate(df_p.iterrows(), start=1):
                with st.container(border=True):
                    c = st.columns(lebar, vertical_alignment="center")
                    c[0].write(no)
                    c[1].markdown(f"**{r['nama_peserta']}**  \n<span style='color:#6B7280; font-size:.78rem;'>{r['id_peserta']}</span>", unsafe_allow_html=True)
                    c[2].write(r.get("status", "-"))
                    if c[3].button("✏️ Edit", key=f"edit_{r['id_peserta']}"):
                        dialog_edit_peserta(r["id_peserta"], spreadsheet_obj)
                    if c[4].button("🗑️ Hapus", key=f"del_{r['id_peserta']}"):
                        dialog_hapus_peserta(r["id_peserta"], r["nama_peserta"], spreadsheet_obj)

    # ---------------- 3. KELOLA INSTANSI ----------------
    elif menu_admin == "👥 Kelola Instansi":
        st.markdown("#### 👥 Kelola Data Instansi Asal")
        _show_flash("flash_instansi")

        with st.expander("➕ Tambah Instansi Baru", expanded=False):
            with st.form("form_tambah_instansi", clear_on_submit=True):
                nama_ins = st.text_input("Nama Instansi / Perusahaan*", placeholder="Contoh: PT Inovasi Digital / Universitas")
                if st.form_submit_button("Simpan Instansi ➔"):
                    df_ins = st.session_state.db_instansi
                    if not nama_ins.strip():
                        st.error("Nama instansi wajib diisi!")
                    elif not df_ins.empty and nama_ins.strip().lower() in df_ins["nama_instansi"].str.lower().tolist():
                        st.error("Instansi tersebut sudah terdaftar.")
                    else:
                        new_id = db_helper.next_id(df_ins, "INS", "id_instansi")
                        new_row = {"id_instansi": new_id, "nama_instansi": nama_ins.strip()}
                        st.session_state.db_instansi = pd.concat([df_ins, pd.DataFrame([new_row])], ignore_index=True)

                        ok, serr = db_helper.safe_append(spreadsheet_obj, "instansi", [new_id, nama_ins.strip()])
                        st.session_state["flash_instansi"] = (
                            ("success", f"Instansi **{nama_ins.strip()}** berhasil ditambahkan!") if ok
                            else ("warning", f"Instansi tersimpan di aplikasi, tetapi gagal menulis ke Google Sheet. ({serr})")
                        )
                        st.rerun()

        st.markdown("##### Daftar Instansi Terdaftar")
        df_ins = st.session_state.db_instansi
        if df_ins.empty:
            st.info("Belum ada data instansi.")
        else:
            lebar = [0.5, 4.0]
            head = st.columns(lebar, vertical_alignment="center")
            for kolom, judul in zip(head, ["No", "Nama Instansi"]):
                kolom.markdown(f"**{judul}**")
            for no, (_, r) in enumerate(df_ins.iterrows(), start=1):
                with st.container(border=True):
                    c = st.columns(lebar, vertical_alignment="center")
                    c[0].write(no)
                    c[1].markdown(f"**{r['nama_instansi']}**  \n<span style='color:#6B7280; font-size:.78rem;'>{r['id_instansi']}</span>", unsafe_allow_html=True)

    # ---------------- 4. RANKING & NILAI ----------------
    elif menu_admin == "🏆 Ranking & Nilai":
        st.markdown("#### 🏆 Klasemen Ranking Akhir & Seluruh Nilai Juri")
        if not st.session_state.db_penilaian.empty:
            st.dataframe(st.session_state.db_penilaian, use_container_width=True)
        else:
            st.info("Belum ada data penilaian masuk dari dewan juri.")

    # ---------------- 5. PESERTA FAVORIT ----------------
    elif menu_admin == "⭐ Peserta Favorit":
        st.markdown("#### ⭐ Akumulasi Pilihan Peserta Favorit Dewan Juri")
        if not st.session_state.db_favorit.empty:
            st.dataframe(st.session_state.db_favorit, use_container_width=True)
        else:
            st.info("Belum ada data voting peserta favorit dari dewan juri.")

    # ---------------- 6. DATABASE GOOGLE SHEET ----------------
    elif menu_admin == "📑 Database Google Sheet":
        st.markdown("#### 📑 Lihat Isi Live Database Google Sheets")
        if st.button("🔄 Refresh Data dari Sheet"):
            db_helper.auto_connect_and_sync(force=True)
            st.success("Data berhasil disinkronkan!")
            st.rerun()

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Penilaian", "📁 Peserta", "👥 Juri", "⭐ Favorit", "🏢 Instansi"])
        with tab1: st.dataframe(st.session_state.db_penilaian, use_container_width=True)
        with tab2: st.dataframe(st.session_state.db_peserta, use_container_width=True)
        with tab3: st.dataframe(st.session_state.db_juri, use_container_width=True)
        with tab4: st.dataframe(st.session_state.db_favorit, use_container_width=True)
        with tab5: st.dataframe(st.session_state.db_instansi, use_container_width=True)

    st.markdown("""
        <div style="text-align: center; margin-top: 40px; padding: 15px; color: #6B7280; font-size: 0.75rem;">
            FINAL PROJECT PBK DIGITAL AI WORK EXHIBITION • Panel Administrator
        </div>
    """, unsafe_allow_html=True)