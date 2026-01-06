import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import requests

# --- 1. THE "META TAG" INJECTION ---
# This fixes the "Couldn't verify your site" error on Streamlit
components.html(
    f"""
    <script>
        // Inject the Google AdSense account tag into the parent head
        var adsenseMeta = document.createElement('meta');
        adsenseMeta.name = "google-adsense-account";
        adsenseMeta.content = "ca-pub-7892378866702980";
        parent.document.getElementsByTagName('head')[0].appendChild(adsenseMeta);

        // Inject the Search Console verification tag
        var searchMeta = document.createElement('meta');
        searchMeta.name = "google-site-verification";
        searchMeta.content = "HTd_e07Z3vt7rxoCVHyfti8A1mm9sWs_eRSETKtN-BY";
        parent.document.getElementsByTagName('head')[0].appendChild(searchMeta);
    </script>
    """, height=0,
)

# --- 2. CONFIG & STYLE ---
st.set_page_config(page_title="YNFINANCE | AI Terminal", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #050505; color: #E0E0E0; }
    h1 { color: #00D4FF !important; text-shadow: 0px 0px 10px #00D4FF; }
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=3600)
def get_sp500_data():
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        tickers = pd.read_html(response.text)[0]['Symbol'].str.replace('.', '-').tolist()
        
        # Pull 2 days of data for percent change calculation
        data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
        
        results = []
        for t in tickers:
            try:
                df = data[t]
                if df.empty: continue
                cp, pc = df['Close'].iloc[-1], df['Close'].iloc[-2]
                pct = ((cp - pc) / pc) * 100
                sig = "⚡ BUY" if pct > 0.5 else "💀 SELL" if pct < -0.5 else "🌑 NEUTRAL"
                results.append({"Ticker": t, "Price": round(cp, 2), "Change %": round(pct, 2), "Signal": sig})
            except: continue
        return pd.DataFrame(results).sort_values(by="Change %", ascending=False)
    except: return pd.DataFrame()

# --- 4. NAVIGATION ---
page = st.sidebar.radio("MENU", ["TERMINAL", "ABOUT", "PRIVACY", "CONTACT"])

if page == "TERMINAL":
    st.title("⚡ YNFINANCE CYBER TERMINAL")
    
    # Placeholder for Manual Ads
    st.caption("ADVERTISEMENT")
    components.html('<div style="background:#111; color:#444; text-align:center; padding:10px; border:1px dashed #333;">AD BANNER SLOT</div>', height=90)
    
    df = get_sp500_data()
    if not df.empty:
        st.dataframe(df, use_container_width=True, height=600)
    else:
        st.error("Data Stream Offline. Reconnecting...")

elif page == "ABOUT":
    st.title("About YNFINANCE")
    st.write("YNFINANCE is a high-speed AI terminal for S&P 500 market data.")

elif page == "PRIVACY":
    st.title("Privacy Policy")
    st.write("We use Google AdSense cookies for ad personalization.")

elif page == "CONTACT":
    st.title("Contact Us")
    st.write("Inquiries: support@ynfinance.org")

st.sidebar.markdown("---")
st.sidebar.write("Logged in: Guest")
