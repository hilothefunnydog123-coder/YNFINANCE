import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from groq import Groq
from lightweight_charts_v5 import lightweight_charts_v5_component
from datetime import datetime, timedelta

# --- 1. SETUP ---
st.set_page_config(page_title="YNFINANCE Elite", layout="wide", page_icon="🌱")

# Connect to Groq
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Missing GROQ_API_KEY in Streamlit Secrets!")

# --- 2. THE STRATEGY ENGINE ---
@st.cache_data(ttl=3600) # Cache signals for 1 hour
def get_elite_data(symbol):
    df = yf.download(symbol, period="1y", interval="1d")
    if df.empty: return None
    
    # Custom Indicator: EMA 9 & 21
    df['EMA9'] = ta.ema(df['Close'], length=9)
    df['EMA21'] = ta.ema(df['Close'], length=21)
    
    # Fix the Signal: Use 1 and 0 instead of True/False to avoid Series errors
    df['Signal'] = 0
    df.loc[(df['EMA9'] > df['EMA21']) & (df['EMA9'].shift(1) <= df['EMA21'].shift(1)), 'Signal'] = 1
    return df

# --- 3. UI DASHBOARD ---
st.title("🌱 YNFINANCE")
ticker = st.text_input("Enter Symbol:", value="NVDA").upper()

if ticker:
    df = get_elite_data(ticker)
    
    if df is not None:
        # Prepare Chart Data
        candles = [
            {"time": str(date.date()), "open": float(row["Open"]), "high": float(row["High"]), 
             "low": float(row["Low"]), "close": float(row["Close"])}
            for date, row in df.iterrows()
        ]

        markers = []
        # FIX: Loop properly using .itertuples() for speed and to avoid ValueErrors
        for row in df.itertuples():
            if getattr(row, "Signal") == 1:
                markers.append({
                    "time": str(row.Index.date()), 
                    "position": "belowBar",
                    "color": "#2196F3", 
                    "shape": "arrowUp", 
                    "text": "ENTRY"
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
                    {"type": "Line", "data": [{"time": str(d.date()), "value": float(v)} for d, v in df['EMA9'].dropna().items()], "options": {"color": "#2196F3", "lineWidth": 1}},
                    {"type": "Line", "data": [{"time": str(d.date()), "value": float(v)} for d, v in df['EMA21'].dropna().items()], "options": {"color": "#FF9800", "lineWidth": 1}}
                ],
                "height": 600
            }],
            height=600
        )

# --- 5. AI ADVISOR ---
st.divider()
if st.button("Run AI Alpha Scan"):
    with st.spinner("AI analyzing chart patterns..."):
        recent_context = df.tail(10).to_string()
        ai_resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"You are a Professional Technical Analyst. Analyze these recent daily prices and indicators for {ticker}. Give a clear trade plan with entry and exit: {recent_context}"}]
        )
        st.info(ai_resp.choices[0].message.content)
