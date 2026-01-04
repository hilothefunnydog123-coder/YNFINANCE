import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq
from datetime import datetime

# --- 1. SETUP GROQ ---
# This looks for your key in the Streamlit "Secrets" settings
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Missing Groq API Key! Add it to Streamlit Secrets.")

# --- 2. THE APP THEME ---
st.set_page_config(page_title="QuantTrade Groq", layout="wide")
st.title("⚡ QuantTrade AI (Powered by Groq)")

# --- 3. SIDEBAR MENU ---
st.sidebar.title("Membership Plans")
plan = st.sidebar.selectbox("Choose Plan", ["Free", "Pro ($5)", "Elite ($10)"])
st.sidebar.info("The Sunday Newspaper publishes every Sunday night at 8PM!")

# --- 4. STOCK SCANNER ENGINE ---
def get_stock_picks():
    tickers = ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN", "META", "AMD", "NFLX", "PLTR"]
    results = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            df = stock.history(period="5d")
            if df.empty: continue
            price = df['Close'].iloc[-1]
            change = ((price - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
            results.append({"Ticker": t, "Price": round(price, 2), "5D %": round(change, 2)})
        except: continue
    return pd.DataFrame(results)

# --- 5. DISPLAY LOGIC ---
df_stocks = get_stock_picks()

if plan == "Free":
    st.header("Free Daily Buys")
    st.table(df_stocks.head(3))
elif plan == "Pro ($5)":
    st.header("💎 Pro Unlimited Buys")
    st.dataframe(df_stocks, use_container_width=True)
else:
    st.header("🔥 Elite 'Very Strong' Buys")
    strong_buys = df_stocks[df_stocks['5D %'] > 2.0]
    st.dataframe(strong_buys, use_container_width=True)

# --- 6. AI ADVICE (Using Groq Llama 3) ---
st.divider()
st.header("🤖 AI Portfolio Advisor")
user_query = st.text_input("Ask about your stocks:")
if st.button("Get AI Advice"):
    if user_query:
        with st.spinner("Groq is thinking at 500 tokens/sec..."):
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"Finance expert advice for: {user_query}"}]
            )
            st.write(completion.choices[0].message.content)

# --- 7. SUNDAY NEWSPAPER ---
st.divider()
st.header("📰 Weekly Finance Newspaper")
if datetime.now().weekday() == 6: # Sunday
    if st.button("Generate Sunday Report"):
        market_str = df_stocks.to_string()
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": f"Write a professional Sunday financial newspaper based on this: {market_str}"}]
        )
        st.write(completion.choices[0].message.content)
else:
    st.write("The next edition arrives Sunday night!")

