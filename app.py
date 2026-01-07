import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import requests

# --- 1. MONETAG VERIFICATION (BETWEEN HEAD/HEAD WORKAROUND) ---
components.html(
    """
    <script>
        // This script 'hoists' the tag into the main page head for verification
        var meta = document.createElement('meta');
        meta.name = "monetag";
        meta.content = "df49902eaadca0329ff1a8bf57159c0a"; 
        parent.document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
    """, height=0,
)

# --- 2. ADS ENGINE ---
def show_ad():
    # Replace YOUR_ZONE_ID with the actual number from Monetag later
    ad_tag = """
    <script>(function(s,u,z,p){s.src=u,s.setAttribute('data-zone',z),p.appendChild(s);})(document.createElement('script'),'https://itubego.com/tag.min.js',YOUR_ZONE_ID,document.body||document.documentElement)</script>
    """
    components.html(ad_tag, height=100)

# --- 3. UI CONFIG & STYLING ---
st.set_page_config(page_title="YNFINANCE | Terminal", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #050505; color: #E0E0E0; }
    h1 { color: #00D4FF !important; text-shadow: 0px 0px 10px #00D4FF; font-family: monospace; }
    .stDataFrame { border: 1px solid #30363D; border-radius: 10px; }
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. FULL S&P 500 SCANNER LOGIC ---
@st.cache_data(ttl=3600)
def get_sp500_scanner():
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        tickers = pd.read_html(response.text)[0]['Symbol'].str.replace('.', '-').tolist()
        
        # Pull data for all tickers
        data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
        
        scan_results = []
        for t in tickers:
            try:
                df = data[t]
                if df.empty: continue
                cp, pc = df['Close'].iloc[-1], df['Close'].iloc[-2]
                pct = ((cp - pc) / pc) * 100
                
                # Assign Signal and Neon Colors
                if pct > 0.5: sig, color = "📈 BUY", "#00FF88"
                elif pct < -0.5: sig, color = "📉 SELL", "#FF0055"
                else: sig, color = "🌑 NEUTRAL", "#888888"
                
                scan_results.append({
                    "Ticker": t, 
                    "Price": f"${cp:,.2f}", 
                    "Change %": round(pct, 2), 
                    "Signal": sig,
                    "Color": color
                })
            except: continue
        return pd.DataFrame(scan_results).sort_values(by="Change %", ascending=False)
    except:
        return pd.DataFrame()

# --- 5. MAIN APP INTERFACE ---
st.title("⚡ YNFINANCE CYBER TERMINAL")

# Navigation for AdSense/Monetag approval requirements
menu = st.sidebar.radio("NAV", ["MARKET", "PRIVACY", "ABOUT"])

if menu == "MARKET":
    show_ad() # Ad placement
    
    with st.spinner("Scanning S&P 500 Neural Net..."):
        df = get_sp500_scanner()
        
    if not df.empty:
        # Apply the neon coloring to the Signal column
        def style_signal(row):
            return [f'color: {row["Color"]}; font-weight: bold' if name == 'Signal' else '' for name in row.index]
        
        st.dataframe(df.style.apply(style_signal, axis=1).hide(axis='columns', subset=['Color']), 
                     use_container_width=True, height=700)
    else:
        st.error("Terminal Offline. Check Connection.")

elif menu == "PRIVACY":
    st.header("Privacy Policy")
    st.write("We use Monetag cookies for advertisement delivery and analytics.")

elif menu == "ABOUT":
    st.header("About YNFINANCE")
    st.write("Real-time automated market sentiment and technical analysis terminal.")

st.sidebar.markdown("---")
st.sidebar.caption("YNFINANCE // GLOBAL DATA // 2026")
