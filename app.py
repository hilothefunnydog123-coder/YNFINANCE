import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import requests

# --- 1. ADSENSE & SEARCH CONSOLE INJECTION ---
# This "tricks" Streamlit into putting your ID in the <head>
components.html(
    f"""
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-0000000000000000" crossorigin="anonymous"></script>
    <script>
        var meta = document.createElement('meta');
        meta.name = "google-site-verification";
        meta.content = "HTd_e07Z3vt7rxoCVHyfti8A1mm9sWs_eRSETKtN-BY";
        parent.document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
    """, height=0,
)

# --- 2. UI STYLING ---
st.set_page_config(page_title="YNFINANCE | AI Terminal", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #050505; color: #E0E0E0; }
    h1 { color: #00D4FF !important; text-shadow: 0px 0px 15px #00D4FF; font-family: monospace; }
    .stDataFrame { border: 1px solid #30363D; border-radius: 10px; }
    footer { visibility: hidden; }
    .nav-link { color: #00D4FF; text-decoration: none; margin-right: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=3600)
def get_sp500_scanner():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    tickers = pd.read_html(response.text)[0]['Symbol'].str.replace('.', '-').tolist()
    
    # Batch download to save speed
    data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
    
    scan_results = []
    for t in tickers:
        try:
            df = data[t]
            if df.empty: continue
            cp, pc = df['Close'].iloc[-1], df['Close'].iloc[-2]
            pct = ((cp - pc) / pc) * 100
            
            sig = "⚡ STRONG BUY" if pct > 2.0 else "📈 BUY" if pct > 0.3 else "💀 SELL" if pct < -0.3 else "🌑 NEUTRAL"
            scan_results.append({"Ticker": t, "Price": round(cp, 2), "Change %": round(pct, 2), "Signal": sig})
        except: continue
    return pd.DataFrame(scan_results).sort_values(by="Change %", ascending=False)

# --- 4. NAVIGATION / ROUTING ---
# We use a sidebar to simulate real website pages
page = st.sidebar.radio("NAVIGATION", ["TERMINAL", "ABOUT", "PRIVACY", "CONTACT"])

if page == "TERMINAL":
    st.title("⚡ YNFINANCE CYBER TERMINAL")
    
    # MANUAL AD SLOT 1
    components.html('<div style="color: #444; text-align:center; border: 1px dashed #444; padding: 10px;">AD SLOT: TOP BANNER</div>', height=90)
    
    st.markdown("### 🔥 Real-Time S&P 500 Signals")
    df = get_sp500_scanner()
    
    # Styling the Signal column
    def color_signal(val):
        color = '#00FF88' if 'BUY' in val else '#FF0055' if 'SELL' in val else '#888'
        return f'color: {color}; font-weight: bold'

    st.dataframe(df.style.map(color_signal, subset=['Signal']), use_container_width=True, height=600)

    # MANUAL AD SLOT 2
    components.html('<div style="color: #444; text-align:center; border: 1px dashed #444; padding: 10px;">AD SLOT: BOTTOM FEED</div>', height=250)

elif page == "ABOUT":
    st.title("About YNFINANCE")
    st.write("YNFINANCE is an AI-powered financial terminal providing instant market analysis.")

elif page == "PRIVACY":
    st.title("Privacy Policy")
    st.write("We use Google AdSense and cookies to personalize your experience. Your data is never sold.")

elif page == "CONTACT":
    st.title("Contact Us")
    st.write("Reach us at: support@ynfinance.org")

# --- 5. FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("YNFINANCE // GLOBAL DATA // 2026")
