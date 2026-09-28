"""warm_dark CLI: JSON manifest → Warm Dark PNG cards."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .render import render_manifest, types, validate


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="warm_dark.py",
        description="Render Warm Dark cards from a JSON manifest. "
                    "Prints one PNG path per line; QA warnings go to stderr.",
        epilog="Examples:\n"
               "  warm_dark.py cards.json\n"
               "  warm_dark.py cards.json --outdir /tmp/cards --scale 2\n"
               "  cat cards.json | warm_dark.py - --outdir /tmp/cards\n"
               "  warm_dark.py cards.json --validate\n"
               "  warm_dark.py --types",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("manifest", nargs="?", help="Path to cards.json, or - for stdin")
    ap.add_argument("--outdir", type=Path, help="Override manifest outdir")
    ap.add_argument("--scale", type=float, help="Output scale (1 = 810x1146, 2 = retina)")
    ap.add_argument("--only", action="append", help="Render only this slug or type (repeatable)")
    ap.add_argument("--validate", action="store_true", help="Validate manifest and exit")
    ap.add_argument("--strict", action="store_true", help="Exit 2 if any card has QA warnings")
    ap.add_argument("--json", action="store_true", help="Print a JSON report instead of paths")
    ap.add_argument("--types", action="store_true", help="List card types and aliases")
    a = ap.parse_args(argv)

    if a.types:
        for t, al in types().items():
            print(t + (f"  (aliases: {', '.join(sorted(al))})" if al else ""))
        return 0
    if not a.manifest:
        ap.error("manifest path required (or --types)")

    if a.manifest != "-" and not Path(a.manifest).is_file():
        print(f"error: manifest not found: {a.manifest}", file=sys.stderr)
        return 1
    raw = sys.stdin.read() if a.manifest == "-" else Path(a.manifest).read_text()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"error: manifest is not valid JSON: {e}", file=sys.stderr)
        return 1

    errs = validate(data)
    if a.validate:
        for e in errs:
            print(f"invalid: {e}", file=sys.stderr)
        print("ok" if not errs else f"{len(errs)} problem(s)")
        return 1 if errs else 0
    for e in errs:
        print(f"warn: schema: {e}", file=sys.stderr)

    base = Path(a.manifest).parent if a.manifest != "-" else Path.cwd()
    outdir = a.outdir or Path(data.get("outdir") or "out")
    if not outdir.is_absolute() and not a.outdir:
        outdir = base / outdir
    results = render_manifest(data, outdir, a.scale, set(a.only) if a.only else None, base_dir=base)
    warned = False
    for r in results:
        for w in r.warnings:
            warned = True
            print(f"warn: {r.slug}: {w}", file=sys.stderr)
    if a.json:
        print(json.dumps([{"path": str(r.path), "type": r.type, "slug": r.slug, "warnings": r.warnings}
                          for r in results], indent=2))
    else:
        for r in results:
            print(r.path)
    return 2 if (a.strict and warned) else 0
