"""Industrial production signals sourced from FRED.

Primary series:
  INDPRO — Industrial Production Index (monthly, seasonally adjusted, 2017=100)
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from macro_supply_signals.catalog import ACTIVITY_INDUSTRIAL_PRODUCTION, fetch_signal


def get_industrial_production(
    start: Optional[str] = "2000-01-01",
    end: Optional[str] = None,
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Pull Industrial Production Index from FRED.

    Returns a DataFrame with columns:
      date               — observation date
      native_series_id   — "INDPRO"
      value       — index level (2017=100)
      ip_yoy      — year-over-year % change
      ip_mom      — month-over-month % change
    """
    return fetch_signal(ACTIVITY_INDUSTRIAL_PRODUCTION, start=start, end=end, api_key=api_key)
