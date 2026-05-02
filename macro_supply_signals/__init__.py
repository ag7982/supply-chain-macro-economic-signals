"""Macro Supply Signals — pull and normalise macro indicators for supply-chain analysis."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("macro-supply-signals")
except PackageNotFoundError:
    __version__ = "0.1.0"

from macro_supply_signals.client import SignalClient

__all__ = ["SignalClient"]
