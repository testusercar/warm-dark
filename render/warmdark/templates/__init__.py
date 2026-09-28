"""Template registry. Each template takes a Card and stacks body items."""
from __future__ import annotations

from typing import Callable

from ..layout import Card

REGISTRY: dict[str, Callable[[Card], None]] = {}
ALIASES: dict[str, str] = {}


def template(name: str, *aliases: str):
    def deco(fn: Callable[[Card], None]) -> Callable[[Card], None]:
        REGISTRY[name] = fn
        for a in aliases:
            ALIASES[a] = name
        return fn

    return deco


def resolve(name: str) -> str:
    name = (name or "brief").lower().strip()
    return ALIASES.get(name, name)


from . import charts_t, lists, metrics, networth, status  # noqa: E402,F401
