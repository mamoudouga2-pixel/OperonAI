# Part 02 — Audit & Fix Log (2026-08-29)

Cross-checked `docs/IMPLEMENTATION_CHECKLIST.md` / `docs/REQUIREMENT_TRACEABILITY.md`
against the actual code by importing and executing it (not just reading it).
The docs claimed 100% complete with "18 passed" tests, which was true for the
tests that existed — but several core code paths were never exercised by any
test and were broken. All items below were reproduced, then fixed, then
re-verified by re-running the reproduction.

## Critical (installer could not run at all)

1. **`logging/` package shadowed Python's stdlib `logging` module.**
   Because the installer's own log-handling package was named `logging` and
   sits on `sys.path` as the project root, `import logging` anywhere
   (including inside the package's own `installer_logger.py`) resolved to
   itself instead of the standard library, causing
   `AttributeError: module 'logging' has no attribute 'getLogger'`.
   This crashed `Installer.__init__` on every single call — including the
   README's own documented demo (`python -m launcher --demo`).
   **Fix:** renamed the package to `installer_logging/` and updated the one
   import site (`installer_engine/installer.py`).

2. **`Installer.install(manifest)` crashed when passed a `Manifest` object.**
   `launcher.py`'s own `demo_manifest()` builds a `Manifest` via
   `Manifest.from_dict(...)`, exactly as `Installer.install()` is documented
   to expect — but `_system_check`/`_platform_check` did `for c in manifest`,
   and `Manifest` isn't iterable, so this always raised
   `TypeError: 'Manifest' object is not iterable`. The full install pipeline
   was therefore never actually reachable end-to-end.
   **Fix:** `install()` now normalizes `manifest` to its `.components` list
   once at the top (matching the pattern `DependencyManager` already used).

3. **`browser_setup/browser_installer.py` wrote into a directory it never created.**
   Non-archive artifacts were written to `paths.browser/'runtime'/<name>`
   without first creating the `runtime/` subdirectory, raising
   `FileNotFoundError` for any non-zip/tar browser artifact.
   **Fix:** the directory is now created before writing.

4. **`update_system/transactional.py` (`TransactionalUpdate`) crashed on construction.**
   It read `paths.previous` / `paths.failed`, but `InstallPaths` never
   defines those attributes (every other module in the codebase builds them
   as `paths.base/'previous'` and `paths.base/'failed'` instead).
   **Fix:** `TransactionalUpdate` now builds and uses those paths the same
   way `StagedUpdate` and `Installer` do.

## Logic bugs (ran without crashing, but silently did the wrong thing)

5. **Health-check dicts were used where a boolean was expected**, in three
   places: `model_setup/model_manager.py`, `runtime_setup/health_check.py`,
   and `bootstrap/first_launch.py`. `OllamaAdapter.health_check()` returns a
   dict like `{"healthy": False, ...}`, which is always *truthy* as an
   object — so `if not runtime.health_check()` was always `False`
   regardless of actual health, meaning the code never noticed an unhealthy
   runtime and (in `first_launch`) the final `last_result` was always
   reported as `"degraded"` even on a fully healthy first launch, because it
   compared the dict `is True`.
   **Fix:** all three now read `.get("healthy", False)` explicitly.

6. **`Updater.update(current, target)` was a no-op.** It called
   `self.prepare()` with no source, which defaults to staging a copy of the
   *current* install over itself — so "updating" never actually placed any
   new version content anywhere; it just did a pointless atomic swap of
   identical content. This was never caught because the test suite
   (`tests/update/test_update.py`) bypasses `Updater` entirely and drives
   `StagedUpdate` directly.
   **Fix:** `Updater.update()` now takes a required `source` (the prepared
   new-version payload) and threads it through `prepare()`/`stage()`, and
   returns `activation_failed` instead of silently reporting success if the
   post-activation health gate fails.

## Structural (spec §3 folder list)

The spec's `02_INSTALLER/` folder list names `integrity_checker/` and
`first_launch/` as top-level modules. The implementation had this logic
working correctly but under different names (`artifact_manager/` for
checksum+signature verification, `bootstrap/first_launch.py` for the launch
sequence). Rather than duplicate ~1,500 lines of working, tested logic under
new names, added `integrity_checker/` and `first_launch/` as thin,
spec-named façades that re-export the existing implementation, so both the
spec's folder contract and the existing internal structure are satisfied
without behavioral duplication or drift.

## Verification performed after every fix

- `python -m compileall -q .` — no syntax/import errors across all 162+ files.
- Full test suite re-run (18/18 passing) after each change.
- Direct execution smoke tests beyond the existing unit tests: constructing
  `Installer`, running `python -m launcher --demo`, a full
  `Installer.install()` → `generate_config` → `validate_config` →
  `run_first_launch()` pipeline against a real local artifact, a full
  `TransactionalUpdate` stage/activate/rollback cycle, and a full
  `Updater.update()` stage/activate/rollback cycle with real differing
  content — all confirmed working end-to-end, not just import-clean.

## Still out of scope for this pass

- No live network access was available in this environment, so the actual
  HTTPS download path (`download_manager/downloader.py` against a real
  server) was reviewed but not executed end-to-end; the resumable-download
  and retry unit tests do exercise it against mocked/local conditions.
- Ollama/browser binaries were not actually installed or started (by
  design — this environment has no GUI/runtime to install into); the
  adapter code paths were reviewed and partially exercised, but a real
  `ollama serve` health-check loop was not run.
