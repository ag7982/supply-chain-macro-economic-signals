"""Energy price signals sourced from FRED.

Primary series:
  DCOILWTICO — Crude Oil Prices: West Texas Intermediate (WTI), daily
  DCOILBRENTEU — Crude Oil Prices: Brent (Europe), daily
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from macro_supply_signals.sources.fred import FREDClient

_WTI_SERIES = "DCOILWTICO"
_BRENT_SERIES = "DCOILBRENTEU"
_FREQUENCY = "D"
_SOURCE = "fred"


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
    client = FREDClient(api_key=api_key)
    df = client.fetch_series(_WTI_SERIES, start=start, end=end)

    df = df.sort_values("date").reset_index(drop=True)
    df["signal_id"] = "energy.crude_wti"
    df["frequency"] = _FREQUENCY
    df["source"] = _SOURCE
    df["chg_1d"] = df["value"].pct_change(periods=1).mul(100).round(4)
    df["chg_30d"] = df["value"].pct_change(periods=30).mul(100).round(4)

    return df


def get_brent(
    start: Optional[str] = "2000-01-01",
    end: Optional[str] = None,
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Pull Brent crude oil daily prices.

    Returns a DataFrame with columns:
<<<<<<< HEAD
      date               — observation date
      native_series_id   — "DCOILBRENTEU"
      value       — price in USD per barrel
      chg_1d      — 1-day % change
      chg_30d     — 30-day % change
    """
    return fetch_signal(ENERGY_CRUDE_BRENT, start=start, end=end, api_key=api_key)
=======
      date              — observation date
      signal_id         — "energy.crude_brent"
      native_series_id  — "DCOILBRENTEU"
      value             — price in USD per barrel
      frequency         — "D" (daily)
      source            — "fred"
      chg_1d            — 1-day % change
      chg_30d           — 30-day % change
    """
    client = FREDClient(api_key=api_key)
    df = client.fetch_series(_BRENT_SERIES, start=start, end=end)

    df = df.sort_values("date").reset_index(drop=True)
    df["signal_id"] = "energy.crude_brent"
    df["frequency"] = _FREQUENCY
    df["source"] = _SOURCE
    df["chg_1d"] = df["value"].pct_change(periods=1).mul(100).round(4)
    df["chg_30d"] = df["value"].pct_change(periods=30).mul(100).round(4)

    return df
>>>>>>> 355b049 (normalise all six get_* functions)
