import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import requests

# --- 1. THE "CRAWLER FIX" INJECTION ---
# This script forces the Meta Tag into the very top level of the website
components.html(
    f"""
    <script>
        // 1. Meta tag for AdSense account verification
        var adsenseMeta = document.createElement('meta');
        adsenseMeta.name = "google-adsense-account";
        adsenseMeta.content = "ca-pub-7892378866702980";
        parent.document.getElementsByTagName('head')[0].appendChild(adsenseMeta);

        // 2. Meta tag for Search Console ownership
        var searchMeta = document.createElement('meta');
        searchMeta.name = "google-site-verification";
        searchMeta.content = "HTd_e07Z3vt7rxoCVHyfti8A1mm9sWs_eRSETKtN-BY";
        parent.document.getElementsByTagName('head')[0].appendChild(searchMeta);
    </script>
    """, height=0,
)

# --- 2. LAYOUT & STYLE ---
st.set_page_config(page_title="YNFINANCE | Terminal", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #050505; color: #E0E0E0; }
    h1 { color: #00D4FF !important; text-shadow: 0px 0px 10px #00D4FF; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE LOGIC ---
@st.cache_data(ttl=3600)
def get_data():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    tickers = pd.read_html(res.text)[0]['Symbol'].str.replace('.', '-').tolist()
    data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
    
    results = []
    for t in tickers:
        try:
            df = data[t]
            cp, pc = df['Close'].iloc[-1], df['Close'].iloc[-2]
            pct = ((cp - pc) / pc) * 100
            results.append({"Ticker": t, "Price": round(cp, 2), "Change %": round(pct, 2)})
        except: continue
    return pd.DataFrame(results).sort_values(by="Change %", ascending=False)

# --- 4. NAVIGATION PAGES (Required for Approval) ---
page = st.sidebar.radio("NAVIGATION", ["TERMINAL", "PRIVACY", "ABOUT"])

if page == "TERMINAL":
    st.title("⚡ YNFINANCE CYBER TERMINAL")
    df = get_data()
    st.dataframe(df, use_container_width=True, height=600)
    
    # Ad slot for manual placement
    components.html('<div style="text-align:center; color:#444; border:1px dashed #333; padding:10px;">ADVERTISING SPACE</div>', height=90)

elif page == "PRIVACY":
    st.title("Privacy Policy")
    st.write("YNFINANCE uses Google AdSense cookies for ad personalization.")

elif page == "ABOUT":
    st.title("About Us")
    st.write("YNFINANCE is an automated market scanner for S&P 500 movers.")
