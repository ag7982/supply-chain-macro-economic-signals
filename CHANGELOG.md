# Changelog

All notable changes to this project will be documented here.

## [0.1.0] — 2026-05-02

Initial release.

### Added
- `SignalClient` with `pull(signal_id)` and `pull_many([...], align=)` for batch pulls
- Signal catalog (`catalog.py`) with `SignalSpec` entries for CPI, PPI, Industrial Production, WTI, Brent, USD Index
- Standard output columns: `signal_id`, `frequency`, `source`, `native_series_id`, `retrieved_at`
- `include_derived` flag for optional MoM/YoY/change transforms
- FRED source connector (`FREDClient`) with mocked test suite (no API key required to run tests)
- CI pipeline (GitHub Actions, Python 3.9 + 3.12): lint with ruff, pytest with coverage
- PyPI publish workflow using OIDC trusted publisher (no stored API token)
