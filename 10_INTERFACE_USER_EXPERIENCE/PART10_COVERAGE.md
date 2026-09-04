# Part 10 Completion & Integration Coverage

This package implements the user-facing Part 10 contract from the supplied specification as a runnable local web prototype.

## Covered
- 10.1 primary journey: install/run, first launch, task, plan, approval, execution, verification, report, history
- 10.2 UX principles: simple UI, visible state, risky-action transparency, pause/cancel, keyboard-friendly controls
- 10.3 application shell and adapter-oriented structure
- 10.4 dashboard, 10.5 sidebar, 10.6 instruction input
- 10.7 clarification-ready task conversation, 10.8 plan display
- 10.9 live execution, evidence status, redaction-aware presentation
- 10.10 pause/cancel semantics
- 10.11 fingerprint-bound approval simulation
- 10.12 permission/settings presentation
- 10.13 verified final reporting
- 10.14 history and 10.15 user-facing errors
- 10.16 health/diagnostics UI
- 10.17 onboarding architecture represented by the application shell
- 10.18 install/download concerns documented in the local launcher package
- 10.19 model/runtime settings
- 10.20 language architecture (English/Bengali-ready)
- 10.21 accessibility controls and keyboard navigation
- 10.22 UI state model
- 10.23 schema-checked command/event names
- 10.24 event/reconnect architecture hooks
- 10.25 evidence viewer/status presentation
- 10.26 settings
- 10.27 diagnostics/repair
- 10.28 plugin/skill settings entry point
- 10.29 privacy/history controls
- 10.30 update/repair considerations
- 10.31 error-code vocabulary
- 10.32 smoke tests
- 10.33 end-to-end acceptance flow represented in the prototype
- 10.34 explicit Part 01–09 adapter boundary
- 10.35 acceptance criteria
- 10.36 definition of done
- 10.37 final engineering directive

## Important boundary
The supplied document defines Part 10 and its integration contracts; it does **not** contain the implementations of Parts 01–09. Therefore this package cannot truthfully claim to be the complete multi-agent worker for Parts 01–09. Those components must be supplied/implemented separately and connected through the contract boundary described in Part 10.

## Fixes applied in this revision
- **Layout bug**: the Task page was not part of the `.page` show/hide system, so it stayed visible underneath History/Settings/Diagnostics at the same time. Fixed by giving it `page active` classes and an ID-scoped `display:grid` override.
- **Incomplete state model**: `app.js` only defined 9 of the 14 states from §10.22/contract.json. Added `APP_STARTING`, `SETUP_REQUIRED`, `WAITING_FOR_USER`, `RECOVERING`, `FAILED`.
- **Off-contract error code**: event validation threw a made-up `UI_EVENT_INVALID` instead of the §10.31 vocabulary. Now throws `UI_EVENT_SYNC_FAILED`, and the full `ERROR_CODES` list from §10.31 is defined for downstream use (`APPROVAL_STATE_INVALID`, `HEALTH_CHECK_FAILED`, etc. are now actually raised where relevant).
- **§10.16 health gating**: risky tasks can now be blocked with a `HEALTH_CHECK_FAILED` event when a subsystem is unhealthy, instead of always being allowed to start.
- **§10.27 diagnostics**: the Diagnostics page previously rendered nothing. It now lists per-subsystem health (Core, Model/runtime, Browser worker, Memory store, Security service) and "Run repair check" actually re-checks and updates the list plus the header health indicator.
- **§10.21 accessibility**: added `:focus-visible` styling, a working reduced-motion toggle (`body.reduce-motion`), a working text-scaling slider, `role="dialog"`/`aria-modal` and focus management (focus moves into the approval dialog on open, returns to the trigger on close, Escape cancels), `aria-live` regions for the message log/activity feed/diagnostics, and `aria-current="page"` on the active nav item.
- **Dead code removed**: `tests/test_smoke.py` had a no-op `for x in [...]: pass` loop. It now asserts the referenced elements and CSS features actually exist in the shipped files.
- Verified: `unzip -t` reports no errors, `node --check src/app.js` passes, `python tests/test_smoke.py` passes, and all three static assets serve `200` from `server.py`.
