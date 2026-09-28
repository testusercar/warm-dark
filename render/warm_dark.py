#!/usr/bin/env python3
"""Warm Dark card renderer.

  python3 warm_dark.py cards.json [--outdir DIR] [--scale 2] [--validate] [--types]

Prints one PNG path per line. QA warnings go to stderr. See ../SKILL.md.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from warmdark.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
