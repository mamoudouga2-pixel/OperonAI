# PART 06 — DESKTOP AND FILE AGENT (fixed & completed)

Implementation of the Part 06 Master Technical Specification (Desktop/File Agent).

## What this covers vs. the spec
- Path policy (6.9): allowed/restricted roots, traversal + symlink blocking,
  and restricted subtrees are now pruned *during* recursive scans, not just
  checked at the top-level call.
- File operations (6.10–6.14): create folder, copy, move, rename — each with
  precondition/postcondition checks, overwrite protection, and an
  idempotent move helper for crash-recovery re-runs.
- Desktop session + window management (6.6, 6.16): session lifecycle,
  active-window/focused-app tracking, foreground verification before any
  input, bounded focus recovery.
- Application launch (6.15): only security-registry-approved app ids
  resolve to a trusted path; never a raw/model-supplied path.
- Mouse/keyboard control (6.17): every input action is guarded by a
  foreground/window check and supports cancellation.
- Screen observation (6.18) + evidence (6.21): capture produces a real
  SHA-256-hashed, timestamped evidence record; failures map to
  SCREEN_OBSERVATION_FAILED.
- Workflow recorder/replay (6.25–6.26): steps, JSON serialization,
  environment-precondition re-validation, and a non-idempotent-step guard.
- Recovery + loop protection (6.27–6.28): bounded retries only for
  retryable error codes, state re-checked each attempt, loop detector halts
  runaway repetition.
- Error codes / events (6.31, 6.33) centralized in `errors.py` so every
  module raises exactly the codes defined in the spec.
- Cross-platform adapter boundary (6.29): abstract `DesktopAdapter` +
  `MockAdapter` for tests; real platform adapters (e.g. pyautogui-based)
  plug in without changing anything above the boundary.

## Bugs fixed from the original submission
1. Restricted subdirectories nested under an allowed root were listed by
   `scan()` — only the top-level argument was policy-checked. Fixed by
   pruning restricted entries during the `os.walk` traversal.
2. `hashlib` was imported but never used — evidence had no real hash.
   Evidence records now carry a genuine SHA-256 of the mutated file.
3. `DesktopController` had no way to ever set `active_window` /
   `focused_application`, so window checks were permanently unusable.
   Added `set_window`, `verify_foreground`, `recover_focus`.
4. No permission/lock-error mapping — a `PermissionError` from the OS
   would crash with a raw Python traceback instead of `PERMISSION_DENIED`.
5. No source-changed / conflict re-check before mutating (6.23) — added
   fingerprint-based `_check_unchanged`.
6. `mkdir`/`rename` accepted any string as a name; a name like `"../x"`
   could reach the filesystem call before being rejected only by luck of
   path resolution. Added explicit name validation.
7. No crash-recovery path for a worker that moved a file then died before
   reporting: re-running `move()` naively would raise `FILE_NOT_FOUND`.
   Added `move_idempotent()` used by the recovery pipeline.
8. Only 13 of the 20 items in the 6.36 testing checklist had a test.
   Expanded to 32 tests covering permission denied, locked file, invalid
   path, large-directory bound, application launch, wrong-window
   prevention, input cancellation, non-idempotent replay, crash recovery,
   and verification failure.

## Running the tests
```
cd 06_DESKTOP_AGENT
python3 -m unittest tests.test_part06 -v
```
