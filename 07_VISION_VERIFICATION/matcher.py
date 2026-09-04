import difflib


def _text_similarity(a, b):
    if not a or not b:
        return 0.0
    a, b = a.strip().lower(), b.strip().lower()
    if a == b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


class GroundingMatcher:
    """Scores candidate on-screen elements against a target description
    (spec 7.9): role, text, surrounding context, active window, and
    expected task context must all be weighed -- a visual hit alone is not
    enough to authorize a click. Previously only role/text/window_id were
    considered and text required exact equality; this adds context/task
    scoring and fuzzy text matching (OCR/vision text rarely matches a
    target string byte-for-byte).
    """

    WEIGHTS = {"role": 0.35, "text": 0.30, "window": 0.10, "context": 0.15, "task": 0.10}

    def match(self, target, context):
        out = []
        active_window = context.get("active_window_id")
        surrounding = set(context.get("surrounding_text", []) or [])
        expected_task = context.get("task_context")
        for element in context.get("elements", []):
            score = 0.0
            if target.get("role") and element.get("role") == target["role"]:
                score += self.WEIGHTS["role"]
            if target.get("text"):
                score += self.WEIGHTS["text"] * _text_similarity(target["text"], element.get("text", ""))
            window_id = element.get("window_id", active_window)
            if target.get("window_id") and window_id == target["window_id"]:
                score += self.WEIGHTS["window"]
            elif target.get("window_id") and active_window and target["window_id"] == active_window:
                score += self.WEIGHTS["window"]
            if target.get("nearby_text") and target["nearby_text"] in surrounding:
                score += self.WEIGHTS["context"]
            if target.get("task_context") and expected_task and target["task_context"] == expected_task:
                score += self.WEIGHTS["task"]
            if score > 0:
                out.append((round(score, 4), element))
        return sorted(out, key=lambda x: x[0], reverse=True)

    def ground_by_coordinates(self, x, y, elements):
        """Coordinate-only fallback (spec 7.9: 'Coordinate-only grounding
        fallback হিসেবে ব্যবহার হবে') -- used only when semantic matching
        above finds nothing usable; returns the smallest element whose
        bounding box contains (x, y), since the smallest containing box is
        the most specific match for overlapping/nested elements.
        """
        hits = []
        for element in elements:
            box = element.get("bounding_box") or {}
            bx, by = box.get("x", 0), box.get("y", 0)
            bw, bh = box.get("width", 0), box.get("height", 0)
            if bx <= x <= bx + bw and by <= y <= by + bh:
                hits.append((bw * bh, element))
        if not hits:
            return None
        hits.sort(key=lambda pair: pair[0])
        return hits[0][1]
