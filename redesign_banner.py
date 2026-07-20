"""Redesign harsha-banner SVGs: smaller portrait, less clutter."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Portrait placement (was 690,130 540x522)
IMG_X, IMG_Y, IMG_W, IMG_H = 920, 96, 280, 360
GLOW_CX, GLOW_CY, GLOW_R = IMG_X + IMG_W // 2, IMG_Y + IMG_H // 2, 190

IMPACT_Y = 400
IMPACT_H = 88
CARD_W = 198
CARD_GAP = 14
CARD_X0 = 48

IMPACT_STATS = [
    ("160+", "Servers", "#38bdf8", "🚀"),
    ("4,000+", "Workflows", "#a78bfa", "⚡"),
    ("IEEE", "Codeathon", "#fbbf24", "🏆"),
    ("Author", "AI / IoT", "#34d399", "📚"),
]


def impact_cards_svg() -> str:
    lines = [
        f'<!-- Compact impact row -->',
        f'<g class="st" style="animation:fadeIn .5s ease 5.2s forwards">',
    ]
    for i, (value, label, color, icon) in enumerate(IMPACT_STATS):
        x = CARD_X0 + i * (CARD_W + CARD_GAP)
        lines.append(
            f'  <rect x="{x}" y="{IMPACT_Y}" width="{CARD_W}" height="{IMPACT_H}" rx="12" '
            f'fill="#111827" fill-opacity="0.55" stroke="url(#borderg)" stroke-width="1"/>'
        )
        lines.append(
            f'  <text x="{x + 16}" y="{IMPACT_Y + 34}" font-size="11" fill="#64748b">{icon} '
            f'<tspan fill="{color}" font-weight="bold" font-size="20">{value}</tspan></text>'
        )
        lines.append(
            f'  <text x="{x + 16}" y="{IMPACT_Y + 62}" font-size="12" fill="#94a3b8">{label}</text>'
        )
    lines.append("</g>")
    return "\n".join(lines)


def tech_pills_svg() -> str:
    pills = [
        (48, 326, 76, "Python", "rgba(227,79,38,.13)", "#e34f26", "#ff8a65"),
        (132, 326, 80, "PyTorch", "rgba(38,119,189,.15)", "#38bdf8", "#7dd3fc"),
        (220, 326, 86, "AI &amp; ML", "rgba(247,223,30,.10)", "#f7df1e", "#fde047"),
        (314, 326, 80, "React", "rgba(97,218,251,.10)", "#61dafb", "#67e8f9"),
        (402, 326, 102, "TypeScript", "rgba(0,118,206,.14)", "#4a9eda", "#93c5fd"),
        (512, 326, 84, "Node.js", "rgba(139,92,246,.14)", "#6366f1", "#c4b5fd"),
    ]
    lines = [
        '<text class="ii" x="48" y="318" font-size="14" fill="#818cf8" font-weight="bold" '
        'style="animation:fadeIn .4s ease 4.4s forwards">Tech stack</text>',
    ]
    delay = 4.6
    for x, y, w, label, fill, stroke, text_fill in pills:
        cx = x + w // 2
        lines.append(
            f'<g class="pill" style="animation:fadeIn .3s ease {delay:.1f}s forwards">'
            f'<rect x="{x}" y="{y}" width="{w}" height="24" rx="12" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="1"/>'
            f'<text x="{cx}" y="{y + 16}" text-anchor="middle" font-size="11" fill="{text_fill}" '
            f'font-weight="bold">{label}</text></g>'
        )
        delay += 0.1
    return "\n".join(lines)


def patch_svg(content: str, *, light: bool) -> str:
    quote_fill = "#1e293b" if not light else "#f1f5f9"
    quote_stroke = "#334155" if not light else "#cbd5e1"
    quote_text = "#e6edf3" if not light else "#1e293b"
    role_fill = "#2dd4bf" if not light else "#0d9488"
    hi_fill = "#e6edf3" if not light else "#0f172a"
    prompt_green = "#4ade80" if not light else "#16a34a"
    prompt_gray = "#8b949e" if not light else "#64748b"

    # Update hero clip paths
    content = re.sub(
        r'<clipPath id="heroReveal"><rect x="\d+" y="\d+" width="\d+" height="0" rx="16">\s*'
        r'<animate attributeName="height" from="0" to="\d+" dur="1.8s begin="\.5s" fill="freeze"/>',
        f'<clipPath id="heroReveal"><rect x="{IMG_X}" y="{IMG_Y}" width="{IMG_W}" height="0" rx="16">\n'
        f'  <animate attributeName="height" from="0" to="{IMG_H}" dur="1.8s" begin=".5s" fill="freeze"/>',
        content,
    )
    content = re.sub(
        r'<clipPath id="heroBox"><rect x="\d+" y="\d+" width="\d+" height="\d+" rx="16"/></clipPath>',
        f'<clipPath id="heroBox"><rect x="{IMG_X}" y="{IMG_Y}" width="{IMG_W}" height="{IMG_H}" rx="16"/></clipPath>',
        content,
    )

    # Extract base64 image href
    img_match = re.search(
        r'(<image x="\d+" y="\d+" width="\d+" height="\d+" preserveAspectRatio="[^"]+" href=")(data:image[^"]+)(")',
        content,
    )
    if not img_match:
        raise RuntimeError("Could not find embedded image")
    img_tag = (
        f'<image x="{IMG_X}" y="{IMG_Y}" width="{IMG_W}" height="{IMG_H}" '
        f'preserveAspectRatio="xMidYMid slice" href="{img_match.group(2)}"/>'
    )

    # Remove old right-side clutter: code card, neon sign, extra sparkle after neon
    content = re.sub(
        r"\n<!-- buildDreams\(\) code card -->.*?(?=\n<!-- ================= FOOTER)",
        "",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"\n<!-- Neon sign -->.*?(?=\n<!-- ================= FOOTER|\n<g class=\"tw\" style=\"animation-delay:1\.4s\")",
        "",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r'\n<g class="tw" style="animation-delay:1\.4s"><path d="M1236 320[^<]+</g>',
        "",
        content,
    )

    # Replace hero illustration block
    hero_block = f"""<!-- ================= RIGHT: PORTRAIT ================= -->
<circle cx="{GLOW_CX}" cy="{GLOW_CY}" r="{GLOW_R}" fill="url(#heroGlow)"><animate attributeName="r" values="{GLOW_R};{GLOW_R + 18};{GLOW_R}" dur="5s" repeatCount="indefinite"/></circle>
<g class="fl">
  <g clip-path="url(#heroReveal)">{img_tag}</g>
  <g clip-path="url(#heroBox)">
    <rect x="{IMG_X}" y="{IMG_Y}" width="{IMG_W}" height="{IMG_H}" rx="16" fill="none" stroke="url(#borderg)" stroke-width="1.5"/>
  </g>
</g>"""

    content = re.sub(
        r"<!-- ================= RIGHT: ILLUSTRATION ================= -->.*?(?=\n<!-- ================= FOOTER|\n<!-- buildDreams|\n<!-- Neon sign -->|\n<g class=\"tw\" style=\"animation-delay:1\.4s\")",
        hero_block,
        content,
        flags=re.DOTALL,
    )

    # Replace metrics card with compact row
    content = re.sub(
        r"<!-- Metrics card -->.*?</g>\s*\n\s*\n<!-- ================= RIGHT",
        impact_cards_svg() + "\n\n<!-- ================= RIGHT",
        content,
        flags=re.DOTALL,
    )

    # Replace tech section
    content = re.sub(
        r"<!-- Tech I Know -->.*?(?=<!-- Metrics card -->|<!-- Compact impact row -->)",
        tech_pills_svg() + "\n\n",
        content,
        flags=re.DOTALL,
    )

    # Slimmer quote box + updated quote clip paths
    content = re.sub(
        r'<clipPath id="q1"><rect x="76" y="250" width="0" height="46">',
        '<clipPath id="q1"><rect x="76" y="248" width="0" height="28">',
        content,
    )
    content = re.sub(
        r'<clipPath id="q2"><rect x="76" y="276" width="0" height="46">',
        '<clipPath id="q2"><rect x="76" y="272" width="0" height="28">',
        content,
    )
    content = re.sub(
        r"<g class=\"cl\" style=\"animation:fadeIn \.5s ease 3\.2s forwards\">\s*"
        r"<rect x=\"48\" y=\"255\" width=\"460\" height=\"68\"[^/]*/>\s*"
        r"<rect x=\"48\" y=\"259\" width=\"3\.5\" height=\"60\"[^/]*/>\s*</g>",
        f'<g class="cl" style="animation:fadeIn .5s ease 3.2s forwards">'
        f'<rect x="48" y="248" width="560" height="52" rx="8" fill="{quote_fill}" fill-opacity="0.45" '
        f'stroke="{quote_stroke}" stroke-width="1"/>'
        f'<rect x="48" y="252" width="3" height="44" rx="1.5" fill="#38bdf8"/></g>',
        content,
    )
    content = re.sub(
        r'<text clip-path="url\(#q1\)" x="76" y="283" font-size="15" fill="#e6edf3">',
        f'<text clip-path="url(#q1)" x="76" y="268" font-size="14" fill="{quote_text}">',
        content,
    )
    content = re.sub(
        r'<text clip-path="url\(#q2\)" x="76" y="307" font-size="15">',
        f'<text clip-path="url(#q2)" x="76" y="288" font-size="14">',
        content,
    )
    content = re.sub(
        r'<g class="tw" style="animation-delay:\.9s"><path d="M480 279[^<]+</g>\s*',
        "",
        content,
    )

    # Remove name-adjacent sparkle (crowded)
    content = re.sub(
        r'<g class="tw" style="animation-delay:3s"><path d="M650 168[^<]+</g>\s*',
        "",
        content,
    )

    # Smaller name
    content = re.sub(
        r"(<text x=\"0\" y=\"0\" font-family=\"system-ui[^\"]+\" font-size=\")46",
        r"\g<1>40",
        content,
    )
    content = re.sub(
        r'transform="translate\(48,180\)"',
        'transform="translate(48,172)"',
        content,
    )

    # Reduce decorative particles
    content = re.sub(
        r"<!-- rising particles -->\s*"
        r"(<circle class=\"rp\"[^/]*/>\s*){6}",
        """<!-- rising particles -->
<circle class="rp" cx="140" cy="620" r="1.2" fill="#38bdf8" style="animation-duration:5.5s"/>
<circle class="rp" cx="820" cy="640" r="1" fill="#818cf8" style="animation-duration:6.2s;animation-delay:1.2s"/>
<circle class="rp" cx="1180" cy="560" r="1.1" fill="#2dd4bf" style="animation-duration:5s;animation-delay:.8s"/>
""",
        content,
        flags=re.DOTALL,
    )

    # Fewer sparkles
    content = re.sub(
        r"<!-- sparkles -->\s*"
        r'(<g class="tw"[^<]+</g>\s*){3}',
        """<!-- sparkles -->
<g class="tw" style="animation-delay:.6s"><path d="M470 120l3 8 8 3-8 3-3 8-3-8-8-3 8-3z" fill="#67e8f9"/></g>
<g class="tw" style="animation-delay:2s"><path d="M860 88l2.4 6.4 6.4 2.4-6.4 2.4-2.4 6.4-2.4-6.4-6.4-2.4 6.4-2.4z" fill="#38bdf8"/></g>
""",
        content,
        flags=re.DOTALL,
    )

    # Footer: move collaborate status left, shorten quote area
    content = re.sub(
        r'<text class="soc" x="700" y="707"',
        '<text class="soc" x="620" y="707"',
        content,
    )

    return content


def main() -> None:
    for name, light in [("harsha-banner.svg", False), ("harsha-banner-light.svg", True)]:
        path = ROOT / name
        original = path.read_text(encoding="utf-8")
        updated = patch_svg(original, light=light)
        path.write_text(updated, encoding="utf-8")
        print(f"Updated {name} ({len(original)} -> {len(updated)} chars)")


if __name__ == "__main__":
    main()
