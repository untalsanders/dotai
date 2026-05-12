"""
Infografía 2 — Ciclo de vida de una sesión de Claude Code
Muestra qué hooks, agentes y comandos se activan en cada fase.
"""

W, H = 2400, 1400
FONT = "Ubuntu Nerd Font"

BG      = "#0D1117"
SURFACE = "#161B22"
BORDER  = "#30363D"
TEXT    = "#E6EDF3"
TEXT2   = "#8B949E"
TEXT3   = "#6E7681"

C_AGENTS   = "#6366F1"
C_COMMANDS = "#10B981"
C_HOOKS    = "#F59E0B"
C_RULES    = "#06B6D4"
C_SKILLS   = "#EC4899"
C_CONFIG   = "#8B5CF6"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def rect(x, y, w, h, fill, rx=12, stroke=None, sw=1.5, opacity=1):
    s = stroke or "none"
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{s}" stroke-width="{sw}" opacity="{opacity}"/>')

def text_el(x, y, content, size=24, fill=TEXT, weight="normal", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'
            f'{esc(content)}</text>')

def arrow(x1, y1, x2, y2, color="#30363D", width=3):
    return (f'<defs><marker id="arr_{x2}_{y2}" markerWidth="10" markerHeight="7" '
            f'refX="9" refY="3.5" orient="auto">'
            f'<polygon points="0 0, 10 3.5, 0 7" fill="{color}"/></marker></defs>'
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{width}" marker-end="url(#arr_{x2}_{y2})"/>')

def phase_box(x, y, w, h, color, phase_num, title, description, tags):
    out = ""
    # Shadow
    out += rect(x+5, y+5, w, h, "#000", rx=14, opacity=0.4)
    # Body
    out += rect(x, y, w, h, SURFACE, rx=14, stroke=color, sw=2.5)
    # Left accent bar
    out += rect(x, y+14, 6, h-28, color, rx=3)
    # Phase number bubble
    out += f'<circle cx="{x+40}" cy="{y+46}" r="22" fill="{color}"/>'
    out += text_el(x+40, y+53, str(phase_num), size=22, fill="#fff", weight="bold", anchor="middle")
    # Title
    out += text_el(x+74, y+36, title, size=26, fill=TEXT, weight="bold")
    # Description
    lines_desc = description.split(" / ")
    for i, l in enumerate(lines_desc):
        out += text_el(x+74, y+64+i*24, l, size=18, fill=TEXT2)
    # Tags
    tx = x + 74
    ty = y + h - 42
    for tag_label, tag_color in tags:
        tw = len(tag_label)*11 + 22
        out += rect(tx, ty-18, tw, 26, tag_color, rx=6, opacity=0.18)
        out += rect(tx, ty-18, tw, 26, tag_color, rx=6, stroke=tag_color, sw=1, opacity=0.6)
        out += text_el(tx+11, ty, tag_label, size=15, fill=tag_color, weight="bold")
        tx += tw + 12
    return out

def hook_badge(x, y, label, when, color):
    w, h = 310, 110
    out  = rect(x, y, w, h, SURFACE, rx=10, stroke=color, sw=1.5)
    out += rect(x, y, w, 36, color, rx=10)
    out += rect(x, y+18, w, 18, color, rx=0)
    out += f'<text x="{x+16}" y="{y+25}" font-family="{FONT}" font-size="17" font-weight="bold" fill="#fff">{esc(label)}</text>'
    out += f'<text x="{x+14}" y="{y+60}" font-family="{FONT}" font-size="15" fill="{TEXT2}">{esc(when[:48])}</text>'
    if len(when) > 48:
        out += f'<text x="{x+14}" y="{y+80}" font-family="{FONT}" font-size="15" fill="{TEXT2}">{esc(when[48:])}</text>'
    return out


lines = []
lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
lines.append(f'''<defs>
  <linearGradient id="bg2" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#0D1117"/>
    <stop offset="100%" stop-color="#10151E"/>
  </linearGradient>
</defs>''')
lines.append(f'<rect width="{W}" height="{H}" fill="url(#bg2)"/>')

# ── Header ──────────────────────────────────────────────────────────────────
lines.append(rect(0, 0, W, 108, "#111827", rx=0))
lines.append(f'<line x1="0" y1="108" x2="{W}" y2="108" stroke="{BORDER}" stroke-width="1.5"/>')
lines.append(rect(44, 26, 56, 56, C_HOOKS, rx=10))
lines.append(text_el(47, 67, "", size=36, fill="#fff", weight="bold"))
lines.append(text_el(118, 60, "Ciclo de vida de una sesión de Claude Code", size=42, fill=TEXT, weight="bold"))
lines.append(text_el(118, 90, "Qué se activa en cada fase — hooks, agentes, comandos y skills", size=22, fill=TEXT2))
lines.append(text_el(W-44, 64, "dotai", size=32, fill=C_CONFIG, weight="bold", anchor="end"))
lines.append(text_el(W-44, 92, "Flujo de trabajo", size=20, fill=TEXT3, anchor="end"))

# ── Timeline central line ────────────────────────────────────────────────────
TIMELINE_Y = 760
lines.append(f'<line x1="44" y1="{TIMELINE_Y}" x2="{W-44}" y2="{TIMELINE_Y}" stroke="{BORDER}" stroke-width="3" stroke-dasharray="12,6"/>')

# ── Phase boxes ─────────────────────────────────────────────────────────────
phases = [
    # (x, above_timeline, num, title, desc, tags)
    (44,   True,  1, "Inicio de sesión",
     "SessionSmart.sh muestra el contexto / Git status, branch, commits sin push / Migraciones Flyway pendientes / Tests fallidos en último build",
     [("SessionSmart.sh", C_HOOKS), ("git status", TEXT3), ("Flyway info", C_RULES)]),

    (520,  False, 2, "Exploración del codebase",
     "Claude lee archivos y busca símbolos / Se delega al agente explorer / Localiza clases, interfaces y endpoints / Traza cadenas de llamadas",
     [("explorer", C_AGENTS), ("Read / Grep / Glob", TEXT3)]),

    (996,  True,  3, "Implementación de código",
     "Skill /backend o /frontend activa el flujo / PreToolUse bloquea escrituras peligrosas / PostToolUse valida arquitectura hexagonal / Agente feature-dev si se delega",
     [("PreToolUse.sh", C_HOOKS), ("PostToolUse.sh", C_HOOKS), ("/backend", C_SKILLS), ("feature-dev", C_AGENTS)]),

    (1472, False, 4, "Revisión y calidad",
     "Comando /pr-review lanza el análisis / Agente core-reviewer revisa el diff / security-auditor escanea vulnerabilidades / Reporte publicado en GitHub",
     [("/pr-review", C_COMMANDS), ("core-reviewer", C_AGENTS), ("security-auditor", C_AGENTS)]),

    (1948, True,  5, "Commit y deploy",
     "pre-commit.sh bloquea si hay errores / secrets → arquitectura → Flyway → compile → test / Comando /deploy construye y despliega / SessionSmart.sh guarda el resumen",
     [("pre-commit.sh", C_HOOKS), ("/deploy", C_COMMANDS), ("SessionSmart.sh", C_HOOKS)]),
]

PHASE_W = 420
PHASE_H_ABOVE = 370
PHASE_H_BELOW = 370

for (px, above, num, title, desc, tags) in phases:
    if above:
        py = TIMELINE_Y - PHASE_H_ABOVE - 20
        lines.append(phase_box(px, py, PHASE_W, PHASE_H_ABOVE, C_COMMANDS if num in [4] else (C_HOOKS if num in [1,5] else (C_SKILLS if num==3 else C_AGENTS)), num, title, desc, tags))
        # connector
        cx = px + PHASE_W // 2
        lines.append(f'<line x1="{cx}" y1="{py+PHASE_H_ABOVE}" x2="{cx}" y2="{TIMELINE_Y}" stroke="{BORDER}" stroke-width="2" stroke-dasharray="6,4"/>')
        lines.append(f'<circle cx="{cx}" cy="{TIMELINE_Y}" r="10" fill="{SURFACE}" stroke="{BORDER}" stroke-width="2"/>')
        lines.append(f'<circle cx="{cx}" cy="{TIMELINE_Y}" r="5" fill="{TEXT3}"/>')
    else:
        py = TIMELINE_Y + 20
        lines.append(phase_box(px, py, PHASE_W, PHASE_H_BELOW, C_COMMANDS if num in [4] else (C_HOOKS if num in [1,5] else (C_SKILLS if num==3 else C_AGENTS)), num, title, desc, tags))
        cx = px + PHASE_W // 2
        lines.append(f'<line x1="{cx}" y1="{TIMELINE_Y}" x2="{cx}" y2="{py}" stroke="{BORDER}" stroke-width="2" stroke-dasharray="6,4"/>')
        lines.append(f'<circle cx="{cx}" cy="{TIMELINE_Y}" r="10" fill="{SURFACE}" stroke="{BORDER}" stroke-width="2"/>')
        lines.append(f'<circle cx="{cx}" cy="{TIMELINE_Y}" r="5" fill="{TEXT3}"/>')

# ── Hooks summary bar ────────────────────────────────────────────────────────
BY = 1260
lines.append(rect(44, BY, W-88, 110, SURFACE, rx=12, stroke=BORDER, sw=1.5))
lines.append(text_el(74, BY+32, "Hooks de Claude Code (siempre se ejecutan — no son instrucciones opcionales)", size=19, fill=TEXT2, weight="bold"))

hooks_info = [
    ("PreToolUse.sh",  C_HOOKS,    "Antes de cada herramienta"),
    ("PostToolUse.sh", C_HOOKS,    "Después de cada herramienta"),
    ("SessionSmart.sh",C_CONFIG,   "Inicio y fin de sesión"),
    ("pre-commit.sh",  "#EF4444",  "git commit (hook de git)"),
]
hx = 74
for name, color, when in hooks_info:
    hw = len(name)*12 + len(when)*10 + 40
    lines.append(rect(hx, BY+50, hw, 46, color, rx=8, opacity=0.15))
    lines.append(rect(hx, BY+50, hw, 46, color, rx=8, stroke=color, sw=1, opacity=0.5))
    lines.append(text_el(hx+14, BY+72, name, size=18, fill=color, weight="bold"))
    lines.append(text_el(hx+14, BY+90, when, size=15, fill=TEXT2))
    hx += hw + 18

# ── Footer ──────────────────────────────────────────────────────────────────
lines.append(f'<line x1="0" y1="{H-44}" x2="{W}" y2="{H-44}" stroke="{BORDER}" stroke-width="1"/>')
legend = [
    (C_HOOKS,    "Hooks"),
    (C_AGENTS,   "Agents"),
    (C_COMMANDS, "Commands"),
    (C_SKILLS,   "Skills"),
    (C_CONFIG,   "Config"),
]
lx = 44
for color, label in legend:
    lines.append(f'<circle cx="{lx+8}" cy="{H-18}" r="7" fill="{color}"/>')
    lines.append(text_el(lx+22, H-12, label, size=17, fill=TEXT2))
    lx += len(label)*12 + 38
lines.append(text_el(W-44, H-12, "dotai · Ciclo de vida de Claude Code", size=17, fill=TEXT3, anchor="end"))

lines.append("</svg>")

svg_path = "/infographics/ciclo_de_vida.svg"
with open(svg_path, "w") as f:
    f.write("\n".join(lines))
print(f"SVG generado: {svg_path}")
