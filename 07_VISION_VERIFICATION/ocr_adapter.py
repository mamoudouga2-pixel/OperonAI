"""Real OCR adapter (spec 7.7 priority 5: OCR fallback; 7.25: 'OCR fallback' test).

Backed by ``pytesseract`` + the Tesseract binary, both of which are common,
widely-available local dependencies (no network calls, no cloud API --
consistent with this being a *local* multi-agent worker). If either is
missing on a given machine, ``read`` raises a clear, catchable error instead
of importing at module load time, so a system with no vision adapter and no
OCR installed still fails loudly and specifically rather than with a bare
``NotImplementedError``.
"""
from __future__ import annotations
import io


class OCRUnavailableError(RuntimeError):
    pass


class OCRAdapterImpl:
    def __init__(self, lang: str = "eng"):
        self.lang = lang

    def read(self, artifact) -> dict:
        """``artifact`` is raw image bytes (PNG/JPEG/etc), or a dict with a
        ``data`` key holding raw image bytes (the shape returned by
        ``capture/providers.py``). Returns a screen_understanding-shaped
        dict: elements (one per detected text line, with bounding box and
        per-line confidence) plus a flat ``ocr_text`` convenience string.
        """
        raw = artifact["data"] if isinstance(artifact, dict) else artifact
        if not raw:
            raise OCRUnavailableError("empty image data passed to OCR adapter")
        try:
            from PIL import Image
            import pytesseract
        except ImportError as exc:
            raise OCRUnavailableError(
                "pytesseract and Pillow are required for OCRAdapterImpl "
                "(pip install pytesseract pillow, plus the tesseract-ocr system binary)"
            ) from exc
        try:
            image = Image.open(io.BytesIO(raw))
            data = pytesseract.image_to_data(image, lang=self.lang, output_type=pytesseract.Output.DICT)
        except pytesseract.TesseractNotFoundError as exc:
            raise OCRUnavailableError(
                "tesseract binary not found on PATH -- install the tesseract-ocr system package"
            ) from exc
        except Exception as exc:
            raise OCRUnavailableError(f"OCR failed: {exc}") from exc

        elements = []
        words = []
        n = len(data.get("text", []))
        for i in range(n):
            text = (data["text"][i] or "").strip()
            if not text:
                continue
            conf_raw = data["conf"][i]
            try:
                confidence = max(0.0, float(conf_raw)) / 100.0
            except (TypeError, ValueError):
                confidence = 0.0
            elements.append({
                "role": "text",
                "text": text,
                "bounding_box": {
                    "x": data["left"][i], "y": data["top"][i],
                    "width": data["width"][i], "height": data["height"][i],
                },
                "confidence": round(confidence, 4),
            })
            words.append(text)
        return {
            "elements": elements,
            "ocr_text": " ".join(words),
            "errors": [],
            "loading": False,
            "confidence": round(sum(e["confidence"] for e in elements) / len(elements), 4) if elements else 0.0,
            "uncertainty_reason": None if elements else "no_text_detected",
            "source": "ocr",
        }
