import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# --- 1. SETUP GEMINI AI ---
# This looks for your key in the Streamlit "Secrets" settings
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    st.error("Missing Gemini API Key! Add it to Streamlit Secrets.")

# --- 2. THE APP THEME ---
st.set_page_config(page_title="QuantTrade Gemini", layout="wide")
st.title("🚀 QuantTrade AI (Powered by Gemini)")

# --- 3. SIDEBAR MENU ---
st.sidebar.title("Membership Plans")
plan = st.sidebar.selectbox("Choose Plan", ["Free", "Pro ($5)", "Elite ($10)"])
st.sidebar.info("The Sunday Newspaper publishes every Sunday night at 8PM!")

# --- 4. STOCK SCANNER ENGINE ---
def get_stock_picks():
    # You can add more tickers here from your original long list
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
    st.write("Showing top 3 picks:")
    st.table(df_stocks.head(3))
elif plan == "Pro ($5)":
    st.header("💎 Pro Unlimited Buys")
    st.write("Updating every minute for Pro members.")
    st.dataframe(df_stocks, use_container_width=True)
else:
    st.header("🔥 Elite 'Very Strong' Buys")
    # Show stocks with high 5-day growth
    strong_buys = df_stocks[df_stocks['5D %'] > 2.0]
    st.dataframe(strong_buys, use_container_width=True)

# --- 6. AI ADVICE (Free with Gemini Key) ---
st.divider()
st.header("🤖 AI Portfolio Advisor")
user_query = st.text_input("Ask about your stocks or portfolio strategy:")
if st.button("Get AI Advice"):
    if user_query:
        with st.spinner("Gemini is thinking..."):
            response = model.generate_content(f"You are a finance expert. User asks: {user_query}")
            st.write(response.text)
    else:
        st.warning("Please enter a question first.")

# --- 7. SCREENSHOT AI (Elite $10 Only) ---
if plan == "Elite ($10)":
    st.divider()
    st.header("📸 Screenshot Chart Analyzer")
    uploaded_file = st.file_uploader("Upload a trading chart screenshot", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        st.image(uploaded_file, caption="Target Chart", width=500)
        if st.button("Analyze with Gemini Vision"):
            with st.spinner("Analyzing image..."):
                # Gemini can read images directly
                img_data = uploaded_file.getvalue()
                response = model.generate_content([
                    "Analyze this trading chart. Give a BUY or SELL signal, a Take Profit (TP), and a Stop Loss (SL).", 
                    {"mime_type": "image/jpeg", "data": img_data}
                ])
                st.success("Analysis Complete!")
                st.write(response.text)

# --- 8. SUNDAY NEWSPAPER ---
st.divider()
st.header("📰 Weekly Finance Newspaper")
# Only show content if today is Sunday (day 6)
if datetime.now().weekday() == 6:
    st.write("### 📢 THE SUNDAY GAZETTE")
    st.write("The market showed major volatility this week. Here is your AI summary...")
    # You can add a button here to use Gemini to summarize the whole week
else:
    st.write("The next edition arrives this Sunday night at 8:00 PM EST!")


