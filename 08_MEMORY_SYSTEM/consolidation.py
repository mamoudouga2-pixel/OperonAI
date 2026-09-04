"""
Memory consolidation (spec 8.17 MEMORY CONSOLIDATION).

"Repeated temporary observations do not automatically become permanent
memory. Consolidation checks provenance, usefulness, duplication and
user policy."
"""

from collections import Counter


class Consolidator:
    def consolidate(self, items, policy, min_repeats=1):
        """Return the subset of ``items`` eligible for permanent
        long-term storage.

        - Provenance and retention_policy must both pass ``policy``.
        - USER_APPROVED_INFERENCE items must carry explicit approval.
        - A temporary observation only becomes eligible once seen at
          least ``min_repeats`` times with the same summary (dedup by
          content, not just by re-submission of the same memory_id).
        """
        seen = Counter(
            item.get("summary")
            for item in items
            if item.get("provenance") and item.get("retention_policy") in policy.ALLOWED
        )

        eligible = []
        deduped_summaries = set()
        for item in items:
            provenance = item.get("provenance")
            if not provenance or item.get("retention_policy") not in policy.ALLOWED:
                continue
            if provenance.get("source") == "USER_APPROVED_INFERENCE" and not provenance.get(
                "approved"
            ):
                continue
            if seen[item.get("summary")] < min_repeats:
                continue
            if item.get("summary") in deduped_summaries:
                continue
            deduped_summaries.add(item.get("summary"))
            eligible.append(item)
        return eligible
