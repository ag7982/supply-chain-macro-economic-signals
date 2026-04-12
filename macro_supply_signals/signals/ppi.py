"""Producer Price Index signals sourced from FRED.

Primary series:
  PPIACO — Producer Price Index: All Commodities (monthly, not seasonally adjusted)

PPI leads CPI — it captures upstream cost pressure before it reaches consumers,
making it useful as a leading supply-chain cost indicator.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from macro_supply_signals.sources.fred import FREDClient

_PPI_SERIES = "PPIACO"
_SIGNAL_ID = "inflation.ppi_all_commodities"
_FREQUENCY = "M"
_SOURCE = "fred"


def get_ppi(
    start: Optional[str] = "2000-01-01",
    end: Optional[str] = None,
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Pull Producer Price Index (all commodities) from FRED.

    Returns a DataFrame with columns:
      date              — observation date
      signal_id         — "inflation.ppi_all_commodities"
      native_series_id  — "PPIACO"
      value             — index level (1982=100)
      frequency         — "M" (monthly)
      source            — "fred"
      ppi_yoy           — year-over-year % change
      ppi_mom           — month-over-month % change
    """
    client = FREDClient(api_key=api_key)
    df = client.fetch_series(_PPI_SERIES, start=start, end=end)

    df = df.sort_values("date").reset_index(drop=True)
    df["signal_id"] = _SIGNAL_ID
    df["frequency"] = _FREQUENCY
    df["source"] = _SOURCE
    df["ppi_yoy"] = df["value"].pct_change(periods=12).mul(100).round(4)
    df["ppi_mom"] = df["value"].pct_change(periods=1).mul(100).round(4)

    return df
