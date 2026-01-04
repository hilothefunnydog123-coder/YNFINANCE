import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from groq import Groq
from lightweight_charts_v5 import lightweight_charts_v5_component
import requests

# --- 1. SETUP ---
st.set_page_config(page_title="YNFINANCE Elite", layout="wide", page_icon="🌱")

if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Missing GROQ_API_KEY in Streamlit Secrets!")

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
    df['Signal'] = 0
    # Set signal to 1 where EMA9 crosses EMA21
    df.loc[(df['EMA9'] > df['EMA21']) & (df['EMA9'].shift(1) <= df['EMA21'].shift(1)), 'Signal'] = 1
    return df

# --- 3. UI DASHBOARD ---
st.title("🌱 YNFINANCE")
tab1, tab2, tab3 = st.tabs(["📊 Market Pulse", "📈 Elite Chart", "🧠 AI Advisor"])

with tab1:
    st.dataframe(get_pulse(), use_container_width=True, hide_index=True)

with tab2:
    ticker = st.text_input("Symbol", value="NVDA").upper()
    df = get_elite_chart(ticker)
    
    if df is not None:
        # 1. Format Candles
        candles = [{"time": str(d.date()), "open": float(r['Open']), "high": float(r['High']), 
                    "low": float(r['Low']), "close": float(r['Close'])} for d, r in df.iterrows()]
        
        # 2. Extract Markers & RR Boxes
        markers = []
        rects = []
        
        # FIXED LOOP: Uses range and iloc to avoid ValueError
        for i in range(len(df)):
            if df['Signal'].iloc[i] == 1:
                entry_date = str(df.index[i].date())
                entry_price = float(df['Close'].iloc[i])
                
                # Add Entry Arrow
                markers.append({
                    "time": entry_date, "position": "belowBar", 
                    "color": "#2196F3", "shape": "arrowUp", "text": "BUY"
                })
                
                # Add RR Box (Green zone for Profit, Red zone for Stop)
                # target: +5%, stop: -2.5%
                rects.append({
                    "from": entry_date, 
                    "to": str((df.index[i] + pd.Timedelta(days=7)).date()),
                    "price_start": entry_price * 0.975,
                    "price_end": entry_price * 1.05,
                    "color": "rgba(76, 175, 80, 0.15)"
                })

        # 3. Render Chart
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
    if st.button("Run AI Deep Scan"):
        st.write("### AI Trade Analysis")
        # Send last 5 days of data to AI
        context = df.tail(5).to_string()
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Analyze these stock metrics for {ticker}: {context}"}]
        )
        st.info(completion.choices[0].message.content)

st.divider()
st.caption("YNFINANCE | Professional Intelligence")
