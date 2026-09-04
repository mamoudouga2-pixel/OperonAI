"""Public API / Interfaces (spec 7.23).

Previously this section of the spec had no corresponding code at all: the
underlying capability existed scattered across classes with *different*
names and signatures (``GroundingMatcher.match`` not ``ground``,
``EvidenceCollector.collect`` not ``collect_evidence``,
``ErrorDetector.detect`` not ``detect_error``,
``FailureClassifier.classify`` not ``classify_failure``,
``RecoveryStrategy.recommend`` not ``recommend_recovery``), and
``health_check()`` did not exist anywhere. This module is the single,
literal implementation of the 9 functions the spec names, wiring sane
defaults for each subsystem while still allowing full override via
``configure()`` -- consistent with the adapter-based / no-hard-dependency
design in 7.6, this facade is a convenience layer, not a requirement to
use the underlying classes directly.

Import as (matching this project's flat, sys.path-based module layout --
see tests/test_part07.py)::

    import sys; sys.path.insert(0, "path/to/07_VISION_VERIFICATION")
    import api
    api.health_check()
"""
from __future__ import annotations
import tempfile
from pathlib import Path

from adapters.registry import AdapterRegistry
from adapters.ocr_adapter import OCRAdapterImpl
from capture.artifact_store import ArtifactStore
from capture.screen_capture import ScreenCapture
from capture.window_capture import WindowCapture
from capture.providers import CaptureUnavailableError
from screen_understanding.analyzer import ScreenAnalyzer
from grounding.matcher import GroundingMatcher
from grounding.confidence import ConfidencePolicy
from verification.postcondition import PostconditionEngine
from verification.independent_check import IndependentCheck
from verification.verifier import Verifier
from evidence.collector import EvidenceCollector
from evidence.retention import RetentionPolicy
from error_detection.detector import ErrorDetector
from error_detection.classifier import FailureClassifier
from recovery.strategy import RecoveryStrategy
from recovery.retry_policy import RetryPolicy
from loop_detection.detector import LoopDetector
from events import default_bus


class _Registry:
    """Lazily-built default component wiring. Call ``configure()`` before
    first use to override any piece (e.g. plug in a real vision model
    adapter, or point evidence storage at a different directory)."""

    def __init__(self):
        self._evidence_root = None
        self._components = {}

    def configure(self, evidence_root=None, vision_adapters=None, ocr_adapters=None,
                   confidence_policy=None, max_evidence_age_ms=30000, retention_max_age_ms=None,
                   loop_limit=3, retry_max=3, verification_timeout_ms=15000, event_bus=None):
        self._evidence_root = evidence_root or self._evidence_root
        self._components = {}  # force rebuild on next access
        self._overrides = dict(
            vision_adapters=vision_adapters or [],
            ocr_adapters=ocr_adapters if ocr_adapters is not None else [OCRAdapterImpl()],
            confidence_policy=confidence_policy or ConfidencePolicy(),
            max_evidence_age_ms=max_evidence_age_ms,
            retention_max_age_ms=retention_max_age_ms or max_evidence_age_ms * 100,
            loop_limit=loop_limit,
            retry_max=retry_max,
            verification_timeout_ms=verification_timeout_ms,
            event_bus=event_bus or default_bus,
        )

    def _ensure(self):
        if self._components:
            return self._components
        overrides = getattr(self, "_overrides", None) or {}
        vision_adapters = overrides.get("vision_adapters", [])
        ocr_adapters = overrides.get("ocr_adapters", [OCRAdapterImpl()])
        confidence_policy = overrides.get("confidence_policy") or ConfidencePolicy()
        event_bus = overrides.get("event_bus") or default_bus

        registry = AdapterRegistry(event_bus=event_bus)
        for a in vision_adapters:
            registry.register_vision(a)
        for a in ocr_adapters:
            registry.register_ocr(a)

        evidence_root = self._evidence_root or str(Path(tempfile.gettempdir()) / "part07_evidence")
        store = ArtifactStore(evidence_root)

        postconditions = PostconditionEngine()
        checker = IndependentCheck(postconditions)
        verifier = Verifier(
            checker,
            max_age_ms=overrides.get("max_evidence_age_ms", 30000),
            timeout_ms=overrides.get("verification_timeout_ms", 15000),
            confidence_policy=confidence_policy,
            event_bus=event_bus,
        )

        self._components = {
            "registry": registry,
            "store": store,
            "screen_capture": ScreenCapture(event_bus=event_bus),
            "window_capture": WindowCapture(event_bus=event_bus),
            "analyzer": ScreenAnalyzer(registry),
            "matcher": GroundingMatcher(),
            "evidence_collector": EvidenceCollector(store, event_bus=event_bus),
            "retention": RetentionPolicy(overrides.get("retention_max_age_ms", 3_000_000)),
            "postconditions": postconditions,
            "verifier": verifier,
            "error_detector": ErrorDetector(),
            "classifier": FailureClassifier(),
            "recovery": RecoveryStrategy(event_bus=event_bus),
            "retry_policy": RetryPolicy(overrides.get("retry_max", 3)),
            "loop_detector": LoopDetector(overrides.get("loop_limit", 3), event_bus=event_bus),
            "confidence_policy": confidence_policy,
        }
        return self._components


_registry = _Registry()


def configure(**kwargs):
    """Override default component wiring. See ``_Registry.configure``."""
    _registry.configure(**kwargs)


def capture(request: dict) -> dict:
    """spec 7.23: capture(request) -> raw capture result (7.2).

    ``request = {"mode": "screen" | "window", ...}``; extra keys (e.g.
    ``bbox``, ``window_id``) are forwarded to the underlying provider.
    """
    request = dict(request or {})
    mode = request.pop("mode", "screen")
    comps = _registry._ensure()
    if mode == "window":
        return comps["window_capture"].capture(request)
    return comps["screen_capture"].capture(request)


def analyze(observation: dict) -> dict:
    """spec 7.23: analyze(observation) -> Screen Understanding Output (7.5)."""
    return _registry._ensure()["analyzer"].analyze(observation)


def ground(target_query: dict, context: dict) -> dict | None:
    """spec 7.23: ground(target_query, context) -> best matching element or None.

    Falls back to coordinate-only grounding (7.9) when semantic matching
    finds nothing and ``target_query`` carries explicit ``x``/``y``.
    """
    comps = _registry._ensure()
    candidates = comps["matcher"].match(target_query, context)
    if candidates:
        return {"element": candidates[0][1], "score": candidates[0][0], "method": "semantic"}
    if "x" in target_query and "y" in target_query:
        hit = comps["matcher"].ground_by_coordinates(target_query["x"], target_query["y"], context.get("elements", []))
        if hit:
            return {"element": hit, "score": None, "method": "coordinate_fallback"}
    return None


def collect_evidence(context: dict):
    """spec 7.23: collect_evidence(context) -> Evidence (7.10).

    ``context`` = {task_id, action_id, source, data, description, type?}
    """
    comps = _registry._ensure()
    return comps["evidence_collector"].collect(
        context["task_id"], context["action_id"], context["source"], context["data"],
        context.get("description", ""), context.get("type", "SCREENSHOT"),
    )


def verify(request: dict) -> dict:
    """spec 7.23: verify(request) -> Verification Output (7.13).

    ``request`` follows the 7.4 input contract and additionally carries
    ``current_state`` (observed state to check postconditions against) and
    ``evidence`` (resolved evidence records) inline, since this facade has
    no separate evidence-resolution service to look ``evidence_ids`` up
    against -- callers that already resolved evidence themselves (e.g. via
    ``collect_evidence``) pass the records straight through.
    """
    current_state = request.get("current_state", {})
    evidence = request.get("evidence", [])
    return _registry._ensure()["verifier"].verify(request, current_state, evidence)


def detect_error(observation: dict) -> list:
    """spec 7.23: detect_error(observation) -> list of error codes (7.16)."""
    return _registry._ensure()["error_detector"].detect(observation)


def classify_failure(data) -> str:
    """spec 7.23: classify_failure(data) -> one of the 7.17 failure classes."""
    return _registry._ensure()["classifier"].classify(data)


def recommend_recovery(context: dict) -> str:
    """spec 7.23: recommend_recovery(context) -> recovery action (7.18).

    ``context`` = {"failure": <failure class>, "partial": bool}
    """
    comps = _registry._ensure()
    return comps["recovery"].recommend(context.get("failure"), context.get("partial", False))


def health_check() -> dict:
    """spec 7.23: health_check() -> subsystem status.

    Did not exist at all before. Reports, per subsystem, whether it is
    wired and (where cheaply checkable) usable -- this never raises; a
    broken subsystem is reflected in the returned dict, not an exception,
    since a health check that itself crashes defeats its purpose.
    """
    comps = _registry._ensure()
    status = {"status": "OK", "subsystems": {}}

    def record(name, ok, detail=None):
        status["subsystems"][name] = {"ok": ok, "detail": detail}
        if not ok:
            status["status"] = "DEGRADED"

    try:
        comps["store"].save("__health_check__.tmp", b"ok")
        comps["store"].delete("__health_check__.tmp")
        record("evidence_store", True, str(comps["store"].root))
    except Exception as exc:
        record("evidence_store", False, str(exc))

    reg = comps["registry"]
    record(
        "vision_ocr_adapters",
        bool(reg.vision or reg.ocr),
        {"vision_adapters": len(reg.vision), "ocr_adapters": len(reg.ocr)},
    )

    try:
        from PIL import Image  # noqa
        record("capture_backend_importable", True, "Pillow available")
    except ImportError as exc:
        record("capture_backend_importable", False, str(exc))

    try:
        import pytesseract  # noqa
        record("ocr_backend_importable", True, "pytesseract available")
    except ImportError as exc:
        record("ocr_backend_importable", False, str(exc))

    record("event_bus", True, {"events_recorded": len(default_bus.history)})
    return status
