from .element_detector import ElementDetector
from .text_reader import TextReader
from .state_classifier import StateClassifier
from error_detection.detector import ErrorDetector


class ScreenAnalyzer:
    """Combines the raw adapter output with error detection and state
    classification into the full 7.5 Screen Understanding Output contract.

    Previously this just returned whatever the registry/adapter produced
    verbatim, so element_detector/text_reader/state_classifier existed but
    were never actually wired together into one call -- this is the piece
    that was missing.
    """

    def __init__(self, registry, error_detector=None, state_classifier=None,
                 element_detector=None, text_reader=None):
        self.registry = registry
        self.error_detector = error_detector or ErrorDetector()
        self.state_classifier = state_classifier or StateClassifier()
        self.element_detector = element_detector or ElementDetector()
        self.text_reader = text_reader or TextReader()

    def analyze(self, observation):
        raw = self.registry.analyze(observation)

        elements = self.element_detector.detect(raw)
        text_lines = self.text_reader.read(raw)

        adapter_errors = list(raw.get("errors", []) or [])
        detected_errors = self.error_detector.detect({"text": text_lines, **observation})
        errors = sorted(set(adapter_errors) | set(detected_errors))

        loading = bool(raw.get("loading", False))
        confidence = raw.get("confidence", 0.0)
        uncertainty_reason = raw.get("uncertainty_reason")
        if not elements and uncertainty_reason is None:
            uncertainty_reason = "no_elements_detected"

        output = {
            "elements": elements,
            "errors": errors,
            "loading": loading,
            "confidence": confidence,
            "uncertainty_reason": uncertainty_reason,
            "text": text_lines,
        }
        output["state"] = self.state_classifier.classify(output)
        return output
