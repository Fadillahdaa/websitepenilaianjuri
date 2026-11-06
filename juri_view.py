import streamlit as st
import pandas as pd
from datetime import datetime
import db_helper
import styles


def render_juri_portal():
    spreadsheet_obj, conn_err = db_helper.auto_connect_and_sync()
    tanggal_format = db_helper.get_current_date_indonesia()

    if "juri_auth" not in st.session_state:
        st.session_state.juri_auth = {"is_logged_in": False, "id_juri": "", "nama": "", "id_instansi": ""}

    styles.inject(dark_stage=not st.session_state.juri_auth["is_logged_in"])

    # ==============================================================================
    # 1. HALAMAN LOGIN / CHECK-IN DEWAN JURI
    # ==============================================================================
    if not st.session_state.juri_auth["is_logged_in"]:

        st.markdown("""
        <style>
            .block-container { padding-top: 3rem !important; }

            .login-brand { display:flex; align-items:center; gap:14px; margin-bottom:22px; }
            .login-brand .mark {
                width:54px; height:54px; border-radius:14px; font-size:28px;
                display:flex; align-items:center; justify-content:center;
                background:rgba(231,226,206,.12); border:1px solid rgba(231,226,206,.30);
            }
            .login-brand .name { font-size:.95rem; font-weight:800; letter-spacing:1.5px; color:#E7E2CE; }
            .login-title { font-size:2.7rem; font-weight:800; line-height:1.1; color:#ffffff; margin:0 0 12px 0; }
            .login-tagline { color:#BEB7A7; font-style:italic; font-size:.95rem; margin:0 0 30px 0; }
            .login-info {
                background:rgba(255,255,255,.06);
                border:1px solid rgba(231,226,206,.18);
                border-left:4px solid #E7E2CE;
                border-radius:14px; padding:22px 24px;
            }
            .login-info .t { color:#E7E2CE; font-weight:700; font-size:1rem; margin-bottom:6px; }
            .login-info .d { color:#CFCAB8; font-size:.88rem; line-height:1.65; }

            .login-head { text-align:center; margin-bottom:18px; }
            .login-head .h { color:#112250; font-size:1.7rem; font-weight:800; margin:0 0 6px 0; }
            .login-head .s { color:#5B6B8C; font-size:.9rem; margin:0; }
            .login-foot {
                text-align:center; margin-top:14px; padding-top:12px;
                border-top:1px solid #E7E2CE; color:#8A93A8; font-size:.72rem; letter-spacing:.3px;
            }

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
                    <div class="login-title">WORK EXHIBITION</div>
                    <div class="login-tagline">"Innovating with AI, Building a Smarter Future"</div>
                    <div class="login-info">
                        <div class="t">Portal Penilaian Resmi Dewan Juri</div>
                        <div class="d">Masukkan nama lengkap dan pilih instansi Anda untuk mulai memberikan
                        penilaian yang objektif dan terintegrasi secara realtime.</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col_form:
            df_instansi = st.session_state.db_instansi
            daftar_instansi_nama = df_instansi['nama_instansi'].tolist() if not df_instansi.empty else []
            PLACEHOLDER = "-- Pilih Instansi dari Daftar --"

            with st.form("form_login_juri"):
                st.markdown("""
                    <div class="login-head">
                        <div class="h">Selamat Datang</div>
                        <p class="s">Silakan masukkan nama dan pilih instansi Anda</p>
                    </div>
                """, unsafe_allow_html=True)

                input_nama_juri = st.text_input(
                    "Nama Lengkap*",
                    placeholder="Contoh: Dr. Ir. Ahmad Subarjo, M.Kom"
                )
                selected_instansi = st.selectbox("Pilih Instansi Asal*", options=[PLACEHOLDER] + daftar_instansi_nama)
                custom_instansi = st.text_input(
                    "Atau ketik instansi baru jika belum ada di daftar",
                    placeholder="Contoh: PT Inovasi Digital"
                )

                btn_masuk = st.form_submit_button("Masuk ke Sistem Penilaian")

                st.markdown('<div class="login-foot">FINAL PROJECT PBK DIGITAL AI WORK EXHIBITION</div>',
                            unsafe_allow_html=True)

                if btn_masuk:
                    if custom_instansi.strip():
                        instansi_final_nama = custom_instansi.strip()
                    elif selected_instansi != PLACEHOLDER:
                        instansi_final_nama = selected_instansi
                    else:
                        instansi_final_nama = ""

                    if not input_nama_juri.strip():
                        st.error("Nama lengkap juri wajib diisi!")
                    elif not instansi_final_nama:
                        st.error("Pilih instansi dari daftar atau ketik instansi baru.")
                    else:
                        nama_final = input_nama_juri.strip()

                        # ---- Instansi ----
                        df_ins = st.session_state.db_instansi
                        if not df_ins.empty:
                            matched_ins = df_ins[df_ins['nama_instansi'].str.lower() == instansi_final_nama.lower()]
                        else:
                            matched_ins = df_ins
                        if not matched_ins.empty:
                            instansi_id_final = matched_ins.iloc[0]['id_instansi']
                        else:
                            instansi_id_final = db_helper.next_id(df_ins, "INS", "id_instansi")
                            new_ins_row = {"id_instansi": instansi_id_final, "nama_instansi": instansi_final_nama}
                            st.session_state.db_instansi = pd.concat(
                                [df_ins, pd.DataFrame([new_ins_row])], ignore_index=True
                            )
                            ok, serr = db_helper.safe_append(
                                spreadsheet_obj, "instansi", [instansi_id_final, instansi_final_nama]
                            )
                            if not ok:
                                st.warning(f"Instansi baru gagal ditulis ke Google Sheet: {serr}")

                        # ---- Juri ----
                        df_juri = st.session_state.db_juri
                        if not df_juri.empty:
                            existing_juri = df_juri[df_juri['nama_juri'].str.lower() == nama_final.lower()]
                        else:
                            existing_juri = df_juri

                        if not existing_juri.empty:
                            juri_id_final = existing_juri.iloc[0]['id_juri']
                        else:
                            juri_id_final = db_helper.next_id(df_juri, "JUR", "id_juri")
                            new_juri_row = {
                                "id_juri": juri_id_final,
                                "nama_juri": nama_final,
                                "id_instansi": instansi_id_final
                            }
                            st.session_state.db_juri = pd.concat(
                                [df_juri, pd.DataFrame([new_juri_row])], ignore_index=True
                            )
                            ok, serr = db_helper.safe_append(
                                spreadsheet_obj, "juri", [juri_id_final, nama_final, instansi_id_final]
                            )
                            if not ok:
                                st.warning(f"Data juri gagal ditulis ke Google Sheet: {serr}")

                        st.session_state.juri_auth = {
                            "is_logged_in": True,
                            "id_juri": juri_id_final,
                            "nama": nama_final,
                            "id_instansi": instansi_id_final
                        }
                        st.rerun()

    # ==============================================================================
    # 2. DASHBOARD & MENU UTAMA JURI SETELAH LOGIN
    # ==============================================================================
    else:
        juri_id_aktif = st.session_state.juri_auth["id_juri"]
        nama_juri_aktif = st.session_state.juri_auth["nama"]
        instansi_id_aktif = st.session_state.juri_auth["id_instansi"]

        instansi_nama_aktif = instansi_id_aktif
        if not st.session_state.db_instansi.empty:
            m_ins = st.session_state.db_instansi[
                st.session_state.db_instansi['id_instansi'].astype(str) == str(instansi_id_aktif)
            ]
            if not m_ins.empty:
                instansi_nama_aktif = m_ins.iloc[0]['nama_instansi']

        total_peserta_count = len(st.session_state.db_peserta)

        dinilai_juri_ini = 0
        if not st.session_state.db_penilaian.empty:
            df_p_juri = st.session_state.db_penilaian[
                st.session_state.db_penilaian['id_juri'].astype(str) == str(juri_id_aktif)
            ]
            dinilai_juri_ini = df_p_juri['id_peserta'].nunique() if 'id_peserta' in df_p_juri.columns else len(df_p_juri)

        sisa_peserta = max(0, total_peserta_count - dinilai_juri_ini)
        persen_progress = int((dinilai_juri_ini / total_peserta_count * 100)) if total_peserta_count > 0 else 0

        with st.sidebar:
            st.markdown(f"""
                <div style="background: white; border: 1px solid #E7E2CE; border-radius: 12px; padding: 16px; margin-bottom: 20px; text-align: center; color: #112250;">
                    <div style="font-size: 32px;">👨‍⚖️</div>
                    <div style="font-weight: 800; font-size: 1.05rem; color: #112250; margin-top: 4px;">{nama_juri_aktif}</div>
                    <div style="font-size: 0.82rem; color: #6B7280; font-weight: 600;">{instansi_nama_aktif}</div>
                </div>
            """, unsafe_allow_html=True)

            menu_juri = styles.sidebar_menu(
                ["🏠 Dashboard", "📝 Penilaian Peserta", "⭐ Peserta Favorit",
                 "📋 Riwayat Penilaian", "🚪 Logout"],
                key="menu_juri_state",
                divider_before="🚪 Logout",
            )

            if menu_juri == "🚪 Logout":
                st.session_state.juri_auth = {"is_logged_in": False, "id_juri": "", "nama": "", "id_instansi": ""}
                st.session_state["menu_juri_state"] = "🏠 Dashboard"
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

        # ---------------- DASHBOARD ----------------
        if menu_juri == "🏠 Dashboard":
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
            st.markdown("<p style='color: #666; font-size: 0.9rem;'>Berikan nilai pada peserta sesuai 4 kriteria yang telah ditentukan (rentang nilai 0 - 100).</p>", unsafe_allow_html=True)

            if "flash_nilai" in st.session_state:
                tipe, pesan = st.session_state.pop("flash_nilai")
                (st.success if tipe == "success" else st.warning)(pesan)

            if st.session_state.db_peserta.empty:
                st.warning("⚠️ Belum ada data peserta yang dimasukkan oleh Administrator.")
            else:
                df_peserta = st.session_state.db_peserta

                sudah_dinilai_id_list = []
                if not st.session_state.db_penilaian.empty:
                    df_p_j = st.session_state.db_penilaian[
                        st.session_state.db_penilaian['id_juri'].astype(str) == str(juri_id_aktif)
                    ]
                    if 'id_peserta' in df_p_j.columns:
                        sudah_dinilai_id_list = df_p_j['id_peserta'].tolist()

                opsi_peserta = []
                map_label_ke_id = {}
                for idx, row in df_peserta.iterrows():
                    p_id = row['id_peserta']
                    p_nama = row['nama_peserta']
                    status_icon = "✅ (Sudah Dinilai)" if p_id in sudah_dinilai_id_list else "⏳ (Belum Dinilai)"
                    label_display = f"{p_nama} [{p_id}] {status_icon}"
                    opsi_peserta.append(label_display)
                    map_label_ke_id[label_display] = p_id

                selected_label = st.selectbox("Pilih Peserta:", options=opsi_peserta)
                peserta_id_terpilih = map_label_ke_id[selected_label]

                info_p = df_peserta[df_peserta['id_peserta'] == peserta_id_terpilih].iloc[0]
                peserta_nama_terpilih = info_p['nama_peserta']

                st.markdown(f"""
                    <div style="padding-top: 10px;">
                        <span style="background: #112250; color: #3BF07D; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">Kandidat Terpilih</span>
                        <h2 style="color: #112250; margin: 10px 0 4px 0;">{peserta_nama_terpilih}</h2>
                        <p style="color: #666; font-size: 0.9rem;">ID Peserta: <b>{peserta_id_terpilih}</b></p>
                    </div>
                """, unsafe_allow_html=True)

                default_scores = [80] * 4
                default_catatan = ""
                if peserta_id_terpilih in sudah_dinilai_id_list:
                    prev_row = st.session_state.db_penilaian[
                        (st.session_state.db_penilaian['id_juri'].astype(str) == str(juri_id_aktif)) &
                        (st.session_state.db_penilaian['id_peserta'].astype(str) == str(peserta_id_terpilih))
                    ].iloc[-1]
                    default_scores = []
                    for i in range(1, 5):
                        try:
                            default_scores.append(int(float(prev_row.get(f'k{i}', 80))))
                        except (ValueError, TypeError):
                            default_scores.append(80)
                    default_catatan = str(prev_row.get('catatan', '') or '')
                    st.info("ℹ️ Anda sudah pernah menilai peserta ini. Mengirim nilai baru akan memperbarui penilaian Anda.")

                st.markdown("<br><h4>4 Kriteria Penilaian (Skala 0 - 100)</h4>", unsafe_allow_html=True)
                with st.form("form_skor_juri_4_kriteria"):
                    k1 = st.number_input("1. Riset & Relevansi Industri", 0, 100, default_scores[0])
                    k2 = st.number_input("2. Inovasi & Kualitas Solusi", 0, 100, default_scores[1])
                    k3 = st.number_input("3. Pemanfaatan & Etika AI", 0, 100, default_scores[2])
                    k4 = st.number_input("4. Presentasi & Komunikasi", 0, 100, default_scores[3])

                    catatan = st.text_area(
                        "Catatan Juri (opsional)",
                        value=default_catatan,
                        placeholder="Tulis komentar atau masukan untuk peserta ini...",
                        max_chars=500,
                        key=f"catatan_{peserta_id_terpilih}",
                    )

                    scores = [k1, k2, k3, k4]
                    avg_val = round(sum(scores) / len(scores), 2)

                    st.markdown(f"""
                        <div style="background: white; border: 2px solid #3B507D; border-radius: 12px; padding: 14px; margin: 15px 0; text-align: center;">
                            <span style="color: #BEB7A7; font-weight: 600;">Rata-rata Skor Keseluruhan:</span>
                            <span style="font-size: 1.6rem; font-weight: 800; color: #112250; margin-left: 12px;">{avg_val}</span>
                        </div>
                    """, unsafe_allow_html=True)

                    if st.form_submit_button("💾 Simpan Nilai ➔"):
                        ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        penilaian_id = f"PEN-{int(datetime.now().timestamp())}"

                        new_penilaian = {
                            "id": penilaian_id,
                            "id_juri": juri_id_aktif,
                            "id_instansi": instansi_id_aktif,
                            "id_peserta": peserta_id_terpilih,
                            "k1": k1, "k2": k2, "k3": k3, "k4": k4,
                            "waktu_input": ts_now,
                            "catatan": catatan.strip()
                        }

                        df_pen = st.session_state.db_penilaian
                        if not df_pen.empty:
                            mask = ~((df_pen['id_juri'].astype(str) == str(juri_id_aktif)) &
                                     (df_pen['id_peserta'].astype(str) == str(peserta_id_terpilih)))
                            st.session_state.db_penilaian = df_pen[mask]

                        st.session_state.db_penilaian = pd.concat(
                            [st.session_state.db_penilaian, pd.DataFrame([new_penilaian])], ignore_index=True
                        )

                        gagal_sheet = False
                        detail_error = ""
                        if spreadsheet_obj:
                            try:
                                ws_pen = db_helper.get_ws(spreadsheet_obj, "penilaian")

                                semua = ws_pen.get_all_values()
                                baris_lama = [
                                    i for i, r in enumerate(semua[1:], start=2)
                                    if len(r) > 3 and r[1] == str(juri_id_aktif) and r[3] == str(peserta_id_terpilih)
                                ]
                                for nomor in sorted(baris_lama, reverse=True):
                                    ws_pen.delete_rows(nomor)

                                ws_pen.append_row([
                                    penilaian_id, juri_id_aktif, instansi_id_aktif, peserta_id_terpilih,
                                    k1, k2, k3, k4, ts_now, catatan.strip()
                                ])
                            except Exception as e:
                                gagal_sheet = True
                                detail_error = f"{type(e).__name__}: {e}"
                                print(f"Gagal simpan penilaian ke Sheet: {detail_error}")
                        else:
                            gagal_sheet = True
                            detail_error = "Koneksi ke Google Sheet tidak tersedia."

                        if gagal_sheet:
                            st.session_state["flash_nilai"] = (
                                "warning",
                                f"Nilai tersimpan di aplikasi, tetapi gagal menulis ke Google Sheet. ({detail_error})"
                            )
                        else:
                            st.session_state["flash_nilai"] = (
                                "success",
                                f"🎉 Nilai untuk **{peserta_nama_terpilih}** berhasil disimpan! Rata-rata: **{avg_val}**"
                            )
                        st.rerun()

        # ---------------- PESERTA FAVORIT ----------------
        elif menu_juri == "⭐ Peserta Favorit":
            st.markdown("### ⭐ Peserta Favorit Pilihan Anda")
            st.markdown("<p style='color: #666; font-size: 0.9rem;'>Pilih 1 peserta favorit Anda dari daftar berikut. Pilihan ini akan menjadi bagian dari hasil akhir penilaian.</p>", unsafe_allow_html=True)

            if "flash_fav" in st.session_state:
                tipe, pesan = st.session_state.pop("flash_fav")
                (st.success if tipe == "success" else st.warning)(pesan)

            if not st.session_state.db_peserta.empty:
                df_peserta = st.session_state.db_peserta
                current_fav_id = None
                if not st.session_state.db_favorit.empty:
                    df_fav_juri = st.session_state.db_favorit[
                        st.session_state.db_favorit['id_juri'].astype(str) == str(juri_id_aktif)
                    ]
                    if not df_fav_juri.empty and 'id_peserta' in df_fav_juri.columns:
                        current_fav_id = df_fav_juri.iloc[-1]['id_peserta']

                list_id_peserta = df_peserta['id_peserta'].tolist()
                idx_def = list_id_peserta.index(current_fav_id) if current_fav_id in list_id_peserta else 0

                with st.form("form_voting_favorit"):
                    selected_fav_label = st.selectbox(
                        "-- Pilih Peserta Favorit --",
                        options=df_peserta['nama_peserta'] + " [" + df_peserta['id_peserta'] + "]",
                        index=idx_def
                    )

                    pilih_fav_id = selected_fav_label.split("[")[-1].replace("]", "").strip()
                    st.markdown("<br>", unsafe_allow_html=True)

                    if st.form_submit_button("⭐ Simpan Pilihan Favorit"):
                        ts_fav = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        new_fav = {
                            "waktu_input": ts_fav,
                            "id_juri": juri_id_aktif,
                            "id_instansi": instansi_id_aktif,
                            "id_peserta": pilih_fav_id
                        }

                        df_fav = st.session_state.db_favorit
                        if not df_fav.empty:
                            st.session_state.db_favorit = df_fav[df_fav['id_juri'].astype(str) != str(juri_id_aktif)]

                        st.session_state.db_favorit = pd.concat(
                            [st.session_state.db_favorit, pd.DataFrame([new_fav])], ignore_index=True
                        )

                        gagal_fav = False
                        detail_fav = ""
                        if spreadsheet_obj:
                            try:
                                ws_fav = db_helper.get_ws(spreadsheet_obj, "favorit")
                                semua = ws_fav.get_all_values()
                                lama = [
                                    i for i, r in enumerate(semua[1:], start=2)
                                    if len(r) > 1 and r[1] == str(juri_id_aktif)
                                ]
                                for nomor in sorted(lama, reverse=True):
                                    ws_fav.delete_rows(nomor)
                                ws_fav.append_row([ts_fav, juri_id_aktif, instansi_id_aktif, pilih_fav_id])
                            except Exception as e:
                                gagal_fav = True
                                detail_fav = f"{type(e).__name__}: {e}"
                        else:
                            gagal_fav = True
                            detail_fav = "Koneksi ke Google Sheet tidak tersedia."

                        st.session_state["flash_fav"] = (
                            ("warning", f"Pilihan tersimpan di aplikasi, tetapi gagal menulis ke Google Sheet. ({detail_fav})")
                            if gagal_fav else ("success", "Pilihan peserta favorit berhasil disimpan!")
                        )
                        st.rerun()
            else:
                st.warning("⚠️ Belum ada data peserta yang dimasukkan oleh Administrator.")

        # ---------------- RIWAYAT ----------------
        elif menu_juri == "📋 Riwayat Penilaian":
            st.markdown(f"### 📋 Riwayat Penilaian oleh {nama_juri_aktif}")
            if not st.session_state.db_penilaian.empty:
                df_my = st.session_state.db_penilaian[
                    st.session_state.db_penilaian['id_juri'].astype(str) == str(juri_id_aktif)
                ]
                if not df_my.empty:
                    st.dataframe(df_my, use_container_width=True)
                else:
                    st.info("Anda belum menilai peserta manapun.")
            else:
                st.info("Belum ada data nilai tersimpan.")

    st.markdown("""
        <div style="text-align: center; margin-top: 50px; padding: 20px; border-top: 1px solid #E7E2CE; color: #BEB7A7; font-size: 0.8rem;">
            FINAL PROJECT PBK DIGITAL AI WORK EXHIBITION • Portal Dewan Juri
        </div>
    """, unsafe_allow_html=True)
