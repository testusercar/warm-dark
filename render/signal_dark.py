#!/usr/bin/env python3
"""Compatibility entry point. The v1 filename is kept so existing agent habits
and scripts keep working; everything now renders through warm_dark.py (v2).

v1 manifests (hero / metric / alert / bullets / watch) render unchanged.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from warmdark.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
