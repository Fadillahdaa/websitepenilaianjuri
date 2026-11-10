import hmac
import time
import streamlit as st
import pandas as pd
import db_helper
import styles

_dialog = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
if _dialog is None:
    raise RuntimeError("Fitur popup butuh Streamlit >= 1.34. Jalankan: pip install -U streamlit")

# Jumlah favorit per juri (samakan dengan JUMLAH_FAVORIT di juri_view.py)
JUMLAH_FAVORIT = 3

# Batas waktu sesi admin dalam detik (2 jam = 2 * 3600 detik)
ADMIN_SESSION_TIMEOUT = 2 * 3600

_ADMIN_CSS = """
<style>
    .stApp {
        background-color: #F5F4F0;
    }

    /* Styling Card Putih Utama */
    [data-testid="stForm"] {
        background: #ffffff !important;
        border: 1px solid #E7E2CE !important;
        border-radius: 20px !important;
        padding: 35px 30px !important;
        box-shadow: 0 15px 35px rgba(17, 34, 80, 0.08) !important;
        width: 100% !important;
    }

    [data-testid="stForm"] label p {
        color: #112250 !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
    }

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

    /* Expander ranking */
    [data-testid="stMain"] [data-testid="stExpander"] {
        background: #ffffff; border: 1px solid #E7E2CE !important; border-radius: 14px !important; margin-bottom: 8px;
    }
    [data-testid="stMain"] [data-testid="stExpander"] summary p {
        color: #112250 !important; font-weight: 700 !important;
    }
</style>
"""


_HIDE_SIDEBAR_CSS = """
<style>
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
</style>
"""

_KRIT = ["k1", "k2", "k3", "k4"]
# Bobot tiap kriteria: Riset 40% · Visual 30% · Video 20% · Presentasi 10%
_BOBOT = [0.40, 0.30, 0.20, 0.10]


# ============================ LOGIN ADMIN (st.secrets) ============================
# Isi .streamlit/secrets.toml (atau Secrets di Streamlit Cloud):
#   [admin]
#   username = "..."
#   password = "..."
def _admin_terkonfigurasi():
    try:
        cfg = st.secrets["admin"]
        return bool(str(cfg["username"])) and bool(str(cfg["password"]))
    except Exception:
        return False


def _cek_admin(username, password):
    if not _admin_terkonfigurasi():
        return False
    cfg = st.secrets["admin"]
    ok_user = hmac.compare_digest(str(username).encode(), str(cfg["username"]).encode())
    ok_pass = hmac.compare_digest(str(password).encode(), str(cfg["password"]).encode())
    return ok_user and ok_pass


# ============================ HELPER ============================
def _show_flash(key):
    flash = st.session_state.pop(key, None)
    if flash:
        (st.success if flash[0] == "success" else st.warning)(flash[1])


def _siapkan_ranking():
    """Return (df_rank, df_detail, jumlah_baris_diabaikan)."""
    df_n = st.session_state.db_penilaian.copy()
    df_p = st.session_state.db_peserta
    df_j = db_helper.tampilkan_nama_juri(st.session_state.db_juri)

    if df_n.empty or df_p.empty or "id_peserta" not in df_n.columns:
        return pd.DataFrame(), pd.DataFrame(), 0

    valid = df_n["id_peserta"].isin(df_p["id_peserta"])
    diabaikan = int((~valid).sum())
    df_n = df_n[valid].copy()

    for k in _KRIT:
        df_n[k] = pd.to_numeric(df_n[k], errors="coerce") if k in df_n.columns else float("nan")

    df_n["rata_juri"] = (df_n[_KRIT] * _BOBOT).sum(axis=1, min_count=len(_KRIT)).round(2)
    df_n = df_n.dropna(subset=["rata_juri"])
    if df_n.empty:
        return pd.DataFrame(), pd.DataFrame(), diabaikan

    if "waktu_input" in df_n.columns:
        df_n = df_n.sort_values("waktu_input")
    df_n = df_n.drop_duplicates(subset=["id_juri", "id_peserta"], keep="last")

    kolom_juri = [c for c in ["id_juri", "nama_juri", "jenis_instansi", "nama_instansi"] if c in df_j.columns]
    df_detail = df_n.merge(df_j[kolom_juri].drop_duplicates(subset="id_juri"), on="id_juri", how="left")
    for c in ["nama_juri", "jenis_instansi", "nama_instansi"]:
        if c not in df_detail.columns:
            df_detail[c] = "-"
        df_detail[c] = df_detail[c].fillna("-")

    df_rank = (
        df_detail.groupby("id_peserta")
        .agg(nilai_akhir=("rata_juri", "mean"), jumlah_juri=("id_juri", "nunique"))
        .reset_index()
        .merge(df_p[["id_peserta", "nama_peserta"]], on="id_peserta", how="left")
        .sort_values("nilai_akhir", ascending=False)
        .reset_index(drop=True)
    )
    df_rank["peringkat"] = df_rank["nilai_akhir"].rank(method="min", ascending=False).astype(int)
    return df_rank, df_detail, diabaikan


@_dialog("✏️ Edit Peserta")
def dialog_edit_peserta(id_peserta, db_client):
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

        # Update ke Firestore via db_helper.ubah_sel_by_id
        ok, serr = db_helper.ubah_sel_by_id(db_client, "peserta", id_peserta, "nama_peserta", nama_baru)

        st.session_state["flash_peserta"] = (
            ("warning", f"Peserta diperbarui di aplikasi, tetapi gagal ke Firestore. ({serr})")
            if not ok else ("success", f"Data peserta **{nama_baru}** berhasil diperbarui.")
        )
        st.rerun()


@_dialog("🗑️ Hapus Peserta")
def dialog_hapus_peserta(id_peserta, nama, db_client):
    st.markdown(f"#### Yakin hapus peserta **{nama}**?")
    st.caption("Nilai dan pilihan favorit untuk peserta ini juga akan ikut terhapus.")
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

        ok, serr = db_helper.hapus_baris_by_id(db_client, "peserta", id_peserta)

        # Bersihkan nilai & favorit milik peserta ini (id_peserta = kolom ke-3 di kedua koleksi)
        for sheet in ("penilaian", "favorit"):
            ok2, err2 = db_helper.hapus_baris_by_id(db_client, sheet, id_peserta, kolom=3)
            if not ok2:
                ok, serr = False, err2

        st.session_state["flash_peserta"] = (
            ("warning", f"Peserta dihapus di aplikasi, tetapi gagal membersihkan data di Firestore. ({serr})")
            if not ok else ("success", f"Peserta **{nama}** berhasil dihapus.")
        )
        st.rerun()


# ============================ HALAMAN ADMIN ============================
def render_admin_portal():
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
        st.session_state.admin_login_time = 0.0

    # --- CEK BATAS WAKTU SESI 2 JAM ---
    if st.session_state.admin_logged_in:
        elapsed_time = time.time() - st.session_state.get("admin_login_time", 0.0)
        if elapsed_time > ADMIN_SESSION_TIMEOUT:
            st.session_state.admin_logged_in = False
            st.session_state.admin_login_time = 0.0
            st.warning("⏱️ Sesi login Anda telah berakhir (lebih dari 2 jam). Silakan login kembali.")

    # ================= FORM LOGIN ADMIN (TAMPIL DI TENGAH) =================
    if not st.session_state.admin_logged_in:
        styles.inject(dark_stage=True)
        st.markdown(_ADMIN_CSS, unsafe_allow_html=True)
        st.markdown(_HIDE_SIDEBAR_CSS, unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)

        _, col_center, _ = st.columns([1, 1.2, 1])

        with col_center:
            with st.form("form_login_admin"):
                st.markdown("""
                    <div style="text-align: center; margin-bottom: 20px;">
                        <h2 style="color: #112250; font-size: 1.6rem; font-weight: 800; margin: 0 0 4px 0;">ADMIN LOGIN</h2>
                        <p style="color: #8A93A8; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin: 0;">PORTAL MANAJEMEN EKSIBISI</p>
                    </div>
                """, unsafe_allow_html=True)

                username_input = st.text_input("Username", placeholder="Masukkan username admin")
                password_input = st.text_input("Password", type="password", placeholder="Masukkan password admin")

                _, btn_col, _ = st.columns([0.3, 2, 0.3])
                with btn_col:
                    btn_login = st.form_submit_button("Masuk Panel Admin ➔", width="stretch")

                if btn_login:
                    if not _admin_terkonfigurasi():
                        st.error("Kredensial admin belum diatur di st.secrets (bagian [admin]).")
                    elif _cek_admin(username_input, password_input):
                        st.session_state.admin_logged_in = True
                        st.session_state.admin_login_time = time.time()
                        st.success("Login berhasil! Memuat sistem...")
                        st.rerun()
                    else:
                        st.error("Username atau password salah!")
        return

    # ================= PANEL UTAMA ADMIN SETELAH LOGIN =================
    styles.inject()
    st.markdown(_ADMIN_CSS, unsafe_allow_html=True)

    db_client, conn_err = db_helper.auto_connect_and_sync()
    tanggal_format = db_helper.get_current_date_indonesia()

    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 10px 0 20px 0; border-bottom: 1px solid #3B507D; margin-bottom: 10px;">
                <div style="font-size: 28px; margin-bottom: 4px;">🏆</div>
                <div style="font-size: 0.78rem; font-weight: 800; color: #E7E2CE; letter-spacing: 1px;">FINAL PROJECT PBK</div>
                <div style="font-size: 0.65rem; color: #BEB7A7; font-weight: 600;">DIGITAL AI WORK EXHIBITION</div>
            </div>
        """, unsafe_allow_html=True)

        if not conn_err:
            st.markdown("""
                <div style="margin: 10px 0 16px 0; padding: 10px 12px; background: rgba(59,240,125,0.12); border: 1px solid #3B507D; border-radius: 8px; font-size: 0.75rem; color: #E7E2CE; font-weight: 600; text-align: center;">
                    🟢 <b>Firebase Tersambung</b>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="margin: 10px 0 16px 0; padding: 10px 12px; background: rgba(220,53,69,0.15); border: 1px solid #dc3545; border-radius: 8px; font-size: 0.75rem; color: #E7E2CE; font-weight: 600; text-align: center;">
                    🔴 <b>Koneksi Gagal</b>
                </div>
            """, unsafe_allow_html=True)

        menu_admin = styles.sidebar_menu(
            ["📊 Dashboard", "📁 Kelola Peserta", "👥 Kelola Instansi",
             "🏆 Ranking & Nilai", "⭐ Peserta Favorit", "📑 Database Firestore", "🚪 Logout Admin"],
            key="menu_admin_state",
        )

        if menu_admin == "🚪 Logout Admin":
            st.session_state.admin_logged_in = False
            st.session_state.admin_login_time = 0.0
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
        st.error(f"❌ Firestore bermasalah: {conn_err}")

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
        df_peserta = st.session_state.db_peserta
        medali = {1: "🥇", 2: "🥈", 3: "🥉"}

        st.markdown("#### 🏆 Top 3 Ranking Sementara")
        df_rank_dash, _, _ = _siapkan_ranking()
        if not df_rank_dash.empty:
            top3 = df_rank_dash.head(3)[["peringkat", "nama_peserta", "nilai_akhir"]].copy()
            top3["peringkat"] = top3["peringkat"].map(lambda p: medali.get(p, f"#{p}"))
            top3.columns = ["Peringkat", "Nama Peserta", "Nilai Akhir"]
            st.dataframe(
                top3.style.format({"Nilai Akhir": "{:.2f}"}),
                width="stretch", hide_index=True,
            )
        else:
            st.info("Belum ada data penilaian.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### ⭐ Top 3 Peserta Favorit")
        df_fav = db_helper.ensure_cols(st.session_state.db_favorit, "favorit")
        if not df_fav.empty and not df_peserta.empty and "id_peserta" in df_fav.columns:
            fav_counts = (
                df_fav.drop_duplicates(subset=["id_juri", "id_peserta"])["id_peserta"]
                .value_counts().reset_index()
            )
            fav_counts.columns = ["id_peserta", "total_vote"]
            fav_counts = (
                fav_counts.merge(df_peserta[["id_peserta", "nama_peserta"]], on="id_peserta", how="inner")
                .sort_values(["total_vote", "nama_peserta"], ascending=[False, True])
                .reset_index(drop=True)
            )
            fav_counts["peringkat"] = fav_counts["total_vote"].rank(method="min", ascending=False).astype(int)

            top3_fav = fav_counts.head(3)[["peringkat", "nama_peserta", "total_vote"]].copy()
            top3_fav["peringkat"] = top3_fav["peringkat"].map(lambda p: medali.get(p, f"#{p}"))
            top3_fav.columns = ["Peringkat", "Nama Peserta", "Total Voting"]
            st.dataframe(top3_fav, width="stretch", hide_index=True)
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
                            db_client, "peserta", [new_id, p_nama.strip(), "Belum Lengkap"]
                        )
                        st.session_state["flash_peserta"] = (
                            ("success", f"Peserta **{p_nama.strip()}** berhasil ditambahkan!") if ok
                            else ("warning", f"Peserta tersimpan di aplikasi, tetapi gagal menulis ke Firestore. ({serr})")
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
                        dialog_edit_peserta(r["id_peserta"], db_client)
                    if c[4].button("🗑️ Hapus", key=f"del_{r['id_peserta']}"):
                        dialog_hapus_peserta(r["id_peserta"], r["nama_peserta"], db_client)

    # ---------------- 3. KELOLA INSTANSI ----------------
    elif menu_admin == "👥 Kelola Instansi":
        st.markdown("#### 👥 Kelola Pilihan Instansi")
        st.caption("Pilihan di sini muncul sebagai dropdown 'Pilih Instansi Asal' pada halaman login Dewan Juri.")
        _show_flash("flash_instansi")

        with st.expander("➕ Tambah Pilihan Instansi", expanded=False):
            with st.form("form_tambah_jenis", clear_on_submit=True):
                nama_jenis = st.text_input("Nama Pilihan Instansi*", placeholder="Contoh: Dinas / LPKS / DU/DI")
                if st.form_submit_button("Simpan Pilihan ➔"):
                    df_j = st.session_state.db_jenis
                    bersih = nama_jenis.strip()
                    if not bersih:
                        st.error("Nama pilihan instansi wajib diisi!")
                    elif not df_j.empty and bersih.lower() in df_j["nama_jenis"].str.lower().tolist():
                        st.error("Pilihan tersebut sudah ada.")
                    else:
                        new_id = db_helper.next_id(df_j, "JNS", "id_jenis")
                        new_row = {"id_jenis": new_id, "nama_jenis": bersih}
                        st.session_state.db_jenis = pd.concat([df_j, pd.DataFrame([new_row])], ignore_index=True)
                        ok, serr = db_helper.safe_append(db_client, "jenis", [new_id, bersih])
                        st.session_state["flash_instansi"] = (
                            ("success", f"Pilihan **{bersih}** berhasil ditambahkan!") if ok
                            else ("warning", f"Tersimpan di aplikasi, tetapi gagal menulis ke Firestore. ({serr})")
                        )
                        st.rerun()

        st.markdown("##### Pilihan Dropdown Terdaftar")
        df_j = st.session_state.db_jenis
        if df_j.empty:
            st.info("Belum ada pilihan instansi. Tambahkan dulu agar juri bisa login.")
        else:
            lebar = [0.5, 4.0, 1.1]
            head = st.columns(lebar, vertical_alignment="center")
            for kolom, judul in zip(head, ["No", "Pilihan Instansi", ""]):
                kolom.markdown(f"**{judul}**" if judul else "")
            for no, (_, r) in enumerate(df_j.iterrows(), start=1):
                with st.container(border=True):
                    c = st.columns(lebar, vertical_alignment="center")
                    c[0].write(no)
                    c[1].markdown(f"**{r['nama_jenis']}**  \n<span style='color:#6B7280; font-size:.78rem;'>{r['id_jenis']}</span>", unsafe_allow_html=True)
                    if c[2].button("🗑️ Hapus", key=f"del_jns_{r['id_jenis']}"):
                        st.session_state.db_jenis = df_j[df_j["id_jenis"] != r["id_jenis"]].reset_index(drop=True)
                        ok, serr = db_helper.hapus_baris_by_id(db_client, "jenis", r["id_jenis"])
                        st.session_state["flash_instansi"] = (
                            ("warning", f"Dihapus di aplikasi, gagal di Firestore. ({serr})") if not ok
                            else ("success", f"Pilihan **{r['nama_jenis']}** berhasil dihapus.")
                        )
                        st.rerun()

        st.markdown("##### Dewan Juri yang Sudah Masuk")
        df_juri = db_helper.ensure_cols(st.session_state.db_juri, "juri")
        if df_juri.empty:
            st.info("Belum ada juri yang masuk ke sistem.")
        else:
            status_magang = df_juri["terima_magang"].astype(str).str.strip()
            n_ya = int((status_magang == "Ya").sum())
            n_tidak = int((status_magang == "Tidak").sum())
            n_belum = len(df_juri) - n_ya - n_tidak
            st.caption(
                f"🎓 Terima magang: **{n_ya}** instansi  ·  Tidak menerima: **{n_tidak}**  ·  Belum diisi: **{n_belum}**"
            )

            df_tampil = db_helper.tampilkan_nama_juri(df_juri)
            df_tampil["terima_magang"] = (
                status_magang
                .map({"Ya": "✅ Menerima", "Tidak": "❌ Tidak menerima"})
                .fillna("⏳ Belum diisi")
            )
            st.dataframe(
                df_tampil[["id_juri", "nama_juri", "jenis_instansi", "nama_instansi", "terima_magang"]].rename(columns={
                    "id_juri": "ID", "nama_juri": "Nama Juri",
                    "jenis_instansi": "Instansi Asal", "nama_instansi": "Nama Instansi",
                    "terima_magang": "Terima Magang",
                }),
                width="stretch", hide_index=True,
            )

    # ---------------- 4. RANKING & NILAI ----------------
    elif menu_admin == "🏆 Ranking & Nilai":
        st.markdown("#### 🏆 Klasemen Ranking Akhir")
        st.caption(
            "Peringkat berdasarkan rata-rata nilai akhir berbobot seluruh juri "
            "(Riset & Relevansi 40% · Visual & Infografis 30% · Video 20% · Presentasi 10%). "
            "Klik nama peserta untuk melihat siapa saja yang menilai."
        )

        df_rank, df_detail, diabaikan = _siapkan_ranking()

        if df_rank.empty:
            st.info("Belum ada data penilaian masuk dari dewan juri.")
        else:
            if diabaikan:
                st.warning(f"{diabaikan} baris penilaian diabaikan karena ID peserta tidak cocok dengan data peserta.")

            medali = {1: "🥇", 2: "🥈", 3: "🥉"}
            for _, r in df_rank.iterrows():
                ikon = medali.get(r["peringkat"], f"**#{r['peringkat']}**")
                judul = f"{ikon}  {r['nama_peserta']}  —  Nilai Akhir {r['nilai_akhir']:.2f}  ({r['jumlah_juri']} juri)"
                with st.expander(judul):
                    det = df_detail[df_detail["id_peserta"] == r["id_peserta"]].copy()
                    kolom_tampil = ["nama_juri", "jenis_instansi", "nama_instansi", *_KRIT, "rata_juri"]
                    for opsional in ["catatan", "waktu_input"]:
                        if opsional in det.columns:
                            kolom_tampil.append(opsional)
                    tampil = det[kolom_tampil].rename(columns={
                        "nama_juri": "Nama Juri", "jenis_instansi": "Jenis Instansi",
                        "nama_instansi": "Nama DUDIKA",
                        "k1": "K1 Riset (40%)", "k2": "K2 Visual (30%)",
                        "k3": "K3 Video (20%)", "k4": "K4 Presentasi (10%)",
                        "rata_juri": "Nilai Akhir", "catatan": "Catatan", "waktu_input": "Waktu Input",
                    })
                    st.dataframe(
                        tampil.style.format({"Nilai Akhir": "{:.2f}"}),
                        width="stretch", hide_index=True,
                    )

            belum = st.session_state.db_peserta[~st.session_state.db_peserta["id_peserta"].isin(df_rank["id_peserta"])]
            if not belum.empty:
                st.caption("Belum dinilai: " + ", ".join(belum["nama_peserta"].tolist()))

    # ---------------- 5. PESERTA FAVORIT ----------------
    elif menu_admin == "⭐ Peserta Favorit":
        st.markdown("#### ⭐ Akumulasi Pilihan Peserta Favorit Dewan Juri")
        st.caption(f"Setiap juri memilih tepat {JUMLAH_FAVORIT} peserta favorit.")
        df_fav = db_helper.ensure_cols(st.session_state.db_favorit, "favorit")
        if not df_fav.empty:
            df_j = (db_helper.tampilkan_nama_juri(st.session_state.db_juri)
                    [["id_juri", "nama_juri", "jenis_instansi", "nama_instansi"]]
                    .drop_duplicates(subset="id_juri"))
            df_p = (db_helper.ensure_cols(st.session_state.db_peserta, "peserta")
                    [["id_peserta", "nama_peserta"]]
                    .drop_duplicates(subset="id_peserta"))

            df_tampil = (df_fav.merge(df_j, on="id_juri", how="left")
                               .merge(df_p, on="id_peserta", how="left"))
            for c in ["nama_juri", "jenis_instansi", "nama_instansi", "nama_peserta"]:
                df_tampil[c] = df_tampil[c].fillna("-")

            st.markdown("##### 🏅 Rekap Vote per Peserta (Peringkat)")
            votes = (
                df_fav.drop_duplicates(subset=["id_juri", "id_peserta"])["id_peserta"]
                .value_counts()
            )
            rekap = df_p.copy()
            rekap["total_vote"] = rekap["id_peserta"].map(votes).fillna(0).astype(int)
            rekap = rekap.sort_values(
                ["total_vote", "nama_peserta"], ascending=[False, True]
            ).reset_index(drop=True)
            rekap["peringkat"] = rekap["total_vote"].rank(method="min", ascending=False).astype(int)

            medali_rekap = {1: "🥇", 2: "🥈", 3: "🥉"}
            rekap["Peringkat"] = [
                medali_rekap.get(p, f"#{p}") if v > 0 else f"#{p}"
                for p, v in zip(rekap["peringkat"], rekap["total_vote"])
            ]
            tampil_rekap = rekap[["Peringkat", "nama_peserta", "total_vote"]].rename(
                columns={"nama_peserta": "Nama Peserta", "total_vote": "Total Voting"}
            )
            st.dataframe(
                tampil_rekap,
                width="stretch",
                hide_index=True,
                height=(len(tampil_rekap) + 1) * 35 + 3,
                column_config={
                    "Peringkat": st.column_config.TextColumn("Peringkat", width="small"),
                    "Total Voting": st.column_config.NumberColumn("Total Voting", width="small"),
                },
            )
            st.caption(
                f"Total suara masuk: {int(rekap['total_vote'].sum())} "
                f"· Skor sama = peringkat sama, diurutkan abjad."
            )

            per_juri = df_fav.groupby("id_juri")["id_peserta"].nunique()
            kurang = per_juri[per_juri != JUMLAH_FAVORIT]
            if not kurang.empty:
                st.warning(
                    f"{len(kurang)} juri belum memiliki tepat {JUMLAH_FAVORIT} pilihan favorit."
                )

            st.markdown("##### 📋 Detail Pilihan Tiap Juri")
            st.dataframe(
                df_tampil[["waktu_input", "nama_juri", "jenis_instansi", "nama_instansi", "nama_peserta"]]
                .rename(columns={
                    "waktu_input": "Waktu Input", "nama_juri": "Nama Juri",
                    "jenis_instansi": "Instansi Asal", "nama_instansi": "Nama Instansi",
                    "nama_peserta": "Peserta Favorit",
                }),
                width="stretch", hide_index=True,
            )
        else:
            st.info("Belum ada data voting peserta favorit dari dewan juri.")

    # ---------------- 6. DATABASE FIRESTORE ----------------
    elif menu_admin == "📑 Database Firestore":
        st.markdown("#### 📑 Lihat Isi Live Database Firestore")
        if st.button("🔄 Refresh Data dari Firestore"):
            db_helper.auto_connect_and_sync(force=True)
            st.success("Data berhasil disinkronkan!")
            st.rerun()

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Penilaian", "📁 Peserta", "👥 Juri", "⭐ Favorit", "🏷️ Pilihan Instansi"])
        with tab1: st.dataframe(st.session_state.db_penilaian, width="stretch")
        with tab2: st.dataframe(st.session_state.db_peserta, width="stretch")
        with tab3: st.dataframe(st.session_state.db_juri, width="stretch")
        with tab4: st.dataframe(st.session_state.db_favorit, width="stretch")
        with tab5: st.dataframe(st.session_state.db_jenis, width="stretch")

    st.markdown("""
        <div style="text-align: center; margin-top: 40px; padding: 15px; color: #6B7280; font-size: 0.75rem;">
            FINAL PROJECT PBK DIGITAL AI WORK EXHIBITION • Panel Administrator
        </div>
    """, unsafe_allow_html=True)