import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import requests

# --- 1. THE "CRAWLER-FIX" INJECTION ---
# This script forces your tags into the actual <head> of the website
components.html(
    f"""
    <script>
        // FUNCTION TO INJECT TAGS INTO THE TOP-LEVEL HEAD
        function injectAdSense() {{
            var head = parent.document.getElementsByTagName('head')[0];

            // A. The Meta Tag Google asked for
            var metaAccount = document.createElement('meta');
            metaAccount.name = "google-adsense-account";
            metaAccount.content = "ca-pub-7892378866702980";
            head.appendChild(metaAccount);

            // B. The AdSense Snippet (The "Engine")
            var adScript = document.createElement('script');
            adScript.async = true;
            adScript.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7892378866702980";
            adScript.crossOrigin = "anonymous";
            head.appendChild(adScript);

            // C. Google Search Console Verification
            var metaVerify = document.createElement('meta');
            metaVerify.name = "google-site-verification";
            metaVerify.content = "HTd_e07Z3vt7rxoCVHyfti8A1mm9sWs_eRSETKtN-BY";
            head.appendChild(metaVerify);
        }}
        
        // Execute the injection
        injectAdSense();
    </script>
    """,
    height=0,
)

# --- 2. LAYOUT & UI ---
st.set_page_config(page_title="YNFINANCE | AI Terminal", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #050505; color: #E0E0E0; }
    h1 { color: #00D4FF !important; text-shadow: 0px 0px 10px #00D4FF; font-family: monospace; }
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA SCANNER ---
@st.cache_data(ttl=3600)
def get_sp500_data():
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        tickers = pd.read_html(response.text)[0]['Symbol'].str.replace('.', '-').tolist()
        
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
    
    # Manual Ad Container
    components.html('<div style="text-align:center; color:#444; border:1px dashed #333; padding:10px;">ADVERTISING SLOT</div>', height=90)
    
    df = get_sp500_data()
    if not df.empty:
        st.dataframe(df, use_container_width=True, height=600)
    else:
        st.error("Connection Interrupted. Retrying...")

elif page == "ABOUT":
    st.title("About YNFINANCE")
    st.write("YNFINANCE is a high-speed AI scanner for global market movers.")

elif page == "PRIVACY":
    st.title("Privacy Policy")
    st.write("We use Google AdSense and third-party cookies for ad delivery.")

elif page == "CONTACT":
    st.title("Contact Us")
    st.write("Inquiries: support@ynfinance.org")

st.sidebar.markdown("---")
st.sidebar.caption("YNFINANCE // 2026")
