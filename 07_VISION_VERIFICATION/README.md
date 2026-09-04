# Part 07 — Vision and Independent Verification

Reference implementation of the Part 07 v1.0 specification (screen understanding,
adapter-based vision/OCR, element grounding, evidence collection, independent
postcondition verification, confidence/uncertainty policy, error detection,
bounded recovery, loop detection, and events).

## Status

This package was reviewed against the specification and revised; it is **not**
being re-labelled "100% complete" here, in keeping with the spec's own core
principle (7.1/7.30): a claim of completeness is not the same thing as
independently verified completeness. What changed and what is still an
intentional extension point is listed below so you can verify it yourself.

### What's genuinely implemented and tested in this environment
- Full event system (7.22) — `events.py`, 12 named events, wired into capture,
  adapters, verification, evidence, recovery, and loop detection.
- Public API facade (7.23) — `api.py` implements all 9 functions
  (`capture`, `analyze`, `ground`, `collect_evidence`, `verify`, `detect_error`,
  `classify_failure`, `recommend_recovery`, `health_check`) under their spec
  names; previously 5 of 9 did not exist under any name, and `health_check`
  did not exist at all.
- OCR fallback (7.7 priority 5) — `adapters/ocr_adapter.py` is a real,
  working implementation on `pytesseract` + Tesseract, verified end-to-end in
  this environment against actual rendered text (not a mock).
- Verifier (7.12–7.14, 7.20, 7.21) — `BLOCKED` and `ERROR` states are now
  reachable (they were declared but dead code before); `missing_conditions`
  in the output is the real list of failed postcondition checks, not a
  hardcoded placeholder; multi-source corroboration (7.7) is computed from
  `request["sources"]` vs. evidence actually supplied; a verification
  timeout is enforced; evidence staleness also checks action-ordering, not
  only a clock diff (7.20).
- Postcondition engine (7.15) — genuine nested AND/OR composition, plus
  `DOM_STATE`, `VISUAL_CONFIRMATION`, `CONFIRMATION_ID_EXISTS`,
  `RECORD_EXISTS` condition types that didn't exist before.
- Grounding (7.9) — role/text/window matching extended with surrounding-
  context and task-context scoring, fuzzy text similarity instead of exact
  string equality, and the coordinate-only fallback the spec calls for
  (previously absent).
- Error detection / failure classification (7.16–7.17) — all 9 error
  categories and all 10 failure classes are reachable (4 error categories
  and 5 failure classes had no code path before).
- Recovery (7.18) — the `partial` completion flag is now actually used to
  change the recommendation.
- Evidence (7.10–7.11) — evidence `type` is a real parameter (was hardcoded
  to `SCREENSHOT`); `redaction_status` reflects what actually happened
  instead of always saying `APPLIED`; redaction also catches unlabeled
  secret-shaped strings (JWTs, opaque tokens), not just keyword hits;
  storage paths are permission-controlled (`chmod 700`/`600`); retention has
  a real `sweep()` that deletes expired artifacts, not just a boolean check.
- 92 automated tests: `tests/test_part07.py` (original 12, kept for
  backward compatibility, all still passing unmodified), `tests/unit/`
  (68 new tests covering modules that had zero test coverage before —
  capture, adapters, screen_understanding, grounding, events, error
  detection, recovery, loop detection), `tests/integration/` (4 tests
  exercising the full `api.py` facade), `tests/end_to_end/` (8 tests
  implementing all 5 named scenarios from spec 7.26, which previously had
  no corresponding code at all).

### What's implemented but NOT exercised against real hardware here
`capture/providers.py` performs real screen/window pixel capture via
`PIL.ImageGrab`. This sandbox is headless (no display, no network to install
alternatives), so the actual pixel-grab call could not be run end-to-end here
— only its error handling and the dependency-injection path (via a fake
provider) were tested. **Verify this on your own machine** before relying on
it; `tests/unit/test_capture.py::test_default_provider_fails_clearly_without_a_display`
documents the exact failure mode you'd see if a display genuinely isn't
available. `ImageGrab` is native on Windows/macOS; on Linux it needs an
active X11/Wayland-XWayland session plus `scrot`/`maim` or `python-xlib`.

### What's an intentional extension point, not a gap
`adapters/vision_model_adapter.py` stays an abstract base per spec 7.6
("no specific vision model hard dependency") — plug in a concrete Qwen/Gemma/
etc. adapter at integration time. The system is still fully functional
without one: `AdapterRegistry` falls through to the real OCR adapter, which
is tested (`tests/integration/test_api_facade.py::test_analyze_then_ground_chain_with_real_ocr_fallback`).

## Install
```
pip install -r requirements.txt
# plus the tesseract-ocr system package, e.g.:
#   apt install tesseract-ocr      (Debian/Ubuntu)
#   brew install tesseract         (macOS)
```

## Run tests
```
python -m unittest discover -s 07_VISION_VERIFICATION/tests -v
```
Or by layer:
```
python -m unittest discover -s 07_VISION_VERIFICATION/tests/unit -v
python -m unittest discover -s 07_VISION_VERIFICATION/tests/integration -v
python -m unittest discover -s 07_VISION_VERIFICATION/tests/end_to_end -v
```

`VERIFICATION_REPORT.txt` in this bundle is the literal output of the command
above, run in this environment. Per this module's own operating principle,
treat that report the same way the Verifier treats a Worker's claim: rerun it
yourself rather than trusting it on file.
