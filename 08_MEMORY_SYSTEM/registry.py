"""
Vector backend registry (spec 8.9: backend must be replaceable).

Lets the runtime pick a backend by name from config rather than hard
importing a specific adapter everywhere.
"""

from .qdrant_adapter import QdrantAdapter


class VectorRegistry:
    """Wraps whichever backend instance is active.

    Backwards compatible with the original 1-arg constructor
    (``VectorRegistry(backend_instance)``), and also supports named
    registration for config-driven selection.
    """

    _FACTORIES = {"qdrant": QdrantAdapter}

    def __init__(self, backend=None):
        self.backend = backend

    @classmethod
    def register(cls, name, factory):
        cls._FACTORIES[name] = factory

    @classmethod
    def create(cls, name, **kwargs):
        if name not in cls._FACTORIES:
            raise ValueError(f"Unknown vector backend '{name}'")
        return cls(cls._FACTORIES[name](**kwargs))

    def get(self):
        return self.backend

    def set(self, backend):
        self.backend = backend
