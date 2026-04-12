"""Tests for the central signal registry (no network calls)."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from macro_supply_signals.catalog import (
    ACTIVITY_INDUSTRIAL_PRODUCTION,
    ENERGY_CRUDE_BRENT,
    ENERGY_CRUDE_WTI,
    FX_USD_BROAD_NOMINAL,
    INFLATION_CPI_HEADLINE,
    INFLATION_PPI_ALL_COMMODITIES,
    SIGNALS_BY_ID,
    fetch_signal,
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
    ]
    + [
        {"date": f"2024-02-{d:02d}", "value": str(110 + d)}
        for d in range(1, 6)
    ]
}


def _mock_get(obs: dict):
    resp = MagicMock()
    resp.json.return_value = obs
    resp.raise_for_status.return_value = None
    return resp


def _patch(obs: dict):
    return patch(
        "macro_supply_signals.sources.fred.requests.get",
        return_value=_mock_get(obs),
    )


EXPECTED_IDS = frozenset(
    {
        INFLATION_CPI_HEADLINE,
        INFLATION_PPI_ALL_COMMODITIES,
        ACTIVITY_INDUSTRIAL_PRODUCTION,
        ENERGY_CRUDE_WTI,
        ENERGY_CRUDE_BRENT,
        FX_USD_BROAD_NOMINAL,
    }
)


def test_signals_by_id_matches_exported_constants():
    assert set(SIGNALS_BY_ID.keys()) == EXPECTED_IDS
    for sid in EXPECTED_IDS:
        assert SIGNALS_BY_ID[sid].signal_id == sid


@pytest.mark.parametrize(
    "signal_id,native_series,frequency",
    [
        (INFLATION_CPI_HEADLINE, "CPIAUCSL", "M"),
        (INFLATION_PPI_ALL_COMMODITIES, "PPIACO", "M"),
        (ACTIVITY_INDUSTRIAL_PRODUCTION, "INDPRO", "M"),
        (ENERGY_CRUDE_WTI, "DCOILWTICO", "D"),
        (ENERGY_CRUDE_BRENT, "DCOILBRENTEU", "D"),
        (FX_USD_BROAD_NOMINAL, "DTWEXBGS", "D"),
    ],
)
def test_spec_native_series_and_frequency(signal_id, native_series, frequency):
    spec = SIGNALS_BY_ID[signal_id]
    assert spec.native_series_id == native_series
    assert spec.frequency == frequency
    assert spec.source == "fred"


def test_fetch_signal_unknown_id_raises():
    with pytest.raises(KeyError, match="Unknown signal_id"):
        fetch_signal("not.a.real.signal", api_key="test-key")


@pytest.mark.parametrize(
    "signal_id,obs,extra_cols",
    [
        (INFLATION_CPI_HEADLINE, _MONTHLY_OBS, ["cpi_yoy", "cpi_mom"]),
        (INFLATION_PPI_ALL_COMMODITIES, _MONTHLY_OBS, ["ppi_yoy", "ppi_mom"]),
        (ACTIVITY_INDUSTRIAL_PRODUCTION, _MONTHLY_OBS, ["ip_yoy", "ip_mom"]),
        (ENERGY_CRUDE_WTI, _DAILY_OBS, ["chg_1d", "chg_30d"]),
        (ENERGY_CRUDE_BRENT, _DAILY_OBS, ["chg_1d", "chg_30d"]),
        (FX_USD_BROAD_NOMINAL, _DAILY_OBS, ["chg_1d", "chg_30d"]),
    ],
)
def test_fetch_signal_returns_expected_columns(signal_id, obs, extra_cols):
    with _patch(obs):
        df = fetch_signal(signal_id, api_key="test-key")

    assert isinstance(df, pd.DataFrame)
    assert {"date", "native_series_id", "value", *extra_cols}.issubset(df.columns)
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert pd.api.types.is_numeric_dtype(df["value"])
    assert len(df) > 0
