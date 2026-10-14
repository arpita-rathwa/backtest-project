import warnings
warnings.filterwarnings("ignore")

import json
import os

import pandas as pd
import streamlit as st
import yfinance as yf
from backtesting import Backtest, Strategy
from backtesting.lib import crossover


def rsi(series, n=14):
    delta = pd.Series(series).diff()
    gain = delta.clip(lower=0).rolling(n).mean()
    loss = (-delta.clip(upper=0)).rolling(n).mean()
    return 100 - 100 / (1 + gain / loss)


class RsiOscillator(Strategy):
    upper_bound = 70
    lower_bound = 30
    rsi_window = 14

    def init(self):
        self.rsi = self.I(rsi, self.data.Close, self.rsi_window)

    def next(self):
        if crossover(self.rsi, self.upper_bound):
            if self.position:
                self.position.close()
        elif crossover(self.lower_bound, self.rsi):
            if not self.position:
                self.buy(size=0.95)


@st.cache_data(show_spinner="Downloading prices...")
def load_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df[["Open", "High", "Low", "Close", "Volume"]].dropna()


COMPANIES = {
    "Reliance Industries": "RELIANCE.NS",
    "Tata Consultancy Services": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Hindustan Unilever": "HINDUNILVR.NS",
    "ITC": "ITC.NS",
    "State Bank of India": "SBIN.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "Larsen & Toubro": "LT.NS",
    "Axis Bank": "AXISBANK.NS",
    "Asian Paints": "ASIANPAINT.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "Sun Pharma": "SUNPHARMA.NS",
    "Titan": "TITAN.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
    "Wipro": "WIPRO.NS",
    "UltraTech Cement": "ULTRACEMCO.NS",
    "Nestle India": "NESTLEIND.NS",
    "Tata Steel": "TATASTEEL.NS",
    "HCL Technologies": "HCLTECH.NS",
    "ONGC": "ONGC.NS",
    "NTPC": "NTPC.NS",
    "Power Grid": "POWERGRID.NS",
    "Mahindra & Mahindra": "M&M.NS",
    "Adani Enterprises": "ADANIENT.NS",
    "Coal India": "COALINDIA.NS",
    "Tech Mahindra": "TECHM.NS",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Alphabet (Google)": "GOOGL",
    "Amazon": "AMZN",
    "Tesla": "TSLA",
    "Nvidia": "NVDA",
    "Other (type ticker)": None,
}

st.title("Mini Backtesting Engine")

with st.sidebar:
    name = st.selectbox("Company (type to search)", list(COMPANIES))
    ticker = COMPANIES[name]
    if ticker is None:
        ticker = st.text_input("Ticker (NSE: add .NS)", "INFY.NS").upper().strip()
    start = st.date_input("Start", pd.Timestamp("2019-01-01"))
    end = st.date_input("End", pd.Timestamp.today())
    cash = st.number_input("Starting cash", 1000, 10_000_000, 100_000, step=1000)
    commission = st.slider("Commission (%)", 0.0, 1.0, 0.1, 0.05) / 100
    lower = st.slider("RSI buy below", 10, 45, 30)
    upper = st.slider("RSI sell above", 55, 90, 70)
    window = st.slider("RSI window", 5, 30, 14)
    run = st.button("Run backtest", type="primary")

PORTFOLIO_FILE = "portfolio.json"
START_CASH = 1_000_000


def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE) as f:
            return json.load(f)
    return {"cash": START_CASH, "holdings": {}, "log": []}


def save_portfolio(p):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(p, f, indent=2)


@st.cache_data(ttl=60, show_spinner=False)
def latest_price(symbol):
    hist = yf.Ticker(symbol).history(period="5d")
    return float(hist["Close"].iloc[-1]) if not hist.empty else None


data = load_data(ticker, start, end)
if data.empty:
    st.error("No data found. Check the ticker (Indian stocks end in .NS).")
    st.stop()

tab_bt, tab_pf = st.tabs(["Backtest", "Paper Portfolio"])

with tab_bt:
    st.subheader(f"{ticker} price")
    st.line_chart(data["Close"])

    if run:
        bt = Backtest(data, RsiOscillator, cash=cash, commission=commission)
        stats = bt.run(lower_bound=lower, upper_bound=upper, rsi_window=window)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Strategy return", f"{stats['Return [%]']:.1f}%")
        c2.metric("Buy & hold", f"{stats['Buy & Hold Return [%]']:.1f}%")
        c3.metric("Sharpe", f"{stats['Sharpe Ratio']:.2f}")
        c4.metric("Max drawdown", f"{stats['Max. Drawdown [%]']:.1f}%")

        st.subheader("Equity curve")
        st.line_chart(stats["_equity_curve"]["Equity"])

        st.subheader("Trades")
        st.dataframe(stats["_trades"])

with tab_pf:
    pf = load_portfolio()
    price = latest_price(ticker)

    if price is None:
        st.error("Could not fetch a live price for this ticker.")
    else:
        st.subheader(f"Trade {ticker} at {price:,.2f}")
        qty = st.number_input("Quantity", min_value=1, value=1, step=1)
        b, s_ = st.columns(2)

        if b.button("Buy", type="primary"):
            cost = qty * price
            if cost > pf["cash"]:
                st.error("Not enough cash.")
            else:
                pf["cash"] -= cost
                pf["holdings"][ticker] = pf["holdings"].get(ticker, 0) + qty
                pf["log"].append({"side": "BUY", "ticker": ticker, "qty": qty, "price": round(price, 2)})
                save_portfolio(pf)
                st.rerun()

        if s_.button("Sell"):
            if pf["holdings"].get(ticker, 0) < qty:
                st.error("You don't own that many shares.")
            else:
                pf["cash"] += qty * price
                pf["holdings"][ticker] -= qty
                if pf["holdings"][ticker] == 0:
                    del pf["holdings"][ticker]
                pf["log"].append({"side": "SELL", "ticker": ticker, "qty": qty, "price": round(price, 2)})
                save_portfolio(pf)
                st.rerun()

    rows, holdings_value = [], 0.0
    for sym, q in pf["holdings"].items():
        p_now = latest_price(sym) or 0.0
        holdings_value += q * p_now
        rows.append({"Ticker": sym, "Qty": q, "Price": round(p_now, 2), "Value": round(q * p_now, 2)})

    total = pf["cash"] + holdings_value
    m1, m2, m3 = st.columns(3)
    m1.metric("Cash", f"{pf['cash']:,.0f}")
    m2.metric("Holdings", f"{holdings_value:,.0f}")
    m3.metric("Total", f"{total:,.0f}", f"{(total / START_CASH - 1) * 100:.2f}%")

    st.subheader("Holdings")
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True)
    else:
        st.caption("No holdings yet.")

    st.subheader("Trade history")
    if pf["log"]:
        st.dataframe(pd.DataFrame(pf["log"][::-1]), hide_index=True)

    if st.button("Reset portfolio"):
        save_portfolio({"cash": START_CASH, "holdings": {}, "log": []})
        st.rerun()