"""Load and query personalities.json (single source of truth for type pages)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from types_meta import ROLES, type_payload

DATA_PATH = Path(__file__).resolve().parent / "data" / "personalities.json"

GROUP_ROLE_KEY = {
    "Analysts": "analysts",
    "Diplomats": "diplomats",
    "Sentinels": "sentinels",
    "Explorers": "explorers",
}


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    with DATA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def studies_by_id(catalog: dict | None = None) -> dict[str, dict]:
    catalog = catalog or load_catalog()
    return {s["id"]: s for s in catalog.get("studies", [])}


def types_list(catalog: dict | None = None) -> list[dict]:
    catalog = catalog or load_catalog()
    return list(catalog.get("types", []))


def type_by_slug(slug: str) -> dict | None:
    slug = (slug or "").strip().lower()
    for t in types_list():
        if t.get("slug") == slug:
            return t
    return None


def group_blocks(catalog: dict | None = None) -> list[dict]:
    """Groups with full type objects + UI colors for the grid."""
    catalog = catalog or load_catalog()
    by_code = {t["code"]: t for t in catalog.get("types", [])}
    blocks = []
    for g in catalog.get("groups", []):
        role_key = GROUP_ROLE_KEY.get(g["name"], "analysts")
        role = ROLES[role_key]
        types = []
        for code in g.get("types", []):
            t = by_code.get(code)
            if not t:
                continue
            meta = type_payload(code) or {}
            types.append(
                {
                    **t,
                    "avatar": meta.get("avatar", f"chars/{code}.png"),
                    "color": role["color"],
                    "soft": role["soft"],
                    "ink": role["ink"],
                }
            )
        blocks.append(
            {
                "name": g["name"],
                "key": role_key,
                "color": role["color"],
                "soft": role["soft"],
                "types": types,
            }
        )
    return blocks


def enrich_type_page(slug: str) -> dict | None:
    """Bundle one type with studies, neighbors, and role colors for the detail template."""
    catalog = load_catalog()
    types = types_list(catalog)
    index = next((i for i, t in enumerate(types) if t.get("slug") == slug.lower()), None)
    if index is None:
        return None
    t = types[index]
    study_map = studies_by_id(catalog)
    studies = [study_map[sid] for sid in t.get("study_ids", []) if sid in study_map]
    meta = type_payload(t["code"]) or {}
    role_key = GROUP_ROLE_KEY.get(t.get("group", ""), meta.get("role", "analysts"))
    role = ROLES.get(role_key, ROLES["analysts"])
    prev_t = types[index - 1] if index > 0 else None
    next_t = types[index + 1] if index < len(types) - 1 else None
    return {
        "type": t,
        "studies": studies,
        "meta_note": catalog.get("meta", {}).get("note", ""),
        "color": role["color"],
        "soft": role["soft"],
        "ink": role["ink"],
        "avatar": meta.get("avatar", f"chars/{t['code']}.png"),
        "prev": prev_t,
        "next": next_t,
    }
