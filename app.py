import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from fredapi import Fred

st.set_page_config(page_title="Macro News & Prediction Dashboard", layout="wide")
st.title("📊 Macroeconomic News Dashboard & XAU/USD Predictor")

fred_api_key = st.sidebar.text_input(
    "Masukkan FRED API Key:", type="password", value=""
)

news_option = st.sidebar.selectbox(
    "Pilih Indikator Berita:",
    [
        "Non-Farm Payrolls (PAYEMS)",
        "Unemployment Rate (UNRATE)",
        "CPI Inflation (CPIAUCSL)",
        "Fed Funds Rate (FEDFUNDS)",
    ],
)

indicator_code_map = {
    "Non-Farm Payrolls (PAYEMS)": "PAYEMS",
    "Unemployment Rate (UNRATE)": "UNRATE",
    "CPI Inflation (CPIAUCSL)": "CPIAUCSL",
    "Fed Funds Rate (FEDFUNDS)": "FEDFUNDS",
}

series_id = indicator_code_map[news_option]

st.subheader("🎯 Live Prediction Engine: NFP Malam Ini")

col1, col2, col3 = st.columns(3)
with col1:
    forecast_val = st.number_input("Forecast (Konsensus):", value=185)
with col2:
    previous_val = st.number_input("Previous (Bulan Lalu):", value=206)
with col3:
    actual_input = st.number_input("Actual (Diisi Saat Rilis):", value=0)

if actual_input != 0:
    st.markdown("### 🤖 Hasil Analisis Otomatis Rilis Data:")
    if actual_input > forecast_val and actual_input > previous_val:
        st.error(
            "🔴 **PREDIKSI: BEARISH XAU/USD (BULLISH USD)**\n\n"
            "Data Tenaga Kerja Sangat Kuat. Potensi Fed menunda pemangkasan suku bunga."
        )
    elif actual_input < forecast_val and actual_input < previous_val:
        st.success(
            "🟢 **PREDIKSI: BULLISH XAU/USD (BEARISH USD)**\n\n"
            "Data Tenaga Kerja Lemah. Mendorong ekspektasi pemangkasan suku bunga Fed (*Dovish*)."
        )
    else:
        st.warning(
            "🟡 **PREDIKSI: MIXED / WHIPSAW (HATI-HATI)**\n\n"
            "Data mendekati perkiraan atau bercampur. Kemungkinan lonjakan 2 arah."
        )

st.divider()
st.subheader(f"📈 Histori Tahunan Data: {news_option}")

if fred_api_key:
    try:
        fred = Fred(api_key=fred_api_key)
        df_data = fred.get_series(series_id)
        df = pd.DataFrame(df_data, columns=["Nilai"]).reset_index()
        df.rename(columns={"index": "Tanggal"}, inplace=True)
        df["Tanggal"] = pd.to_datetime(df["Tanggal"])
        df_filtered = df[df["Tanggal"] >= "2005-01-01"]

        fig = px.line(
            df_filtered,
            x="Tanggal",
            y="Nilai",
            title=f"Tren Histori {news_option} (2005 - Sekarang)",
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error FRED API Key: {e}")
else:
    st.info("💡 Masukkan FRED API Key di sidebar untuk memuat grafik historis 20 tahun.")
