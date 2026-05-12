#!/usr/bin/env bash
# Git pre-commit hook — se ejecuta antes de CADA commit.
#
# Si cualquier verificación falla, el commit es BLOQUEADO (exit != 0).
# Instalar: ln -s ../../.claude/hooks/pre-commit.sh .git/hooks/pre-commit
#
# Para saltar en casos excepcionales (no recomendado):
#   git commit --no-verify -m "mensaje"

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info()  { echo -e "  ${GREEN}✔${NC}  $*"; }
log_warn()  { echo -e "  ${YELLOW}⚠${NC}  $*"; }
log_error() { echo -e "  ${RED}✘${NC}  $*" >&2; }

echo ""
echo "┌─ Pre-commit checks ─────────────────────────────────────────┐"

STAGED_JAVA=$(git diff --cached --name-only | grep -E "\.java$" || true)
STAGED_SQL=$(git diff --cached --name-only  | grep -E "\.sql$"  || true)
STAGED_YML=$(git diff --cached --name-only  | grep -E "\.(yml|yaml|properties)$" || true)
FAILED=0

# ─── 1. SECRETS EN ARCHIVOS STAGED ────────────────────────────────────────────

echo "│"
echo "│  [1/5] Escaneo de secrets"

SECRET_PATTERN='(password|passwd|secret|api_key|apikey|private_key|token)\s*[:=]\s*["\x27][^"\x27${}]{6,}'
if git diff --cached -U0 | grep -iEq "$SECRET_PATTERN"; then
  log_error "Posible secret hardcodeado detectado en el diff:"
  git diff --cached -U0 | grep -iE "$SECRET_PATTERN" | head -5 | sed 's/^/     /'
  echo "│"
  echo "│  Usa variables de entorno o un gestor de secretos (Vault, AWS SM)."
  FAILED=1
else
  log_info "Sin secrets detectados"
fi

# ─── 2. VIOLACIONES DE ARQUITECTURA ───────────────────────────────────────────

echo "│"
echo "│  [2/5] Revisión de arquitectura hexagonal"

ARCH_FAIL=0
for FILE in $STAGED_JAVA; do
  if echo "$FILE" | grep -q "/domain/" && [ -f "$FILE" ]; then
    if grep -qE "^import org\.springframework\.|^import (javax|jakarta)\.persistence\." "$FILE"; then
      log_error "Import prohibido en domain/: $FILE"
      grep -nE "^import org\.springframework\.|^import (javax|jakarta)\.persistence\." "$FILE" | sed 's/^/     /'
      ARCH_FAIL=1
    fi
  fi
done

if [ "$ARCH_FAIL" -eq 0 ]; then
  log_info "Sin violaciones de arquitectura"
else
  FAILED=1
fi

# ─── 3. CONVENCIÓN DE MIGRACIONES FLYWAY ──────────────────────────────────────

echo "│"
echo "│  [3/5] Convención de migraciones Flyway"

MIGRATION_FAIL=0
for FILE in $STAGED_SQL; do
  BASENAME=$(basename "$FILE")
  # Formato esperado: V{major}.{minor}.{patch}__{descripcion_snake_case}.sql
  if echo "$FILE" | grep -q "db/migration"; then
    if ! echo "$BASENAME" | grep -qE "^V[0-9]+\.[0-9]+\.[0-9]+__[a-z0-9_]+\.sql$"; then
      log_error "Nombre de migración inválido: $BASENAME"
      log_warn  "Formato esperado: V1.2.3__descripcion_en_snake_case.sql"
      MIGRATION_FAIL=1
    fi
  fi
done

if [ "$MIGRATION_FAIL" -eq 0 ]; then
  if [ -n "$STAGED_SQL" ]; then
    log_info "Convención de migraciones correcta"
  else
    log_info "Sin migraciones en este commit"
  fi
else
  FAILED=1
fi

# ─── 4. COMPILACIÓN ───────────────────────────────────────────────────────────

echo "│"
echo "│  [4/5] Compilación (./mvnw compile)"

if [ -n "$STAGED_JAVA" ]; then
  if ! ./mvnw compile -q 2>/tmp/mvn-compile-err; then
    log_error "La compilación falló:"
    grep -E "ERROR|error:" /tmp/mvn-compile-err | head -10 | sed 's/^/     /'
    FAILED=1
  else
    log_info "Compilación exitosa"
  fi
else
  log_info "Sin archivos Java staged — compilación omitida"
fi

# ─── 5. TESTS UNITARIOS ───────────────────────────────────────────────────────

echo "│"
echo "│  [5/5] Tests unitarios (./mvnw test)"

if [ -n "$STAGED_JAVA" ]; then
  if ! ./mvnw test -q 2>/tmp/mvn-test-err; then
    log_error "Tests fallidos:"
    grep -E "FAIL|ERROR|Tests run" /tmp/mvn-test-err | grep -v "Tests run: 0" | head -10 | sed 's/^/     /'
    echo "│"
    echo "│  Ejecuta './mvnw test' para ver el detalle completo."
    FAILED=1
  else
    TEST_COUNT=$(grep -oE "Tests run: [0-9]+" /tmp/mvn-test-err 2>/dev/null | awk -F': ' '{sum+=$2} END{print sum}' || echo "?")
    log_info "Tests en verde ($TEST_COUNT tests)"
  fi
else
  log_info "Sin archivos Java staged — tests omitidos"
fi

# ─── RESULTADO FINAL ──────────────────────────────────────────────────────────

echo "│"
if [ "$FAILED" -eq 0 ]; then
  echo "│  ✔  Todos los checks pasaron — commit autorizado."
  echo "└──────────────────────────────────────────────────────────────┘"
  echo ""
  exit 0
else
  echo "│  ✘  Checks fallidos — commit BLOQUEADO."
  echo "│"
  echo "│  Corrige los errores y vuelve a intentar."
  echo "│  Para omitir (no recomendado): git commit --no-verify"
  echo "└──────────────────────────────────────────────────────────────┘"
  echo ""
  exit 1
fi
