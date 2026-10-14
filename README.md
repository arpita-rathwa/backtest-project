# Mini Backtesting Engine

An interactive web app for backtesting an RSI trading strategy on real stock data and practising trades in a paper (virtual) portfolio. Built with Python and Streamlit.

**Live app:** https://backtest-project-3mmg8ghagewpwilmuchhwi.streamlit.app/

> Educational project. Nothing here is financial advice, and no real money is involved.

## Features

- **Stock selection:** choose from about 35 popular Indian (NSE) and US stocks, or type any Yahoo Finance ticker.
- **Price charts:** historical closing prices for the selected stock and date range.
- **RSI backtesting:** set the RSI window, buy threshold, sell threshold, starting cash and commission, then run the strategy.
- **Performance metrics:** strategy return vs buy-and-hold, Sharpe ratio, maximum drawdown, equity curve and a full trade list.
- **Paper portfolio:** start with virtual cash, buy and sell at the latest market price, and track holdings, total value and trade history.

## How the strategy works

The strategy trades on the Relative Strength Index (RSI), a momentum indicator from 0 to 100.

- **Buy** when RSI crosses back above the lower threshold (default 30, "oversold").
- **Sell** when RSI crosses above the upper threshold (default 70, "overbought").
- Only one position is held at a time, and each buy uses 95% of available cash.

Backtesting is done with the [`backtesting.py`](https://kernc.github.io/backtesting.py/) library, which executes orders on the next bar to avoid lookahead bias. RSI is computed with plain pandas, so no TA-Lib install is needed.

## Tech stack

- Python 3.12
- Streamlit (UI)
- backtesting.py (strategy engine)
- yfinance (market data)
- pandas, numpy

## Run locally

```bash
git clone https://github.com/arpita-rathwa/backtest-project.git
cd backtest-project

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

python -m pip install -r requirements.txt
python -m streamlit run mini_backtesting_engine.py
```

The app opens at `http://localhost:8501`.

## Project structure

```
backtest-project/
├── mini_backtesting_engine.py   # Streamlit app: strategy, backtest tab, paper portfolio tab
├── requirements.txt             # Dependencies (also used by Streamlit Cloud)
└── README.md
```

## Usage

1. Pick a company in the sidebar (or choose **Other** and type a ticker such as `IRCTC.NS` or `META`).
2. Set the date range, cash, commission and RSI parameters.
3. Click **Run backtest** and compare the strategy against buy-and-hold.
4. Open the **Paper Portfolio** tab to buy and sell the selected stock with virtual cash.

## Limitations

- **Overfitting:** tuning RSI parameters on past data can produce results that don't hold up on new data. A good result in a backtest is not evidence of future profit.
- **Simplified costs:** commission is modelled as a flat percentage. Slippage, taxes and liquidity are ignored.
- **Single shared portfolio:** the paper portfolio is stored in one `portfolio.json` file, so on a hosted deployment all visitors share it and it resets when the app restarts.
- **Data source:** prices come from Yahoo Finance through yfinance and may be delayed or occasionally missing.

## Roadmap

- User login with a separate saved portfolio per user
- Train/test split to check strategies on unseen data
- More strategies (moving-average crossover, Bollinger Bands)
- Parameter optimization heatmap

## License

MIT
