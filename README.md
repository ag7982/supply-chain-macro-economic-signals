# macro-supply-signals

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
#         date series_id    value  cpi_yoy  cpi_mom
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

### End-to-end demo script

Fetches CPI, prints a summary, and saves to `data/cpi.csv`:

```bash
python scripts/pull_cpi.py
```

## Project structure

```
macro_supply_signals/
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
├── test_fred.py         # FREDClient unit tests
└── test_signals.py      # smoke tests for all signal functions
```

## Running tests

```bash
pytest
```

## Roadmap

- [ ] Baltic Dry Index (shipping) — requires scraping
- [ ] Combined `pull_all.py` script across all signals
- [ ] Normalised output schema across signal types
- [ ] Scheduled pulls / incremental updates
