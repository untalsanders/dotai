"""
Infografía 3 — Red de agentes dotai
Los 8 subagentes: modelo, herramientas, propósito y proceso.
"""

W, H = 2400, 1760
FONT = "Ubuntu Nerd Font"

BG      = "#0D1117"
SURFACE = "#161B22"
SURFACE2= "#1C2128"
BORDER  = "#30363D"
TEXT    = "#E6EDF3"
TEXT2   = "#8B949E"
TEXT3   = "#6E7681"
C_AGENTS = "#6366F1"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def rect(x, y, w, h, fill, rx=12, stroke=None, sw=1.5, opacity=1):
    s = stroke or "none"
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{s}" stroke-width="{sw}" opacity="{opacity}"/>')

def text_el(x, y, content, size=22, fill=TEXT, weight="normal", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'
            f'{esc(content)}</text>')

def pill(x, y, label, bg, fg="#fff"):
    w = len(label) * 10 + 20
    out  = rect(x, y-17, w, 24, bg, rx=12)
    out += text_el(x+10, y, label, size=14, fill=fg, weight="bold")
    return out, w

def agent_card(x, y, w, h, color, name, icon, model, tools, description, steps):
    out = ""
    # Shadow
    out += rect(x+4, y+4, w, h, "#000", rx=14, opacity=0.4)
    # Body
    out += rect(x, y, w, h, SURFACE, rx=14, stroke=color, sw=2)
    # Header bar
    out += rect(x, y, w, 62, color, rx=14)
    out += rect(x, y+42, w, 20, color, rx=0)

    # Icon circle
    out += f'<circle cx="{x+38}" cy="{y+31}" r="22" fill="rgba(0,0,0,0.25)"/>'
    out += text_el(x+38, y+38, icon, size=22, fill="#fff", weight="bold", anchor="middle")

    # Agent name
    out += text_el(x+70, y+25, name, size=22, fill="#fff", weight="bold")

    # Model badge
    model_color = "#10B981" if model == "sonnet" else "#F59E0B"
    model_label = f" {model}"
    out += rect(x+70, y+32, len(model_label)*10+16, 22, model_color, rx=5, opacity=0.9)
    out += text_el(x+78, y+47, model_label, size=14, fill="#fff", weight="bold")

    # Description
    desc_words = description.split()
    desc_lines = []
    current = ""
    for word in desc_words:
        if len(current) + len(word) + 1 > 44:
            desc_lines.append(current)
            current = word
        else:
            current = (current + " " + word).strip()
    if current:
        desc_lines.append(current)

    dy = y + 82
    for dl in desc_lines[:3]:
        out += text_el(x+18, dy, dl, size=17, fill=TEXT2)
        dy += 22

    # Tools section
    dy += 6
    out += text_el(x+18, dy, "Herramientas:", size=15, fill=TEXT3, weight="bold")
    dy += 20
    tx = x + 18
    for tool in tools:
        tw = len(tool)*9 + 18
        if tx + tw > x + w - 14:
            tx = x + 18
            dy += 24
        out += rect(tx, dy-16, tw, 22, SURFACE2, rx=5, stroke=BORDER, sw=1)
        out += text_el(tx+9, dy, tool, size=13, fill=TEXT2)
        tx += tw + 8
    dy += 28

    # Divider
    out += f'<line x1="{x+14}" y1="{dy}" x2="{x+w-14}" y2="{dy}" stroke="{BORDER}" stroke-width="1"/>'
    dy += 18

    # Steps
    out += text_el(x+18, dy, "Proceso:", size=15, fill=TEXT3, weight="bold")
    dy += 22
    for i, step in enumerate(steps[:5]):
        out += f'<circle cx="{x+27}" cy="{dy-5}" r="9" fill="{color}" opacity="0.85"/>'
        out += text_el(x+27, dy-1, str(i+1), size=12, fill="#fff", weight="bold", anchor="middle")
        # Wrap step text
        step_words = step.split()
        step_line = ""
        step_lines_list = []
        for word in step_words:
            if len(step_line) + len(word) + 1 > 38:
                step_lines_list.append(step_line)
                step_line = word
            else:
                step_line = (step_line + " " + word).strip()
        if step_line:
            step_lines_list.append(step_line)
        for sl in step_lines_list[:2]:
            out += text_el(x+44, dy, sl, size=15, fill=TEXT)
            dy += 19
        dy += 6

    return out


# ── Agents data ─────────────────────────────────────────────────────────────
AGENTS = [
    {
        "name": "core-reviewer", "icon": "", "color": "#6366F1",
        "model": "sonnet", "tools": ["Read", "Glob", "Grep", "Bash"],
        "description": "Revisa código antes del merge detectando bugs, violaciones de arquitectura y gaps de testing",
        "steps": ["Leer el diff completo", "Verificar arquitectura hexagonal", "Escanear secrets y SQL injection", "Analizar calidad del código", "Ejecutar ./mvnw verify", "Publicar reporte BLOQUEANTE/WARNING/OK"],
    },
    {
        "name": "debugger", "icon": "", "color": "#EF4444",
        "model": "sonnet", "tools": ["Read", "Glob", "Grep", "Bash"],
        "description": "Diagnostica bugs trazando la causa raíz desde los logs hasta el código fuente sin asumir nada",
        "steps": ["Recolectar logs y stack traces", "Leer stack trace de adentro hacia afuera", "Reproducir en un test que falla", "Trazar el flujo capa por capa", "Formular hipótesis y verificar", "Implementar el fix mínimo"],
    },
    {
        "name": "doc-writer", "icon": "", "color": "#F59E0B",
        "model": "haiku", "tools": ["Read", "Glob", "Grep", "Write", "Edit", "Bash"],
        "description": "Genera Javadoc en puertos, anotaciones OpenAPI en controllers y actualiza documentación técnica",
        "steps": ["Inventariar qué necesita documentación", "Escribir Javadoc en interfaces de puertos", "Anotar controllers con @Operation", "Documentar Value Objects y excepciones", "Verificar que OpenAPI spec es válido"],
    },
    {
        "name": "explorer", "icon": "", "color": "#06B6D4",
        "model": "haiku", "tools": ["Read", "Glob", "Grep", "Bash"],
        "description": "Localiza clases, interfaces, endpoints y traza cadenas de llamadas en el codebase sin modificar nada",
        "steps": ["Localizar clase o interfaz por nombre", "Encontrar implementaciones de interfaz", "Mapear endpoints REST existentes", "Trazar cadena: controller → use case → repo", "Reportar con archivo y número de línea"],
    },
    {
        "name": "feature-dev", "icon": "", "color": "#10B981",
        "model": "sonnet", "tools": ["Read", "Glob", "Grep", "Write", "Edit", "Bash"],
        "description": "Implementa features completas siguiendo arquitectura hexagonal: dominio, caso de uso, persistencia, REST y tests",
        "steps": ["Explorar el estado actual del codebase", "Modelar dominio: VOs, entidad, puertos", "Implementar caso de uso con @Transactional", "Crear adapter JPA + migración Flyway", "Crear controller + DTOs + OpenAPI", "Escribir tests unitarios y de integración"],
    },
    {
        "name": "refactorer", "icon": "", "color": "#EC4899",
        "model": "sonnet", "tools": ["Read", "Glob", "Grep", "Write", "Edit", "Bash"],
        "description": "Mejora la estructura interna del código sin cambiar su comportamiento aplicando SOLID y patrones Java 21",
        "steps": ["Establecer línea base con mvnw verify", "Identificar métodos largos y duplicación", "Priorizar por impacto y riesgo", "Aplicar refactorings atómicos", "Ejecutar tests después de cada cambio", "Commit separado por cada refactoring"],
    },
    {
        "name": "security-auditor", "icon": "", "color": "#8B5CF6",
        "model": "sonnet", "tools": ["Read", "Glob", "Grep", "Bash"],
        "description": "Audita OWASP Top 10, credenciales expuestas, IDOR, CORS permisivo y configuración insegura de producción",
        "steps": ["Escanear secrets hardcodeados en diff", "Detectar inyección SQL por concatenación", "Revisar auth/authz e IDOR", "Verificar validación de entrada", "Revisar CORS y headers de seguridad", "Clasificar: CRÍTICO / ALTO / MEDIO"],
    },
    {
        "name": "test-writter", "icon": "", "color": "#14B8A6",
        "model": "sonnet", "tools": ["Read", "Glob", "Grep", "Write", "Edit", "Bash"],
        "description": "Escribe suites de tests unitarios, slices @WebMvcTest e integración con Testcontainers para PostgreSQL real",
        "steps": ["Analizar código a testear", "Tests unitarios del dominio (sin Spring)", "Tests del caso de uso con mocks manuales", "Tests de slice del controller @WebMvcTest", "Tests de repo con @DataJpaTest + Testcontainers", "Verificar con ./mvnw verify"],
    },
]

# ── SVG ─────────────────────────────────────────────────────────────────────
lines = []
lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
lines.append(f'''<defs>
  <linearGradient id="bg3" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#0D1117"/>
    <stop offset="100%" stop-color="#0F172A"/>
  </linearGradient>
</defs>''')
lines.append(f'<rect width="{W}" height="{H}" fill="url(#bg3)"/>')

# ── Header ──────────────────────────────────────────────────────────────────
lines.append(rect(0, 0, W, 108, "#111827", rx=0))
lines.append(f'<line x1="0" y1="108" x2="{W}" y2="108" stroke="{BORDER}" stroke-width="1.5"/>')
lines.append(rect(44, 26, 56, 56, C_AGENTS, rx=28))
lines.append(text_el(72, 66, "", size=34, fill="#fff", weight="bold", anchor="middle"))
lines.append(text_el(118, 60, "Red de agentes dotai", size=42, fill=TEXT, weight="bold"))
lines.append(text_el(118, 90, "8 subagentes especializados — cada uno con modelo, herramientas y proceso propios", size=22, fill=TEXT2))
lines.append(text_el(W-44, 58, "sonnet", size=20, fill="#10B981", weight="bold", anchor="end"))
lines.append(text_el(W-44, 82, "haiku", size=20, fill="#F59E0B", weight="bold", anchor="end"))
lines.append(text_el(W-44, 100, "Modelos disponibles", size=16, fill=TEXT3, anchor="end"))

# ── Agent cards grid: 4 cols × 2 rows ───────────────────────────────────────
CARD_W = 548
CARD_H = 760
PAD_X  = 44
PAD_Y  = 130
GAP_X  = 26
GAP_Y  = 32
COLS   = 4

for i, agent in enumerate(AGENTS):
    col = i % COLS
    row = i // COLS
    cx = PAD_X + col * (CARD_W + GAP_X)
    cy = PAD_Y + row * (CARD_H + GAP_Y)
    lines.append(agent_card(
        cx, cy, CARD_W, CARD_H,
        agent["color"], agent["name"], agent["icon"],
        agent["model"], agent["tools"],
        agent["description"], agent["steps"]
    ))

# ── Footer ──────────────────────────────────────────────────────────────────
FY = H - 46
lines.append(f'<line x1="0" y1="{FY-12}" x2="{W}" y2="{FY-12}" stroke="{BORDER}" stroke-width="1"/>')
lines.append(text_el(44, FY+12, "Los agentes de haiku son más rápidos para búsquedas. Los de sonnet para razonamiento complejo.", size=18, fill=TEXT3))
lines.append(text_el(W-44, FY+12, "dotai · Red de agentes Claude Code", size=18, fill=TEXT3, anchor="end"))

lines.append("</svg>")

svg_path = "/infographics/agentes.svg"
with open(svg_path, "w") as f:
    f.write("\n".join(lines))
print(f"SVG generado: {svg_path}")
