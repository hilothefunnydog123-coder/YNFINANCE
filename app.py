import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import requests

# --- 1. MONETAG VERIFICATION HOISTING ---
# Replace 'YOUR_CODE_HERE' with the content string from Monetag
components.html(
    f"""
    <script>
        var meta = document.createElement('meta');
        meta.name = "monetag";
        meta.content = "YOUR_CODE_HERE"; 
        parent.document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
    """, height=0,
)

# --- 2. THE ADS ENGINE (NATIVE BANNER) ---
# Once verified, paste your "Native Banner" tag here
def show_ad():
    ad_tag = """
    <script>(function(s,u,z,p){s.src=u,s.setAttribute('data-zone',z),p.appendChild(s);})(document.createElement('script'),'https://itubego.com/tag.min.js',YOUR_ZONE_ID,document.body||document.documentElement)</script>
    """
    components.html(ad_tag, height=100)

# --- 3. UI & STOCK LOGIC ---
st.set_page_config(page_title="YNFINANCE", layout="wide")
st.title("⚡ YNFINANCE TERMINAL")

show_ad() # Ad shows at the top

@st.cache_data(ttl=600)
def get_data():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    tickers = pd.read_html(res.text)[0]['Symbol'].str.replace('.', '-').tolist()
    data = yf.download(tickers, period="1d", progress=False)
    # Simplified for speed
    return pd.DataFrame({"Ticker": tickers[:10], "Price": [0]*10})

st.dataframe(get_data(), use_container_width=True)
