#!/usr/bin/env bash
# Hook de Claude Code — se ejecuta DESPUÉS de cada llamada a una herramienta.
#
# Entrada (stdin): JSON con { tool_name, tool_input, tool_response }
# Salida:
#   exit 0 → sin efecto sobre Claude
#   exit 1 → Claude ve el mensaje de stderr como feedback adicional

INPUT=$(cat)
TOOL=$(echo "$INPUT"     | jq -r '.tool_name              // empty')
FILE=$(echo "$INPUT"     | jq -r '.tool_input.file_path   // empty')
COMMAND=$(echo "$INPUT"  | jq -r '.tool_input.command     // empty')
EXIT_CODE=$(echo "$INPUT"| jq -r '.tool_response.exitCode // empty')

# ─── 1. GUARDIÁN DE ARQUITECTURA (tras Write o Edit) ─────────────────────────

if [ "$TOOL" = "Write" ] || [ "$TOOL" = "Edit" ]; then

  # Detectar imports de Spring/JPA dentro del paquete domain/
  if echo "$FILE" | grep -q "/domain/" && [[ "$FILE" == *.java ]]; then
    if grep -qE "^import org\.springframework\.|^import (javax|jakarta)\.persistence\." "$FILE" 2>/dev/null; then
      echo "" >&2
      echo "[PostToolUse] ⚠️  VIOLACIÓN DE ARQUITECTURA detectada en:" >&2
      echo "  $FILE" >&2
      echo "" >&2
      echo "  El paquete domain/ no debe depender de Spring ni de JPA." >&2
      echo "  Imports problemáticos encontrados:" >&2
      grep -nE "^import org\.springframework\.|^import (javax|jakarta)\.persistence\." "$FILE" >&2
      echo "" >&2
      echo "  Solución: mueve la clase a infrastructure/ o elimina el import." >&2
    fi
  fi

  # Detectar entidades JPA expuestas directamente en controllers
  if echo "$FILE" | grep -q "/web/" && [[ "$FILE" == *.java ]]; then
    if grep -qE "JpaEntity|@Entity" "$FILE" 2>/dev/null; then
      echo "" >&2
      echo "[PostToolUse] ⚠️  ENTIDAD JPA en capa web detectada en:" >&2
      echo "  $FILE" >&2
      echo "  Las entidades JPA no deben llegar al controller — usa DTOs." >&2
    fi
  fi

  # Detectar nuevos archivos de migración Flyway sin índices
  if echo "$FILE" | grep -qE "db/migration/.*\.sql"; then
    if ! grep -qiE "CREATE INDEX|CREATE UNIQUE INDEX" "$FILE" 2>/dev/null; then
      echo "" >&2
      echo "[PostToolUse] 💡 SUGERENCIA: la migración no define índices:" >&2
      echo "  $FILE" >&2
      echo "  Si la tabla tiene columnas de filtrado/join, considera agregar índices." >&2
    fi
  fi

fi

# ─── 2. FEEDBACK TRAS EJECUCIÓN DE MAVEN ─────────────────────────────────────

if [ "$TOOL" = "Bash" ]; then

  # Si mvnw verify falló, resaltar el error principal
  if echo "$COMMAND" | grep -qE "mvnw? verify|mvnw? test"; then
    if [ "$EXIT_CODE" != "0" ] && [ -n "$EXIT_CODE" ]; then
      echo "" >&2
      echo "[PostToolUse] ❌ Maven falló. Revisa los errores antes de continuar." >&2
      # Buscar el BUILD FAILURE en el output del proceso (ya visible en la respuesta)
    fi
  fi

  # Si se hizo commit, recordar hacer push si el branch tiene upstream
  if echo "$COMMAND" | grep -qE "^git commit"; then
    if [ "$EXIT_CODE" = "0" ]; then
      BRANCH=$(git branch --show-current 2>/dev/null)
      if git rev-parse --abbrev-ref "@{upstream}" &>/dev/null; then
        AHEAD=$(git rev-list --count "@{upstream}..HEAD" 2>/dev/null || echo 0)
        if [ "$AHEAD" -gt 0 ]; then
          echo "" >&2
          echo "[PostToolUse] 📌 Tienes $AHEAD commit(s) por encima del upstream en '$BRANCH'." >&2
          echo "  Recuerda hacer push cuando el cambio esté listo." >&2
        fi
      fi
    fi
  fi

fi

# ─── 3. LOG DE AUDITORÍA ─────────────────────────────────────────────────────

LOG_DIR="${HOME}/.claude/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/tool-audit-$(date +%Y-%m-%d).log"

{
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | TOOL=$TOOL | EXIT=$EXIT_CODE"
  [ -n "$FILE" ]    && echo "  file:    $FILE"
  [ -n "$COMMAND" ] && echo "  command: ${COMMAND:0:120}"  # truncar a 120 chars
  echo ""
} >> "$LOG_FILE"

exit 0
