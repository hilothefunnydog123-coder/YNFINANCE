import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import google.generativeai as genai
from groq import Groq
from lightweight_charts_v5 import lightweight_charts_v5_component
from PIL import Image
import requests

# --- 1. GOOGLE SEARCH CONSOLE VERIFICATION ---
components.html(
    """
    <script>
        var meta = document.createElement('meta');
        meta.name = "google-site-verification";
        meta.content = "HTd_e07Z3vt7rxoCVHyfti8A1mm9sWs_eRSETKtN-BY";
        parent.document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
    """,
    height=0,
)

# --- 2. PAGE CONFIG & SECRETS ---
st.set_page_config(page_title="YNFINANCE", page_icon="🌱", layout="wide")

if "GROQ_API_KEY" in st.secrets:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    vision_model = genai.GenerativeModel('gemini-2.0-flash')

# --- 3. DATA FUNCTIONS ---
def get_chart_data(symbol):
    df = yf.download(symbol, period="1y", interval="1d")
    if df.empty: return None
    df['EMA9'] = ta.ema(df['Close'], length=9)
    df['EMA21'] = ta.ema(df['Close'], length=21)
    return df

# --- 4. MAIN INTERFACE ---
st.title("🌱 YNFINANCE")

tab1, tab2, tab3 = st.tabs(["📈 Chart & AI Advisor", "📸 Vision Scanner", "📊 Market Pulse"])

# TAB 1: CHART & CHATBOT
with tab1:
    ticker = st.text_input("Ticker Symbol:", value="NVDA").upper()
    df = get_chart_data(ticker)
    
    if df is not None:
        # Prepare Data
        candles = [{"time": str(d.date()), "open": float(r['Open']), "high": float(r['High']), 
                    "low": float(r['Low']), "close": float(r['Close'])} for d, r in df.iterrows()]
        
        # FIXED: Added the 'name' parameter to prevent TypeError
        lightweight_charts_v5_component(
            name="YN_Main_Chart",
            charts=[{
                "chart": {"layout": {"background": {"color": "#FFFFFF"}}},
                "series": [{"type": "Candlestick", "data": candles}]
            }], 
            height=450
        )
        
        if st.button("Ask AI Advisor"):
            context = df.tail(10).to_string()
            chat = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"Analyze {ticker} and give me a trade plan based on: {context}"}]
            )
            st.info(chat.choices[0].message.content)

# TAB 2: SCREENSHOT ANALYZER
with tab2:
    st.subheader("Analyze Chart Screenshot")
    img_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
    if img_file:
        img = Image.open(img_file)
        st.image(img, use_container_width=True)
        if st.button("Vision Scan"):
            response = vision_model.generate_content(["Analyze this chart for trade setups.", img])
            st.success(response.text)

# TAB 3: MARKET PULSE (Simplified)
with tab1:
    st.caption("Data provided by YFinance. Trade at your own risk.")
