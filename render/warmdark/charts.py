"""Chart primitives. Rules: no boxes, no axis lines, no tick marks, no legends
when a direct label will do. Current = ink (olive only when above a reference
or explicitly positive), prior = faint, references = dashed muted.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

from . import tokens as T
from .canvas import Canvas, Font
from .text import Delta, fmt, nice_ticks, typo

Point = tuple[float, float]


class Lin:
    def __init__(self, d0: float, d1: float, r0: float, r1: float):
        self.d0, self.d1, self.r0, self.r1 = d0, d1, r0, r1

    def __call__(self, v: float) -> float:
        if self.d1 == self.d0:
            return (self.r0 + self.r1) / 2
        return self.r0 + (v - self.d0) / (self.d1 - self.d0) * (self.r1 - self.r0)


def monotone(pts: Sequence[Point], n: int = 12) -> list[Point]:
    """Fritsch–Carlson monotone cubic: smooth without overshooting data."""
    if len(pts) < 3:
        return list(pts)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    k = len(pts)
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(k - 1)]
    m = [d[0]] + [0.0] * (k - 2) + [d[-1]]
    for i in range(1, k - 1):
        m[i] = 0.0 if d[i - 1] * d[i] <= 0 else (d[i - 1] + d[i]) / 2
    for i in range(k - 1):
        if d[i] == 0:
            m[i] = m[i + 1] = 0.0
            continue
        a, b = m[i] / d[i], m[i + 1] / d[i]
        s = a * a + b * b
        if s > 9:
            t = 3 / math.sqrt(s)
            m[i], m[i + 1] = t * a * d[i], t * b * d[i]
    out: list[Point] = []
    for i in range(k - 1):
        h = xs[i + 1] - xs[i]
        for j in range(n):
            t = j / n
            h00 = 2 * t**3 - 3 * t**2 + 1
            h10 = t**3 - 2 * t**2 + t
            h01 = -2 * t**3 + 3 * t**2
            h11 = t**3 - t**2
            out.append((xs[i] + t * h, h00 * ys[i] + h10 * h * m[i] + h01 * ys[i + 1] + h11 * h * m[i + 1]))
    out.append(pts[-1])
    return out


def split_above(pts: Sequence[Point], ref_y) -> list[tuple[bool, list[Point]]]:
    """Split a pixel polyline into runs above/below ref_y(x) (above = smaller y)."""
    runs: list[tuple[bool, list[Point]]] = []
    cur: list[Point] = []
    state: bool | None = None
    prev: tuple[Point, float | None] | None = None
    for p in pts:
        r = ref_y(p[0])
        s = False if r is None else p[1] < r
        if prev is not None and s != state:
            pp, pr = prev
            if pr is not None and r is not None:
                d0, d1 = pp[1] - pr, p[1] - r
                t = d0 / (d0 - d1) if d0 != d1 else 0.5
                cross = (pp[0] + (p[0] - pp[0]) * t, pp[1] + (p[1] - pp[1]) * t)
            else:
                cross = pp
            cur.append(cross)
            runs.append((bool(state), cur))
            cur = [cross]
        state = s
        cur.append(p)
        prev = (p, r)
    runs.append((bool(state), cur))
    runs = [(s, r) for s, r in runs if len(r) >= 2]
    # Absorb slivers (a hair's dip across the reference) into the neighbouring run.
    merged: list[tuple[bool, list[Point]]] = []
    for s, r in runs:
        length = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(r, r[1:]))
        if merged and (length < 10 or s == merged[-1][0]):
            merged[-1] = (merged[-1][0], merged[-1][1] + r[1:])
        else:
            merged.append((s, r))
    return merged


def dot(c: Canvas, p: Point, fill: str, r: float = 5.5, halo: float = 3.5) -> None:
    if halo:
        c.circle(p, r + halo, fill=T.CANVAS)
    c.circle(p, r, fill=fill)


def domain(values: Sequence[float], zero: bool = False, pad: float = 0.1,
           lo: float | None = None, hi: float | None = None, target: int = 4) -> tuple[float, float, list[float]]:
    vals = [v for v in values if v is not None]
    a, b = (min(vals), max(vals)) if vals else (0.0, 1.0)
    if zero:
        a, b = min(0.0, a), max(0.0, b)
    span = (b - a) or abs(b) or 1.0
    a2 = a if (zero and a == 0) else a - span * pad
    b2 = b + span * pad
    if lo is not None:
        a2 = lo
    if hi is not None:
        b2 = hi
    ticks = nice_ticks(a2, b2, target)
    if len(ticks) >= 2:
        step = ticks[1] - ticks[0]
        if ticks[-1] < b and hi is None:
            ticks.append(round(ticks[-1] + step, 10))
        if ticks[0] > a and lo is None and not zero:
            ticks.insert(0, round(ticks[0] - step, 10))
    d0 = min(a2, ticks[0]) if ticks else a2
    d1 = max(b2, ticks[-1]) if ticks else b2
    return d0, d1, ticks


def axis_labels(ticks: Sequence[float], spec: str) -> list[str]:
    """Consistent compact axis: 0 · 0.5k · 1k, never 500 next to 1k."""
    if "{:k}" in spec and ticks and max(abs(t) for t in ticks) >= 1000:
        out = []
        for t in ticks:
            if t == 0:
                out.append(spec.replace("{:k}", "0"))
            else:
                out.append(fmt(t, spec.replace("{:k}", f"{abs(t) / 1000:g}k").replace("{", "{{").replace("}", "}}")))
        return out
    return [fmt(t, spec) for t in ticks]


def auto_ticks(n: int, want: int = 4) -> list[int]:
    if n <= 1:
        return [0]
    if n <= want:
        return list(range(n))
    step = (n - 1) / (want - 1)
    return sorted({round(i * step) for i in range(want)})


# ---------------------------------------------------------------- line chart

ROLE_STYLE = {
    "current": (T.INK, T.LINE_W),
    "prior": (T.FAINT, T.PRIOR_W),
    "reference": (T.MUTED, T.REF_W),
    "target": (T.MUTED, T.REF_W),
    "projection": (T.MUTED, 1.8),
}


def line_chart(c: Canvas, box: tuple[float, float, float, float], spec: dict[str, Any]) -> dict[str, Any]:
    x, y, w, h = box
    series = [s for s in spec.get("series", []) if s.get("values")]
    steps = spec.get("steps") or []
    refs = spec.get("refs") or []
    ann = spec.get("annotations") or []
    vfmt = spec.get("fmt") or "{:,.0f}"
    afmt = spec.get("axis_fmt") or vfmt
    n = max((len(s["values"]) for s in series), default=2)
    f_axis, f_end, f_end2 = Font.of("axis"), Font.of("axis-strong"), Font.of("whisper", 15)

    allv: list[float] = [v for s in series for v in s["values"] if v is not None]
    for st in steps:
        allv += [p[1] for p in st.get("points", [])]
    allv += [r["value"] for r in refs if r.get("value") is not None]
    d0, d1, ticks = domain(allv, spec.get("zero", False), spec.get("pad", 0.12),
                           spec.get("y_min"), spec.get("y_max"), spec.get("ticks", 4))
    show_grid = spec.get("grid", True)
    show_y = spec.get("y_labels", show_grid)
    tick_labels = axis_labels(ticks, afmt) if show_y else []
    gutter_l = (max((c.measure(t, f_axis) for t in tick_labels), default=0) + 14) if show_y else 0

    end_labels: list[dict[str, Any]] = []
    if spec.get("end_labels", True):
        for s in series:
            vals = [v for v in s["values"] if v is not None]
            if not vals or s.get("end_label") is False:
                continue
            role = s.get("role", "current")
            last_i = max(i for i, v in enumerate(s["values"]) if v is not None)
            end_labels.append({"v": vals[-1], "i": last_i,
                               "t1": typo(s.get("label") or fmt(vals[-1], vfmt)),
                               "t2": typo(s.get("name") or ""), "role": role,
                               "inline": last_i < n - 1 and n > 2,
                               "rising": len(vals) < 2 or vals[-1] >= vals[-2]})
        for st in steps:
            if st.get("points") and st.get("label", True) is not False:
                v = st["points"][-1][1]
                end_labels.append({"v": v, "i": n - 1, "t1": typo(st.get("label") or fmt(v, vfmt)),
                                   "t2": typo(st.get("name") or ""), "role": "reference"})
        for r in refs:
            end_labels.append({"v": r["value"], "i": n - 1, "t1": typo(r.get("label") or fmt(r["value"], vfmt)),
                               "t2": typo(r.get("name") or ""), "role": "reference"})
    gutter_labels = [e for e in end_labels if not e.get("inline")]
    gutter_r = (max((max(c.measure(e["t1"], f_end), c.measure(e["t2"], f_end2)) for e in gutter_labels),
                    default=0) + 18) if gutter_labels else 0
    gutter_r = spec.get("gutter_r", gutter_r)

    rows = 0
    if ann:
        rows = 1 if len(ann) == 1 else 2
    top_pad = rows * 46 + (14 if rows else 8)
    bottom_pad = 34 if spec.get("x") else 8
    bleed = spec.get("bleed")
    px0 = x + gutter_l
    px1 = x + w - gutter_r
    if bleed:
        px0, px1 = bleed
    py0, py1 = y + top_pad, y + h - bottom_pad
    X = Lin(0, max(1, n - 1), px0, px1)
    Y = Lin(d0, d1, py1, py0)

    if show_grid:
        for t, lab in zip(ticks, tick_labels or [None] * len(ticks)):
            gy = Y(t)
            if py0 - 2 <= gy <= py1 + 2:
                c.line([(x + gutter_l if not bleed else px0, gy), (px1, gy)], T.GRID, 1)
                if lab:
                    c.text((x + gutter_l - 14, gy + f_axis.cap / 2), lab, f_axis, T.FAINT, anchor="rs")
    if spec.get("baseline") or spec.get("zero"):
        by = Y(max(d0, 0) if d0 <= 0 <= d1 else d0)
        c.line([(px0, by), (px1, by)], T.HAIR, 1)

    def pts_of(vals: Sequence[float | None]) -> list[Point]:
        return [(X(i), Y(v)) for i, v in enumerate(vals) if v is not None]

    ref_fn = None
    step_polys: list[list[Point]] = []
    for st in steps:
        sp = sorted(st.get("points", []), key=lambda p: p[0])
        poly: list[Point] = []
        for j, (i0, v) in enumerate(sp):
            i1 = sp[j + 1][0] if j + 1 < len(sp) else n - 1
            if poly:
                poly.append((X(i0), poly[-1][1]))
            poly.append((X(i0), Y(v)))
            poly.append((X(i1), Y(v)))
        step_polys.append(poly)
        if ref_fn is None and sp:
            def ref_fn(px: float, sp=sp) -> float | None:
                idx = (px - px0) / (px1 - px0) * (n - 1) if px1 != px0 else 0
                cur = None
                for i0, v in sp:
                    if idx + 1e-6 >= i0:
                        cur = v
                return None if cur is None else Y(cur)
    for r in refs:
        if ref_fn is None and r.get("above"):
            ry = Y(r["value"])
            ref_fn = lambda px, ry=ry: ry  # noqa: E731

    smooth = spec.get("smooth", True)
    cur_series = next((s for s in series if s.get("role", "current") == "current"), series[0] if series else None)
    geo: dict[str, Any] = {"X": X, "Y": Y, "plot": (px0, py0, px1, py1)}

    if spec.get("area") and cur_series:
        pts = pts_of(cur_series["values"])
        dense = monotone(pts) if smooth else pts
        base = Y(max(d0, 0)) if spec.get("zero") else py1
        if dense:
            tint = T.OLIVE if cur_series.get("color") == "olive" else T.INK
            c.fade([(dense[0][0], base)] + dense + [(dense[-1][0], base)], tint,
                   min(p[1] for p in dense), base, T.AREA_ALPHA * (0.8 if tint == T.OLIVE else 1.0))

    for r in refs:
        ry = Y(r["value"])
        c.dashed([(px0, ry), (px1, ry)], T.MUTED if r.get("strong") else T.FAINT, T.REF_W, (6, 6))
    for poly in step_polys:
        c.dashed(poly, T.MUTED, T.REF_W, (6, 6))

    for s in sorted(series, key=lambda s: 0 if s.get("role") in ("prior", "reference", "target", "projection") else 1):
        role = s.get("role", "current")
        col, wid = ROLE_STYLE.get(role, ROLE_STYLE["current"])
        if s.get("color") == "olive":
            col = T.OLIVE
        pts = pts_of(s["values"])
        dense = monotone(pts) if (smooth and s.get("smooth", True)) else pts
        if role in ("reference", "target"):
            c.dashed(dense, col, wid, (6, 6))
            continue
        if role == "projection":
            c.dotted(dense, col, wid * 0.62, 7)
            continue
        if role == "current" and ref_fn is not None and spec.get("above", True):
            for above, run in split_above(dense, ref_fn):
                c.line(run, T.OLIVE if above else col, wid, round_caps=True)
        else:
            c.line(dense, col, wid, round_caps=True)
        geo.setdefault("pts", {})[s.get("name") or role] = pts

    cur_pts = pts_of(cur_series["values"]) if cur_series else []

    def line_y_at(px: float) -> float | None:
        for (x0, y0), (x1, y1) in zip(cur_pts, cur_pts[1:]):
            if x0 <= px <= x1:
                return y0 + (y1 - y0) * ((px - x0) / (x1 - x0) if x1 != x0 else 0)
        return None

    for mk in spec.get("markers") or []:
        i = mk["at"]
        v = mk.get("value")
        if v is None and cur_series:
            v = cur_series["values"][i]
        p = (X(i), Y(v))
        c.circle(p, 7, fill=T.CANVAS)
        c.ring(p, 5, T.MUTED, 1.6)
        if mk.get("label"):
            lab = typo(mk["label"])
            lw = c.measure(lab, f_end2)
            best, best_score = None, -1.0
            for dx, dy, anchor in ((9, 25, "ls"), (-9, 25, "rs"), (9, -14, "ls"), (-9, -14, "rs")):
                lx0 = p[0] + dx if anchor == "ls" else p[0] + dx - lw
                ly = p[1] + dy
                if lx0 < px0 - 4 or lx0 + lw > px1 + 4:
                    continue
                score = 1e9
                for k in range(9):
                    yy = line_y_at(lx0 + lw * k / 8)
                    if yy is not None:
                        score = min(score, abs(yy - (ly - f_end2.cap / 2)))
                if score > best_score:
                    best, best_score = (p[0] + dx, ly, anchor), score
            if best:
                c.text((best[0], best[1]), lab, f_end2, T.MUTED, anchor=best[2])

    if cur_series:
        pts = pts_of(cur_series["values"])
        if pts and spec.get("end_dot", True):
            last_col = T.INK
            if ref_fn is not None:
                rv = ref_fn(pts[-1][0] - 0.01)
                if rv is not None and pts[-1][1] < rv:
                    last_col = T.OLIVE
            if cur_series.get("color") == "olive" or spec.get("positive"):
                last_col = T.OLIVE
            dot(c, pts[-1], last_col)
        geo["last"] = pts[-1] if pts else None
    for s in series:
        if s.get("role") == "prior":
            pts = pts_of(s["values"])
            if pts:
                c.circle(pts[-1], 3.5, fill=T.FAINT)

    # annotations: dot on the line, dotted leader up to a label row
    if ann and cur_series:
        polys = [pts_of(s["values"]) for s in series]

        def clear(x0: float, x1: float, top: float, bot: float) -> bool:
            for poly in polys:
                for (ax, ay), (bx, by) in zip(poly, poly[1:]):
                    if bx < x0 or ax > x1:
                        continue
                    for k in range(5):
                        t = k / 4
                        qx, qy = ax + (bx - ax) * t, ay + (by - ay) * t
                        if x0 <= qx <= x1 and top <= qy <= bot:
                            return False
            return all(bot < pt or top > pb or x1 < pl or x0 > pr for pl, pt, pr, pb in placed)

        placed: list[tuple[float, float, float, float]] = []
        for j, a in enumerate(sorted(ann, key=lambda a: a["at"])):
            s = next((q for q in series if q.get("name") == a.get("series")), cur_series)
            i = int(a["at"])
            v = s["values"][i]
            p = (X(i), Y(v))
            row = j % rows if rows > 1 else 0
            t1, t2 = typo(a.get("text", "")), typo(a.get("sub", ""))
            wlab = max(c.measure(t1, f_end), c.measure(t2, f_end2))
            right_side = p[0] > (px0 + px1) / 2
            anchor = "rs" if right_side else "ls"
            tx = p[0] + (6 if not right_side else -6)
            tx = min(max(tx, x + (wlab if right_side else 0)), x + w - (0 if right_side else wlab))
            lx0, lx1 = (tx - wlab, tx) if right_side else (tx, tx + wlab)
            ly = y + 20 + row * 46
            cand = p[1] - 64
            while cand > ly:
                if clear(lx0 - 6, lx1 + 6, cand - 20, cand + 32):
                    ly = cand
                    break
                cand -= 12
            placed.append((lx0, ly - 16, lx1, ly + 26))
            c.dotted([(p[0], ly + 24), (p[0], p[1] - 10)], T.ASH, 1.0, 5)
            c.text((tx, ly), t1, f_end, T.INK, anchor=anchor)
            if t2:
                c.text((tx, ly + 19), t2, f_end2, T.MUTED, anchor=anchor)
            dot(c, p, T.OLIVE if a.get("positive") else T.INK, 4.5, 3)
    for e in [e for e in end_labels if e.get("inline")]:
        px, py = X(e["i"]), Y(e["v"])
        col1 = {"current": T.OLIVE if spec.get("positive") else T.INK, "prior": T.MUTED}.get(e["role"], T.MUTED)
        if e["rising"]:
            c.text((px - 14, py - 34 if e["t2"] else py - 16), e["t1"], f_end, col1, anchor="rs")
            if e["t2"]:
                c.text((px - 14, py - 15), e["t2"], f_end2, T.FAINT, anchor="rs")
        else:
            c.text((px + 14, py + 30), e["t1"], f_end, col1, anchor="ls")
            if e["t2"]:
                c.text((px + 14, py + 49), e["t2"], f_end2, T.FAINT, anchor="ls")
    end_labels = [e for e in end_labels if not e.get("inline")]
    if end_labels:
        for e in end_labels:
            e["y"] = Y(e["v"])
        end_labels.sort(key=lambda e: e["y"])
        minsep = 40
        for k in range(1, len(end_labels)):
            if end_labels[k]["y"] - end_labels[k - 1]["y"] < minsep:
                end_labels[k]["y"] = end_labels[k - 1]["y"] + minsep
        overflow = end_labels[-1]["y"] - (py1 + 6)
        if overflow > 0:
            for e in end_labels:
                e["y"] -= overflow
        lx = px1 + 16
        for e in end_labels:
            col1 = {"current": T.INK, "prior": T.MUTED}.get(e["role"], T.MUTED)
            if e["role"] == "current" and geo.get("last") is not None and ref_fn is not None:
                rv = ref_fn(geo["last"][0] - 0.01)
                if rv is not None and geo["last"][1] < rv:
                    col1 = T.OLIVE
            if e["role"] == "current" and spec.get("positive"):
                col1 = T.OLIVE
            ty = e["y"] + (f_end.cap / 2 if not e["t2"] else -1)
            c.text((lx, ty), e["t1"], f_end, col1)
            if e["t2"]:
                c.text((lx, ty + 19), e["t2"], f_end2, T.FAINT)

    xl = spec.get("x")
    if xl:
        idx = spec.get("x_ticks") or auto_ticks(len(xl), spec.get("x_count", 4))
        for i in idx:
            if i >= len(xl) or not xl[i]:
                continue
            anchor = "ls" if i == 0 else "rs" if i == len(xl) - 1 else "ms"
            if bleed and i == 0:
                anchor = "ls"
            px = X(i)
            if bleed:
                px = min(max(px, x), x + w)
            c.text((px, py1 + 28), typo(xl[i]), f_axis, T.FAINT, anchor=anchor)
    return geo


# ----------------------------------------------------------------- bar charts


def vbars(c: Canvas, box: tuple[float, float, float, float], spec: dict[str, Any]) -> None:
    x, y, w, h = box
    cats = [typo(k) for k in spec["categories"]]
    series = spec["series"]
    stacked = spec.get("stacked", False)
    vfmt = spec.get("fmt") or "{:,.0f}"
    hi = spec.get("highlight")
    hi_idx = cats.index(typo(hi)) if isinstance(hi, str) and typo(hi) in cats else hi if isinstance(hi, int) else None
    n = len(cats)
    if stacked and hi_idx is None:
        hi_idx = n - 1
    f_axis, f_val = Font.of("axis"), Font.of("axis-strong")
    if stacked:
        totals = [sum((s["values"][i] or 0) for s in series) for i in range(n)]
        vmax = max(totals) if totals else 1
    else:
        vmax = max((v or 0) for s in series for v in s["values"]) or 1
    top_pad, bot_pad = 34, 36
    py0, py1 = y + top_pad, y + h - bot_pad
    Y = Lin(0, vmax * 1.04, py1, py0)
    slot = w / n
    grouped = len(series) > 1 and not stacked
    bw = min(slot * (0.6 if grouped else 0.42), 92 if grouped else 56)
    rad = min(bw / 2, 8)
    c.line([(x, py1), (x + w, py1)], T.GRID, 1)
    for i in range(n):
        cx = x + slot * (i + 0.5)
        is_hi = hi_idx == i
        if stacked:
            base = py1
            for k, s in enumerate(series):
                v = s["values"][i] or 0
                top = base - (py1 - Y(v))
                ramp = T.RAMP if is_hi else T.STACK
                col = ramp[min(k, len(ramp) - 1)]
                c.rect(cx - bw / 2, top + (2 if k else 0), cx + bw / 2, base, col,
                       radius=rad if k == len(series) - 1 else 0,
                       corners=(True, True, False, False))
                base = top
            label_v = sum((s["values"][i] or 0) for s in series)
            c.text((cx, base - 10), fmt(label_v, vfmt), f_val if is_hi else f_axis, T.INK if is_hi else T.MUTED,
                   anchor="ms")
        elif grouped:
            gw = (bw - 4) / len(series)
            for k, s in enumerate(series):
                v = s["values"][i] or 0
                role = s.get("role", "current" if k == len(series) - 1 else "prior")
                col = T.INK if role == "current" else T.ASH
                if role == "current" and s.get("good_positive") and is_hi:
                    col = T.OLIVE
                bx = cx - bw / 2 + k * (gw + 4)
                c.rect(bx, Y(v), bx + gw, py1, col, radius=min(gw / 2, 8), corners=(True, True, False, False))
            cur = series[-1]["values"][i] or 0
            c.text((cx + bw / 2 - (bw - 4) / len(series) / 2, Y(cur) - 10), fmt(cur, vfmt),
                   f_val if is_hi else f_axis, T.INK if is_hi else T.MUTED, anchor="ms")
        else:
            v = series[0]["values"][i] or 0
            col = (T.OLIVE if spec.get("highlight_positive") else T.INK) if is_hi else (
                T.ASH if hi_idx is not None else T.SOFT)
            c.rect(cx - bw / 2, Y(v), cx + bw / 2, py1, col, radius=rad, corners=(True, True, False, False))
            if spec.get("value_labels", True):
                c.text((cx, Y(v) - 10), fmt(v, vfmt), f_val if is_hi else f_axis,
                       T.INK if is_hi else T.MUTED, anchor="ms")
        c.text((cx, py1 + 27), cats[i], f_val if is_hi else f_axis, T.INK if is_hi else T.FAINT, anchor="ms")


def hbar_rows(c: Canvas, box: tuple[float, float, float, float], rows: list[dict[str, Any]],
              vmax: float | None = None, row_h: float = 66, bar_h: float = 6,
              label_font: Font | None = None, value_font: Font | None = None,
              track: str = T.GRID, dividers: bool = False) -> float:
    """Ranked rows: label left, value right, thin bar underneath. Returns height used."""
    x, y, w, _ = box
    lf = label_font or Font.of("row")
    vf = value_font or Font.of("row-num")
    sf = Font.of("whisper")
    vmax = vmax or max((abs(r.get("num") or 0) for r in rows), default=1) or 1
    yy = y
    for r in rows:
        hi = r.get("highlight")
        base = yy + lf.cap + 6
        label = typo(r.get("label", ""))
        c.text((x, base), label, lf, T.INK)
        if r.get("sub"):
            c.text((x + c.measure(label, lf) + 12, base), typo(r["sub"]), sf, T.QUIET)
        vx = x + w
        if r.get("delta") is not None:
            d: Delta = r["delta"]
            from .text import delta_width, draw_delta

            df = Font.of("axis-strong")
            dw = delta_width(c, d, df)
            draw_delta(c, vx, base, d, df, align="r")
            vx -= dw + 18
        c.text((vx, base), typo(r.get("value", "")), vf, T.INK, anchor="rs")
        by = base + 15
        c.rect(x, by, x + w, by + bar_h, track, radius=bar_h / 2)
        frac = max(0.0, min(1.0, abs(r.get("num") or 0) / vmax))
        if frac > 0:
            col = r.get("color") or (T.OLIVE if hi == "positive" else T.INK if hi else T.ASH)
            c.rect(x, by, x + max(bar_h, w * frac), by + bar_h, col, radius=bar_h / 2)
        if dividers and r is not rows[-1]:
            c.line([(x, yy + row_h), (x + w, yy + row_h)], T.DIVIDER, 1)
        yy += row_h
    return yy - y


def share_bar(c: Canvas, x: float, y: float, w: float, h: float, parts: Sequence[float],
              colors: Sequence[str] | None = None, gap: float = 3.0) -> list[tuple[float, float]]:
    total = sum(max(0, p) for p in parts) or 1
    colors = colors or T.RAMP
    spans = []
    cx = x
    avail = w - gap * (len(parts) - 1)
    for i, p in enumerate(parts):
        seg = avail * max(0, p) / total
        col = colors[min(i, len(colors) - 1)]
        r = h / 2 if (i == 0 or i == len(parts) - 1) else 0
        corners = (i == 0, i == len(parts) - 1, i == len(parts) - 1, i == 0)
        c.rect(cx, y, cx + seg, y + h, col, radius=r if r else 0, corners=corners if r else None)
        spans.append((cx, cx + seg))
        cx += seg + gap
    return spans


def donut(c: Canvas, center: Point, r: float, width: float, parts: Sequence[float],
          colors: Sequence[str] | None = None, gap_deg: float = 1.6) -> None:
    total = sum(max(0, p) for p in parts) or 1
    colors = colors or T.RAMP
    a = 0.0
    for i, p in enumerate(parts):
        sweep = 360 * max(0, p) / total
        if sweep <= gap_deg:
            a += sweep
            continue
        c.arc(center, r, a + gap_deg / 2, a + sweep - gap_deg / 2, colors[min(i, len(colors) - 1)], width)
        a += sweep


def gauge(c: Canvas, center: Point, r: float, width: float, frac: float, color: str = T.INK) -> None:
    c.arc(center, r, 0, 360, T.TRACK, width)
    frac = max(0.0, min(1.0, frac))
    if frac > 0:
        c.arc(center, r, 0, 360 * frac, color, width)
        a = math.radians(360 * frac)
        rr = r - width / 2
        for ang in (0.0, a):
            c.circle((center[0] + rr * math.sin(ang), center[1] - rr * math.cos(ang)), width / 2, fill=color)
