"""List-shaped templates: brief, radar, timeline, holdings, roster, spend, cover."""
from __future__ import annotations

from typing import Any

from .. import blocks as B
from .. import tokens as T
from ..canvas import Font
from ..layout import Card, Item, gap, spring
from ..text import Hero, Style, draw_block, draw_delta, parse_delta, text_block, typo
from . import template


def _points(card: Card, key: str = "points") -> list[Any]:
    pts = list(card.card.get(key) or [])
    if len(pts) > T.MAX_PUNCHES:
        card.ctx.warnings.append(f"{len(pts)} {key} — capped at {T.MAX_PUNCHES}; split the card")
        pts = pts[: T.MAX_PUNCHES]
    return pts


@template("brief", "bullets", "watch", "list")
def brief(card: Card) -> None:
    d = card.card
    c = card.c
    watch = str(d.get("type", "")).lower() == "watch" or d.get("style") == "watch"
    items = card.title_items()
    pts = _points(card)
    indent = 40
    tw = card.cw - indent
    few = len(pts) <= 3
    f_lead = Font.of("lead", 30 if few else 27, 40 if few else 36)
    f_body = Font.of("body", 29 if few else 27, 40 if few else 38)
    f_sub = Font.of("row", 24 if few else 23, 34 if few else 32)
    st_lead = Style(f_lead, T.INK, Font("sans-semibold", f_lead.size, f_lead.lh), T.INK)
    st_body = Style(f_body, T.INK, Font.of("body-strong"), T.INK)
    st_sub = Style(f_sub, T.MUTED, Font("sans-medium", f_sub.size, f_sub.lh), T.SOFT)
    blocks: list[Item] = []
    for p in pts:
        if isinstance(p, dict):
            lead = typo(p.get("lead") or p.get("title") or "")
            body = typo(p.get("text") or p.get("body") or "")
            when = typo(p.get("when") or p.get("tag") or "")
        else:
            lead, body, when = "", typo(p), ""
        when_w = c.label_width(when) + 20 if when else 0
        if lead:
            l1, _ = text_block(c, lead, st_lead, tw - when_w, 2)
            l2, cut = text_block(c, body, st_sub, tw, 3) if body else ([], False)
            h = len(l1) * f_lead.lh + (6 + len(l2) * f_sub.lh if l2 else 0)
            first_font = f_lead
        else:
            l1, cut = text_block(c, body, st_body, tw - when_w, 3)
            l2 = []
            h = len(l1) * f_body.lh
            first_font = f_body
        if cut:
            card.ctx.warnings.append("a punch was truncated — cut copy")

        def draw(x, y, w, hh, l1=l1, l2=l2, lead=lead, when=when, ff=first_font):
            cy = y + ff.baseline_in() - ff.cap / 2
            if watch:
                c.ring((x + 8, cy), 6.5, T.OLIVE, 2)
            else:
                c.circle((x + 8, cy), 5.5, fill=T.OLIVE)
            if lead:
                draw_block(c, x + indent, y, l1, st_lead)
                if l2:
                    draw_block(c, x + indent, y + len(l1) * f_lead.lh + 6, l2, st_sub)
            else:
                draw_block(c, x + indent, y, l1, st_body)
            if when:
                c.label((x + w, y + ff.baseline_in()), when, T.QUIET, anchor="rs")

        blocks.append(Item(h, draw, name="point"))
    take = d.get("takeaway") or d.get("bottom_line")
    body: list[Item] = [gap(52)]
    for i, b in enumerate(blocks):
        body.append(b)
        if i < len(blocks) - 1:
            body += [gap(38), spring(1, max_h=72 if few else 44)]
    lower: list[Item] = []
    img = B.image(card, d.get("image"))
    if img:
        lower += [gap(36), img]
    if take:
        lower += [spring(3), B.callout(card, d.get("takeaway_label", "Bottom line"), take, name="takeaway")]
    else:
        lower.append(spring(3))
    card.stack(items + body + B.compact_items(lower))


ROW_F = 25
MINI_W = 80


def _money_rows(card: Card, rows: list[dict[str, Any]], total_assets: float, x: float, y: float, w: float,
                row_h: float, val_w: float) -> float:
    """Label · note ......... [mini share bar]  value (tabular, right-aligned)."""
    c = card.c
    lf, vf, sf = Font.of("row", ROW_F), Font.of("row-num", ROW_F), Font.of("whisper")
    yy = y
    bar_x1 = x + w - val_w - 26
    for r in rows:
        base = yy + (row_h + lf.cap) / 2
        lab = typo(r.get("label", ""))
        c.text((x, base), lab, lf, T.INK)
        if r.get("note"):
            c.text((x + c.measure(lab, lf) + 12, base), typo(r["note"]), sf, T.QUIET)
        num = r.get("num")
        val = typo(r.get("value", ""))
        neg = (num is not None and num < 0) or val.startswith("\u2212")
        c.text((x + w, base), val, vf, T.INK, anchor="rs")
        if num is not None and total_assets and not neg:
            by = base - lf.cap / 2 - 2
            c.rect(bar_x1 - MINI_W, by, bar_x1, by + 4, T.TRACK_S, radius=2)
            frac = min(1.0, abs(num) / total_assets)
            c.rect(bar_x1 - MINI_W, by, bar_x1 - MINI_W + max(4, MINI_W * frac), by + 4,
                   T.FAINT if neg else T.SOFT, radius=2)
        if r is not rows[-1]:
            c.line([(x, yy + row_h), (x + w, yy + row_h)], T.DIVIDER, 1)
        yy += row_h
    return yy - y


@template("roster", "balance_sheet", "accounts")
def roster(card: Card) -> None:
    d = card.card
    c = card.c
    items = card.title_items()
    groups = d.get("groups") or [{"label": "", "items": d.get("items") or []}]
    all_rows = [r for g in groups for r in g.get("items", [])]
    total_assets = sum((r.get("num") or 0) for r in all_rows if (r.get("num") or 0) > 0)
    vf = Font.of("row-num", ROW_F)
    val_w = max((c.measure(typo(r.get("value", "")), vf) for r in all_rows), default=0)
    row_h = 54 if len(all_rows) > 5 else 58
    lf = Font.of("label")
    px, py = 24, 4
    blocks: list[Item] = [gap(36)]
    for gi, g in enumerate(groups):
        rows = g.get("items", [])
        has_head = bool(g.get("label") or g.get("subtotal"))
        head_h = lf.cap + 14 if has_head else 0
        h = head_h + len(rows) * row_h + 2 * py

        def draw(x, y, w, hh, g=g, rows=rows, head_h=head_h):
            if head_h:
                c.label((x, y + lf.cap), typo(g.get("label", "")))
                if g.get("subtotal"):
                    c.text((x + w, y + lf.cap), typo(g["subtotal"]), Font.of("axis-strong", 17), T.MUTED,
                           anchor="rs")
            top = y + head_h
            c.panel(x, top, x + w, y + hh, radius=T.RADIUS - 4)
            _money_rows(card, rows, total_assets, x + px, top + py, w - 2 * px, row_h, val_w)

        blocks.append(Item(h, draw, name="group"))
        if gi < len(groups) - 1:
            blocks += [gap(26), spring(1, max_h=40)]
    tot = d.get("total") or {}
    lower: list[Item] = [gap(36), spring(1.4)]
    if tot:
        tf = Font.of("stat")
        sst = Style(Font.of("small"), T.QUIET)
        tot_w = Hero(c, typo(tot.get("value", "")), card.cw * 0.58, size=tf.size, min_size=40).width
        sub_lines = text_block(c, typo(tot["sub"]), sst, card.cw - tot_w - 36, 2)[0] if tot.get("sub") else []
        th = max(tf.cap, lf.cap + 12 + len(sub_lines) * sst.font.lh)

        def draw_total(x, y, w, hh):
            by = y + tf.cap
            c.text((x, y + lf.cap), typo(tot.get("label", "Total")), Font.of("row-strong", 22), T.INK)
            if sub_lines:
                draw_block(c, x, y + lf.cap + 12, sub_lines, sst)
            Hero(c, typo(tot.get("value", "")), w * 0.58, size=tf.size, min_size=40).draw(x + w, by, "r")

        lower.append(Item(th + 6, draw_total, name="total"))
    aside = d.get("aside")
    if aside:
        af = Font.of("row", 22)

        def draw_aside(x, y, w, hh):
            base = y + af.cap
            c.text((x, base), typo(aside.get("label", "")), af, T.MUTED)
            if aside.get("note"):
                lw = c.measure(typo(aside.get("label", "")), af)
                c.text((x + lw + 12, base), typo(aside["note"]), Font.of("whisper"), T.QUIET)
            c.text((x + w, base), typo(aside.get("value", "")), Font.of("row-num", 22), T.MUTED, anchor="rs")

        lower += [gap(26), Item(af.cap + 6, draw_aside, name="aside")]
    card.stack(items + blocks + lower)


@template("radar", "news", "headlines")
def radar(card: Card) -> None:
    d = card.card
    c = card.c
    items = card.title_items()
    pts = _points(card, "items")
    idx_w = 56
    tw = card.cw - idx_w
    f_idx = Font.of("index", 26)
    f_head = Font.of("lead", 27, 36)
    f_why = Font.of("row", 22, 30)
    f_src = Font.of("whisper", 15.5)
    st_head = Style(f_head, T.INK, Font("sans-semibold", 27, 36), T.INK)
    st_why = Style(f_why, T.MUTED, Font("sans-medium", 22, 30), T.SOFT)
    blocks: list[Item] = []
    for i, p in enumerate(pts):
        sig = typo(p.get("signal") or "")
        sig_w = c.label_width(sig) + 18 if sig else 0
        head, _ = text_block(c, typo(p.get("headline") or p.get("lead") or ""), st_head, tw - sig_w, 2)
        why, cut = text_block(c, typo(p.get("why") or p.get("text") or ""), st_why, tw, 2)
        if cut:
            card.ctx.warnings.append("radar 'why' truncated — cut copy")
        src = p.get("sources") or []
        src_line = "  ·  ".join(typo(s) for s in src)
        if p.get("when"):
            src_line = (src_line + "  ·  " if src_line else "") + typo(p["when"])
        h = len(head) * f_head.lh + (6 + len(why) * f_why.lh if why else 0) + (12 + f_src.lh if src_line else 0)

        def draw(x, y, w, hh, i=i, head=head, why=why, src_line=src_line, sig=sig):
            c.text((x, y + f_head.baseline_in()), f"{i + 1:02d}", f_idx, T.FAINT)
            tx = x + idx_w
            draw_block(c, tx, y, head, st_head)
            yy = y + len(head) * f_head.lh
            if why:
                draw_block(c, tx, yy + 6, why, st_why)
                yy += 6 + len(why) * f_why.lh
            if src_line:
                sy = yy + 12 + f_src.baseline_in()
                c.text((tx, sy), src_line, f_src, T.QUIET)
            if sig:
                c.label((x + w, y + f_head.baseline_in() - 2), sig, T.QUIET, anchor="rs")

        blocks.append(Item(h, draw, name="item"))
    body: list[Item] = [gap(48)]
    for i, b in enumerate(blocks):
        body.append(b)
        if i < len(blocks) - 1:
            body += [gap(34), spring(1, max_h=36)]
    take = d.get("takeaway")
    if take:
        body += [gap(36), spring(3), B.callout(card, d.get("takeaway_label", "Why it matters"), take,
                                               name="takeaway")]
    else:
        body.append(spring(3))
    card.stack(items + B.compact_items(body))


def _split_date(s: str) -> tuple[str, str]:
    parts = typo(s).split()
    if len(parts) >= 2 and parts[-1].isdigit():
        return " ".join(parts[:-1]), parts[-1]
    if len(parts) >= 2 and parts[0].isdigit():
        return " ".join(parts[1:]), parts[0]
    return "", typo(s)


@template("timeline", "agenda", "upcoming", "cadence")
def timeline(card: Card) -> None:
    d = card.card
    c = card.c
    items = card.title_items()
    evs = list(d.get("events") or [])[:6]
    if len(d.get("events") or []) > 6:
        card.ctx.warnings.append("timeline capped at 6 events")
    f_day = Font.of("stat-m", 42)
    f_txt = Font.of("row-strong", 25, 33)
    f_meta = Font.of("small", 18.5, 25)
    col_w = 92
    rail_x_off = col_w + 22
    tx_off = rail_x_off + 32
    tw = card.cw - tx_off
    rows = []
    for e in evs:
        lines, _ = text_block(c, typo(e.get("text", "")), Style(f_txt, T.INK), tw, 2)
        meta = typo(e.get("meta", ""))
        h = max(f_day.cap + 30, len(lines) * f_txt.lh + (6 + f_meta.lh if meta else 0))
        rows.append((e, lines, meta, h))
    total_h = sum(r[3] for r in rows)
    n = len(rows)

    def draw(x, y, w, hh):
        spare = max(0, hh - total_h)
        g = min(80, spare / max(1, n - 1)) if n > 1 else 0
        yy = y
        centers = []
        for e, lines, meta, h in rows:
            state = e.get("state", "next")
            mon, day = _split_date(e.get("date", ""))
            muted = state == "past"
            base = yy + f_day.cap
            c.text((x + col_w, base), day, f_day, T.FAINT if muted else T.INK, anchor="rs")
            sub = " · ".join(s for s in (typo(e.get("dow", "")), mon) if s)
            c.label((x + col_w, base + 25), sub, T.FAINT if muted else T.QUIET, anchor="rs", size=15.5)
            cy = yy + f_day.cap / 2
            centers.append((cy, state))
            tcol = T.MUTED if muted else T.INK
            st = Style(Font(f_txt.kind, f_txt.size, f_txt.lh), tcol)
            draw_block(c, x + tx_off, yy + f_day.cap / 2 - f_txt.lh / 2, lines, st)
            if meta:
                c.text((x + tx_off, yy + f_day.cap / 2 - f_txt.lh / 2 + len(lines) * f_txt.lh + 4 + f_meta.cap),
                       meta, f_meta, T.FAINT if muted else T.QUIET)
            if e.get("tag") and lines:
                from ..text import line_width

                tb = yy + f_day.cap / 2 - f_txt.lh / 2 + f_txt.baseline_in()
                c.label((x + tx_off + line_width(c, lines[0]) + 16, tb - 2), typo(e["tag"]), T.QUIET)
            yy += h + g
        rx = x + rail_x_off
        if centers:
            c.line([(rx, centers[0][0]), (rx, centers[-1][0])], T.HAIR, 1.5)
        for cy, state in centers:
            if state == "today" or state == "now":
                c.circle((rx, cy), 12, fill=T.CANVAS)
                c.circle((rx, cy), 7, fill=T.INK)
            elif state == "done":
                c.circle((rx, cy), 9, fill=T.CANVAS)
                c.circle((rx, cy), 6, fill=T.OLIVE)
            elif state == "past":
                c.circle((rx, cy), 8, fill=T.CANVAS)
                c.circle((rx, cy), 4, fill=T.FAINT)
            else:
                c.circle((rx, cy), 10, fill=T.CANVAS)
                c.ring((rx, cy), 6.5, T.SOFT if state == "next" else T.FAINT, 1.8)

    body: list[Item] = [gap(46), Item(total_h, draw, flex=1, max_h=total_h + 80 * max(0, n - 1), name="events")]
    if d.get("note"):
        body += [spring(1), B.callout(card, d.get("note_label", "Cadence"), d["note"], "row", max_lines=2,
                                      name="note")]
    else:
        body.append(spring(1))
    card.stack(items + B.compact_items(body))


@template("holdings", "portfolio", "positions")
def holdings(card: Card) -> None:
    d = card.card
    c = card.c
    items = card.title_items()
    rows = list(d.get("rows") or [])[:7]
    if len(d.get("rows") or []) > 7:
        card.ctx.warnings.append("holdings capped at 7 rows — roll the tail into 'Other'")
    nf, sf = Font.of("row-strong", 24), Font.of("whisper", 15.5)
    vf, pf = Font.of("row-num", 24), Font.of("axis-strong", 16)
    val_w = max((c.measure(typo(r.get("value", "")), vf) for r in rows), default=80)
    wmax = 100.0
    row_h = 72
    lf = Font.of("label", 15.5)
    head_cols = d.get("columns") or ["Holding", "Weight", "Value · P/L"]
    px, py = 24, 22

    def draw(x, y, w, hh):
        c.panel(x, y, x + w, y + hh)
        x, w = x + px, w - 2 * px
        y0 = y + py
        vx = x + w
        bar_w = 104
        bx1 = vx - max(val_w, 120) - 34
        bx0 = bx1 - bar_w
        c.label((x, y0 + lf.cap), head_cols[0], T.QUIET, size=15.5)
        c.label((bx0, y0 + lf.cap), head_cols[1], T.QUIET, size=15.5)
        c.label((vx, y0 + lf.cap), head_cols[2], T.QUIET, anchor="rs", size=15.5)
        yy = y0 + lf.cap + 14
        row_h = (hh - 2 * py - lf.cap - 14) / max(1, len(rows))
        for i, r in enumerate(rows):
            top = yy + i * row_h
            c.line([(x, top), (x + w, top)], T.DIVIDER, 1)
            base = top + (row_h - 26) / 2 + nf.cap / 2 - 2
            c.text((x, base), typo(r.get("name", "")), nf, T.INK)
            if r.get("sub"):
                c.text((x, base + 25), typo(r["sub"]), sf, T.QUIET)
            c.text((vx, base), typo(r.get("value", "")), vf, T.INK, anchor="rs")
            dd = parse_delta(r.get("pl"))
            if dd:
                draw_delta(c, vx, base + 25, dd, pf, align="r")
            wv = r.get("weight")
            if wv is not None:
                my = base - nf.cap / 2
                c.rect(bx0, my - 2, bx1, my + 2, T.TRACK_S, radius=2)
                c.rect(bx0, my - 2, bx0 + max(4, bar_w * wv / wmax), my + 2, T.SOFT, radius=2)
                c.text((bx0, base + 25), f"{wv:.0f}%" if isinstance(wv, (int, float)) else typo(wv),
                       Font.of("axis"), T.QUIET)

    base_h = 2 * py + lf.cap + 14
    body: list[Item] = [gap(36), Item(base_h + len(rows) * row_h, draw, flex=1,
                                      max_h=base_h + len(rows) * 104, name="table")]
    tot = d.get("total")
    body.append(spring(1))
    if tot:
        body += [gap(24), B.facts(card, [
            {"label": tot.get("label", "Total"), "value": tot.get("value", ""), "delta": tot.get("pl"),
             "sub": tot.get("sub")},
            *(d.get("facts") or [])[:2],
        ]) or gap(0)]
    card.stack(items + body)


@template("spend", "merchants", "spend_digest")
def spend(card: Card) -> None:
    from ..charts import hbar_rows

    d = card.card
    c = card.c
    items = card.title_items()
    ms = list(d.get("merchants") or [])[:6]
    if len(d.get("merchants") or []) > 6:
        card.ctx.warnings.append("spend capped at 6 merchants")
    days = d.get("days") or []
    day_labels = d.get("day_labels") or ["M", "T", "W", "T", "F", "S", "S"][: len(days)]

    hh = Hero(c, typo(d.get("value", "")), card.cw * (0.58 if days else 1), size=d.get("size", 120), min_size=64)
    dd = parse_delta(d.get("delta") if isinstance(d.get("delta"), dict) else
                     {"value": d.get("delta"), "polarity": "down_good"} if d.get("delta") else None,
                     d.get("delta_note"))
    df = Font.of("delta")
    head_h = hh.cap + (22 + df.cap if dd else 0) + 4

    def head(x, y, w, h):
        hh.draw(x, y + hh.cap)
        if dd:
            draw_delta(c, x, y + hh.cap + 22 + df.cap, dd, df)
        if days:
            bw, g = 16, 12
            n = len(days)
            tot_w = n * bw + (n - 1) * g
            x0 = x + w - tot_w
            vmax = max(days) or 1
            base = y + hh.cap
            hi_i = days.index(max(days))
            for i, v in enumerate(days):
                bh = max(4, (hh.cap - 6) * v / vmax)
                bx = x0 + i * (bw + g)
                c.rect(bx, base - bh, bx + bw, base, T.INK if i == hi_i else T.ASH, radius=bw / 2,
                       corners=(True, True, False, False))
                c.text((bx + bw / 2, base + 24), day_labels[i], Font.of("axis"), T.INK if i == hi_i else T.FAINT,
                       anchor="ms")

    rows = [{"label": m.get("name", ""), "sub": m.get("sub") or (f"{m['count']}×" if m.get("count") else None),
             "value": m.get("value", ""), "num": m.get("num"), "highlight": i == 0} for i, m in enumerate(ms)]
    rh = 64
    px, py = 24, 10

    def draw_rows(x, y, w, h):
        c.panel(x, y, x + w, y + h)
        hbar_rows(c, (x + px, y + py + 4, w - 2 * px, h - 2 * py), rows, row_h=(h - 2 * py) / max(1, len(rows)),
                  track=T.TRACK_S)

    body = [spring(0.4), Item(head_h, head, name="headline"), gap(50),
            B.eyebrow(card, d.get("rows_label", "Top merchants"), d.get("rows_right")), gap(16),
            Item(len(rows) * rh + 2 * py, draw_rows, flex=1, max_h=len(rows) * 80 + 2 * py, name="rows"),
            spring(0.4)]
    f = B.facts(card, d.get("facts") or [], drop=1)
    if f:
        body += [gap(20), f]
    card.stack(items + B.compact_items(body))


@template("cover", "digest", "series_cover")
def cover(card: Card) -> None:
    d = card.card
    c = card.c
    title = typo(d.get("title") or "Digest")
    tf = Font.of("title", 72)
    while c.measure(title, tf) > card.cw and tf.size > 50:
        tf = tf.sized(tf.size - 2)
    entries = list(d.get("items") or [])[:4]
    kicker = typo(d.get("kicker", ""))
    f_idx = Font.of("axis-strong", 16)
    f_t = Font.of("lead", 25, 32)
    f_n = Font.of("small", 18, 24)
    f_v = Font.of("stat-s", 28)
    row_h = 108
    px = 24
    dst = Style(Font.of("dek", 24, 34), T.MUTED)

    def head(x, y, w, h):
        yy = y
        if kicker:
            c.label((x, yy + Font.of("label").cap), kicker)
            yy += Font.of("label").cap + 24
        c.text((x, yy + tf.cap), title, tf, T.INK)
        if d.get("dek"):
            lines, _ = text_block(c, typo(d["dek"]), dst, w, 2)
            draw_block(c, x, yy + tf.cap + 22, lines, dst)

    dek_lines = len(text_block(c, typo(d.get("dek", "")), dst, card.cw, 2)[0]) if d.get("dek") else 0
    head_h = (Font.of("label").cap + 24 if kicker else 0) + tf.cap + (22 + dek_lines * 34 if dek_lines else 0)

    def rows(x, y, w, h):
        c.panel(x, y, x + w, y + h)
        x, w = x + px, w - 2 * px
        rh = h / max(1, len(entries))
        for i, e in enumerate(entries):
            top = y + i * rh
            if i:
                c.line([(x, top), (x + w, top)], T.DIVIDER, 1)
            base = top + rh / 2 - 2
            c.text((x, base - 1), f"{i + 1:02d}", f_idx, T.FAINT)
            tx = x + 44
            vtxt = typo(e.get("value", ""))
            vw = c.measure(vtxt, f_v) if vtxt else 0
            has_note = bool(e.get("note"))
            ty = base - (4 if has_note else -f_t.cap / 2 + 1)
            t_lines, _ = text_block(c, typo(e.get("title", "")), Style(f_t, T.INK), w - 44 - vw - 24, 1)
            draw_block(c, tx, ty - f_t.baseline_in(), t_lines, Style(f_t, T.INK))
            if has_note:
                n_lines, _ = text_block(c, typo(e["note"]), Style(f_n, T.QUIET), w - 44 - vw - 24, 1)
                draw_block(c, tx, base + 8, n_lines, Style(f_n, T.QUIET))
            if vtxt:
                dd = parse_delta(e.get("delta"))
                col = T.OLIVE if e.get("tone") == "positive" else T.INK
                vy = base - (4 if dd else -f_v.cap / 2 + 1)
                c.text((x + w, vy), vtxt, f_v, col, anchor="rs")
                if dd:
                    draw_delta(c, x + w, base + 26, dd, Font.of("axis-strong"), align="r")

    body = [spring(0.9), Item(head_h, head, name="head"), spring(1.1),
            Item(len(entries) * row_h, rows, name="contents"), gap(24)]
    body.append(B.eyebrow(card, d.get("count_label") or f"{len(entries)} cards follow", d.get("right_label")))
    card.stack(body)
