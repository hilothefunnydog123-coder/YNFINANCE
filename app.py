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

# --- 1. GOOGLE SEARCH CONSOLE VERIFICATION INJECTION ---
# This injects the meta tag into the <head> so Google can verify your site.
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

# --- 2. SEO & PAGE CONFIGURATION ---
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

# --- 3. DATA ENGINES ---
@st.cache_data(ttl=900)
def get_market_pulse():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    tickers = pd.read_html(resp.text)[0]['Symbol'].str.replace('.', '-').tolist()
    # Scans top 50 to save speed for the free tier
    data = yf.download(tickers[:50], period="2d", group_by='ticker', progress=False)
    pulse = []
    for t in tickers[:50]:
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
    # Positional Signal Generation
    mask = (df['EMA9'] > df['EMA21']) & (df['EMA9'].shift(1) <= df['EMA21'].shift(1))
    df.loc[mask, 'Signal'] = 1
    return df

# --- 4. MAIN UI ---
st.title("🌱 YNFINANCE")
st.markdown("### Elite AI-Powered Market Intelligence & Trade Signals")

tab1, tab2, tab3 = st.tabs(["📊 Market Pulse", "📈 Interactive Chart", "📸 AI Vision"])

# TAB 1: MARKET SCANNER
with tab1:
    st.subheader("Daily Market Leaders (S&P 500)")
    pulse_df = get_market_pulse()
    st.dataframe(pulse_df.style.background_gradient(subset=["Change %"], cmap="RdYlGn"), 
                 use_container_width=True, height=450, hide_index=True)

# TAB 2: ELITE CHARTING & EMA CROSS SIGNALS
with tab2:
    col_input, col_info = st.columns([1, 2])
    with col_input:
        ticker = st.text_input("Symbol Lookup:", value="NVDA").upper()
    
    df = get_chart_data(ticker)
    
    if df is not None:
        # Format for TradingView-style Lightweight Chart
        candles = [{"time": str(d.date()), "open": float(r['Open']), "high": float(r['High']), 
                    "low": float(r['Low']), "close": float(r['Close'])} for d, r in df.iterrows()]
        
        markers = []
        for i in range(len(df)):
            if df['Signal'].iloc[i] == 1:
                markers.append({"time": str(df.index[i].date()), "position": "belowBar", 
                                "color": "#2196F3", "shape": "arrowUp", "text": "BUY"})

        lightweight_charts_v5_component(
            charts=[{
                "chart": {"layout": {"background": {"color": "#FFFFFF"}}, "grid": {"vertLines": {"visible": False}}},
                "series": [
                    {"type": "Candlestick", "data": candles, "markers": markers},
                    {"type": "Line", "data": [{"time": str(d.date()), "value": float(v)} for d, v in df['EMA9'].dropna().items()], "options": {"color": "#2196F3", "lineWidth": 1}},
                    {"type": "Line", "data": [{"time": str(d.date()), "value": float(v)} for d, v in df['EMA21'].dropna().items()], "options": {"color": "#FF9800", "lineWidth": 1}}
                ],
            }], height=500
        )
        
        if st.button("Generate AI Alpha Report"):
            context = df.tail(15).to_string()
            chat = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"Analyze these metrics for {ticker} and provide an Elite trade plan with stop loss: {context}"}]
            )
            st.info(chat.choices[0].message.content)

# TAB 3: AI VISION ANALYZER (GEMINI 2.0)
with tab3:
    st.subheader("Chart Vision Pattern Analysis")
    st.write("Upload any screenshot of a chart to identify support/resistance levels.")
    img_file = st.file_uploader("Upload PNG/JPG", type=['png', 'jpg', 'jpeg'])
    
    if img_file:
        img = Image.open(img_file)
        st.image(img, width=700, caption="Chart for Analysis")
        if st.button("Run Vision Scan"):
            with st.spinner("AI is reading market patterns..."):
                prompt = "Act as a professional technical analyst. Identify the trend, key support/resistance levels, and suggest a trade entry if applicable."
                response = vision_model.generate_content([prompt, img])
                st.success(response.text)

st.divider()
st.caption("YNFINANCE Global Markets Data | Professional AI Intelligence")
