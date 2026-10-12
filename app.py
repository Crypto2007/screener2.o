import logging
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf

import database as db
import fetcher
import quant

# Page Configuration
st.set_page_config(
    page_title="Multi-Index Quantitative Equity Screener",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

logging.basicConfig(level=logging.INFO)


def _inject_custom_theme():
    """Injects high-end Black, Charcoal Grey, and Electric Indigo styling."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Core Canvas */
        .stApp {
            background-color: #090A0F;
            color: #E2E8F0;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #10121B;
            border-right: 1px solid #1E2230;
        }

        /* Metric Cards — Dark Grey with Indigo Accent Hover */
        [data-testid="stMetric"] {
            background: linear-gradient(145deg, #131622, #0E1017);
            border: 1px solid #232738;
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        [data-testid="stMetric"]:hover {
            border-color: rgba(99, 102, 241, 0.6);
            box-shadow: 0 6px 24px rgba(99, 102, 241, 0.25);
            transform: translateY(-2px);
        }

        [data-testid="stMetricLabel"] {
            color: #94A3B8 !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            letter-spacing: 0.5px;
        }

        [data-testid="stMetricValue"] {
            color: #FFFFFF !important;
            font-size: 26px !important;
            font-weight: 700 !important;
        }

        /* Buttons — Indigo Glow */
        .stButton > button {
            background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(129, 140, 248, 0.3) !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 8px 18px !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.25) !important;
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, #818CF8 0%, #6366F1 100%) !important;
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45) !important;
            transform: translateY(-1px) !important;
        }

        /* Download Button */
        .stDownloadButton > button {
            background: #131622 !important;
            color: #818CF8 !important;
            border: 1px solid rgba(99, 102, 241, 0.4) !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }

        .stDownloadButton > button:hover {
            background: rgba(99, 102, 241, 0.15) !important;
            border-color: #818CF8 !important;
            color: #FFFFFF !important;
        }

        /* Tabs — Indigo Active Indicator */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
            border-bottom: 1px solid #1E2230;
        }

        .stTabs [data-baseweb="tab"] {
            height: 44px;
            border-radius: 8px 8px 0px 0px;
            color: #94A3B8;
            background-color: transparent;
            border: none;
            font-weight: 500;
        }

        .stTabs [aria-selected="true"] {
            color: #818CF8 !important;
            background-color: #131622 !important;
            border-bottom: 2px solid #6366F1 !important;
            font-weight: 600 !important;
        }

        /* Form Controls & Inputs */
        .stTextInput input, .stSelectbox [data-baseweb="select"] {
            background-color: #131622 !important;
            color: #E2E8F0 !important;
            border: 1px solid #232738 !important;
            border-radius: 8px !important;
        }

        /* Sliders */
        .stSlider [data-baseweb="slider"] {
            color: #6366F1 !important;
        }

        /* Hover Tooltip */
        .tooltip-container {
            position: relative;
            display: inline-flex;
            align-items: center;
            cursor: pointer;
        }

        .info-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: rgba(99, 102, 241, 0.15);
            border: 1px solid rgba(99, 102, 241, 0.5);
            color: #818CF8;
            font-size: 12px;
            font-weight: 700;
            font-family: serif;
            font-style: italic;
            transition: all 0.2s ease;
            user-select: none;
        }

        .tooltip-container:hover .info-icon {
            background: #6366F1;
            color: #FFFFFF;
            box-shadow: 0 0 10px rgba(99, 102, 241, 0.8);
            transform: scale(1.15);
        }

        .tooltip-box {
            visibility: hidden;
            opacity: 0;
            width: 275px;
            background-color: #12141F;
            color: #E2E8F0;
            text-align: left;
            border-radius: 10px;
            padding: 12px 14px;
            position: absolute;
            z-index: 999999;
            top: 26px;
            right: 0;
            font-size: 12px;
            line-height: 1.45;
            border: 1px solid rgba(99, 102, 241, 0.4);
            box-shadow: 0 10px 28px rgba(0, 0, 0, 0.7);
            transition: opacity 0.2s ease, visibility 0.2s ease, transform 0.2s ease;
            transform: translateY(-4px);
            pointer-events: none;
        }

        .tooltip-container:hover .tooltip-box {
            visibility: visible;
            opacity: 1;
            transform: translateY(0);
        }

        /* Divider */
        hr {
            border-color: #1E2230 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def _bootstrap_db() -> bool:
    """Ensure database schema and migrations are initialized."""
    return db.init_db()


def fmt_val(val: Any, decimals: int = 2, prefix: str = "", suffix: str = "", default: str = "—") -> str:
    """Safely format numbers with specified decimal places and graceful fallback."""
    if val is None or pd.isna(val) or str(val).strip() in ("", "-", "None", "nan", "NaN"):
        return default
    try:
        f_val = float(val)
        return f"{prefix}{f_val:,.{decimals}f}{suffix}"
    except (ValueError, TypeError):
        return str(val)


def fmt_pct(val: Any, decimals: int = 2, is_ratio: bool = True, signed: bool = False, default: str = "—") -> str:
    """Safely format percentage values (handling both ratios e.g. 0.15 and pre-computed pct e.g. 15.0)."""
    if val is None or pd.isna(val) or str(val).strip() in ("", "-", "None", "nan", "NaN"):
        return default
    try:
        f_val = float(val)
        if is_ratio and abs(f_val) <= 2.0:
            f_val *= 100.0
        sign = "+" if signed and f_val > 0 else ""
        return f"{sign}{f_val:,.{decimals}f}%"
    except (ValueError, TypeError):
        return str(val)


@st.cache_data(ttl=1800, show_spinner=False)
def get_stock_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Fetch and cache historical closing candles for interactive price line charts."""
    clean_sym = ticker.replace(".NS", "").replace(".BO", "")
    for suffix in [".NS", ".BO"]:
        try:
            t = yf.Ticker(f"{clean_sym}{suffix}")
            hist = t.history(period=period)
            if not hist.empty:
                hist = hist.reset_index()
                hist["Date"] = pd.to_datetime(hist["Date"]).dt.tz_localize(None)
                return hist
        except Exception:
            continue
    return pd.DataFrame()


def render_stock_price_chart(ticker: str, company_name: str, key_suffix: str = ""):
    """Renders an interactive Black, Grey, and Indigo price line chart with timeframe selector."""
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 18px; margin-bottom: 10px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="background: #6366F1; width: 4px; height: 18px; border-radius: 2px;"></div>
                <h4 style="color: #FFFFFF; margin: 0; font-size: 16px; font-weight: 700;">
                    📈 Historical Price Trend &bull; <span style="color: #818CF8;">{ticker}</span> <span style="font-size: 13px; color: #94A3B8; font-weight: 400;">({company_name})</span>
                </h4>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    labels = ["1M", "3M", "6M", "1Y", "5Y"]
    label_to_period = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}

    col_tf, col_stats = st.columns([2, 3])
    with col_tf:
        selected_label = st.radio(
            "Period",
            options=labels,
            index=3,  # Default 1Y
            horizontal=True,
            label_visibility="collapsed",
            key=f"period_radio_{ticker}_{key_suffix}"
        )

    period = label_to_period.get(selected_label, "1y")
    hist_df = get_stock_price_history(ticker, period=period)

    if hist_df.empty:
        st.info(f"Price chart data currently loading or unavailable for {ticker}.")
        return

    start_price = float(hist_df.iloc[0]["Close"])
    end_price = float(hist_df.iloc[-1]["Close"])
    period_return = ((end_price - start_price) / start_price) * 100.0 if start_price else 0.0
    period_high = float(hist_df["High"].max())
    period_low = float(hist_df["Low"].min())
    ret_color = "#10B981" if period_return >= 0 else "#F43F5E"

    with col_stats:
        st.markdown(
            f"""
            <div style="display: flex; gap: 16px; justify-content: flex-end; align-items: center; font-size: 13px; color: #94A3B8;">
                <div>Latest: <b style="color: #FFFFFF;">₹{end_price:,.2f}</b></div>
                <div>{selected_label} Return: <b style="color: {ret_color};">{period_return:+.2f}%</b></div>
                <div>Range: <b style="color: #CBD5E1;">₹{period_low:,.2f} — ₹{period_high:,.2f}</b></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Indigo Line Graph with Gradient Shadow
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist_df["Date"],
        y=hist_df["Close"],
        mode="lines",
        name=ticker,
        line=dict(color="#6366F1", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(99, 102, 241, 0.12)",
        hovertemplate="<b>Date:</b> %{x|%b %d, %Y}<br><b>Price:</b> ₹%{y:,.2f}<extra></extra>"
    ))

    fig.update_layout(
        height=320,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="#10121B",
        plot_bgcolor="#10121B",
        font=dict(color="#E2E8F0"),
        xaxis=dict(
            gridcolor="#1E2230",
            zerolinecolor="#2D3247",
            showgrid=True,
            showline=False,
        ),
        yaxis=dict(
            gridcolor="#1E2230",
            zerolinecolor="#2D3247",
            showgrid=True,
            side="right",
            tickprefix="₹",
            tickformat=",.0f"
        ),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)


def load_data_and_score(
    index_key: str,
    val_weight: float,
    qual_weight: float,
    gro_weight: float,
    force_fundamentals: bool = False
) -> pd.DataFrame:
    """Fetches market data, merges live quotes, and applies quant factor scoring."""
    df, meta = fetcher.fetch_universe_data(
        index_key=index_key,
        force_fundamentals=force_fundamentals
    )
    st.session_state["feed_meta"] = meta

    if df.empty:
        return df

    weights = {"value": val_weight, "quality": qual_weight, "growth": gro_weight}
    scored_df = quant.calculate_quant_scores(df, weights)
    return scored_df


def main():
    _bootstrap_db()
    _inject_custom_theme()

    # Sidebar: Index Universe Selection & Factor Weights
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <div style="background: #6366F1; width: 4px; height: 24px; border-radius: 2px;"></div>
            <h2 style="color: #FFFFFF; margin: 0; font-size: 20px; font-weight: 700;">Market Universe</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    available_indices = list(fetcher.INDEX_REGISTRY.keys())
    selected_index = st.sidebar.selectbox(
        "📌 Select Index",
        options=available_indices,
        index=0,
        help="Dynamic constituents tracked straight from exchange feeds"
    )

    index_info = fetcher.INDEX_REGISTRY[selected_index]
    st.sidebar.caption(f"_{index_info['description']}_")

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="background: #6366F1; width: 4px; height: 20px; border-radius: 2px;"></div>
                <h3 style="color: #FFFFFF; margin: 0; font-size: 16px; font-weight: 600;">Factor Model Weights</h3>
            </div>
            <div class="tooltip-container">
                <span class="info-icon" title="Hover to view factor explanations">i</span>
                <div class="tooltip-box">
                    <div style="font-weight: 700; color: #818CF8; margin-bottom: 8px; font-size: 13px;">⚖️ Multi-Factor Model Guide</div>
                    <div style="margin-bottom: 8px;">
                        <b style="color: #FFFFFF;">💎 Value Weight:</b><br/>
                        Emphasizes low P/E, low P/B, and high Free Cash Flow Yield to find bargains and undervalued stocks.
                    </div>
                    <div style="margin-bottom: 8px;">
                        <b style="color: #FFFFFF;">🛡️ Quality Weight:</b><br/>
                        Favors strong balance sheets with high Return on Equity (ROE), fat operating margins, and low debt-to-equity leverage.
                    </div>
                    <div>
                        <b style="color: #FFFFFF;">🚀 Growth Weight:</b><br/>
                        Rewards fast-expanding companies with accelerating revenue and earnings per share (EPS) growth.
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    value_w = st.sidebar.slider(
        "Value Weight (PE, PB, FCF Yield)",
        0.0, 1.0, 0.35, 0.05,
        help="Valuation Factor: Higher weight ranks cheaper stocks higher based on low P/E, low P/B, and high Free Cash Flow Yield."
    )
    quality_w = st.sidebar.slider(
        "Quality Weight (ROE, Margins, Debt)",
        0.0, 1.0, 0.35, 0.05,
        help="Quality Factor: Higher weight rewards high Return on Equity (ROE), operating profitability, and low debt leverage."
    )
    growth_w = st.sidebar.slider(
        "Growth Weight (Rev & EPS Growth)",
        0.0, 1.0, 0.30, 0.05,
        help="Growth Factor: Higher weight rewards rapid year-over-year revenue expansion and earnings momentum."
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <div style="background: #6366F1; width: 4px; height: 20px; border-radius: 2px;"></div>
            <h3 style="color: #FFFFFF; margin: 0; font-size: 16px; font-weight: 600;">Live Feed Controls</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_btn1, col_btn2 = st.sidebar.columns(2)
    with col_btn1:
        quick_refresh = st.button("⚡ Live Price", help="Sub-second tick update via official exchange API (<400ms)")
    with col_btn2:
        full_refresh = st.button("🔄 Full Sync", help="Deep re-fetch of quarterly balance sheets + live prices")

    # Determine fetch strategy
    force_fundamentals = full_refresh

    # Load data
    with st.spinner(f"Loading {selected_index} live data..."):
        data = load_data_and_score(
            selected_index,
            value_w,
            quality_w,
            growth_w,
            force_fundamentals=force_fundamentals
        )

    # Header Section
    meta = st.session_state.get("feed_meta", {})
    latency = meta.get("latency_ms", 0.0)
    source_name = meta.get("source", "Direct Feed")
    ts = meta.get("timestamp", "")

    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown(
            f"""
            <div style="margin-bottom: 6px;">
                <h1 style="color: #FFFFFF; font-size: 32px; font-weight: 800; margin: 0; letter-spacing: -0.5px;">
                    {selected_index} <span style="color: #818CF8;">Quantitative Screener</span>
                </h1>
                <p style="color: #94A3B8; font-size: 14px; margin-top: 4px;">
                    Multi-Factor Ranking Engine &bull; Valuation &bull; Quality &bull; Momentum Growth
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with header_col2:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(18, 20, 29, 0.8)); border: 1px solid rgba(99, 102, 241, 0.4); border-radius: 12px; padding: 12px 16px; text-align: center; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);">
                <div style="display: flex; align-items: center; justify-content: center; gap: 6px;">
                    <div style="width: 8px; height: 8px; background: #6366F1; border-radius: 50%; box-shadow: 0 0 8px #6366F1;"></div>
                    <span style="color: #818CF8; font-weight: 700; font-size: 13px; letter-spacing: 0.5px;">ULTRA-FAST FEED</span>
                </div>
                <div style="margin-top: 4px; font-size: 12px; color: #CBD5E1;">Source: <b style="color: #FFFFFF;">{source_name}</b></div>
                <div style="font-size: 12px; color: #94A3B8;">Latency: <b style="color: #818CF8;">{latency} ms</b> &bull; {ts}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    if data.empty:
        st.warning(f"No market data available for {selected_index}. Click '⚡ Live Price' or '🔄 Full Sync' in the sidebar.")
        return

    # Top KPI Metrics Cards
    st.markdown("### 🏆 Top Quant Ranked Leaderboard")
    top_picks = data.head(3)
    kpi_cols = st.columns(4)

    # 3 Top Quant picks
    for idx, (_, row) in enumerate(top_picks.iterrows()):
        with kpi_cols[idx]:
            p_chg = row.get("p_change", 0.0) or 0.0
            delta_str = f"{p_chg:+.2f}%" if pd.notnull(p_chg) else "0.0%"
            st.metric(
                label=f"#{row['rank']} {row['ticker']}",
                value=f"₹{row.get('current_price', 0.0):,.2f}" if pd.notnull(row.get('current_price')) else "N/A",
                delta=delta_str
            )
            st.caption(f"{row.get('company_name', row['ticker'])} | **{row['overall_percentile']:.1f} Score**")

    # 4th Card: Top Gainer in the index today
    with kpi_cols[3]:
        valid_gainers = data[data["p_change"].notnull()] if "p_change" in data.columns else pd.DataFrame()
        if not valid_gainers.empty:
            top_gainer = valid_gainers.sort_values(by="p_change", ascending=False).iloc[0]
            st.metric(
                label=f"🚀 Top Gainer: {top_gainer['ticker']}",
                value=f"₹{top_gainer.get('current_price', 0.0):,.2f}",
                delta=f"{top_gainer.get('p_change', 0.0):+.2f}% Today"
            )
            st.caption(f"{top_gainer.get('sector', 'N/A')}")
        else:
            st.metric(label="Index Constituents", value=f"{len(data)} Stocks")
            st.caption(f"Universe: {selected_index}")

    st.markdown("---")

    # Main Visual Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Screener Table", "🎯 Factor Scatter Matrix", "🔍 Stock Deep-Dive"])

    with tab1:
        st.subheader(f"All {len(data)} Constituents — Factor Ranking")

        filter_col1, filter_col2 = st.columns([1, 2])
        with filter_col1:
            sectors = ["All"] + sorted(list(data["sector"].dropna().unique()))
            selected_sector = st.selectbox("Filter by Sector", sectors)
        with filter_col2:
            search_query = st.text_input("🔍 Search by Ticker or Name", "")

        filtered_df = data.copy()
        if selected_sector != "All":
            filtered_df = filtered_df[filtered_df["sector"] == selected_sector]
        if search_query:
            q = search_query.strip().upper()
            filtered_df = filtered_df[
                filtered_df["ticker"].str.upper().str.contains(q, na=False) |
                filtered_df["company_name"].astype(str).str.upper().str.contains(q, na=False)
            ]

        # Target display columns
        display_cols = [
            "rank", "ticker", "company_name", "sector", "current_price",
            "p_change", "overall_percentile", "value_score", "quality_score",
            "growth_score", "pe_ratio", "pb_ratio", "roe", "fifty_two_week_high", "volume"
        ]
        available_cols = [c for c in display_cols if c in filtered_df.columns]

        # Prepare cleanly typed dataframe for styling
        table_df = filtered_df[available_cols].copy()
        numeric_targets = [
            "current_price", "p_change", "overall_percentile", "value_score",
            "quality_score", "growth_score", "pe_ratio", "pb_ratio", "roe",
            "fifty_two_week_high", "volume"
        ]
        for col in numeric_targets:
            if col in table_df.columns:
                table_df[col] = pd.to_numeric(table_df[col], errors="coerce")

        # Format mappings
        fmt_dict = {
            "current_price": "₹{:,.2f}",
            "p_change": "{:+.2f}%",
            "overall_percentile": "{:.1f}%",
            "value_score": "{:+.2f}",
            "quality_score": "{:+.2f}",
            "growth_score": "{:+.2f}",
            "pe_ratio": "{:.2f}",
            "pb_ratio": "{:.2f}",
            "roe": "{:.2%}",
            "fifty_two_week_high": "₹{:,.2f}",
            "volume": "{:,.0f}"
        }
        active_fmt = {k: v for k, v in fmt_dict.items() if k in available_cols}

        st.markdown(
            """
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <span style="color: #94A3B8; font-size: 13px;">💡 <b>Click any row</b> in the table below to inspect its interactive price chart:</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        clicked_ticker = None
        try:
            event = st.dataframe(
                table_df.style.format(active_fmt, na_rep="—"),
                use_container_width=True,
                height=360,
                on_select="rerun",
                selection_mode="single-row",
                key="screener_interactive_table"
            )
            if event and hasattr(event, "selection") and event.selection:
                rows = event.selection.get("rows", [])
                if rows and len(rows) > 0 and rows[0] < len(table_df):
                    clicked_ticker = table_df.iloc[rows[0]]["ticker"]
        except Exception:
            st.dataframe(
                table_df.style.format(active_fmt, na_rep="—"),
                use_container_width=True,
                height=360
            )

        if clicked_ticker:
            st.session_state["selected_table_ticker"] = clicked_ticker

        active_ticker = st.session_state.get(
            "selected_table_ticker",
            table_df.iloc[0]["ticker"] if not table_df.empty else None
        )

        csv = table_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Screener Data (CSV)",
            data=csv,
            file_name=f"{selected_index.lower().replace(' ', '_')}_screener.csv",
            mime="text/csv",
        )

        # Render Price Line Graph for Clicked Stock
        if active_ticker:
            active_info = data[data["ticker"] == active_ticker]
            c_name = active_info.iloc[0]["company_name"] if not active_info.empty else active_ticker
            render_stock_price_chart(active_ticker, c_name, key_suffix="tab1")

    with tab2:
        st.subheader("Value vs Quality Factor Matrix")
        st.caption("Identify undervalued, high-quality leaders (Upper-Right quadrant indicates ideal quant opportunities).")

        fig = px.scatter(
            data,
            x="value_score",
            y="quality_score",
            size="overall_percentile",
            color="sector",
            hover_name="ticker",
            text="ticker",
            labels={
                "value_score": "Value Score (Z-Score)",
                "quality_score": "Quality Score (Z-Score)"
            },
            title=f"{selected_index} Factor Distribution (Bubble Size = Overall Rank Percentile)"
        )
        fig.update_traces(textposition="top center")
        fig.update_layout(
            height=550,
            paper_bgcolor="#10121B",
            plot_bgcolor="#10121B",
            font=dict(color="#E2E8F0"),
            title_font=dict(color="#818CF8", size=16),
            xaxis=dict(gridcolor="#1E2230", zerolinecolor="#2D3247"),
            yaxis=dict(gridcolor="#1E2230", zerolinecolor="#2D3247"),
            colorway=["#6366F1", "#818CF8", "#A5B4FC", "#38BDF8", "#34D399", "#F472B6", "#FBBF24"]
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Constituent Deep-Dive Analysis")
        selected_ticker = st.selectbox("Select a Company", data["ticker"].unique())
        stock_row = data[data["ticker"] == selected_ticker].iloc[0]

        d_col1, d_col2, d_col3 = st.columns(3)

        with d_col1:
            curr_p = stock_row.get('current_price')
            p_chg = stock_row.get('p_change', 0.0) or 0.0
            st.markdown(
                f"""
                <div style="background: #131622; border: 1px solid #232738; border-radius: 12px; padding: 20px;">
                    <div style="color: #818CF8; font-weight: 700; font-size: 14px;">PROFILE & LIVE PRICING</div>
                    <h2 style="color: #FFFFFF; margin: 8px 0 4px 0; font-size: 22px;">{stock_row['company_name']}</h2>
                    <div style="color: #94A3B8; font-size: 13px; margin-bottom: 12px;">Ticker: <b style="color: #E2E8F0;">{stock_row['ticker']}</b> &bull; Sector: {stock_row.get('sector', 'N/A')}</div>
                    <div style="font-size: 28px; font-weight: 800; color: #FFFFFF;">
                        ₹{fmt_val(curr_p, 2)}
                        <span style="font-size: 16px; color: {'#10B981' if p_chg >= 0 else '#F43F5E'}; font-weight: 600;">
                            ({fmt_pct(p_chg, 2, is_ratio=False, signed=True)})
                        </span>
                    </div>
                    <hr style="border-color: #1E2230; margin: 14px 0;"/>
                    <div style="color: #94A3B8; font-size: 13px;"><b>Volume:</b> {fmt_val(stock_row.get('volume'), 0)}</div>
                    <div style="color: #94A3B8; font-size: 13px;"><b>52W Range:</b> ₹{fmt_val(stock_row.get('fifty_two_week_low'), 2)} — ₹{fmt_val(stock_row.get('fifty_two_week_high'), 2)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with d_col2:
            st.markdown(
                f"""
                <div style="background: #131622; border: 1px solid #232738; border-radius: 12px; padding: 20px;">
                    <div style="color: #818CF8; font-weight: 700; font-size: 14px;">VALUATION & FUNDAMENTALS</div>
                    <div style="margin-top: 14px; display: flex; flex-direction: column; gap: 8px; font-size: 14px;">
                        <div style="display: flex; justify-content: space-between;"><span style="color: #94A3B8;">P/E Ratio</span><b style="color: #FFFFFF;">{fmt_val(stock_row.get('pe_ratio'), 2)}</b></div>
                        <div style="display: flex; justify-content: space-between;"><span style="color: #94A3B8;">P/B Ratio</span><b style="color: #FFFFFF;">{fmt_val(stock_row.get('pb_ratio'), 2)}</b></div>
                        <div style="display: flex; justify-content: space-between;"><span style="color: #94A3B8;">ROE</span><b style="color: #FFFFFF;">{fmt_pct(stock_row.get('roe'), 2)}</b></div>
                        <div style="display: flex; justify-content: space-between;"><span style="color: #94A3B8;">Operating Margin</span><b style="color: #FFFFFF;">{fmt_pct(stock_row.get('operating_margin'), 2)}</b></div>
                        <div style="display: flex; justify-content: space-between;"><span style="color: #94A3B8;">Debt to Equity</span><b style="color: #FFFFFF;">{fmt_val(stock_row.get('debt_to_equity'), 2)}</b></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with d_col3:
            st.markdown(
                f"""
                <div style="background: #131622; border: 1px solid #232738; border-radius: 12px; padding: 20px;">
                    <div style="color: #818CF8; font-weight: 700; font-size: 14px;">QUANT FACTOR PROFILE</div>
                    <div style="margin-top: 8px; font-size: 30px; font-weight: 800; color: #818CF8;">
                        {fmt_val(stock_row.get('overall_percentile', 0), 1)}% <span style="font-size: 14px; color: #94A3B8; font-weight: 500;">Percentile</span>
                    </div>
                    <div style="color: #94A3B8; font-size: 13px; margin-bottom: 12px;">Rank: <b style="color: #FFFFFF;">#{stock_row.get('rank', '—')}</b> of {len(data)}</div>
                    <hr style="border-color: #1E2230; margin: 10px 0;"/>
                    <div style="display: flex; flex-direction: column; gap: 6px; font-size: 13px;">
                        <div style="display: flex; justify-content: space-between;"><span style="color: #94A3B8;">Value Z-Score</span><b style="color: #E2E8F0;">{fmt_val(stock_row.get('value_score', 0), 2)}</b></div>
                        <div style="display: flex; justify-content: space-between;"><span style="color: #94A3B8;">Quality Z-Score</span><b style="color: #E2E8F0;">{fmt_val(stock_row.get('quality_score', 0), 2)}</b></div>
                        <div style="display: flex; justify-content: space-between;"><span style="color: #94A3B8;">Growth Z-Score</span><b style="color: #E2E8F0;">{fmt_val(stock_row.get('growth_score', 0), 2)}</b></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Historical Price Line Chart for Selected Stock in Deep-Dive
        render_stock_price_chart(selected_ticker, stock_row["company_name"], key_suffix="tab3")


if __name__ == "__main__":
    main()