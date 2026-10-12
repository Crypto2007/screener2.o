# ⚡ Multi-Index Quantitative Equity Screener

A high-performance quantitative equity research screener built with **Python**, **Streamlit**, **NSE India Session API**, **yfinance**, and **SQLite**. 

This application fetches real-time market data and fundamentals for **Nifty 50**, **Bank Nifty**, **BSE Sensex**, **Nifty IT**, and **Nifty Next 50**, normalizes metrics using **Z-score standardisation and Winsorization**, and ranks companies dynamically based on customizable factor weights.

---

## 🌟 Key Features

- **⚡ Sub-Second Live Market Data:** Direct connection to official NSE India Session API fetching all index constituents in **< 400ms** in a single call (with fallback to Yahoo batch quotes).
- **🔄 100% Dynamic Rebalancing (Zero Hardcoded Stocks):** All index constituents are pulled live from exchange APIs and official archives. Whenever an index rebalances (March/September), new constituents are tracked automatically with zero manual code updates.
- **📌 Multi-Index Universe Support:**
  - **Nifty 50** (NSE Benchmark)
  - **Bank Nifty** (Banking Index)
  - **BSE Sensex** (30 Bluechips)
  - **Nifty IT** (Tech Sector)
  - **Nifty Next 50**, **Nifty 100**, **Nifty Midcap 50**, **Nifty Auto**, **Nifty Pharma**, **Nifty FMCG**
- **Multi-Factor Quant Model:**
  - **Value Factor:** P/E Ratio, P/B Ratio, Free Cash Flow Yield
  - **Quality Factor:** Return on Equity (ROE), Operating Margin, Debt-to-Equity
  - **Growth Factor:** Revenue Growth, EPS Growth
- **Two-Tier Fast Architecture:**
  - **⚡ Quick Live Price Refresh:** Sub-second tick updates (<400ms) without heavy balance-sheet scraping.
  - **🔄 Full Fundamental Sync:** Periodic deep synchronization of quarterly financials.
- **Statistical Normalization:** Outlier clipping (Winsorization) and Z-score standardization across index peers.
- **Interactive UI:**
  - Index universe switcher dropdown.
  - Real-time factor weight customization sliders.
  - Sector filtering, search bar, and CSV export.
  - Plotly Value vs. Quality factor scatter matrix.
  - Stock deep-dive analysis cards with 52-week ranges.
- **Caching Layer:** SQLite database persistence (`screener_cache.db`) with dynamic migrations.

---

## 🏗️ Project Architecture

```text
├── app.py              # Main Streamlit UI dashboard with multi-index navigation
├── quant.py            # Quantitative factor calculation & Z-scoring engine
├── fetcher.py          # Ultra-fast NSE Session API & Yahoo batch multi-index fetcher
├── database.py         # SQLite database management, migrations & upsert caching
├── main.py             # CLI leaderboard runner
├── requirements.txt    # Production dependencies (Streamlit, Pandas, Requests, Plotly)
└── .streamlit/
    └── config.toml     # Streamlit theme & server configuration
```