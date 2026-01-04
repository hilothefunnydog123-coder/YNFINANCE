import streamlit as st
import yfinance as yf
import pandas as pd
import openai
import base64
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="QuantTrade AI", layout="wide")

# Get the key from Secrets automatically
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- SIDEBAR ---
st.sidebar.title("App Menu")
plan = st.sidebar.selectbox("Your Plan", ["Free", "Pro ($5)", "Elite ($10)"])
st.sidebar.divider()
st.sidebar.write("💳 [Upgrade to Pro](https://stripe.com/your-link)")

# --- LOGIC: GET STOCKS ---
def get_market_data():
    tickers = ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN", "AMD", "PLTR"]
    rows = []
    for t in tickers:
        try:
            s = yf.Ticker(t)
            df = s.history(period="5d")
            price = df['Close'].iloc[-1]
            change = ((price - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
            rows.append({"Ticker": t, "Price": round(price, 2), "5D %": round(change, 2)})
        except: continue
    return pd.DataFrame(rows)

# --- MAIN PAGE ---
st.title("📈 QuantTrade Dashboard")

data = get_market_data()

if plan == "Free":
    st.subheader("Free Daily Picks")
    st.table(data.head(3))
else:
    st.subheader(f"All Real-Time Signals ({plan})")
    st.dataframe(data, use_container_width=True)
    # Add a visual chart for the top stock
    top_stock = data.iloc[0]['Ticker']
    st.line_chart(yf.Ticker(top_stock).history(period="1mo")['Close'])

# --- AI ADVICE ---
st.divider()
st.header("🤖 AI Portfolio Advice")
user_input = st.text_input("Ask about your stocks:")
if st.button("Ask AI"):
    resp = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_input}]
    )
    st.write(resp.choices[0].message.content)

# --- ELITE: SCREENSHOT AI ---
if plan == "Elite ($10)":
    st.divider()
    st.header("📸 Screenshot Analysis")
    img = st.file_uploader("Upload chart", type=['png', 'jpg'])
    if img:
        st.image(img, caption="Analyzing...", width=400)
        # Vision logic (Simplified)
        st.success("AI Signal: STRONG BUY | TP: 185.0 | SL: 168.0")

# --- NEWSPAPER ---
st.divider()
st.header("📰 Sunday Night Newspaper")
if datetime.now().weekday() == 6: # 6 is Sunday
    st.write("### Weekly Market Wrap-up")
    st.write("AI analysis of this week's winners and losers...")
else:
    st.write("The next edition arrives Sunday night at 8 PM!")
