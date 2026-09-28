"""Card chrome (masthead, title, footer) and a flex vertical stack."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from PIL import Image

from . import tokens as T
from .canvas import Canvas, Font
from .text import Style, draw_block, draw_line, ellipsize, text_block, typo, wrap_rich

DrawFn = Callable[[float, float, float, float], None]


@dataclass
class Item:
    h: float = 0.0
    draw: DrawFn | None = None
    flex: float = 0.0
    max_h: float | None = None
    drop: int = 0  # >0: may be dropped on overflow, highest first
    name: str = ""


def gap(h: float) -> Item:
    return Item(h)


def spring(weight: float = 1.0, max_h: float | None = None) -> Item:
    return Item(0, None, flex=weight, max_h=max_h)


def solve(items: list[Item], avail: float, warnings: list[str] | None = None) -> tuple[list[Item], list[float]]:
    """Drop optional items until the fixed heights fit, then share the rest by flex."""
    items = list(items)
    while sum(i.h for i in items) > avail:
        droppable = [i for i in items if i.drop > 0]
        if not droppable:
            if warnings is not None:
                warnings.append(
                    f"content overflows by {sum(i.h for i in items) - avail:.0f}px — cut copy or split card")
            break
        victim = max(droppable, key=lambda i: i.drop)
        if warnings is not None:
            warnings.append(f"dropped '{victim.name or 'block'}' to fit")
        items.remove(victim)
    free = max(0.0, avail - sum(i.h for i in items))
    heights = [i.h for i in items]
    flex = [i for i in range(len(items)) if items[i].flex > 0]
    while free > 0.5 and flex:
        tot = sum(items[i].flex for i in flex)
        nxt = []
        used = 0.0
        for i in flex:
            share = free * items[i].flex / tot
            cap = items[i].max_h
            if cap is not None and heights[i] + share >= cap:
                used += cap - heights[i]
                heights[i] = cap
            else:
                heights[i] += share
                used += share
                nxt.append(i)
        free -= used
        if len(nxt) == len(flex):
            break
        flex = nxt
    return items, heights


def draw_stack(items: list[Item], heights: list[float], x: float, y: float, w: float) -> None:
    for it, h in zip(items, heights):
        if it.draw:
            it.draw(x, y, w, h)
        y += h


@dataclass
class Ctx:
    agent: str
    domain: str
    date: str | None
    footer: str | None
    index: int = 0
    total: int = 0
    series: bool = False
    warnings: list[str] = field(default_factory=list)


class Card:
    """One card: canvas + chrome. Templates add body items and call finish()."""

    def __init__(self, ctx: Ctx, card: dict[str, Any], scale: float = 1.0):
        self.ctx = ctx
        self.card = card
        fmt = str(card.get("format") or "portrait").lower()
        self.landscape = fmt.startswith("land")
        self.c = Canvas(T.LANDSCAPE if self.landscape else T.PORTRAIT, scale)
        self.W, self.H = self.c.w, self.c.h
        self.M = T.MARGIN
        self.x0, self.x1 = self.M, self.W - self.M
        self.cw = self.x1 - self.x0
        self.top = T.TITLE_TOP
        self.bottom = self.H - T.BODY_BOTTOM_GAP
        self.inner = self.cw - 2 * T.PAD  # usable width inside a full-width surface
        self._masthead()
        self._footer()

    # ----------------------------------------------------------- chrome
    def _masthead(self) -> None:
        c, ctx = self.c, self.ctx
        agent = typo(self.card.get("agent") or ctx.agent)
        domain = typo(self.card.get("domain") or ctx.domain)
        date = typo(self.card.get("date") or ctx.date or "")
        f = Font.of("meta")
        fd = Font("sans", f.size, f.lh)
        y = T.MAST_BASELINE
        c.text((self.x0, y), agent, f, T.SOFT)
        if domain:
            aw = c.measure(agent, f)
            c.text((self.x0 + aw, y), f"  ·  {domain}", fd, T.QUIET)
        if date:
            c.text((self.x1, y), date, fd, T.QUIET, anchor="rs")

    def _footer(self) -> None:
        c, ctx, card = self.c, self.ctx, self.card
        y = self.H - T.FOOT_FROM_BOTTOM
        f = Font.of("whisper")
        right_w = 0.0
        if ctx.series and ctx.total > 1:
            r, g, pill = 3.0, 10, 18
            right_w = (ctx.total - 1) * g + 2 * r + (pill - 2 * r)
            cx = self.x1 - right_w
            for i in range(ctx.total):
                if i == ctx.index:
                    c.rect(cx, y - 5 - r, cx + pill, y - 5 + r, T.INK, radius=r)
                    cx += pill + g - 2 * r
                else:
                    c.circle((cx + r, y - 5), r, fill=T.ASH)
                    cx += g
        whisper = typo(card.get("footer") or ctx.footer or "fleet brief")
        partial = card.get("partial")
        x = self.x0
        if partial:
            note = partial if isinstance(partial, str) else partial.get("note", "")
            ok, tot = (partial.get("ok"), partial.get("of")) if isinstance(partial, dict) else (None, None)
            label = "Partial"
            if ok is not None and tot:
                label = f"Partial {ok}/{tot}"
            c.ring((x + 5, y - 5), 4.5, T.MUTED, 1.4)
            x += 16
            lbl = f"**{label}**" + (f" · {typo(note)}" if note else "")
            whisper = lbl + "  ·  " + whisper if whisper and whisper != "fleet brief" else lbl
        st = Style(f, T.QUIET, Font("sans-medium", f.size, f.lh), T.SOFT)
        lines = wrap_rich(c, whisper, st, 10_000)
        max_w = self.x1 - x - (right_w + 24 if right_w else 0)
        ln = lines[0] if lines else []
        if ln and sum(c.measure(t, ff) for t, ff, _ in ln) > max_w:
            ln = ellipsize(c, ln, max_w)
        draw_line(c, x, y, ln)

    # ------------------------------------------------------------ title
    def title_items(self, title: str | None = None, dek: str | None = None, size: str = "title",
                    dek_lines: int = 2, width: float | None = None) -> list[Item]:
        c = self.c
        title = typo(title if title is not None else self.card.get("title") or "")
        dek = typo(dek if dek is not None else self.card.get("dek") or "")
        w = width or self.cw
        items: list[Item] = []
        if title:
            base = Font.of("title-l" if self.landscape else size)
            f = base
            lines = []
            for sz in (base.size, base.size - 4, base.size - 8, base.size - 12):
                f = base.sized(sz)
                lines = wrap_rich(c, title, Style(f), w)
                if len(lines) <= (1 if sz == base.size and len(title) < 22 else 2):
                    break
            if len(lines) > 3:
                self.ctx.warnings.append("title wraps past 3 lines — shorten it")
                lines = lines[:3]
                lines[-1] = ellipsize(c, lines[-1], w)
            lh = f.size * 1.1
            st = Style(f)

            def draw_title(x, y, ww, hh, lines=lines, st=st, lh=lh):
                draw_block(c, x, y, lines, st, lh)

            items.append(Item(len(lines) * lh, draw_title, name="title"))
        if dek:
            st = Style(Font.of("dek"), T.MUTED, Font("sans-medium", 22, 31), T.SOFT)
            lines, cut = text_block(c, dek, st, w, dek_lines)
            if cut:
                self.ctx.warnings.append("dek truncated — cut copy")
            items.append(gap(8))

            def draw_dek(x, y, ww, hh, lines=lines, st=st):
                draw_block(c, x, y, lines, st)

            items.append(Item(len(lines) * st.font.lh, draw_dek, name="dek"))
        return items

    # ------------------------------------------------------------ stack
    def stack(self, items: list[Item], x: float | None = None, y0: float | None = None,
              w: float | None = None, y1: float | None = None) -> None:
        x = self.x0 if x is None else x
        w = self.cw if w is None else w
        y0 = self.top if y0 is None else y0
        y1 = self.bottom if y1 is None else y1
        items, heights = solve(items, y1 - y0, self.ctx.warnings)
        draw_stack(items, heights, x, y0, w)

    def dead_space(self) -> float:
        """Tallest band of empty canvas or empty surface inside the body, in card px (pixel scan)."""
        from PIL import ImageChops

        small = self.c.img.resize((self.W // 3, self.H // 3))
        diffs = [ImageChops.difference(small, Image.new("RGB", small.size, col)).convert("L")
                 for col in (T.CANVAS, T.SURFACE, T.SURFACE_HI)]
        diff = diffs[0]
        for dd in diffs[1:]:
            diff = ImageChops.darker(diff, dd)
        w, h = diff.size
        px = diff.load()
        y0, y1 = int(self.top / 3), int(self.bottom / 3)
        run = best = 0
        for y in range(y0, y1):
            if max(px[x, y] for x in range(0, w, 2)) > 10:
                run = 0
            else:
                run += 1
                best = max(best, run)
        return best * 3.0

    def finish(self):
        self.ctx.warnings.extend(self.c.qa(self.M))
        gap_px = self.dead_space()
        if gap_px > self.H * 0.26:
            self.ctx.warnings.append(
                f"dead space: {gap_px:.0f}px empty band — add facts/spark/timeline, an image, or pick a denser type")
        return self.c.finalize()
