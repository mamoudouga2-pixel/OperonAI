# LOCAL MULTI-AGENT COMPUTER WORKER — PART 05
## BROWSER AGENT — COMPLETE REFERENCE IMPLEMENTATION

Based on the supplied Part 05 Master Technical Specification.

Design:
- engine-independent BrowserAdapter public contract
- isolated task sessions and lifecycle cleanup
- URL/domain validation and redirect protection
- page/DOM/accessibility/state inspection
- semantic locator ordering + confidence gate + bounded fallback
- click/type/select/scroll/navigate/wait/keyboard
- form, upload and download policy validation
- tab/frame switching
- observation/evidence records with sensitive-value redaction
- independent-verification gate
- bounded retry + loop detection + crash recovery
- non-idempotent action protection
- untrusted webpage-content separation
- structured event/log output
- configurable concurrency and timeouts

The implementation is dependency-free and includes a deterministic mock adapter for tests.
A Playwright adapter seam is included without making Playwright mandatory.

Run:
    python -m unittest discover -s 05_BROWSER_AGENT/tests -v
