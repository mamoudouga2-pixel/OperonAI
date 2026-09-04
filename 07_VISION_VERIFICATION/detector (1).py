import re

# Text-pattern signals (spec 7.16 categories that are inherently textual).
# Word-boundary regex instead of plain substring search cuts some false
# positives (e.g. "errors" still matches "error", but "terroir" no longer
# would). This is still naive keyword matching, not negation-aware NLP --
# a message like "no errors found" will still (incorrectly) flag
# VISIBLE_ERROR. Prefer the structured signals below, or a
# VISUAL_CONFIRMATION postcondition, wherever the caller can supply them;
# text matching is the last-resort source per the 7.7 priority order.
TEXT_PATTERNS = {
    re.compile(r"\berror\b", re.I): "VISIBLE_ERROR",
    re.compile(r"\bpermission\b|\baccess denied\b", re.I): "PERMISSION",
    re.compile(r"\blog ?in\b|\bsession expired\b|\bsign in\b", re.I): "SESSION_EXPIRED",
    re.compile(r"\btimeout\b|\btimed out\b", re.I): "LOADING_TIMEOUT",
    re.compile(r"\bnetwork\b|\boffline\b|\bconnection failed\b", re.I): "NETWORK",
}


class ErrorDetector:
    """Detects the error categories in spec 7.16.

    Previously only 5 of the 9 listed categories were detectable at all
    (via text substring matching), and 4 -- unexpected dialog, wrong
    page/window, file conflict, target disappearance -- had no code path
    whatsoever, since they aren't really *textual* signals. Those are now
    read from structured fields on the observation, which is how a
    desktop/browser agent would actually report them (dialog handles,
    window ids, filesystem conflict flags, prior-vs-current target
    presence), rather than trying to infer them from prose.
    """

    def detect(self, observation):
        found = set()
        text = " ".join(observation.get("text", []) or [])
        for pattern, code in TEXT_PATTERNS.items():
            if pattern.search(text):
                found.add(code)

        if observation.get("dialog_present") and not observation.get("dialog_expected"):
            found.add("UNEXPECTED_DIALOG")

        expected_window = observation.get("expected_window_id")
        actual_window = observation.get("window_id")
        if expected_window and actual_window and expected_window != actual_window:
            found.add("WRONG_WINDOW")

        if observation.get("file_conflict"):
            found.add("FILE_CONFLICT")

        if observation.get("target_expected") and observation.get("target_present") is False:
            found.add("TARGET_DISAPPEARED")

        return sorted(found)
