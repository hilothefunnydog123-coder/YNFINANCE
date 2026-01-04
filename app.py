import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from groq import Groq
from lightweight_charts_v5 import lightweight_charts_v5_component
import requests
from datetime import timedelta

# --- 1. SETUP ---
st.set_page_config(page_title="YNFINANCE Elite", layout="wide", page_icon="🌱")

if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Missing GROQ_API_KEY in Secrets!")

# --- 2. DATA ENGINE ---
@st.cache_data(ttl=900)
def get_pulse():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    tickers = pd.read_html(resp.text)[0]['Symbol'].str.replace('.', '-').tolist()
    data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
    pulse = []
    for t in tickers:
        try:
            c, p = data[t]['Close'].iloc[-1], data[t]['Close'].iloc[-2]
            pulse.append({"Ticker": t, "Price": round(c, 2), "Change %": round(((c-p)/p)*100, 2)})
        except: continue
    return pd.DataFrame(pulse).sort_values(by="Change %", ascending=False)

def get_elite_chart(symbol):
    df = yf.download(symbol, period="1y", interval="1d")
    if df.empty: return None
    df['EMA9'] = ta.ema(df['Close'], length=9)
    df['EMA21'] = ta.ema(df['Close'], length=21)
    # Signal: 1 for Buy, 0 for None
    df['Signal'] = 0
    df.loc[(df['EMA9'] > df['EMA21']) & (df['EMA9'].shift(1) <= df['EMA21'].shift(1)), 'Signal'] = 1
    return df

# --- 3. UI ---
st.title("🌱 YNFINANCE")
tab1, tab2, tab3 = st.tabs(["📊 Pulse", "📈 Elite Chart", "🧠 AI Advisor"])

with tab1:
    st.dataframe(get_pulse(), use_container_width=True, hide_index=True)

with tab2:
    ticker = st.text_input("Symbol", value="NVDA").upper()
    df = get_elite_chart(ticker)
    
    if df is not None:
        candles = [{"time": str(d.date()), "open": float(r['Open']), "high": float(r['High']), 
                    "low": float(r['Low']), "close": float(r['Close'])} for d, r in df.iterrows()]
        
        # FIXED LOOP: Uses .loc or .at to ensure we get a single value, not a Series
        markers = []
        for i in range(len(df)):
            if df['Signal'].iloc[i] == 1:
                markers.append({
                    "time": str(df.index[i].date()), 
                    "position": "belowBar", "color": "#2196F3", 
                    "shape": "arrowUp", "text": "BUY"
                })

        lightweight_charts_v5_component(
            charts=[{
                "chart": {"layout": {"background": {"color": "#FFFFFF"}}},
                "series": [
                    {"type": "Candlestick", "data": candles, "markers": markers},
                    {"type": "Line", "data": [{"time": str(d.date()), "value": float(v)} for d, v in df['EMA9'].dropna().items()], "options": {"color": "#2196F3"}},
                    {"type": "Line", "data": [{"time": str(d.date()), "value": float(v)} for d, v in df['EMA21'].dropna().items()], "options": {"color": "#FF9800"}}
                ],
            }], height=600
        )

with tab3:
    if st.button("Run AI Scan"):
        chat = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Analyze {ticker} based on recent EMA 9/21 cross."}]
        )
        st.info(chat.choices[0].message.content)
