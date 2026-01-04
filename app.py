import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq
import requests
import base64
from datetime import datetime

# --- 1. SETUP & BRANDING ---
st.set_page_config(page_title="YNFINANCE Pro", layout="wide", page_icon="🌱")

# Connect to Groq (Ensure GROQ_API_KEY is in your Streamlit Secrets)
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Please add your GROQ_API_KEY to Streamlit Secrets!")

# --- 2. DATA ENGINE (The "Every Stock" Scanner) ---
@st.cache_data(ttl=900)
def get_market_master():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers)
        tickers = pd.read_html(resp.text)[0]['Symbol'].str.replace('.', '-').tolist()
        
        # Batch download for speed and safety
        data = yf.download(tickers, period="2d", interval="1d", group_by='ticker', progress=False)
        
        results = []
        for t in tickers:
            try:
                current = data[t]['Close'].iloc[-1]
                prev = data[t]['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                results.append({
                    "Ticker": t,
                    "Price": round(current, 2),
                    "Change %": round(change, 2),
                    "Signal": "🟢 Strong Buy" if change > 2.5 else "🟡 Hold" if change > -1 else "🔴 Sell"
                })
            except: continue
        return pd.DataFrame(results).sort_values(by="Change %", ascending=False)
    except Exception as e:
        st.error(f"Data Sync Error: {e}")
        return pd.DataFrame()

# --- 3. HEADER & HERO SECTION ---
st.title("🌱 YNFINANCE")
st.markdown("*Professional Intelligence for the Modern Trader.*")

# --- 4. THE INTERACTIVE TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Market Scanner", "🧠 AI Advisor", "📸 Chart Vision"])

with tab1:
    st.subheader("Live Market Signals")
    with st.expander("🔍 Search & Filter"):
        search = st.text_input("Find a specific ticker:").upper()
        
    data_df = get_market_master()
    
    if search:
        display_df = data_df[data_df['Ticker'] == search]
    else:
        display_df = data_df

    # Styled Table
    st.dataframe(
        display_df.style.background_gradient(subset=["Change %"], cmap="RdYlGn"),
        use_container_width=True,
        height=500
    )

with tab2:
    st.subheader("AI Financial Intelligence")
    query = st.text_area("What's on your mind? (e.g., 'Analyze NVDA vs AMD for the next 6 months')")
    if st.button("Consult AI", key="ai_button"):
        with st.spinner("Processing market sentiment..."):
            chat = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"You are a Senior Hedge Fund Analyst. Answer: {query}"}]
            )
            st.info(chat.choices[0].message.content)

with tab3:
    st.subheader("Technical Vision Analysis")
    st.write("Upload any trading chart and let the AI find patterns.")
    img_file = st.file_uploader("Upload Image (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
    
    if img_file:
        st.image(img_file, width=600)
        if st.button("Run Vision Analysis"):
            base64_img = base64.b64encode(img_file.getvalue()).decode('utf-8')
            with st.spinner("Reading candles..."):
                vision_resp = client.chat.completions.create(
                    model="llama-3.2-11b-vision-preview",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this chart. Identify the trend, key support/resistance, and give a clear Buy/Sell signal."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                        ]
                    }]
                )
                st.success(vision_resp.choices[0].message.content)

# --- 5. FOOTER ---
st.divider()
if datetime.now().weekday() == 6:
    st.markdown("📰 **Sunday Edition:** The Weekly Gazette is now live in the Scanner tab!")
else:
    st.caption("YNFINANCE Global Markets Data | Updates every 15 minutes")
