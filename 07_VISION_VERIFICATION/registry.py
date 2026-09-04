from events import default_bus, VISION_ANALYSIS_STARTED, VISION_ANALYSIS_COMPLETED


class AdapterRegistry:
    """Model registry (spec 7.6): selects a vision/OCR adapter by capability,
    core verifier code never needs to know which concrete model is behind it.
    """

    def __init__(self, event_bus=None):
        self.vision = []
        self.ocr = []
        self.event_bus = event_bus or default_bus
        self.last_errors = []  # diagnostics for health_check(); most recent analyze() call only

    def register_vision(self, adapter):
        self.vision.append(adapter)

    def register_ocr(self, adapter):
        self.ocr.append(adapter)

    def analyze(self, artifact):
        self.event_bus.emit(VISION_ANALYSIS_STARTED)
        self.last_errors = []
        for adapter in self.vision:
            try:
                result = adapter.analyze(artifact)
                self.event_bus.emit(VISION_ANALYSIS_COMPLETED, adapter=type(adapter).__name__, kind="vision")
                return result
            except Exception as exc:
                self.last_errors.append({"adapter": type(adapter).__name__, "kind": "vision", "error": str(exc)})
                continue
        for adapter in self.ocr:
            try:
                result = adapter.read(artifact)
                self.event_bus.emit(VISION_ANALYSIS_COMPLETED, adapter=type(adapter).__name__, kind="ocr")
                return result
            except Exception as exc:
                self.last_errors.append({"adapter": type(adapter).__name__, "kind": "ocr", "error": str(exc)})
                continue
        raise RuntimeError("MODEL_ADAPTER_FAILURE")

    def health(self):
        return {
            "vision_adapters_registered": len(self.vision),
            "ocr_adapters_registered": len(self.ocr),
            "last_errors": self.last_errors,
        }
