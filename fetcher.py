import io
import logging
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple, Optional
import requests
import pandas as pd
import yfinance as yf

import database as db

logger = logging.getLogger(__name__)

# Official Index Registry — ZERO HARDCODED STOCKS!
# All constituents are fetched dynamically from NSE / BSE servers to automatically track rebalancings.
INDEX_REGISTRY: Dict[str, Dict[str, Any]] = {
    "Nifty 50": {
        "type": "NSE",
        "slug": "NIFTY 50",
        "csv_slug": "nifty50",
        "description": "NSE Benchmark index — 50 large-cap market leaders",
    },
    "Bank Nifty": {
        "type": "NSE",
        "slug": "NIFTY BANK",
        "csv_slug": "niftybank",
        "description": "NSE Banking Sector — 12 most liquid Indian banks",
    },
    "Sensex (BSE 30)": {
        "type": "BSE",
        "slug": "16",
        "csv_slug": None,
        "description": "BSE Benchmark index — 30 premier blue-chip companies",
    },
    "Nifty IT": {
        "type": "NSE",
        "slug": "NIFTY IT",
        "csv_slug": "niftyit",
        "description": "Indian technology & software leaders",
    },
    "Nifty Next 50": {
        "type": "NSE",
        "slug": "NIFTY NEXT 50",
        "csv_slug": "niftynext50",
        "description": "50 large-cap companies immediately behind Nifty 50",
    },
    "Nifty 100": {
        "type": "NSE",
        "slug": "NIFTY 100",
        "csv_slug": "nifty100",
        "description": "Top 100 Indian large-cap companies",
    },
    "Nifty Midcap 50": {
        "type": "NSE",
        "slug": "NIFTY MIDCAP 50",
        "csv_slug": "niftymidcap50",
        "description": "Top 50 high-growth mid-cap companies",
    },
    "Nifty Auto": {
        "type": "NSE",
        "slug": "NIFTY AUTO",
        "csv_slug": "niftyauto",
        "description": "Top automotive OEMs and component manufacturers",
    },
    "Nifty Pharma": {
        "type": "NSE",
        "slug": "NIFTY PHARMA",
        "csv_slug": "niftypharma",
        "description": "Top pharmaceutical and healthcare leaders",
    },
    "Nifty FMCG": {
        "type": "NSE",
        "slug": "NIFTY FMCG",
        "csv_slug": "niftyfmcg",
        "description": "Fast-moving consumer goods giants",
    }
}

# Standard browser headers for live exchange APIs
EXCHANGE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/market-data/live-equity-market",
}


def _create_nse_session() -> requests.Session:
    """Create a configured session with valid NSE session cookies."""
    session = requests.Session()
    session.headers.update(EXCHANGE_HEADERS)
    try:
        # Handshake with home page to obtain session cookies
        session.get("https://www.nseindia.com", timeout=4)
    except Exception as err:
        logger.debug("Initial NSE handshake warning: %s", err)
    return session


def fetch_nse_live_constituents(slug: str) -> Tuple[List[Dict[str, Any]], float]:
    """
    Dynamically fetch all constituent stocks and live prices from NSE India.
    Zero hardcoding: the API response returns every current constituent stock.
    Automatically reflects index rebalancing without any manual edits.
    """
    t0 = time.time()
    session = _create_nse_session()
    encoded_slug = urllib.parse.quote(slug)
    url = f"https://www.nseindia.com/api/equity-stockIndices?index={encoded_slug}"

    resp = session.get(url, timeout=5)
    resp.raise_for_status()

    payload = resp.json()
    raw_data = payload.get("data", [])
    quotes = []

    for item in raw_data:
        sym = item.get("symbol")
        # Exclude index aggregate header row
        if not sym or sym.upper() == slug.upper() or item.get("priority") == 0:
            continue

        meta_info = item.get("meta") or {}
        company_name = meta_info.get("companyName") or item.get("identifier", sym).replace("EQN", "").replace("EQ", "")
        industry = meta_info.get("industry") or item.get("sector") or "General"

        quotes.append({
            "ticker": sym,
            "company_name": company_name,
            "sector": industry,
            "current_price": round(float(item["lastPrice"]), 2) if item.get("lastPrice") is not None else None,
            "change": round(float(item["change"]), 2) if item.get("change") is not None else 0.0,
            "p_change": round(float(item["pChange"]), 2) if item.get("pChange") is not None else 0.0,
            "fifty_two_week_high": round(float(item["yearHigh"]), 2) if item.get("yearHigh") else None,
            "fifty_two_week_low": round(float(item["yearLow"]), 2) if item.get("yearLow") else None,
            "volume": float(item["totalTradedVolume"]) if item.get("totalTradedVolume") is not None else 0.0,
            "pe_ratio": round(float(item["pe"]), 2) if item.get("pe") not in (None, "-", "") else None,
            "pb_ratio": round(float(item["pb"]), 2) if item.get("pb") not in (None, "-", "") else None,
        })

    latency_ms = (time.time() - t0) * 1000.0
    return quotes, latency_ms


def fetch_bse_live_constituents(index_code: str = "16") -> Tuple[List[Dict[str, Any]], float]:
    """
    Dynamically fetch constituent stocks and live ticks from BSE India API (Sensex 30).
    Zero hardcoding: constituents are parsed directly from BSE's official endpoint.
    """
    t0 = time.time()
    session = requests.Session()
    session.headers.update({
        "User-Agent": EXCHANGE_HEADERS["User-Agent"],
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.bseindia.com/",
    })

    # BSE API endpoint for index constituents (16 = S&P BSE SENSEX)
    url = f"https://api.bseindia.com/BseIndiaAPI/api/GetIndexConstituent/w?index={index_code}"
    resp = session.get(url, timeout=5)
    resp.raise_for_status()

    data = resp.json()
    items = data.get("Table", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    quotes = []

    for item in items:
        sym = item.get("scrip_id") or item.get("Symbol") or item.get("Security_Code")
        if not sym:
            continue
        quotes.append({
            "ticker": str(sym).strip(),
            "company_name": item.get("security_name") or item.get("Security_Name") or str(sym),
            "sector": item.get("industry") or item.get("Sector") or "General",
            "current_price": float(item["LTP"]) if item.get("LTP") else None,
            "change": float(item.get("Change", 0.0) or 0.0),
            "p_change": float(item.get("PChange", 0.0) or 0.0),
            "volume": float(item.get("Volume", 0.0) or 0.0),
            "fifty_two_week_high": float(item["FiftyTwoWeekHigh"]) if item.get("FiftyTwoWeekHigh") else None,
            "fifty_two_week_low": float(item["FiftyTwoWeekLow"]) if item.get("FiftyTwoWeekLow") else None,
        })

    latency_ms = (time.time() - t0) * 1000.0
    return quotes, latency_ms


def fetch_nse_archive_csv_constituents(csv_slug: str) -> List[Dict[str, Any]]:
    """
    Fallback method: Fetch the official rebalanced constituent CSV from NSE Archives.
    Example: https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv
    """
    url = f"https://nsearchives.nseindia.com/content/indices/ind_{csv_slug}list.csv"
    try:
        session = requests.Session()
        session.headers.update(EXCHANGE_HEADERS)
        resp = session.get(url, timeout=5)
        resp.raise_for_status()
        csv_df = pd.read_csv(io.StringIO(resp.text))
        records = []
        for _, row in csv_df.iterrows():
            sym = row.get("Symbol")
            if pd.notnull(sym):
                records.append({
                    "ticker": str(sym).strip(),
                    "company_name": row.get("Company Name", sym),
                    "sector": row.get("Industry", "General"),
                })
        return records
    except Exception as err:
        logger.warning("Failed to fetch official NSE constituent CSV for %s: %s", csv_slug, err)
        return []


def fetch_yahoo_batch_quotes(tickers: List[str]) -> Tuple[List[Dict[str, Any]], float]:
    """
    Fallback batch quote fetcher using Yahoo Finance for price ticks.
    """
    t0 = time.time()
    yf_symbols = [f"{t}.NS" for t in tickers]
    quotes = []

    try:
        data = yf.download(yf_symbols, period="2d", group_by="ticker", progress=False, threads=True)
        for sym in tickers:
            yf_sym = f"{sym}.NS"
            try:
                sub = data[yf_sym].dropna() if yf_sym in data else pd.DataFrame()
                if not sub.empty:
                    last_row = sub.iloc[-1]
                    price = float(last_row["Close"])
                    prev_close = float(sub.iloc[-2]["Close"]) if len(sub) > 1 else price
                    chg = price - prev_close
                    p_chg = (chg / prev_close * 100.0) if prev_close else 0.0
                    vol = float(last_row.get("Volume", 0.0))
                    quotes.append({
                        "ticker": sym,
                        "current_price": price,
                        "change": chg,
                        "p_change": p_chg,
                        "volume": vol,
                    })
            except Exception:
                continue
    except Exception as err:
        logger.warning("Yahoo batch quote error: %s", err)

    latency_ms = (time.time() - t0) * 1000.0
    return quotes, latency_ms


def fetch_ticker_metrics(ticker_symbol: str) -> Dict[str, Any]:
    """Fetch fundamental metrics for a single ticker via yfinance."""
    clean_symbol = ticker_symbol.replace(".NS", "").replace(".BO", "")
    yf_symbol = f"{clean_symbol}.NS"

    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info or {}

        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")

        return {
            "ticker": clean_symbol,
            "company_name": info.get("shortName") or info.get("longName") or clean_symbol,
            "sector": info.get("sector") or "General",
            "industry": info.get("industry") or "General",
            "market_cap": round(float(info.get("marketCap", 0.0) or 0.0), 2),
            "pe_ratio": round(float(pe), 2) if (pe := (info.get("trailingPE") or info.get("forwardPE"))) is not None else None,
            "pb_ratio": round(float(pb), 2) if (pb := info.get("priceToBook")) is not None else None,
            "ps_ratio": round(float(ps), 2) if (ps := info.get("priceToSalesTrailing12Months")) is not None else None,
            "ev_ebitda": round(float(ev), 2) if (ev := info.get("enterpriseToEbitda")) is not None else None,
            "roe": round(float(roe), 4) if (roe := info.get("returnOnEquity")) is not None else None,
            "roa": round(float(roa), 4) if (roa := info.get("returnOnAssets")) is not None else None,
            "gross_margin": round(float(gm), 4) if (gm := info.get("grossMargins")) is not None else None,
            "operating_margin": round(float(om), 4) if (om := info.get("operatingMargins")) is not None else None,
            "net_margin": round(float(nm), 4) if (nm := info.get("profitMargins")) is not None else None,
            "revenue_growth": round(float(rg), 4) if (rg := info.get("revenueGrowth")) is not None else None,
            "earnings_growth": round(float(eg), 4) if (eg := info.get("earningsGrowth")) is not None else None,
            "free_cashflow_yield": (
                round(float(info.get("freeCashflow", 0.0) / info.get("marketCap", 1.0)), 4)
                if info.get("marketCap") and info.get("freeCashflow")
                else None
            ),
            "debt_to_equity": round(float(de), 2) if (de := info.get("debtToEquity")) is not None else None,
            "current_ratio": round(float(cr), 2) if (cr := info.get("currentRatio")) is not None else None,
            "quick_ratio": round(float(qr), 2) if (qr := info.get("quickRatio")) is not None else None,
            "dividend_yield": round(float(dy), 4) if (dy := info.get("dividendYield")) is not None else None,
            "payout_ratio": round(float(pr), 4) if (pr := info.get("payoutRatio")) is not None else None,
            "beta": round(float(b), 2) if (b := info.get("beta")) is not None else None,
            "fifty_two_week_high": round(float(h), 2) if (h := info.get("fiftyTwoWeekHigh")) is not None else None,
            "fifty_two_week_low": round(float(l), 2) if (l := info.get("fiftyTwoWeekLow")) is not None else None,
            "current_price": round(float(price), 2) if price is not None else None,
        }
    except Exception as err:
        logger.warning("Failed to fetch metrics for %s: %s", ticker_symbol, err)
        return {
            "ticker": clean_symbol,
            "company_name": clean_symbol,
            "sector": "General",
        }


def fetch_fundamentals_batch(tickers: List[str], max_workers: int = 10) -> pd.DataFrame:
    """Concurrently fetch fundamental metrics for a list of tickers."""
    records = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_sym = {executor.submit(fetch_ticker_metrics, sym): sym for sym in tickers}
        for future in as_completed(future_to_sym):
            try:
                res = future.result()
                if res:
                    records.append(res)
            except Exception as err:
                sym = future_to_sym[future]
                logger.debug("Error processing %s: %s", sym, err)

    return pd.DataFrame(records)


def fetch_universe_data(
    index_key: str = "Nifty 50",
    force_fundamentals: bool = False,
    max_workers: int = 10
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    100% Dynamic Multi-Index Data Fetcher:
    1. Connects to official NSE/BSE live API to fetch current rebalanced constituents & quotes (<400ms).
    2. Saves rebalanced constituent membership to SQLite.
    3. Merges live ticks with cached fundamentals (ROE, Margins, Debt, P/B).
    4. Auto-seeds fundamentals for any new constituents entering the index upon rebalancing.
    """
    cfg = INDEX_REGISTRY.get(index_key, INDEX_REGISTRY["Nifty 50"])
    index_type = cfg["type"]
    slug = cfg["slug"]
    csv_slug = cfg.get("csv_slug")

    live_quotes: List[Dict[str, Any]] = []
    latency_ms = 0.0
    source_label = f"{index_type} Official Live API"

    # Step 1: Dynamically fetch constituents & quotes from Exchange
    if index_type == "NSE":
        try:
            live_quotes, latency_ms = fetch_nse_live_constituents(slug)
        except Exception as nse_err:
            logger.warning("Live NSE endpoint failed for %s: %s", slug, nse_err)
    elif index_type == "BSE":
        try:
            live_quotes, latency_ms = fetch_bse_live_constituents(slug)
        except Exception as bse_err:
            logger.warning("Live BSE endpoint failed for %s: %s", slug, bse_err)

    # Step 2: Handle fallback if Exchange API is temporarily down
    if not live_quotes and csv_slug:
        logger.info("Attempting official NSE archive CSV for %s...", csv_slug)
        csv_records = fetch_nse_archive_csv_constituents(csv_slug)
        if csv_records:
            tickers = [r["ticker"] for r in csv_records]
            batch_quotes, latency_ms = fetch_yahoo_batch_quotes(tickers)
            source_label = "NSE Official Archive CSV + Batch Quotes"
            # Merge CSV metadata with batch quotes
            quote_map = {q["ticker"]: q for q in batch_quotes}
            for r in csv_records:
                sym = r["ticker"]
                q_data = quote_map.get(sym, {})
                r.update(q_data)
            live_quotes = csv_records

    # Step 3: Handle offline fallback from SQLite constituents table
    if not live_quotes:
        cached_tickers = db.load_index_constituents(index_key)
        if cached_tickers:
            logger.info("Loading %d cached rebalanced constituents from SQLite...", len(cached_tickers))
            batch_quotes, latency_ms = fetch_yahoo_batch_quotes(cached_tickers)
            source_label = "Cached Constituents + Batch Quotes"
            live_quotes = batch_quotes

    # Save dynamically discovered constituent membership into SQLite
    if live_quotes:
        db.save_index_constituents(index_key, live_quotes)

    live_df = pd.DataFrame(live_quotes)
    if live_df.empty:
        # Ultimate fallback to cached stocks
        return db.load_stock_cache(), {"source": "Local Cache", "latency_ms": 0.0, "count": 0, "timestamp": "N/A"}

    live_df["index_name"] = index_key
    active_tickers = live_df["ticker"].tolist()

    # Step 4: Check SQLite for fundamental metrics
    cached_df = db.load_stock_cache(tickers=active_tickers)
    cached_tickers = set(cached_df["ticker"].tolist()) if not cached_df.empty else set()
    missing_tickers = [t for t in active_tickers if t not in cached_tickers]

    # Step 5: Automatically fetch fundamentals for newly added stocks (e.g. after index rebalance)
    if force_fundamentals or len(missing_tickers) > 0:
        tickers_to_fetch = active_tickers if force_fundamentals else missing_tickers
        logger.info("Auto-syncing fundamentals for %d index constituents...", len(tickers_to_fetch))
        fresh_fund_df = fetch_fundamentals_batch(tickers_to_fetch, max_workers=max_workers)
        if not fresh_fund_df.empty:
            fresh_fund_df["index_name"] = index_key
            db.save_stock_cache(fresh_fund_df)
            cached_df = db.load_stock_cache(tickers=active_tickers)

    # Step 6: Merge live quotes into fundamental dataset
    if not live_df.empty and not cached_df.empty:
        live_cols = [
            c for c in ["ticker", "company_name", "sector", "current_price", "change", "p_change", "volume", "fifty_two_week_high", "fifty_two_week_low", "pe_ratio", "pb_ratio"]
            if c in live_df.columns
        ]
        # Remove live-updated columns from cached_df before merging
        drop_cols = [c for c in live_cols if c != "ticker" and c in cached_df.columns]
        merged_base = cached_df.drop(columns=drop_cols, errors="ignore")
        final_df = pd.merge(merged_base, live_df[live_cols], on="ticker", how="inner")
    else:
        final_df = live_df

    metadata = {
        "index_name": index_key,
        "source": source_label,
        "latency_ms": round(latency_ms, 1),
        "count": len(final_df),
        "timestamp": time.strftime("%H:%M:%S IST")
    }

    return final_df, metadata


# ---------------------------------------------------------
# Dynamic CLI & Pipeline Wrappers
# ---------------------------------------------------------
def load_universe(universe_name: str = "nifty_50") -> List[str]:
    """
    Dynamically loads current constituent tickers for any index without manual lists.
    """
    norm_name = universe_name.lower().replace("_", " ").replace("-", " ")
    matched_key = "Nifty 50"
    for k in INDEX_REGISTRY:
        if k.lower() == norm_name or norm_name in k.lower():
            matched_key = k
            break

    # First check if SQLite has the dynamic constituents
    tickers = db.load_index_constituents(matched_key)
    if not tickers:
        df, _ = fetch_universe_data(matched_key)
        if not df.empty and "ticker" in df.columns:
            tickers = df["ticker"].tolist()

    return tickers


def fetch_universe_batch(tickers: List[str] = None, max_workers: int = 10) -> List[Dict[str, Any]]:
    """Helper for CLI runner (main.py) to fetch data dynamically."""
    if not tickers:
        tickers = load_universe("nifty_50")
    df, _ = fetch_universe_data("Nifty 50", force_fundamentals=False, max_workers=max_workers)
    if df.empty:
        df = fetch_fundamentals_batch(tickers, max_workers=max_workers)
    return df.to_dict(orient="records")


# Backward compatibility alias
INDEX_UNIVERSE = INDEX_REGISTRY