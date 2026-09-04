# LOCAL MULTI-AGENT COMPUTER WORKER
## PART 04 — BOSS_AGENT_SUPERVISOR_SYSTEM
Complete reference implementation based on the supplied Master Technical Specification.

Flow:
User Instruction -> Understand -> Clarify -> Plan -> Security Check -> Approval ->
Worker Selection -> Execute -> Verify -> Recover/Re-plan -> Final Report

Safety:
- critical missing information produces clarification
- high-risk actions pause before execution
- worker success claims are never accepted without evidence
- bounded retries and loop detection prevent infinite recovery
- final report contains outcome, steps, approvals, evidence, recovery and verification

Python 3.11+, standard library only.
Run: python -m unittest discover -s 04_BOSS_AGENT/tests -v
