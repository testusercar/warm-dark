"""State templates: hero, alert, empty, decision, experiment, vitals."""
from __future__ import annotations

from typing import Any

from .. import blocks as B
from .. import tokens as T
from ..canvas import Font
from ..charts import Lin, dot, gauge, share_bar
from ..layout import Card, Item, gap, spring
from ..text import Hero, Style, draw_block, draw_delta, fmt, parse_delta, text_block, typo
from . import template


@template("hero", "photo")
def hero_photo(card: Card) -> None:
    d = card.card
    items = card.title_items()
    body = B.compact_items([
        gap(14),
        B.text(card, d.get("body") or d.get("caption") or "", "row", T.SOFT, 3, strong_color=T.INK, name="body"),
        gap(40),
        B.image(card, d.get("image") or d.get("photo"), 300, anchor="center") or spring(1),
    ])
    f = B.facts(card, d.get("facts") or [])
    if f:
        body += [gap(36), f]
    card.stack(items + body)


SEVERITY = {
    "sev1": ("Sev 1", "solid"),
    "sev2": ("Sev 2", "outline"),
    "sev3": ("Sev 3", "quiet"),
    "info": ("Info", "quiet"),
    "resolved": ("Resolved", "olive"),
    "blocked": ("Blocked", "solid"),
    "alert": ("Alert", "outline"),
    "watch": ("Watch", "quiet"),
}


def _pill(card: Card, text: str, style: str, trailing: str = "") -> Item:
    c = card.c
    pf = Font("sans-semibold", 16, 20)
    tw = c.measure(text, pf)
    ph, px = 34, 16
    dot_w = 16 if style in ("outline", "quiet") else 0

    def draw(x, y, w, h):
        base = y + ph / 2 + pf.cap / 2
        x1 = x + tw + 2 * px + dot_w
        if style in ("solid", "olive"):
            c.rect(x, y, x1, y + ph, T.OLIVE if style == "olive" else T.INK, radius=ph / 2)
            c.text((x + px, base), text, pf, T.CANVAS)
        else:
            c.rect(x, y, x1, y + ph, T.SURFACE_HI, radius=ph / 2)
            c.circle((x + px + 4, y + ph / 2), 4, fill=T.INK if style == "outline" else T.MUTED)
            c.text((x + px + dot_w, base), text, pf, T.INK if style == "outline" else T.SOFT)
        if trailing:
            c.text((x1 + 16, base), typo(trailing), Font.of("small"), T.QUIET)

    return Item(ph, draw, name="pill")


def _rail(card: Card, events: list[dict[str, Any]]) -> Item:
    c = card.c
    tf, xf = Font.of("axis", 16), Font.of("row", 23, 30)
    time_w = max((c.measure(typo(e.get("time", "")), tf) for e in events), default=40) + 16
    tw = card.cw - time_w - 34
    rows = []
    for e in events:
        lines, _ = text_block(c, typo(e.get("text", "")), Style(xf, T.INK), tw, 2)
        rows.append((e, lines, len(lines) * xf.lh))
    g = 20
    total = sum(r[2] for r in rows) + g * (len(rows) - 1)

    def draw(x, y, w, h):
        rx = x + time_w + 8
        yy = y
        centers = []
        for e, lines, hh in rows:
            state = e.get("state", "done")
            col = T.MUTED if state == "done" else T.INK
            if state == "next":
                col = T.SOFT
            base = yy + xf.baseline_in()
            c.text((x + time_w - 8, base), typo(e.get("time", "")), tf, T.QUIET, anchor="rs")
            draw_block(c, rx + 26, yy, lines, Style(xf, col))
            centers.append((yy + xf.lh / 2, state))
            yy += hh + g
        if centers:
            c.line([(rx, centers[0][0]), (rx, centers[-1][0])], T.HAIR, 1.5)
        for cy, state in centers:
            if state == "now":
                c.circle((rx, cy), 10, fill=T.CANVAS)
                c.circle((rx, cy), 6.5, fill=T.INK)
            elif state == "next":
                c.circle((rx, cy), 9, fill=T.CANVAS)
                c.ring((rx, cy), 5.5, T.SOFT, 1.8)
            elif state == "ok":
                c.circle((rx, cy), 9, fill=T.CANVAS)
                c.circle((rx, cy), 5.5, fill=T.OLIVE)
            else:
                c.circle((rx, cy), 8, fill=T.CANVAS)
                c.circle((rx, cy), 4, fill=T.FAINT)

    return Item(total, draw, name="timeline", drop=1)


@template("alert", "incident", "status")
def alert(card: Card) -> None:
    d = card.card
    sev = str(d.get("severity") or "alert").lower()
    text, style = SEVERITY.get(sev, (sev.upper(), "outline"))
    status = typo(d.get("status", ""))
    pill_text = f"{text} · {status}" if status and status.upper() != text else text
    items: list[Item] = [_pill(card, pill_text, style, d.get("since", "")), gap(28)]
    items += card.title_items()
    body = B.compact_items([
        gap(22),
        B.text(card, d.get("body", ""), "body", T.INK, 3, name="body"),
        gap(10) if d.get("detail") else None,
        B.text(card, d.get("detail", ""), "row", T.MUTED, 2, name="detail"),
    ])
    f = B.facts(card, d.get("impact") or d.get("facts") or [], value_font="stat-s", drop=2)
    if f:
        body += [gap(34), f]
    tl = d.get("timeline") or []
    if tl:
        body += [spring(1), B.eyebrow(card, d.get("timeline_label", "Timeline")), gap(20), _rail(card, tl[:5])]
    body.append(spring(1))
    nxt = d.get("next")
    if nxt:
        if isinstance(nxt, str):
            nxt = {"text": nxt}
        body += [gap(24), B.callout(card, nxt.get("label", "Next"), nxt.get("text", ""), "lead",
                                    right=nxt.get("owner"), max_lines=2, hi=style == "solid", name="next")]
    card.stack(items + B.compact_items(body))


@template("empty", "no_data", "pending")
def empty(card: Card) -> None:
    d = card.card
    c = card.c
    items = card.title_items()
    shape = d.get("skeleton", "line")

    def skeleton(x, y, w, h):
        c.panel(x, y, x + w, y + h)
        x, y, w, h = x + T.PAD, y + T.PAD, w - 2 * T.PAD, h - 2 * T.PAD
        if shape != "list":
            for k in range(4):
                gy = y + h * (0.1 + k * 0.26)
                c.line([(x, gy), (x + w, gy)], T.DIVIDER, 1)
        if shape == "bars":
            n = 8
            for i in range(n):
                bh = h * (0.25 + 0.5 * ((i * 37) % 10) / 10)
                bx = x + i * w / n + w / n * 0.2
                c.rect(bx, y + h * 0.88 - bh, bx + w / n * 0.6, y + h * 0.88, T.TRACK_S, radius=6)
        elif shape == "list":
            for k, fy in enumerate((0.1, 0.27, 0.73, 0.9)):
                ly = y + h * fy
                c.circle((x + 9, ly), 7, fill=T.TRACK_S)
                c.rect(x + 36, ly - 7, x + 36 + w * (0.72 - 0.12 * (k % 2)), ly + 7, T.TRACK_S, radius=7)
        else:
            pts = [(x + w * i / 11, y + h * (0.62 - 0.28 * ((i * 7) % 5) / 5 - 0.02 * i)) for i in range(12)]
            c.dotted(pts, T.ASH, 1.6, 9)
        msg = typo(d.get("message", "No data yet"))
        mf = Font.of("quote", 38, 46)
        c.rect(x - 2, y + h / 2 - 46, x + w + 2, y + h / 2 + 36, T.SURFACE)
        c.text((x + w / 2, y + h / 2 + 8), msg, mf, T.SOFT, anchor="ms")

    body = B.compact_items([
        gap(36),
        Item(360, skeleton, flex=0.6, max_h=460, name="skeleton"),
        gap(36),
        B.text(card, d.get("reason", ""), "body", T.INK, 3, name="reason"),
        gap(12) if d.get("expected") else None,
        B.text(card, d.get("expected", ""), "row", T.MUTED, 3, name="expected"),
        spring(1),
    ])
    f = B.facts(card, d.get("facts") or [])
    if f:
        body += [gap(20), f]
    card.stack(items + body)


@template("decision", "ask", "approval")
def decision(card: Card) -> None:
    d = card.card
    c = card.c
    items = card.title_items(dek_lines=3)
    opts = list(d.get("options") or [])[:4]
    f_lab = Font.of("lead", 26, 34)
    f_det = Font.of("row", 22, 30)
    px, py = 24, 22
    key_w = 64
    tw = card.cw - 2 * px - key_w
    blocks: list[Item] = []
    for o in opts:
        rec = bool(o.get("recommended"))
        rec_lab = typo(d.get("recommended_label", "Recommended"))
        rw = c.label_width(rec_lab) + 16 if rec else 0
        l1, _ = text_block(c, typo(o.get("label", "")), Style(f_lab, T.INK), tw - rw, 2)
        l2, _ = text_block(c, typo(o.get("detail", "")), Style(f_det, T.MUTED), tw, 2) if o.get("detail") else ([], 0)
        inner = len(l1) * f_lab.lh + (2 + len(l2) * f_det.lh if l2 else 0)
        h = inner + 2 * py

        def draw(x, y, w, hh, o=o, l1=l1, l2=l2, rec=rec, rec_lab=rec_lab, inner=inner):
            c.panel(x, y, x + w, y + hh, hi=rec, radius=T.RADIUS - 4)
            yy = y + (hh - inner) / 2
            cy = yy + f_lab.lh / 2
            key = typo(o.get("key", "?"))
            kf = Font("display-medium", 22)
            kx = x + px + 22
            if rec:
                c.circle((kx, cy), 22, fill=T.INK)
                c.text((kx, cy + kf.cap / 2), key, kf, T.CANVAS, anchor="ms")
            else:
                c.circle((kx, cy), 22, fill=T.TRACK_S)
                c.text((kx, cy + kf.cap / 2), key, kf, T.SOFT, anchor="ms")
            tx = x + px + key_w
            draw_block(c, tx, yy, l1, Style(f_lab, T.INK))
            if rec:
                c.label((x + w - px, yy + f_lab.baseline_in()), rec_lab, T.OLIVE, anchor="rs")
            if l2:
                draw_block(c, tx, yy + len(l1) * f_lab.lh + 2, l2, Style(f_det, T.MUTED))

        blocks.append(Item(h, draw, name="option"))
    body: list[Item] = [gap(40)]
    for i, b in enumerate(blocks):
        body.append(b)
        if i < len(blocks) - 1:
            body += [gap(14), spring(1, max_h=14)]
    body.append(spring(2))
    if d.get("why"):
        body += [B.eyebrow(card, d.get("why_label", "Why")), gap(12),
                 B.text(card, d["why"], "row", T.SOFT, 3, name="why") or gap(0), gap(36), spring(0.8)]
    reply = d.get("reply") or "Reply " + ", ".join(typo(o.get("key", "")) for o in opts[:-1]) + (
        f" or {typo(opts[-1].get('key', ''))}" if len(opts) > 1 else "")
    if d.get("deadline"):
        body += [B.eyebrow(card, d["deadline"], None, T.MUTED), gap(10)]
    body.append(B.text(card, reply + (f" · {typo(d['default'])}" if d.get("default") else ""), "row", T.INK, 2,
                       name="reply") or gap(0))
    card.stack(items + body)


@template("experiment", "ab", "ab_test")
def experiment(card: Card) -> None:
    d = card.card
    c = card.c
    items = card.title_items()
    vs = list(d.get("variants") or [])[:4]
    vfmt = d.get("fmt", "{:.1f}%")
    winner = d.get("winner")
    head = B.compact_items([
        B.hero(card, d.get("verdict", "—"), size=d.get("size", 130), min_size=64),
        gap(24),
        B.delta(card, d.get("lift"), d.get("lift_note")),
        gap(12),
        B.text(card, d.get("confidence", ""), "dek", T.MUTED, 2, strong_color=T.INK, name="confidence"),
    ])
    lo = min((v.get("ci") or [v.get("rate", 0)] * 2)[0] for v in vs) if vs else 0
    hi = max((v.get("ci") or [v.get("rate", 0)] * 2)[1] for v in vs) if vs else 1
    span = (hi - lo) or 1
    lf, nf = Font.of("row-strong", 25), Font.of("row-num", 25)
    row_h = 92

    def plot(x, y, w, h):
        X = Lin(lo - span * 0.15, hi + span * 0.15, x, x + w)
        ctrl = next((v for v in vs if v.get("control")), vs[0] if vs else None)
        if ctrl is not None:
            cx = X(ctrl.get("rate", 0))
            c.dashed([(cx, y + 10), (cx, y + len(vs) * row_h - 8)], T.ASH, 1.4, (4, 5))
            c.text((cx, y + len(vs) * row_h + 26), d.get("control_label", "control"), Font.of("whisper", 15),
                   T.MUTED, anchor="ms")
        for i, v in enumerate(vs):
            top = y + i * row_h
            base = top + lf.cap
            is_win = winner is not None and (v.get("key") == winner or v.get("name") == winner)
            name = typo(v.get("name", ""))
            c.text((x, base), name, lf, T.INK)
            if v.get("label"):
                c.text((x + c.measure(name, lf) + 12, base), typo(v["label"]), Font.of("small"), T.MUTED)
            c.text((x + w, base), typo(v.get("display") or fmt(v.get("rate"), vfmt)), nf,
                   T.OLIVE if is_win and d.get("positive", True) else T.INK, anchor="rs")
            if v.get("n"):
                nlab = typo(v["n"]) if isinstance(v["n"], str) else f"n = {v['n']:,}"
                rw = c.measure(typo(v.get("display") or fmt(v.get("rate"), vfmt)), nf)
                c.text((x + w - rw - 16, base), nlab, Font.of("axis"), T.FAINT, anchor="rs")
            ty = base + 30
            c.line([(x, ty), (x + w, ty)], T.GRID, 1.5)
            ci = v.get("ci")
            col = (T.OLIVE if d.get("positive", True) else T.INK) if is_win else T.ASH
            if ci:
                c.rect(X(ci[0]), ty - 4, X(ci[1]), ty + 4, col if is_win else T.TRACK, radius=4)
            dot(c, (X(v.get("rate", 0)), ty), T.INK if not is_win else col, 6.5, 3)
        from ..text import nice_ticks

        ax = y + len(vs) * row_h + 4
        ctrl_x = X(ctrl.get("rate", 0)) if ctrl is not None else None
        for t in nice_ticks(lo - span * 0.15, hi + span * 0.15, 4):
            tx = X(t)
            if ctrl_x is not None and abs(tx - ctrl_x) < 40:
                continue
            c.text((tx, ax), fmt(t, vfmt.replace(".1f", ".0f") if float(t).is_integer() else vfmt),
                   Font.of("axis"), T.FAINT, anchor="ms")

    body = [spring(0.5)] + head + [spring(0.8), B.eyebrow(card, d.get("plot_label", "Rate with 95% interval")),
                                   gap(26), Item(len(vs) * row_h + 36, plot, name="plot"), spring(0.6)]
    f = B.facts(card, d.get("facts") or [], drop=1)
    if f:
        body += [gap(20), f]
    card.stack(items + body)


@template("vitals", "health", "sleep")
def vitals(card: Card) -> None:
    d = card.card
    c = card.c
    items = card.title_items()
    score = d.get("score")
    R = 84
    left_w = card.cw - (2 * R + 40 if score is not None else 0)
    hh = Hero(c, typo(d.get("value", "")), left_w, size=d.get("size", 132), min_size=64)
    dd = parse_delta(d.get("delta"), d.get("delta_note"))
    df = Font.of("delta", 25)
    ctx_lines = text_block(c, typo(d.get("context", "")), Style(Font.of("dek", 22, 30), T.MUTED), left_w, 2)[0] \
        if d.get("context") else []
    top_h = max(2 * R + 8, hh.cap + (22 + df.cap if dd else 0) + (14 + len(ctx_lines) * 30 if ctx_lines else 0))

    def top(x, y, w, h):
        hh.draw(x, y + hh.cap + 12)
        yy = y + hh.cap + 12
        if dd:
            draw_delta(c, x, yy + 22 + df.cap, dd, df, Font.of("dek", 22))
            yy += 22 + df.cap
        if ctx_lines:
            draw_block(c, x, yy + 14, ctx_lines, Style(Font.of("dek", 22, 30), T.MUTED))
        if score is not None:
            cx, cy = x + w - R, y + R + 4
            good = score >= d.get("score_good", 80)
            gauge(c, (cx, cy), R, 8, score / 100, T.OLIVE if good else T.INK)
            sf = Font.of("stat", 56)
            c.text((cx, cy + sf.cap / 2 - 8), f"{score:.0f}", sf, T.INK, anchor="ms")
            c.label((cx, cy + sf.cap / 2 + 22), d.get("score_label", "score"), T.MUTED, anchor="ms")

    stages = d.get("stages") or []
    sf = Font.of("small", 19)
    snf = Font.of("small-num", 19)

    def stage_bar(x, y, w, h):
        lf = Font.of("label")
        c.label((x, y + lf.cap), d.get("stages_label", "Stages"))
        share_bar(c, x, y + lf.cap + 16, w, 12, [s["minutes"] for s in stages], gap=3)
        yy = y + lf.cap + 16 + 16 + 30
        n = len(stages)
        colw = w / max(1, n)
        for i, s in enumerate(stages):
            cx = x + i * colw
            col = T.RAMP[min(i, len(T.RAMP) - 1)]
            c.circle((cx + 5, yy - sf.cap / 2), 5, fill=col)
            c.text((cx + 18, yy), typo(s.get("label", "")), sf, T.SOFT)
            m = int(s["minutes"])
            dur = f"{m // 60}h {m % 60:02d}m" if m >= 60 else f"{m}m"
            c.text((cx + 18, yy + 26), dur, snf, T.QUIET)

    hist = d.get("history") or {}

    def history(x, y, w, h):
        vals = hist.get("values") or []
        labs = hist.get("labels") or [""] * len(vals)
        lf = Font.of("label")
        c.label((x, y + lf.cap), hist.get("label", "Last 7 nights"))
        py0, py1 = y + lf.cap + 26, y + h - 30
        vmax = max(vals + [hist.get("goal") or 0]) * 1.08 or 1
        Y = Lin(0, vmax, py1, py0)
        n = len(vals)
        slot = w / max(1, n)
        bw = slot * 0.5
        for i, v in enumerate(vals):
            bx = x + slot * i + (slot - bw) / 2
            last = i == n - 1
            c.rect(bx, Y(v), bx + bw, py1, T.INK if last else T.ASH, radius=3, corners=(True, True, False, False))
            c.text((bx + bw / 2, py1 + 24), typo(labs[i]), Font.of("axis"), T.INK if last else T.FAINT, anchor="ms")
        if hist.get("goal"):
            gy = Y(hist["goal"])
            c.dashed([(x, gy), (x + w, gy)], T.MUTED, 1.4, (6, 5))
            c.text((x + w, gy - 8), typo(hist.get("goal_label", "goal")), Font.of("whisper", 15), T.MUTED,
                   anchor="rs")

    body: list[Item] = [gap(36), Item(top_h, top, name="top")]
    if stages:
        body += [spring(0.7), Item(Font.of("label").cap + 16 + 16 + 30 + 30, stage_bar, name="stages")]
    if hist.get("values"):
        body += [spring(0.7), Item(200, history, flex=0.5, max_h=260, name="history", drop=1)]
    body.append(spring(0.5))
    f = B.facts(card, d.get("facts") or [])
    if f:
        body += [gap(24), f]
    card.stack(items + body)
