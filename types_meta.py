"""MBTI-style type metadata for UI (roles, colors, nicknames, blurbs)."""

from __future__ import annotations

# Role colors inspired by common personality-test palettes (original copy).
ROLES = {
    "analysts": {
        "label": "Analysts",
        "color": "#88619A",
        "soft": "#F3EAF8",
        "ink": "#4A2F5C",
    },
    "diplomats": {
        "label": "Diplomats",
        "color": "#33A474",
        "soft": "#E7F6EF",
        "ink": "#1B5C40",
    },
    "sentinels": {
        "label": "Sentinels",
        "color": "#4298B5",
        "soft": "#E6F4F8",
        "ink": "#1D5366",
    },
    "explorers": {
        "label": "Explorers",
        "color": "#E4AE3A",
        "soft": "#FBF3DE",
        "ink": "#6B4E12",
    },
}

TYPE_INFO = {
    "INTJ": {
        "role": "analysts",
        "nickname": "Architect",
        "blurb": "Imaginative planners who map the future before they act.",
    },
    "INTP": {
        "role": "analysts",
        "nickname": "Logician",
        "blurb": "Curious minds chasing patterns, theories, and better ideas.",
    },
    "ENTJ": {
        "role": "analysts",
        "nickname": "Commander",
        "blurb": "Bold organizers who turn ambition into clear plans.",
    },
    "ENTP": {
        "role": "analysts",
        "nickname": "Debater",
        "blurb": "Quick thinkers who love challenges and sharp conversation.",
    },
    "INFJ": {
        "role": "diplomats",
        "nickname": "Advocate",
        "blurb": "Quiet idealists who care deeply about meaning and people.",
    },
    "INFP": {
        "role": "diplomats",
        "nickname": "Mediator",
        "blurb": "Warm, creative spirits drawn to causes and kindness.",
    },
    "ENFJ": {
        "role": "diplomats",
        "nickname": "Protagonist",
        "blurb": "Charismatic helpers who bring out the best in others.",
    },
    "ENFP": {
        "role": "diplomats",
        "nickname": "Campaigner",
        "blurb": "Enthusiastic free spirits who find joy in new possibilities.",
    },
    "ISTJ": {
        "role": "sentinels",
        "nickname": "Logistician",
        "blurb": "Reliable realists who keep promises and finish the work.",
    },
    "ISFJ": {
        "role": "sentinels",
        "nickname": "Defender",
        "blurb": "Loyal caretakers who notice needs and defend what matters.",
    },
    "ESTJ": {
        "role": "sentinels",
        "nickname": "Executive",
        "blurb": "Practical leaders who bring order, standards, and results.",
    },
    "ESFJ": {
        "role": "sentinels",
        "nickname": "Consul",
        "blurb": "Warm connectors who make groups feel welcome and cared for.",
    },
    "ISTP": {
        "role": "explorers",
        "nickname": "Virtuoso",
        "blurb": "Hands-on problem solvers who learn by building and testing.",
    },
    "ISFP": {
        "role": "explorers",
        "nickname": "Adventurer",
        "blurb": "Gentle explorers who follow beauty, feeling, and the moment.",
    },
    "ESTP": {
        "role": "explorers",
        "nickname": "Entrepreneur",
        "blurb": "Energetic realists who thrive on action and quick decisions.",
    },
    "ESFP": {
        "role": "explorers",
        "nickname": "Entertainer",
        "blurb": "Lively entertainers who turn ordinary days into shared fun.",
    },
}


def type_payload(code: str | None) -> dict | None:
    if not code:
        return None
    code = str(code).upper().strip()
    info = TYPE_INFO.get(code)
    if not info:
        return None
    role = ROLES[info["role"]]
    return {
        "code": code,
        "nickname": info["nickname"],
        "blurb": info["blurb"],
        "role": info["role"],
        "role_label": role["label"],
        "color": role["color"],
        "soft": role["soft"],
        "ink": role["ink"],
        "avatar": f"chars/{code}.png",
    }


def types_by_role() -> list[dict]:
    order = ["analysts", "diplomats", "sentinels", "explorers"]
    out = []
    for role_key in order:
        role = ROLES[role_key]
        types = [
            type_payload(code)
            for code, info in TYPE_INFO.items()
            if info["role"] == role_key
        ]
        out.append(
            {
                "key": role_key,
                "label": role["label"],
                "color": role["color"],
                "soft": role["soft"],
                "types": types,
            }
        )
    return out
