"""Smoke tests for all signal modules (no network calls)."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from macro_supply_signals.signals.energy import get_wti, get_brent
from macro_supply_signals.signals.fx import get_usd_index
from macro_supply_signals.signals.industrial import get_industrial_production
from macro_supply_signals.signals.inflation import get_cpi
from macro_supply_signals.signals.ppi import get_ppi

# 15 monthly observations — enough to compute a valid YoY for the last 3
_MONTHLY_OBS = {
    "observations": [
        {"date": f"202{y}-{m:02d}-01", "value": str(100 + y * 12 + m)}
        for y in range(2)
        for m in range(1, 13)
    ][:15]
}

# 35 daily observations — enough for a valid 30-day rolling change
_DAILY_OBS = {
    "observations": [
        {"date": f"2024-01-{d:02d}", "value": str(80 + d)}
        for d in range(1, 32)
    ] + [
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


_SCHEMA_COLS = {"date", "signal_id", "native_series_id", "value", "frequency", "source"}

_SIGNAL_META = {
    get_cpi:                   ("inflation.cpi_headline",          "M", "CPIAUCSL"),
    get_ppi:                   ("inflation.ppi_all_commodities",   "M", "PPIACO"),
    get_industrial_production: ("activity.industrial_production",  "M", "INDPRO"),
    get_wti:                   ("energy.crude_wti",                "D", "DCOILWTICO"),
    get_brent:                 ("energy.crude_brent",              "D", "DCOILBRENTEU"),
    get_usd_index:             ("fx.usd_broad_nominal",            "D", "DTWEXBGS"),
}


@pytest.mark.parametrize("fn,obs,extra_cols", [
    (get_cpi,                   _MONTHLY_OBS, ["cpi_yoy", "cpi_mom"]),
    (get_ppi,                   _MONTHLY_OBS, ["ppi_yoy", "ppi_mom"]),
    (get_industrial_production, _MONTHLY_OBS, ["ip_yoy", "ip_mom"]),
    (get_wti,                   _DAILY_OBS,   ["chg_1d", "chg_30d"]),
    (get_brent,                 _DAILY_OBS,   ["chg_1d", "chg_30d"]),
    (get_usd_index,             _DAILY_OBS,   ["chg_1d", "chg_30d"]),
])
def test_signal_returns_expected_columns(fn, obs, extra_cols):
    with _patch(obs):
        df = fn(api_key="test-key")

    assert isinstance(df, pd.DataFrame)
    assert (_SCHEMA_COLS | set(extra_cols)).issubset(df.columns)
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert pd.api.types.is_numeric_dtype(df["value"])
    assert len(df) > 0


@pytest.mark.parametrize("fn,obs", [
    (get_cpi,                   _MONTHLY_OBS),
    (get_ppi,                   _MONTHLY_OBS),
    (get_industrial_production, _MONTHLY_OBS),
    (get_wti,                   _DAILY_OBS),
    (get_brent,                 _DAILY_OBS),
    (get_usd_index,             _DAILY_OBS),
])
def test_signal_schema_values(fn, obs):
    """Each row carries correct signal_id, frequency, source, and native_series_id."""
    expected_signal_id, expected_freq, expected_native = _SIGNAL_META[fn]
    with _patch(obs):
        df = fn(api_key="test-key")

    assert (df["signal_id"] == expected_signal_id).all()
    assert (df["frequency"] == expected_freq).all()
    assert (df["source"] == "fred").all()
    assert (df["native_series_id"] == expected_native).all()
