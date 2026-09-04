"""
Duplicate and conflict handling (spec 8.18).

    New Memory
      -> same namespace/entity lookup
      -> compare provenance + timestamps
      -> merge / version / reject conflict
      -> retain audit metadata as policy allows
"""

# Provenance sources ranked from least to most authoritative. Later
# beats earlier when timestamps tie.
PROVENANCE_RANK = {
    "USER_APPROVED_INFERENCE": 0,
    "TASK_RESULT": 1,
    "SYSTEM_CONFIGURATION": 2,
    "USER_EXPLICIT": 3,
}


class ConflictResolver:
    """Decides what happens when a new memory collides with an existing
    one in the same namespace/entity slot."""

    def resolve(self, existing, incoming):
        """Return ``(action, memory)``.

        action is one of: "insert", "merge", "version", "reject".

        Authority is checked first, before same-id-ness: a lower-ranked
        provenance source must not silently overwrite a
        higher-ranked one just by reusing the same memory_id. Only
        once authority clears do we look at whether this is the same
        logical record (-> version) or a different id with identical
        content (-> merge) or genuinely new content (-> version, as a
        new entry in that entity's version chain).
        """
        if existing is None:
            inserted = dict(incoming)
            inserted.setdefault("version", 1)
            return "insert", inserted

        same_entity = existing.get("memory_id") == incoming.get("memory_id")
        existing_rank = PROVENANCE_RANK.get(
            (existing.get("provenance") or {}).get("source"), -1
        )
        incoming_rank = PROVENANCE_RANK.get(
            (incoming.get("provenance") or {}).get("source"), -1
        )

        if incoming_rank < existing_rank:
            # A less-authoritative source cannot overwrite a
            # more-authoritative one, whether it reuses the same id
            # (an automated process quietly editing a user-stated
            # value) or targets a different id with the same content.
            return "reject", existing

        if same_entity:
            merged = dict(incoming)
            merged["version"] = int(existing.get("version", 1)) + 1
            merged["audit"] = {
                "previous_version": existing.get("version", 1),
                "previous_provenance": existing.get("provenance"),
            }
            return "version", merged

        if incoming.get("summary") == existing.get("summary"):
            # True duplicate content from an equal/better source: merge
            # provenance rather than storing two rows.
            merged = dict(existing)
            merged.setdefault("audit", {})["merged_from"] = incoming.get("memory_id")
            return "merge", merged

        merged = dict(incoming)
        merged["version"] = int(existing.get("version", 1)) + 1
        merged["audit"] = {
            "previous_version": existing.get("version", 1),
            "previous_memory_id": existing.get("memory_id"),
            "previous_provenance": existing.get("provenance"),
        }
        return "version", merged
