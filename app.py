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

# --- 2. DARK MODE UI STYLING (CSS) ---
st.set_page_config(page_title="YNFINANCE | AI Terminal", page_icon="🌱", layout="wide")

st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: #161B22;
        padding: 10px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        color: #8B949E;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #58A6FF !important;
        border-bottom-color: #58A6FF !important;
    }
    /* Metric / Card Styling */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #58A6FF;
    }
    /* Global Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #238636;
        color: white;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #2ea043;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_name=True)

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
            cp = df['Close'].iloc[-1]
            pc = df['Close'].iloc[-2]
            pct = ((cp - pc) / pc) * 100
            
            if pct > 2.5: sig = "🟢 STRONG BUY"
            elif pct > 0.5: sig = "📈 BUY"
            elif pct < -2.5: sig = "🔴 STRONG SELL"
            elif pct < -0.5: sig = "📉 SELL"
            else: sig = "⚪ NEUTRAL"
            
            ranked_list.append({"Ticker": t, "Price": f"${cp:,.2f}", "Change %": round(pct, 2), "Signal": sig})
        except: continue
    return pd.DataFrame(ranked_list).sort_values(by="Change %", ascending=False)

def signal_style(s):
    if 'BUY' in s: bg = '#238636'; text = 'white'
    elif 'SELL' in s: bg = '#da3633'; text = 'white'
    else: bg = '#30363d'; text = '#8b949e'
    return f'background-color: {bg}; color: {text}; font-weight: bold; border-radius: 4px; padding: 5px;'

# --- 4. APP INTERFACE ---
st.title("🌱 YNFINANCE TERMINAL")
st.write("Professional-Grade AI Stock Intelligence")

tab1, tab2, tab3 = st.tabs(["⚡ Market Pulse", "🧠 AI Analyst", "👁️ Vision Scan"])

with tab1:
    st.subheader("S&P 500 Intelligence Ranking")
    with st.spinner("Crunching Market Data..."):
        df_ranked = get_full_sp500_ranked()
        st.dataframe(
            df_ranked.style.map(signal_style, subset=['Signal'])
            .background_gradient(subset=['Change %'], cmap='RdYlGn'),
            use_container_width=True, height=800, hide_index=True
        )

with tab2:
    st.subheader("AI Trade Strategist")
    col1, col2 = st.columns([1, 2])
    with col1:
        ticker_input = st.text_input("Enter Ticker:", value="NVDA").upper()
        analyze_btn = st.button("Generate Alpha Plan")
    with col2:
        if analyze_btn:
            hist = yf.download(ticker_input, period="1mo")
            chat = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"Analyze {ticker_input}: {hist.tail(10).to_string()}"}]
            )
            st.markdown(f"### Trade Setup for {ticker_input}")
            st.info(chat.choices[0].message.content)

with tab3:
    st.subheader("Vision Chart Intelligence")
    st.write("Upload a chart screenshot for pattern recognition.")
    uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True, caption="Chart for Vision Analysis")
        if st.button("Run Vision Scan"):
            with st.spinner("AI analyzing patterns..."):
                res = vision_model.generate_content(["Provide a professional technical analysis for this chart image.", img])
                st.success(res.text)

st.markdown("---")
st.caption("YNFINANCE | Data provided by Yahoo Finance | AI Intelligence by Groq & Gemini")
