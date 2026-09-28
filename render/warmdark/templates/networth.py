"""Holistic net-worth templates (Ledger): multi_institution_nw, cashflow_sankey,
nw_delta_weekly, manulife_notes_strip, home_equity_card.

Money is ownership economics: every figure is Aaron's share, net of what is owed.
"""
from __future__ import annotations

from typing import Any

from .. import blocks as B
from .. import tokens as T
from ..canvas import Font
from ..charts import Lin, dot, line_chart, share_bar
from ..layout import Card, Item, gap, spring
from ..text import (Hero, Style, delta_width, draw_block, draw_delta, ellipsize, fmt, nice_ticks, parse_delta,
                    text_block, typo)
from . import template
from .charts_t import _headline_row

MONEY = "C${:,.0f}"

LINK = T.mix(T.CANVAS, T.MUTED, 0.20)
LINK_INK = T.mix(T.CANVAS, T.INK, 0.24)
LINK_GOOD = T.mix(T.CANVAS, T.OLIVE, 0.30)


# ------------------------------------------------------------------ helpers


def _obj(v: Any) -> dict[str, Any]:
    if isinstance(v, dict):
        return v
    if isinstance(v, bool):
        return {}
    if isinstance(v, (int, float)):
        return {"num": v}
    if isinstance(v, str):
        return {"value": v}
    return {}


def _n(v: Any) -> float | None:
    x = _obj(v).get("num")
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _show(v: Any, spec: str, signed: bool = False) -> str:
    o = _obj(v)
    if o.get("value") not in (None, ""):
        return typo(o["value"])
    n = _n(v)
    return fmt(n, spec, signed) if n is not None else "—"


def _frac(v: Any) -> float | None:
    """45 / 0.45 / "45%" -> 0.45."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, str):
        try:
            x = float(v.strip().rstrip("%"))
        except ValueError:
            return None
        return x / 100
    x = float(v)
    return x / 100 if x > 1 else x


def _pct(f: float) -> str:
    return f"{f * 100:.1f}".rstrip("0").rstrip(".") + "%"


def _agree(card: Card, what: str, given: float | None, computed: float | None, tol: float = 1.0) -> None:
    if given is not None and computed is not None and abs(given - computed) > tol:
        card.ctx.warnings.append(
            f"{what} is {given:,.0f} but its parts come to {computed:,.0f} — numbers must agree")


def _fit(c, s: str, f: Font, max_w: float) -> str:
    """s if it fits in max_w, else ellipsized; '' when there is no room at all."""
    if not s or c.measure(s, f) <= max_w:
        return s
    if max_w < c.measure("…", f) * 3:
        return ""
    line = ellipsize(c, [(s, f, T.FAINT)], max_w)
    return line[0][0] if line else ""


def _polar(raw: Any, polarity: str) -> Any:
    if isinstance(raw, str) and raw:
        return {"value": raw, "polarity": polarity}
    if isinstance(raw, dict) and "polarity" not in raw:
        return {**raw, "polarity": polarity}
    return raw


def _hero_head(card: Card, label: str | None, value: str, delta: Any = None, note: str | None = None,
               context: str | None = None, size: float = 170, right: str | None = None) -> list[Item]:
    return B.compact_items([
        gap(28),
        B.eyebrow(card, typo(label), typo(right) if right else None) if label else None,
        gap(20) if label else None,
        B.hero(card, value, size=size, min_size=72),
        gap(24) if delta else None,
        B.delta(card, delta, note) if delta else None,
        gap(12) if context else None,
        B.text(card, context or "", "dek", T.MUTED, 2, strong_color=T.INK, name="context"),
    ])


# -------------------------------------------------------- multi_institution_nw


def _included(r: dict[str, Any]) -> bool:
    return not (r.get("exclude") is True or r.get("included") is False)


def _share_text(v: Any) -> str:
    if isinstance(v, str):
        return typo(v)
    f = _frac(v)
    return _pct(f) if f is not None else ""


@template("multi_institution_nw", "nw_buckets", "networth_buckets", "institution_nw")
def multi_institution_nw(card: Card) -> None:
    d = card.card
    c = card.c
    spec = d.get("fmt") or MONEY
    rows = [r for r in (d.get("rows") or []) if isinstance(r, dict)]
    inc = [r for r in rows if _included(r)]
    exc = [r for r in rows if not _included(r)]
    if len(inc) > 8:
        card.ctx.warnings.append(f"{len(inc)} included rows — capped at 8; roll small buckets together")
        inc = inc[:8]
    if len(exc) > 3:
        card.ctx.warnings.append(f"{len(exc)} excluded rows — capped at 3")
        exc = exc[:3]
    inc_sum = sum(_n(r) or 0 for r in inc)
    exc_sum = sum(_n(r) or 0 for r in exc)
    tot = _obj(d.get("total"))
    _agree(card, "total", _n(tot), inc_sum)
    total_value = typo(tot.get("value") or fmt(inc_sum, spec))

    items = card.title_items()
    head = _hero_head(card, tot.get("label", "Net worth"), total_value, d.get("delta"), d.get("delta_note"),
                      tot.get("sub"), size=d.get("size", 150), right=tot.get("right"))

    assets = [r for r in inc if (_n(r) or 0) > 0]
    colour = {id(r): T.RAMP[min(k, len(T.RAMP) - 1)] for k, r in enumerate(assets)}

    def bar(x, y, w, h):
        if assets:
            share_bar(c, x, y, w, h, [_n(r) or 0 for r in assets], [colour[id(r)] for r in assets], gap=3)

    lf, vf, sf = Font.of("row", 25), Font.of("row-num", 25), Font.of("whisper")
    shf = Font.of("small-num", 19)
    all_rows = inc + exc
    val_w = max((c.measure(_show(r, spec), vf) for r in all_rows), default=80)
    share_w = max((c.measure(_share_text(r.get("share")), shf) for r in all_rows if r.get("share") is not None),
                  default=0)

    def draw_rows(x, y, w, h, rows, muted=False):
        rh = h / max(1, len(rows))
        share_x = x + w - val_w - 26
        text_x1 = share_x - (share_w + 18 if share_w else 0)
        for i, r in enumerate(rows):
            base = y + i * rh + rh / 2 + lf.cap / 2
            num = _n(r)
            sy = base - lf.cap / 2
            if muted:
                c.ring((x + 6, sy), 5.5, T.FAINT, 1.6)
            elif num is not None and num < 0:
                c.rect(x, sy - 1.6, x + 13, sy + 1.6, T.INK, radius=1.6)
            elif not num:
                c.ring((x + 6, sy), 5.5, T.FAINT, 1.6)
            else:
                c.rect(x, sy - 6.5, x + 13, sy + 6.5, colour.get(id(r), T.FAINT), radius=3)
            lab = typo(r.get("label", ""))
            lx = x + 30
            c.text((lx, base), lab, lf, T.MUTED if muted else T.INK)
            if r.get("sub"):
                sx = lx + c.measure(lab, lf) + 12
                c.text((sx, base), _fit(c, typo(r["sub"]), sf, text_x1 - sx), sf, T.FAINT)
            if r.get("share") is not None:
                c.text((share_x, base), _share_text(r["share"]), shf, T.FAINT, anchor="rs")
            col = T.MUTED if (muted or not num) else T.INK
            c.text((x + w, base), _show(r, spec), vf, col, anchor="rs")

    row_h = 52
    body: list[Item] = [spring(0.4)] + head + [gap(34), Item(16, bar, name="stack"), gap(22)]
    body.append(Item(len(inc) * row_h, lambda x, y, w, h: draw_rows(x, y, w, h, inc), flex=0.6,
                     max_h=len(inc) * 64, name="rows"))
    if exc:
        body += [gap(30), spring(0.6), B.eyebrow(card, typo(d.get("excluded_label", "Not in total")),
                                        typo(d["excluded_right"]) if d.get("excluded_right") else None), gap(6),
                 Item(len(exc) * 48, lambda x, y, w, h: draw_rows(x, y, w, h, exc, muted=True), name="excluded")]
        all_in = d.get("all_in", True)
        if all_in:
            ao = _obj(all_in) if not isinstance(all_in, bool) else {}
            _agree(card, "all_in", _n(ao), inc_sum + exc_sum)
            txt = f"{typo(ao.get('label', 'With excluded rows'))}: **{typo(ao.get('value') or fmt(inc_sum + exc_sum, spec))}**"
            body += [gap(14), B.text(card, txt, "small", T.MUTED, 1, strong_color=T.SOFT, name="all_in")]
    body.append(spring(0.5))
    f = B.facts(card, d.get("facts") or [], drop=1)
    if f:
        body += [gap(20), f]
    card.stack(items + B.compact_items(body))


# ------------------------------------------------------------ cashflow_sankey


def _bez(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    u = 1 - t
    return u * u * u * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t * t * t * p3


def _band(c, sx: float, sy: float, tx: float, ty: float, th: float, col: str, steps: int = 28) -> None:
    m = (tx - sx) * 0.5
    top = [(_bez(sx, sx + m, tx - m, tx, s / steps), _bez(sy, sy, ty, ty, s / steps)) for s in range(steps + 1)]
    bot = [(px, py + th) for px, py in reversed(top)]
    c.polygon(top + bot, col)


@template("cashflow_sankey", "sankey", "cashflow", "flow")
def cashflow_sankey(card: Card) -> None:
    d = card.card
    c = card.c
    spec = d.get("fmt") or MONEY
    nodes = [n for n in (d.get("nodes") or []) if isinstance(n, dict) and n.get("id") is not None]
    ids = {str(n["id"]): n for n in nodes}
    links = []
    for lk in d.get("links") or []:
        s, t = str(lk.get("source")), str(lk.get("target"))
        if s not in ids or t not in ids:
            card.ctx.warnings.append(f"link {s}→{t} names an unknown node")
            continue
        if (lk.get("num") or 0) > 0:
            links.append({**lk, "source": s, "target": t})

    preds: dict[str, list[str]] = {k: [] for k in ids}
    for lk in links:
        preds[lk["target"]].append(lk["source"])
    col: dict[str, int] = {k: int(n["column"]) for k, n in ids.items() if isinstance(n.get("column"), int)}

    def depth(k: str, seen: frozenset = frozenset()) -> int:
        if k in col:
            return col[k]
        if k in seen:
            card.ctx.warnings.append("sankey has a cycle — flows must run one way")
            return 0
        ps = preds[k]
        col[k] = 0 if not ps else 1 + max(depth(p, seen | {k}) for p in ps)
        return col[k]

    for k in ids:
        depth(k)
    ncols = (max(col.values()) + 1) if col else 0
    inflow = {k: sum(lk["num"] for lk in links if lk["target"] == k) for k in ids}
    outflow = {k: sum(lk["num"] for lk in links if lk["source"] == k) for k in ids}
    total = {k: max(inflow[k], outflow[k]) for k in ids}
    for k in ids:
        if inflow[k] and outflow[k] and abs(inflow[k] - outflow[k]) > max(1.0, 0.005 * total[k]):
            card.ctx.warnings.append(
                f"node '{k}' takes in {inflow[k]:,.0f} but sends out {outflow[k]:,.0f} — flows must balance")
    columns: list[list[str]] = [[k for k in ids if col[k] == i and total[k] > 0] for i in range(ncols)]
    if ncols < 2 or not links:
        card.ctx.warnings.append("sankey needs at least two columns of linked nodes")
    if not card.landscape and (max((len(cl) for cl in columns), default=0) > 7 or len(ids) > 14):
        card.ctx.warnings.append(f"{len(ids)} nodes is too many for portrait — set \"format\": \"landscape\"")

    nf, vf = Font.of("row-strong", 20), Font.of("small-num", 18)
    n_lh, v_lh = 24, 22

    def label_of(k: str) -> tuple[str, str]:
        n = ids[k]
        v = n.get("value") or fmt(n["num"] if isinstance(n.get("num"), (int, float)) else total[k], spec)
        return typo(n.get("label", k)), typo(v)

    def one_w(k: str) -> float:
        a, b = label_of(k)
        return c.measure(a, nf) + 10 + c.measure(b, vf)

    def two_w(k: str) -> float:
        a, b = label_of(k)
        return max(c.measure(a, nf), c.measure(b, vf))

    lanes = [max((two_w(k) for k in cl), default=0) for cl in columns]
    if lanes:
        cap = card.cw * 0.2
        for i in {0, len(lanes) - 1}:
            lanes[i] = max(lanes[i], min(cap, max(one_w(k) for k in columns[i])))
    stages = [typo(s) for s in (d.get("stages") or [])]
    stage_h = (Font.of("label").cap + 22) if stages else 0

    def colour_of(k: str, ci: int) -> str:
        tone = ids[k].get("tone")
        if tone == "good":
            return T.OLIVE
        if tone == "ink":
            return T.INK
        if tone == "muted":
            return T.MUTED
        return T.INK if ci == 0 else (T.SOFT if ci < ncols - 1 else T.MUTED)

    def link_colour(lk: dict[str, Any]) -> str:
        tone = lk.get("tone")
        if tone == "good" or (tone is None and "good" in (ids[lk["source"]].get("tone"), ids[lk["target"]].get("tone"))):
            return LINK_GOOD
        if tone == "ink":
            return LINK_INK
        return LINK

    def draw(x, y, w, h):
        if ncols < 2:
            return
        bw, pad = 10, 10
        fixed = lanes[0] + pad + ncols * bw + pad + lanes[-1]
        link_w = (w - fixed) / (ncols - 1)
        mid_room = link_w - pad - 18
        if ncols > 2 and mid_room < max(lanes[1:-1]):
            card.ctx.warnings.append(
                f"sankey links only {link_w:.0f}px wide — middle labels crowd the next column; go landscape")
        geo = []
        for i in range(ncols):
            if i == 0:
                bar_x = x + lanes[0] + pad
                geo.append({"bar": bar_x, "out": bar_x + bw, "lab": bar_x - pad, "align": "r", "room": lanes[0]})
            else:
                bar_x = geo[-1]["out"] + link_w
                geo.append({"bar": bar_x, "out": bar_x + bw, "lab": bar_x + bw + pad, "align": "l",
                            "room": lanes[-1] if i == ncols - 1 else mid_room})
        for i, s in enumerate(stages[:ncols]):
            g = geo[i]
            ex = g["bar"] + bw if i == 0 else g["bar"]
            c.label((ex, y + Font.of("label").cap), s, T.MUTED, anchor="rs" if i == 0 else "ls")
        py0, py1 = y + stage_h, y + h
        node_gap = 14
        k = min(((py1 - py0) - node_gap * (len(cl) - 1)) / (sum(total[n] for n in cl) or 1) for cl in columns if cl)
        pos: dict[str, tuple[float, float]] = {}
        for cl in columns:
            hs = [max(2.0, total[n] * k) for n in cl]
            col_h = sum(hs) + node_gap * (len(cl) - 1)
            yy = py0 + ((py1 - py0) - col_h) / 2
            for n, hh in zip(cl, hs):
                pos[n] = (yy, yy + hh)
                yy += hh + node_gap
        centre = {n: (a + b) / 2 for n, (a, b) in pos.items()}
        out_acc = {n: pos[n][0] for n in pos}
        in_acc = {n: pos[n][0] for n in pos}
        segs = []
        for lk in sorted(links, key=lambda lk: (centre.get(lk["source"], 0), centre.get(lk["target"], 0))):
            s, t = lk["source"], lk["target"]
            if s not in pos or t not in pos:
                continue
            segs.append([lk, s, t, lk["num"] * k])
        for seg in sorted(segs, key=lambda sg: centre[sg[2]]):
            seg.append(out_acc[seg[1]])
            out_acc[seg[1]] += seg[3]
        for seg in sorted(segs, key=lambda sg: centre[sg[1]]):
            seg.append(in_acc[seg[2]])
            in_acc[seg[2]] += seg[3]
        order = {LINK: 0, LINK_INK: 1, LINK_GOOD: 2}
        for lk, s, t, th, sy, ty in sorted(segs, key=lambda sg: order[link_colour(sg[0])]):
            _band(c, geo[col[s]]["out"], sy, geo[col[t]]["bar"], ty, th, link_colour(lk))
        for ci, cl in enumerate(columns):
            for n in cl:
                a, b = pos[n]
                c.rect(geo[ci]["bar"], a, geo[ci]["bar"] + bw, b, colour_of(n, ci), radius=2)
        for ci, cl in enumerate(columns):
            g = geo[ci]
            blocks = []
            for n in cl:
                a, b = pos[n]
                two = (b - a) >= 40 or one_w(n) > g["room"] + 0.5
                hh = n_lh + v_lh if two else n_lh
                blocks.append([n, centre[n] - hh / 2, hh, two])
            for j in range(1, len(blocks)):
                prev = blocks[j - 1]
                blocks[j][1] = max(blocks[j][1], prev[1] + prev[2] + 4)
            if blocks and blocks[-1][1] + blocks[-1][2] > py1:
                blocks[-1][1] = py1 - blocks[-1][2]
                for j in range(len(blocks) - 2, -1, -1):
                    blocks[j][1] = min(blocks[j][1], blocks[j + 1][1] - blocks[j][2] - 4)
            for n, top, hh, two in blocks:
                name, val = label_of(n)
                vcol = T.OLIVE if ids[n].get("tone") == "good" else T.MUTED
                anchor = "rs" if g["align"] == "r" else "ls"
                if two:
                    c.text((g["lab"], top + 18), name, nf, T.INK, anchor=anchor)
                    c.text((g["lab"], top + n_lh + 17), val, vf, vcol, anchor=anchor)
                elif g["align"] == "r":
                    c.text((g["lab"], top + 18), val, vf, vcol, anchor="rs")
                    c.text((g["lab"] - c.measure(val, vf) - 10, top + 18), name, nf, T.INK, anchor="rs")
                else:
                    c.text((g["lab"], top + 18), name, nf, T.INK)
                    c.text((g["lab"] + c.measure(name, nf) + 10, top + 18), val, vf, vcol)

    body: list[Item] = []
    if d.get("value"):
        body += [gap(26), _headline_row(card, d["value"], d.get("delta"), d.get("delta_note"),
                                        size=d.get("size", 96 if not card.landscape else 84), right=d.get("aside"))]
        if d.get("context"):
            body += [gap(12), B.text(card, d["context"], "dek", T.MUTED, 1, strong_color=T.INK, name="context")]
    body += [gap(34), Item(stage_h + (420 if not card.landscape else 250), draw, flex=1, name="sankey")]
    f = B.facts(card, d.get("facts") or [], drop=1)
    if f:
        body += [gap(30), f]
    card.stack(card.title_items() + B.compact_items(body))


# ------------------------------------------------------------ nw_delta_weekly


@template("nw_delta_weekly", "nw_delta", "networth_delta", "nw_weekly")
def nw_delta_weekly(card: Card) -> None:
    d = card.card
    c = card.c
    spec = d.get("fmt") or MONEY
    polarity = d.get("polarity", "up_good")
    raw = _polar(d.get("delta"), polarity)
    dd = parse_delta(raw, d.get("delta_note"))
    good = bool(dd and dd.good)
    prior = _obj(d.get("prior"))
    cur_num = d.get("num") if isinstance(d.get("num"), (int, float)) else None
    context = d.get("context")
    if not context and prior.get("value"):
        context = f"From **{typo(prior['value'])}**" + (f" on {typo(prior['label'])}" if prior.get("label") else "")
    items = card.title_items()
    head = _hero_head(card, d.get("value_label"), d.get("value", "—"), raw, d.get("delta_note"), context,
                      size=d.get("size", 200))
    if dd:
        bdf = Font.of("delta", 32)
        bnf = Font.of("dek", 27)

        def big_delta(x, y, w, h):
            draw_delta(c, x, y + bdf.cap, dd, bdf, bnf)

        head = [Item(bdf.cap + 4, big_delta, name="delta") if it.name == "delta" else it for it in head]

    lower: list[Item] = []
    sp = d.get("spark")
    if isinstance(sp, list):
        sp = {"values": sp}
    vals = (sp or {}).get("values") or []
    if len(vals) >= 2:
        n = len(vals)
        markers = []
        if prior and n >= 3 and sp.get("prior_at", n - 2) is not None:
            markers.append({"at": int(sp.get("prior_at", n - 2)), "label": typo(prior.get("label", ""))})
        xl = sp.get("x")
        s = {
            "series": [{"values": vals, "role": "current", "end_label": False}],
            "x": xl, "x_ticks": sp.get("x_ticks") or ([0, len(xl) - 1] if xl else None),
            "grid": False, "area": True, "end_labels": False, "positive": good, "markers": markers, "pad": 0.1,
        }

        def spark(x, y, w, h):
            yy = y
            if sp.get("label"):
                c.label((x, yy + Font.of("label").cap), typo(sp["label"]))
                yy += Font.of("label").cap + 12
            line_chart(c, (x, yy, w, y + h - yy), s)

        lower += [Item(170, spark, flex=0.4, max_h=250, name="spark", drop=2)]

    drivers = [r for r in (d.get("drivers") or []) if isinstance(r, dict)][: T.MAX_PUNCHES]
    if len(d.get("drivers") or []) > T.MAX_PUNCHES:
        card.ctx.warnings.append(f"drivers capped at {T.MAX_PUNCHES} — roll the rest into 'Other'")
    if drivers:
        nums = [_n(r) for r in drivers]
        if cur_num is not None and _n(prior) is not None and all(v is not None for v in nums):
            _agree(card, "net worth change", cur_num - _n(prior), sum(nums))
        lf, sf = Font.of("row", 24), Font.of("whisper")
        df = Font.of("axis-strong", 19)
        parsed = [parse_delta(_polar(_show(r, spec, signed=True), polarity)) for r in drivers]
        dw = max((delta_width(c, p, df) for p in parsed if p), default=60)
        vmax = max((abs(v or 0) for v in nums), default=1) or 1
        text_w = max(c.measure(typo(r.get("label", "")), lf) + (10 + c.measure(typo(r["sub"]), sf) if r.get("sub")
                                                                 else 0) for r in drivers)

        def draw_drivers(x, y, w, h):
            rh = h / len(drivers)
            lane1 = x + w - dw - 28
            lane0 = min(max(x + w * 0.5, x + text_w + 24), lane1 - 110)
            zx = (lane0 + lane1) / 2
            half = (lane1 - lane0) / 2
            c.line([(zx, y + 4), (zx, y + h - 4)], T.HAIR, 1.2)
            for i, (r, p) in enumerate(zip(drivers, parsed)):
                base = y + i * rh + rh / 2 + lf.cap / 2
                lab = typo(r.get("label", ""))
                c.text((x, base), lab, lf, T.INK)
                if r.get("sub"):
                    sx = x + c.measure(lab, lf) + 10
                    c.text((sx, base), _fit(c, typo(r["sub"]), sf, lane0 - 18 - sx), sf, T.FAINT)
                v = nums[i] or 0
                if p:
                    draw_delta(c, x + w, base, p, df, align="r")
                if v:
                    bl = max(3.0, half * abs(v) / vmax)
                    by = base - lf.cap / 2
                    col = p.color if p else T.INK
                    if v > 0:
                        c.rect(zx, by - 5, zx + bl, by + 5, col, radius=2, corners=(False, True, True, False))
                    else:
                        c.rect(zx - bl, by - 5, zx, by + 5, col, radius=2, corners=(True, False, False, True))

        lower += [gap(34) if lower else gap(0), B.eyebrow(card, typo(d.get("drivers_label", "What moved it")),
                                                          typo(d["drivers_right"]) if d.get("drivers_right") else None),
                  gap(8), Item(len(drivers) * 46, draw_drivers, flex=0.3, max_h=len(drivers) * 58, name="drivers")]
    comp = None if (lower or not d.get("composition")) else B.composition(
        card, d.get("composition") or [], label=d.get("composition_label"), drop=1)
    if comp:
        lower.append(comp)
    f = B.facts(card, d.get("facts") or [], drop=1)
    if f:
        lower += [gap(40), f]
    card.stack(items + [spring(0.6)] + head + [spring(0.7)] + lower + ([] if f else [spring(0.3)]))


# -------------------------------------------------------- manulife_notes_strip


@template("manulife_notes_strip", "notes_strip", "structured_notes", "manulife_notes")
def manulife_notes_strip(card: Card) -> None:
    d = card.card
    c = card.c
    spec = d.get("fmt") or MONEY
    notes = [n for n in (d.get("notes") or []) if isinstance(n, dict)]
    if len(notes) != 3:
        card.ctx.warnings.append(f"{len(notes)} notes — this strip is built for exactly 3")
    notes = notes[:3]
    rows = []
    best_known = 0.0
    for n in notes:
        p, a, m = _n(n.get("principal")), _n(n.get("accrued")), _n(n.get("mtm"))
        acc = (a / p * 100) if (p and a is not None) else None
        mtm = (m / p * 100) if (p and m is not None) else None
        rows.append((n, p, a, m, acc, mtm))
        best_known += m if m is not None else (p or 0) + (a or 0)
    known = sum(1 for r in rows if r[3] is not None)
    pts = [100.0] + [100 + r[4] for r in rows if r[4] is not None] + [r[5] for r in rows if r[5] is not None]
    span = max(2.0, max(abs(v - 100) for v in pts))
    ticks = nice_ticks(100 - span * 1.15, 100 + span * 1.15, 4)
    lo, hi = min(ticks[0], 100 - span * 1.15), max(ticks[-1], 100 + span * 1.15)

    value = d.get("value") or fmt(best_known, spec)
    context = d.get("context")
    if context is None and known < len(rows):
        context = f"MTM on {known} of {len(rows)} · rest valued at principal + accrued"
    items = card.title_items()
    head = _hero_head(card, d.get("value_label", "Notes value"), value, d.get("delta"), d.get("delta_note"),
                      context, size=d.get("size", 112))

    nf, sf = Font.of("row-strong", 26), Font.of("whisper")
    mf = Font.of("row-num", 26)
    lab_f, fig_f = Font.of("label"), Font.of("row-num", 21)
    df = Font.of("axis-strong", 19)
    axis_f = Font.of("axis")

    def axis(x, y, w, h):
        X = Lin(lo, hi, x + 8, x + w - 8)
        for t in ticks:
            if t < lo or t > hi:
                continue
            txt = "principal" if abs(t - 100) < 1e-9 else fmt(t - 100, "{:g}%", signed=True)
            c.text((X(t), y + axis_f.cap), txt, axis_f, T.MUTED if abs(t - 100) < 1e-9 else T.FAINT, anchor="ms")

    def strips(x, y, w, h):
        X = Lin(lo, hi, x + 8, x + w - 8)
        sh = h / max(1, len(rows))
        for i, (n, p, a, m, acc, mtm) in enumerate(rows):
            top = y + i * sh
            if i:
                c.line([(x, top), (x + w, top)], T.GRID, 1)
            base = top + 22 + nf.cap
            name = typo(n.get("name", f"Note {i + 1}"))
            c.text((x, base), name, nf, T.INK)
            if m is not None:
                mv = _show(n.get("mtm"), spec)
                c.text((x + w, base), mv, mf, T.INK, anchor="rs")
                c.label((x + w - c.measure(mv, mf) - 14, base - 2), "MTM", T.MUTED, anchor="rs")
                right_w = c.measure(mv, mf) + 14 + c.label_width("MTM")
            else:
                c.label((x + w, base - 2), typo(n.get("mtm_note", "MTM pending")), T.MUTED, anchor="rs")
                right_w = c.label_width(typo(n.get("mtm_note", "MTM pending")))
            if n.get("sub"):
                sx = x + c.measure(name, nf) + 12
                c.text((sx, base), _fit(c, typo(n["sub"]), sf, x + w - right_w - 20 - sx), sf, T.FAINT)
            ty = base + 34
            c.line([(x, ty), (x + w, ty)], T.GRID, 2)
            px = X(100)
            c.dashed([(px, ty - 13), (px, ty + 13)], T.ASH, 1.4, (4, 4))
            if acc is not None:
                ax = X(100 + acc)
                c.rect(min(px, ax), ty - 3.5, max(px, ax), ty + 3.5, T.SOFT, radius=3.5)
            if mtm is not None:
                dot(c, (X(mtm), ty), T.OLIVE if mtm >= 100 else T.INK, 7, 3)
            elif acc is not None:
                c.circle((X(100 + acc), ty), 8, fill=T.CANVAS)
                c.ring((X(100 + acc), ty), 5.5, T.MUTED, 1.8)
            fy = ty + 30
            cols = [("Principal", _show(n.get("principal"), spec)),
                    ("Accrued", _show(n.get("accrued"), spec, signed=True) if n.get("accrued") is not None else "—")]
            if n.get("maturity"):
                cols.append(("Matures", typo(n["maturity"])))
            perf = n.get("delta")
            if perf is None and p:
                if m is not None:
                    perf = {"value": fmt((m - p) / p * 100, "{:.1f}%", signed=True)}
                elif a is not None:
                    perf = {"value": fmt(a / p * 100, "{:.1f}%", signed=True), "note": "accrued"}
            pd = parse_delta(perf)
            ncol = len(cols) + (1 if pd else 0)
            cw = w / ncol
            for j, (lab, val) in enumerate(cols):
                c.label((x + j * cw, fy + lab_f.cap), lab)
                c.text((x + j * cw, fy + lab_f.cap + 12 + fig_f.cap), val, fig_f,
                       T.INK if j == 0 else T.SOFT)
            if pd:
                c.label((x + w, fy + lab_f.cap), typo(n.get("delta_label", "vs principal")), anchor="rs")
                draw_delta(c, x + w, fy + lab_f.cap + 12 + fig_f.cap, pd, df, Font.of("whisper"), align="r")

    strip_h = 22 + nf.cap + 34 + 30 + lab_f.cap + 12 + fig_f.cap + 22
    body = [spring(0.4)] + head + [gap(30), spring(0.6), Item(axis_f.cap + 8, axis, name="axis"), gap(4),
                                   Item(len(rows) * strip_h, strips, flex=0.5, max_h=len(rows) * (strip_h + 40),
                                        name="strips"), spring(0.4)]
    if d.get("note"):
        body += [gap(10), B.text(card, d["note"], "small", T.MUTED, 2, name="note")]
    card.stack(items + B.compact_items(body))


# ---------------------------------------------------------- home_equity_card


@template("home_equity_card", "home_equity", "property_equity")
def home_equity_card(card: Card) -> None:
    d = card.card
    c = card.c
    spec = d.get("fmt") or MONEY
    prop, mort, cash = _obj(d.get("property")), _obj(d.get("mortgage")), _obj(d.get("joint_cash"))
    pct = _frac(d.get("equity_pct"))
    if pct is None:
        card.ctx.warnings.append("equity_pct missing — assuming 100%")
        pct = 1.0
    m_pct = _frac(mort.get("share")) if mort.get("share") is not None else pct
    j_pct = _frac(cash.get("share")) if cash.get("share") is not None else pct
    pv, mv, jv = _n(prop) or 0.0, _n(mort) or 0.0, _n(cash) or 0.0
    p_share, m_share, j_share = pv * pct, mv * m_pct, jv * j_pct
    equity = p_share - m_share + j_share
    _agree(card, "value", d.get("num") if isinstance(d.get("num"), (int, float)) else None, equity)
    value = d.get("value") or fmt(equity, spec)

    items = card.title_items()
    ctx = d.get("context")
    if ctx is None:
        ctx = f"**{_pct(pct)}** of value − mortgage" + (" + joint cash" if cash else "")
    head = _hero_head(card, d.get("value_label", "Your equity"), value, d.get("delta"), d.get("delta_note"), ctx,
                      size=d.get("size", 180), right=d.get("status"))

    home_eq = max(0.0, p_share - m_share)
    lf = Font.of("label")

    def stack_bar(x, y, w, h):
        if p_share <= 0:
            return
        bh = 16
        spans = share_bar(c, x, y, w, bh, [m_share, home_eq], [T.ASH, T.INK], gap=3)
        ly = y + bh + 18 + lf.cap
        ltv = m_share / p_share
        c.label((x, ly), f"{typo(d.get('mortgage_bar_label', 'Mortgage'))} {_pct(round(ltv, 3))}", T.MUTED)
        c.label((x + w, ly), f"{typo(d.get('equity_bar_label', 'Equity in home'))} {_pct(round(1 - ltv, 3))}",
                T.SOFT, anchor="rs")

    rf, sf = Font.of("row", 23), Font.of("whisper")
    nfnt = Font.of("row-num", 23)
    of = Font.of("stat-s", 26)
    ledger = [
        ("", typo(prop.get("label", "Property value")), typo(prop.get("sub", "")), _show(prop, spec), T.SOFT),
        ("×", typo(d.get("equity_label", "Ownership")), typo(d.get("equity_source", "")), _pct(pct), T.SOFT),
        ("=", "Your share of the home", "", fmt(p_share, spec), T.SOFT),
        ("−", typo(mort.get("label", "Mortgage share")),
         f"{_pct(m_pct)} of {_show(mort, spec)}" + (f" · {typo(mort['sub'])}" if mort.get("sub") else ""),
         fmt(-m_share, spec), T.SOFT),
    ]
    if cash:
        ledger.append(("+", typo(cash.get("label", "Joint cash share")),
                       f"{_pct(j_pct)} of {_show(cash, spec)}" + (f" · {typo(cash['sub'])}" if cash.get("sub") else ""),
                       fmt(j_share, spec, signed=True), T.SOFT))
    ledger.append(("=", typo(d.get("result_label", "Your equity")), "", typo(value), T.INK))

    def draw_ledger(x, y, w, h):
        rh = h / len(ledger)
        for i, (op, lab, sub, val, col) in enumerate(ledger):
            base = y + i * rh + rh / 2 + rf.cap / 2
            last = i == len(ledger) - 1
            if last:
                c.line([(x, y + i * rh), (x + w, y + i * rh)], T.HAIR, 1)
            if op:
                c.text((x + 10, base + 1), op, of, T.MUTED, anchor="ms")
            lx = x + 40
            font = Font.of("row-strong", 23) if last else rf
            c.text((lx, base), lab, font, T.INK if last else T.SOFT)
            vw = c.measure(val, nfnt)
            if sub:
                sx = lx + c.measure(lab, font) + 12
                c.text((sx, base), _fit(c, sub, sf, x + w - vw - 20 - sx), sf, T.FAINT)
            c.text((x + w, base), val, Font.of("row-num", 24) if last else nfnt, col, anchor="rs")

    body = [spring(0.5)] + head + [spring(0.5), Item(16 + 18 + lf.cap + 4, stack_bar, name="stack"), spring(0.5),
                                   B.eyebrow(card, typo(d.get("ledger_label", "How it's built"))), gap(6),
                                   Item(len(ledger) * 46, draw_ledger, flex=0.3, max_h=len(ledger) * 54,
                                        name="ledger")]
    f = B.facts(card, d.get("facts") or [], drop=1)
    body += [spring(0.4)]
    if f:
        body += [gap(12), f]
    card.stack(items + B.compact_items(body))
