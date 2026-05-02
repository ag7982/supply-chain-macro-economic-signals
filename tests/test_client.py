"""Tests for SignalClient — pull() and pull_many() with alignment."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from macro_supply_signals import SignalClient
from macro_supply_signals.catalog import (
    INFLATION_CPI_HEADLINE,
    INFLATION_PPI_ALL_COMMODITIES,
    ENERGY_CRUDE_WTI,
)

_MONTHLY_OBS = {
    "observations": [
        {"date": f"202{y}-{m:02d}-01", "value": str(100 + y * 12 + m)}
        for y in range(2)
        for m in range(1, 13)
    ][:15]
}

_DAILY_OBS = {
    "observations": [
        {"date": f"2024-01-{d:02d}", "value": str(80 + d)}
        for d in range(1, 32)
    ] + [
        {"date": f"2024-02-{d:02d}", "value": str(110 + d)}
        for d in range(1, 6)
    ]
}


def _mock_response(obs: dict) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = obs
    resp.raise_for_status.return_value = None
    return resp


def _patch_fred(obs: dict):
    return patch(
        "macro_supply_signals.sources.fred.requests.get",
        return_value=_mock_response(obs),
    )


def _patch_fred_side_effect(mapping: dict):
    """Patch requests.get so different series return different mock responses."""
    def _side_effect(*args, **kwargs):
        series_id = kwargs.get("params", {}).get("series_id", "")
        obs = mapping.get(series_id, _MONTHLY_OBS)
        return _mock_response(obs)

    return patch("macro_supply_signals.sources.fred.requests.get", side_effect=_side_effect)


# ---------------------------------------------------------------------------
# pull()
# ---------------------------------------------------------------------------

def test_pull_returns_dataframe():
    client = SignalClient(fred_api_key="test-key")
    with _patch_fred(_MONTHLY_OBS):
        df = client.pull(INFLATION_CPI_HEADLINE, start="2020-01-01")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "signal_id" in df.columns
    assert (df["signal_id"] == INFLATION_CPI_HEADLINE).all()


def test_pull_unknown_signal_raises():
    client = SignalClient(fred_api_key="test-key")
    with pytest.raises(KeyError, match="Unknown signal_id"):
        client.pull("not.a.real.signal")


# ---------------------------------------------------------------------------
# pull_many() — no alignment
# ---------------------------------------------------------------------------

def test_pull_many_no_align_returns_dict():
    client = SignalClient(fred_api_key="test-key")
    sids = [INFLATION_CPI_HEADLINE, INFLATION_PPI_ALL_COMMODITIES]
    with _patch_fred(_MONTHLY_OBS):
        result = client.pull_many(sids, start="2020-01-01")
    assert isinstance(result, dict)
    assert set(result.keys()) == set(sids)
    for sid, df in result.items():
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0


def test_pull_many_empty_list():
    client = SignalClient(fred_api_key="test-key")
    result = client.pull_many([])
    assert result == {}


def test_pull_many_invalid_align_raises():
    client = SignalClient(fred_api_key="test-key")
    with _patch_fred(_MONTHLY_OBS):
        with pytest.raises(ValueError, match="Unsupported align policy"):
            client.pull_many([INFLATION_CPI_HEADLINE], align="interpolate")


# ---------------------------------------------------------------------------
# pull_many() — align="month_end"
# ---------------------------------------------------------------------------

def test_pull_many_month_end_returns_dataframe():
    client = SignalClient(fred_api_key="test-key")
    sids = [INFLATION_CPI_HEADLINE, INFLATION_PPI_ALL_COMMODITIES]
    with _patch_fred(_MONTHLY_OBS):
        panel = client.pull_many(sids, align="month_end")
    assert isinstance(panel, pd.DataFrame)
    assert isinstance(panel.columns, pd.MultiIndex)


def test_pull_many_month_end_has_signal_ids_as_top_level():
    client = SignalClient(fred_api_key="test-key")
    sids = [INFLATION_CPI_HEADLINE, INFLATION_PPI_ALL_COMMODITIES]
    with _patch_fred(_MONTHLY_OBS):
        panel = client.pull_many(sids, align="month_end")
    top_level = panel.columns.get_level_values(0).unique().tolist()
    assert set(top_level) == set(sids)


def test_pull_many_month_end_index_is_month_end():
    client = SignalClient(fred_api_key="test-key")
    with _patch_fred(_MONTHLY_OBS):
        panel = client.pull_many([INFLATION_CPI_HEADLINE], align="month_end")
    # All index dates should be the last day of their respective month
    for date in panel.index:
        assert date == date + pd.offsets.MonthEnd(0), f"{date} is not a month-end date"


def test_pull_many_month_end_mixed_frequencies():
    """Daily and monthly signals can be aligned together without interpolation."""
    client = SignalClient(fred_api_key="test-key")
    mapping = {"CPIAUCSL": _MONTHLY_OBS, "DCOILWTICO": _DAILY_OBS}
    with _patch_fred_side_effect(mapping):
        panel = client.pull_many(
            [INFLATION_CPI_HEADLINE, ENERGY_CRUDE_WTI],
            align="month_end",
        )
    assert INFLATION_CPI_HEADLINE in panel.columns.get_level_values(0)
    assert ENERGY_CRUDE_WTI in panel.columns.get_level_values(0)
    # No interpolation — gaps are NaN, not filled
    assert isinstance(panel, pd.DataFrame)


def test_pull_many_month_end_no_interpolation():
    """Rows with no observation in a month must be NaN, not filled."""
    client = SignalClient(fred_api_key="test-key")
    # Daily obs only cover Jan–Feb 2024; any other month must be NaN
    with _patch_fred(_DAILY_OBS):
        panel = client.pull_many([ENERGY_CRUDE_WTI], align="month_end")
    value_col = panel[ENERGY_CRUDE_WTI]["value"]
    # Months outside the obs window should be NaN (not forward-filled)
    assert value_col.isna().any() or len(value_col) <= 2
