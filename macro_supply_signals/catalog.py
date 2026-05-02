"""Central registry of curated signals: FRED series, frequency, and transforms.

Stable ``signal_id`` values match ``docs/DESIGN.md`` (e.g. ``inflation.cpi_headline``).
Use :func:`fetch_signal` for programmatic pulls; convenience ``get_*`` functions in
``macro_supply_signals.signals`` delegate here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Final, List, Literal, Optional

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
    title: str = ""
    description: str = ""
    units: str = ""
    seasonal_adjustment: str = ""
    supply_chain_tags: List[str] = field(default_factory=list)
    downstream_join_hint: str = ""
    yoy_column: Optional[str] = None
    mom_column: Optional[str] = None


SIGNALS_BY_ID: Dict[str, SignalSpec] = {
    INFLATION_CPI_HEADLINE: SignalSpec(
        signal_id=INFLATION_CPI_HEADLINE,
        native_series_id="CPIAUCSL",
        source="fred",
        frequency="M",
        transform="monthly_pct",
        title="CPI — Consumer Price Index (Headline)",
        description=(
            "Measures the average change in prices paid by urban consumers for a basket of goods "
            "and services. Rising CPI signals input-cost pressure that flows through to landed costs, "
            "contract renegotiations, and consumer demand erosion."
        ),
        units="Index (1982-84=100)",
        seasonal_adjustment="Seasonally adjusted",
        supply_chain_tags=["input_costs", "demand", "contract_pricing"],
        downstream_join_hint="Monthly series; align to month-end for panel joins with daily signals.",
        yoy_column="cpi_yoy",
        mom_column="cpi_mom",
    ),
    INFLATION_PPI_ALL_COMMODITIES: SignalSpec(
        signal_id=INFLATION_PPI_ALL_COMMODITIES,
        native_series_id="PPIACO",
        source="fred",
        frequency="M",
        transform="monthly_pct",
        title="PPI — Producer Price Index (All Commodities)",
        description=(
            "Tracks average selling prices received by domestic producers for their output. "
            "PPI leads CPI and is a direct proxy for upstream input-cost pressure on manufacturers, "
            "distributors, and logistics providers."
        ),
        units="Index (1982=100)",
        seasonal_adjustment="Not seasonally adjusted",
        supply_chain_tags=["input_costs", "procurement", "manufacturing"],
        downstream_join_hint="Monthly series; align to month-end for panel joins with daily signals.",
        yoy_column="ppi_yoy",
        mom_column="ppi_mom",
    ),
    ACTIVITY_INDUSTRIAL_PRODUCTION: SignalSpec(
        signal_id=ACTIVITY_INDUSTRIAL_PRODUCTION,
        native_series_id="INDPRO",
        source="fred",
        frequency="M",
        transform="monthly_pct",
        title="Industrial Production Index",
        description=(
            "Measures real output of manufacturing, mining, and electric and gas utilities. "
            "A leading indicator of factory utilization and capacity constraints; "
            "sustained contraction signals falling demand and potential supplier fragility."
        ),
        units="Index (2017=100)",
        seasonal_adjustment="Seasonally adjusted",
        supply_chain_tags=["capacity", "manufacturing", "demand"],
        downstream_join_hint="Monthly series; align to month-end for panel joins with daily signals.",
        yoy_column="ip_yoy",
        mom_column="ip_mom",
    ),
    ENERGY_CRUDE_WTI: SignalSpec(
        signal_id=ENERGY_CRUDE_WTI,
        native_series_id="DCOILWTICO",
        source="fred",
        frequency="D",
        transform="daily_pct",
        title="WTI Crude Oil Price",
        description=(
            "West Texas Intermediate spot price — the U.S. benchmark for crude oil. "
            "Directly drives fuel surcharges, petrochemical feedstock costs, and air-freight rates; "
            "sharp moves typically reprice transportation contracts within one to two billing cycles."
        ),
        units="USD per barrel",
        seasonal_adjustment="Not seasonally adjusted",
        supply_chain_tags=["energy", "transportation_cost", "input_costs"],
        downstream_join_hint=(
            "Daily series with occasional missing values (weekends, holidays). "
            "Use as-of merge or resample to month-end last for monthly panel joins."
        ),
    ),
    ENERGY_CRUDE_BRENT: SignalSpec(
        signal_id=ENERGY_CRUDE_BRENT,
        native_series_id="DCOILBRENTEU",
        source="fred",
        frequency="D",
        transform="daily_pct",
        title="Brent Crude Oil Price",
        description=(
            "North Sea Brent spot price — the global benchmark for crude oil and a key input "
            "to bunker fuel pricing. Tracks WTI closely but diverges during regional supply shocks; "
            "most relevant for ocean-freight and European/Asian sourcing cost models."
        ),
        units="USD per barrel",
        seasonal_adjustment="Not seasonally adjusted",
        supply_chain_tags=["energy", "transportation_cost", "ocean_freight", "input_costs"],
        downstream_join_hint=(
            "Daily series with occasional missing values (weekends, holidays). "
            "Use as-of merge or resample to month-end last for monthly panel joins."
        ),
    ),
    FX_USD_BROAD_NOMINAL: SignalSpec(
        signal_id=FX_USD_BROAD_NOMINAL,
        native_series_id="DTWEXBGS",
        source="fred",
        frequency="D",
        transform="daily_pct",
        title="USD Broad Nominal Effective Exchange Rate",
        description=(
            "Trade-weighted average of the U.S. dollar against a broad basket of foreign currencies. "
            "A stronger dollar cheapens imports and raises the USD cost of exports; "
            "directly affects landed cost calculations for internationally sourced goods."
        ),
        units="Index (Jan 2006=100)",
        seasonal_adjustment="Not seasonally adjusted",
        supply_chain_tags=["trade_exposure", "fx", "import_costs", "export_competitiveness"],
        downstream_join_hint=(
            "Daily series with occasional missing values (weekends, holidays). "
            "Use as-of merge or resample to month-end last for monthly panel joins."
        ),
    ),
}


def _apply_transforms(
    spec: SignalSpec, df: pd.DataFrame, include_derived: bool = True
) -> pd.DataFrame:
    df = df.sort_values("date").reset_index(drop=True)
    if spec.transform == "monthly_pct":
        if spec.yoy_column is None or spec.mom_column is None:
            raise ValueError(f"monthly_pct signal {spec.signal_id!r} needs yoy_column and mom_column")
        if include_derived:
            df[spec.yoy_column] = df["value"].pct_change(periods=12).mul(100).round(4)
            df[spec.mom_column] = df["value"].pct_change(periods=1).mul(100).round(4)
    elif spec.transform == "daily_pct":
        if include_derived:
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
    include_derived: bool = True,
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
    df = _apply_transforms(spec, df, include_derived=include_derived)
    df["signal_id"] = spec.signal_id
    df["frequency"] = spec.frequency
    df["source"] = spec.source
    return df
