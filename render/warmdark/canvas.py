"""Supersampled drawing surface in logical (card) pixels.

Everything is drawn at K x resolution and downsampled once, which gives
anti-aliased strokes, arcs and polygons that Pillow cannot do natively.
Every text draw is recorded so QA can flag anything outside the safe area.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageDraw, ImageFont

from . import tokens as T

FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"

FONT_FILES = {
    "display-light": "InterDisplay-Light.ttf",
    "display": "InterDisplay-Regular.ttf",
    "display-medium": "InterDisplay-Medium.ttf",
    "display-semibold": "InterDisplay-SemiBold.ttf",
    "sans": "Inter-Regular.ttf",
    "sans-medium": "Inter-Medium.ttf",
    "sans-semibold": "Inter-SemiBold.ttf",
    "sans-tnum": "Inter-Regular-tnum.ttf",
    "sans-medium-tnum": "Inter-Medium-tnum.ttf",
    "sans-semibold-tnum": "Inter-SemiBold-tnum.ttf",
}
# v2 slab kinds still resolve (custom templates, old forks); v3 ships no slab.
KIND_ALIASES = {
    "slab-light": "display-light",
    "slab": "display",
    "slab-medium": "display-medium",
}

CAP = 0.727
XH = 0.546

Point = tuple[float, float]


def resolve_kind(kind: str) -> str:
    return KIND_ALIASES.get(kind, kind)


@lru_cache(maxsize=512)
def _load(kind: str, px: int) -> ImageFont.FreeTypeFont:
    path = FONT_DIR / FONT_FILES[resolve_kind(kind)]
    if path.is_file():
        return ImageFont.truetype(str(path), px)
    try:
        return ImageFont.truetype("DejaVuSans.ttf", px)
    except OSError:
        return ImageFont.load_default(px)


class Font:
    """A font at a logical size; resolves to a pixel font for a given K."""

    __slots__ = ("kind", "size", "lh")

    def __init__(self, kind: str, size: float, lh: float | None = None):
        self.kind = resolve_kind(kind)
        self.size = size
        self.lh = lh if lh is not None else round(size * 1.3)

    @classmethod
    def of(cls, name: str, size: float | None = None, lh: float | None = None) -> "Font":
        kind, sz, l = T.TYPE[name]
        if size is not None:
            return cls(kind, size, lh if lh is not None else l * size / sz)
        return cls(kind, sz, lh if lh is not None else l)

    def sized(self, size: float) -> "Font":
        return Font(self.kind, size, self.lh * size / self.size)

    @property
    def family(self) -> str:
        return "display" if self.kind.startswith("display") else "sans"

    @property
    def cap(self) -> float:
        return self.size * CAP

    @property
    def xh(self) -> float:
        return self.size * XH

    def baseline_in(self, lh: float | None = None) -> float:
        """Baseline offset that optically centres cap height in the line box."""
        l = self.lh if lh is None else lh
        return (l + self.cap) / 2


class Canvas:
    def __init__(self, size: tuple[int, int], scale: float = 1.0, ss: int | None = None):
        self.w, self.h = size
        self.scale = scale
        self.k = ss or (3 if scale <= 1 else 4)
        self.img = Image.new("RGB", (int(self.w * self.k), int(self.h * self.k)), T.CANVAS)
        self.d = ImageDraw.Draw(self.img)
        self.texts: list[tuple[str, tuple[float, float, float, float]]] = []
        self.warnings: list[str] = []

    # ------------------------------------------------------------------ fonts
    def pil(self, f: Font) -> ImageFont.FreeTypeFont:
        return _load(f.kind, max(1, int(round(f.size * self.k))))

    def measure(self, s: str, f: Font, tracking: float = 0.0) -> float:
        if not s:
            return 0.0
        if tracking:
            return sum(self.measure(ch, f) for ch in s) + tracking * f.size * (len(s) - 1)
        return self.pil(f).getlength(s) / self.k

    # ------------------------------------------------------------------- text
    def text(
        self,
        xy: Point,
        s: str,
        f: Font,
        fill: str = T.INK,
        anchor: str = "ls",
        tracking: float = 0.0,
        record: bool = True,
    ) -> tuple[float, float, float, float]:
        if not s:
            return (xy[0], xy[1], xy[0], xy[1])
        x, y = xy
        if tracking:
            total = self.measure(s, f, tracking)
            h = anchor[0]
            x0 = x - (total if h == "r" else total / 2 if h == "m" else 0)
            cx = x0
            for ch in s:
                self.text((cx, y), ch, f, fill, "l" + anchor[1], record=False)
                cx += self.measure(ch, f) + tracking * f.size
            bb = (x0, y - f.cap, x0 + total, y + f.size * 0.25)
        else:
            k = self.k
            fnt = self.pil(f)
            self.d.text((x * k, y * k), s, font=fnt, fill=fill, anchor=anchor)
            b = self.d.textbbox((x * k, y * k), s, font=fnt, anchor=anchor)
            bb = (b[0] / k, b[1] / k, b[2] / k, b[3] / k)
        if record:
            self.texts.append((s, bb))
        return bb

    @staticmethod
    def _label_text(s: str, caps: bool | None) -> tuple[str, float]:
        caps = T.LABEL_CAPS if caps is None else caps
        return (s.upper(), 0.08) if caps else (s, T.LABEL_TRACKING)

    def label(self, xy: Point, s: str, fill: str = T.MUTED, anchor: str = "ls", size: float | None = None,
              caps: bool | None = None) -> float:
        """Section label (sentence case in v3). Returns width."""
        f = Font.of("label", size)
        s, tr = self._label_text(s, caps)
        self.text(xy, s, f, fill, anchor, tracking=tr)
        return self.measure(s, f, tr)

    def label_width(self, s: str, size: float | None = None, caps: bool | None = None) -> float:
        s, tr = self._label_text(s, caps)
        return self.measure(s, Font.of("label", size), tr)

    # ----------------------------------------------------------------- shapes
    def _p(self, pts: Iterable[Point]) -> list[tuple[float, float]]:
        k = self.k
        return [(x * k, y * k) for x, y in pts]

    def line(self, pts: Sequence[Point], fill: str, width: float = 1.0, round_caps: bool = False) -> None:
        if len(pts) < 2:
            return
        w = max(1, int(round(width * self.k)))
        self.d.line(self._p(pts), fill=fill, width=w, joint="curve")
        if round_caps and width >= 2:
            for p in (pts[0], pts[-1]):
                self.circle(p, width / 2, fill=fill)

    def dashed(self, pts: Sequence[Point], fill: str, width: float = 1.0, dash: tuple[float, float] = (6, 5)) -> None:
        on, off = dash
        seg_left, drawing = on, True
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            pos = 0.0
            while pos < L - 1e-6:
                step = min(seg_left, L - pos)
                if drawing:
                    a = (x0 + (x1 - x0) * pos / L, y0 + (y1 - y0) * pos / L)
                    b = (x0 + (x1 - x0) * (pos + step) / L, y0 + (y1 - y0) * (pos + step) / L)
                    self.line([a, b], fill, width)
                pos += step
                seg_left -= step
                if seg_left <= 1e-6:
                    drawing = not drawing
                    seg_left = on if drawing else off

    def dotted(self, pts: Sequence[Point], fill: str, r: float = 1.2, gap: float = 6.0) -> None:
        carry = 0.0
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            pos = carry
            while pos <= L:
                self.circle((x0 + (x1 - x0) * pos / L, y0 + (y1 - y0) * pos / L), r, fill=fill)
                pos += gap
            carry = pos - L

    def rect(self, x0: float, y0: float, x1: float, y1: float, fill: str, radius: float = 0,
             corners: tuple[bool, bool, bool, bool] | None = None) -> None:
        if x1 - x0 <= 0 or y1 - y0 <= 0:
            return
        k = self.k
        box = (x0 * k, y0 * k, x1 * k, y1 * k)
        r = min(radius * k, (x1 - x0) * k / 2 - 1.5, (y1 - y0) * k / 2 - 1.5) if radius > 0 else 0
        if r >= 1:
            try:
                self.d.rounded_rectangle(box, radius=r, fill=fill, corners=corners)
            except TypeError:
                self.d.rounded_rectangle(box, radius=r, fill=fill)
        else:
            self.d.rectangle(box, fill=fill)

    def panel(self, x0: float, y0: float, x1: float, y1: float, hi: bool = False,
              radius: float = T.RADIUS) -> None:
        """Soft raised surface. Tone does the separating; no border, no shadow."""
        self.rect(x0, y0, x1, y1, T.SURFACE_HI if hi else T.SURFACE, radius=radius)

    def fade(self, pts: Sequence[Point], fill: str, y_top: float, y_bot: float,
             a_top: float = T.AREA_ALPHA, a_bot: float = 0.0) -> None:
        """Fill a polygon with a vertical alpha fade (area under a line)."""
        if len(pts) < 3 or y_bot <= y_top:
            return
        k = self.k
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        bx0, by0 = int(math.floor(min(xs) * k)), int(math.floor(min(ys) * k))
        bx1, by1 = int(math.ceil(max(xs) * k)) + 1, int(math.ceil(max(ys) * k)) + 1
        w, h = bx1 - bx0, by1 - by0
        if w <= 0 or h <= 0:
            return
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).polygon([(x * k - bx0, y * k - by0) for x, y in pts], fill=255)
        ramp = Image.new("L", (1, h))
        top, bot = y_top * k - by0, y_bot * k - by0
        for yy in range(h):
            t = min(1.0, max(0.0, (yy - top) / (bot - top)))
            ramp.putpixel((0, yy), int(round(255 * (a_top + (a_bot - a_top) * t))))
        ramp = ramp.resize((w, h))
        from PIL import ImageChops

        alpha = ImageChops.multiply(mask, ramp)
        self.img.paste(Image.new("RGB", (w, h), fill), (bx0, by0), alpha)

    def circle(self, c: Point, r: float, fill: str | None = None, outline: str | None = None, width: float = 0) -> None:
        k = self.k
        x, y = c
        box = ((x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k)
        self.d.ellipse(box, fill=fill, outline=outline, width=max(1, int(round(width * k))) if outline else 0)

    def ring(self, c: Point, r: float, fill: str, width: float) -> None:
        self.circle(c, r, outline=fill, width=width)

    def polygon(self, pts: Sequence[Point], fill: str) -> None:
        self.d.polygon(self._p(pts), fill=fill)

    def arc(self, c: Point, r: float, start: float, end: float, fill: str, width: float) -> None:
        """Angles in degrees, 0 = 12 o'clock, clockwise."""
        k = self.k
        x, y = c
        box = ((x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k)
        self.d.arc(box, start - 90, end - 90, fill=fill, width=max(1, int(round(width * k))))

    def triangle(self, cx: float, baseline: float, size: float, up: bool, fill: str) -> None:
        h = size * 0.86
        if up:
            pts = [(cx - size / 2, baseline), (cx + size / 2, baseline), (cx, baseline - h)]
        else:
            pts = [(cx - size / 2, baseline - h), (cx + size / 2, baseline - h), (cx, baseline)]
        self.polygon(pts, fill)

    def paste(self, im: Image.Image, box: tuple[float, float, float, float], radius: float = 0) -> None:
        k = self.k
        x0, y0, x1, y1 = box
        w, h = int((x1 - x0) * k), int((y1 - y0) * k)
        im = im.convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
        if radius:
            mask = Image.new("L", (w, h), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), radius=radius * k, fill=255)
            self.img.paste(im, (int(x0 * k), int(y0 * k)), mask)
        else:
            self.img.paste(im, (int(x0 * k), int(y0 * k)))

    # --------------------------------------------------------------- finalize
    def qa(self, margin: float = T.MARGIN, tolerance: float = 6) -> list[str]:
        out = []
        lo_x, hi_x = margin - tolerance, self.w - margin + tolerance
        for s, (x0, y0, x1, y1) in self.texts:
            if x0 < lo_x or x1 > hi_x or y0 < 24 or y1 > self.h - 20:
                out.append(f"text outside safe area: {s[:40]!r}")
        return out

    def finalize(self) -> Image.Image:
        size = (int(round(self.w * self.scale)), int(round(self.h * self.scale)))
        return self.img.resize(size, Image.Resampling.LANCZOS)
