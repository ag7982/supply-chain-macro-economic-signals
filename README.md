# macro-supply-signals

[![CI](https://github.com/ag7982/macro-supply-signals/actions/workflows/ci.yml/badge.svg)](https://github.com/ag7982/macro-supply-signals/actions/workflows/ci.yml)
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

## Setup

**Prerequisites:** Python 3.9+

```bash
git clone https://github.com/ag7982/macro-supply-signals.git
cd macro-supply-signals
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

**API key:** register for a free FRED API key at https://fred.stlouisfed.org/docs/api/api_key.html, then:

```bash
cp .env.example .env
# open .env and set FRED_API_KEY=your_key_here
```

## Usage

### Pull a single signal

```python
from macro_supply_signals.signals.inflation import get_cpi

df = get_cpi(start="2020-01-01")
print(df.tail())
#         date native_series_id    value  cpi_yoy  cpi_mom
# 2025-03-01  CPIAUCSL  319.785   2.3820   0.0332
# 2025-04-01  CPIAUCSL  320.302   2.3254   0.1617
# ...
```

Each function accepts optional `start`, `end` (ISO date strings), and `api_key` parameters.

### Available signal functions

```python
from macro_supply_signals.signals.inflation import get_cpi
from macro_supply_signals.signals.ppi import get_ppi
from macro_supply_signals.signals.industrial import get_industrial_production
from macro_supply_signals.signals.energy import get_wti, get_brent
from macro_supply_signals.signals.fx import get_usd_index
```

### Pull by stable signal id (registry)

All convenience functions delegate to a central catalog. You can call the same logic by id (for batch tooling or a future client API):

```python
from macro_supply_signals.catalog import fetch_signal, INFLATION_CPI_HEADLINE

df = fetch_signal(INFLATION_CPI_HEADLINE, start="2020-01-01")
# equivalent to get_cpi(start="2020-01-01")
```

### End-to-end demo script

Fetches CPI, prints a summary, and saves to `data/cpi.csv`:

```bash
python scripts/pull_cpi.py
```

## Project structure

```
macro_supply_signals/
├── catalog.py           # SIGNALS_BY_ID, fetch_signal(), stable signal id constants
├── sources/
│   └── fred.py          # FREDClient — wraps the FRED REST API
└── signals/
    ├── inflation.py     # get_cpi()
    ├── ppi.py           # get_ppi()
    ├── industrial.py    # get_industrial_production()
    ├── energy.py        # get_wti(), get_brent()
    └── fx.py            # get_usd_index()
scripts/
└── pull_cpi.py          # demo pull
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

## Roadmap

- [x] CI pipeline (GitHub Actions, Python 3.9 + 3.12)
- [x] MIT license
- [x] `SignalClient` with `pull()` and `pull_many()` (#7)
- [ ] Standard columns + `retrieved_at` + `include_derived` (#6) — in progress
- [ ] Baltic Dry Index (shipping) — requires scraping (#11)
- [ ] Combined `pull_all.py` script across all signals (#9)
- [ ] PyPI publish (#5)
- [ ] Scheduled pulls / incremental updates
