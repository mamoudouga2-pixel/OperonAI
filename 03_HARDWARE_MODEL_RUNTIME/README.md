# LOCAL MULTI-AGENT COMPUTER WORKER — PART 03
## HARDWARE_AND_MODEL_RUNTIME_SYSTEM — SPECIFICATION-COMPLETE REFERENCE IMPLEMENTATION

Implemented directly against the supplied Part 03 specification:
1. hardware profile/contract
2. adapter-based runtime interface
3. reasoning/language, vision, embedding, lightweight and policy-gated remote classes
4. required selection flow
5. RAM/VRAM pressure, load/unload policy, concurrency, context budget and low-resource mode
6. bounded fallback: primary -> secondary -> lightweight -> deterministic -> approval/safe failure
7. post-fallback task-state and capability revalidation
8. clear diagnostics for unsupported configurations
9. model replacement without Core rewrite
10. benchmark module for adapter latency/reliability measurement

No third-party runtime dependencies. Python 3.11+.

Run:
    python -m unittest discover -s 03_HARDWARE_RUNTIME/tests -v
