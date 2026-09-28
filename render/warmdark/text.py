"""Typesetting helpers: rich runs, wrapping, hero numerals, deltas, number formats."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from . import tokens as T
from .canvas import Canvas, Font

MINUS = "\u2212"

# ------------------------------------------------------------------ numbers


def typo(s: Any) -> str:
    """Typographic polish: real minus signs, no double spaces."""
    s = "" if s is None else str(s)
    s = re.sub(r"(^|[\s(\[/])-(?=\d|[$€£¥]|C\$|US\$|A\$)", lambda m: m.group(1) + MINUS, s)
    return re.sub(r"[ \t]{2,}", " ", s).strip()


def compact(v: float) -> str:
    a = abs(v)
    if a < 1000:
        s = f"{a:,.0f}" if a >= 100 or a == int(a) else f"{a:,.1f}"
    elif a < 10_000:
        s = f"{a / 1000:.1f}".rstrip("0").rstrip(".") + "k"
    elif a < 1_000_000:
        s = f"{a / 1000:.0f}k"
    else:
        s = f"{a / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    return s


def fmt(v: float | None, spec: str | None = None, signed: bool = False) -> str:
    """Format with a Python format string; ``{:k}`` means compact (4.2k).

    Negative numbers put a real minus before any prefix: −C$1,938.
    """
    if v is None:
        return "—"
    spec = spec or "{:,.0f}"
    neg = v < 0
    a = abs(v)
    if "{:k}" in spec:
        body = spec.replace("{:k}", compact(a))
    else:
        try:
            body = spec.format(a)
        except (ValueError, IndexError):
            body = f"{a:,.0f}"
    if neg and round(a, 6) != 0:
        return MINUS + body
    if signed and a != 0:
        return "+" + body
    return body


def percents(nums: list[float]) -> list[int]:
    """Whole percentages that always sum to 100 (largest remainder)."""
    total = sum(max(0.0, n) for n in nums) or 1.0
    raw = [max(0.0, n) / total * 100 for n in nums]
    out = [int(r) for r in raw]
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - out[i], reverse=True)[: 100 - sum(out)]:
        out[i] += 1
    return out


def nice_step(span: float, target: int = 4) -> float:
    import math

    if span <= 0:
        return 1.0
    raw = span / max(1, target)
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


def nice_ticks(lo: float, hi: float, target: int = 4) -> list[float]:
    import math

    step = nice_step(hi - lo, target)
    start = math.floor(lo / step) * step
    ticks = []
    v = start
    while v <= hi + step * 0.001:
        if v >= lo - step * 0.001:
            ticks.append(round(v, 10))
        v += step
    return ticks


# ---------------------------------------------------------------- rich text

_RICH = re.compile(r"(\*\*.+?\*\*|\{\{.+?\}\})")


@dataclass
class Run:
    text: str
    style: str  # normal | strong | pos | neg


def parse_rich(s: str) -> list[Run]:
    runs: list[Run] = []
    for part in _RICH.split(typo(s)):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            runs.append(Run(part[2:-2], "strong"))
        elif part.startswith("{{") and part.endswith("}}"):
            inner = typo(part[2:-2])
            runs.append(Run(inner, "neg" if inner.startswith((MINUS, "-")) else "pos"))
        else:
            runs.append(Run(part, "normal"))
    return runs


def plain(s: str) -> str:
    return "".join(r.text for r in parse_rich(s))


@dataclass
class Style:
    font: Font
    color: str = T.INK
    strong: Font | None = None
    strong_color: str | None = None

    def font_for(self, style: str) -> Font:
        if style in ("strong", "pos", "neg") and self.strong:
            return self.strong
        return self.font

    def color_for(self, style: str) -> str:
        if style == "pos":
            return T.OLIVE
        if style == "neg":
            return T.INK
        if style == "strong":
            return self.strong_color or T.INK
        return self.color


Line = list[tuple[str, Font, str]]


def wrap_rich(c: Canvas, s: str, st: Style, max_w: float) -> list[Line]:
    words: list[tuple[str, str, bool]] = []  # (word, style, space_before)
    space = False
    for run in parse_rich(s):
        for p in re.split(r"(\s+)", run.text):
            if not p:
                continue
            if p.isspace():
                space = True
                continue
            words.append((p, run.style, space and bool(words)))
            space = False
    lines: list[Line] = []
    cur: Line = []
    cur_w = 0.0
    for w, style, sp in words:
        f = st.font_for(style)
        col = st.color_for(style)
        piece = (" " if sp and cur else "") + w
        pw = c.measure(piece, f)
        if cur and cur_w + pw > max_w:
            lines.append(cur)
            cur, cur_w = [(w, f, col)], c.measure(w, f)
        else:
            cur.append((piece, f, col))
            cur_w += pw
    if cur:
        lines.append(cur)
    if len(lines) > 1 and len(lines[-1]) == 1 and len(lines[-2]) >= 2:
        t, f, col = lines[-2].pop()
        t0, f0, c0 = lines[-1][0]
        cand = [(t.lstrip(), f, col), (" " + t0.lstrip(), f0, c0)]
        if sum(c.measure(p, ff) for p, ff, _ in cand) <= max_w:
            lines[-1] = cand
        else:
            lines[-2].append((t, f, col))
    return lines


def line_width(c: Canvas, line: Line) -> float:
    return sum(c.measure(t, f) for t, f, _ in line)


def draw_line(c: Canvas, x: float, baseline: float, line: Line, align: str = "l") -> float:
    w = line_width(c, line)
    if align == "r":
        x -= w
    elif align == "m":
        x -= w / 2
    for t, f, col in line:
        c.text((x, baseline), t, f, col)
        x += c.measure(t, f)
    return w


def ellipsize(c: Canvas, line: Line, max_w: float) -> Line:
    line = list(line)
    while line and line_width(c, line) + c.measure("…", line[-1][1]) > max_w:
        t, f, col = line[-1]
        t = t[:-1].rstrip()
        if t:
            line[-1] = (t, f, col)
        else:
            line.pop()
    if line:
        t, f, col = line[-1]
        line[-1] = (t + "…", f, col)
    return line


def text_block(c: Canvas, s: str, st: Style, max_w: float, max_lines: int = 99) -> tuple[list[Line], bool]:
    lines = wrap_rich(c, s, st, max_w)
    cut = len(lines) > max_lines
    if cut:
        lines = lines[:max_lines]
        lines[-1] = ellipsize(c, lines[-1], max_w)
    return lines, cut


def draw_block(c: Canvas, x: float, y: float, lines: list[Line], st: Style, lh: float | None = None,
               align: str = "l") -> float:
    """Draw wrapped lines with top at y. Returns total height."""
    lh = lh or st.font.lh
    base = st.font.baseline_in(lh)
    for i, ln in enumerate(lines):
        draw_line(c, x, y + i * lh + base, ln, align)
    return len(lines) * lh


def fit_single(c: Canvas, s: str, f: Font, max_w: float, min_size: float) -> Font:
    size = f.size
    while size > min_size and c.measure(s, f.sized(size)) > max_w:
        size -= 1
    return f.sized(size)


# ------------------------------------------------------------- hero numerals

_NUMERIC = re.compile(r"[\d.,:]+|[+\u2212\-±≈~](?=\d)")


def split_value(value: str) -> list[tuple[str, bool]]:
    """Split "C$140,022" -> [("C$", unit), ("140,022", num)]; "7h 12m" alternates."""
    value = typo(value)
    out: list[tuple[str, bool]] = []
    i = 0
    for m in _NUMERIC.finditer(value):
        if m.start() > i:
            out.append((value[i:m.start()], False))
        out.append((m.group(), True))
        i = m.end()
    if i < len(value):
        out.append((value[i:], False))
    merged: list[tuple[str, bool]] = []
    for t, num in out:
        if merged and merged[-1][1] == num:
            merged[-1] = (merged[-1][0] + t, num)
        else:
            merged.append((t, num))
    if not any(ch.isdigit() for ch in value):
        return [(value, True)]
    return merged or [(value, True)]


class Hero:
    """Big Inter Display numeral with a raised, muted currency prefix and small baseline suffix."""

    UNIT_RATIO = 0.40

    def __init__(self, c: Canvas, value: str, max_w: float, size: float = 172, min_size: float = 88,
                 kind: str | None = None, unit_color: str = T.MUTED, color: str = T.INK):
        self.c = c
        self.parts = split_value(value)
        self.color, self.unit_color = color, unit_color
        self.kind = kind or T.TYPE["display"][0]
        s = size
        while s > min_size and self._width(s) > max_w:
            s -= 2
        self.size = s
        self.width = self._width(s)

    def _fonts(self, s: float) -> tuple[Font, Font]:
        big = Font(self.kind, s, s)
        longest = max((len(t.strip()) for t, num in self.parts if not num), default=0)
        ratio = self.UNIT_RATIO if longest <= 2 else self.UNIT_RATIO * 0.84
        unit = Font("display", max(18, s * ratio))
        return big, unit

    def _is_prefix(self, i: int) -> bool:
        return not any(num and any(ch.isdigit() for ch in t) for t, num in self.parts[:i])

    def _width(self, s: float) -> float:
        big, unit = self._fonts(s)
        w = 0.0
        for i, (t, num) in enumerate(self.parts):
            if num:
                w += self.c.measure(t, big)
            else:
                w += self.c.measure(t.strip(), unit) + big.size * (0.03 if self._is_prefix(i) else 0.05)
                if not self._is_prefix(i) and i < len(self.parts) - 1:
                    w += big.size * 0.07
        return w

    @property
    def cap(self) -> float:
        return self._fonts(self.size)[0].cap

    @property
    def descent(self) -> float:
        """Extra room below the baseline for descending glyphs (Ship, Sept, 1,284)."""
        s = "".join(t for t, num in self.parts if num)
        if any(ch in "gjpqyQ" for ch in s):
            return self.size * 0.2
        if "," in s or ";" in s:
            return self.size * 0.08
        return 0.0

    def draw(self, x: float, baseline: float, align: str = "l") -> tuple[float, float]:
        big, unit = self._fonts(self.size)
        if align == "r":
            x -= self.width
        elif align == "m":
            x -= self.width / 2
        x0 = x
        for i, (t, num) in enumerate(self.parts):
            if num:
                self.c.text((x, baseline), t, big, self.color)
                x += self.c.measure(t, big)
            else:
                t = t.strip()
                if self._is_prefix(i):
                    self.c.text((x, baseline - big.cap + unit.cap), t, unit, self.unit_color)
                    x += self.c.measure(t, unit) + big.size * 0.03
                else:
                    x += big.size * 0.05
                    self.c.text((x, baseline), t, unit, self.unit_color)
                    x += self.c.measure(t, unit)
                    if i < len(self.parts) - 1:
                        x += big.size * 0.07
        return x0, x


# -------------------------------------------------------------------- deltas


@dataclass
class Delta:
    value: str
    direction: str  # up | down | flat
    good: bool | None
    note: str = ""

    @property
    def color(self) -> str:
        """Olive = good (either direction). Bad or neutral moves = ink. Only flat is muted."""
        if self.good is True:
            return T.OLIVE
        if self.direction == "flat":
            return T.MUTED
        return T.INK


def parse_delta(d: Any, note: str | None = None) -> Delta | None:
    if d in (None, "", {}):
        return None
    polarity = "up_good"
    good = None
    if isinstance(d, dict):
        value = typo(d.get("value", ""))
        note = d.get("note", note)
        polarity = d.get("polarity", polarity)
        good = d.get("good")
        direction = d.get("dir") or d.get("direction")
    else:
        value, direction = typo(d), None
    if not direction:
        if value.startswith("+") or value.startswith("▲"):
            direction = "up"
        elif value.startswith((MINUS, "-", "▼")):
            direction = "down"
        else:
            direction = "flat"
    value = value.lstrip("▲▼ ")
    if good is None and direction != "flat" and polarity != "neutral":
        good = (direction == "up") == (polarity != "down_good")
    return Delta(value, direction, good, typo(note or ""))


def draw_delta(c: Canvas, x: float, baseline: float, d: Delta, f: Font | None = None,
               note_font: Font | None = None, align: str = "l") -> float:
    """▲ +12% vs prior. Returns width. Triangles are vector, not glyphs."""
    f = f or Font.of("delta")
    nf = note_font or Font.of("dek", f.size * 0.92)
    tri = f.cap * 0.7
    gap = f.size * 0.3
    w_val = c.measure(d.value, f)
    w_note = c.measure(d.note, nf) if d.note else 0
    total = (tri + gap if d.direction != "flat" else 0) + w_val + (gap * 1.4 + w_note if d.note else 0)
    if align == "r":
        x -= total
    elif align == "m":
        x -= total / 2
    if d.direction != "flat":
        c.triangle(x + tri / 2, baseline - (f.cap - tri * 0.86) / 2, tri, d.direction == "up", d.color)
        x += tri + gap
    c.text((x, baseline), d.value, f, d.color)
    x += w_val
    if d.note:
        c.text((x + gap * 1.4, baseline), d.note, nf, T.MUTED)
    return total


def delta_width(c: Canvas, d: Delta, f: Font | None = None, note_font: Font | None = None) -> float:
    f = f or Font.of("delta")
    nf = note_font or Font.of("dek", f.size * 0.92)
    tri = f.cap * 0.7
    gap = f.size * 0.3
    return ((tri + gap) if d.direction != "flat" else 0) + c.measure(d.value, f) + (
        gap * 1.4 + c.measure(d.note, nf) if d.note else 0)
