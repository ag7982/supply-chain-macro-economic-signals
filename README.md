# macro-supply-signals

[![CI](https://github.com/ag7982/supply-chain-macro-economic-signals/actions/workflows/ci.yml/badge.svg)](https://github.com/ag7982/supply-chain-macro-economic-signals/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Pull and normalise macro-economic indicators relevant to supply-chain analysis. All signals are sourced from [FRED (Federal Reserve Economic Data)](https://fred.stlouisfed.org/) and returned as clean pandas DataFrames.

## Signals

| Signal | Source | FRED series | Frequency |
|---|---|---|---|
| CPI (headline inflation) | FRED | `CPIAUCSL` | Monthly |
| PPI (producer prices) | FRED | `PPIACO` | Monthly |
| Industrial Production Index | FRED | `INDPRO` | Monthly |
| WTI crude oil price | FRED | `DCOILWTICO` | Daily |
| Brent crude oil price | FRED | `DCOILBRENTEU` | Daily |
| USD broad index (FX) | FRED | `DTWEXBGS` | Daily |

Every signal is documented in the catalog with a title, description of supply-chain relevance, units, seasonal adjustment status, domain tags, and join hints.

## Setup

**Prerequisites:** Python 3.9+

```bash
git clone https://github.com/ag7982/supply-chain-macro-economic-signals.git
cd supply-chain-macro-economic-signals
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"           # core + dev tools
pip install -e ".[dev,notebook]"  # also installs matplotlib for the quickstart notebook
```

**API key:** register for a free FRED API key at https://fred.stlouisfed.org/docs/api/api_key.html, then:

```bash
cp .env.example .env
# open .env and set FRED_API_KEY=your_key_here
```

## Usage

### Single signal — convenience functions

```python
from macro_supply_signals.signals.inflation import get_cpi

df = get_cpi(start="2020-01-01")
print(df.tail())
#         date native_series_id    value  cpi_yoy  cpi_mom  ...  retrieved_at
# 2025-12-01  CPIAUCSL  326.031   3.0023   0.2978  ...  2026-05-01 12:00:00+00:00
```

Pass `include_derived=False` to get a slim frame with only the schema columns:

```python
df = get_cpi(start="2020-01-01", include_derived=False)
# columns: date, native_series_id, value, retrieved_at, signal_id, frequency, source
```

Each function accepts optional `start`, `end` (ISO date strings), `api_key`, and `include_derived` parameters.

### Available signal functions

```python
from macro_supply_signals.signals.inflation import get_cpi
from macro_supply_signals.signals.ppi import get_ppi
from macro_supply_signals.signals.industrial import get_industrial_production
from macro_supply_signals.signals.energy import get_wti, get_brent
from macro_supply_signals.signals.fx import get_usd_index
```

### Batch pulls — `SignalClient`

`SignalClient` is the recommended entry point when pulling more than one signal. It binds the API key once and supports aligned panel output.

```python
from macro_supply_signals import SignalClient

client = SignalClient()  # reads FRED_API_KEY from environment

# Pull multiple signals — returns dict[signal_id, DataFrame]
frames = client.pull_many(
    ["inflation.cpi_headline", "energy.crude_wti"],
    start="2020-01-01",
)

# Align to month-end — returns a wide DataFrame with MultiIndex columns
panel = client.pull_many(
    ["inflation.cpi_headline", "energy.crude_wti"],
    start="2020-01-01",
    align="month_end",
)
# panel["inflation.cpi_headline"]["cpi_yoy"]  →  monthly CPI YoY series
```

No interpolation is applied — gaps remain `NaN`.

### Pull by stable signal id (registry)

All convenience functions delegate to a central catalog. You can call the same logic by id directly:

```python
from macro_supply_signals.catalog import fetch_signal, INFLATION_CPI_HEADLINE

df = fetch_signal(INFLATION_CPI_HEADLINE, start="2020-01-01")
# equivalent to get_cpi(start="2020-01-01")
```

### Inspect the catalog

```python
from macro_supply_signals.catalog import SIGNALS_BY_ID

for sid, spec in SIGNALS_BY_ID.items():
    print(spec.title, "|", spec.supply_chain_tags)
# CPI — Consumer Price Index (Headline) | ['input_costs', 'demand', 'contract_pricing']
# WTI Crude Oil Price                   | ['energy', 'transportation_cost', 'input_costs']
# ...
```

## Output schema

Every DataFrame carries these columns:

| Column | Type | Description |
|---|---|---|
| `date` | `datetime64[ns]` | Observation date (start of period for monthly; trade date for daily) |
| `signal_id` | `str` | Stable logical id, e.g. `inflation.cpi_headline` |
| `native_series_id` | `str` | Vendor series id, e.g. `CPIAUCSL` |
| `value` | `float` | Primary level for the signal |
| `frequency` | `str` | `D` (daily) or `M` (monthly) |
| `source` | `str` | Data provider — currently always `fred` |
| `retrieved_at` | `datetime64[ns, UTC]` | UTC timestamp of the fetch |

Plus derived columns per signal family (`cpi_yoy`, `cpi_mom`, `chg_1d`, `chg_30d`, …), omitted when `include_derived=False`.

## Project structure

```
macro_supply_signals/
├── __init__.py          # exports SignalClient
├── client.py            # SignalClient — pull(), pull_many(align=)
├── catalog.py           # SIGNALS_BY_ID, SignalSpec, fetch_signal(), stable id constants
├── sources/
│   └── fred.py          # FREDClient — wraps the FRED REST API
└── signals/
    ├── inflation.py     # get_cpi()
    ├── ppi.py           # get_ppi()
    ├── industrial.py    # get_industrial_production()
    ├── energy.py        # get_wti(), get_brent()
    └── fx.py            # get_usd_index()
notebooks/
└── 00_quickstart.ipynb  # end-to-end walkthrough of every public entry-point
scripts/
└── pull_cpi.py          # demo script — fetches CPI, prints summary, saves to data/cpi.csv
tests/
├── test_catalog.py      # registry and fetch_signal tests
├── test_client.py       # SignalClient integration tests
├── test_fred.py         # FREDClient unit tests
└── test_signals.py      # smoke tests for all signal functions
```

## Running tests

```bash
pytest --cov=macro_supply_signals --cov-report=term-missing
```

All tests mock the FRED HTTP layer — no API key required.

## Roadmap

- [x] CI pipeline (GitHub Actions, Python 3.9 + 3.12)
- [x] MIT license
- [x] `SignalClient` with `pull()` and `pull_many()` (#7)
- [x] Standard columns + `retrieved_at` + `include_derived`
- [ ] Baltic Dry Index (shipping) — requires scraping (#11)
- [x] PyPI publish (#5)
- [ ] Scheduled pulls / incremental updates
