import numpy as np
import pandas as pd
from typing import Dict


def winsorize_series(s: pd.Series, lower_quantile: float = 0.05, upper_quantile: float = 0.95) -> pd.Series:
    """Cap extreme outliers in a series at specified quantiles."""
    s_clean = s.dropna()
    if s_clean.empty:
        return s
    q_low = s_clean.quantile(lower_quantile)
    q_high = s_clean.quantile(upper_quantile)
    return s.clip(lower=q_low, upper=q_high)


def z_score_series(s: pd.Series, invert: bool = False) -> pd.Series:
    """Calculate Z-scores for a series with optional sign inversion for 'lower is better' metrics."""
    s_clean = s.dropna()
    if len(s_clean) < 2:
        return pd.Series(0.0, index=s.index)

    std = s_clean.std()
    if std == 0 or np.isnan(std):
        z = pd.Series(0.0, index=s.index)
    else:
        z = (s - s_clean.mean()) / std

    z = z.fillna(0.0)
    return -z if invert else z


def calculate_quant_scores(
    df: pd.DataFrame,
    weights: Dict[str, float] = None,
    value_weight: float = None,
    quality_weight: float = None,
    growth_weight: float = None
) -> pd.DataFrame:
    """Compute composite factor scores (Value, Quality, Growth) and final overall Quant Rank."""
    if df.empty:
        return df

    res = df.copy()

    # Allow passing either a dictionary of weights or individual weight parameters
    if weights is None:
        weights = {
            "value": value_weight if value_weight is not None else 0.35,
            "quality": quality_weight if quality_weight is not None else 0.35,
            "growth": growth_weight if growth_weight is not None else 0.30,
        }

    # Normalize weights to sum to 1.0
    total_w = sum(weights.values()) or 1.0
    w_val = weights.get("value", 0.35) / total_w
    w_qual = weights.get("quality", 0.35) / total_w
    w_gro = weights.get("growth", 0.30) / total_w

    # Value Factor (lower metrics like PE/PB are better, higher FCF yield is better)
    pe_z = z_score_series(winsorize_series(res.get("pe_ratio", pd.Series(dtype=float))), invert=True)
    pb_z = z_score_series(winsorize_series(res.get("pb_ratio", pd.Series(dtype=float))), invert=True)
    fcf_z = z_score_series(winsorize_series(res.get("free_cashflow_yield", pd.Series(dtype=float))), invert=False)
    res["value_score"] = (pe_z + pb_z + fcf_z) / 3.0

    # Quality Factor (higher margins, ROE, lower debt are better)
    roe_z = z_score_series(winsorize_series(res.get("roe", pd.Series(dtype=float))), invert=False)
    op_m_z = z_score_series(winsorize_series(res.get("operating_margin", pd.Series(dtype=float))), invert=False)
    debt_z = z_score_series(winsorize_series(res.get("debt_to_equity", pd.Series(dtype=float))), invert=True)
    res["quality_score"] = (roe_z + op_m_z + debt_z) / 3.0

    # Growth Factor
    rev_g_z = z_score_series(winsorize_series(res.get("revenue_growth", pd.Series(dtype=float))), invert=False)
    earn_g_z = z_score_series(winsorize_series(res.get("earnings_growth", pd.Series(dtype=float))), invert=False)
    res["growth_score"] = (rev_g_z + earn_g_z) / 2.0

    # Composite Quant Score
    res["quant_score"] = (
        (res["value_score"] * w_val) +
        (res["quality_score"] * w_qual) +
        (res["growth_score"] * w_gro)
    )

    # Convert to percentile ranks (0 - 100)
    res["overall_percentile"] = (res["quant_score"].rank(pct=True) * 100).round(1)
    res["rank"] = res["quant_score"].rank(ascending=False, method="min").astype(int)

    # Round all factor Z-scores to 2 decimal places
    res["value_score"] = res["value_score"].round(2)
    res["quality_score"] = res["quality_score"].round(2)
    res["growth_score"] = res["growth_score"].round(2)
    res["quant_score"] = res["quant_score"].round(2)

    # Output aliases for CLI/terminal compatibility
    res["Rank"] = res["rank"]
    res["Symbol"] = res.get("ticker", "")
    res["Price"] = res.get("current_price", 0.0)
    res["Trailing P/E"] = res.get("pe_ratio")
    res["ROE"] = res.get("roe")
    res["Valuation Score"] = res["value_score"]
    res["Quality Score"] = res["quality_score"]
    res["Growth Score"] = res["growth_score"]
    res["Quant Score"] = res["quant_score"]

    return res.sort_values(by="rank")