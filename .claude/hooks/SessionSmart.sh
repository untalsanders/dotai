#!/usr/bin/env bash
# Hook de Claude Code — se ejecuta al INICIAR y al FINALIZAR una sesión.
#
# Entrada (stdin): JSON con { event: "session_start" | "session_end", session_id, ... }
# Salida: texto en stdout que Claude recibe como contexto adicional (en session_start)
#         o como resumen visible al usuario (en session_end)

INPUT=$(cat)
EVENT=$(echo "$INPUT" | jq -r '.event // "session_start"')

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
MEMORY_DIR="${HOME}/.claude/projects/$(echo "$PROJECT_ROOT" | tr '/' '-')/memory"
SESSION_LOG="$MEMORY_DIR/session-$(date +%Y-%m-%d).md"
mkdir -p "$MEMORY_DIR"

# ─── SESSION START ────────────────────────────────────────────────────────────

if [ "$EVENT" = "session_start" ]; then

  echo "## Contexto de sesión — $(date '+%Y-%m-%d %H:%M')"
  echo ""

  # Estado del repositorio
  echo "### Git"
  BRANCH=$(git -C "$PROJECT_ROOT" branch --show-current 2>/dev/null)
  echo "- Branch actual: \`$BRANCH\`"

  DIRTY=$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  if [ "$DIRTY" -gt 0 ]; then
    echo "- Archivos modificados sin commitear: $DIRTY"
    git -C "$PROJECT_ROOT" status --short 2>/dev/null | head -10 | sed 's/^/  /'
  else
    echo "- Working tree limpio"
  fi

  AHEAD=$(git -C "$PROJECT_ROOT" rev-list --count "@{upstream}..HEAD" 2>/dev/null || echo 0)
  if [ "$AHEAD" -gt 0 ]; then
    echo "- Commits pendientes de push: $AHEAD"
  fi

  echo ""

  # Últimos commits para dar contexto de qué se estaba trabajando
  echo "### Últimos commits"
  git -C "$PROJECT_ROOT" log --oneline -5 2>/dev/null | sed 's/^/- /'
  echo ""

  # Migraciones Flyway pendientes
  PENDING_MIGRATIONS=$(find "$PROJECT_ROOT/src/main/resources/db/migration" -name "*.sql" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$PENDING_MIGRATIONS" -gt 0 ]; then
    LATEST_MIGRATION=$(find "$PROJECT_ROOT/src/main/resources/db/migration" -name "*.sql" 2>/dev/null | sort | tail -1 | xargs basename 2>/dev/null)
    echo "### Base de datos"
    echo "- Migraciones totales: $PENDING_MIGRATIONS"
    echo "- Última migración: \`$LATEST_MIGRATION\`"
    echo ""
  fi

  # Tests que fallaron en la última ejecución (si hay un surefire-reports)
  FAILED_TESTS=$(find "$PROJECT_ROOT/target/surefire-reports" -name "*.xml" 2>/dev/null \
    | xargs grep -l 'failures="[^0]"\|errors="[^0]"' 2>/dev/null | wc -l | tr -d ' ')
  if [ "$FAILED_TESTS" -gt 0 ]; then
    echo "### ⚠️  Tests fallidos en la última ejecución: $FAILED_TESTS archivos"
    find "$PROJECT_ROOT/target/surefire-reports" -name "*.xml" 2>/dev/null \
      | xargs grep -l 'failures="[^0]"\|errors="[^0]"' 2>/dev/null \
      | xargs basename -s .xml 2>/dev/null | head -5 | sed 's/^/- /'
    echo ""
  fi

  # Leer notas de sesiones anteriores si existen
  if ls "$MEMORY_DIR/session-"*.md &>/dev/null 2>&1; then
    LAST_SESSION=$(ls "$MEMORY_DIR/session-"*.md 2>/dev/null | sort | tail -2 | head -1)
    if [ -n "$LAST_SESSION" ] && [ "$LAST_SESSION" != "$SESSION_LOG" ]; then
      echo "### Notas de la sesión anterior"
      tail -20 "$LAST_SESSION" 2>/dev/null | sed 's/^/> /'
      echo ""
    fi
  fi

  # Inicializar el log de la sesión actual
  {
    echo "# Sesión — $(date '+%Y-%m-%d %H:%M')"
    echo "Branch: $BRANCH"
    echo ""
  } >> "$SESSION_LOG"

fi

# ─── SESSION END ──────────────────────────────────────────────────────────────

if [ "$EVENT" = "session_end" ]; then

  echo ""
  echo "## Resumen de sesión — $(date '+%Y-%m-%d %H:%M')"
  echo ""

  # Archivos modificados durante la sesión
  CHANGED=$(git -C "$PROJECT_ROOT" diff --name-only HEAD 2>/dev/null | wc -l | tr -d ' ')
  STAGED=$(git -C "$PROJECT_ROOT" diff --name-only --cached 2>/dev/null | wc -l | tr -d ' ')
  UNTRACKED=$(git -C "$PROJECT_ROOT" ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')

  echo "### Cambios en el repositorio"
  echo "- Archivos modificados: $CHANGED"
  echo "- Archivos en staging:  $STAGED"
  echo "- Archivos nuevos:      $UNTRACKED"
  echo ""

  if [ "$CHANGED" -gt 0 ] || [ "$STAGED" -gt 0 ]; then
    echo "Archivos tocados:"
    { git -C "$PROJECT_ROOT" diff --name-only HEAD 2>/dev/null
      git -C "$PROJECT_ROOT" diff --name-only --cached 2>/dev/null; } \
      | sort -u | head -15 | sed 's/^/- /'
    echo ""
  fi

  # Commits realizados en esta sesión (aproximado: última hora)
  NEW_COMMITS=$(git -C "$PROJECT_ROOT" log --oneline --since="1 hour ago" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$NEW_COMMITS" -gt 0 ]; then
    echo "### Commits realizados"
    git -C "$PROJECT_ROOT" log --oneline --since="1 hour ago" 2>/dev/null | sed 's/^/- /'
    echo ""
  fi

  # Guardar resumen en el log de memoria
  {
    echo ""
    echo "## Fin de sesión — $(date '+%Y-%m-%d %H:%M')"
    echo "- Archivos modificados: $CHANGED | Staged: $STAGED | Nuevos: $UNTRACKED"
    echo "- Commits: $NEW_COMMITS"
    if [ "$CHANGED" -gt 0 ]; then
      echo "Archivos:"
      git -C "$PROJECT_ROOT" diff --name-only HEAD 2>/dev/null | head -10 | sed 's/^/  - /'
    fi
  } >> "$SESSION_LOG"

  echo "Log guardado en: $SESSION_LOG"

fi

exit 0
