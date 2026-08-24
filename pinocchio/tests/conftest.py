from __future__ import annotations

import sys
import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
root = str(ROOT)
if root in sys.path:
    sys.path.remove(root)
sys.path.insert(0, root)

pinocchio = importlib.import_module("pinocchio")
if not hasattr(pinocchio, "__path__"):
    raise RuntimeError("pinocchio package import was shadowed by the CLI module")
