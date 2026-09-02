# Implementation notes

## Included
- Explicit application lifecycle state machine.
- Explicit task state machine with terminal-state locking.
- Module manifest validation and API compatibility check.
- Event publish/subscribe with handler and payload bounds.
- Atomic JSON state writes using temporary-file replacement.
- JSONL audit trail for error/fail-closed/invalid-transition events.
- Worker crash isolation with bounded module retries and post-recovery health verification.
- Fail-closed behavior when permission or safety state is uncertain.
- Health checks for one or all registered modules.
- Standard-library-only runtime.

## Deliberate boundary
The Core package does not claim to implement browser control, desktop control,
vision, OCR, credential handling, model orchestration, or platform-specific
automation. Those belong to worker/integration parts rather than Core.

## Validation
The included acceptance suite covers lifecycle, invalid transitions,
persistence, manifest validation, event delivery, bounded retries,
worker failure recovery, and fail-closed behavior.
