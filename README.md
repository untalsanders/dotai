# dotai

Repositorio de configuración y dotfiles para [Claude Code](https://claude.ai/code) — la CLI oficial de Anthropic para Claude. Centraliza en un solo lugar los agentes, comandos personalizados, reglas, hooks y skills que definen cómo Claude trabaja en cualquier proyecto del equipo.

**Stack de referencia:** Java 21 · Spring Boot 3 · Arquitectura Hexagonal · Maven · PostgreSQL.

La idea es sencilla: clonar este repo, enlazar la carpeta `.claude/` al proyecto y obtener el mismo entorno de trabajo en cualquier máquina.

---

## Estructura del proyecto

```
dotai/
├── .claude/
│   ├── CLAUDE.md                   # Instrucciones y contexto global para Claude
│   ├── settings.json               # Permisos, variables de entorno y configuración del harness
│   │
│   ├── agents/                     # Subagentes especializados — cada uno es un experto delegable
│   │   ├── core-reviewer.md        # Revisa código antes del merge (arquitectura, seguridad, tests)
│   │   ├── debugger.md             # Diagnostica bugs trazando la causa raíz
│   │   ├── doc-writer.md           # Genera Javadoc, anotaciones OpenAPI y documentación técnica
│   │   ├── explorer.md             # Localiza clases, métodos, endpoints y flujos en el codebase
│   │   ├── feature-dev.md          # Implementa features completas siguiendo arquitectura hexagonal
│   │   ├── refactorer.md           # Mejora la estructura interna sin cambiar el comportamiento
│   │   ├── security-auditor.md     # Audita vulnerabilidades OWASP, secrets y configuración insegura
│   │   └── test-writter.md         # Escribe suites de tests unitarios, slice e integración
│   │
│   ├── commands/                   # Slash commands personalizados invocables con /nombre
│   │   ├── fix-issue.md            # /fix-issue <N> — corrige un issue de GitHub de punta a punta
│   │   ├── pr-review.md            # /pr-review [N] — revisa un PR y publica un reporte estructurado
│   │   └── deploy.md               # /deploy <entorno> — construye, valida y despliega la aplicación
│   │
│   ├── hooks/                      # Scripts ejecutados automáticamente por el harness de Claude Code
│   │   ├── PreToolUse.sh           # Guarda antes de cada herramienta (bloquea destructivos)
│   │   ├── PostToolUse.sh          # Audita y valida arquitectura después de cada herramienta
│   │   ├── SessionSmart.sh         # Contexto al inicio y resumen al fin de cada sesión
│   │   └── pre-commit.sh           # Git hook: compile → secrets → arquitectura → tests
│   │
│   ├── rules/                      # Reglas por dominio técnico que Claude aplica al generar código
│   │   ├── architecture.md         # Arquitectura hexagonal, SOLID, patrones de dominio
│   │   ├── api.md                  # Diseño REST, envelope de respuesta, errores, paginación
│   │   ├── database.md             # JPA vs JDBC, Flyway, queries, transacciones, HikariCP
│   │   └── frontend.md             # Contrato backend-frontend: CORS, JWT, schemas, OpenAPI
│   │
│   └── skills/                     # Flujos de trabajo reutilizables invocables como /nombre
│       ├── SKILL.md                # Plantilla para crear nuevas skills
│       ├── context.md              # Contexto compartido inyectado en todas las skills
│       ├── backend/
│       │   └── SKILL.md            # /backend — implementa una feature de backend completa
│       └── frontend/
│           └── SKILL.md            # /frontend — diseña el contrato de API para el frontend
│
├── infographics/                   # Infografías del proyecto en SVG y PNG 4K
│   ├── ecosistema.svg / .png       # Mapa completo de todos los componentes
│   ├── ciclo_de_vida.svg / .png    # Ciclo de vida de una sesión de Claude Code
│   ├── agentes.svg / .png          # Los 8 agentes con modelo, herramientas y proceso
│   ├── gen_infografia1.py          # Script generador — ecosistema
│   ├── gen_infografia2.py          # Script generador — ciclo de vida
│   └── gen_infografia3.py          # Script generador — agentes
│
├── .gitignore
└── README.md
```

---

## `.claude/CLAUDE.md`

Archivo de instrucciones globales que Claude lee al inicio de cada conversación. Define el rol del asistente, el stack tecnológico, la arquitectura esperada, las convenciones de código, las reglas de API, persistencia, seguridad, testing, rendimiento y una lista explícita de antipatrones a evitar.

Es el punto de entrada de toda la configuración. Si un comportamiento debe aplicarse en **todo** el proyecto, va aquí.

---

## `.claude/settings.json`

Controla el comportamiento del harness de Claude Code:

- **Permisos** — qué herramientas y comandos puede ejecutar Claude sin pedir confirmación.
- **Variables de entorno** — valores inyectados en cada sesión.
- **Registro de hooks** — qué scripts se asocian a cada evento del ciclo de vida.

Es el archivo que hace que los hooks se ejecuten automáticamente.

---

## `.claude/agents/`

Los agentes son subinstancias especializadas de Claude que el agente principal puede invocar para delegar tareas concretas. Cada archivo `.md` define el rol, las herramientas disponibles (`tools`), el modelo a usar y el proceso paso a paso que debe seguir.

**Ventajas de usar agentes:**
- Aíslan el contexto del agente principal — conversaciones más limpias y precisas.
- Permiten ejecutar tareas en paralelo.
- Cada agente tiene acceso solo a las herramientas que necesita.

| Agente | Modelo | Herramientas | Para qué sirve |
|---|---|---|---|
| `core-reviewer` | sonnet | Read, Glob, Grep, Bash | Revisa diffs antes del merge: arquitectura, seguridad, calidad y cobertura |
| `debugger` | sonnet | Read, Glob, Grep, Bash | Traza la causa raíz de un bug desde los logs hasta el código fuente |
| `doc-writer` | haiku | Read, Glob, Grep, Write, Edit, Bash | Genera Javadoc en puertos, `@Operation` en controllers y actualiza docs técnicos |
| `explorer` | haiku | Read, Glob, Grep, Bash | Localiza clases, interfaces, endpoints y traza cadenas de llamadas |
| `feature-dev` | sonnet | Read, Glob, Grep, Write, Edit, Bash | Implementa features completas: dominio → caso de uso → persistencia → REST → tests |
| `refactorer` | sonnet | Read, Glob, Grep, Write, Edit, Bash | Refactoriza sin cambiar comportamiento: extrae métodos, aplica SOLID, convierte a `record` |
| `security-auditor` | sonnet | Read, Glob, Grep, Bash | Audita OWASP Top 10, secrets expuestos, IDOR, CORS, Actuator sin protección |
| `test-writter` | sonnet | Read, Glob, Grep, Write, Edit, Bash | Escribe tests unitarios, slices `@WebMvcTest` e integración con Testcontainers |

**Estructura de un agente:**

```markdown
---
name: core-reviewer
description: Revisa código antes del merge. Detecta bugs, violaciones de arquitectura,
             problemas de seguridad y gaps de testing.
tools: Read, Glob, Grep, Bash
model: sonnet
---

Eres un senior code reviewer especializado en Java 21 y Spring Boot 3...

## Proceso
Paso 1 — Leer el diff completo ...
Paso 2 — Verificar arquitectura hexagonal ...
...
```

---

## `.claude/commands/`

Los comandos son slash commands personalizados invocados escribiendo `/nombre [argumento]` en Claude Code. Encapsulan flujos de trabajo completos y repetitivos. Usan `$ARGUMENTS` para recibir parámetros del usuario.

| Comando | Invocación | Qué hace |
|---|---|---|
| `fix-issue.md` | `/fix-issue 42` | Lee el issue de GitHub, localiza el código afectado, escribe el test que falla, implementa el fix mínimo, corre `./mvnw verify` y abre el PR |
| `pr-review.md` | `/pr-review [N]` | Revisa el PR (activo o por número) contra las reglas de arquitectura, API, BD y seguridad; publica el reporte como comentario en GitHub |
| `deploy.md` | `/deploy staging` | Valida el branch, corre tests, construye la imagen Docker, despliega con `kubectl`, verifica el health check y las migraciones Flyway; hace rollback automático si algo falla |

**Estructura de un comando:**

```markdown
---
name: fix-issue
description: Lee un issue de GitHub, implementa el fix mínimo, escribe el test
             de regresión y abre el PR.
argument-hint: <issue-number>
---

Resuelve el issue de GitHub #$ARGUMENTS siguiendo estos pasos:

## 1. Leer y entender el issue
gh issue view $ARGUMENTS
...
## 5. Ejecutar la suite completa
./mvnw verify -q
...
```

---

## `.claude/hooks/`

Los hooks son scripts de shell que el harness de Claude Code ejecuta automáticamente cuando ocurre un evento. A diferencia de las instrucciones en `CLAUDE.md` (que Claude puede o no seguir), los hooks **siempre se ejecutan** — son la capa de control obligatorio.

| Script | Tipo | Evento | Qué hace |
|---|---|---|---|
| `PreToolUse.sh` | Claude Code hook | Antes de cada herramienta | Bloquea `rm -rf` críticos, force push a main, `git reset --hard`, DROP TABLE y sobreescritura de migraciones Flyway existentes |
| `PostToolUse.sh` | Claude Code hook | Después de cada herramienta | Detecta imports de Spring/JPA en `domain/`, entidades JPA en la capa web, y registra un log de auditoría en `~/.claude/logs/` |
| `SessionSmart.sh` | Claude Code hook | Inicio y fin de sesión | Al iniciar: muestra branch, archivos sucios, commits sin push, última migración y tests fallidos. Al finalizar: guarda un resumen en `~/.claude/projects/.../memory/` |
| `pre-commit.sh` | Git hook | `git commit` | Ejecuta 5 checks secuenciales: secrets en el diff, violaciones de arquitectura hexagonal, convención de nombres Flyway, `./mvnw compile` y `./mvnw test` |

### Códigos de salida de los Claude Code hooks

| Código | Efecto |
|---|---|
| `0` | Claude procede normalmente |
| `1` | Claude recibe el mensaje de stderr como advertencia y puede decidir |
| `2` | Acción **bloqueada** — Claude no puede continuar con esa herramienta |

### Instalar el git hook

`pre-commit.sh` es un hook de git estándar, no de Claude Code. Debe instalarse manualmente en cada repositorio donde quieras usarlo:

```bash
ln -s /ruta/a/dotai/.claude/hooks/pre-commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Checks que ejecuta `pre-commit.sh`:**

```
[1/5] Secrets en el diff         → bloquea si hay passwords/tokens hardcodeados
[2/5] Arquitectura hexagonal      → bloquea si domain/ tiene imports de Spring/JPA
[3/5] Convención Flyway           → bloquea si el nombre no es V1.2.3__descripcion.sql
[4/5] ./mvnw compile              → bloquea si hay errores de compilación
[5/5] ./mvnw test                 → bloquea si hay tests fallidos
```

---

## `.claude/rules/`

Las reglas son instrucciones específicas por dominio técnico. Son más granulares que `CLAUDE.md`: en lugar de definir el comportamiento general, cada archivo dicta las convenciones, patrones y restricciones de un área concreta. Claude las carga cuando trabaja en código de ese dominio.

| Archivo | Dominio | Qué define |
|---|---|---|
| `architecture.md` | Arquitectura | Arquitectura hexagonal con diagramas, reglas de dependencia entre capas, patrones DDD tácticos (aggregates, value objects, eventos de dominio), tabla SOLID con señales de violación |
| `api.md` | API REST | Diseño de URLs y métodos HTTP, tabla completa de códigos de estado, envelope `{data, error, meta}`, `ProblemDetail` RFC 9457, paginación con `Pageable`, validación con Bean Validation, versionado, idempotency keys, documentación OpenAPI |
| `database.md` | Persistencia | Árbol de decisión JPA vs JDBC, convenciones de entidades JPA, las tres soluciones al N+1 (`@EntityGraph`, `JOIN FETCH`, proyecciones), formato de migraciones Flyway, gestión de transacciones, configuración de HikariCP, features de PostgreSQL a aprovechar |
| `frontend.md` | Contrato backend-frontend | Configuración de CORS por perfil, flujo JWT con refresh token en cookie `httpOnly`, campos `null` vs ausentes en la respuesta, estructura de errores con array `errors[{field, message}]`, cuándo usar SSE vs WebSocket, documentación OpenAPI como contrato de equipo |

---

## `.claude/skills/`

Las skills son flujos de trabajo reutilizables invocados como slash commands. A diferencia de los `commands/` (que automatizan tareas operativas), las skills guían la implementación de código siguiendo las convenciones del proyecto.

| Skill | Invocación | Qué hace |
|---|---|---|
| `backend/` | `/backend <descripcion>` | Implementa una feature completa en 7 fases: explorar el estado actual → modelar el dominio → implementar el caso de uso → crear el adapter de persistencia con migración Flyway → crear el adapter web con DTOs y OpenAPI → escribir los tres niveles de tests → verificar con `./mvnw verify` |
| `frontend/` | `/frontend <descripcion>` | Diseña el contrato de API para el frontend en 7 fases: entender qué pantallas necesita → diseñar endpoints → definir schemas de request/response → diseñar errores con `errors[{field, message}]` → definir filtros y paginación → documentar con `@Operation` → escribir tests de contrato |

**Archivos de soporte:**

- **`SKILL.md` (raíz)** — Plantilla y guía para crear nuevas skills: formato del frontmatter, cómo estructurar los pasos, convenciones de nomenclatura.
- **`context.md`** — Contexto compartido inyectado en todas las skills: stack tecnológico, estructura de paquetes, tabla de nomenclatura completa, reglas de dependencia entre capas, contratos fijos (envelope, `ProblemDetail`), comandos Maven frecuentes y archivos clave a leer antes de implementar.

---

## Primeros pasos

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/dotai.git
```

### 2. Enlazar la configuración a tu proyecto

```bash
# Opción A — symlink (los cambios en dotai se reflejan automáticamente)
ln -s /ruta/a/dotai/.claude /ruta/a/tu-proyecto/.claude

# Opción B — copiar (configuración independiente por proyecto)
cp -r /ruta/a/dotai/.claude /ruta/a/tu-proyecto/.claude
```

### 3. Instalar el git hook (opcional pero recomendado)

```bash
cd /ruta/a/tu-proyecto
ln -s /ruta/a/dotai/.claude/hooks/pre-commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### 4. Abrir Claude Code

```bash
claude
```

La configuración de `.claude/` se carga automáticamente. Los hooks se activan desde `settings.json`.

### 5. Verificar que todo funciona

```bash
# Probar un slash command
/fix-issue --help

# Probar un skill
/backend "endpoint de ejemplo"
```

---

## Personalizar para tu proyecto

Este repositorio está configurado para un stack Java 21 + Spring Boot 3. Para adaptarlo a otro stack:

1. **`CLAUDE.md`** — Actualiza el rol, el stack tecnológico y las convenciones de código.
2. **`rules/`** — Reescribe o agrega archivos con las reglas de tu stack (p.ej. `rules/nodejs.md`, `rules/python.md`).
3. **`hooks/pre-commit.sh`** — Reemplaza `./mvnw compile` y `./mvnw test` con los comandos de tu build tool.
4. **`skills/`** — Crea skills específicas para los flujos de tu proyecto.
5. **`agents/`** — Ajusta los modelos y herramientas según las necesidades de cada agente.

---

## Contribuir

1. Crea una rama desde `main`.
2. Agrega o modifica la configuración que necesites.
3. Abre un Pull Request con el comando `/pr-review` antes de solicitar revisión.
