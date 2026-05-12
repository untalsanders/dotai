---
name: backend
description: Implementa una nueva feature de backend en Spring Boot siguiendo la arquitectura hexagonal. Cubre dominio, caso de uso, persistencia, endpoint REST y tests.
argument-hint: <descripcion-de-la-feature>
---

Implementa la siguiente feature de backend: **$ARGUMENTS**

Antes de escribir una sola línea de código, lee:
- `.claude/skills/context.md` — convenciones, estructura y comandos del proyecto
- `.claude/rules/architecture.md` — reglas de arquitectura hexagonal
- `.claude/rules/api.md` — reglas de diseño REST
- `.claude/rules/database.md` — reglas de persistencia

---

## Fase 1 — Entender antes de implementar

### 1.1 Explorar el estado actual

```bash
# Ver los casos de uso existentes para no duplicar
find src/main/java -path "*/domain/port/in/*.java" | sort

# Ver los endpoints existentes para respetar la estructura
find src/main/java -path "*/infrastructure/web/*Controller.java" | sort

# Ver la versión actual del schema
ls src/main/resources/db/migration/ | sort
```

### 1.2 Hacerse estas preguntas antes de diseñar

- ¿Qué entidades de dominio están involucradas? ¿Ya existen o hay que crearlas?
- ¿Qué invariantes de negocio debe garantizar esta feature? (condiciones que deben ser siempre verdaderas)
- ¿Qué cambia en la base de datos? (columnas nuevas, tablas, índices)
- ¿Cuál es el endpoint que expone esta feature? ¿Existe ya uno relacionado?
- ¿Quién puede ejecutar esta acción? (autenticación / autorización)

---

## Fase 2 — Modelar el dominio

### 2.1 Value Objects (si aplica)

Crea los Value Objects para los conceptos que tienen validación propia. Usa `record` de Java 21:

```java
// domain/model/
public record <NombreVO>(<Tipo> value) {
    public <NombreVO> {
        // Validaciones de invariante aquí
        Objects.requireNonNull(value, "<campo> cannot be null");
        if (<condicion_invalida>) throw new <NombreDomainException>("<mensaje>");
    }
}
```

### 2.2 Entidad / Aggregate Root

```java
// domain/model/
public class <NombreEntidad> {
    private final <NombreId> id;
    // ... campos
    private final List<DomainEvent> domainEvents = new ArrayList<>();

    // Constructor privado — usa factory method
    private <NombreEntidad>(...) { ... }

    // Factory method con nombre expresivo del dominio
    public static <NombreEntidad> <verboDeNegocio>(...) {
        var entity = new <NombreEntidad>(...);
        entity.domainEvents.add(new <Nombre>Event(entity.id));
        return entity;
    }

    // Comportamiento de dominio — no getters/setters ciegos
    public void <accionDeNegocio>(...) {
        // Validar invariantes antes de cambiar estado
        // Registrar evento si aplica
    }

    public List<DomainEvent> pullDomainEvents() {
        var events = List.copyOf(domainEvents);
        domainEvents.clear();
        return events;
    }
}
```

### 2.3 Excepciones de dominio

```java
// domain/exception/
public class <Nombre>NotFoundException extends RuntimeException {
    public <Nombre>NotFoundException(<NombreId> id) {
        super("<Nombre> with id '%s' not found".formatted(id.value()));
    }
}
```

### 2.4 Puertos

```java
// domain/port/in/  — interfaz del caso de uso
public interface <Verbo><Sustantivo>UseCase {
    <TipoRetorno> execute(<Verbo><Sustantivo>Command command);
}

// domain/port/out/ — interfaz del repositorio
public interface <Sustantivo>Repository {
    void save(<NombreEntidad> entity);
    Optional<<NombreEntidad>> findById(<NombreId> id);
}
```

---

## Fase 3 — Implementar el caso de uso

```java
// application/usecase/
@Service
@Transactional
@RequiredArgsConstructor
public class <Verbo><Sustantivo>Service implements <Verbo><Sustantivo>UseCase {

    private final <Sustantivo>Repository repository;
    // otros puertos de salida que necesite

    @Override
    public <TipoRetorno> execute(<Verbo><Sustantivo>Command command) {
        // 1. Cargar entidades necesarias (fallar rápido si no existen)
        // 2. Ejecutar la lógica de dominio
        // 3. Persistir
        // 4. Publicar eventos si aplica
        // 5. Retornar resultado
    }
}
```

---

## Fase 4 — Implementar el adapter de persistencia

### 4.1 Entidad JPA (separada de la entidad de dominio)

```java
// infrastructure/persistence/
@Entity
@Table(name = "<nombre_tabla>", indexes = {
    @Index(name = "idx_<tabla>_<campo>", columnList = "<campo>")
})
public class <Nombre>JpaEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    // Todos los @Column con nullable, length, updatable explícitos
    // Sin lógica de negocio
}
```

### 4.2 Spring Data Repository

```java
// infrastructure/persistence/
public interface <Nombre>JpaRepository extends JpaRepository<<Nombre>JpaEntity, UUID> {
    // Solo derived queries o @Query — sin lógica en el cuerpo
}
```

### 4.3 Adapter que implementa el puerto de salida

```java
// infrastructure/persistence/
@Repository
@RequiredArgsConstructor
public class <Nombre>RepositoryAdapter implements <Nombre>Repository {

    private final <Nombre>JpaRepository jpaRepository;
    private final <Nombre>PersistenceMapper mapper;

    @Override
    public void save(<NombreEntidad> entity) {
        jpaRepository.save(mapper.toJpaEntity(entity));
    }

    @Override
    public Optional<<NombreEntidad>> findById(<NombreId> id) {
        return jpaRepository.findById(id.value()).map(mapper::toDomain);
    }
}
```

### 4.4 Migración Flyway

Si hay cambios en el schema, crea la migración. Nunca uses `ddl-auto=update`:

```sql
-- src/main/resources/db/migration/V{siguiente_version}__{descripcion}.sql
CREATE TABLE <nombre_tabla> (
    id          UUID        NOT NULL DEFAULT gen_random_uuid(),
    -- campos con tipos PostgreSQL correctos (TIMESTAMPTZ, NUMERIC, etc.)
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_<tabla> PRIMARY KEY (id)
);

CREATE INDEX idx_<tabla>_<campo> ON <nombre_tabla> (<campo>);
```

---

## Fase 5 — Implementar el adapter web

### 5.1 DTOs

```java
// infrastructure/web/dto/
public record <Accion><Nombre>Request(
    @NotNull /* validaciones */ TipoCampo campo
) {}

public record <Nombre>Response(
    UUID id,
    // campos relevantes para el cliente
    Instant createdAt
) {}
```

### 5.2 Controller

```java
// infrastructure/web/
@RestController
@RequestMapping("/api/v1/<recursos>")
@RequiredArgsConstructor
@Tag(name = "<Nombre>", description = "<Descripción para OpenAPI>")
public class <Nombre>Controller {

    private final <Verbo><Sustantivo>UseCase useCase;
    private final <Nombre>WebMapper mapper;

    @PostMapping
    @PreAuthorize("hasRole('ROLE_USER')")
    @Operation(summary = "<descripción>")
    public ResponseEntity<ApiResponse<<Nombre>Response>> <verbo>(
            @Valid @RequestBody <Accion><Nombre>Request request) {

        var command = mapper.toCommand(request);
        var result  = useCase.execute(command);
        return ResponseEntity
            .status(HttpStatus.CREATED)
            .body(ApiResponse.of(mapper.toResponse(result)));
    }
}
```

---

## Fase 6 — Tests

Escribe los tests en este orden: unitario primero, integración después.

### 6.1 Test unitario del caso de uso

```java
// test/java/.../application/usecase/
class <Verbo><Sustantivo>ServiceTest {

    private final <Sustantivo>Repository repository = mock(<Sustantivo>Repository.class);
    private final <Verbo><Sustantivo>Service service = new <Verbo><Sustantivo>Service(repository);

    @Test
    void should_<resultado>_when_<condicion>() {
        // Arrange
        var command = new <Verbo><Sustantivo>Command(/* datos válidos */);
        // Act
        var result = service.execute(command);
        // Assert
        assertThat(result).isNotNull();
        verify(repository).save(any());
    }

    @Test
    void should_throw_<excepcion>_when_<condicion_invalida>() {
        // ...
    }
}
```

### 6.2 Test de slice del controller

```java
// test/java/.../infrastructure/web/
@WebMvcTest(<Nombre>Controller.class)
class <Nombre>ControllerTest {

    @Autowired MockMvc mockMvc;
    @MockBean <Verbo><Sustantivo>UseCase useCase;

    @Test
    void should_return_201_when_request_is_valid() throws Exception {
        given(useCase.execute(any())).willReturn(/* resultado */);

        mockMvc.perform(post("/api/v1/<recursos>")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    { "campo": "valor" }
                    """))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.data.id").isNotEmpty());
    }

    @Test
    void should_return_400_when_request_is_invalid() throws Exception {
        mockMvc.perform(post("/api/v1/<recursos>")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{}"))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.error.status").value(400));
    }
}
```

### 6.3 Test de integración del repositorio (Testcontainers)

```java
// test/java/.../infrastructure/persistence/
@DataJpaTest
@AutoConfigureTestDatabase(replace = NONE)
@Testcontainers
class <Nombre>RepositoryAdapterIT {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired <Nombre>RepositoryAdapter adapter;

    @Test
    void should_persist_and_retrieve_<nombre>() {
        var entity = <NombreEntidad>.<factoryMethod>(...);
        adapter.save(entity);
        var found = adapter.findById(entity.id());
        assertThat(found).isPresent();
    }
}
```

---

## Fase 7 — Verificación final

```bash
# 1. Todos los tests en verde
./mvnw verify -q

# 2. Sin warnings del compilador
./mvnw compile 2>&1 | grep -i warning || echo "Sin warnings"

# 3. Verificar que la migración se aplica correctamente
./mvnw flyway:info

# 4. Levantar la app y probar el endpoint manualmente
./mvnw spring-boot:run &
curl -s -X POST http://localhost:8080/api/v1/<recursos> \
  -H "Content-Type: application/json" \
  -d '{ "campo": "valor" }' | jq .
```

## Criterios de éxito

- [ ] `./mvnw verify` pasa en verde sin modificaciones adicionales.
- [ ] El dominio (`domain/`) no importa nada de Spring, JPA ni `infrastructure`.
- [ ] El caso de uso implementa el puerto de entrada correspondiente.
- [ ] La entidad JPA está separada de la entidad de dominio.
- [ ] Si hubo cambios de schema, existe la migración Flyway correspondiente.
- [ ] El controller devuelve el envelope `{ data, error, meta }`.
- [ ] Hay tests unitarios para el caso de uso y tests de slice para el controller.
- [ ] El endpoint está documentado en OpenAPI con `@Operation`.
