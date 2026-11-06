import streamlit as st
import pandas as pd
import db_helper
import styles

_dialog = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
if _dialog is None:
    raise RuntimeError("Fitur popup butuh Streamlit >= 1.34. Jalankan: pip install -U streamlit")

_ADMIN_CSS = """
<style>
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
    [data-testid="stMain"] div[class*="st-key-del_"] .stButton > button * { color: #ffffff !important; }

    div[class*="st-key-confirm_yes"] .stButton > button {
        background-color: #dc3545 !important; color: #ffffff !important;
        border: none !important; font-weight: 700 !important; width: 100% !important; border-radius: 10px !important;
    }
    div[class*="st-key-confirm_yes"] .stButton > button * { color: #ffffff !important; }
    div[class*="st-key-confirm_no"] .stButton > button {
        background-color: #E7E2CE !important; color: #112250 !important;
        border: 1px solid #BEB7A7 !important; font-weight: 700 !important; width: 100% !important; border-radius: 10px !important;
    }
    div[class*="st-key-confirm_no"] .stButton > button * { color: #112250 !important; }

    [data-testid="stDialog"] label p,
    [data-testid="stDialog"] h1, [data-testid="stDialog"] h4 { color: #112250 !important; }
    [data-testid="stDialog"] [data-testid="stForm"] { border: none !important; box-shadow: none !important; padding: 0 !important; }
</style>
"""


# ============================ HELPER ============================
def _next_id(df, prefix, col):
    nums = []
    if not df.empty and col in df.columns:
        for v in df[col].tolist():
            if isinstance(v, str) and v.startswith(prefix + "-") and v.split("-")[-1].isdigit():
                nums.append(int(v.split("-")[-1]))
            elif str(v).isdigit():
                nums.append(int(v))
    return f"{prefix}-{(max(nums) if nums else 0) + 1:03d}"


def _exact_cells(ws, value, col):
    return [c for c in ws.findall(str(value), in_column=col) if c.value == str(value)]


def _show_flash(key):
    flash = st.session_state.pop(key, None)
    if flash:
        (st.success if flash[0] == "success" else st.warning)(flash[1])


# ============================ POPUP PESERTA ============================
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

        gagal = False
        if spreadsheet_obj:
            try:
                ws = spreadsheet_obj.worksheet("peserta")
                cells = _exact_cells(ws, id_peserta, 1)
                if cells:
                    ws.update_cell(cells[0].row, 2, nama_baru)
                else:
                    gagal = True
            except Exception:
                gagal = True

        st.session_state["flash_peserta"] = (
            ("warning", "Peserta diperbarui di aplikasi, tetapi gagal menyinkronkan ke Google Sheet.")
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

        gagal = False
        if spreadsheet_obj:
            try:
                ws = spreadsheet_obj.worksheet("peserta")
                for r in sorted({c.row for c in _exact_cells(ws, id_peserta, 1)}, reverse=True):
                    ws.delete_rows(r)
            except Exception:
                gagal = True

        st.session_state["flash_peserta"] = (
            ("warning", "Peserta dihapus dari aplikasi, tetapi gagal menghapus di Google Sheet.")
            if gagal else ("success", f"Peserta **{nama}** berhasil dihapus.")
        )
        st.rerun()


# ============================ HALAMAN ADMIN ============================
def render_admin_portal():
    spreadsheet_obj, conn_err = db_helper.auto_connect_and_sync()
    tanggal_format = db_helper.get_current_date_indonesia()
    styles.inject()
    st.markdown(_ADMIN_CSS, unsafe_allow_html=True)

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

        menu_admin = styles.sidebar_menu(
            ["📊 Dashboard", "📁 Kelola Peserta", "👥 Kelola Instansi",
             "🏆 Ranking & Nilai", "⭐ Peserta Favorit", "📑 Database Google Sheet"],
            key="menu_admin_state",
        )
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
                        new_id = _next_id(df_p, "PST", "id_peserta")
                        new_row = {
                            "id_peserta": new_id,
                            "nama_peserta": p_nama.strip(),
                            "status": "Belum Lengkap",
                        }
                        st.session_state.db_peserta = pd.concat([df_p, pd.DataFrame([new_row])], ignore_index=True)

                        err_sheet = False
                        if spreadsheet_obj:
                            try:
                                ws = spreadsheet_obj.worksheet("peserta")
                                ws.append_row([new_id, p_nama.strip(), "Belum Lengkap"])
                            except Exception as e:
                                err_sheet = True
                                print(f"Gagal append ke sheet peserta: {e}")

                        st.session_state["flash_peserta"] = (
                            ("warning", f"Peserta **{p_nama.strip()}** tersimpan di aplikasi, tetapi gagal menulis ke Google Sheet.")
                            if err_sheet else ("success", f"Peserta **{p_nama.strip()}** berhasil ditambahkan!")
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
                        new_id = _next_id(df_ins, "INS", "id_instansi")
                        new_row = {"id_instansi": new_id, "nama_instansi": nama_ins.strip()}
                        st.session_state.db_instansi = pd.concat([df_ins, pd.DataFrame([new_row])], ignore_index=True)
                        if spreadsheet_obj:
                            try:
                                spreadsheet_obj.worksheet("instansi").append_row([new_id, nama_ins.strip()])
                            except Exception:
                                pass
                        st.session_state["flash_instansi"] = ("success", f"Instansi **{nama_ins.strip()}** berhasil ditambahkan!")
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
        df_n = st.session_state.db_penilaian
        if df_n.empty:
            st.info("Belum ada data penilaian masuk dari dewan juri.")
        else:
            st.dataframe(df_n, use_container_width=True)

            if "catatan" in df_n.columns:
                st.markdown("##### 📝 Catatan Juri")
                df_c = df_n[df_n["catatan"].astype(str).str.strip() != ""]
                if df_c.empty:
                    st.caption("Belum ada catatan dari juri.")
                else:
                    df_pes = st.session_state.db_peserta
                    nama_map = dict(zip(df_pes["id_peserta"], df_pes["nama_peserta"]))
                    for _, r in df_c.iterrows():
                        peserta = nama_map.get(r.get("id_peserta"), r.get("id_peserta", "-"))
                        juri = r.get("id_juri", "-")
                        with st.container(border=True):
                            st.markdown(f"**{peserta}** · oleh {juri}")
                            st.write(r["catatan"])

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
            db_helper.sync_data_from_sheets(spreadsheet_obj)
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