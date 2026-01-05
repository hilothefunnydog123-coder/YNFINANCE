import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import google.generativeai as genai
from groq import Groq
from PIL import Image
import requests

# --- 1. GOOGLE SEARCH CONSOLE VERIFICATION ---
components.html(
    f"""<script>
        var meta = document.createElement('meta');
        meta.name = "google-site-verification";
        meta.content = "HTd_e07Z3vt7rxoCVHyfti8A1mm9sWs_eRSETKtN-BY";
        parent.document.getElementsByTagName('head')[0].appendChild(meta);
    </script>""", height=0,
)

# --- 2. CONFIG & SECRETS ---
st.set_page_config(page_title="YNFINANCE", page_icon="🌱", layout="wide")

groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"]) if "GROQ_API_KEY" in st.secrets else None
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    vision_model = genai.GenerativeModel('gemini-2.0-flash')

# --- 3. LOGIC ENGINES ---
@st.cache_data(ttl=900)
def get_sp500_data():
    # Scrapes S&P 500 Tickers
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tickers = pd.read_html(url)[0]['Symbol'].str.replace('.', '-').tolist()
    # Batch download (First 50 for speed)
    data = yf.download(tickers[:50], period="2mo", group_by='ticker', progress=False)
    
    results = []
    for t in tickers[:50]:
        try:
            df = data[t]
            close = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            change = ((close - prev_close) / prev_close) * 100
            
            # Technical Logic for Buy/Sell/Neutral
            ema9 = ta.ema(df['Close'], length=9).iloc[-1]
            ema21 = ta.ema(df['Close'], length=21).iloc[-1]
            
            if ema9 > ema21 * 1.01: signal = "STRONG BUY"
            elif ema9 > ema21: signal = "BUY"
            elif ema9 < ema21 * 0.99: signal = "STRONG SELL"
            elif ema9 < ema21: signal = "SELL"
            else: signal = "NEUTRAL"
            
            results.append({"Ticker": t, "Price": round(close, 2), "Change %": round(change, 2), "Signal": signal})
        except: continue
    return pd.DataFrame(results)

def color_signals(val):
    color = '#2ecc71' if 'BUY' in val else '#e74c3c' if 'SELL' in val else '#95a5a6'
    return f'background-color: {color}; color: white; font-weight: bold'

# --- 4. THE INTERFACE ---
st.title("🌱 YNFINANCE | Market Intelligence")

tab1, tab2, tab3 = st.tabs(["📊 Market Pulse", "🤖 AI Advisor", "📸 Vision Scan"])

with tab1:
    st.subheader("S&P 500 Signal Scanner")
    pulse_df = get_sp500_data()
    st.dataframe(
        pulse_df.style.applymap(color_signals, subset=['Signal'])
        .background_gradient(subset=['Change %'], cmap='RdYlGn'),
        use_container_width=True, height=600, hide_index=True
    )

with tab2:
    st.subheader("AI Trade Strategist")
    ticker = st.text_input("Enter Ticker (e.g. AAPL):", value="NVDA").upper()
    if st.button("Get AI Analysis"):
        df_mini = yf.download(ticker, period="1mo")
        context = df_mini.tail(10).to_string()
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Analyze this data for {ticker} and provide a trade plan: {context}"}]
        )
        st.write(response.choices[0].message.content)

with tab3:
    st.subheader("Vision Chart Analysis")
    file = st.file_uploader("Upload Chart Screenshot", type=['png', 'jpg', 'jpeg'])
    if file:
        img = Image.open(file)
        st.image(img, use_container_width=True)
        if st.button("Run AI Vision Scan"):
            res = vision_model.generate_content(["Identify support, resistance, and the current trend in this chart.", img])
            st.success(res.text)
