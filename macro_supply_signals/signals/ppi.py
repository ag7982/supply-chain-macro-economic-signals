"""Producer Price Index signals sourced from FRED.

Primary series:
  PPIACO — Producer Price Index: All Commodities (monthly, not seasonally adjusted)

PPI leads CPI — it captures upstream cost pressure before it reaches consumers,
making it useful as a leading supply-chain cost indicator.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from macro_supply_signals.catalog import INFLATION_PPI_ALL_COMMODITIES, fetch_signal


def get_ppi(
    start: Optional[str] = "2000-01-01",
    end: Optional[str] = None,
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Pull Producer Price Index (all commodities) from FRED.

    Returns a DataFrame with columns:
      date               — observation date
      native_series_id   — "PPIACO"
      value       — index level (1982=100)
      ppi_yoy     — year-over-year % change
      ppi_mom     — month-over-month % change
    """
    return fetch_signal(INFLATION_PPI_ALL_COMMODITIES, start=start, end=end, api_key=api_key)
