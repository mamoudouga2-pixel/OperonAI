"""
"Forget" command flow (spec 8.20 FORGET COMMAND).

    User command: "forget this" / "এটা ভুলে যাও"
      -> identify scope
      -> ask clarification if ambiguous
      -> locate records/index entries
      -> delete primary record + vector/index/cache references
      -> verify deletion
      -> report completion
"""

from errors import MemoryNotFound


class AmbiguousForgetTarget(Exception):
    """Raised when a forget request matches more than one candidate and
    needs user clarification before anything is deleted."""

    def __init__(self, candidates):
        self.candidates = candidates
        super().__init__(f"{len(candidates)} candidates match; clarification required")


class Forgetter:
    def __init__(self, structured, semantic, cache, verifier=None, bus=None):
        self.s = structured
        self.v = semantic
        self.c = cache
        self.verifier = verifier
        self.bus = bus

    def resolve(self, candidates):
        """Given a list of memory records matching the user's forget
        request, return the single target or raise for clarification."""
        if not candidates:
            raise MemoryNotFound("no matching memory to forget")
        if len(candidates) > 1:
            raise AmbiguousForgetTarget(candidates)
        return candidates[0]

    def forget(self, memory_id):
        if self.bus is not None:
            self.bus.emit_forget_requested(memory_id) if hasattr(
                self.bus, "emit_forget_requested"
            ) else self.bus.emit("MEMORY_FORGET_REQUESTED", memory_id=memory_id)

        self.s.delete(memory_id)
        self.v.delete(memory_id)
        self.c.invalidate(memory_id)

        if self.verifier is not None:
            self.verifier.verify(memory_id, self.s, self.v, self.c)

        if self.bus is not None:
            self.bus.emit("MEMORY_DELETED", memory_id=memory_id)
            self.bus.emit("MEMORY_DELETE_VERIFIED", memory_id=memory_id)

        return True
