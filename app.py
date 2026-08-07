import google.generativeai as genai
import pandas as pd
import streamlit as st

# ==========================================
# 1. KONFIGURASI APLIKASI
# ==========================================
st.set_page_config(page_title="AI Multi-Pair News Predictor", layout="wide")
st.title("🤖 AI Fundamental News & Multi-Pair Predictor")
st.caption("Analisis Skenario Dampak Berita High-Impact Secara Real-Time Menggunakan AI")

# ==========================================
# 2. SISTEM OTOMATISASI API KEY
# ==========================================
st.sidebar.header("⚙️ Status Sistem AI")

gemini_api_key = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        gemini_api_key = st.secrets["GEMINI_API_KEY"]
except:
    pass

if not gemini_api_key:
    st.sidebar.warning("⚠️ API Key belum tersimpan di Secrets.")
    gemini_api_key = st.sidebar.text_input("Masukkan Gemini API Key Secara Manual:", type="password")

model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        # Kita panggil model utamanya terlebih dahulu
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        st.sidebar.success("✅ AI Engine Online & Siap Digunakan!")
    except Exception as e:
        st.sidebar.error("❌ API Key tidak valid. Silakan periksa kembali.")
else:
    st.sidebar.error("Sistem AI Offline. Butuh API Key.")

# ==========================================
# 3. KALENDER BERITA MENDATANG (PRESET)
# ==========================================
st.subheader("📅 Pilih Berita High Impact (Kalender Ekonomi)")
st.info("Pilih jadwal berita di bawah ini untuk mengisi data secara otomatis, atau pilih 'Isi Manual'.")

news_template = st.selectbox(
    "Pilih Berita yang Akan Rilis:",
    [
        "📝 Custom / Isi Manual",
        "🇺🇸 US Non-Farm Payrolls (NFP)",
        "🇺🇸 US Consumer Price Index (CPI)",
        "🇺🇸 FOMC Economic Projections & Fed Funds Rate",
        "🇬🇧 BOE Interest Rate Decision",
        "🇯🇵 BOJ Press Conference & Rate"
    ]
)

# ==========================================
# 4. FORM INPUT DATA BERITA
# ==========================================
st.subheader("📰 Data Konsensus & Aktual")

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
# 5. PILIHAN PAIR & GENERATOR PREDIKSI AI
# ==========================================
st.subheader("💱 Target Pairs & Sentimen Market")
selected_pairs = st.multiselect(
    "Pilih Pair Forex / Commodity yang Ingin Di-Analisa:",
    ["XAU/USD (Gold)", "USD/JPY", "GBP/USD", "EUR/USD", "AUD/USD", "BTC/USD"],
    default=["XAU/USD (Gold)", "USD/JPY"] if default_curr == "USD" else [f"{default_curr}/USD"] if default_curr != "JPY" else ["USD/JPY"]
)

extra_context = st.text_area(
    "Isu Sentimen Terkini (Opsional - Sangat Disarankan):",
    placeholder="Contoh: Geopolitik sedang memanas, harga minyak melonjak, atau ada pidato pejabat bank sentral kemarin..."
)

if st.button("🚀 Hasilkan Analisis & Prediksi Multi-Pair via AI", use_container_width=True):
    if not model:
        st.error("⚠️ AI Engine belum siap. Pastikan API Key sudah dimasukkan dengan benar!")
    else:
        try:
            with st.spinner(f"AI sedang menganalisis jutaan data fundamental untuk menyusun skenario {news_title}..."):
                prompt = f"""
                Anda adalah analis pasar keuangan makro dan trader institusional senior dengan pengalaman lebih dari 20 tahun.
                
                Tugas Anda adalah membuatkan analisis skenario trading mendalam SEBELUM rilis berita berikut:
                - Nama Berita: {news_title} (Mata Uang Penggerak: {currency_target})
                - Data Perkiraan (Forecast): {forecast_val}
                - Data Sebelumnya (Previous): {previous_val}
                - Pair yang akan ditradingkan: {', '.join(selected_pairs)}
                - Sentimen Tambahan: {extra_context if extra_context else "Tidak ada catatan khusus, fokus pada teknikal makro ekonomi."}

                Tulis analisis Anda secara profesional, tajam, dan mudah dipahami dengan format Markdown berikut:
                
                ### 1. 📌 Rangkuman Ekspektasi Pasar (Pre-Market Sentiment)
                ### 2. ⚡ Skenario Rilis Data (Hawkish vs Dovish)
                ### 3. 🎯 Prediksi Bias Per Pair
                Buatkan tabel rapi format: | Instrumen | Skenario A (Kuat) | Skenario B (Lemah) | Alasan Fundamental |
                ### 4. 🛡️ Strategi Eksekusi & Manajemen Risiko
                """
                
                # Coba generate dengan model utama
                try:
                    response = model.generate_content(prompt)
                except Exception as model_err:
                    # Jika gagal (Error 404), otomatis beralih ke model gemini-pro
                    if "404" in str(model_err) or "not found" in str(model_err).lower():
                        fallback_model = genai.GenerativeModel("gemini-pro")
                        response = fallback_model.generate_content(prompt)
                    else:
                        raise model_err

                st.success("✅ Analisis Berhasil Dibuat!")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses data AI: {e}")
