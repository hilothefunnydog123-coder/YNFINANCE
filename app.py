import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import google.generativeai as genai
from groq import Groq
from lightweight_charts_v5 import lightweight_charts_v5_component
from PIL import Image
import requests
from datetime import datetime

# --- 1. SEO & PAGE CONFIGURATION ---
st.set_page_config(
    page_title="YNFINANCE | AI Stock Intelligence & Trade Signals",
    page_icon="🌱",
    layout="wide",
    menu_items={
        'About': "# YNFINANCE: Elite AI-Powered Technical Analysis and Market Intelligence."
    }
)

# Initialize API Clients
if "GROQ_API_KEY" in st.secrets:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Missing GROQ_API_KEY in Secrets!")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    vision_model = genai.GenerativeModel('gemini-2.0-flash')
else:
    st.warning("Missing GEMINI_API_KEY. Vision Analysis disabled.")

# --- 2. DATA ENGINES ---
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
            c, p = data[t]['Close'].iloc[-1], data[t]['Close'].iloc[-2]
            ch = ((c - p) / p) * 100
            pulse.append({"Ticker": t, "Price": round(c, 2), "Change %": round(ch, 2)})
        except: continue
    return pd.DataFrame(pulse).sort_values(by="Change %", ascending=False)

def get_chart_data(symbol):
    df = yf.download(symbol, period="1y", interval="1d")
    if df.empty: return None
    df['EMA9'] = ta.ema(df['Close'], length=9)
    df['EMA21'] = ta.ema(df['Close'], length=21)
    df['Signal'] = 0
    df.loc[(df['EMA9'] > df['EMA21']) & (df['EMA9'].shift(1) <= df['EMA21'].shift(1)), 'Signal'] = 1
    return df

# --- 3. UI LAYOUT ---
st.title("🌱 YNFINANCE")
st.markdown("### AI-Powered Market Intelligence & Trade Signals")

tab1, tab2, tab3 = st.tabs(["📊 Market Pulse", "📈 Elite Charting", "📸 AI Vision"])

# TAB 1: MARKET SCANNER
with tab1:
    st.subheader("Daily S&P 500 Performance")
    pulse_df = get_market_pulse()
    st.dataframe(pulse_df.style.background_gradient(subset=["Change %"], cmap="RdYlGn"), 
                 use_container_width=True, height=500, hide_index=True)

# TAB 2: ELITE CHARTING & SIGNALS
with tab2:
    ticker = st.text_input("Enter Ticker:", value="NVDA").upper()
    df = get_chart_data(ticker)
    
    if df is not None:
        # Prepare Chart Data
        candles = [{"time": str(d.date()), "open": float(r['Open']), "high": float(r['High']), 
                    "low": float(r['Low']), "close": float(r['Close'])} for d, r in df.iterrows()]
        
        markers = []
        for i in range(len(df)):
            if df['Signal'].iloc[i] == 1:
                markers.append({"time": str(df.index[i].date()), "position": "belowBar", 
                                "color": "#2196F3", "shape": "arrowUp", "text": "BUY"})

        lightweight_charts_v5_component(
            charts=[{
                "chart": {"layout": {"background": {"color": "#FFFFFF"}}},
                "series": [
                    {"type": "Candlestick", "data": candles, "markers": markers},
                    {"type": "Line", "data": [{"time": str(d.date()), "value": float(v)} for d, v in df['EMA9'].dropna().items()], "options": {"color": "#2196F3"}},
                    {"type": "Line", "data": [{"time": str(d.date()), "value": float(v)} for d, v in df['EMA21'].dropna().items()], "options": {"color": "#FF9800"}}
                ],
            }], height=500
        )
        
        if st.button("Generate AI Alpha Report"):
            context = df.tail(10).to_string()
            chat = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"Analyze these metrics for {ticker} and provide a trade plan: {context}"}]
            )
            st.info(chat.choices[0].message.content)

# TAB 3: VISION ANALYZER
with tab3:
    st.subheader("Technical Vision Analysis")
    img_file = st.file_uploader("Upload Chart Screenshot", type=['png', 'jpg', 'jpeg'])
    if img_file:
        img = Image.open(img_file)
        st.image(img, width=700)
        if st.button("Run Vision Analysis"):
            with st.spinner("Gemini is reading the patterns..."):
                prompt = "Identify trends, support/resistance, and provide a Buy/Sell signal based on this chart."
                response = vision_model.generate_content([prompt, img])
                st.success(response.text)

st.divider()
st.caption("YNFINANCE Global Markets Data | Professional Grade Intelligence")
