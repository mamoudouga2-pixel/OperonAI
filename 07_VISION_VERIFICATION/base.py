"""Adapter contracts (spec 7.6): the core verifier depends on these
interfaces only, never on a specific vision/OCR model."""
from abc import ABC, abstractmethod


class VisionAdapter(ABC):
    @abstractmethod
    def analyze(self, artifact): ...


class OCRAdapter(ABC):
    @abstractmethod
    def read(self, artifact): ...
