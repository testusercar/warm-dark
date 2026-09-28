"""Reusable body blocks shared across templates."""
from __future__ import annotations

from typing import Any, Sequence

from . import tokens as T
from .canvas import Font
from .charts import share_bar
from .layout import Card, Item, draw_stack, gap, solve
from .text import Hero, Style, delta_width, draw_block, draw_delta, parse_delta, percents, text_block, typo


def hero(card: Card, value: str, size: float = 172, min_size: float = 88, align: str = "l",
         width: float | None = None, color: str = T.INK, name: str = "hero") -> Item:
    c = card.c
    w = width or card.cw
    h = Hero(c, typo(value), w, size=size, min_size=min_size, color=color)
    cap = h.cap

    def draw(x, y, ww, hh):
        bx = x + (ww if align == "r" else ww / 2 if align == "m" else 0)
        h.draw(bx, y + cap, align)

    return Item(cap + 2 + h.descent, draw, name=name)


def delta(card: Card, d: Any, note: str | None = None, size: float = 24, align: str = "l") -> Item | None:
    dd = parse_delta(d, note)
    if not dd:
        return None
    c = card.c
    f = Font.of("delta", size)
    nf = Font.of("dek", size * 0.92)

    def draw(x, y, w, h):
        bx = x + (w if align == "r" else w / 2 if align == "m" else 0)
        draw_delta(c, bx, y + f.cap, dd, f, nf, align=align)

    return Item(f.cap + 4, draw, name="delta")


def text(card: Card, s: str, font: str = "dek", color: str = T.MUTED, max_lines: int = 2,
         width: float | None = None, align: str = "l", strong_color: str = T.INK, name: str = "text",
         drop: int = 0, lh: float | None = None) -> Item | None:
    if not s:
        return None
    c = card.c
    f = Font.of(font)
    strong = Font("sans-semibold" if f.kind.startswith("sans") else "display-medium", f.size, f.lh)
    st = Style(f, color, strong, strong_color)
    w = width or card.cw
    lines, cut = text_block(c, s, st, w, max_lines)
    if cut:
        card.ctx.warnings.append(f"{name} truncated to {max_lines} lines — cut copy")
    l = lh or f.lh

    def draw(x, y, ww, hh):
        bx = x + (ww if align == "r" else ww / 2 if align == "m" else 0)
        draw_block(c, bx, y, lines, st, l, align)

    return Item(len(lines) * l, draw, name=name, drop=drop)


def eyebrow(card: Card, s: str, right: str | None = None, color: str = T.MUTED) -> Item:
    c = card.c
    f = Font.of("label")

    def draw(x, y, w, h):
        c.label((x, y + f.cap), s, color)
        if right:
            c.label((x + w, y + f.cap), right, T.QUIET, anchor="rs")

    return Item(f.cap + 2, draw, name="eyebrow")


def in_panel(card: Card, items: Sequence[Item | None], pad_x: float = T.PAD, pad_y: float = T.PAD,
             hi: bool = False, name: str = "panel", drop: int = 0, radius: float = T.RADIUS) -> Item:
    """Wrap a small stack of items (built at card.inner width) in a soft surface.

    Flex inside the panel is honoured: the panel grows with the card and hands
    the extra height to its inner springs/charts.
    """
    inner = [i for i in items if i is not None]
    base = sum(i.h for i in inner) + 2 * pad_y
    flex = max((i.flex for i in inner), default=0.0)
    caps = [i.max_h for i in inner if i.flex > 0]
    max_h = None
    if flex and all(cp is not None for cp in caps):
        max_h = base + sum((i.max_h or i.h) - i.h for i in inner if i.flex > 0)
    c = card.c

    def draw(x, y, w, h):
        c.panel(x, y, x + w, y + h, hi=hi, radius=radius)
        its, hs = solve(inner, h - 2 * pad_y, card.ctx.warnings)
        draw_stack(its, hs, x + pad_x, y + pad_y, w - 2 * pad_x)

    return Item(base, draw, flex=flex, max_h=max_h, name=name, drop=drop)


def callout(card: Card, label: str, body: str, font: str = "quote", right: str | None = None,
            max_lines: int = 3, hi: bool = False, name: str = "callout") -> Item | None:
    """Label + one short passage in a surface: bottom lines, next actions, why-it-matters."""
    if not body:
        return None
    txt = text(card, body, font, T.INK, max_lines, width=card.inner, name=name)
    return in_panel(card, [eyebrow(card, label, right), gap(14), txt], pad_y=26, hi=hi, name=name)


def facts(card: Card, items: Sequence[dict[str, Any]], cols: int | None = None, value_font: str = "stat-s",
          name: str = "facts", drop: int = 0, panel: bool = True) -> Item | None:
    """Up to four label/value stats. In v3 they sit in one soft surface with quiet dividers."""
    items = [i for i in (items or []) if i]
    if not items:
        return None
    if len(items) > 4:
        card.ctx.warnings.append("facts capped at 4")
        items = items[:4]
    c = card.c
    n = cols or len(items)
    lf = Font.of("label")
    vf = Font.of(value_font)
    sf = Font.of("whisper")
    px, py = (T.PAD, 24) if panel else (0, 0)
    colgap = 2 * 22 if panel else 28
    avail = card.cw - 2 * px
    colw = (avail - (n - 1) * colgap) / n
    has_sub = any(i.get("sub") or i.get("delta") for i in items)
    vfs = []
    for it in items:
        v = typo(it.get("value", ""))
        f = vf
        while c.measure(v, f) > colw and f.size > 20:
            f = f.sized(f.size - 1)
        vfs.append(f)
    inner_h = lf.cap + 14 + vf.cap + (13 + sf.cap + 3 if has_sub else 3)
    h = inner_h + 2 * py

    def draw(x, y, w, hh):
        if panel:
            c.panel(x, y, x + w, y + hh)
        ix, iw = x + px, w - 2 * px
        top = y + (hh - inner_h) / 2
        cw = (iw - (n - 1) * colgap) / n
        for k, it in enumerate(items):
            cx = ix + k * (cw + colgap)
            if panel and k:
                dx = cx - colgap / 2
                c.line([(dx, top + 2), (dx, top + inner_h - 2)], T.DIVIDER, 1)
            c.label((cx, top + lf.cap), typo(it.get("label", "")))
            vy = top + lf.cap + 14 + vf.cap
            col = T.INK
            if it.get("tone") == "muted":
                col = T.MUTED
            elif it.get("tone") == "positive":
                col = T.OLIVE
            c.text((cx, vy), typo(it.get("value", "")), vfs[k], col)
            sy = vy + 13 + sf.cap
            if it.get("delta"):
                d = parse_delta(it["delta"], it.get("sub"))
                if d:
                    draw_delta(c, cx, sy, d, Font.of("axis-strong"), Font.of("whisper"))
            elif it.get("sub"):
                sub = typo(it["sub"])
                lines, _ = text_block(c, sub, Style(sf, T.QUIET), cw, 1)
                draw_block(c, cx, sy - sf.baseline_in(), lines, Style(sf, T.QUIET))

    return Item(h, draw, name=name, drop=drop)


def composition(card: Card, parts: Sequence[dict[str, Any]], height: float = 10, legend: bool = True,
                label: str | None = None, name: str = "composition", drop: int = 0,
                width: float | None = None) -> Item | None:
    parts = [p for p in (parts or []) if (p.get("num") or 0) > 0]
    if not parts:
        return None
    c = card.c
    w_all = width or card.cw
    f = Font.of("small")
    fnum = Font.of("small-num")
    r = 4.5
    rows: list[list[tuple[str, str, int]]] = [[]]
    row_w = 0.0
    entries = []
    pcts = percents([p["num"] for p in parts])
    for i, p in enumerate(parts):
        pct = f"{pcts[i]}%"
        lab = typo(p.get("label", ""))
        ew = 2 * r + 10 + c.measure(lab, f) + 8 + c.measure(pct, fnum) + 28
        entries.append((lab, pct, i, ew))
    for lab, pct, i, ew in entries:
        if row_w + ew > w_all and rows[-1]:
            rows.append([])
            row_w = 0
        rows[-1].append((lab, pct, i))
        row_w += ew
    lab_h = (Font.of("label").cap + 18) if label else 0
    h = lab_h + height + (22 + len(rows) * 32 - 6 if legend else 0)

    def draw(x, y, w, hh):
        yy = y
        if label:
            c.label((x, yy + Font.of("label").cap), label)
            yy += lab_h
        share_bar(c, x, yy, w, height, [p["num"] for p in parts])
        yy += height + 22
        if legend:
            for row in rows:
                cx = x
                base = yy + f.cap + 2
                for lab, pct, i in row:
                    col = T.RAMP[min(i, len(T.RAMP) - 1)]
                    c.circle((cx + r, base - f.cap / 2), r, fill=col)
                    cx += 2 * r + 10
                    c.text((cx, base), lab, f, T.SOFT)
                    cx += c.measure(lab, f) + 8
                    c.text((cx, base), pct, fnum, T.QUIET)
                    cx += c.measure(pct, fnum) + 28
                yy += 32

    return Item(h, draw, name=name, drop=drop)


def image(card: Card, src: str | None, min_h: float = 180, anchor: str = "top") -> Item | None:
    if not src:
        return None
    from pathlib import Path

    from PIL import Image

    p = Path(str(src))
    if not p.is_file():
        card.ctx.warnings.append(f"image not found: {src}")
        return None
    try:
        im = Image.open(p)
        im.load()
    except Exception:
        card.ctx.warnings.append(f"image unreadable: {src}")
        return None
    c = card.c

    def draw(x, y, w, h):
        iw, ih = im.size
        s = min(w / iw, h / ih)
        nw, nh = iw * s, ih * s
        bx = x + (w - nw) / 2
        by = y if anchor == "top" else y + (h - nh) / 2
        c.paste(im, (bx, by, bx + nw, by + nh), radius=T.RADIUS_S + 4)

    return Item(min_h, draw, flex=1, name="image")


def compact_items(items: Sequence[Item | None]) -> list[Item]:
    return [i for i in items if i is not None]


def delta_w(card: Card, d: Any, size: float = 24) -> float:
    dd = parse_delta(d)
    return delta_width(card.c, dd, Font.of("delta", size)) if dd else 0.0


__all__ = ["hero", "delta", "text", "eyebrow", "facts", "composition", "image", "compact_items", "gap", "delta_w",
           "in_panel", "callout"]
