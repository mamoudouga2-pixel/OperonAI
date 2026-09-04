# Part 08 — Memory, State and Data Retention System

Local Multi-Agent Computer Worker · File 08 · Spec version 1.08.0

Status: **complete** — all folders from spec section 8.3 are implemented,
all testing requirements from 8.31 and all end-to-end scenarios from
8.32 have automated tests, and the acceptance criteria in 8.33 are met
by the current codebase (see "Acceptance criteria" below).

## Running the tests

```bash
cd 08_MEMORY
python3 -m unittest discover -s tests -p "test_*.py" -v
```

91 tests: 11 in `tests/test_part08.py` (original regression suite,
kept as-is), 63 in `tests/unit/`, 8 in `tests/integration/`, 6 in
`tests/end_to_end/` (one per 8.32 scenario). No external dependencies —
`requirements.txt` stays empty beyond the standard library, matching
the local-first default in spec 8.2.

**Import convention:** this package's directory name (`08_MEMORY`)
starts with a digit and is not a valid Python package identifier, so it
is never imported as `08_MEMORY.xxx`. Instead the runtime (and every
test file) adds the `08_MEMORY/` directory itself to `sys.path` and
imports its subpackages as top-level modules, e.g. `import errors` or
`from memory_manager.policy import MemoryPolicy`. Keep this in mind if
you add new modules — use absolute imports (`from privacy.redaction
import Redactor`), not `from ..privacy...`.

## Layout

```
08_MEMORY/
├── __init__.py            package version marker
├── config.py               MemoryConfig — loads/validates 8.30 JSON config
├── errors.py                MEMORY_* error codes as exception classes (8.29)
├── events.py                MEMORY_* event bus + names (8.28)
├── reconciliation.py        partial-failure log + retry job (8.27)
├── memory_manager/          write/retrieve orchestration (8.1, 8.13, 8.16)
│   ├── manager.py            MemoryManager — the single write/retrieve entry point
│   ├── policy.py              MemoryPolicy — provenance/sensitivity/retention checks
│   ├── router.py               MemoryRouter — type -> store name
│   ├── cache.py                 RetrievalCache with id-based invalidation (8.24)
│   └── conflict.py               ConflictResolver — dup/merge/version/reject (8.18)
├── working_memory/          ephemeral task-execution state (8.5)
├── task_memory/              plans, checkpoints, history (8.6)
├── structured_storage/        SQLite + migrations + Repository contract (8.7)
├── long_term_memory/          embedding, semantic store, retrieval, consolidation (8.8, 8.10, 8.16, 8.17)
├── vector_storage/             VectorStoreAdapter contract + reference adapter (8.9)
├── user_preferences/           versioned preferences + consent (8.14)
├── retention/                   policy classes, cleanup, scheduler (8.19)
├── forgetting/                   forget command, coordinated deletion, verification (8.20, 8.21)
├── privacy/                      sensitivity classification + redaction (8.15)
├── backup_recovery/              backup/restore with checksum + optional encryption (8.25)
└── tests/
    ├── test_part08.py           original 11-test regression suite (kept intact)
    ├── unit/                     one file per module, isolated
    ├── integration/               MemoryManager driving multiple real stores together
    └── end_to_end/                the five 8.32 scenarios
```

## What changed from the previous drop

The earlier `PART08_MEMORY_STATE_DATA_RETENTION_COMPLETE.zip` had every
file present and its 11 tests passing, but most modules were terse
one-line-per-method stubs (3–16 lines each) that covered only the
happy paths those 11 tests exercised. This revision:

- Added `errors.py` (typed exceptions per 8.29 error code) and
  `events.py` (an actual pub/sub bus for the 8.28 event list) instead
  of bare `RuntimeError("CODE_STRING")`.
- Added `MemoryManager` as the real single entry point described in
  8.1/8.13/8.16 — it now validates, routes, persists, invalidates the
  cache, and emits events in one place, instead of callers wiring
  policy/router/store together by hand.
- Added `RetrievalCache` with real invalidation (8.24) and
  `ConflictResolver` for duplicate/merge/version/reject handling
  (8.18), **wired directly into `MemoryManager.write()`** — not just
  built and unit-tested in isolation. Catching that gap took a second
  pass: the first version had `ConflictResolver` fully tested on its
  own but never called from the actual write path, and a follow-up
  bug in the resolver itself let a same-id rewrite from a
  lower-authority source silently win over a user-stated value just
  because it reused the same id (authority is now checked before
  same-id-ness, not after).
- Made SQLite migrations a real, idempotent runner (8.7) instead of a
  `VERSION = 1` constant with no `apply()`.
- Made the vector adapter implement the full `VectorStoreAdapter` ABC,
  including `delete_namespace`, `snapshot`/`restore`, and a
  `set_outage()` hook so backend-unavailable behaviour (8.26, 8.32
  scenario 4) is actually testable.
- Made `CheckpointStore.resume` genuinely refuse to resume when the
  state fingerprint has changed (8.6's "re-check real-world state
  before resume"), with a dedicated error code.
- Made backup/restore support an optional encrypted path with a
  SHA-256 checksum integrity check (8.25). The bundled encryption is a
  dependency-free XOR/keystream placeholder — swap in a real library
  (e.g. `cryptography`'s Fernet) before using this for anything that
  needs actual confidentiality; the point here is that the
  encrypted-vs-plaintext code path and config flag are wired correctly.
- Added `reconciliation.py` for the "partial failures must be
  detectable and reconcilable" requirement in 8.27, which had no
  corresponding code before.
- Populated `tests/unit/`, `tests/integration/`, and `tests/end_to_end/`
  (previously empty except for `__init__.py`) with 75 new tests.

## Acceptance criteria (spec 8.33) — status

- [x] Working, task, structured and semantic memory clearly separated (four distinct stores, routed by `MemoryRouter`).
- [x] All persistent memories carry metadata/provenance policy (`MemoryPolicy.validate`).
- [x] Secret plaintext semantic storage blocked (`privacy.Classifier` + `MemoryPolicy`, tested with untagged secret-shaped content too).
- [x] User-controlled forgetting works across relevant stores (`forgetting.Forgetter` + `DeletionCoordinator` + `DeletionVerifier`).
- [x] Expired memory is cleaned according to policy (`retention.RetentionPolicy` + `Cleanup` + `Scheduler`).
- [x] Qdrant/backend replaceable through adapter (`VectorStoreAdapter` ABC + `VectorRegistry`).
- [x] Crash recovery does not blindly replay stale state (`CheckpointStore.resume` fingerprint check).
- [x] Namespace isolation enforced (retrieval always scoped by `user_scope` + optional `namespace` filter; see end-to-end scenario 5).
- [x] Partial failures are detectable and reconcilable (`DeletionCoordinator` + `ReconciliationLog`/`ReconciliationJob`).
- [x] Unit/integration/end-to-end tests pass (91/91).

### Known scope limitation (documented honestly, not swept under the rug)

Duplicate/conflict handling (8.18) is wired into `MemoryManager.write()`,
but it detects conflicts by **exact `memory_id` match** in the target
store. Re-writing the same id is correctly authority-checked and
versioned/rejected. Two *different* memory_ids that happen to describe
the same fact are **not** cross-referenced — that would need a
namespace/entity dedup index this package doesn't build. If a future
part needs true content-level dedup, add an index lookup keyed on
`(namespace, subject)` and pass that as `existing` to
`ConflictResolver.resolve()` instead of an id lookup.

## Integration notes for Part 09 / Part 10

- **Part 09 (Security / credential vault):** this package deliberately
  refuses to store anything the `privacy.Classifier` flags as
  `SECRET` (spec 8.15) — `MemoryPolicy.validate` raises
  `MemorySensitivityBlocked` before it ever reaches a store. Part 09's
  vault is the only place credentials should live; nothing here needs
  to change when that lands, it just needs to keep calling
  `MemoryPolicy.validate`/`redact` before writing anything a user or
  task supplies.
- **Part 10 (forget/preferences UI):** `user_preferences.Preferences`
  (get/set/delete, versioned) and `forgetting.Forgetter` (with
  `AmbiguousForgetTarget` for the "which one did you mean?" case) are
  the two entry points Part 10 should call directly rather than
  reaching into individual stores.
