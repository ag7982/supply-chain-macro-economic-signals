"""Central registry of curated signals: FRED series, frequency, and transforms.

Stable ``signal_id`` values match ``docs/DESIGN.md`` (e.g. ``inflation.cpi_headline``).
Use :func:`fetch_signal` for programmatic pulls; convenience ``get_*`` functions in
``macro_supply_signals.signals`` delegate here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Final, Literal, Optional

import pandas as pd

from macro_supply_signals.sources.fred import FREDClient

TransformKind = Literal["monthly_pct", "daily_pct"]

# --- Stable signal ids (public contract for fetch_signal / future batch API) ---

INFLATION_CPI_HEADLINE: Final = "inflation.cpi_headline"
INFLATION_PPI_ALL_COMMODITIES: Final = "inflation.ppi_all_commodities"
ACTIVITY_INDUSTRIAL_PRODUCTION: Final = "activity.industrial_production"
ENERGY_CRUDE_WTI: Final = "energy.crude_wti"
ENERGY_CRUDE_BRENT: Final = "energy.crude_brent"
FX_USD_BROAD_NOMINAL: Final = "fx.usd_broad_nominal"


@dataclass(frozen=True)
class SignalSpec:
    """Definition of one curated signal."""

    signal_id: str
    native_series_id: str
    source: str
    frequency: str
    transform: TransformKind
    yoy_column: Optional[str] = None
    mom_column: Optional[str] = None


SIGNALS_BY_ID: Dict[str, SignalSpec] = {
    INFLATION_CPI_HEADLINE: SignalSpec(
        signal_id=INFLATION_CPI_HEADLINE,
        native_series_id="CPIAUCSL",
        source="fred",
        frequency="M",
        transform="monthly_pct",
        yoy_column="cpi_yoy",
        mom_column="cpi_mom",
    ),
    INFLATION_PPI_ALL_COMMODITIES: SignalSpec(
        signal_id=INFLATION_PPI_ALL_COMMODITIES,
        native_series_id="PPIACO",
        source="fred",
        frequency="M",
        transform="monthly_pct",
        yoy_column="ppi_yoy",
        mom_column="ppi_mom",
    ),
    ACTIVITY_INDUSTRIAL_PRODUCTION: SignalSpec(
        signal_id=ACTIVITY_INDUSTRIAL_PRODUCTION,
        native_series_id="INDPRO",
        source="fred",
        frequency="M",
        transform="monthly_pct",
        yoy_column="ip_yoy",
        mom_column="ip_mom",
    ),
    ENERGY_CRUDE_WTI: SignalSpec(
        signal_id=ENERGY_CRUDE_WTI,
        native_series_id="DCOILWTICO",
        source="fred",
        frequency="D",
        transform="daily_pct",
    ),
    ENERGY_CRUDE_BRENT: SignalSpec(
        signal_id=ENERGY_CRUDE_BRENT,
        native_series_id="DCOILBRENTEU",
        source="fred",
        frequency="D",
        transform="daily_pct",
    ),
    FX_USD_BROAD_NOMINAL: SignalSpec(
        signal_id=FX_USD_BROAD_NOMINAL,
        native_series_id="DTWEXBGS",
        source="fred",
        frequency="D",
        transform="daily_pct",
    ),
}


def _apply_transforms(spec: SignalSpec, df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("date").reset_index(drop=True)
    if spec.transform == "monthly_pct":
        if spec.yoy_column is None or spec.mom_column is None:
            raise ValueError(f"monthly_pct signal {spec.signal_id!r} needs yoy_column and mom_column")
        df[spec.yoy_column] = df["value"].pct_change(periods=12).mul(100).round(4)
        df[spec.mom_column] = df["value"].pct_change(periods=1).mul(100).round(4)
    elif spec.transform == "daily_pct":
        df["chg_1d"] = df["value"].pct_change(periods=1).mul(100).round(4)
        df["chg_30d"] = df["value"].pct_change(periods=30).mul(100).round(4)
    else:
        raise ValueError(f"Unknown transform: {spec.transform!r}")
    return df


def fetch_signal(
    signal_id: str,
    start: Optional[str] = "2000-01-01",
    end: Optional[str] = None,
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Pull one signal by logical id and return the same DataFrame shape as the matching ``get_*``.

    Raises:
        KeyError: If ``signal_id`` is not in :data:`SIGNALS_BY_ID`.
        NotImplementedError: If the source is not implemented (non-FRED).
    """
    try:
        spec = SIGNALS_BY_ID[signal_id]
    except KeyError as err:
        raise KeyError(f"Unknown signal_id: {signal_id!r}") from err

    if spec.source != "fred":
        raise NotImplementedError(f"Source {spec.source!r} is not implemented for {signal_id!r}")

    client = FREDClient(api_key=api_key)
    df = client.fetch_series(spec.native_series_id, start=start, end=end)
    return _apply_transforms(spec, df)
