# Reglas de API REST

## Diseño de recursos

### URLs

- Sustantivos en plural, en minúsculas, separados por guiones: `/api/v1/customer-orders`.
- Recursos anidados solo un nivel: `/api/v1/orders/{orderId}/items`. Más profundo → recurso propio.
- Nunca incluyas verbos en la URL: ~~`/getUser`~~, ~~`/createOrder`~~.
- Acciones que no encajan en CRUD usan sub-recursos descriptivos: `POST /api/v1/orders/{id}/cancellation`.

### Métodos HTTP

| Método | Semántica | Idempotente | Body |
|---|---|---|---|
| `GET` | Leer recurso o colección | Sí | No |
| `POST` | Crear recurso o acción | No | Sí |
| `PUT` | Reemplazar recurso completo | Sí | Sí |
| `PATCH` | Actualizar parcialmente | No* | Sí |
| `DELETE` | Eliminar recurso | Sí | No |

*`PATCH` puede hacerse idempotente con operaciones JSON Patch (RFC 6902).

### Códigos de estado

Usa el código más específico disponible:

```
200 OK             → GET exitoso, PUT/PATCH exitoso con body de respuesta
201 Created        → POST que crea un recurso (incluye Location header)
204 No Content     → DELETE exitoso, PUT/PATCH sin body de respuesta
400 Bad Request    → Payload inválido, validación fallida
401 Unauthorized   → No autenticado
403 Forbidden      → Autenticado pero sin permiso
404 Not Found      → Recurso inexistente
409 Conflict       → Violación de unicidad, estado incompatible
422 Unprocessable  → Semánticamente inválido (regla de negocio)
429 Too Many Reqs  → Rate limit superado
500 Internal Error → Error inesperado del servidor
```

---

## Contratos de request/response

### Envelope de respuesta

Toda respuesta usa el mismo envelope. Nunca devuelvas el objeto desnudo:

```json
{
  "data": { },
  "error": null,
  "meta": {
    "timestamp": "2025-01-01T12:00:00Z",
    "requestId": "uuid-aqui"
  }
}
```

En errores, `data` es `null` y `error` tiene contenido:

```json
{
  "data": null,
  "error": {
    "type": "/errors/resource-not-found",
    "title": "Resource Not Found",
    "status": 404,
    "detail": "Order with id '42' does not exist",
    "instance": "/api/v1/orders/42"
  },
  "meta": {
    "timestamp": "2025-01-01T12:00:00Z",
    "requestId": "uuid-aqui"
  }
}
```

### Records para DTOs

```java
// Request
public record CreateOrderRequest(
    @NotNull UUID productId,
    @Positive int quantity,
    @NotNull @Valid ShippingAddressRequest shippingAddress
) {}

// Response
public record OrderResponse(
    UUID id,
    String status,
    List<OrderItemResponse> items,
    MoneyResponse total,
    Instant createdAt
) {}
```

### Fechas y formatos

- Fechas: ISO 8601 en UTC — `"2025-01-01T12:00:00Z"`. Nunca timestamps Unix.
- Dinero: `{ "amount": "19.99", "currency": "USD" }`. Nunca `float` o `double`.
- IDs: UUID en formato string. Nunca expongas IDs numéricos secuenciales.
- Enums: string en UPPER_SNAKE_CASE.

---

## Manejo de errores

### `@RestControllerAdvice` global

Un único punto de manejo de excepciones. Nunca manejes excepciones individualmente en cada controller:

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ApiResponse<Void>> handleNotFound(
            ResourceNotFoundException ex, HttpServletRequest request) {
        log.warn("Resource not found: {}", ex.getMessage());
        var problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        problem.setType(URI.create("/errors/resource-not-found"));
        problem.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(ApiResponse.error(problem));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidation(
            MethodArgumentNotValidException ex) {
        var errors = ex.getBindingResult().getFieldErrors().stream()
            .map(e -> "%s: %s".formatted(e.getField(), e.getDefaultMessage()))
            .toList();
        var problem = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        problem.setTitle("Validation Failed");
        problem.setProperty("errors", errors);
        return ResponseEntity.badRequest().body(ApiResponse.error(problem));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleUnexpected(Exception ex) {
        log.error("Unexpected error", ex);
        var problem = ProblemDetail.forStatus(HttpStatus.INTERNAL_SERVER_ERROR);
        problem.setTitle("Internal Server Error");
        return ResponseEntity.internalServerError().body(ApiResponse.error(problem));
    }
}
```

---

## Paginación

Toda colección debe ser paginada. Nunca devuelvas una lista sin límite:

```java
@GetMapping
public ResponseEntity<ApiResponse<Page<OrderResponse>>> listOrders(
        @PageableDefault(size = 20, sort = "createdAt", direction = DESC) Pageable pageable) {
    return ResponseEntity.ok(ApiResponse.of(orderService.list(pageable)));
}
```

Respuesta de colección paginada:

```json
{
  "data": {
    "content": [ ],
    "page": {
      "size": 20,
      "number": 0,
      "totalElements": 150,
      "totalPages": 8
    }
  },
  "error": null,
  "meta": { "timestamp": "..." }
}
```

Parámetros de paginación estándar: `?page=0&size=20&sort=createdAt,desc`.

---

## Validación

Nunca valides manualmente en el controller. Usa Bean Validation y deja que `@Valid` lo dispare:

```java
public record CreateUserRequest(
    @NotBlank @Size(min = 2, max = 100) String name,
    @NotBlank @Email String email,
    @NotNull @Past LocalDate birthDate,
    @NotBlank @Pattern(regexp = "^(?=.*[A-Z])(?=.*\\d).{8,}$",
                      message = "must have 8+ chars, one uppercase, one digit")
    String password
) {}
```

Para validaciones de negocio que Bean Validation no puede cubrir, lanza excepciones de dominio desde el caso de uso — no desde el controller.

---

## Versionado

- Versionado en la URL desde el día 1: `/api/v1/`.
- Antes de lanzar una versión nueva (`v2`), mantén `v1` operativa durante al menos 6 meses.
- Documenta los cambios breaking en el CHANGELOG con la versión en la que se eliminará `v1`.
- Nunca cambies un contrato existente sin versionar: agregar campos opcionales está bien; eliminar o renombrar campos requiere nueva versión.

---

## Documentación con OpenAPI

```java
@Operation(
    summary = "Place a new order",
    description = "Creates an order for the authenticated customer.",
    responses = {
        @ApiResponse(responseCode = "201", description = "Order created"),
        @ApiResponse(responseCode = "400", description = "Invalid request payload"),
        @ApiResponse(responseCode = "404", description = "Product not found")
    }
)
@PostMapping
public ResponseEntity<ApiResponse<OrderResponse>> placeOrder(
        @Valid @RequestBody CreateOrderRequest request) { ... }
```

- Todos los endpoints públicos documentados con `@Operation`.
- Los schemas de error documentados en `@ApiResponse` con `content`.
- El archivo OpenAPI generado expuesto en `/api-docs` (JSON) y `/swagger-ui` (UI).

---

## Idempotencia

Para operaciones que pueden reintentarse (pagos, creación de pedidos), soporta idempotency keys:

```
POST /api/v1/orders
Idempotency-Key: uuid-del-cliente
```

Almacena el resultado de la primera ejecución asociado a la key. Las siguientes peticiones con la misma key devuelven el resultado almacenado sin re-ejecutar la lógica.

---

## Headers de respuesta obligatorios

```
Content-Type: application/json
X-Request-Id: {uuid}           # Trazabilidad — propaga el requestId del cliente o genera uno
X-Response-Time: {ms}          # Tiempo de procesamiento en milisegundos
```

En endpoints con paginación, añade también:

```
Link: <url?page=1>; rel="next", <url?page=7>; rel="last"
```

---

## Lo que NO hacer

- No uses `@ResponseBody` directamente — extiende `ResponseEntityExceptionHandler` o usa `@RestControllerAdvice`.
- No devuelvas `null` desde un controller — devuelve `204 No Content` o un body vacío explícito.
- No filtres resultados con lógica `if` en el controller — delega al caso de uso o al repositorio.
- No mezcles lógica de diferentes recursos en un mismo controller.
- No expongas stacktraces en las respuestas de error en producción.
