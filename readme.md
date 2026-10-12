# ⚡ Multi-Index Quantitative Equity Screener (Screener 2.0)

[![Streamlit](https://img.shields.io/badge/Streamlit-1.42+-FF4B4B?style=flat-square&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![NSE India](https://img.shields.io/badge/NSE_India-Real--Time_Data-003366?style=flat-square)](https://www.nseindia.com)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive_Charts-3F4F75?style=flat-square&logo=plotly)](https://plotly.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

A high-performance quantitative equity research and factor-investing screener for Indian stock markets (**NSE & BSE**). Built with **Python**, **Streamlit**, direct **NSE India Session APIs**, and **Plotly**, wrapped in a sleek **Pitch Black & Electric Indigo** design system.

The platform eliminates static stock lists by **dynamically fetching live index constituents directly from official exchange feeds**, shielding your research from manual updates across index rebalancing cycles.

---

## 🌟 Key Features

### ⚡ Sub-Second Live Market Data & Dynamic Rebalancing
- **Direct Official NSE India Session Ingestion:** Retrieves real-time constituent prices, volume, and intraday changes in **< 400ms** per index in a single network roundtrip.
- **100% Dynamic Rebalancing (Zero Hardcoded Stocks):** Automatically captures additions and deletions during biannual index rebalancings (March & September) directly from live exchange feeds and official archives.
- **Graceful Fallbacks:** Built-in multi-layered failover to Yahoo Finance batch quotes and official exchange archives ensuring zero downtime.

### 📌 Multi-Index Universe Support
Seamlessly switch between core benchmark and sectoral universes:
- **Major Benchmarks:** Nifty 50, BSE Sensex 30, Bank Nifty, Nifty Next 50, Nifty 100
- **Midcaps & Broad Market:** Nifty Midcap 50, Nifty Midcap 100
- **Key Sectoral Indices:** Nifty IT, Nifty Auto, Nifty Pharma, Nifty FMCG

### 🧮 Multi-Factor Quantitative Engine
A modular factor model that standardizes metrics cross-sectionally across peers using **Winsorization (outlier clipping)** and **Z-Score Normalization**:
- **💎 Value Factor:** P/E Ratio, P/B Ratio, Free Cash Flow Yield
- **🏆 Quality Factor:** Return on Equity (ROE), Operating Margin, Debt-to-Equity
- **🚀 Growth Factor:** Quarterly Revenue Growth, EPS Growth
- **Interactive Weight Customization:** Fine-tune factor allocations in real time via responsive sliders with an interactive hovering `ℹ` factor guide explaining model mechanics.

### 📈 Interactive Stock Price Charts
- **Click-to-Graph Visualization:** Simply select any row in the quantitative leaderboard to instantly generate a smooth, interactive Plotly line chart with volume subplots.
- **Multi-Period Range Toggles:** Easily switch between **1M**, **3M**, **6M**, **1Y**, and **5Y** price intervals with high/low annotations.

### 🎨 Pitch Black & Electric Indigo UI
- **Modern Dark Aesthetic:** Custom-engineered palette (`#090A0F` Pitch Black background, `#12141D` Charcoal Grey surface cards, and `#6366F1` Electric Indigo accents).
- **Clean Number Formatting:** Rigorous 2-decimal truncation across all financial ratios and percentage metrics with color-coded positive/negative badges.
- **Factor Matrix Visualization:** 2D interactive scatter plot mapping Value vs. Quality factor scores across all peer constituents.

---

## 🏗️ System Architecture

```text
├── app.py              # Main Streamlit UI dashboard & interactive chart views
├── quant.py            # Quantitative factor calculation & Z-scoring engine
├── fetcher.py          # Ultra-fast NSE Session API & Yahoo batch multi-index fetcher
├── database.py         # SQLite database management, migrations & upsert caching
├── main.py             # CLI leaderboard runner
├── requirements.txt    # Production dependencies
└── .streamlit/
    └── config.toml     # Streamlit theme & server configuration
```

---

## 🚀 Quickstart Guide

### 1. Clone the Repository
```bash
git clone https://github.com/Crypto2007/screener2.o.git
cd screener2.o
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Screener
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🛠️ Tech Stack

- **Frontend & App Framework:** [Streamlit](https://streamlit.io/)
- **Data Visualization:** [Plotly Express & Graph Objects](https://plotly.com/python/)
- **Data Engineering:** [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
- **Market Data Feeds:** Official NSE Session API, BSE India, [yfinance](https://github.com/ranaroussi/yfinance)
- **Local Storage:** SQLite3 with automated schema migrations

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).