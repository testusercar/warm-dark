"""Number-first templates: kpi, scoreboard, gap, progress."""
from __future__ import annotations

from typing import Any

from .. import blocks as B
from .. import tokens as T
from ..canvas import Font
from ..charts import Lin, dot, line_chart
from ..layout import Card, Item, gap, spring
from ..text import Hero, delta_width, draw_delta, fmt, parse_delta, typo
from . import template


def _spark_item(card: Card, sp: dict[str, Any] | list, height: float = 150) -> Item | None:
    if not sp:
        return None
    if isinstance(sp, list):
        sp = {"values": sp}
    vals = sp.get("values") or []
    if len(vals) < 2:
        return None
    c = card.c
    label = sp.get("label")

    def draw(x, y, w, h):
        yy = y
        if label:
            c.label((x, yy + Font.of("label").cap), typo(label))
            yy += Font.of("label").cap + 12
        spec = {
            "series": [{"values": vals, "role": "current", "end_label": False}],
            "x": sp.get("x"),
            "x_ticks": sp.get("x_ticks") or ([0, len(sp["x"]) - 1] if sp.get("x") else None),
            "grid": False,
            "area": sp.get("area", True),
            "end_labels": False,
            "positive": sp.get("positive", False),
        }
        if sp.get("prior"):
            spec["series"].insert(0, {"values": sp["prior"], "role": "prior", "end_label": False})
        line_chart(c, (x, yy, w, y + h - yy), spec)

    return Item(height, draw, flex=0.4, max_h=height * 1.5, name="spark", drop=2)


@template("kpi", "metric", "hero_metric", "big_number")
def kpi(card: Card) -> None:
    d = card.card
    items = card.title_items()
    body = B.compact_items([
        B.hero(card, d.get("value", "—"), size=d.get("size", 172)),
        gap(24),
        B.delta(card, d.get("delta"), d.get("delta_note")),
        gap(12) if d.get("delta") else None,
        B.text(card, d.get("context", ""), "dek", T.MUTED, 2, name="context"),
    ])
    lower: list[Item] = []
    spark = _spark_item(card, d.get("spark"))
    comp = B.composition(card, d.get("composition") or [], label=d.get("composition_label"), width=card.inner)
    if spark:
        lower += [spark, gap(40)]
    elif comp:
        lower += [B.in_panel(card, [comp], pad_y=26, name="composition", drop=1), gap(16)]
    elif d.get("image"):
        img = B.image(card, d.get("image"), anchor="center")
        if img:
            lower += [img, gap(32)]
    f = B.facts(card, d.get("facts") or [])
    has_visual = bool(lower)
    if f:
        lower.append(f)
    top = spring(0.4 if has_visual else 0.5)
    card.stack(items + [top] + body + [spring(1.0)] + lower)


def _pair(card: Card, cur: dict[str, Any], prior: dict[str, Any], d: Any, note: str | None) -> Item:
    """Current hero (left, ink) against prior (right, muted) on one baseline."""
    c = card.c
    lf = Font.of("label")
    right_w = card.cw * 0.34
    hcur = Hero(c, typo(cur.get("value", "")), card.cw - right_w - 24, size=144, min_size=72)
    hpri = Hero(c, typo(prior.get("value", "")), right_w, size=min(hcur.size * 0.42, 60), min_size=34,
                kind="display", color=T.MUTED, unit_color=T.FAINT)
    dd = parse_delta(d, note)
    df = Font.of("delta")
    h = lf.cap + 20 + hcur.cap + (24 + df.cap if dd else 0) + 4

    def draw(x, y, w, hh):
        base = y + lf.cap + 20 + hcur.cap
        c.label((x, y + lf.cap), typo(cur.get("label", "Now")))
        c.label((x + w, y + lf.cap), typo(prior.get("label", "Prior")), T.QUIET, anchor="rs")
        hcur.draw(x, base)
        hpri.draw(x + w, base, "r")
        if dd:
            draw_delta(c, x, base + 24 + df.cap, dd, df)

    return Item(h, draw, name="pair")


def _dumbbell_rows(card: Card, rows: list[dict[str, Any]]) -> Item:
    c = card.c
    lf, nf, sf = Font.of("row", 23), Font.of("small-num"), Font.of("whisper")
    row_h = 80

    def draw(x, y, w, hh):
        yy = y
        rh = (hh + 20) / max(1, len(rows))
        for k, r in enumerate(rows):
            if k:
                c.line([(x, yy - 20), (x + w, yy - 20)], T.DIVIDER, 1)
            cur, pri = float(r.get("current") or 0), float(r.get("prior") or 0)
            base = yy + lf.cap
            c.text((x, base), typo(r.get("label", "")), lf, T.INK)
            spec = r.get("fmt") or "{:,.0f}"
            dcur = typo(r.get("current_label") or fmt(cur, spec))
            dpri = typo(r.get("prior_label") or fmt(pri, spec))
            dd = parse_delta(r.get("delta"))
            if dd is None and pri:
                pct = (cur - pri) / abs(pri) * 100
                dd = parse_delta({"value": f"{'+' if pct >= 0 else '−'}{abs(pct):.0f}%",
                                  "polarity": r.get("polarity", "up_good")})
            rx = x + w
            if dd:
                df = Font.of("axis-strong")
                draw_delta(c, rx, base, dd, df, align="r")
                rx -= delta_width(c, dd, df) + 20
            c.text((rx, base), dpri, nf, T.QUIET, anchor="rs")
            rx -= c.measure(dpri, nf) + 10
            c.text((rx, base), "vs", sf, T.FAINT, anchor="rs")
            rx -= c.measure("vs", sf) + 10
            c.text((rx, base), dcur, Font.of("row-num", 20), T.INK, anchor="rs")
            ty = base + 24
            lo_v, hi_v = min(cur, pri), max(cur, pri)
            d0 = lo_v * 0.6 if lo_v > 0 else lo_v - (hi_v - lo_v or 1)
            X = Lin(d0, hi_v * 1.06 if hi_v > 0 else hi_v + (hi_v - lo_v or 1) * 0.1, x + 8, x + w - 8)
            c.line([(x, ty), (x + w, ty)], T.TRACK_S, 2)
            a, b = X(pri), X(cur)
            c.line([(min(a, b), ty), (max(a, b), ty)], T.ASH, 4)
            c.circle((a, ty), 7, fill=T.SURFACE)
            c.ring((a, ty), 5.5, T.FAINT, 1.8)
            c.circle((b, ty), 9, fill=T.SURFACE)
            c.circle((b, ty), 6, fill=T.OLIVE if (dd and dd.good) else T.INK)
            yy += rh

    return Item(len(rows) * row_h - 20, draw, flex=1, max_h=len(rows) * 100 - 20, name="rows")


@template("scoreboard", "dual_kpi", "versus")
def scoreboard(card: Card) -> None:
    d = card.card
    c = card.c
    items = card.title_items()
    rows = list(d.get("rows") or [])[: T.MAX_PUNCHES]
    body: list[Item] = [spring(0.35),
                        _pair(card, d.get("current") or {}, d.get("prior") or {}, d.get("delta"), d.get("delta_note"))]
    if rows:
        def legend(x, y, w, hh):
            lf = Font.of("label")
            c.label((x, y + lf.cap), d.get("rows_label", "Breakdown"))
            wl = c.label_width("prior")
            c.label((x + w, y + lf.cap), "prior", T.QUIET, anchor="rs")
            c.ring((x + w - wl - 14, y + lf.cap / 2), 5, T.FAINT, 1.6)
            wn = c.label_width("now")
            nx = x + w - wl - 40
            c.label((nx, y + lf.cap), "now", T.QUIET, anchor="rs")
            c.circle((nx - wn - 14, y + lf.cap / 2), 5, fill=T.INK)

        body += [spring(0.5), B.in_panel(card, [Item(Font.of("label").cap + 30, legend, name="legend"),
                                                _dumbbell_rows(card, rows)], pad_y=26, name="breakdown")]
    else:
        body.append(spring(1))
    f = B.facts(card, d.get("facts") or [], drop=1)
    if f:
        body += [gap(20), f]
    card.stack(items + body)


@template("gap", "before_after", "target_gap")
def gap_card(card: Card) -> None:
    d = card.card
    c = card.c
    items = card.title_items()
    before, after, target = d.get("before") or {}, d.get("after") or {}, d.get("target") or {}
    pts = [p for p in (before, after, target) if p.get("num") is not None]
    hero_items = B.compact_items([
        B.hero(card, d.get("value", "—"), size=d.get("size", 164)),
        gap(24),
        B.delta(card, d.get("delta"), d.get("delta_note")),
        gap(12) if d.get("delta") else None,
        B.text(card, d.get("context", ""), "dek", T.MUTED, 2, name="context"),
    ])

    def track(x, y, w, h):
        if not pts:
            return
        nums = [p["num"] for p in pts]
        lo, hi = min(nums), max(nums)
        span = (hi - lo) or abs(hi) or 1
        X = Lin(lo - span * 0.12, hi + span * 0.12, x + 6, x + w - 6)
        ty = y + h * 0.52
        vf = Font.of("stat-s", 28)
        c.line([(x, ty), (x + w, ty)], T.TRACK, 2)
        reached = False
        if target.get("num") is not None and after.get("num") is not None:
            better_low = d.get("polarity", "down_good" if target["num"] < before.get("num", target["num"]) else "up_good")
            reached = after["num"] <= target["num"] if better_low == "down_good" else after["num"] >= target["num"]
        if before.get("num") is not None and after.get("num") is not None:
            a, b = X(before["num"]), X(after["num"])
            c.line([(a, ty), (b, ty)], T.ASH, 4)
        if not reached and after.get("num") is not None and target.get("num") is not None:
            b, t = X(after["num"]), X(target["num"])
            c.dotted([(b, ty), (t, ty)], T.MUTED, 1.5, 8)
            if d.get("gap_label"):
                c.text(((b + t) / 2, ty + 34), typo(d["gap_label"]), Font.of("axis-strong"), T.MUTED, anchor="ms")
        if target.get("num") is not None:
            tx = X(target["num"])
            col = T.OLIVE if reached else T.MUTED
            c.dashed([(tx, ty - 54), (tx, ty + 54)], col, 1.4, (5, 5))
            c.label((tx, ty + 80), typo(target.get("label", "Target")), col, anchor="ms")
            c.text((tx, ty + 80 + vf.cap + 14), typo(target.get("value", "")), vf, col, anchor="ms")
        for p, is_after in ((before, False), (after, True)):
            if p.get("num") is None:
                continue
            px = X(p["num"])
            if is_after:
                dot(c, (px, ty), T.OLIVE if reached else T.INK, 8, 4.5)
            else:
                c.circle((px, ty), 10, fill=T.CANVAS)
                c.ring((px, ty), 7, T.FAINT, 2)
            col = T.INK if is_after else T.MUTED
            c.text((px, ty - 32), typo(p.get("value", "")), vf, col, anchor="ms")
            c.label((px, ty - 32 - vf.cap - 14), typo(p.get("label", "")), T.MUTED, anchor="ms")

    body = [spring(0.8)] + hero_items + [spring(0.7), Item(260, track, name="track"), spring(0.6)]
    f = B.facts(card, d.get("facts") or [], drop=1)
    if f:
        body += [gap(20), f]
    card.stack(items + body)


@template("progress", "north_star", "goal")
def progress(card: Card) -> None:
    d = card.card
    c = card.c
    items = card.title_items()
    cur = d.get("current") or {}
    goal = d.get("goal") or {}
    frac = (cur.get("num") or 0) / (goal.get("num") or 1)
    pace = d.get("pace") or {}
    on_pace = d.get("on_pace")
    if on_pace is None and pace.get("expected_frac") is not None:
        on_pace = frac >= pace["expected_frac"]
    value = d.get("value") or f"{frac * 100:.0f}%"
    head = B.compact_items([
        B.hero(card, value, size=d.get("size", 156)),
        gap(22),
        B.text(card, d.get("context") or f"**{typo(cur.get('value', ''))}** of {typo(goal.get('value', ''))}",
               "dek", T.MUTED, 2, strong_color=T.INK, name="context"),
    ])

    def bar(x, y, w, h):
        bh = 14
        by = y + 28
        c.rect(x, by, x + w, by + bh, T.TRACK, radius=bh / 2)
        col = T.OLIVE if on_pace else T.INK
        c.rect(x, by, x + max(bh, w * min(1, frac)), by + bh, col, radius=bh / 2)
        if pace.get("expected_frac") is not None:
            ex = x + w * min(1, pace["expected_frac"])
            c.line([(ex, by - 10), (ex, by + bh + 10)], T.MUTED, 1.6)
            lab = typo(pace.get("marker_label", "pace today"))
            c.label((ex, by - 20), lab, T.MUTED, anchor="ms" if 60 < ex - x < w - 60 else "rs")
        lf = Font.of("axis")
        c.text((x, by + bh + 30), typo(d.get("start_label", "0")), lf, T.FAINT)
        c.text((x + w, by + bh + 30), typo(goal.get("value", "")), lf, T.FAINT, anchor="rs")

    body = [spring(0.5)] + head + [gap(38), Item(100, bar, name="bar")]
    if pace.get("actual"):
        spec = {
            "series": [{"values": pace["actual"], "role": "current", "name": pace.get("actual_name", "actual"),
                        "label": pace.get("actual_label")}],
            "x": pace.get("x"),
            "x_ticks": pace.get("x_ticks"),
            "fmt": d.get("fmt", "{:,.0f}"),
            "axis_fmt": d.get("axis_fmt"),
            "zero": True,
            "ticks": 3,
            "positive": bool(on_pace),
        }
        if pace.get("required"):
            spec["series"].insert(0, {"values": pace["required"], "role": "target",
                                      "name": pace.get("required_name", "needed"), "label": pace.get("required_label"),
                                      "smooth": False})
        if pace.get("projection"):
            spec["series"].insert(0, {"values": pace["projection"], "role": "projection",
                                      "name": pace.get("projection_name", "projected"),
                                      "label": pace.get("projection_label"), "smooth": False})

        def chart(x, y, w, h, spec=spec):
            line_chart(c, (x, y, w, h), spec)

        body += [gap(16), Item(260, chart, flex=1, name="chart", drop=2)]
    else:
        body.append(spring(1))
    f = B.facts(card, d.get("facts") or [], drop=1)
    if f:
        body += [gap(36), f]
    card.stack(items + body)
