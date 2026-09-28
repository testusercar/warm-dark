"""Manifest → PNGs."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .layout import Card, Ctx
from .templates import ALIASES, REGISTRY, resolve

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "refs" / "manifest.schema.json"
SCHEMA_VERSION = 2

_GROSS = re.compile(r"\bgross\b", re.I)


@dataclass
class Result:
    path: Path
    type: str
    slug: str
    warnings: list[str] = field(default_factory=list)


def _strings(o: Any):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v)


def lint(card: dict[str, Any]) -> list[str]:
    out = []
    if any(_GROSS.search(s) for s in _strings(card)):
        out.append("mentions 'gross' — earnings figures are seller net only unless the user asked")
    title = str(card.get("title") or "")
    if len(title) > 28:
        out.append(f"title is {len(title)} chars — aim for 1–3 words")
    return out


def validate(manifest: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    try:
        import jsonschema  # type: ignore
    except ImportError:
        jsonschema = None
    if jsonschema and SCHEMA_PATH.is_file():
        schema = json.loads(SCHEMA_PATH.read_text())
        v = jsonschema.Draft202012Validator(schema)
        for e in sorted(v.iter_errors(manifest), key=lambda e: list(e.path)):
            loc = "/".join(str(p) for p in e.path) or "(root)"
            errs.append(f"{loc}: {e.message}")
    for i, card in enumerate(manifest.get("cards") or []):
        t = resolve(str(card.get("type") or "brief"))
        if t not in REGISTRY:
            errs.append(f"cards/{i}: unknown type {card.get('type')!r}")
    return errs


def _resolve_images(card: dict[str, Any], base: Path | None) -> dict[str, Any]:
    if base is None:
        return card
    out = dict(card)
    for key in ("image", "photo"):
        v = out.get(key)
        if isinstance(v, str) and v and not Path(v).is_absolute():
            out[key] = str((base / v).resolve())
    return out


def render_manifest(manifest: dict[str, Any], outdir: Path, scale: float | None = None,
                    only: set[str] | None = None, base_dir: Path | None = None) -> list[Result]:
    cards = list(manifest.get("cards") or [])
    series = manifest.get("series")
    if series is None:
        series = any(resolve(str(c.get("type"))) == "cover" for c in cards)
    scale = float(scale or manifest.get("scale") or 1)
    outdir.mkdir(parents=True, exist_ok=True)
    results: list[Result] = []
    for i, card in enumerate(cards):
        typ = resolve(str(card.get("type") or "brief"))
        slug = str(card.get("slug") or f"{i + 1:02d}-{typ}")
        if only and slug not in only and typ not in only:
            continue
        ctx = Ctx(
            agent=str(manifest.get("agent") or "Fleet"),
            domain=str(manifest.get("domain") or ""),
            date=manifest.get("date"),
            footer=manifest.get("footer"),
            index=i,
            total=len(cards),
            series=bool(series),
        )
        fn = REGISTRY.get(typ)
        if fn is None:
            ctx.warnings.append(f"unknown type {typ!r}; rendered as brief")
            fn = REGISTRY["brief"]
        card = _resolve_images(card, base_dir)
        c = Card(ctx, card, scale)
        fn(c)
        img = c.finish()
        path = outdir / f"{slug}.png"
        img.save(path, "PNG", optimize=True)
        results.append(Result(path, typ, slug, lint(card) + ctx.warnings))
    return results


def types() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in sorted(REGISTRY)}
    for a, t in ALIASES.items():
        out.setdefault(t, []).append(a)
    return out
