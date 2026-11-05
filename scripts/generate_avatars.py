"""Generate original SVG character avatars for each personality type."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "static" / "avatars"

COLORS = {
    "analysts": "#88619A",
    "diplomats": "#33A474",
    "sentinels": "#4298B5",
    "explorers": "#C4921A",
}

TYPES = {
    "INTJ": ("analysts", "board"),
    "INTP": ("analysts", "book"),
    "ENTJ": ("analysts", "flag"),
    "ENTP": ("analysts", "bolt"),
    "INFJ": ("diplomats", "lantern"),
    "INFP": ("diplomats", "flower"),
    "ENFJ": ("diplomats", "heart"),
    "ENFP": ("diplomats", "star"),
    "ISTJ": ("sentinels", "clipboard"),
    "ISFJ": ("sentinels", "shield"),
    "ESTJ": ("sentinels", "checklist"),
    "ESFJ": ("sentinels", "gift"),
    "ISTP": ("explorers", "wrench"),
    "ISFP": ("explorers", "brush"),
    "ESTP": ("explorers", "goggles"),
    "ESFP": ("explorers", "mic"),
}


def prop(kind: str, accent: str) -> str:
    props = {
        "board": f'<rect x="148" y="118" width="36" height="48" rx="4" fill="#fff" stroke="{accent}" stroke-width="3"/><path d="M156 132h20M156 142h16M156 152h18" stroke="{accent}" stroke-width="2"/>',
        "book": f'<rect x="150" y="128" width="34" height="42" rx="3" fill="#fff" stroke="{accent}" stroke-width="3"/><path d="M167 128v42" stroke="{accent}" stroke-width="2"/>',
        "flag": f'<path d="M162 110v70" stroke="{accent}" stroke-width="4"/><path d="M164 112h28l-6 10 6 10H164z" fill="{accent}"/>',
        "bolt": f'<path d="M170 112l-14 28h12l-8 30 26-36h-12l10-22z" fill="{accent}"/>',
        "lantern": f'<rect x="156" y="124" width="28" height="36" rx="6" fill="#fff8c8" stroke="{accent}" stroke-width="3"/><path d="M170 116v8M156 132h28" stroke="{accent}" stroke-width="2"/>',
        "flower": f'<circle cx="170" cy="132" r="8" fill="{accent}"/><circle cx="158" cy="140" r="7" fill="{accent}" opacity=".85"/><circle cx="182" cy="140" r="7" fill="{accent}" opacity=".85"/><circle cx="164" cy="152" r="7" fill="{accent}" opacity=".85"/><circle cx="176" cy="152" r="7" fill="{accent}" opacity=".85"/><circle cx="170" cy="142" r="5" fill="#fff"/>',
        "heart": f'<path d="M170 168c-18-14-28-24-28-36 0-10 8-16 16-16 6 0 10 3 12 7 2-4 6-7 12-7 8 0 16 6 16 16 0 12-10 22-28 36z" fill="{accent}"/>',
        "star": f'<path d="M170 118l8 16 18 2-13 13 4 18-17-10-17 10 4-18-13-13 18-2z" fill="{accent}"/>',
        "clipboard": f'<rect x="150" y="118" width="40" height="52" rx="4" fill="#fff" stroke="{accent}" stroke-width="3"/><rect x="160" y="112" width="20" height="10" rx="2" fill="{accent}"/><path d="M158 136h24M158 148h20M158 160h22" stroke="{accent}" stroke-width="2"/>',
        "shield": f'<path d="M170 112l28 10v22c0 18-12 32-28 40-16-8-28-22-28-40v-22z" fill="{accent}"/><path d="M170 128v34" stroke="#fff" stroke-width="3"/>',
        "checklist": f'<rect x="148" y="120" width="44" height="54" rx="4" fill="#fff" stroke="{accent}" stroke-width="3"/><path d="M156 136l6 6 12-14M156 154l6 6 12-14" stroke="{accent}" stroke-width="3" fill="none"/>',
        "gift": f'<rect x="150" y="138" width="40" height="34" rx="3" fill="{accent}"/><rect x="166" y="138" width="8" height="34" fill="#fff" opacity=".5"/><rect x="150" y="148" width="40" height="8" fill="#fff" opacity=".5"/><path d="M170 138c-8-12-20-8-20 0 12-4 16 0 20 8 4-8 8-12 20-8 0-8-12-12-20 0z" fill="{accent}"/>',
        "wrench": f'<path d="M150 150l28-28 8 8-10 10 14 14-10 10-14-14-10 10z" fill="{accent}"/><circle cx="186" cy="114" r="10" fill="none" stroke="{accent}" stroke-width="4"/>',
        "brush": f'<path d="M176 110c10 0 16 8 12 16l-28 48-14-8 28-48c2-4 0-8 2-8z" fill="{accent}"/><rect x="142" y="168" width="22" height="10" rx="2" fill="#5b4636"/>',
        "goggles": f'<circle cx="108" cy="96" r="14" fill="none" stroke="{accent}" stroke-width="5"/><circle cx="140" cy="96" r="14" fill="none" stroke="{accent}" stroke-width="5"/><path d="M122 96h12" stroke="{accent}" stroke-width="4"/>',
        "mic": f'<rect x="162" y="120" width="16" height="28" rx="8" fill="{accent}"/><path d="M156 148c0 10 6 16 14 16s14-6 14-16" fill="none" stroke="{accent}" stroke-width="3"/><path d="M170 164v16" stroke="{accent}" stroke-width="3"/>',
    }
    return props.get(kind, "")


def svg_for(code: str, role: str, kind: str) -> str:
    accent = COLORS[role]
    soft = {
        "analysts": "#F3EAF8",
        "diplomats": "#E7F6EF",
        "sentinels": "#E6F4F8",
        "explorers": "#FBF3DE",
    }[role]
    # Keep soft fills in sync with types_meta.ROLES
    # Slight pose variation by code hash
    lean = {"I": -4, "E": 4}[code[0]]
    hair = {
        "NT": f'<path d="M86 78c8-28 52-28 60 0" fill="{accent}"/>',
        "NF": f'<path d="M84 84c6-30 58-30 64 0M78 96c4-8 12-10 18-6M152 90c6-6 14-4 18 4" fill="{accent}"/>',
        "SJ": f'<path d="M90 86c10-24 48-24 58 0" fill="{accent}"/>',
        "SP": f'<path d="M88 80c12-26 50-24 60 2M150 78l10-14 6 12" fill="{accent}"/>',
    }
    group = code[1] + ("T" if code[2] == "T" else "F") if False else None
    # Map to hair style by second+third letters category
    if code[1] == "N" and code[2] == "T":
        hair_svg = hair["NT"]
    elif code[1] == "N":
        hair_svg = hair["NF"]
    elif code[3] == "J":
        hair_svg = hair["SJ"]
    else:
        hair_svg = hair["SP"]

    shirt = accent
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" role="img" aria-label="{code} character">
  <rect width="240" height="240" rx="28" fill="{soft}"/>
  <g transform="translate({lean},0)">
    <!-- body -->
    <path d="M78 210c8-46 30-70 42-70s34 24 42 70" fill="{shirt}"/>
    <circle cx="120" cy="100" r="36" fill="#F7D7C4"/>
    {hair_svg}
    <!-- face -->
    <circle cx="108" cy="98" r="3.5" fill="#4a3428"/>
    <circle cx="132" cy="98" r="3.5" fill="#4a3428"/>
    <path d="M112 114c6 8 16 8 22 0" fill="none" stroke="#4a3428" stroke-width="3" stroke-linecap="round"/>
    {prop(kind, accent)}
  </g>
  <text x="20" y="36" font-family="Segoe UI, Arial, sans-serif" font-size="18" font-weight="700" fill="{accent}">{code}</text>
</svg>
'''


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for code, (role, kind) in TYPES.items():
        path = OUT / f"{code}.svg"
        path.write_text(svg_for(code, role, kind), encoding="utf-8")
        print("wrote", path.name)
    print("done", OUT)


if __name__ == "__main__":
    main()
