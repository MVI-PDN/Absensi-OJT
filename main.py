from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import random

# Inisialisasi Aplikasi FastAPI
app = FastAPI(title="AI XAU/USD Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hati-hati di production, ganti "*" dengan URL Frontend lu nanti
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    mode: str # scalping, intraday, swing

def generate_mock_market_data(mode: str):
    """
    Fungsi ini menyimulasikan data pergerakan XAU/USD.
    Nantinya fungsi ini diganti dengan fungsi request ke API Asli (misal: TwelveData).
    """
    base_price = round(random.uniform(2300.00, 2380.00), 2)
    
    # Menyesuaikan volatilitas (ATR buatan) berdasarkan timeframe/mode
    if mode == "scalping":
        atr = random.uniform(1.0, 3.0)   # Pergerakan kecil
    elif mode == "intraday":
        atr = random.uniform(3.0, 8.0)   # Pergerakan menengah
    else: # swing
        atr = random.uniform(8.0, 25.0)  # Pergerakan besar
        
    return {
        "current_price": base_price,
        "atr": atr,
        # Simulasi area Support (selalu lebih rendah dari harga sekarang)
        "support": round(base_price - random.uniform(atr, atr * 3), 2),
        # Simulasi area Resistance (selalu lebih tinggi dari harga sekarang)
        "resistance": round(base_price + random.uniform(atr, atr * 3), 2),
        "trend": random.choice(["Bullish", "Bearish", "Sideways"])
    }

def ai_trading_logic(data: dict, mode: str):
    """
    Fungsi utama AI untuk menentukan Sinyal, Entry, SL, dan TP.
    """
    signal = "WAIT"
    entry = None
    sl = None
    tp = None
    reason = "Kondisi market kurang ideal, tunggu konfirmasi lebih lanjut."

    current_price = data["current_price"]
    support = data["support"]
    resistance = data["resistance"]
    trend = data["trend"]
    atr = data["atr"]

    # Menentukan Risk Reward Ratio berdasarkan gaya trading
    rr_multiplier = 1.5 if mode == "scalping" else (2.0 if mode == "intraday" else 3.0)
    
    # Toleransi jarak harga ke Support/Resistance sebelum memutuskan Entry
    proximity_tolerance = atr * 0.8 

    # Logika Buy: Sedang Uptrend dan Harga mendekati area Support
    if trend == "Bullish" and (current_price - support) <= proximity_tolerance:
        signal = "BUY"
        entry = current_price
        # SL dipasang di bawah Support (ditambah sedikit buffer (ATR/2))
        sl = support - (atr * 0.5)
        # TP dihitung berdasarkan rasio Risk to Reward
        tp = entry + ((entry - sl) * rr_multiplier)
        reason = "Terdeteksi pola *pullback* pada tren Bullish mendekati area Demand (Support). Rejeksi terkonfirmasi."

    # Logika Sell: Sedang Downtrend dan Harga mendekati area Resistance
    elif trend == "Bearish" and (resistance - current_price) <= proximity_tolerance:
        signal = "SELL"
        entry = current_price
        # SL dipasang di atas Resistance (ditambah sedikit buffer (ATR/2))
        sl = resistance + (atr * 0.5)
        # TP dihitung berdasarkan rasio Risk to Reward
        tp = entry - ((sl - entry) * rr_multiplier)
        reason = "Terdeteksi tekanan jual (Seller) di area Supply (Resistance) pada tren Bearish. Momentum *breakdown* berlanjut."
        
    return {
        "signal": signal,
        "entry": round(entry, 2) if entry else None,
        "stop_loss": round(sl, 2) if sl else None,
        "take_profit": round(tp, 2) if tp else None,
        "reasoning": reason
    }

@app.post("/analyze")
async def analyze_market(req: AnalyzeRequest):
    valid_modes = ["scalping", "intraday", "swing"]
    if req.mode not in valid_modes:
        raise HTTPException(status_code=400, detail="Mode tidak valid. Pilih: scalping, intraday, atau swing.")
    
    # 1. Tarik Data Market (Saat ini masih pakai Simulator)
    market_data = generate_mock_market_data(req.mode)
    
    # 2. Proses data menggunakan Logika AI
    analysis_result = ai_trading_logic(market_data, req.mode)
    
    # 3. Kembalikan Response (JSON) ke Frontend
    return {
        "market": "XAU/USD",
        "timeframe_mode": req.mode.upper(),
        "market_condition": {
            "current_price": market_data["current_price"],
            "trend": market_data["trend"],
            "key_levels": {
                "support": market_data["support"],
                "resistance": market_data["resistance"]
            }
        },
        "recommendation": analysis_result
    }

@app.get("/")
async def root():
    return {"message": "AI XAU/USD Analyzer Backend is running. Status: ONLINE 🟢"}
