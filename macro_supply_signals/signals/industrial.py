"""Industrial production signals sourced from FRED.

Primary series:
  INDPRO — Industrial Production Index (monthly, seasonally adjusted, 2017=100)
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from macro_supply_signals.sources.fred import FREDClient

_IP_SERIES = "INDPRO"


def get_industrial_production(
    start: Optional[str] = "2000-01-01",
    end: Optional[str] = None,
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Pull Industrial Production Index from FRED.

    Returns a DataFrame with columns:
      date        — observation date
      series_id   — "INDPRO"
      value       — index level (2017=100)
      ip_yoy      — year-over-year % change
      ip_mom      — month-over-month % change
    """
    client = FREDClient(api_key=api_key)
    df = client.fetch_series(_IP_SERIES, start=start, end=end)

    df = df.sort_values("date").reset_index(drop=True)
    df["ip_yoy"] = df["value"].pct_change(periods=12).mul(100).round(4)
    df["ip_mom"] = df["value"].pct_change(periods=1).mul(100).round(4)

    return df
