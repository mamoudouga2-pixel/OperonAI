from events import default_bus, VERIFICATION_STARTED, VERIFICATION_VERIFIED, VERIFICATION_FAILED, VERIFICATION_UNCERTAIN
from grounding.confidence import ConfidencePolicy
from verification.postcondition import UnknownConditionType


class Verifier:
    """Independent verifier (spec 7.12-7.14, 7.20, 7.21).

    Fixes relative to the original version:
    - BLOCKED and ERROR were declared in STATES but never actually
      returned by any code path; both are now reachable (BLOCKED via the
      confidence/corroboration/approval policy, ERROR via a caught
      internal exception).
    - ``missing_conditions`` is now the real list of failed postcondition
      identifiers (from ``PostconditionEngine.check_detailed``), not a
      hardcoded ``["postcondition"]`` placeholder.
    - Multi-source corroboration (spec 7.7) is now actually computed from
      ``request["sources"]`` vs. the sources present in the supplied
      evidence, and feeds into whether a HIGH/MEDIUM risk action is
      allowed to be declared VERIFIED.
    - Confidence is read from observed state / computed corroboration
      through ``ConfidencePolicy`` instead of hardcoded magic numbers.
    - Evidence staleness also considers action-ordering
      (``action_occurred_after_evidence``), not only a clock diff, per 7.20.
    - A verification timeout is enforced (spec 7.25's "Verification
      timeout" test requirement had no corresponding code before).
    """

    STATES = {"VERIFIED", "NOT_VERIFIED", "UNCERTAIN", "BLOCKED", "ERROR"}

    def __init__(self, checker, max_age_ms=30000, timeout_ms=15000,
                 confidence_policy=None, event_bus=None):
        self.checker = checker
        self.max_age_ms = max_age_ms
        self.timeout_ms = timeout_ms
        self.confidence_policy = confidence_policy or ConfidencePolicy()
        self.event_bus = event_bus or default_bus

    def verify(self, request, current_state, evidence):
        self.event_bus.emit(VERIFICATION_STARTED, verification_id=request.get("verification_id"))
        try:
            result = self._verify(request, current_state, evidence)
        except UnknownConditionType as exc:
            result = self.out(request, "ERROR", 0.0, f"Postcondition configuration error: {exc}",
                               [], "STOP", missing_conditions=["invalid_condition_type"])
        except Exception as exc:  # verification must fail safe, never crash the caller
            result = self.out(request, "ERROR", 0.0, f"Internal verification error: {exc}",
                               [], "STOP", missing_conditions=["internal_error"])
        self._emit_outcome(result)
        return result

    def _verify(self, request, current_state, evidence):
        if not evidence:
            return self.out(request, "UNCERTAIN", 0.0, "No independent evidence", [], "STOP",
                             missing_conditions=["independent_evidence"])

        stale, stale_reason = self._staleness(current_state)
        if stale:
            return self.out(request, "UNCERTAIN", 0.0, stale_reason, [], "RECAPTURE",
                             missing_conditions=["evidence_freshness"])

        if current_state.get("processing_ms", 0) > self.timeout_ms:
            return self.out(request, "UNCERTAIN", 0.0, "Verification timeout", [], "STOP",
                             missing_conditions=["completed_within_timeout"])

        ok, missing = self.checker.check_detailed(request["expected_state"], current_state)
        if not ok:
            reason = "Expected postcondition not confirmed: " + ", ".join(missing)
            next_state = "RECOVER" if current_state.get("errors") else "REPLAN"
            return self.out(request, "NOT_VERIFIED", 0.15, reason, [], next_state,
                             missing_conditions=missing)

        if current_state.get("errors"):
            return self.out(request, "NOT_VERIFIED", 0.1, "Blocking error visible", [], "RECOVER",
                             missing_conditions=["NO_ERROR"])

        confidence = current_state.get("confidence", 0.9)
        risk = request.get("risk", "LOW")
        expected_sources = set(request.get("sources") or [])
        observed_sources = {e.get("source") for e in evidence if e.get("source")}
        corroborated = len(expected_sources) <= 1 or len(observed_sources) >= 2
        approved = bool(current_state.get("approved", False))

        if not self.confidence_policy.allow(confidence, risk, corroborated, approved):
            gaps = []
            if confidence < self.confidence_policy.threshold_for(risk):
                gaps.append("confidence_threshold")
            if risk in ("MEDIUM", "HIGH") and not corroborated:
                gaps.append("multi_source_corroboration")
            if risk == "HIGH" and not approved:
                gaps.append("human_approval")
            return self.out(
                request, "BLOCKED", confidence,
                f"Confidence policy denies {risk}-risk success claim (corroborated={corroborated}, approved={approved})",
                [e.get("evidence_id") for e in evidence], "STOP",
                missing_conditions=gaps or ["confidence_policy"],
            )

        return self.out(
            request, "VERIFIED", confidence, "Expected postcondition confirmed",
            [e.get("evidence_id") for e in evidence], "CONTINUE", missing_conditions=[],
        )

    def _staleness(self, current_state):
        age = current_state.get("evidence_age_ms", 0)
        if age > self.max_age_ms:
            return True, "Stale evidence"
        if current_state.get("action_occurred_after_evidence"):
            return True, "Evidence predates a later state-changing action (7.20 ordering check)"
        return False, None

    def out(self, r, status, confidence, reason, evidence_ids, next_state, missing_conditions=None):
        assert status in self.STATES, f"invalid verification status: {status!r}"
        return {
            "verification_id": r.get("verification_id"),
            "status": status,
            "confidence": confidence,
            "reason": reason,
            "evidence_ids": evidence_ids,
            "missing_conditions": missing_conditions or [],
            "recommended_next_state": next_state,
        }

    def _emit_outcome(self, result):
        event = {
            "VERIFIED": VERIFICATION_VERIFIED,
            "NOT_VERIFIED": VERIFICATION_FAILED,
            "UNCERTAIN": VERIFICATION_UNCERTAIN,
            "BLOCKED": VERIFICATION_FAILED,
            "ERROR": VERIFICATION_FAILED,
        }[result["status"]]
        self.event_bus.emit(event, verification_id=result.get("verification_id"), status=result["status"])
