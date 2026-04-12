# Design: macro-supply-signals

**Status:** Draft  
**Audience:** Maintainers, contributors, and users integrating macro context into supply-chain analytics  
**Version:** Aligns with package `0.1.x`; evolves with implementation

---

## 1. Problem statement

Supply-chain and operations models (demand forecasting, inventory optimization, sourcing, transportation planning) benefit from **external macro and logistics context**: input-cost pressure, industrial activity, energy and FX shocks, and freight conditions. Today, practitioners typically:

- Wire up **generic** data clients (FRED wrappers, ad-hoc APIs) and repeatedly rediscover **which** series matter and **how** to normalize them.
- Maintain **bespoke** joins across frequencies (daily oil vs monthly CPI) and inconsistent column naming.
- Lack a **single, documented** mapping from “business question” → “signal” → **provenance** and **units**.

This package exists to shrink that glue code and cognitive load—not to replace full-featured FRED SDKs, but to sit **above** them as an **opinionated signal layer** for supply-chain analytics.

---

## 2. Product thesis (what makes it unique)

| Generic FRED clients (`fredapi`, `pyfredapi`, `fedfred`, …) | **macro-supply-signals** |
| ------------------------------------------------------------ | ------------------------- |
| Expose the **entire** FRED API and series universe | Expose a **curated catalog** of signals chosen for supply-chain relevance |
| User picks series IDs and derives features | Package provides **stable IDs** (`inflation.cpi_headline`, …), **default transforms**, and **documentation of intent** |
| Schema is “whatever FRED returns” | **Normalized output contract** (see §5) across sources where feasible |
| Usually FRED-only | **Pluggable sources** (FRED first; freight, PMIs, trade stats later where licensing permits) |

**One-sentence positioning:** *A typed, documented catalog of macro and logistics **signals**—not a database browser—with pandas-native outputs and a stable schema for downstream models.*

**Non-goals (explicit):**

- Reimplementing every FRED endpoint or competing on API completeness.
- Providing proprietary forecasts or ML models (users bring models; we provide **features**).
- Guaranteeing real-time or lowest-latency market data (correctness, clarity, and reproducibility come first).

---

## 3. Design principles

1. **Signal-first API** — Callers ask for named signals (e.g. CPI headline, USD broad index), not raw vendor series IDs, unless they opt into low-level access.
2. **Provenance by default** — Every row carries enough metadata to audit: source, native series id, retrieval timestamp where applicable, frequency, units.
3. **Deterministic transforms** — YoY/MoM, log returns, and resampling rules are **versioned and tested**; breaking changes bump semver.
4. **Pandas today, tabular tomorrow** — Standard return type is `pandas.DataFrame`; optional Polars or Arrow exports can be added behind extras without changing core semantics.
5. **Thin sources, fat catalog** — Source modules fetch and parse; **catalog** maps signal → fetch spec + transforms + docs.
6. **Progressive disclosure** — Simple `get_*` functions for quick use; `SignalClient` / registry for batch pulls, caching, and CLI later.

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  User / downstream models (forecasting, features, dashboards) │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│  Public API                                                  │
│  • get_cpi(), get_ppi(), … (stable convenience functions)    │
│  • SignalClient.pull(signal_id | list, start, end, options)   │
│  • pull_panel() — aligned multi-signal DataFrame (future)    │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│  Catalog & transforms                                        │
│  • signal_id → { source, native_series, frequency,          │
│                  transforms, column_map, doc_slug }          │
│  • transform pipeline (pct_change, resample, rename)           │
└─────────────────────────────┬───────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Source: FRED │    │  Source: …    │    │  Source: …    │
│  (HTTP/API)   │    │  (future)     │    │  (future)     │
└───────────────┘    └───────────────┘    └───────────────┘
```

**Layers:**

| Layer | Responsibility |
|-------|----------------|
| **Sources** | Authentication, HTTP, parsing vendor JSON/CSV into a minimal internal table (`date`, `value`, optional native id). |
| **Catalog** | Declarative definitions: which source + native id + default date range + transforms + human-readable metadata. |
| **Transforms** | Pure functions: sort, pct_change for YoY/MoM, optional calendar alignment, column naming to standard schema. |
| **Public API** | Stable entrypoints; backward-compatible deprecations when renaming. |

**Current codebase mapping:**

- `macro_supply_signals/sources/fred.py` → **Source** (FRED).
- `macro_supply_signals/signals/*.py` → Today: **catalog + transforms** inlined per module. **Target:** converge on a shared catalog registry to avoid duplication and enable `pull_panel`.

---

## 5. Normalized output schema (target contract)

All **signal-level** functions SHOULD return a `DataFrame` with at least:

| Column | Type | Description |
|--------|------|-------------|
| `date` | `datetime64[ns]` | Observation period (start of period for monthly; trade date for daily). |
| `signal_id` | `string` | Stable logical id, e.g. `inflation.cpi_headline`. |
| `value` | `float` | Primary level or agreed-upon canonical value for that signal. |
| `frequency` | `string` | `D`, `W`, `M`, `Q`, `A` (pandas-style or ISO-like enum). |
| `source` | `string` | e.g. `fred`. |
| `native_series_id` | `string` | e.g. `CPIAUCSL`. |
| `retrieved_at` | `datetime64[ns]` (optional) | UTC time of fetch; useful for reproducibility. |

**Derived columns** (feature flags):

- Named consistently per **family**: e.g. `*_yoy`, `*_mom` for monthly index levels; `chg_1d`, `chg_30d` for daily series.
- Documented in catalog per signal; optional `include_derived: bool` on pull API.

**Migration from 0.1.x:** Existing columns `series_id` align with `native_series_id`; add `signal_id` and `frequency` as the package matures. Deprecate `series_id` only in a minor/major release with a changelog.

---

## 6. Signal catalog (identifier scheme)

Use **dot-separated** logical ids, grouped by domain:

- `inflation.cpi_headline` — CPI AUCSL + YoY/MoM.
- `inflation.ppi_all_commodities` — PPIACO + YoY/MoM.
- `activity.industrial_production` — INDPRO + YoY/MoM.
- `energy.crude_wti`, `energy.crude_brent` — Daily levels + short-horizon returns.
- `fx.usd_broad_nominal` — DTWEXBGS + short-horizon returns.

**Future examples** (subject to data rights and implementation):

- `logistics.baltic_dry` — Dry bulk freight proxy.
- `logistics.container_spot_index` — If a licensed or scrapable source is defined.
- `surveys.ism_manufacturing_pmi` — If sourced reliably.

Each catalog entry SHOULD define:

- `signal_id`, `title`, `description` (1–3 sentences: **why** it matters for supply chain).
- `supply_chain_tags`: e.g. `input_costs`, `capacity`, `trade_exposure`, `energy`, `freight`.
- `source`, `native_series_id`, `frequency`, `units`, `seasonal_adjustment`.
- `transforms`: ordered list (e.g. `sort`, `pct_change_12`, `pct_change_1`).
- `downstream_join_hints`: e.g. “safe to monthly-align to month-end; daily series use as-of merge.”

---

## 7. Public API design

### 7.1 Convenience functions (stable, keep)

Retain module-level functions for discoverability and backward compatibility:

```python
from macro_supply_signals.signals.inflation import get_cpi
```

Signature pattern:

`get_<signal>(start=None, end=None, api_key=None, **options) -> pd.DataFrame`

### 7.2 Registry / client (introduce as package matures)

```python
from macro_supply_signals import SignalClient

client = SignalClient(fred_api_key="...")
df = client.pull("inflation.cpi_headline", start="2020-01-01")
panel = client.pull_many(
    ["inflation.cpi_headline", "energy.crude_wti"],
    start="2020-01-01",
    align="month_end",  # optional resampling policy
)
```

**Alignment policies** (future): `asof`, `month_end`, `interpolate` — each documented with statistical caveats; default to **no** implicit interpolation to avoid silent fiction.

### 7.3 Configuration

- Environment: `FRED_API_KEY` (current behavior).
- Optional config object: timeouts, retries, user-agent string for polite scraping (if ever added).

---

## 8. Dependencies strategy

| Component | Recommendation |
|-----------|----------------|
| FRED access | **Short term:** keep internal `FREDClient` for minimal deps and full control. **Medium term:** optional dependency on `fredapi` or `pyfredapi` behind `[fred]` extra if maintenance cost dominates. |
| HTTP | `requests` is fine; `httpx` if async or HTTP/2 is needed later. |
| Data | `pandas` required; `polars` optional extra later. |

---

## 9. Quality, testing, and releases

- **Unit tests:** Mock HTTP for FRED; assert transform math on fixed fixtures.
- **Integration tests (optional):** Marked `pytest -m fred_live`, require `FRED_API_KEY`, run in CI only when secret available.
- **Versioning:** Semantic versioning; catalog additions are **minor**; breaking column renames or signal_id changes are **major** (or deprecated for one minor).
- **Documentation:** Each signal has a short docstring + longer prose in docs or auto-generated catalog page from YAML/JSON registry.

---

## 10. Phased roadmap (implementation order)

| Phase | Outcome |
|-------|---------|
| **P0 — Schema & catalog skeleton** | Introduce `signal_id`, `frequency`, `source` on outputs; central registry (dict or YAML) backing existing `get_*` functions without breaking column sets yet. |
| **P1 — Panel pull** | `pull_many` + documented default alignment (e.g. monthly backbone + daily as-of). |
| **P2 — Non-FRED signals** | One high-value logistics or survey signal with clear licensing; proves multi-source architecture. |
| **P3 — Ergonomics** | Caching (disk/memory), CLI `macro-supply-signals pull …`, optional Parquet export. |
| **P4 — Ecosystem** | Optional Polars; type hints for return protocols; Jupyter examples for “features for demand forecasting.” |

---

## 11. Open decisions (to resolve in implementation)

1. **Catalog format:** In-code dict vs `signals.yaml` checked into repo (easier for non-Python contributors).
2. **Time zone:** All `date` as timezone-naive UTC vs explicit `UTC`; document FRED’s convention.
3. **Revision handling:** Whether to expose ALFRED/vintage-aware pulls for backtesting (high value for ML; scope increase).
4. **Scraping:** Prefer official APIs and licensed feeds; any scraping needs legal review and robust failure modes.

---

## 12. Summary

**macro-supply-signals** should win on **curation, schema, and supply-chain semantics**, not on being the thinnest FRED wrapper. The unique promise is: *install one package, call stable signal names, get documented, join-ready features with provenance*—with room to grow into a true multi-source panel for operational and forecasting models.
