"""FX / currency signals sourced from FRED.

Primary series:
  DTWEXBGS — Nominal Broad U.S. Dollar Index (daily, goods & services)
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from macro_supply_signals.sources.fred import FREDClient

_USD_INDEX_SERIES = "DTWEXBGS"


def get_usd_index(
    start: Optional[str] = "2000-01-01",
    end: Optional[str] = None,
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Pull the nominal broad USD index from FRED.

    A rising value means a stronger dollar — relevant for import costs and
    commodity prices denominated in USD.

    Returns a DataFrame with columns:
      date        — observation date
      series_id   — "DTWEXBGS"
      value       — index level (Jan 2006=100)
      chg_1d      — 1-day % change
      chg_30d     — 30-day % change
    """
    client = FREDClient(api_key=api_key)
    df = client.fetch_series(_USD_INDEX_SERIES, start=start, end=end)

    df = df.sort_values("date").reset_index(drop=True)
    df["chg_1d"] = df["value"].pct_change(periods=1).mul(100).round(4)
    df["chg_30d"] = df["value"].pct_change(periods=30).mul(100).round(4)

    return df
