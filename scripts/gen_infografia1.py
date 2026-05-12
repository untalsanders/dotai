"""
Infografía 1 — Ecosistema dotai
Mapa completo de todos los componentes del proyecto.
"""

W, H = 2400, 1700
FONT = "Ubuntu Nerd Font"

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
C_BADGE    = "#21262D"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rect(x, y, w, h, fill, rx=12, stroke=None, stroke_w=1.5, opacity=1):
    s = stroke or "none"
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{s}" stroke-width="{stroke_w}" opacity="{opacity}"/>')


def text(x, y, content, size=28, fill=TEXT, weight="normal", anchor="start", family=FONT):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'
            f'{esc(content)}</text>')


def badge(x, y, label, color, text_color="#FFFFFF"):
    w = len(label) * 11 + 24
    out  = rect(x, y - 18, w, 26, color, rx=6)
    out += f'<text x="{x+12}" y="{y}" font-family="{FONT}" font-size="16" '
    out += f'font-weight="bold" fill="{text_color}">{esc(label)}</text>'
    return out, w


def card(x, y, w, h, color, title, icon, items, subtitle=""):
    out = ""
    # Shadow
    out += rect(x+6, y+6, w, h, "#000000", rx=14, opacity=0.35)
    # Card body
    out += rect(x, y, w, h, SURFACE, rx=14, stroke=color, stroke_w=2)
    # Top bar
    out += rect(x, y, w, 56, color, rx=14)
    out += rect(x, y+28, w, 28, color, rx=0)
    # Icon + Title
    out += f'<text x="{x+22}" y="{y+38}" font-family="{FONT}" font-size="26" font-weight="bold" fill="#FFFFFF">{esc(icon)}  {esc(title)}</text>'
    if subtitle:
        out += f'<text x="{x+22}" y="{y+78}" font-family="{FONT}" font-size="19" fill="{TEXT2}">{esc(subtitle)}</text>'
    # Items
    start_y = y + (98 if subtitle else 84)
    for i, (name, desc) in enumerate(items):
        iy = start_y + i * 58
        # file bullet
        out += f'<circle cx="{x+30}" cy="{iy+4}" r="5" fill="{color}" opacity="0.8"/>'
        # filename
        out += f'<text x="{x+48}" y="{iy+9}" font-family="{FONT}" font-size="20" font-weight="bold" fill="{TEXT}">{esc(name)}</text>'
        # description
        out += f'<text x="{x+48}" y="{iy+30}" font-family="{FONT}" font-size="17" fill="{TEXT2}">{esc(desc)}</text>'
        # separator line
        if i < len(items) - 1:
            out += f'<line x1="{x+22}" y1="{iy+44}" x2="{x+w-22}" y2="{iy+44}" stroke="{BORDER}" stroke-width="1"/>'
    return out


# ── Layout ─────────────────────────────────────────────────────────────────
lines = []
lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')

# Background gradient
lines.append(f'''<defs>
  <linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%"   stop-color="#0D1117"/>
    <stop offset="100%" stop-color="#111827"/>
  </linearGradient>
  <linearGradient id="headerGrad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%"   stop-color="#1e1b4b"/>
    <stop offset="100%" stop-color="#0D1117"/>
  </linearGradient>
</defs>''')
lines.append(f'<rect width="{W}" height="{H}" fill="url(#bgGrad)"/>')

# ── Header ──────────────────────────────────────────────────────────────────
lines.append(rect(0, 0, W, 110, "url(#headerGrad)", rx=0))
lines.append(f'<line x1="0" y1="110" x2="{W}" y2="110" stroke="{BORDER}" stroke-width="1.5"/>')
# Logo mark
lines.append(rect(44, 28, 54, 54, C_CONFIG, rx=10))
lines.append(text(46, 68, "", size=36, fill="#FFFFFF", weight="bold"))
# Title
lines.append(text(118, 62, "dotai", size=46, fill=TEXT, weight="bold"))
lines.append(text(118, 90, "Ecosistema de configuración para Claude Code", size=22, fill=TEXT2))
# Subtitle right
lines.append(text(W-44, 58, "Java 21 · Spring Boot 3 · Arquitectura Hexagonal", size=21, fill=TEXT3, anchor="end"))
lines.append(text(W-44, 88, "claude.ai/code", size=20, fill=C_CONFIG, anchor="end"))

# ── Config files row (small cards) ─────────────────────────────────────────
CY = 140
lines.append(text(44, CY + 36, "Configuración global", size=22, fill=TEXT2, weight="bold"))

# CLAUDE.md mini card
lines.append(rect(44, CY+48, 520, 88, SURFACE, rx=10, stroke=C_CONFIG, stroke_w=2))
lines.append(rect(44, CY+48, 520, 38, C_CONFIG, rx=10))
lines.append(rect(44, CY+72, 520, 14, C_CONFIG, rx=0))
lines.append(text(68, CY+76, " CLAUDE.md", size=22, fill="#fff", weight="bold"))
lines.append(text(68, CY+114, "Instrucciones globales: rol, stack, convenciones y antipatrones", size=18, fill=TEXT2))

# settings.json mini card
lines.append(rect(584, CY+48, 520, 88, SURFACE, rx=10, stroke=C_CONFIG, stroke_w=2))
lines.append(rect(584, CY+48, 520, 38, C_CONFIG, rx=10))
lines.append(rect(584, CY+72, 520, 14, C_CONFIG, rx=0))
lines.append(text(608, CY+76, " settings.json", size=22, fill="#fff", weight="bold"))
lines.append(text(608, CY+114, "Permisos de herramientas, variables de entorno y registro de hooks", size=18, fill=TEXT2))

# ── Main cards grid 3x2 ─────────────────────────────────────────────────────
CARD_W  = 720
CARD_H  = 640
PAD_X   = 44
PAD_Y   = 310
GAP_X   = 48
GAP_Y   = 42

cards_data = [
    # (color, title, icon, subtitle, items)
    (C_AGENTS, "agents/", "", "8 subagentes especializados con rol y herramientas propias", [
        ("core-reviewer", "Revisa código: arquitectura, seguridad y tests"),
        ("debugger", "Traza la causa raíz de un bug paso a paso"),
        ("doc-writer", "Genera Javadoc y anotaciones OpenAPI"),
        ("explorer", "Localiza clases, métodos y flujos en el codebase"),
        ("feature-dev", "Implementa features completas en arquitectura hexagonal"),
        ("refactorer", "Mejora estructura sin cambiar comportamiento"),
        ("security-auditor", "Audita OWASP Top 10, secrets y configuración insegura"),
        ("test-writter", "Escribe tests unitarios, slice e integración"),
    ]),
    (C_COMMANDS, "commands/", "", "Slash commands — flujos operativos invocados con /nombre", [
        ("/fix-issue <N>", "Lee el issue, implementa el fix, corre tests y abre PR"),
        ("/pr-review [N]", "Revisa el PR y publica reporte en GitHub"),
        ("/deploy <env>", "Build → Docker → kubectl → health check → rollback si falla"),
    ]),
    (C_HOOKS, "hooks/", "", "Scripts ejecutados automáticamente en eventos del ciclo de vida", [
        ("PreToolUse.sh", "Bloquea rm -rf, force push, reset --hard y migración sobreescrita"),
        ("PostToolUse.sh", "Detecta violaciones de arquitectura y audita en log diario"),
        ("SessionSmart.sh", "Contexto al inicio, resumen persistido al final de sesión"),
        ("pre-commit.sh", "Git hook: secrets → arquitectura → Flyway → compile → test"),
    ]),
    (C_RULES, "rules/", "", "Reglas por dominio que Claude aplica al generar código", [
        ("architecture.md", "Hexagonal, SOLID, DDD táctico, aggregates y eventos"),
        ("api.md", "REST, envelope {data,error,meta}, ProblemDetail, paginación"),
        ("database.md", "JPA vs JDBC, Flyway, N+1, transacciones, HikariCP"),
        ("frontend.md", "CORS, JWT httpOnly, schemas null-safe, OpenAPI como contrato"),
    ]),
    (C_SKILLS, "skills/", "", "Flujos de implementación invocados como slash commands", [
        ("/backend <feature>", "7 fases: dominio → use case → persistencia → REST → tests"),
        ("/frontend <desc>", "Diseña endpoints, schemas, errores y tests de contrato"),
        ("context.md", "Contexto compartido inyectado en todas las skills"),
        ("SKILL.md", "Plantilla para crear nuevas skills personalizadas"),
    ]),
]

positions = [
    (PAD_X,                    PAD_Y),
    (PAD_X + CARD_W + GAP_X,  PAD_Y),
    (PAD_X + (CARD_W+GAP_X)*2, PAD_Y),
    (PAD_X,                    PAD_Y + CARD_H + GAP_Y),
    (PAD_X + CARD_W + GAP_X,  PAD_Y + CARD_H + GAP_Y),
]

for idx, (color, title, icon, subtitle, items) in enumerate(cards_data):
    cx, cy = positions[idx]
    # Trim items to fit card height (max 8 items in agents, others 4)
    lines.append(card(cx, cy, CARD_W, CARD_H, color, title, icon, items, subtitle))

# ── Legend / footer ──────────────────────────────────────────────────────────
FY = H - 52
lines.append(f'<line x1="0" y1="{FY-14}" x2="{W}" y2="{FY-14}" stroke="{BORDER}" stroke-width="1"/>')

legend = [
    (C_AGENTS, "Agents"),
    (C_COMMANDS, "Commands"),
    (C_HOOKS, "Hooks"),
    (C_RULES, "Rules"),
    (C_SKILLS, "Skills"),
    (C_CONFIG, "Config"),
]
lx = 44
for color, label in legend:
    lines.append(f'<circle cx="{lx+8}" cy="{FY+8}" r="8" fill="{color}"/>')
    lines.append(text(lx+22, FY+14, label, size=18, fill=TEXT2))
    lx += len(label)*13 + 44

lines.append(text(W-44, FY+14, "dotai · github.com/tu-usuario/dotai", size=18, fill=TEXT3, anchor="end"))

lines.append("</svg>")

svg_path = "/infographics/ecosistema.svg"
with open(svg_path, "w") as f:
    f.write("\n".join(lines))

print(f"SVG generado: {svg_path}")
