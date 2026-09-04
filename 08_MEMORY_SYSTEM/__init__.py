"""Structured persistent storage: settings, preferences, metadata."""

from .migrations import Migrations
from .repository import Repository
from .sqlite_adapter import SQLiteAdapter

__all__ = ["SQLiteAdapter", "Migrations", "Repository"]
