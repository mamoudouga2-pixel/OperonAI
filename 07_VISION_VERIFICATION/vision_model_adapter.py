"""Vision-model adapter extension point (spec 7.6: 'কোনো নির্দিষ্ট vision model
hard dependency হবে না' -- no specific vision model is a hard dependency).

This is intentionally NOT a working implementation: which local model
(Qwen-VL, Gemma, LLaVA, or a future model) is available is a deployment-time
decision the core verifier must stay ignorant of, per spec. Ship a concrete
subclass at integration time, register it with ``AdapterRegistry``, and the
rest of this package (grounding, verification, error detection) works
unchanged against whatever ``analyze()`` returns, as long as it matches the
7.5 Screen Understanding Output shape.

Until a concrete adapter is registered, ``AdapterRegistry.analyze`` still
functions correctly by falling through to the OCR adapter (see
``adapters/ocr_adapter.py``, which *is* a real, working default) --
that fallback chain is exercised in
``tests/integration/test_adapter_fallback_chain.py``.
"""
from __future__ import annotations


class VisionModelAdapter:
    """Subclass this and implement ``analyze`` against a specific local model.

    Expected return shape (spec 7.5)::

        {
          "elements": [{"role": ..., "text": ..., "bounding_box": {...}, "confidence": ...}, ...],
          "errors": [...],
          "loading": bool,
          "confidence": float,
          "uncertainty_reason": str | None,
        }
    """

    model_name: str = "unset"

    def analyze(self, artifact):
        raise NotImplementedError(
            f"{type(self).__name__} has not implemented analyze(); this base class is a "
            "deliberate extension point (spec 7.6), not a usable adapter on its own. "
            "Subclass VisionModelAdapter with a concrete local model integration, or rely "
            "on the OCR fallback in adapters/ocr_adapter.py."
        )
