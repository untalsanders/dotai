# Plantilla para crear nuevas Skills

Las skills son instrucciones reutilizables que Claude ejecuta cuando se invoca `/nombre-skill`. Cada skill vive en su propia subcarpeta dentro de `.claude/skills/` y se define en un archivo `SKILL.md`.

---

## Estructura mínima de una skill

```markdown
---
name: nombre-skill
description: Una línea que describe qué hace esta skill y cuándo invocarla.
argument-hint: <argumento-requerido> [argumento-opcional]
---

Instrucciones que Claude seguirá al invocar esta skill.

Usa $ARGUMENTS para referirte al argumento pasado por el usuario.
```

---

## Campos del frontmatter

| Campo | Requerido | Descripción |
|---|---|---|
| `name` | Sí | Nombre del slash command (`/nombre-skill`) |
| `description` | Sí | Descripción corta para el autocompletado en Claude Code |
| `argument-hint` | No | Muestra al usuario qué argumentos acepta la skill |

---

## Cómo estructurar las instrucciones

Una buena skill tiene tres partes:

### 1. Contexto (qué debe entender Claude antes de actuar)
Dile qué leer, qué preguntar al usuario y qué asumir si no hay argumentos.

### 2. Pasos (qué debe hacer y en qué orden)
Pasos numerados, claros y accionables. Cada paso debe producir un resultado verificable.

### 3. Criterios de éxito (cómo sabe Claude que terminó bien)
Lista de condiciones que deben cumplirse antes de declarar la tarea completa.

---

## Ejemplo completo

```markdown
---
name: add-endpoint
description: Implementa un nuevo endpoint REST siguiendo la arquitectura hexagonal del proyecto.
argument-hint: <descripcion-del-endpoint>
---

Implementa el endpoint: $ARGUMENTS

## Antes de empezar

Lee los archivos de contexto:
- `.claude/skills/context.md` — convenciones y estructura del proyecto
- `.claude/rules/api.md` — reglas de diseño REST
- `.claude/rules/architecture.md` — reglas de arquitectura hexagonal

## Pasos

1. Diseña el recurso: URL, método HTTP, request body, response body.
2. Crea el DTO de request con Bean Validation.
3. Crea el DTO de response como `record`.
4. Define el puerto de entrada en `domain/port/in/`.
5. Implementa el caso de uso en `application/usecase/`.
6. Crea el controller en `infrastructure/web/`.
7. Escribe el test con `@WebMvcTest`.

## Criterios de éxito

- [ ] `./mvnw verify` pasa en verde.
- [ ] El endpoint está documentado en OpenAPI.
- [ ] El response sigue el envelope `{ data, error, meta }`.
```

---

## Convenciones

- Nombre de la carpeta = nombre del slash command (kebab-case).
- Si la skill necesita contexto del proyecto, referencia `context.md` explícitamente en las instrucciones.
- Prefiere pasos pequeños y verificables sobre instrucciones largas y ambiguas.
- Escribe las instrucciones como si las leyera alguien que no conoce el proyecto — porque la skill puede invocarse en cualquier contexto.
