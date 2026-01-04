import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq
from datetime import datetime
import requests

# --- 1. CONFIG & API SETUP ---
st.set_page_config(page_title="QuantTrade Pro", layout="wide", page_icon="📈")

# Groq Setup
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Missing GROQ_API_KEY in Streamlit Secrets!")

# --- 2. SIDEBAR MEMBERSHIP ---
st.sidebar.title("💳 Your Account")
plan = st.sidebar.radio("Active Plan:", ["Free", "Pro ($5)", "Elite ($10)"])
st.sidebar.divider()
st.sidebar.info("""
**Free:** Top 3 Stocks
**Pro:** Top 100 + AI Summary
**Elite:** Full Market + Chart Analysis
""")

# --- 3. THE DATA ENGINE (Batch & Cache) ---
@st.cache_data(ttl=900) # Only runs once every 15 minutes
def get_sp500_data():
    with st.status("📥 Syncing Market Data... (May take 15-30 seconds)", expanded=True) as status:
        # Step A: Spoof browser to get Wikipedia list
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        table = pd.read_html(response.text)
        tickers = table[0]['Symbol'].str.replace('.', '-').tolist()
        
        # Step B: Batch download to prevent getting banned
        st.write("📊 Downloading 500+ Stock Prices...")
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
                    "1D %": round(change, 2),
                    "Trend": "🔥" if change > 3 else "🚀" if change > 0 else "📉"
                })
            except: continue
        
        status.update(label="✅ Market Data Live!", state="complete", expanded=False)
    return pd.DataFrame(results)

# Load the data
all_data = get_sp500_data()

# --- 4. SEARCH BAR ---
st.header("🔍 Stock Lookup")
search_query = st.text_input("Find a stock (e.g. NVDA, TSLA):").upper()

if search_query:
    search_res = all_data[all_data['Ticker'] == search_query]
    if not search_res.empty:
        st.success(f"Result for {search_query}")
        st.table(search_res)
    else:
        st.error("Ticker not found in S&P 500.")

st.divider()

# --- 5. TIERED LISTS ---
st.header("🎯 Market Signals")

# Logic for displaying based on plan
if plan == "Free":
    st.subheader("Free Daily Top 3 Picks")
    st.table(all_data.head(3))
    st.warning("Upgrade to Pro to unlock the full list!")

elif plan == "Pro ($5)":
    st.subheader("💎 Pro Plan: Top 100 Stocks")
    st.dataframe(all_data.head(100), use_container_width=True)

elif plan == "Elite ($10)":
    st.subheader("🔥 Elite Plan: Full S&P 500 Live List")
    # Sort by top gainers for Elite members
    elite_view = all_data.sort_values(by="1D %", ascending=False)
    st.dataframe(elite_view, use_container_width=True)

# --- 6. SUNDAY NEWSPAPER & AI ---
st.divider()
st.header("📰 Sunday Night Gazette")

if plan in ["Pro ($5)", "Elite ($10)"]:
    # Check if today is Sunday (day 6)
    if datetime.now().weekday() == 6:
        if st.button("Generate Today's Market Wrap-Up"):
            with st.spinner("Llama 3 is writing the news..."):
                top_context = all_data.head(10).to_string()
                news = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Write a professional Sunday financial newspaper section based on these stocks: {top_context}"}]
                )
                st.markdown(news.choices[0].message.content)
    else:
        st.write("The Gazette publishes every Sunday at 8:00 PM EST. Check back then!")
else:
    st.info("🔒 The AI Newspaper is only available for Pro and Elite members.")

# --- 7. ELITE SCREENSHOT AI ---
if plan == "Elite ($10)":
    st.divider()
    st.header("📸 Screenshot Analysis")
    st.write("Upload a chart screenshot to get AI entry/exit signals.")
    st.file_uploader("Upload Image", type=['png', 'jpg'])
