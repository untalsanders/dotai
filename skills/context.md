# Contexto compartido del proyecto

Este archivo se inyecta como contexto en todas las skills. Contiene la información que Claude necesita en cualquier tarea, independientemente de la skill invocada.

---

## Stack tecnológico

- **Java 21** — usa records, sealed classes, pattern matching, virtual threads
- **Spring Boot 3.x** — inyección por constructor, no `@Autowired` en campos
- **Spring Data JPA** — entidades separadas del dominio, `FetchType.LAZY` siempre
- **PostgreSQL** — producción; H2 solo para tests de capa web (`@WebMvcTest`)
- **Flyway** — toda migración de schema va en `src/main/resources/db/migration/`
- **Spring Security 6** — JWT stateless, `@PreAuthorize` a nivel de método
- **Maven** — `./mvnw verify` para correr la suite completa
- **JUnit 5 + Mockito + AssertJ + Testcontainers** — sin H2 en tests de repositorio

---

## Estructura de paquetes

```
src/main/java/com/empresa/proyecto/
├── domain/
│   ├── model/          # Entidades de dominio, Value Objects (records), Aggregates
│   ├── port/
│   │   ├── in/         # Interfaces de casos de uso (puertos de entrada)
│   │   └── out/        # Interfaces de repositorios y servicios externos (puertos de salida)
│   └── exception/      # Excepciones de dominio (extienden RuntimeException)
├── application/
│   └── usecase/        # Implementaciones de los casos de uso (@Service, @Transactional)
├── infrastructure/
│   ├── persistence/    # Entidades JPA, Spring Data repositories, mappers
│   ├── web/            # Controllers REST, DTOs request/response, mappers
│   ├── messaging/      # Producers y Consumers de Kafka/RabbitMQ
│   └── config/         # Beans de configuración (Security, Cache, CORS, etc.)
└── shared/
    └── mapper/         # Mappers compartidos entre capas
```

---

## Convenciones de nomenclatura

| Elemento | Convención | Ejemplo |
|---|---|---|
| Caso de uso (interfaz) | `<Verbo><Sustantivo>UseCase` | `PlaceOrderUseCase` |
| Caso de uso (impl) | `<Verbo><Sustantivo>Service` | `PlaceOrderService` |
| Puerto de salida | `<Sustantivo>Repository` / `<Sustantivo>Gateway` | `OrderRepository` |
| Entidad JPA | `<Sustantivo>JpaEntity` | `OrderJpaEntity` |
| DTO de request | `<Acción><Sustantivo>Request` | `CreateOrderRequest` |
| DTO de response | `<Sustantivo>Response` | `OrderResponse` |
| Comando de dominio | `<Verbo><Sustantivo>Command` | `PlaceOrderCommand` |
| Evento de dominio | `<Sustantivo><Participio>Event` | `OrderPlacedEvent` |
| Migración Flyway | `V{version}__{descripcion}.sql` | `V1.2.0__add_order_index.sql` |
| Test unitario | `<Clase>Test` | `PlaceOrderServiceTest` |
| Test de integración | `<Clase>IT` | `OrderControllerIT` |

---

## Reglas de dependencia entre capas (obligatorias)

```
domain  ←  application  ←  infrastructure
```

- `domain`: sin imports de Spring, JPA ni ningún framework.
- `application`: importa `domain`, nunca `infrastructure`.
- `infrastructure`: importa `domain` y `application`. Aquí vive Spring, JPA, HTTP.

**Prueba rápida:** si los tests de `domain` y `application` pasan sin Spring en el classpath, la arquitectura es correcta.

---

## Contratos fijos que no se rompen

### Envelope de respuesta HTTP

```json
{
  "data":  { },
  "error": null,
  "meta":  { "timestamp": "2025-01-01T00:00:00Z", "requestId": "uuid" }
}
```

### Errores con ProblemDetail (RFC 9457)

```json
{
  "data": null,
  "error": {
    "type":     "/errors/resource-not-found",
    "title":    "Not Found",
    "status":   404,
    "detail":   "Order '42' does not exist",
    "instance": "/api/v1/orders/42"
  },
  "meta": { "timestamp": "..." }
}
```

### Versionado de API

Todas las rutas empiezan con `/api/v1/`. Antes de crear una ruta nueva, verificar que no existe ya en `infrastructure/web/`.

---

## Comandos frecuentes

```bash
# Compilar y correr todos los tests
./mvnw verify

# Correr solo tests unitarios (rápido)
./mvnw test

# Correr un test específico
./mvnw test -Dtest=NombreTest#nombre_metodo -q

# Correr tests de integración
./mvnw verify -P integration-tests

# Aplicar migraciones Flyway en local
./mvnw flyway:migrate -Dflyway.url=jdbc:postgresql://localhost:5432/db

# Ver qué migraciones están pendientes
./mvnw flyway:info

# Construir el JAR sin tests
./mvnw package -DskipTests -q
```

---

## Archivos clave a leer antes de implementar

Antes de tocar código en cualquier skill, verifica estos archivos para entender el estado actual del proyecto:

1. `src/main/resources/application.yml` — configuración activa
2. `src/main/resources/db/migration/` — versión actual del schema
3. El puerto de entrada relevante en `domain/port/in/` — qué casos de uso ya existen
4. El controller relevante en `infrastructure/web/` — qué endpoints ya existen
