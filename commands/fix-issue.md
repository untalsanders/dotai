---
name: fix-issue
description: Lee un issue de GitHub, implementa el fix mínimo, escribe el test de regresión y abre el PR.
argument-hint: <issue-number>
---

Resuelve el issue de GitHub #$ARGUMENTS siguiendo estos pasos en orden:

## 1. Leer y entender el issue

```bash
gh issue view $ARGUMENTS
```

Antes de tocar código, asegúrate de entender:
- ¿Cuál es el comportamiento actual vs. el esperado?
- ¿Hay pasos de reproducción? Síguelos para confirmar el bug.
- ¿Hay comentarios en el issue con contexto adicional?

## 2. Localizar el código relevante

Busca los archivos afectados. Empieza por los más probables según el tipo de issue:

- Bug en lógica de negocio → `domain/model/` y `application/usecase/`
- Bug en endpoint o respuesta → `infrastructure/web/`
- Bug en queries o persistencia → `infrastructure/persistence/`
- Bug de configuración → `infrastructure/config/`

Lee los archivos relevantes completos antes de modificar nada. Entiende el flujo de punta a punta.

## 3. Reproducir el bug en un test (primero)

Escribe el test que falla **antes** de implementar el fix. Esto confirma que entiendes el problema y que el test es útil:

```bash
./mvnw test -pl <modulo> -Dtest=<NombreTest>#should_fail_when_... -q
```

El test debe fallar por la razón correcta, no por otro motivo.

## 4. Implementar el fix mínimo

Aplica el cambio más pequeño posible que resuelva el problema. No aproveches para refactorizar o limpiar código no relacionado — eso va en un PR separado.

Verifica que respetas las reglas de arquitectura:
- La lógica de negocio vive en `domain`, no en controllers ni en entidades JPA.
- Si el fix requiere un nuevo campo en BD, crea la migración Flyway correspondiente (`V{version}__{descripcion}.sql`).
- Si el fix cambia un contrato de API, actualiza la documentación OpenAPI.

## 5. Verificar que el test ahora pasa

```bash
./mvnw test -pl <modulo> -Dtest=<NombreTest> -q
```

## 6. Ejecutar la suite completa

```bash
./mvnw verify -q
```

Todos los tests deben pasar. Si algún test ajeno al fix falla, investiga antes de continuar — no silencies el fallo.

## 7. Commit con Conventional Commits

```bash
git add <archivos-modificados>
git commit -m "fix: <descripcion-concisa> (closes #$ARGUMENTS)"
```

El mensaje debe describir el *qué se corrigió*, no el *cómo*. Ejemplo:
```
fix: order total not recalculated when item quantity changes (closes #$ARGUMENTS)
```

Si el fix incluye una migración de BD, añade un cuerpo al commit:
```
fix: order total not recalculated when item quantity changes (closes #$ARGUMENTS)

Adds missing recalculation trigger in Order.updateItem().
Migration V1.2.3__add_order_total_index.sql included.
```

## 8. Push y abrir el PR

```bash
git push -u origin fix/issue-$ARGUMENTS-<descripcion-corta>
gh pr create \
  --title "fix: <descripcion> (closes #$ARGUMENTS)" \
  --body "## Problema
<Descripcion del bug según el issue>

## Causa raíz
<Donde estaba el fallo en el código>

## Solución
<Cambio implementado y por qué es correcto>

## Cómo probar
- [ ] <Paso 1>
- [ ] <Paso 2>

## Checklist
- [ ] Test de regresión incluido
- [ ] \`./mvnw verify\` pasa en verde
- [ ] Sin cambios de scope fuera del issue
$([ -f src/main/resources/db/migration/*.sql ] && echo '- [ ] Migración Flyway incluida')
Closes #$ARGUMENTS" \
  --assignee @me
```
