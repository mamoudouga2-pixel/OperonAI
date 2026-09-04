"""Shared sys.path bootstrap so tests can `import` sibling top-level
packages (memory_manager, working_memory, ...) the same way the
runtime does: 08_MEMORY added to sys.path, not imported as a package
(its name is not a valid Python identifier)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
