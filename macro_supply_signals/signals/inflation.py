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

from macro_supply_signals.catalog import INFLATION_CPI_HEADLINE, fetch_signal


def get_cpi(
    start: Optional[str] = "2000-01-01",
    end: Optional[str] = None,
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Pull CPI data and attach derived inflation rate columns.

    Returns a DataFrame with columns:
      date              — observation date
      signal_id         — "inflation.cpi_headline"
      native_series_id  — "CPIAUCSL"
      value             — raw index level
      frequency         — "M" (monthly)
      source            — "fred"
      cpi_yoy           — year-over-year % change
      cpi_mom           — month-over-month % change
    """
    return fetch_signal(INFLATION_CPI_HEADLINE, start=start, end=end, api_key=api_key)
