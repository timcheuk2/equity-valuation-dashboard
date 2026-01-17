import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. setup page
st.set_page_config(page_title="Equity Analytics", layout="wide")
st.title("📊 Equity Valuation & Sensitivity Dashboard")

# 2. sidebar for user inputs
with st.sidebar:
    st.header("Valuation Model Inputs")
    ticker = st.text_input("Ticker Symbol", value = "")
    wacc = st.slider("Discount Rate (WACC) %", 5.0, 15.0, 10.0)/100
    growth = st.slider("Terminal Growth %", 1.0, 4.0, 2.0)/100

if ticker:
    stock = yf.Ticker(ticker)
else:
    st.info("Please enter a ticker symbol (e.g., AAPL, TSLA) to begin.")
    st.stop()

# 3. The Math Engine
if st.button("Run Analytics"):
    try:
        hist=stock.history(period="1d")
        if hist.empty:
            st.error(f"Ticker '{ticker}' not found. Please check the spelling." )
            st.stop()

        fcf = stock.cashflow.loc["Free Cash Flow"].iloc[0]
        shares = stock.info['sharesOutstanding']

        intrinsic_value = (fcf * (1+growth)) / (wacc - growth) / shares
    except Exception as e: 
        st.error(f'Error fetching data for {ticker}. The ticker may be invalid or delisted.')
        st.stop()
    

    # Assuming 'intrinsic_value' is your baseline result from the matrix center
    current_price = stock.history(period="1d")['Close'].iloc[-1]
    upside = ((intrinsic_value / current_price) - 1) * 100


    col1, col2, col3 = st.columns(3)
    col1.metric(f"{ticker} Current Price", f"${current_price:.2f}")
    col2.metric("Intrinsic Value (Base)", f"${intrinsic_value:.2f}")
    col3.metric("Upside / Downside", f"{upside:.1f}%", delta=f"{upside:.1f}%")

    #Sensitivity Matrix
    wacc_range = np.linspace(wacc - 0.02, wacc + 0.02, 5)
    growth_range = np.linspace(growth - 0.01, growth + 0.01, 5)

    results = []
    for g in growth_range:
        row = [(fcf * (1+g)) / (w-g) / shares for w in wacc_range]
        results.append(row)
    
    df = pd.DataFrame(results,
    index = [f"Growth: {g*100:.1f}%" for g in growth_range],
    columns = [f"WACC: {w*100:.1f}%" for w in wacc_range])

    st.subheader(f"Intrinsic Value Sensitivity for {ticker}")
    st.dataframe(df.style.format("${:.2f}"))

with st.sidebar:
    st.divider()
    st.subheader(f"🗞️ Latest {ticker} News")
    
    # We use a 'try/except' block—this is a pro move in Business Analytics 
    # to prevent the whole app from crashing if the news feed is down.
    try:
        news_list = stock.news
        if news_list:
            for news in news_list[:3]:
                st.write(f"**{news['title']}**")
                st.caption(f"Source: {news['publisher']}")
                st.link_button("Read Article", news['link'])
        else:
            st.write("No recent news found for this ticker.")
    except Exception:
        st.write("News feed currently unavailable.")