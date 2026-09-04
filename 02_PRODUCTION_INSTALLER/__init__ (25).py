"""Spec §3 requires a dedicated `first_launch/` module (§7: Detect
environment → Validate installation → Start local services → Health
checks → Create user-data directories → Load safe defaults → Show
readiness).

The implementation lives in `bootstrap/first_launch.py` alongside the
other bootstrap-time state (`bootstrap_state.py`, `environment_check.py`,
`startup_recovery.py`) since they share state and are always run
together. This package is the spec-named entry point.
"""
from bootstrap.first_launch import run_first_launch

__all__ = ["run_first_launch"]
