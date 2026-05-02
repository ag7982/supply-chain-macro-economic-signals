"""High-level SignalClient for batch pulls and panel alignment.

Usage::

    from macro_supply_signals import SignalClient

    client = SignalClient(fred_api_key="...")

    # Single signal
    df = client.pull("inflation.cpi_headline", start="2020-01-01")

    # Multiple signals, no alignment — returns dict[signal_id, DataFrame]
    frames = client.pull_many(
        ["inflation.cpi_headline", "energy.crude_wti"],
        start="2020-01-01",
    )

    # Multiple signals, aligned to month-end — returns wide DataFrame
    panel = client.pull_many(
        ["inflation.cpi_headline", "energy.crude_wti"],
        start="2020-01-01",
        align="month_end",
    )
    # panel has a two-level column MultiIndex: (signal_id, column_name)
    # panel["inflation.cpi_headline"]["cpi_yoy"]
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union

import pandas as pd

from macro_supply_signals.catalog import fetch_signal

AlignPolicy = Literal["month_end"]


class SignalClient:
    """Pull one or many curated signals, with optional panel alignment.

    Args:
        fred_api_key: FRED API key. Falls back to the ``FRED_API_KEY`` environment variable.
    """

    def __init__(self, fred_api_key: Optional[str] = None) -> None:
        self._api_key = fred_api_key

    def pull(
        self,
        signal_id: str,
        start: Optional[str] = "2000-01-01",
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """Pull a single signal by its stable id.

        Returns the same DataFrame as the matching ``get_*`` convenience function.
        """
        return fetch_signal(signal_id, start=start, end=end, api_key=self._api_key)

    def pull_many(
        self,
        signal_ids: List[str],
        start: Optional[str] = "2000-01-01",
        end: Optional[str] = None,
        align: Optional[AlignPolicy] = None,
    ) -> Union[Dict[str, pd.DataFrame], pd.DataFrame]:
        """Pull multiple signals.

        Args:
            signal_ids: List of stable signal ids, e.g. ``["inflation.cpi_headline", "energy.crude_wti"]``.
            start: ISO date string ``"YYYY-MM-DD"``.
            end: ISO date string ``"YYYY-MM-DD"``. Defaults to today.
            align: Alignment policy for the returned panel.

                - ``None`` (default): return ``dict[signal_id, DataFrame]`` with no resampling.
                - ``"month_end"``: resample all signals to calendar month-end (last observation),
                  then return a single wide ``DataFrame`` with a two-level column
                  ``MultiIndex(signal_id, column_name)``. Daily signals are downsampled;
                  monthly signals are shifted to month-end. **No interpolation is applied.**

        Returns:
            - ``dict[str, pd.DataFrame]`` when ``align=None``.
            - ``pd.DataFrame`` with ``MultiIndex`` columns when ``align="month_end"``.

        Raises:
            ValueError: If ``align`` is not a supported policy.
        """
        if align is not None and align not in ("month_end",):
            raise ValueError(
                f"Unsupported align policy: {align!r}. Supported values: 'month_end'."
            )

        frames = {sid: self.pull(sid, start=start, end=end) for sid in signal_ids}

        if align is None:
            return frames

        return _align_month_end(frames)


def _align_month_end(frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Resample each signal to calendar month-end, return a wide MultiIndex DataFrame.

    Each signal's numeric and categorical columns are preserved under a two-level
    MultiIndex so callers can slice by signal: ``panel["inflation.cpi_headline"]``.

    No interpolation is applied; gaps remain as NaN.
    """
    parts: List[pd.DataFrame] = []
    for sid, df in frames.items():
        resampled = df.set_index("date").resample("ME").last()
        resampled.columns = pd.MultiIndex.from_product([[sid], resampled.columns])
        parts.append(resampled)

    if not parts:
        return pd.DataFrame()

    return pd.concat(parts, axis=1)
