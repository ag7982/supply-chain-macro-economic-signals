"""Inflation signals sourced from FRED.

Primary series:
  CPIAUCSL — Consumer Price Index for All Urban Consumers (monthly, seasonally adjusted)

Derived signals:
  cpi_yoy  — Year-over-year % change (headline inflation rate)
  cpi_mom  — Month-over-month % change
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from macro_supply_signals.sources.fred import FREDClient

_CPI_SERIES = "CPIAUCSL"


def get_cpi(
    start: Optional[str] = "2000-01-01",
    end: Optional[str] = None,
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Pull CPI data and attach derived inflation rate columns.

    Returns a DataFrame with columns:
      date        — observation date
      series_id   — "CPIAUCSL"
      value       — raw index level
      cpi_yoy     — year-over-year % change
      cpi_mom     — month-over-month % change
    """
    client = FREDClient(api_key=api_key)
    df = client.fetch_series(_CPI_SERIES, start=start, end=end)

    df = df.sort_values("date").reset_index(drop=True)
    df["cpi_yoy"] = df["value"].pct_change(periods=12).mul(100).round(4)
    df["cpi_mom"] = df["value"].pct_change(periods=1).mul(100).round(4)

    return df
