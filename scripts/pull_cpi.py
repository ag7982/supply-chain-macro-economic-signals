"""Quick end-to-end demo: pull CPI from FRED and print a summary.

Usage:
    python scripts/pull_cpi.py

Requires FRED_API_KEY in .env (or environment).
"""

from macro_supply_signals.signals.inflation import get_cpi


def main() -> None:
    print("Fetching CPI (CPIAUCSL) from FRED...")
    df = get_cpi(start="2000-01-01")

    print(f"\nRows: {len(df)}, Date range: {df['date'].min().date()} → {df['date'].max().date()}")
    print("\nLatest 12 months:")
    print(
        df.tail(12)[["date", "value", "cpi_yoy", "cpi_mom"]]
        .rename(columns={"value": "cpi_index", "cpi_yoy": "yoy_%", "cpi_mom": "mom_%"})
        .to_string(index=False)
    )

    out = "data/cpi.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
