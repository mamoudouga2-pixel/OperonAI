# LOCAL MULTI-AGENT COMPUTER WORKER — PART 01
## CORE_ORCHESTRATION_SYSTEM — COMPLETE REVISION

This package implements the Part 01 Core scope from the supplied specification:
application lifecycle, module lifecycle/registry, task lifecycle, event bus,
state persistence, health monitoring, failure handling/recovery, validation,
audit logging, and acceptance tests.

Important boundary:
- Core orchestrates and coordinates.
- Browser/desktop automation is NOT implemented here.
- Worker modules integrate through validated manifests and callbacks.

Run tests:
    python -m unittest discover -s 01_CORE/tests -v

Run demo:
    python launcher.py
