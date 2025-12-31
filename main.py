from datetime import datetime
import time
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Live Market Data", layout="wide", page_icon="📈")
st.title("Live Security Averages")

with st.sidebar:
    st.header("Settings")
    ticker = st.text_input("Ticker Symbol", "AAPL").upper()
    interval = st.selectbox("Interval", ["1m", "2m", "5m", "15m", "30m", "1h", "1d"], index=2)
    period = st.selectbox("Lookback Period", ["1d", "5d", "1mo", "3mo"], index=0)

    st.divider()

    auto_refresh = st.checkbox("Enable Auto-refresh", value=True)
    refresh_interval = st.slider("Refresh rate (seconds)", 5, 300, 30)

    if st.button("Manual Refresh"):
        st.rerun()

    status_placeholder = st.empty()

try:
    status_placeholder.info("Fetching data...")

    df = yf.download(tickers=ticker, interval=interval, period=period, progress=False)

    if df.empty:
        st.error(f"No data found for **{ticker}**.\n" \
                 "The market might be closed or the symbol is invalid.")
        st.stop()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna()

    if len(df) < 2:
        st.error("Not enough data points to calculate indicators.")
        st.stop()

    df["arith_mean"] = (df["High"] + df["Low"] + df["Close"]) / 3

    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    df["vwap"] = (typical_price * df["Volume"]).cumsum() / df["Volume"].cumsum()

    status_placeholder.success(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

except Exception as e:
    st.error(f"An error occurred: {e}")
    st.stop()

col1, col2, col3, col4 = st.columns(4)

current_close = df["Close"].iloc[-1]
current_vwap = df["vwap"].iloc[-1]
price_change = df["Close"].iloc[-1] - df["Open"].iloc[0]
percent_change = (price_change / df["Open"].iloc[0]) * 100

col1.metric("Latest Close", f"${current_close:.2f}")
col2.metric("VWAP", f"${current_vwap:.2f}", delta=f"{current_close - current_vwap:.2f}")
col3.metric("Period Change", f"{percent_change:.2f}%", delta=f"{price_change:.2f}")
col4.metric("Data Points", len(df))

fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df.index,
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    name="OHLC"
))

fig.add_trace(go.Scatter(
    x=df.index,
    y=df["arith_mean"],
    mode="lines",
    line=dict(color="yellow", width=2),
    name="Arithmetic Mean (H+L+C)/3",
    opacity=0.7
))

fig.add_trace(go.Scatter(
    x=df.index,
    y=df["vwap"],
    mode="lines",
    line=dict(color="orange", width=2),
    name="VWAP"
))

fig.update_layout(
    title=f"{ticker} | {interval} Interval | {period} Period",
    yaxis_title="Price",
    xaxis_title="Date/Time",
    height=600,
    hovermode='x unified',
    xaxis_rangeslider_visible=False,
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)

if auto_refresh:
    countdown_placeholder = st.empty()
    for i in range(refresh_interval, 0, -1):
        countdown_placeholder.caption(f"Refreshing in {i} seconds...")
        time.sleep(1)
    countdown_placeholder.empty()
    st.rerun()
