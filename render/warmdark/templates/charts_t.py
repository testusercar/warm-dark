"""Chart templates: line, area, bars, allocation, breakeven, heatmap, funnel."""
from __future__ import annotations

from typing import Any

from .. import blocks as B
from .. import tokens as T
from ..canvas import Font
from ..charts import line_chart
from ..layout import Card, Item, gap, spring
from ..text import Hero, draw_delta, parse_delta, percents, typo
from . import template


def _headline_row(card: Card, value: str, d: Any, note: str | None = None, size: float = 110,
                  right: dict[str, Any] | None = None) -> Item:
    """Hero number on the left, delta beneath; optional right-aligned stat."""
    c = card.c
    h = Hero(c, typo(value), card.cw * (0.6 if right else 1), size=size, min_size=64)
    dd = parse_delta(d, note)
    f = Font.of("delta")
    nf = Font.of("dek", 22)
    height = h.cap + (22 + f.cap if dd else 0) + 4

    def draw(x, y, w, hh):
        h.draw(x, y + h.cap)
        if dd:
            draw_delta(c, x, y + h.cap + 22 + f.cap, dd, f, nf)
        if right:
            lf = Font.of("label")
            sf = Font.of("stat-s")
            c.label((x + w, y + lf.cap + 4), typo(right.get("label", "")), T.QUIET, anchor="rs")
            c.text((x + w, y + lf.cap + 18 + sf.cap), typo(right.get("value", "")), sf,
                   T.MUTED if right.get("tone") != "ink" else T.INK, anchor="rs")
            if right.get("sub"):
                c.text((x + w, y + lf.cap + 18 + sf.cap + 28), typo(right["sub"]), Font.of("whisper"), T.QUIET,
                       anchor="rs")

    return Item(height, draw, name="headline")


def _chart_item(card: Card, spec: dict[str, Any], min_h: float = 320, flex: float = 1.0,
                bleed: bool = False) -> Item:
    c = card.c

    def draw(x, y, w, h):
        s = dict(spec)
        if bleed:
            s["bleed"] = (0, card.W)
        line_chart(c, (x, y, w, h), s)

    return Item(min_h, draw, flex=flex, name="chart")


@template("breakeven", "break_even", "asset_vs_cost")
def breakeven(card: Card) -> None:
    d = card.card
    items = card.title_items()
    price = d.get("price") or {}
    vals = price.get("values") or []
    steps = d.get("steps") or []
    step_pts = [[s["at"], s["value"]] for s in steps]
    markers = [{"at": s["at"], "value": s["value"], "label": s.get("label")} for s in steps if s.get("label")]
    spec = {
        "series": [{"values": vals, "role": "current", "name": price.get("name", "spot"),
                    "label": price.get("label")}],
        "steps": [{"points": step_pts, "label": d.get("be_label"), "name": d.get("be_name", "break-even")}]
        if step_pts else [],
        "refs": d.get("refs") or [],
        "x": price.get("x"),
        "x_ticks": price.get("x_ticks"),
        "fmt": d.get("fmt", "{:,.0f}"),
        "axis_fmt": d.get("axis_fmt"),
        "markers": markers,
        "annotations": d.get("annotations") or [],
        "smooth": True,
    }
    head = _headline_row(card, d.get("value", ""), d.get("delta"), d.get("delta_note"), size=d.get("size", 120))
    body: list[Item] = [spring(0.5), head, gap(36), _chart_item(card, spec, 360)]
    f = B.facts(card, d.get("facts") or [])
    if f:
        body += [gap(40), f]
    card.stack(items + body)


def _legend_item(card: Card, entries: list[tuple[str, str]]) -> Item:
    """Inline swatch legend — only for stacked/multi-series bars where direct labels can't work."""
    c = card.c
    f = Font.of("small")

    def draw(x, y, w, h):
        cx = x
        base = y + f.cap + 2
        for lab, col in entries:
            c.circle((cx + 5, base - f.cap / 2), 5, fill=col)
            cx += 18
            c.text((cx, base), typo(lab), f, T.SOFT)
            cx += c.measure(typo(lab), f) + 26

    return Item(f.cap + 6, draw, name="legend")


@template("line", "timeseries", "dual_line", "trend")
def line(card: Card) -> None:
    d = card.card
    items = card.title_items()
    body: list[Item] = []
    if d.get("value"):
        body += [gap(34), _headline_row(card, d["value"], d.get("delta"), d.get("delta_note"),
                                        size=d.get("size", 104 if not card.landscape else 88),
                                        right=d.get("aside"))]
    spec = {k: d[k] for k in ("series", "x", "x_ticks", "fmt", "axis_fmt", "annotations", "refs", "steps",
                              "zero", "y_min", "y_max", "smooth", "area", "ticks", "markers") if k in d}
    body += [gap(30), _chart_item(card, spec, 300)]
    f = B.facts(card, d.get("facts") or [], drop=1)
    if f:
        body += [gap(36), f]
    card.stack(items + body)


@template("area", "spark", "annotated")
def area(card: Card) -> None:
    d = card.card
    items = card.title_items()
    head = B.compact_items([
        B.hero(card, d.get("value", "—"), size=d.get("size", 170)),
        gap(22),
        B.delta(card, d.get("delta"), d.get("delta_note")),
        gap(12) if d.get("delta") else None,
        B.text(card, d.get("context", ""), "dek", T.MUTED, 2, name="context"),
    ])
    vals = d.get("values") or []
    spec = {
        "series": [{"values": vals, "role": "current", "end_label": False}],
        "x": d.get("x"),
        "x_ticks": d.get("x_ticks"),
        "grid": False,
        "area": True,
        "end_labels": False,
        "end_dot": True,
        "positive": d.get("positive", False),
        "annotations": d.get("callouts") or d.get("annotations") or [],
        "refs": [{**r, "label": False} for r in (d.get("refs") or [])],
        "zero": d.get("zero", False),
        "pad": 0.06,
    }
    c = card.c

    def chart(x, y, w, h):
        geo = line_chart(c, (x, y, w, h), spec)
        nums = [v for v in vals if v is not None]
        k = max(2, len(nums) // 6)
        for r in d.get("refs") or []:
            rv = r["value"]
            ry = geo["Y"](rv)
            left, right = nums[:k], nums[-k:]
            use_left = min(abs(v - rv) for v in left) >= min(abs(v - rv) for v in right)
            seg = left if use_left else right
            above = sum(v > rv for v in seg) < len(seg) / 2
            ly = ry - 9 if above else ry + 22
            lx, anchor = (card.x0, "ls") if use_left else (card.x1, "rs")
            c.text((lx, ly), typo(r.get("label", "")), Font.of("whisper", 15), T.QUIET, anchor=anchor)

    body = [spring(0.5)] + head + [gap(30), Item(380, chart, flex=1, name="chart")]
    f = B.facts(card, d.get("facts") or [], drop=1)
    if f:
        body += [gap(28), f]
    card.stack(items + body)


@template("bars", "bar", "stacked", "category")
def bars(card: Card) -> None:
    from ..charts import hbar_rows, vbars

    d = card.card
    if str(d.get("type", "")).lower() == "stacked":
        d = card.card = {**d, "stacked": True}
    c = card.c
    items = card.title_items()
    cats = d.get("categories") or []
    series = d.get("series") or []
    orient = d.get("orientation") or ("h" if (len(cats) > 7 and not card.landscape) or d.get("horizontal") else "v")
    body: list[Item] = []
    if d.get("value"):
        body += [gap(30), _headline_row(card, d["value"], d.get("delta"), d.get("delta_note"),
                                        size=d.get("size", 104), right=d.get("aside"))]
    if d.get("stacked") or len(series) > 1:
        ents = []
        for k, s in enumerate(series):
            if d.get("stacked"):
                col = T.RAMP[min(k, len(T.RAMP) - 1)]
            else:
                col = T.INK if s.get("role", "current" if k == len(series) - 1 else "prior") == "current" else T.ASH
            ents.append((s.get("name", ""), col))
        body += [gap(28), _legend_item(card, ents)]
    if orient == "h":
        vals = series[0]["values"] if series else []
        hi = d.get("highlight")
        rows = []
        disp = series[0].get("labels") if series else None
        for i, (k, v) in enumerate(zip(cats, vals)):
            rows.append({"label": k, "num": v, "value": (disp[i] if disp else None) or fmt_value(v, d.get("fmt")),
                         "highlight": ("positive" if d.get("highlight_positive") else True)
                         if (hi == i or hi == k) else None,
                         "sub": (d.get("subs") or [None] * len(cats))[i]})
        rows = rows[:8]
        rh = 66

        def draw_h(x, y, w, h, rows=rows):
            hbar_rows(c, (x, y, w, h), rows, row_h=rh)

        body += [gap(40), Item(len(rows) * rh, draw_h, name="rows"), spring(1)]
    else:
        def draw_v(x, y, w, h):
            vbars(c, (x, y, w, h), d)

        body += [spring(0.4), Item(320, draw_v, flex=1, max_h=520 if not card.landscape else 440, name="chart"),
                 spring(0.3)]
    f = B.facts(card, d.get("facts") or [], drop=1)
    if f:
        body += [gap(36), f]
    card.stack(items + body)


def fmt_value(v: Any, spec: str | None) -> str:
    from ..text import fmt

    return fmt(v, spec or "{:,.0f}") if isinstance(v, (int, float)) else typo(v)


@template("allocation", "composition", "donut", "share")
def allocation(card: Card) -> None:
    from ..charts import donut, share_bar

    d = card.card
    c = card.c
    items = card.title_items()
    parts = [p for p in (d.get("items") or []) if (p.get("num") or 0) > 0]
    if len(parts) > 6:
        rest = parts[5:]
        parts = parts[:5] + [{"label": "Other", "num": sum(p["num"] for p in rest),
                              "value": d.get("other_value", "")}]
        card.ctx.warnings.append("allocation collapsed to 5 + Other")
    style = d.get("style") or ("donut" if str(d.get("type")) == "donut" else "bar")
    body: list[Item] = []
    if style == "donut":
        R = 150

        def draw_d(x, y, w, h):
            cx, cy = x + w / 2, y + h / 2
            donut(c, (cx, cy), R, 20, [p["num"] for p in parts])
            if d.get("total"):
                hh = Hero(c, typo(d["total"]), R * 1.4, size=62, min_size=34)
                hh.draw(cx, cy + hh.cap / 2 - 6, "m")
                c.label((cx, cy + hh.cap / 2 + 28), typo(d.get("total_label", "Total")), anchor="ms")

        body += [spring(0.4), Item(2 * R + 32, draw_d, name="donut"), spring(0.5)]
    elif d.get("total"):
        body += [spring(0.5), B.hero(card, d["total"], size=d.get("size", 150)),
                 gap(22), B.text(card, d.get("context", ""), "dek", T.MUTED, 2, name="context") or gap(0),
                 spring(0.7)]
    bar_h = 0 if style == "donut" else 12 + 30
    row_h = 60
    lf, pf, vf = Font.of("row", 24), Font.of("small-num", 18), Font.of("row-num", 24)
    pcts = percents([p["num"] for p in parts])
    px, py = 24, 6

    def draw_rows(x, y, w, h):
        c.panel(x, y, x + w, y + h)
        x, w = x + px, w - 2 * px
        if bar_h:
            share_bar(c, x, y + 26, w, 10, [p["num"] for p in parts], gap=3)
            y, h = y + bar_h, h - bar_h
        pct_x = x + w - max(c.measure(typo(p.get("value", "")), vf) for p in parts) - 34
        rh = (h - 2 * py) / max(1, len(parts))
        for i, p in enumerate(parts):
            top = y + py + i * rh
            if i:
                c.line([(x, top), (x + w, top)], T.DIVIDER, 1)
            base = top + rh / 2 + lf.cap / 2
            col = T.RAMP[min(i, len(T.RAMP) - 1)]
            c.circle((x + 6, base - lf.cap / 2), 6, fill=col)
            c.text((x + 26, base), typo(p.get("label", "")), lf, T.INK)
            if p.get("note"):
                c.text((x + 26 + c.measure(typo(p["label"]), lf) + 12, base), typo(p["note"]),
                       Font.of("whisper"), T.QUIET)
            c.text((pct_x, base), f"{pcts[i]}%", pf, T.QUIET, anchor="rs")
            c.text((x + w, base), typo(p.get("value", "")), vf, T.INK, anchor="rs")

    body += [Item(bar_h + len(parts) * row_h + 2 * py, draw_rows, flex=0.6,
                  max_h=bar_h + len(parts) * 70 + 2 * py, name="rows"), spring(0.5)]
    if d.get("note"):
        body += [gap(16), B.text(card, d["note"], "small", T.QUIET, 2, name="note")]
    card.stack(items + body)


@template("heatmap", "calendar", "cadence_grid")
def heatmap(card: Card) -> None:
    d = card.card
    c = card.c
    items = card.title_items()
    weeks: list[list[float | None]] = d.get("weeks") or []
    days = d.get("day_labels") or ["M", "T", "W", "T", "F", "S", "S"]
    months = d.get("month_labels") or {}
    flat = [v for wk in weeks for v in wk if v is not None]
    vmax = max(flat) if flat else 1
    ramp = [T.GRID, T.TRACK, T.ASH, T.FAINT, T.MUTED, T.SOFT, T.INK]
    head: list[Item] = []
    if d.get("value"):
        head = [gap(30), _headline_row(card, d["value"], d.get("delta"), d.get("delta_note"),
                                       size=d.get("size", 104), right=d.get("aside"))]

    invert = bool(d.get("invert"))
    lo_lab, hi_lab = (d.get("legend") or ["less", "more"])[:2]
    n = max(1, len(weeks))
    lab_w, g = 30, 6
    cell = min((card.cw - lab_w) / n - g, 60)
    grid_h = 30 + 7 * (cell + g) + 36

    def level(v: float) -> str:
        norm = v / vmax if vmax else 0
        if invert:
            norm = 1 - norm
        elif v == 0:
            return T.GRID
        return ramp[1 + min(len(ramp) - 2, int(norm * (len(ramp) - 1.0001)))]

    def grid(x, y, w, h):
        gx0 = x + lab_w + ((w - lab_w) - n * (cell + g) + g)
        top = y + 30
        fa = Font.of("axis")
        for r, dl in enumerate(days):
            if r % 2 == 0:
                c.text((x, top + r * (cell + g) + cell / 2 + fa.cap / 2), dl, fa, T.FAINT)
        best = d.get("best")
        rad = max(3, cell * 0.14)
        for i, wk in enumerate(weeks):
            key = str(i)
            if key in months:
                c.text((gx0 + i * (cell + g), y + 14), typo(months[key]), fa, T.FAINT)
            for r, v in enumerate(wk):
                cx = gx0 + i * (cell + g)
                cy = top + r * (cell + g)
                if v is None:
                    c.rect(cx, cy, cx + cell, cy + cell, T.HAIR, radius=rad)
                    c.rect(cx + 1.6, cy + 1.6, cx + cell - 1.6, cy + cell - 1.6, T.CANVAS, radius=rad - 1.6)
                    continue
                col = level(v)
                if best is not None and [i, r] == list(best):
                    col = T.OLIVE
                c.rect(cx, cy, cx + cell, cy + cell, col, radius=rad)
        ly = top + 7 * (cell + g) + 30
        sw, sg = 16, 6
        swatches = [T.TRACK, T.ASH, T.MUTED, T.SOFT, T.INK]
        hi_w = c.measure(hi_lab, fa)
        sx1 = x + w - hi_w - 10
        sx0 = sx1 - len(swatches) * (sw + sg) + sg
        c.text((x + w, ly), hi_lab, fa, T.FAINT, anchor="rs")
        for k, col in enumerate(swatches):
            lx = sx0 + k * (sw + sg)
            c.rect(lx, ly - 14, lx + sw, ly + 2, col, radius=3)
        c.text((sx0 - 10, ly), lo_lab, fa, T.FAINT, anchor="rs")
        if best is not None and d.get("best_label"):
            c.rect(x + lab_w, ly - 14, x + lab_w + 16, ly + 2, T.OLIVE, radius=3)
            c.text((x + lab_w + 26, ly), typo(d["best_label"]), fa, T.MUTED)

    body = [spring(0.35)] + head + [spring(0.5), Item(grid_h, grid, name="grid"), spring(0.7)]
    f = B.facts(card, d.get("facts") or [], drop=1)
    if f:
        body.append(f)
    card.stack(items + body)


@template("funnel", "conversion")
def funnel(card: Card) -> None:
    d = card.card
    c = card.c
    items = card.title_items()
    stages = list(d.get("stages") or [])[:6]
    head: list[Item] = []
    if d.get("value"):
        head = [gap(30), _headline_row(card, d["value"], d.get("delta"), d.get("delta_note"),
                                       size=d.get("size", 110), right=d.get("aside"))]
    lf, vf = Font.of("row", 24), Font.of("row-num", 24)
    rates = [None] + [(b.get("num") or 0) / (a.get("num") or 1) for a, b in zip(stages, stages[1:])]
    steps = [r for r in rates if r is not None]
    weakest = rates.index(min(steps)) if steps else None
    base_h = 92

    top_num = (stages[0].get("num") or 1) if stages else 1

    def draw(x, y, w, h):
        row_h = h / max(1, len(stages))
        prev_label = None
        for i, s in enumerate(stages):
            top = y + i * row_h
            base = top + lf.cap
            label = typo(s.get("label", ""))
            c.text((x, base), label, lf, T.INK)
            c.text((x + w, base), typo(s.get("value") or fmt_value(s.get("num"), d.get("fmt"))), vf, T.INK,
                   anchor="rs")
            by = base + 16
            r = rates[i]
            is_weak = i == weakest
            frac = (s.get("num") or 0) / top_num
            c.rect(x, by, x + w, by + 8, T.GRID, radius=4)
            c.rect(x, by, x + max(8, w * frac), by + 8, T.INK if is_weak else T.ASH, radius=4)
            ty = by + 8 + 24
            if r is not None:
                af = Font.of("axis-strong" if is_weak else "axis")
                txt = f"{r * 100:.1f}%".replace(".0%", "%") + f" of {prev_label.lower()}"
                c.text((x, ty), txt, af, T.INK if is_weak else T.QUIET)
                if is_weak:
                    c.label((x + c.measure(txt, af) + 14, ty), d.get("weakest_label", "biggest drop"), T.MUTED,
                            size=15.5)
            else:
                c.text((x, ty), typo(d.get("entry_label", "top of funnel")), Font.of("axis"), T.QUIET)
            prev_label = label

    body = [spring(0.3)] + head + [spring(0.5), Item(len(stages) * base_h, draw, flex=1, max_h=len(stages) * 124,
                                                     name="funnel"), spring(0.4)]
    f = B.facts(card, d.get("facts") or [], drop=1)
    if f:
        body += [gap(24), f]
    card.stack(items + body)
