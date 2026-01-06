import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import google.generativeai as genai
from groq import Groq
from PIL import Image
import requests

# --- 1. GOOGLE SEARCH CONSOLE TAG ---
components.html(
    f"""<script>
        var meta = document.createElement('meta');
        meta.name = "google-site-verification";
        meta.content = "HTd_e07Z3vt7rxoCVHyfti8A1mm9sWs_eRSETKtN-BY";
        parent.document.getElementsByTagName('head')[0].appendChild(meta);
    </script>""", height=0,
)

# --- 2. HIGH-CONTRAST NEON UI STYLING ---
st.set_page_config(page_title="YNFINANCE | AI Terminal", page_icon="🌱", layout="wide")

st.markdown("""
    <style>
    /* Force top header and background to be Dark */
    header[data-testid="stHeader"] {
        background: rgba(0,0,0,0);
    }
    .stApp {
        background: linear-gradient(180deg, #050505 0%, #101216 100%);
        color: #E0E0E0;
    }
    /* Bright Neon Title */
    h1 {
        color: #00D4FF !important;
        text-shadow: 0px 0px 15px #00D4FF;
        font-family: 'Courier New', monospace;
        letter-spacing: 2px;
    }
    /* Better Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #1A1C23;
        padding: 8px;
        border-radius: 12px;
        border: 1px solid #30363D;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        color: #ffffff;
        border-radius: 8px;
        margin: 0 5px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00D4FF22 !important;
        border: 1px solid #00D4FF !important;
        color: #00D4FF !important;
    }
    /* Buttons that Glow */
    .stButton>button {
        background: linear-gradient(90deg, #00D4FF 0%, #0055FF 100%);
        color: white;
        border: none;
        font-weight: bold;
        box-shadow: 0px 4px 15px rgba(0, 212, 255, 0.3);
    }
    .stButton>button:hover {
        box-shadow: 0px 0px 25px rgba(0, 212, 255, 0.6);
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

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
    response = requests.get(url, headers=headers)
    tickers = pd.read_html(response.text)[0]['Symbol'].str.replace('.', '-').tolist()
    data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
    
    ranked_list = []
    for t in tickers:
        try:
            df = data[t]
            if df.empty: continue
            cp, pc = df['Close'].iloc[-1], df['Close'].iloc[-2]
            pct = ((cp - pc) / pc) * 100
            
            if pct > 2.0: sig = "⚡ STRONG BUY"
            elif pct > 0.3: sig = "📈 BUY"
            elif pct < -2.0: sig = "💀 STRONG SELL"
            elif pct < -0.3: sig = "📉 SELL"
            else: sig = "🌑 NEUTRAL"
            
            ranked_list.append({"Ticker": t, "Price": f"${cp:,.2f}", "Change %": round(pct, 2), "Signal": sig})
        except: continue
            
    return pd.DataFrame(ranked_list).sort_values(by="Change %", ascending=False)

def signal_style(s):
    if 'BUY' in s: bg = '#00FF88'; color = '#000000'
    elif 'SELL' in s: bg = '#FF0055'; color = '#ffffff'
    else: bg = '#30363d'; color = '#ffffff'
    return f'background-color: {bg}; color: {color}; font-weight: 900; border-radius: 6px;'

# --- 4. INTERFACE ---
st.title("⚡ YNFINANCE | CYBER TERMINAL")

tab1, tab2, tab3 = st.tabs(["🔥 HOT SIGNALS", "🧠 AI STRATEGIST", "👁️ VISION ANALYZER"])

with tab1:
    st.markdown("### Top Ranked Market Movers")
    df_ranked = get_full_sp500_ranked()
    st.dataframe(
        df_ranked.style.map(signal_style, subset=['Signal'])
        .background_gradient(subset=['Change %'], cmap='RdYlGn'),
        use_container_width=True, height=750, hide_index=True
    )

with tab2:
    st.subheader("Deep Learning Trade Advisor")
    ticker_box = st.text_input("SYMBOL:", value="TSLA").upper()
    if st.button("RUN AI DIAGNOSTICS"):
        h = yf.download(ticker_box, period="1mo")
        c = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Brief trade plan for {ticker_box}: {h.tail(10).to_string()}"}]
        )
        st.info(c.choices[0].message.content)

with tab3:
    st.subheader("Neural Pattern Scan")
    file = st.file_uploader("Upload Snapshot", type=['png', 'jpg', 'jpeg'])
    if file:
        img = Image.open(file)
        st.image(img, use_container_width=True)
        if st.button("EXECUTE VISION SCAN"):
            res = vision_model.generate_content(["Expert chart analysis for this image.", img])
            st.success(res.text)

st.markdown("---")
st.caption("YNFINANCE // GLOBAL DATA // AI OVERRIDE ACTIVE")
