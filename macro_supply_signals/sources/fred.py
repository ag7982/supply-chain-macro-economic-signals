"""FRED (Federal Reserve Economic Data) source connector.

Wraps the FRED REST API: https://fred.stlouisfed.org/docs/api/fred/
Requires a free API key set in the FRED_API_KEY environment variable.
"""

from __future__ import annotations

import os
from datetime import timezone
from datetime import datetime
from typing import Optional

import pandas as pd
import requests

_BASE_URL = "https://api.stlouisfed.org/fred"
_DEFAULT_TIMEOUT = 30  # seconds


class FREDClient:
    """Thin client for the FRED series observations endpoint."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get("FRED_API_KEY")
        if not self.api_key:
            raise ValueError(
                "FRED_API_KEY not found. Set the environment variable or pass api_key= explicitly."
            )

    def fetch_series(
        self,
        series_id: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch observations for a FRED series and return a clean DataFrame.

        Args:
            series_id: FRED series identifier, e.g. "CPIAUCSL".
            start: ISO date string "YYYY-MM-DD". Defaults to FRED's earliest available.
            end: ISO date string "YYYY-MM-DD". Defaults to today.

        Returns:
            DataFrame with columns: date (datetime64), native_series_id (str), value (float).
            Missing / non-numeric observations (FRED uses "." as placeholder) are dropped.
        """
        params: dict = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
        }
        if start:
            params["observation_start"] = start
        if end:
            params["observation_end"] = end

        fetched_at = datetime.now(timezone.utc)

        response = requests.get(
            f"{_BASE_URL}/series/observations",
            params=params,
            timeout=_DEFAULT_TIMEOUT,
        )
        response.raise_for_status()

        payload = response.json()
        observations = payload.get("observations", [])

        df = pd.DataFrame(observations)[["date", "value"]]
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"]).reset_index(drop=True)
        df.insert(1, "native_series_id", series_id)
        df["retrieved_at"] = fetched_at

        return df

