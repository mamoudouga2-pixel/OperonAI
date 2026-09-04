"""
Task checkpointing and safe resume (spec 8.6 TASK CHECKPOINTING).

"Checkpoint must re-check real-world state before resuming, because
computer/browser state can change between crash and restart." We model
that by fingerprinting the environment at save time and refusing to
resume unless the fingerprint still matches.
"""

from errors import MemoryNotFound, MemoryWriteBlocked


class CheckpointStore:
    def __init__(self):
        self.data = {}

    def save(
        self,
        task_id,
        completed_steps,
        evidence_refs,
        plan_version,
        safe_resume_point,
        state_fingerprint,
    ):
        checkpoint = {
            "completed_steps": list(completed_steps),
            "verified_evidence_refs": list(evidence_refs),
            "current_plan_version": plan_version,
            "safe_resume_point": safe_resume_point,
            "state_fingerprint": state_fingerprint,
        }
        self.data[task_id] = checkpoint
        return dict(checkpoint)

    def resume(self, task_id, current_fingerprint):
        """Return the checkpoint if it's still safe to resume from,
        otherwise raise.

        MEMORY_NOT_FOUND: no checkpoint exists for this task.
        MEMORY_WRITE_BLOCKED: the world changed since the checkpoint was
        taken (browser/computer state no longer matches), so blindly
        replaying stale state is refused; the caller must re-plan from
        the current real state instead.
        """
        checkpoint = self.data.get(task_id)
        if not checkpoint:
            raise MemoryNotFound(task_id=task_id)
        if checkpoint["state_fingerprint"] != current_fingerprint:
            raise MemoryWriteBlocked(
                "State changed since checkpoint; safe resume refused",
                task_id=task_id,
            )
        return dict(checkpoint)

    def latest(self, task_id):
        checkpoint = self.data.get(task_id)
        return dict(checkpoint) if checkpoint else None

    def clear(self, task_id):
        self.data.pop(task_id, None)
