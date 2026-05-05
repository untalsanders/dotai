---
name: pr-review
description: Revisa el PR activo contra las reglas de arquitectura, API, base de datos y seguridad. Genera un reporte estructurado.
argument-hint: [pr-number] (opcional, usa el PR del branch actual si se omite)
---

Revisa el Pull Request $ARGUMENTS (o el PR del branch actual si no se indica número).

## 1. Leer el PR

```bash
gh pr view $ARGUMENTS --comments
gh pr diff $ARGUMENTS
```

Lee la descripción completa. Si el PR no tiene descripción, anótalo como **WARNING** — un PR sin contexto es imposible de revisar correctamente.

## 2. Inventario de cambios

Agrupa los archivos modificados por capa:

```bash
gh pr diff $ARGUMENTS --name-only
```

Identifica qué capas toca el PR:
- `domain/` → cambios en modelo de negocio
- `application/` → cambios en casos de uso
- `infrastructure/web/` → cambios en API
- `infrastructure/persistence/` → cambios en persistencia o schema
- `infrastructure/config/` → cambios de configuración
- `src/test/` → cambios en tests

## 3. Revisión por capa

### Arquitectura

- [ ] ¿El `domain` importa clases de `infrastructure` o de `application`? → **BLOQUEANTE**
- [ ] ¿Hay lógica de negocio en controllers o en entidades JPA? → **BLOQUEANTE**
- [ ] ¿Los nuevos casos de uso implementan un puerto de entrada (`port/in`)? → **WARNING** si no
- [ ] ¿Los nuevos repositorios implementan un puerto de salida (`port/out`)? → **WARNING** si no
- [ ] ¿Se usa `@Autowired` en campo en lugar de inyección por constructor? → **WARNING**

### API REST (si hay cambios en `infrastructure/web/`)

- [ ] ¿Los endpoints nuevos siguen el patrón `/api/v{n}/recursos`?
- [ ] ¿Se usa el envelope `{ data, error, meta }` en todas las respuestas?
- [ ] ¿Las colecciones devuelven `Page<T>` con `Pageable`? ¿O devuelven listas sin límite? → **BLOQUEANTE** si sin límite
- [ ] ¿Todos los request bodies tienen `@Valid` y las anotaciones de Bean Validation?
- [ ] ¿Los errores se manejan en `@RestControllerAdvice`? ¿O hay try/catch en el controller? → **WARNING**
- [ ] ¿Se usan los códigos de estado HTTP correctos?
- [ ] ¿Los DTOs son `record`? ¿O clases mutables sin necesidad?
- [ ] ¿Se expone alguna entidad JPA directamente en la respuesta? → **BLOQUEANTE**

### Base de datos (si hay cambios en `infrastructure/persistence/` o en `db/migration/`)

- [ ] ¿Hay migración Flyway para cada cambio de schema? → **BLOQUEANTE** si falta
- [ ] ¿La migración sigue el formato `V{version}__{descripcion}.sql`?
- [ ] ¿La migración define índices explícitamente para las columnas que se filtran o se unen?
- [ ] ¿Hay alguna relación con `FetchType.EAGER`? → **WARNING**
- [ ] ¿Hay queries dentro de bucles que pueden causar N+1? → **WARNING**
- [ ] ¿`@Transactional` está en el caso de uso, no en el controller ni en el repositorio?
- [ ] ¿Se usa `spring.jpa.hibernate.ddl-auto=update`? → **BLOQUEANTE**

### Seguridad

- [ ] ¿Hay alguna credencial, token, clave o secret hardcodeado? → **BLOQUEANTE**
- [ ] ¿Hay concatenación de strings para construir queries SQL? → **BLOQUEANTE**
- [ ] ¿Los endpoints nuevos tienen `@PreAuthorize` o están protegidos en `SecurityConfig`?
- [ ] ¿Se valida la entrada en todos los endpoints públicos?
- [ ] ¿Los stacktraces pueden llegar a la respuesta HTTP en producción? → **WARNING**
- [ ] ¿Se usa `allowedOrigins("*")` en la configuración de CORS? → **BLOQUEANTE**

### Calidad de código

- [ ] ¿Hay métodos de más de 20 líneas? ¿Se puede extraer responsabilidades?
- [ ] ¿Hay comentarios que explican *qué* hace el código en lugar del *por qué*?
- [ ] ¿Hay bloques `catch` vacíos o que solo loguean sin relanzar? → **WARNING**
- [ ] ¿Se usa `System.out.println` en lugar del logger? → **WARNING**
- [ ] ¿Hay código comentado o imports sin usar? → **WARNING**

### Tests

- [ ] ¿Cada nuevo caso de uso tiene tests unitarios?
- [ ] ¿Cada nuevo endpoint tiene tests con `@WebMvcTest`?
- [ ] ¿Cada cambio de persistencia tiene tests con `@DataJpaTest` + Testcontainers?
- [ ] ¿Los tests siguen el patrón `should_[resultado]_when_[condicion]`?
- [ ] ¿Los tests verifican una sola cosa? ¿O hay asserts mezclados de múltiples conceptos?
- [ ] ¿Se mockea la base de datos con H2 en tests de repositorio? → **WARNING** (usar Testcontainers)

## 4. Ejecutar los tests localmente

```bash
gh pr checkout $ARGUMENTS
./mvnw verify -q
```

Si los tests fallan, anótalo como **BLOQUEANTE** con el output del fallo.

## 5. Generar el reporte de revisión

Produce el reporte en este formato:

---

### Revisión PR #$ARGUMENTS — `<título del PR>`

**Veredicto:** APROBADO / APROBADO CON SUGERENCIAS / CAMBIOS REQUERIDOS

---

#### BLOQUEANTES (deben resolverse antes del merge)

- [ ] `archivo:línea` — Descripción del problema y cómo corregirlo.

#### WARNINGS (importantes pero no bloquean el merge)

- [ ] `archivo:línea` — Descripción y sugerencia de mejora.

#### SUGERENCIAS (opcionales, para consideración futura)

- `archivo:línea` — Descripción.

#### Puntos positivos

- Qué está bien hecho y merece reconocimiento.

---

Publica el reporte como comentario en el PR:

```bash
gh pr review $ARGUMENTS --comment --body "<reporte generado>"
```

Si hay BLOQUEANTES, solicita cambios en lugar de solo comentar:

```bash
gh pr review $ARGUMENTS --request-changes --body "<reporte generado>"
```
