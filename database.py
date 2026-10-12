import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)
DB_FILE = Path("screener_cache.db")


def get_connection() -> sqlite3.Connection:
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_initialized() -> None:
    """Internal function to initialize database tables, schema, and column migrations."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Create stock cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_cache (
                ticker TEXT PRIMARY KEY,
                company_name TEXT,
                sector TEXT,
                industry TEXT,
                market_cap REAL,
                pe_ratio REAL,
                pb_ratio REAL,
                ps_ratio REAL,
                ev_ebitda REAL,
                roe REAL,
                roa REAL,
                gross_margin REAL,
                operating_margin REAL,
                net_margin REAL,
                revenue_growth REAL,
                earnings_growth REAL,
                free_cashflow_yield REAL,
                debt_to_equity REAL,
                current_ratio REAL,
                quick_ratio REAL,
                dividend_yield REAL,
                payout_ratio REAL,
                beta REAL,
                fifty_two_week_high REAL,
                fifty_two_week_low REAL,
                current_price REAL,
                change REAL,
                p_change REAL,
                volume REAL,
                index_name TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Column migration for existing databases missing new fields
        cursor.execute("PRAGMA table_info(stock_cache)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        new_cols = {
            "change": "REAL",
            "p_change": "REAL",
            "volume": "REAL",
            "index_name": "TEXT"
        }
        for col_name, col_type in new_cols.items():
            if col_name not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE stock_cache ADD COLUMN {col_name} {col_type}")
                except Exception as alter_err:
                    logger.debug("Column %s already present or cannot be altered: %s", col_name, alter_err)

        # Create historical snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS score_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date DATE DEFAULT CURRENT_DATE,
                ticker TEXT,
                overall_score REAL,
                value_score REAL,
                quality_score REAL,
                growth_score REAL,
                rank INTEGER,
                FOREIGN KEY (ticker) REFERENCES stock_cache (ticker)
            )
        """)

        # Dynamic index constituents table (automatically tracks rebalancing)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS index_constituents (
                index_name TEXT,
                ticker TEXT,
                company_name TEXT,
                industry TEXT,
                last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (index_name, ticker)
            )
        """)

        conn.commit()


def init_db() -> bool:
    """Public wrapper to initialize database tables and schema."""
    try:
        _ensure_initialized()
        logger.info("Database initialized successfully.")
        return True
    except Exception as err:
        logger.error("Failed to initialize database: %s", err)
        return False


def save_stock_cache(df: pd.DataFrame) -> bool:
    """Saves or updates fetched stock records in SQLite using UPSERT."""
    if df.empty:
        return False
    try:
        init_db()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(stock_cache)")
            valid_cols = [row[1] for row in cursor.fetchall()]

            # Keep only columns present in the table schema
            cols_to_insert = [c for c in df.columns if c in valid_cols]
            if not cols_to_insert:
                return False

            df_clean = df[cols_to_insert].copy()
            # Replace NaNs with None for SQLite NULL compatibility
            df_clean = df_clean.where(pd.notnull(df_clean), None)

            placeholders = ", ".join(["?"] * len(cols_to_insert))
            col_str = ", ".join(cols_to_insert)
            sql = f"INSERT OR REPLACE INTO stock_cache ({col_str}) VALUES ({placeholders})"

            cursor.executemany(sql, df_clean.values.tolist())
            conn.commit()
        return True
    except Exception as err:
        logger.error("Error saving stock cache: %s", err)
        return False


def load_stock_cache(tickers: Optional[List[str]] = None) -> pd.DataFrame:
    """Loads cached stock metrics from SQLite, optionally filtered by ticker list."""
    try:
        init_db()
        with get_connection() as conn:
            if tickers:
                placeholders = ", ".join(["?"] * len(tickers))
                query = f"SELECT * FROM stock_cache WHERE ticker IN ({placeholders})"
                return pd.read_sql_query(query, conn, params=tickers)
            return pd.read_sql_query("SELECT * FROM stock_cache", conn)
    except Exception as err:
        logger.error("Error reading stock cache: %s", err)
        return pd.DataFrame()


def save_index_constituents(index_name: str, records: List[Dict[str, Any]]) -> bool:
    """Dynamically save current rebalanced constituent stocks for an index."""
    if not records:
        return False
    try:
        init_db()
        with get_connection() as conn:
            cursor = conn.cursor()
            # Clear old membership to accurately capture index rebalancing deletions
            cursor.execute("DELETE FROM index_constituents WHERE index_name = ?", (index_name,))
            rows = [
                (
                    index_name,
                    r.get("ticker"),
                    r.get("company_name", r.get("ticker")),
                    r.get("industry") or r.get("sector") or "General"
                )
                for r in records if r.get("ticker")
            ]
            cursor.executemany("""
                INSERT OR REPLACE INTO index_constituents (index_name, ticker, company_name, industry)
                VALUES (?, ?, ?, ?)
            """, rows)
            conn.commit()
        return True
    except Exception as err:
        logger.error("Error saving index constituents for %s: %s", index_name, err)
        return False


def load_index_constituents(index_name: str) -> List[str]:
    """Retrieve cached constituent tickers for an index."""
    try:
        init_db()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ticker FROM index_constituents WHERE index_name = ? ORDER BY ticker", (index_name,))
            rows = cursor.fetchall()
            return [r[0] for r in rows]
    except Exception as err:
        logger.error("Error loading index constituents for %s: %s", index_name, err)
        return []


def save_score_snapshot(scores_df: pd.DataFrame) -> bool:
    """Records a scoring snapshot for historical trend analysis."""
    if scores_df.empty:
        return False
    try:
        init_db()
        with get_connection() as conn:
            scores_df.to_sql("score_snapshots", conn, if_exists="append", index=False)
            conn.commit()
        return True
    except Exception as err:
        logger.error("Error saving score snapshot: %s", err)
        return False