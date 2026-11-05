import streamlit as st

st.set_page_config(
    page_title="Website Penilaian",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Website Penilaian")
st.write("Selamat datang di aplikasi Streamlit pertama saya.")

nama = st.text_input("Masukkan Nama")

if st.button("Simpan"):
    st.success(f"Halo, {nama}! Data berhasil diproses.")