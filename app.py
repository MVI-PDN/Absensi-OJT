import google.generativeai as genai
import pandas as pd
import streamlit as st

# ==========================================
# 1. KONFIGURASI APLIKASI
# ==========================================
st.set_page_config(
    page_title="AI Multi-Pair News & Bias Predictor", layout="wide"
)

st.title("🤖 AI Fundamental News & Multi-Pair Forex Predictor")
st.caption(
    "Analisis Skenario Dampak Berita High-Impact Tanpa Menunggu Input Detik Pertama"
)

# Sidebar
st.sidebar.header("⚙️ Pengaturan AI Engine")
gemini_api_key = st.sidebar.text_input(
    "Masukkan Gemini API Key:", type="password"
)

# Form Input Berita
st.subheader("📰 Data Berita High Impact Mendatang")

col1, col2, col3, col4 = st.columns(4)
with col1:
    news_title = st.text_input("Nama Berita:", value="Non-Farm Payrolls (NFP)")
with col2:
    currency_target = st.selectbox(
        "Mata Uang Utama:", ["USD", "JPY", "GBP", "EUR", "AUD"]
    )
with col3:
    forecast_val = st.text_input("Forecast (Konsensus):", value="185K")
with col4:
    previous_val = st.text_input("Previous (Bulan Lalu):", value="206K")

st.divider()

# Selected Pair Analysis Checklist
st.subheader("💱 Pilih Pair Forex/Commodity yang Ingin Di-Analisa AI")
selected_pairs = st.multiselect(
    "Target Pairs:",
    [
        "XAU/USD (Gold)",
        "USD/JPY",
        "GBP/USD",
        "EUR/USD",
        "USD/CAD",
        "AUD/USD",
    ],
    default=["XAU/USD (Gold)", "USD/JPY", "GBP/USD"],
)

extra_context = st.text_area(
    "Isu Sentimen Terkini (Opsional):",
    placeholder="Contoh: Geopolitik Timur Tengah memanas, Kenaikan Yield US10Y, Pidato Dovish Powell kemarin...",
)

# ==========================================
# 2. PROMPT AI GENERATOR
# ==========================================
if st.button("🚀 Hasilkan Analisis & Prediksi Multi-Pair via AI"):
    if not gemini_api_key:
        st.error(" Silakan masukkan Gemini API Key di sidebar kiri!")
    else:
        try:
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
            Anda adalah analis pasar keuangan senior (Macro Economist & Institutional Forex Trader) berpengalaman 20+ tahun.
            
            Tolong buatkan analisis skenario terintegrasi sebelum rilis berita berikut:
            - Berita: {news_title} (Mata Uang Utama: {currency_target})
            - Data Perkiraan (Forecast): {forecast_val}
            - Data Sebelumnya (Previous): {previous_val}
            - Pasangan Mata Uang Target: {', '.join(selected_pairs)}
            - Catatan Sentimen Tambahan: {extra_context if extra_context else "Tidak ada"}

            Berikan output berbentuk laporan terstruktur dengan format Markdown:
            
            ### 1. 📌 Rangkuman Ekspektasi Pasar (Pre-Market Sentiment)
            Singkat tentang apa yang diinginkan pasar dari {currency_target}.

            ### 2. ⚡ Skenario Rilis Data & Analisis Bias
            Buat 2 Skenario Utama:
            - **Skenario A (Data Aktual SANGAT KUAT / Hawkish {currency_target})**
            - **Skenario B (Data Aktual SANGAT LEMAH / Dovish {currency_target})**

            ### 3. 🎯 Prediksi Bias Per Pair (Tabel Ringkasan)
            Buat tabel untuk pair: {', '.join(selected_pairs)} dengan kolom:
            | Pair | Bias Skenario A (Kuat) | Bias Skenario B (Lemah) | Alasan Fundamental Singkat |

            ### 4. 🛡️ Strategi Eksekusi Aman (Risk Management)
            Tips bertindak sebelum vs sesudah berita rilis tanpa terjebak whipsaw/fakeout.
            """

            with st.spinner("AI sedang menganalisis korelasi pasar..."):
                response = model.generate_content(prompt)
                st.markdown(response.text)

        except Exception as e:
            st.error(f"Gagal memproses analisis AI: {e}")
