import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq
import google.generativeai as genai
import requests
import base64
from datetime import datetime
from PIL import Image

# --- 1. SETUP & BRANDING ---
st.set_page_config(page_title="YNFINANCE Pro", layout="wide", page_icon="🌱")

# Connect to Groq (Text Only)
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Missing GROQ_API_KEY in Secrets!")

# Connect to Google Gemini (For Chart Vision)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    vision_model = genai.GenerativeModel('gemini-2.0-flash')
else:
    st.warning("Missing GEMINI_API_KEY. Chart analysis will be disabled.")

# --- 2. DATA ENGINE ---
@st.cache_data(ttl=900)
def get_market_master():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers)
        tickers = pd.read_html(resp.text)[0]['Symbol'].str.replace('.', '-').tolist()
        data = yf.download(tickers, period="2d", interval="1d", group_by='ticker', progress=False)
        results = []
        for t in tickers:
            try:
                current = data[t]['Close'].iloc[-1]
                prev = data[t]['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                results.append({
                    "Ticker": t, "Price": round(current, 2), "Change %": round(change, 2),
                    "Signal": "🟢 Strong Buy" if change > 2.5 else "🟡 Hold" if change > -1 else "🔴 Sell"
                })
            except: continue
        return pd.DataFrame(results).sort_values(by="Change %", ascending=False)
    except Exception as e:
        st.error(f"Data Sync Error: {e}"); return pd.DataFrame()

# --- 3. UI DASHBOARD ---
st.title("🌱 YNFINANCE")
tab1, tab2, tab3 = st.tabs(["📊 Market Scanner", "🧠 AI Advisor", "📸 Chart Vision"])

with tab1:
    st.subheader("Live Market Signals")
    search = st.text_input("Find a specific ticker:").upper()
    data_df = get_market_master()
    display_df = data_df[data_df['Ticker'] == search] if search else data_df
    st.dataframe(display_df.style.background_gradient(subset=["Change %"], cmap="RdYlGn"), use_container_width=True, height=500)

with tab2:
    st.subheader("AI Financial Intelligence")
    query = st.text_area("What's on your mind?")
    if st.button("Consult AI"):
        with st.spinner("Processing..."):
            chat = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": query}])
            st.info(chat.choices[0].message.content)

# --- THE FIXED CHART ANALYZER ---
with tab3:
    st.subheader("Technical Vision Analysis (Gemini 2.0)")
    st.write("Upload a chart for pattern recognition and Buy/Sell signals.")
    img_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
    
    if img_file:
        img = Image.open(img_file)
        st.image(img, width=700, caption="Uploaded Chart")
        
        if st.button("Run Gemini Analysis"):
            with st.spinner("Gemini is reading the candles..."):
                try:
                    # Gemini handles PIL images directly—no base64 hacks needed
                    prompt = "You are an expert technical analyst. Look at this stock chart. Identify key support/resistance, RSI/MACD if visible, and give a clear Buy/Sell/Hold recommendation with target prices."
                    response = vision_model.generate_content([prompt, img])
                    st.success("### Analysis Results")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Vision Error: {e}")

st.divider()
st.caption("YNFINANCE Global Markets Data | Updates every 15 minutes")

