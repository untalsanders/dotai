#!/usr/bin/env bash
# Hook de Claude Code — se ejecuta ANTES de cada llamada a una herramienta.
#
# Entrada (stdin): JSON con { tool_name, tool_input }
# Salida:
#   exit 0 → Claude procede normalmente
#   exit 1 → Claude ve el mensaje de stderr y puede decidir
#   exit 2 → Acción BLOQUEADA, Claude no puede continuar

INPUT=$(cat)
TOOL=$(echo "$INPUT"    | jq -r '.tool_name           // empty')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command  // empty')
FILE=$(echo "$INPUT"    | jq -r '.tool_input.file_path // empty')

# ─── 1. GUARDIANES DE BASH ───────────────────────────────────────────────────

if [ "$TOOL" = "Bash" ]; then

  # Bloquear rm -rf sobre rutas críticas
  if echo "$COMMAND" | grep -qE "rm\s+-[a-z]*r[a-z]*f|rm\s+-[a-z]*f[a-z]*r"; then
    if echo "$COMMAND" | grep -qE "(src|target|/home|~|\.\.)"; then
      echo "[PreToolUse] BLOQUEADO: rm -rf sobre directorio crítico detectado." >&2
      echo "  Comando: $COMMAND" >&2
      exit 2
    fi
  fi

  # Bloquear force push a main/master
  if echo "$COMMAND" | grep -qE "git push.*(--force|-f).*(main|master)|git push.*(main|master).*(--force|-f)"; then
    echo "[PreToolUse] BLOQUEADO: force push a main/master no está permitido." >&2
    exit 2
  fi

  # Bloquear reset --hard sin confirmación previa (destructivo e irreversible)
  if echo "$COMMAND" | grep -qE "git reset --hard"; then
    echo "[PreToolUse] BLOQUEADO: git reset --hard puede destruir trabajo no commiteado." >&2
    echo "  Si es intencional, ejecuta el comando manualmente en la terminal." >&2
    exit 2
  fi

  # Advertir sobre DROP TABLE / DROP DATABASE (no bloquear — puede ser intencional en scripts)
  if echo "$COMMAND" | grep -qiE "\bDROP\s+(TABLE|DATABASE|SCHEMA)\b"; then
    echo "[PreToolUse] ADVERTENCIA: sentencia SQL destructiva detectada: $COMMAND" >&2
    echo "  Verifica que esto es intencional antes de ejecutar." >&2
    exit 1
  fi

  # Bloquear ejecución de la app en puerto 8080 si ya hay algo escuchando
  if echo "$COMMAND" | grep -qE "spring-boot:run|java -jar"; then
    if lsof -i :8080 -sTCP:LISTEN -t &>/dev/null; then
      echo "[PreToolUse] ADVERTENCIA: el puerto 8080 ya está en uso." >&2
      echo "  Detén el proceso existente antes de levantar la aplicación." >&2
      exit 1
    fi
  fi

fi

# ─── 2. GUARDIANES DE ESCRITURA ──────────────────────────────────────────────

if [ "$TOOL" = "Write" ] || [ "$TOOL" = "Edit" ]; then

  # Advertir si se va a sobreescribir una migración Flyway ya existente
  if echo "$FILE" | grep -qE "db/migration/V[0-9]"; then
    if [ -f "$FILE" ]; then
      echo "[PreToolUse] ADVERTENCIA: estás modificando una migración Flyway existente." >&2
      echo "  Archivo: $FILE" >&2
      echo "  Las migraciones aplicadas NO deben modificarse — crea una nueva versión." >&2
      exit 1
    fi
  fi

  # Advertir si se escribe en SecurityConfig (cambios con alto impacto)
  if echo "$FILE" | grep -qiE "SecurityConfig|WebSecurityConfig"; then
    echo "[PreToolUse] ADVERTENCIA: estás modificando la configuración de seguridad." >&2
    echo "  Archivo: $FILE" >&2
    echo "  Asegúrate de que los tests de seguridad cubren el cambio." >&2
    # No bloquear — solo advertir
  fi

fi

exit 0
