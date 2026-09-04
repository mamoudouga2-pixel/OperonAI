# PART 09 — SECURITY, PERMISSION AND SAFETY SYSTEM (v1.1 — complete)
Fail-closed local security reference implementation.
All external actions must pass normalization, target/context validation, deterministic risk
classification, capability+grant+scope evaluation, approval matching where required,
execution boundary, audit/evidence recording, and post-action verification.

Status: every item in spec sections 9.26 (Testing Requirements) and 9.28 (Acceptance Criteria)
is implemented and covered by automated tests — tamper-evident audit hash chain, approval
expiry, network size/duration limits, full 9.24 event wiring (approval/credential/rate-limit/
incident events), plugin capability enforcement, and symlink-escape protection. See
CHANGELOG_PART09.md for the full fix log. 23/23 tests passing, 0 compile errors.
