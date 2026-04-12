"""FX / currency signals sourced from FRED.

Primary series:
  DTWEXBGS — Nominal Broad U.S. Dollar Index (daily, goods & services)
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from macro_supply_signals.catalog import FX_USD_BROAD_NOMINAL, fetch_signal


def get_usd_index(
    start: Optional[str] = "2000-01-01",
    end: Optional[str] = None,
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Pull the nominal broad USD index from FRED.

    A rising value means a stronger dollar — relevant for import costs and
    commodity prices denominated in USD.

    Returns a DataFrame with columns:
      date               — observation date
      native_series_id   — "DTWEXBGS"
      value       — index level (Jan 2006=100)
      chg_1d      — 1-day % change
      chg_30d     — 30-day % change
    """
    return fetch_signal(FX_USD_BROAD_NOMINAL, start=start, end=end, api_key=api_key)
