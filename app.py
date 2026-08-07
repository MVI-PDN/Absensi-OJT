import google.generativeai as genai
import pandas as pd
import streamlit as st

# ==========================================
# KONFIGURASI APLIKASI
# ==========================================
st.set_page_config(page_title="AI Multi-Pair News Predictor", layout="wide")
st.title("🤖 AI Fundamental News & Multi-Pair Predictor")
st.caption("Analisis Skenario Dampak Berita High-Impact Tanpa Menunggu Input Detik Pertama")

# ==========================================
# SIDEBAR: PENGATURAN & VALIDASI API KEY
# ==========================================
st.sidebar.header("⚙️ Pengaturan AI Engine")
gemini_api_key = st.sidebar.text_input("Masukkan Gemini API Key:", type="password")

# Fitur Baru: Indikator Validasi API Key
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        # Jika berhasil inisialisasi model, tampilkan pesan sukses
        st.sidebar.success("✅ API Key Valid & Siap Digunakan!")
    except Exception as e:
        st.sidebar.error("❌ API Key tidak valid atau bermasalah.")

# ==========================================
# KALENDER BERITA MENDATANG (PRESET)
# ==========================================
st.subheader("📅 Kalender Berita High Impact Mendatang")
st.info("Pilih jadwal berita di bawah ini untuk mengisi data secara otomatis, atau pilih 'Isi Manual'.")

news_template = st.selectbox(
    "Pilih Berita:",
    [
        "📝 Custom / Isi Manual",
        "🇺🇸 US Non-Farm Payrolls (NFP) - Berdampak Kuat pada XAU & USD",
        "🇺🇸 US Consumer Price Index (CPI) - Indikator Inflasi Utama",
        "🇺🇸 FOMC Economic Projections & Fed Funds Rate",
        "🇬🇧 BOE Interest Rate Decision - Berdampak Kuat pada GBP",
        "🇯🇵 BOJ Press Conference & Rate - Berdampak Kuat pada JPY"
    ]
)

# ==========================================
# FORM INPUT OTOMATIS / MANUAL
# ==========================================
st.subheader("📰 Data Berita & Konsensus (Forecast)")

# Logika Auto-Fill berdasarkan pilihan dropdown
default_title = "Non-Farm Payrolls"
default_curr = "USD"
default_fc = "185K"
default_prev = "206K"

if "CPI" in news_template:
    default_title, default_curr, default_fc, default_prev = "US Consumer Price Index (CPI) m/m", "USD", "0.2%", "0.1%"
elif "FOMC" in news_template:
    default_title, default_curr, default_fc, default_prev = "FOMC Fed Funds Rate", "USD", "5.25%", "5.50%"
elif "BOE" in news_template:
    default_title, default_curr, default_fc, default_prev = "BOE Interest Rate Decision", "GBP", "5.00%", "5.25%"
elif "BOJ" in news_template:
    default_title, default_curr, default_fc, default_prev = "BOJ Interest Rate Decision", "JPY", "0.25%", "0.10%"
elif "Custom" not in news_template:
    default_title = news_template.split("-")[0].strip()

col1, col2, col3, col4 = st.columns(4)
with col1:
    news_title = st.text_input("Nama Berita:", value=default_title)
with col2:
    currency_target = st.selectbox("Mata Uang Utama:", ["USD", "JPY", "GBP", "EUR", "AUD"], index=["USD", "JPY", "GBP", "EUR", "AUD"].index(default_curr))
with col3:
    forecast_val = st.text_input("Forecast (Konsensus):", value=default_fc)
with col4:
    previous_val = st.text_input("Previous (Bulan Lalu):", value=default_prev)

st.divider()

# ==========================================
# PILIHAN PAIR & GENERATOR PREDIKSI AI
# ==========================================
st.subheader("💱 Target Pairs & Sentimen Market")
selected_pairs = st.multiselect(
    "Pilih Pair Forex/Commodity yang Ingin Di-Analisa AI:",
    ["XAU/USD (Gold)", "USD/JPY", "GBP/USD", "EUR/USD", "AUD/USD"],
    default=["XAU/USD (Gold)", "USD/JPY"] if default_curr == "USD" else [f"{default_curr}/USD"] if default_curr != "JPY" else ["USD/JPY"]
)

extra_context = st.text_area(
    "Isu Sentimen Terkini (Opsional):",
    placeholder="Contoh: Geopolitik memanas, harga minyak naik, pidato pejabat bank sentral..."
)

if st.button("🚀 Hasilkan Analisis & Prediksi Multi-Pair via AI"):
    if not gemini_api_key:
        st.error("⚠️ Silakan masukkan Gemini API Key di sidebar kiri terlebih dahulu!")
    else:
        try:
            with st.spinner(f"AI sedang menyusun skenario trading untuk {news_title}..."):
                prompt = f"""
                Anda adalah analis pasar keuangan senior (Macro Economist & Institutional Forex Trader) berpengalaman 20+ tahun.
                
                Buatkan analisis skenario terintegrasi sebelum rilis berita berikut:
                - Berita: {news_title} (Mata Uang Utama: {currency_target})
                - Data Perkiraan (Forecast): {forecast_val}
                - Data Sebelumnya (Previous): {previous_val}
                - Pasangan Mata Uang Target: {', '.join(selected_pairs)}
                - Catatan Sentimen Tambahan: {extra_context if extra_context else "Tidak ada"}

                Berikan output berbentuk laporan terstruktur dengan format Markdown:
                ### 1. 📌 Rangkuman Ekspektasi Pasar (Pre-Market Sentiment)
                ### 2. ⚡ Skenario Rilis Data (Hawkish vs Dovish)
                ### 3. 🎯 Prediksi Bias Per Pair (Tabel Skenario A & B)
                ### 4. 🛡️ Strategi Eksekusi Aman (Risk Management)
                """
                response = model.generate_content(prompt)
                st.success("✅ Analisis Berhasil Dibuat!")
                st.markdown(response.text)
        except Exception as e:
            st.error(f"Gagal memproses analisis AI: {e}")
