import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import google.generativeai as genai
from groq import Groq
from PIL import Image
import requests
import os

# 1. Paste the EXACT filename Google gave you here
GOOGLE_VERIFY_FILE = "google335b1359243f9e39.html" 

# 2. Paste the EXACT content inside that file here (usually "google-site-verification: google12345...")
GOOGLE_VERIFY_CONTENT = "google-site-verification: google335b1359243f9e39.html"

# This logic handles the "download" request from Google's bot
if st.query_params.get("verify") == "true":
    st.write(GOOGLE_VERIFY_CONTENT)
    st.stop()
# --- 1. GOOGLE SEARCH CONSOLE TAG (UPDATED) ---
components.html(
    f"""<script>
        var meta = document.createElement('meta');
        meta.name = "google-site-verification";
        meta.content = "HTd_e07Z3vt7rxoCVHyfti8A1mm9sWs_eRSETKtN-BY";
        parent.document.getElementsByTagName('head')[0].appendChild(meta);
    </script>""", height=0,
)

# --- 2. APP CONFIG ---
st.set_page_config(page_title="YNFINANCE | Elite Scanner", page_icon="🌱", layout="wide")

# API Setup
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"]) if "GROQ_API_KEY" in st.secrets else None
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    vision_model = genai.GenerativeModel('gemini-2.0-flash')

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=3600)
def get_full_sp500_ranked():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # Get the tickers
    response = requests.get(url, headers=headers)
    tickers = pd.read_html(response.text)[0]['Symbol'].str.replace('.', '-').tolist()
    
    # Download data for the whole list
    data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
    
    ranked_list = []
    for t in tickers:
        try:
            df = data[t]
            current_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2]
            pct_change = ((current_price - prev_price) / prev_price) * 100
            
            # Simple Signal Logic based on daily strength
            if pct_change > 2.5: sig = "STRONG BUY"
            elif pct_change > 0.5: sig = "BUY"
            elif pct_change < -2.5: sig = "STRONG SELL"
            elif pct_change < -0.5: sig = "SELL"
            else: sig = "NEUTRAL"
            
            ranked_list.append({
                "Ticker": t, 
                "Price": round(current_price, 2), 
                "Change %": round(pct_change, 2), 
                "Signal": sig
            })
        except: continue
        
    return pd.DataFrame(ranked_list).sort_values(by="Change %", ascending=False)

def signal_color(s):
    color = '#00c805' if 'BUY' in s else '#ff3b30' if 'SELL' in s else '#8e8e93'
    return f'background-color: {color}; color: white; font-weight: bold; border-radius: 5px;'

# --- 4. UI ---
st.title("🌱 YNFINANCE")

tab1, tab2, tab3 = st.tabs(["📊 Market Pulse", "🤖 AI Advisor", "📸 Vision Scan"])

with tab1:
    st.subheader("S&P 500 Performance: Ranked Best to Worst")
    with st.spinner("Analyzing 500 stocks..."):
        df_ranked = get_full_sp500_ranked()
        st.dataframe(
            df_ranked.style.map(signal_color, subset=['Signal'])
            .background_gradient(subset=['Change %'], cmap='RdYlGn'),
            use_container_width=True, height=800, hide_index=True
        )

with tab2:
    st.subheader("AI Trading Advisor")
    ticker_input = st.text_input("Enter Ticker:", value="NVDA").upper()
    if st.button("Get AI Analysis"):
        hist = yf.download(ticker_input, period="1mo")
        chat = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Analyze {ticker_input}: {hist.tail(10).to_string()}"}]
        )
        st.write(chat.choices[0].message.content)

with tab3:
    st.subheader("Vision Chart Analysis")
    uploaded_file = st.file_uploader("Upload Chart Screenshot", type=['png', 'jpg', 'jpeg'])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        if st.button("Run AI Vision Scan"):
            res = vision_model.generate_content(["Provide technical analysis for this chart.", img])
            st.success(res.text)

