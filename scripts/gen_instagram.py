"""
Infografía para Instagram — dotai
Formato: 1080 × 1350 px (4:5 — óptimo para feed de Instagram)
"""

W, H = 1080, 1350
FONT = "Ubuntu Nerd Font"

# Paleta
BG        = "#0D1117"
SURFACE   = "#161B22"
SURFACE2  = "#1C2128"
BORDER    = "#30363D"
TEXT      = "#E6EDF3"
TEXT2     = "#8B949E"
TEXT3     = "#6E7681"

C_AGENTS   = "#6366F1"
C_COMMANDS = "#10B981"
C_HOOKS    = "#F59E0B"
C_RULES    = "#06B6D4"
C_SKILLS   = "#EC4899"
C_CONFIG   = "#8B5CF6"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def rect(x, y, w, h, fill, rx=0, stroke=None, sw=1.5, opacity=1):
    s = stroke or "none"
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{s}" stroke-width="{sw}" opacity="{opacity}"/>')

def text_el(x, y, content, size=28, fill=TEXT, weight="normal", anchor="middle", family=FONT):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'
            f'{esc(content)}</text>')

def pill_badge(cx, y, label, color):
    w = len(label) * 13 + 32
    x = cx - w // 2
    out  = rect(x, y - 20, w, 32, color, rx=16, opacity=0.18)
    out += rect(x, y - 20, w, 32, color, rx=16, stroke=color, sw=1.5, opacity=0.7)
    out += text_el(cx, y + 1, label, size=17, fill=color, weight="bold")
    return out

def component_card(x, y, w, h, color, icon, title, items):
    out = ""
    # Shadow
    out += rect(x + 4, y + 4, w, h, "#000", rx=20, opacity=0.5)
    # Card
    out += rect(x, y, w, h, SURFACE, rx=20, stroke=color, sw=2)
    # Top accent
    out += rect(x, y, w, 6, color, rx=3)

    # Icon circle
    r = 30
    out += f'<circle cx="{x + w//2}" cy="{y + 52}" r="{r}" fill="{color}" opacity="0.15"/>'
    out += f'<circle cx="{x + w//2}" cy="{y + 52}" r="{r}" fill="none" stroke="{color}" stroke-width="2"/>'
    out += text_el(x + w//2, y + 60, icon, size=26, fill=color, weight="bold")

    # Title
    out += text_el(x + w//2, y + 104, title, size=20, fill=TEXT, weight="bold")

    # Items
    for i, item in enumerate(items):
        iy = y + 132 + i * 34
        out += f'<circle cx="{x + 22}" cy="{iy - 5}" r="4" fill="{color}" opacity="0.8"/>'
        out += text_el(x + 34, iy, item, size=16, fill=TEXT2, anchor="start")

    return out


# ── SVG ──────────────────────────────────────────────────────────────────────
lines = []
lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')

lines.append(f'''<defs>
  <linearGradient id="bgGrad" x1="0" y1="0" x2="0.5" y2="1">
    <stop offset="0%"   stop-color="#0F0C29"/>
    <stop offset="50%"  stop-color="#0D1117"/>
    <stop offset="100%" stop-color="#0a0f1a"/>
  </linearGradient>
  <linearGradient id="titleGrad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%"   stop-color="#8B5CF6"/>
    <stop offset="50%"  stop-color="#6366F1"/>
    <stop offset="100%" stop-color="#06B6D4"/>
  </linearGradient>
  <linearGradient id="divGrad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%"   stop-color="#8B5CF6" stop-opacity="0"/>
    <stop offset="30%"  stop-color="#8B5CF6"/>
    <stop offset="70%"  stop-color="#06B6D4"/>
    <stop offset="100%" stop-color="#06B6D4" stop-opacity="0"/>
  </linearGradient>
  <filter id="glow">
    <feGaussianBlur stdDeviation="8" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>''')

# Background
lines.append(f'<rect width="{W}" height="{H}" fill="url(#bgGrad)"/>')

# Subtle grid pattern
for gx in range(0, W, 60):
    lines.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{H}" stroke="#ffffff" stroke-width="0.3" opacity="0.03"/>')
for gy in range(0, H, 60):
    lines.append(f'<line x1="0" y1="{gy}" x2="{W}" y2="{gy}" stroke="#ffffff" stroke-width="0.3" opacity="0.03"/>')

# Top glow blob
lines.append(f'<ellipse cx="{W//2}" cy="100" rx="320" ry="120" fill="#6366F1" opacity="0.06"/>')

# ── HEADER ────────────────────────────────────────────────────────────────────

# Eyebrow
lines.append(text_el(W//2, 72, "Claude Code · Dotfiles", size=20, fill=TEXT3, weight="normal"))

# Main title with gradient fill
lines.append(f'''<text x="{W//2}" y="148" font-family="{FONT}" font-size="96" font-weight="bold"
  text-anchor="middle" fill="url(#titleGrad)" filter="url(#glow)">dotai</text>''')

# Tagline
lines.append(text_el(W//2, 194,
    "Configura Claude Code como un Senior Engineer",
    size=24, fill=TEXT2))

# Divider
lines.append(f'<rect x="140" y="216" width="800" height="2" fill="url(#divGrad)" rx="1"/>')

# Stack badges row
BADGES = [
    ("Java 21", C_AGENTS),
    ("Spring Boot 3", C_CONFIG),
    ("Hexagonal", C_RULES),
    ("Maven", C_COMMANDS),
]
total_w = sum(len(l) * 13 + 32 + 16 for l, _ in BADGES) - 16
bx = W // 2 - total_w // 2
for label, color in BADGES:
    bw = len(label) * 13 + 32
    bcx = bx + bw // 2
    lines.append(pill_badge(bcx, 258, label, color))
    bx += bw + 16

# ── COMPONENT CARDS GRID ──────────────────────────────────────────────────────
# 2 × 3 grid (but 5 cards + 1 highlight)

CARD_W = 300
CARD_H = 242
GAP    = 24
START_X = (W - (CARD_W * 3 + GAP * 2)) // 2
START_Y = 298

cards = [
    (C_AGENTS,   "", "Agents",   ["8 subagentes expertos", "core-reviewer · debugger", "security-auditor · explorer"]),
    (C_COMMANDS, "", "Commands", ["/fix-issue — corrige issues", "/pr-review — revisa PRs", "/deploy — despliega la app"]),
    (C_HOOKS,    "", "Hooks",    ["PreToolUse · PostToolUse", "SessionSmart — memoria", "pre-commit — valida antes"]),
    (C_RULES,    "", "Rules",    ["architecture · api", "database · frontend", "Reglas por dominio técnico"]),
    (C_SKILLS,   "", "Skills",   ["/backend — feature completa", "/frontend — contrato API", "context · SKILL template"]),
]

for i, (color, icon, title, items) in enumerate(cards):
    col = i % 3
    row = i // 3
    cx = START_X + col * (CARD_W + GAP)
    cy = START_Y + row * (CARD_H + GAP)
    lines.append(component_card(cx, cy, CARD_W, CARD_H, color, icon, title, items))

# ── SETTINGS CARD — full width ────────────────────────────────────────────────
SY = START_Y + 2 * (CARD_H + GAP) + 8
SW_FULL = CARD_W * 3 + GAP * 2
SH = 116

lines.append(rect(START_X + 4, SY + 4, SW_FULL, SH, "#000", rx=20, opacity=0.5))
lines.append(rect(START_X, SY, SW_FULL, SH, SURFACE, rx=20, stroke=C_CONFIG, sw=2))
lines.append(rect(START_X, SY, SW_FULL, 6, C_CONFIG, rx=3))

lines.append(f'<circle cx="{START_X + 56}" cy="{SY + 58}" r="28" fill="{C_CONFIG}" opacity="0.15"/>')
lines.append(f'<circle cx="{START_X + 56}" cy="{SY + 58}" r="28" fill="none" stroke="{C_CONFIG}" stroke-width="2"/>')
lines.append(text_el(START_X + 56, SY + 66, "", size=24, fill=C_CONFIG, weight="bold"))
lines.append(text_el(START_X + 100, SY + 45, "settings.json + CLAUDE.md", size=22, fill=TEXT, weight="bold", anchor="start"))
lines.append(text_el(START_X + 100, SY + 76,
    "Permisos · Hooks · Variables de entorno · Instrucciones globales",
    size=17, fill=TEXT2, anchor="start"))

# ── HOW IT WORKS — 3 steps ────────────────────────────────────────────────────
HY = SY + SH + 40

lines.append(text_el(W//2, HY, "¿Cómo funciona?", size=26, fill=TEXT, weight="bold"))
lines.append(f'<rect x="140" y="{HY + 14}" width="800" height="1.5" fill="url(#divGrad)" rx="1" opacity="0.5"/>')

steps = [
    ("1", "Clona", "git clone dotai"),
    ("2", "Enlaza", "ln -s .claude/ tu-proyecto/"),
    ("3", "Trabaja", "claude — listo"),
]
SW = 220
SX_START = (W - SW * 3 - 24 * 2) // 2

for i, (num, title, sub) in enumerate(steps):
    sx = SX_START + i * (SW + 24)
    scx = sx + SW // 2
    sy = HY + 36

    # Step bubble
    lines.append(f'<circle cx="{scx}" cy="{sy + 28}" r="26" fill="{C_CONFIG}" opacity="0.15"/>')
    lines.append(f'<circle cx="{scx}" cy="{sy + 28}" r="26" fill="none" stroke="{C_CONFIG}" stroke-width="2"/>')
    lines.append(text_el(scx, sy + 35, num, size=22, fill=C_CONFIG, weight="bold"))

    # Arrow between steps
    if i < len(steps) - 1:
        ax = sx + SW + 4
        lines.append(f'<text x="{ax + 8}" y="{sy + 36}" font-family="{FONT}" font-size="22" fill="{TEXT3}" text-anchor="middle">→</text>')

    lines.append(text_el(scx, sy + 78, title, size=20, fill=TEXT, weight="bold"))
    lines.append(text_el(scx, sy + 100,
        sub, size=15, fill=TEXT3,
        family="monospace"))

# ── FOOTER ────────────────────────────────────────────────────────────────────
FY = H - 90

lines.append(f'<rect x="0" y="{FY - 20}" width="{W}" height="{H - FY + 20}" fill="#080B10" opacity="0.6"/>')
lines.append(f'<rect x="140" y="{FY - 20}" width="800" height="1" fill="url(#divGrad)" rx="1" opacity="0.4"/>')

# Hashtags
lines.append(text_el(W//2, FY + 14,
    "#ClaudeCode  #Java  #SpringBoot  #DevTools  #AI",
    size=18, fill=C_CONFIG, weight="bold"))

lines.append(text_el(W//2, FY + 46,
    "github.com/untalsanders/dotai",
    size=20, fill=TEXT2))

lines.append(text_el(W//2, FY + 72,
    "Configura Claude Code como un Senior Engineer de Java  ",
    size=17, fill=TEXT3))

lines.append("</svg>")

svg_path = "/scripts/instagram.svg"
with open(svg_path, "w") as f:
    f.write("\n".join(lines))
print(f"SVG generado: {svg_path}")
