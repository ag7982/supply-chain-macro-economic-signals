"""Energy price signals sourced from FRED.

Primary series:
  DCOILWTICO   — Crude Oil Prices: West Texas Intermediate (WTI), daily
  DCOILBRENTEU — Crude Oil Prices: Brent (Europe), daily
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from macro_supply_signals.catalog import ENERGY_CRUDE_BRENT, ENERGY_CRUDE_WTI, fetch_signal


def get_wti(
    start: Optional[str] = "2000-01-01",
    end: Optional[str] = None,
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Pull WTI crude oil daily prices.

    Returns a DataFrame with columns:
      date              — observation date
      signal_id         — "energy.crude_wti"
      native_series_id  — "DCOILWTICO"
      value             — price in USD per barrel
      frequency         — "D" (daily)
      source            — "fred"
      chg_1d            — 1-day % change
      chg_30d           — 30-day % change (approx 1 month)
    """
    return fetch_signal(ENERGY_CRUDE_WTI, start=start, end=end, api_key=api_key)


def get_brent(
    start: Optional[str] = "2000-01-01",
    end: Optional[str] = None,
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Pull Brent crude oil daily prices.

    Returns a DataFrame with columns:
      date              — observation date
      signal_id         — "energy.crude_brent"
      native_series_id  — "DCOILBRENTEU"
      value             — price in USD per barrel
      frequency         — "D" (daily)
      source            — "fred"
      chg_1d            — 1-day % change
      chg_30d           — 30-day % change
    """
    return fetch_signal(ENERGY_CRUDE_BRENT, start=start, end=end, api_key=api_key)
