"""Unit tests for the FRED connector (no network calls)."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from macro_supply_signals.sources.fred import FREDClient


MOCK_OBSERVATIONS = {
    "observations": [
        {"date": "2024-01-01", "value": "310.326"},
        {"date": "2024-02-01", "value": "311.054"},
        {"date": "2024-03-01", "value": "."},  # FRED missing value
        {"date": "2024-04-01", "value": "312.228"},
    ]
}


def test_fred_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    with pytest.raises(ValueError, match="FRED_API_KEY"):
        FREDClient()


def test_fetch_series_returns_clean_dataframe():
    client = FREDClient(api_key="test-key")

    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_OBSERVATIONS
    mock_resp.raise_for_status.return_value = None

    with patch("macro_supply_signals.sources.fred.requests.get", return_value=mock_resp):
        df = client.fetch_series("CPIAUCSL")

    # Missing "." row should be dropped
    assert len(df) == 3
    assert list(df.columns) == ["date", "series_id", "value"]
    assert df["series_id"].unique()[0] == "CPIAUCSL"
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert pd.api.types.is_float_dtype(df["value"])
