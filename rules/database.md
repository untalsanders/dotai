# Reglas de Base de Datos

## Cuándo usar JPA vs Spring Data JDBC

| Criterio | Spring Data JPA | Spring Data JDBC |
|---|---|---|
| Relaciones complejas (muchos `@OneToMany`, `@ManyToMany`) | ✅ | ❌ |
| Aggregate Root simple con pocos hijos | ❌ | ✅ |
| Rendimiento crítico, control total del SQL | ❌ | ✅ |
| Lazy loading necesario en múltiples niveles | ✅ | ❌ |
| Modelo de dominio rico con comportamiento | ✅ | ✅ |
| Queries CQRS / lectura de datos complejos | ❌ (usa JDBC directamente) | ✅ |

Regla práctica: empieza con **Spring Data JDBC**. Migra a JPA solo cuando necesites una feature que JDBC no provee.

---

## Entidades JPA

### Convenciones

```java
@Entity
@Table(name = "orders", indexes = {
    @Index(name = "idx_orders_customer_id", columnList = "customer_id"),
    @Index(name = "idx_orders_status_created_at", columnList = "status, created_at")
})
public class OrderJpaEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "customer_id", nullable = false)
    private UUID customerId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 50)
    private OrderStatus status;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<OrderItemJpaEntity> items = new ArrayList<>();

    // Sin lógica de negocio. Solo getters y setters.
}
```

### Reglas de entidades JPA

- Usa `GenerationType.UUID` para IDs — nunca `SEQUENCE` o `IDENTITY` con `Long`.
- Todos los campos `@Column` con `nullable`, `length` y `updatable` explícitos.
- Nunca uses `@Data` de Lombok en entidades JPA — rompe `equals`/`hashCode` con lazy loading.
- Implementa `equals` y `hashCode` basados únicamente en el `id`.
- Usa `Instant` para timestamps, nunca `Date` ni `LocalDateTime` sin zona horaria.
- Columnas de auditoría con `@CreatedDate` / `@LastModifiedDate` de Spring Data.

```java
@EntityListeners(AuditingEntityListener.class)
public class BaseEntity {
    @CreatedDate
    @Column(updatable = false)
    private Instant createdAt;

    @LastModifiedDate
    private Instant updatedAt;
}
```

---

## Relaciones y el problema N+1

### El problema

```java
// ❌ N+1: por cada order se hace una query para cargar items
List<Order> orders = orderRepo.findAll();
orders.forEach(o -> o.getItems().size()); // N queries adicionales
```

### Soluciones

**`@EntityGraph`** — para queries específicas que necesitan las relaciones:

```java
@EntityGraph(attributePaths = {"items", "items.product"})
@Query("SELECT o FROM OrderJpaEntity o WHERE o.customerId = :customerId")
List<OrderJpaEntity> findWithItemsByCustomerId(@Param("customerId") UUID customerId);
```

**`JOIN FETCH`** — cuando el `@EntityGraph` no es suficientemente expresivo:

```java
@Query("SELECT DISTINCT o FROM OrderJpaEntity o JOIN FETCH o.items i JOIN FETCH i.product WHERE o.status = :status")
List<OrderJpaEntity> findWithItemsByStatus(@Param("status") OrderStatus status);
```

**Proyecciones** — para lecturas que no necesitan el aggregate completo:

```java
public interface OrderSummary {
    UUID getId();
    String getStatus();
    Instant getCreatedAt();
}

List<OrderSummary> findByCustomerId(UUID customerId);
```

**Regla:** habilita `spring.jpa.properties.hibernate.generate_statistics=true` en desarrollo y monitorea el número de queries por request en los tests de integración.

---

## Fetch Type

- **Siempre `FetchType.LAZY`** en todas las relaciones (`@OneToMany`, `@ManyToMany`, `@ManyToOne`, `@OneToOne`).
- Carga las relaciones explícitamente solo cuando las necesitas.
- `spring.jpa.open-in-view=false` — sin excepción. El lazy loading fuera de la transacción es un bug silencioso.

```yaml
# application.yml
spring:
  jpa:
    open-in-view: false
```

---

## Migraciones con Flyway

### Convención de nombres

```
V{major}.{minor}.{patch}__{descripcion_en_snake_case}.sql

V1.0.0__create_orders_table.sql
V1.1.0__add_shipping_address_to_orders.sql
V1.1.1__create_index_orders_customer_id.sql
V2.0.0__rename_orders_to_purchase_orders.sql
```

### Estructura de una migración bien escrita

```sql
-- V1.0.0__create_orders_table.sql

CREATE TABLE orders (
    id          UUID        NOT NULL DEFAULT gen_random_uuid(),
    customer_id UUID        NOT NULL,
    status      VARCHAR(50) NOT NULL,
    total_amount NUMERIC(19, 4) NOT NULL,
    currency    VARCHAR(3)  NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_orders PRIMARY KEY (id),
    CONSTRAINT chk_orders_status CHECK (status IN ('PENDING', 'CONFIRMED', 'SHIPPED', 'DELIVERED', 'CANCELLED'))
);

CREATE INDEX idx_orders_customer_id   ON orders (customer_id);
CREATE INDEX idx_orders_status        ON orders (status);
CREATE INDEX idx_orders_created_at    ON orders (created_at DESC);

COMMENT ON TABLE orders IS 'Customer purchase orders';
```

### Reglas de migraciones

- **Nunca modifiques** un archivo de migración ya aplicado en producción — crea una nueva.
- Define índices en la migración, no con `@Index` de JPA (Hibernate los puede perder en un `update`).
- Agrega `CHECK CONSTRAINTS` para enums en la BD — no confíes solo en la validación de la app.
- Para tablas grandes, usa migraciones `CONCURRENT` en PostgreSQL para no bloquear: `CREATE INDEX CONCURRENTLY`.
- Incluye el `DROP` correspondiente en una migración de rollback separada si el equipo lo requiere.

---

## Transacciones

```java
// En el caso de uso — aquí vive la transacción
@Service
@Transactional(readOnly = true)  // readOnly por defecto para optimizar lecturas
public class OrderService implements GetOrderUseCase, PlaceOrderUseCase {

    @Override
    @Transactional  // override para operaciones de escritura
    public OrderId execute(PlaceOrderCommand command) { ... }

    @Override
    public OrderResponse execute(GetOrderQuery query) { ... }
}
```

- `@Transactional` vive en la capa `application`, nunca en `infrastructure` ni en `domain`.
- Usa `readOnly = true` en el service por defecto — solo anula en métodos de escritura.
- Nunca uses `@Transactional` en controllers.
- Para operaciones en lote, procesa en chunks con `@Transactional(propagation = REQUIRES_NEW)` para no mantener una transacción gigante abierta.

---

## Queries con Spring Data

### Orden de preferencia

1. **Derived query methods** — para queries simples:
   ```java
   List<Order> findByCustomerIdAndStatus(UUID customerId, OrderStatus status);
   ```

2. **`@Query` con JPQL** — cuando el derived method es ilegible:
   ```java
   @Query("SELECT o FROM OrderJpaEntity o WHERE o.total >= :minAmount AND o.createdAt > :since")
   List<OrderJpaEntity> findHighValueOrders(@Param("minAmount") BigDecimal minAmount, @Param("since") Instant since);
   ```

3. **`@Query` con SQL nativo** — para queries complejas con funciones de PostgreSQL:
   ```java
   @Query(value = "SELECT * FROM orders WHERE to_tsvector('spanish', notes) @@ plainto_tsquery(:term)", nativeQuery = true)
   List<OrderJpaEntity> fullTextSearch(@Param("term") String term);
   ```

4. **`JdbcTemplate` o `NamedParameterJdbcTemplate`** — para CQRS: queries de lectura complejas que no necesitan el modelo de objetos.

### Nunca

- No construyas queries con concatenación de strings — usa parámetros nombrados.
- No uses `findAll()` sin paginación en tablas que crecen.
- No hagas queries dentro de bucles — consolida en una sola query con `IN`.

---

## Pool de conexiones (HikariCP)

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 10          # (núcleos_cpu * 2) + num_discos — ajusta con carga real
      minimum-idle: 5
      connection-timeout: 30000      # 30s máximo esperando conexión del pool
      idle-timeout: 600000           # 10min antes de cerrar conexión idle
      max-lifetime: 1800000          # 30min — siempre menor al wait_timeout de la BD
      leak-detection-threshold: 60000 # Alerta si una conexión se usa más de 60s
```

Monitorea el pool con el endpoint `/actuator/metrics/hikaricp.connections.active`.

---

## PostgreSQL — features a aprovechar

| Feature | Cuándo usarla |
|---|---|
| `gen_random_uuid()` | IDs UUID por defecto en la BD |
| `JSONB` | Datos semiestructurados que necesitas consultar |
| `TIMESTAMPTZ` | Siempre para timestamps (nunca `TIMESTAMP` sin zona) |
| `NUMERIC(19,4)` | Dinero — nunca `FLOAT` o `DOUBLE PRECISION` |
| `UNLOGGED TABLE` | Tablas de caché o staging de alto throughput que puedes perder |
| `PARTITION BY RANGE` | Tablas de eventos o logs con millones de filas por mes |
| Full-Text Search | Búsqueda en texto libre antes de introducir Elasticsearch |

---

## Lo que NO hacer

- No uses `spring.jpa.hibernate.ddl-auto=update` en producción — solo `validate`.
- No mapees columnas calculadas con `@Formula` si puedes hacer la proyección en la query.
- No pongas lógica de negocio en stored procedures — el código de negocio vive en la app.
- No crees un repositorio por entidad JPA sin que corresponda a un aggregate root.
- No hagas `flush()` manual sin una razón documentada — Hibernate lo gestiona.
