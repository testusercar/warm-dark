"""Warm Dark v3 design tokens (fintech refresh, locked 2026-09-27).

Only four brand colours exist: canvas, ink, muted, olive. Every other value
below is a straight mix of those four, so the palette never drifts. v3 keeps
the v2 colours and changes the system around them: one sans family (Inter +
Inter Display), soft raised surfaces instead of bare canvas lists, thinner
chart strokes and more air.
"""
from __future__ import annotations

import math


def _hex(c: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % c


def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix(a: str, b: str, t: float) -> str:
    ra, rb = _rgb(a), _rgb(b)
    return _hex(tuple(round(x + (y - x) * t) for x, y in zip(ra, rb)))  # type: ignore[arg-type]


CANVAS = "#1a1814"
INK = "#f4f2ea"
MUTED = "#9a9688"
OLIVE = "#c4d44a"

# Raised surfaces: the "card within the card". Separation is tone, never a border.
SURFACE = mix(CANVAS, INK, 0.05)
SURFACE_HI = mix(CANVAS, INK, 0.09)
DIVIDER = mix(SURFACE, MUTED, 0.16)
TRACK_S = mix(SURFACE, MUTED, 0.20)

GRID = mix(CANVAS, MUTED, 0.11)
HAIR = mix(CANVAS, MUTED, 0.18)
TRACK = mix(CANVAS, MUTED, 0.24)
ASH = mix(CANVAS, MUTED, 0.42)
FAINT = "#6e6a5e"
QUIET = mix(FAINT, MUTED, 0.45)
SOFT = mix(MUTED, INK, 0.55)
AREA = mix(CANVAS, INK, 0.05)

# Monochrome composition ramp, strongest first. Olive is never part of it.
RAMP = [INK, SOFT, MUTED, FAINT, ASH, TRACK]
# Stacked columns keep the same order as RAMP (first series brightest). The
# highlighted column uses RAMP; every other column uses the dimmed STACK so
# tall stacks never become white slabs and the highlight carries.
STACK = [FAINT, ASH, TRACK, GRID]

PORTRAIT = (810, int(round(810 * math.sqrt(2))))  # 810 x 1146, ISO 216 A-series
LANDSCAPE = (PORTRAIT[1], PORTRAIT[0])  # 1146 x 810, same sheet turned

MARGIN = 64
MAST_BASELINE = 62
TITLE_TOP = 112
FOOT_FROM_BOTTOM = 46
BODY_BOTTOM_GAP = 90

RADIUS = 24  # surfaces
RADIUS_S = 14  # chips, small tiles
PAD = 28  # inside a surface

# Chart strokes
LINE_W = 2.6
PRIOR_W = 1.7
REF_W = 1.4
AREA_ALPHA = 0.16  # top of the fade under a current line; fades to 0

# name: (font kind, size px, line-height px)
TYPE: dict[str, tuple[str, float, float]] = {
    "meta": ("sans-medium", 17, 22),
    "title": ("display-semibold", 46, 52),
    "title-l": ("display-semibold", 42, 48),
    "dek": ("sans", 22, 31),
    "display": ("display-light", 172, 172),
    "stat": ("display", 64, 70),
    "stat-m": ("display", 44, 50),
    "stat-s": ("display-medium", 30, 36),
    "quote": ("display", 30, 40),
    "lead": ("sans-semibold", 27, 36),
    "body": ("sans", 26, 37),
    "body-strong": ("sans-semibold", 26, 37),
    "row": ("sans", 24, 32),
    "row-strong": ("sans-medium", 24, 32),
    "row-num": ("sans-medium-tnum", 24, 32),
    "small": ("sans", 19, 26),
    "small-num": ("sans-tnum", 19, 26),
    "delta": ("sans-semibold", 24, 30),
    "label": ("sans-medium", 17, 22),
    "whisper": ("sans", 15.5, 21),
    "axis": ("sans-tnum", 15, 19),
    "axis-strong": ("sans-medium-tnum", 16, 21),
    "index": ("display", 28, 34),
}

LABEL_TRACKING = 0.0  # v3 labels are sentence case, untracked
LABEL_CAPS = False
MAX_PUNCHES = 4
