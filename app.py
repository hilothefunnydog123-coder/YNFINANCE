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
# This remains hidden but lets Google index your "YN Finance" name.
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

# API Setup
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"]) if "GROQ_API_KEY" in st.secrets else None
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    vision_model = genai.GenerativeModel('gemini-2.0-flash')

# --- 3. DATA ENGINE (S&P 500) ---
@st.cache_data(ttl=3600)
def get_sp500_scanner():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    # Request with headers to avoid HTTP Error
    response = requests.get(url, headers=headers)
    tickers = pd.read_html(response.text)[0]['Symbol'].str.replace('.', '-').tolist()
    
    # Download first 50 for the scanner view
    data = yf.download(tickers[:50], period="3mo", group_by='ticker', progress=False)
    
    scan_results = []
    for t in tickers[:50]:
        try:
            df = data[t]
            cp = df['Close'].iloc[-1]
            pc = df['Close'].iloc[-2]
            pct = ((cp - pc) / pc) * 100
            
            # Buy/Sell Logic (EMA 9/21 Cross)
            e9 = ta.ema(df['Close'], length=9).iloc[-1]
            e21 = ta.ema(df['Close'], length=21).iloc[-1]
            
            if e9 > e21 * 1.02: sig = "STRONG BUY"
            elif e9 > e21: sig = "BUY"
            elif e9 < e21 * 0.98: sig = "STRONG SELL"
            elif e9 < e21: sig = "SELL"
            else: sig = "NEUTRAL"
            
            scan_results.append({"Ticker": t, "Price": round(cp, 2), "Change %": round(pct, 2), "Signal": sig})
        except: continue
    return pd.DataFrame(scan_results)

def signal_style(s):
    bg = '#00C805' if 'BUY' in s else '#FF3B30' if 'SELL' in s else '#8E8E93'
    return f'background-color: {bg}; color: white; font-weight: bold; border-radius: 5px;'

# --- 4. THE APP UI ---
st.title("🌱 YNFINANCE")
st.markdown("### Elite AI Market Scanner & Vision Analysis")

tab1, tab2, tab3 = st.tabs(["📊 Market Pulse", "🤖 AI Advisor", "📸 Vision Scan"])

# TAB 1: THE SCANNER
with tab1:
    st.subheader("S&P 500 Intelligence Feed")
    with st.spinner("Scanning top 500 stocks..."):
        pulse = get_sp500_scanner()
        st.dataframe(
            pulse.style.applymap(signal_style, subset=['Signal'])
            .background_gradient(subset=['Change %'], cmap='RdYlGn'),
            use_container_width=True, height=600, hide_index=True
        )

# TAB 2: THE CHATBOT
with tab2:
    st.subheader("AI Trading Advisor")
    tk = st.text_input("Analyze Symbol:", value="TSLA").upper()
    if st.button("Generate Strategy"):
        d = yf.download(tk, period="1mo")
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Analyze {tk} with this data and provide a trade plan: {d.tail(10).to_string()}"}]
        )
        st.write(response.choices[0].message.content)

# TAB 3: THE SCREENSHOT SCANNER
with tab3:
    st.subheader("Vision Chart Analysis")
    up = st.file_uploader("Drop Chart Image Here", type=['png', 'jpg', 'jpeg'])
    if up:
        img = Image.open(up)
        st.image(img, use_container_width=True)
        if st.button("Run AI Vision Scan"):
            res = vision_model.generate_content(["Break down this chart. Find support/resistance and trend.", img])
            st.success(res.text)
