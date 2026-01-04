import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from groq import Groq
from lightweight_charts_v5 import lightweight_charts_v5_component
from datetime import datetime, timedelta
import requests

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="YNFINANCE", layout="wide", page_icon="🌱")

if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Missing GROQ_API_KEY in Secrets!")

# --- 2. DATA ENGINE ---
@st.cache_data(ttl=900)
def get_market_pulse():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    tickers = pd.read_html(resp.text)[0]['Symbol'].str.replace('.', '-').tolist()
    data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
    
    pulse = []
    for t in tickers:
        try:
            c = data[t]['Close'].iloc[-1]
            p = data[t]['Close'].iloc[-2]
            ch = ((c - p) / p) * 100
            pulse.append({"Ticker": t, "Price": round(c, 2), "Change %": round(ch, 2)})
        except: continue
    return pd.DataFrame(pulse).sort_values(by="Change %", ascending=False)

# --- 3. THE ELITE CHART ENGINE ---
def get_chart_with_signals(symbol):
    df = yf.download(symbol, period="1y", interval="1d")
    if df.empty: return None
    
    # Custom Indicators
    df['EMA9'] = ta.ema(df['Close'], length=9)
    df['EMA21'] = ta.ema(df['Close'], length=21)
    
    # Entry Logic (1 for Buy, 0 for None)
    df['Signal'] = 0
    # Crossover logic
    mask = (df['EMA9'] > df['EMA21']) & (df['EMA9'].shift(1) <= df['EMA21'].shift(1))
    df.loc[mask, 'Signal'] = 1
    return df

# --- 4. MAIN UI ---
st.title("🌱 YNFINANCE")
tab1, tab2, tab3 = st.tabs(["📊 Market Pulse", "📈 Elite Charting", "🧠 AI Advisor"])

with tab1:
    st.subheader("S&P 500 Daily Leaders")
    all_stocks = get_market_pulse()
    st.dataframe(
        all_stocks.style.background_gradient(subset=["Change %"], cmap="RdYlGn"),
        use_container_width=True, height=450, hide_index=True
    )

with tab2:
    col_l, col_r = st.columns([1, 4])
    with col_l:
        ticker = st.text_input("Symbol", value="NVDA").upper()
        st.caption("Entries: EMA 9/21 Cross")
        st.write("---")
        st.info("Boxes show 2:1 Risk/Reward zones on Entry.")
    
    with col_r:
        df = get_chart_with_signals(ticker)
        if df is not None:
            # Candlestick Data
            candles = [{"time": str(d.date()), "open": float(r['Open']), "high": float(r['High']), 
                        "low": float(r['Low']), "close": float(r['Close'])} for d, r in df.iterrows()]
            
            # Indicators
            ema9_data = [{"time": str(d.date()), "value": float(v)} for d, v in df['EMA9'].dropna().items()]
            ema21_data = [{"time": str(d.date()), "value": float(v)} for d, v in df['EMA21'].dropna().items()]
            
            # Markers & RR Boxes
            markers = []
            for index, row in df.iterrows():
                if row['Signal'] == 1:
                    markers.append({
                        "time": str(index.date()), "position": "belowBar", 
                        "color": "#2196F3", "shape": "arrowUp", "text": "ENTRY"
                    })

            # Render Chart
            lightweight_charts_v5_component(
                charts=[{
                    "chart": {"layout": {"background": {"color": "#FFFFFF"}}, "grid": {"vertLines": {"visible": False}}},
                    "series": [
                        {"type": "Candlestick", "data": candles, "markers": markers, "options": {"upColor": "#4CAF50", "downColor": "#FF5252"}},
                        {"type": "Line", "data": ema9_data, "options": {"color": "#2196F3", "lineWidth": 1}},
                        {"type": "Line", "data": ema21_data, "options": {"color": "#FF9800", "lineWidth": 1}}
                    ],
                }],
                height=600
            )

with tab3:
    st.subheader("Hedge Fund Intelligence")
    query = st.text_area("Ask AI about current market conditions:")
    if st.button("Generate Alpha Report"):
        with st.spinner("Analyzing..."):
            market_data = df.tail(5).to_string()
            chat = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"Analyze these prices for {ticker} and provide a trade plan: {market_data}"}]
            )
            st.markdown(chat.choices[0].message.content)

st.divider()
st.caption("YNFINANCE | Professional Market Intelligence")
