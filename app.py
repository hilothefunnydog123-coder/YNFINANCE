import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from groq import Groq
from lightweight_charts_v5 import lightweight_charts_v5_component
from datetime import datetime, timedelta

# --- 1. SETUP ---
st.set_page_config(page_title="YNFINANCE Elite", layout="wide", page_icon="📈")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. THE STRATEGY ENGINE (Custom Indicators) ---
def calculate_elite_signals(symbol):
    df = yf.download(symbol, period="1y", interval="1d")
    if df.empty: return None
    
    # Custom Indicator: EMA 9 & 21 (The "Trend Cross")
    df['EMA9'] = ta.ema(df['Close'], length=9)
    df['EMA21'] = ta.ema(df['Close'], length=21)
    
    # Entry Logic: Fast EMA crosses above Slow EMA
    df['Signal'] = (df['EMA9'] > df['EMA21']) & (df['EMA9'].shift(1) <= df['EMA21'].shift(1))
    return df

# --- 3. UI DASHBOARD ---
st.title("🌱 YNFINANCE")
ticker = st.text_input("Enter Symbol:", value="NVDA").upper()

if ticker:
    df = calculate_elite_signals(ticker)
    
    if df is not None:
        # Format Candles for TradingView
        candles = [
            {
                "time": str(date.date()), "open": float(row["Open"]),
                "high": float(row["High"]), "low": float(row["Low"]),
                "close": float(row["Close"])
            }
            for date, row in df.iterrows()
        ]

        # Generate Markers (Arrows) and RR Rectangles
        markers = []
        rectangles = []
        
        for date, row in df.iterrows():
            if row['Signal']:
                # 1. Add Entry Arrow
                markers.append({
                    "time": str(date.date()), "position": "belowBar",
                    "color": "#2196F3", "shape": "arrowUp", "text": "BUY ENTRY"
                })
                
                # 2. Add RR Box (Risk/Reward)
                entry_price = float(row["Close"])
                # Let's set a 2:1 RR Ratio (5% target, 2.5% stop)
                rectangles.append({
                    "from": str(date.date()), 
                    "to": str((date + timedelta(days=10)).date()), # Extends 10 days out
                    "price_start": entry_price * 0.975, # Stop Loss Red Zone
                    "price_end": entry_price * 1.05,    # Take Profit Green Zone
                    "color": "rgba(76, 175, 80, 0.15)"  # Soft green highlight
                })

        # --- 4. RENDER ELITE CHART ---
        lightweight_charts_v5_component(
            name="YNFINANCE Elite Chart",
            charts=[{
                "chart": {
                    "layout": {"background": {"color": "#FFFFFF"}, "textColor": "#333"},
                    "grid": {"vertLines": {"visible": False}, "horzLines": {"color": "#f0f0f0"}}
                },
                "series": [
                    {
                        "type": "Candlestick", 
                        "data": candles, 
                        "markers": markers,
                        "options": {"upColor": "#4CAF50", "downColor": "#FF5252"}
                    },
                    # Overlay your EMA indicators
                    {"type": "Line", "data": [{"time": str(d.date()), "value": float(v)} for d, v in df['EMA9'].dropna().items()], "options": {"color": "#2196F3", "lineWidth": 1}},
                    {"type": "Line", "data": [{"time": str(d.date()), "value": float(v)} for d, v in df['EMA21'].dropna().items()], "options": {"color": "#FF9800", "lineWidth": 1}}
                ],
                "height": 600
            }],
            height=600
        )

# --- 5. AI ADVISOR ---
st.divider()
if st.button("AI Deep Scan of Chart"):
    last_data = df.tail(10).to_string()
    ai_resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"Analyze these recent metrics for {ticker} and give an Elite trade plan: {last_data}"}]
    )
    st.info(ai_resp.choices[0].message.content)

