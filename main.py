from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import ta
import numpy as np

# Inisialisasi Aplikasi FastAPI
app = FastAPI(title="AI XAU/USD Analyzer API - REAL DATA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    mode: str # scalping, intraday, swing

def get_real_market_data(mode: str) -> pd.DataFrame:
    """
    Mengambil data XAU/USD (Menggunakan Gold Futures GC=F di Yahoo Finance)
    """
    # Mapping timeframe ke format Yahoo Finance
    if mode == "scalping":
        interval = "5m"  # 5 Menit TF
        period = "5d"    # Ambil 5 hari ke belakang
    elif mode == "intraday":
        interval = "1h"  # 1 Jam TF
        period = "1mo"   # 1 bulan ke belakang
    else: # swing
        interval = "1d"  # 1 Hari TF
        period = "1y"    # 1 tahun ke belakang

    try:
        # Menarik data dari Yahoo Finance
        df = yf.download(tickers='GC=F', period=period, interval=interval, progress=False)
        
        # Flatten Multi-Index jika YFinance versi baru mengembalikannya
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def ai_trading_logic(df: pd.DataFrame, mode: str):
    """
    Menganalisa DataFrame menggunakan Indikator Teknikal.
    """
    if df is None or len(df) < 200:
        return None # Butuh minimal 200 candle untuk EMA 200

    # 1. Kalkulasi Indikator
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
    df['EMA_200'] = ta.trend.ema_indicator(df['Close'], window=200)
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    
    # 2. Kalkulasi Area Support & Resistance (SND/SNR)
    window_snr = 20 if mode == "intraday" else (10 if mode == "scalping" else 50)
    df['Support'] = df['Low'].rolling(window=window_snr).min()
    df['Resistance'] = df['High'].rolling(window=window_snr).max()

    # Ambil baris data terakhir (Current Market)
    current = df.iloc[-1]
    current_price = float(current['Close'])
    atr = float(current['ATR'])
    support = float(current['Support'])
    resistance = float(current['Resistance'])
    ema50 = float(current['EMA_50'])
    ema200 = float(current['EMA_200'])

    # 3. Identifikasi Tren
    if ema50 > ema200 and current_price > ema50:
        trend = "Bullish ↗️"
    elif ema50 < ema200 and current_price < ema50:
        trend = "Bearish ↘️"
    else:
        trend = "Sideways ➡️"

    # 4. Logika Eksekusi Trading
    signal = "WAIT"
    entry = None
    sl = None
    tp = None
    reason = "Harga sedang berada di tengah pergerakan (No Man's Land). Algoritma menyarankan tunggu harga mendekati area SND (Support/Resistance)."

    rr_multiplier = 1.5 if mode == "scalping" else (2.0 if mode == "intraday" else 3.0)
    proximity_tolerance = atr * 0.8 # Jarak toleransi harga ke area S/R

    # Skenario BUY (Tren Naik + Harga Pullback ke Support)
    if trend == "Bullish ↗️" and (current_price - support) <= proximity_tolerance:
        signal = "BUY"
        entry = current_price
        sl = support - (atr * 0.5) # SL sedikit di bawah support (buffer)
        tp = entry + ((entry - sl) * rr_multiplier)
        reason = f"Tren terdeteksi Bullish (EMA50 > EMA200). Harga mengalami *pullback* mendekati area Support kunci di {round(support,2)}. Risiko terukur menggunakan volatilitas ATR."

    # Skenario SELL (Tren Turun + Harga Pullback ke Resistance)
    elif trend == "Bearish ↘️" and (resistance - current_price) <= proximity_tolerance:
        signal = "SELL"
        entry = current_price
        sl = resistance + (atr * 0.5) # SL sedikit di atas resistance
        tp = entry - ((sl - entry) * rr_multiplier)
        reason = f"Tren terdeteksi Bearish (EMA50 < EMA200). Harga tertahan di area Resistance / Supply di {round(resistance,2)}. Setup *trend-following* aktif."

    return {
        "current_price": round(current_price, 2),
        "trend": trend,
        "signal": signal,
        "entry": round(entry, 2) if entry else "-",
        "stop_loss": round(sl, 2) if sl else "-",
        "take_profit": round(tp, 2) if tp else "-",
        "reasoning": reason
    }

@app.post("/analyze")
async def analyze_market(req: AnalyzeRequest):
    valid_modes = ["scalping", "intraday", "swing"]
    if req.mode not in valid_modes:
        raise HTTPException(status_code=400, detail="Mode tidak valid.")
    
    # Tarik Data Market Asli
    df = get_real_market_data(req.mode)
    
    if df is None:
        raise HTTPException(status_code=500, detail="Gagal mengambil data dari penyedia pasar (Market Provider).")

    # Proses Logika AI
    result = ai_trading_logic(df, req.mode)
    
    if result is None:
        raise HTTPException(status_code=500, detail="Data market tidak cukup untuk dianalisa (Butuh data lebih panjang).")

    # Kembalikan ke Frontend
    return {
        "timeframe_mode": req.mode.upper(),
        "market_condition": {
            "current_price": result["current_price"],
            "trend": result["trend"]
        },
        "recommendation": {
            "signal": result["signal"],
            "entry": result["entry"],
            "stop_loss": result["stop_loss"],
            "take_profit": result["take_profit"],
            "reasoning": result["reasoning"]
        }
    }

@app.get("/")
async def root():
    return {"message": "AI XAU/USD Analyzer Real-Data Backend is ONLINE 🟢"}
