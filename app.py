import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq
import requests
import base64
from PIL import Image
import io
from datetime import datetime

# --- 1. SETUP ---
st.set_page_config(page_title="YNFINANCE Master", layout="wide", page_icon="🌱")

# Connect to Groq
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Missing GROQ_API_KEY in Secrets!")

# --- 2. DATA ENGINE ---
@st.cache_data(ttl=900)
def get_market_data():
    with st.status("📥 Syncing Market Data... (15-30s)", expanded=False) as status:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers)
        table = pd.read_html(resp.text)
        tickers = table[0]['Symbol'].str.replace('.', '-').tolist()
        
        # Batch download for speed
        data = yf.download(tickers, period="2d", interval="1d", group_by='ticker', progress=False)
        
        results = []
        for t in tickers:
            try:
                ticker_df = data[t]
                current = ticker_df['Close'].iloc[-1]
                prev = ticker_df['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                results.append({
                    "Ticker": t,
                    "Price": round(current, 2),
                    "Change %": round(change, 2),
                    "Action": "🟢 BUY" if change > 2 else "🟡 HOLD" if change > -1 else "🔴 SELL"
                })
            except: continue
        status.update(label="✅ Market Data Live!", state="complete")
    return pd.DataFrame(results).sort_values(by="Change %", ascending=False)

# --- 3. UI LAYOUT ---
st.title("🌱 YNFINANCE")
st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')} EST")

# Pull Data
market_df = get_market_data()

# Create Tabs for a clean look
tab1, tab2, tab3 = st.tabs(["📊 Market Pulse", "🧠 AI Advisor", "📸 Chart Vision"])

with tab1:
    st.subheader("Live Market Scanner")
    search = st.text_input("🔍 Search ticker (e.g., NVDA, AAPL):").upper()
    
    if search:
        display_df = market_df[market_df['Ticker'] == search]
    else:
        display_df = market_df
    
    # Styled Table with automatic green/red coloring
    st.dataframe(
        display_df.style.background_gradient(subset=["Change %"], cmap="RdYlGn"),
        use_container_width=True,
        height=500,
        hide_index=True
    )

with tab2:
    st.subheader("Hedge Fund AI Analyst")
    user_query = st.text_area("Ask the AI about your strategy or specific stocks:")
    if st.button("Get AI Advice"):
        with st.spinner("Analyzing market sentiment..."):
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"You are a Senior Stock Analyst. Advise on: {user_query}"}]
            )
            st.info(completion.choices[0].message.content)

with tab3:
    st.subheader("AI Chart Analysis")
    img_file = st.file_uploader("Upload a chart screenshot", type=['png', 'jpg', 'jpeg'])
    
    if img_file:
        # Resize image for Groq (4MB limit fix)
        image = Image.open(img_file)
        if image.mode in ("RGBA", "P"): image = image.convert("RGB")
        image.thumbnail((1200, 1200))
        
        st.image(image, width=500)
        
        # Prepare for AI
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        base64_img = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        if st.button("Analyze Patterns"):
            with st.spinner("Llama 3 Vision is scanning candles..."):
                vision_resp = client.chat.completions.create(
                    model="llama-3.2-11b-vision-instruct",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this stock chart. Give a Buy/Sell signal and target prices."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                        ]
                    }]
                )
                st.success(vision_resp.choices[0].message.content)

st.divider()
st.caption("YNFINANCE | Built for the future of trading.")

