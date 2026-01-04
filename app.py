import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq
from datetime import datetime
import time

# --- 1. INITIALIZE & THEME ---
st.set_page_config(page_title="QuantTrade S&P 500", layout="wide")

# Connect to Groq (Make sure your key is in Streamlit Secrets!)
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Missing GROQ_API_KEY in Secrets.")

# --- 2. SIDEBAR TIERS ---
st.sidebar.title("💳 Membership Tier")
plan = st.sidebar.radio("Select Plan:", ["Free", "Pro ($5)", "Elite ($10)"])
st.sidebar.divider()
st.sidebar.info("Pro: Unlocks 100 Stocks + News\n\nElite: Unlocks Full Market + Screenshot AI")

# --- 3. THE "UNLIMITED" ENGINE (Batch & Cache) ---
@st.cache_data(ttl=900) # Cache for 15 mins (900 seconds) to avoid rate limits
def get_market_data():
    # Progress warning for the user
    with st.status("📥 Fetching Full S&P 500 List... (May take 15-30 seconds)", expanded=True) as status:
        # Step A: Get all tickers from Wikipedia
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        table = pd.read_html(url)
        tickers = table[0]['Symbol'].str.replace('.', '-').tolist()
        
        # Step B: Batch download current data (Much safer than loops)
        st.write("📊 Downloading prices in batch mode...")
        data = yf.download(tickers, period="2d", interval="1d", group_by='ticker', progress=False)
        
        results = []
        for t in tickers:
            try:
                ticker_df = data[t]
                current_price = ticker_df['Close'].iloc[-1]
                prev_price = ticker_df['Close'].iloc[-2]
                change = ((current_price - prev_price) / prev_price) * 100
                results.append({
                    "Ticker": t,
                    "Price": round(current_price, 2),
                    "1D %": round(change, 2),
                    "Signal": "STRONG BUY" if change > 2 else "GOOD BUY" if change > 0 else "HOLD"
                })
            except: continue
        
        status.update(label="✅ Market Sync Complete!", state="complete", expanded=False)
    return pd.DataFrame(results)

# --- 4. DATA PROCESSING ---
all_stocks_df = get_market_data()

# --- 5. SEARCH BAR ---
st.header("🔍 Search Specific Stock")
search = st.text_input("Type ticker (e.g., NVDA, AAPL):").upper()
if search:
    found = all_stocks_df[all_stocks_df['Ticker'] == search]
    if not found.empty:
        st.table(found)
    else:
        st.error("Ticker not found in S&P 500.")

st.divider()

# --- 6. TIERED LIST DISPLAY ---
st.header("🎯 Market Signals")

if plan == "Free":
    st.subheader("Free Daily Top 3")
    st.table(all_stocks_df.head(3))
    st.warning("Upgrade to Pro to see the Top 100!")

elif plan == "Pro ($5)":
    st.subheader("💎 Pro Top 100 Signals")
    st.dataframe(all_stocks_df.head(100), use_container_width=True)

elif plan == "Elite ($10)":
    st.subheader("🔥 Full Market Scanner (Elite)")
    # Show Top Gainers first
    elite_data = all_stocks_df.sort_values(by="1D %", ascending=False)
    st.dataframe(elite_data, use_container_width=True)

# --- 7. NEWS & AI FEATURES ---
st.divider()
st.header("📰 Weekly Finance Newspaper")
if plan in ["Pro ($5)", "Elite ($10)"]:
    st.info("Latest Edition: Sunday Night Market Wrap-Up")
    if st.button("Generate AI Summary of Current Data"):
        market_context = all_stocks_df.head(10).to_string()
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Write a summary of these stocks: {market_context}"}]
        )
        st.write(resp.choices[0].message.content)
else:
    st.error("Upgrade to Pro or Elite to unlock News and AI advice!")

# --- 8. ELITE SCREENSHOT AI ---
if plan == "Elite ($10)":
    st.divider()
    st.header("📸 Elite Screenshot Analysis")
    st.file_uploader("Upload chart for Buy/Sell signals...", type=['png', 'jpg'])
    st.info("Analysis tool ready for Elite members.")
