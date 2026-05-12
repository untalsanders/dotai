---
name: frontend-design
description: Diseña el contrato de API que el backend expone al frontend: endpoints, schemas de request/response, errores, paginación y documentación OpenAPI.
argument-hint: <descripcion-del-recurso-o-flujo>
---

Diseña el contrato de API para: **$ARGUMENTS**

Esta skill no implementa lógica de negocio — diseña la interfaz entre el backend y el frontend. El objetivo es producir un contrato claro, predecible y consumible antes de que el frontend empiece a trabajar.

Antes de diseñar, lee:
- `.claude/skills/context.md` — convenciones y estructura del proyecto
- `.claude/rules/api.md` — reglas de diseño REST
- `.claude/rules/frontend.md` — reglas de contrato backend-frontend

---

## Fase 1 — Entender qué necesita el frontend

Responde estas preguntas antes de diseñar cualquier endpoint:

1. **¿Qué flujos de usuario activa este recurso?**
   - Listar, crear, editar, eliminar, buscar, filtrar...
   - ¿Hay flujos con múltiples pasos (wizard)?

2. **¿Qué campos necesita mostrar el frontend en cada pantalla?**
   - Vista de lista (tabla/cards): campos mínimos, paginación
   - Vista de detalle: campos completos, relaciones anidadas
   - Formulario de creación/edición: qué campos son editables

3. **¿Qué acciones desencadena el usuario?**
   - ¿Son idempotentes? (el usuario puede hacer clic dos veces)
   - ¿Requieren confirmación?

4. **¿Quién tiene acceso?**
   - ¿Rol requerido?
   - ¿El usuario solo puede ver/editar sus propios recursos?

5. **¿Hay datos en tiempo real?**
   - ¿Polling o SSE?

---

## Fase 2 — Diseñar los endpoints

Define cada endpoint con esta estructura antes de escribir código:

```
<MÉTODO> /api/v1/<recursos>[/<id>][/<sub-recurso>]

Descripción: <qué hace este endpoint>
Auth: <rol requerido o público>
Idempotente: <sí/no>

Request headers:
  Authorization: Bearer <token>
  Idempotency-Key: <uuid>  (solo si es necesario)

Request body:
  <schema con tipos y validaciones>

Response 2xx:
  <schema del body de éxito>

Response 4xx / 5xx:
  <códigos posibles y cuándo ocurren>
```

### Ejemplo de diseño

```
POST /api/v1/orders

Descripción: Crea un pedido para el cliente autenticado.
Auth: ROLE_CUSTOMER
Idempotente: Sí (con Idempotency-Key)

Request body:
  {
    "productId": "uuid",           // requerido
    "quantity": 2,                 // requerido, min: 1, max: 100
    "shippingAddress": {           // requerido
      "street": "string",          // requerido, max: 200
      "city": "string",            // requerido
      "postalCode": "string"       // requerido, formato: /^\d{5}$/
    }
  }

Response 201:
  { "data": { "id": "uuid", "status": "PENDING", "total": { "amount": "59.99", "currency": "USD" } } }

Response 400: payload inválido (campo faltante o formato incorrecto)
Response 404: producto no existe
Response 409: stock insuficiente
Response 422: dirección de envío no disponible en esa zona
```

---

## Fase 3 — Diseñar los schemas de request y response

### DTOs de request

Principios:
- Solo los campos que el frontend puede enviar — sin campos que el backend calcula internamente.
- Todos los campos con tipo, si es requerido u opcional, y las validaciones.
- Usa `@NotBlank` en lugar de `@NotNull` para strings — `@NotNull` acepta `""`.

```java
// infrastructure/web/dto/
public record Create<Nombre>Request(
    @NotNull(message = "campo is required")
    UUID campoRequerido,

    @NotBlank @Size(max = 200)
    String textoCampo,

    @Positive(message = "quantity must be greater than 0")
    int cantidad,

    @Valid @NotNull
    DireccionRequest direccion   // objeto anidado con su propia validación
) {}
```

### DTOs de response

Principios:
- Incluye todos los campos que alguna pantalla del frontend necesita — no filtres de más.
- Los campos opcionales siempre presentes con valor `null` (nunca ausentes).
- Fechas como ISO 8601 en UTC. Dinero como `{ amount: string, currency: string }`.
- IDs siempre como UUID string. Nunca IDs numéricos secuenciales.

```java
// Vista de lista (mínima — para tablas y cards)
public record <Nombre>SummaryResponse(
    UUID id,
    String nombre,
    String status,
    Instant createdAt
) {}

// Vista de detalle (completa — para página de detalle)
public record <Nombre>Response(
    UUID id,
    String nombre,
    String status,
    @Nullable String descripcion,          // null si no tiene valor
    List<<Sub>Response> items,             // lista vacía si no tiene items
    MoneyResponse total,
    Instant createdAt,
    Instant updatedAt
) {}
```

### Response de colección paginada

```java
// El frontend espera esta estructura para renderizar tablas con paginación
public record PageResponse<T>(
    List<T> content,
    PageMetaResponse page
) {}

public record PageMetaResponse(
    int size,
    int number,
    long totalElements,
    int totalPages,
    boolean first,
    boolean last
) {}
```

---

## Fase 4 — Diseñar los errores

El frontend necesita errores predecibles para mostrar mensajes útiles al usuario:

### Error de validación (400) — permite asignar el error al campo del formulario

```json
{
  "data": null,
  "error": {
    "type": "/errors/validation-failed",
    "title": "Validation Failed",
    "status": 400,
    "detail": "Request contains invalid fields",
    "errors": [
      { "field": "email",    "message": "must be a valid email address" },
      { "field": "quantity", "message": "must be greater than 0" }
    ]
  }
}
```

### Error de negocio (404, 409, 422) — permite mostrar un mensaje contextual

```json
{
  "data": null,
  "error": {
    "type":     "/errors/<tipo-especifico>",
    "title":    "<titulo legible>",
    "status":   <codigo>,
    "detail":   "<mensaje que el frontend puede mostrar directamente al usuario>",
    "instance": "/api/v1/<recurso>/<id>"
  }
}
```

Define un `type` único por cada error de negocio que el frontend deba manejar de forma diferente. Si dos errores producen el mismo comportamiento en el frontend, pueden compartir `type`.

---

## Fase 5 — Diseñar filtros y ordenamiento (si aplica)

Para endpoints de listado, define los parámetros de query aceptados:

```
GET /api/v1/<recursos>?
  page=0              # página (0-indexed)
  size=20             # elementos por página (máx: 100)
  sort=createdAt,desc # campo,dirección (asc|desc)
  status=PENDING      # filtro por campo enum
  search=texto        # búsqueda full-text (si aplica)
  from=2025-01-01     # filtro de fecha desde (ISO 8601)
  to=2025-12-31       # filtro de fecha hasta (ISO 8601)
```

Documenta exactamente qué filtros están disponibles y cómo se combinan (AND entre filtros del mismo tipo).

---

## Fase 6 — Documentar en OpenAPI

Documenta cada endpoint con suficiente detalle para que el equipo de frontend genere un cliente tipado automáticamente:

```java
@Tag(name = "<Nombre>s", description = "Gestión de <nombres>")
@RestController
@RequestMapping("/api/v1/<recursos>")
public class <Nombre>Controller {

    @Operation(
        summary = "Listar <nombres>",
        description = "Retorna una lista paginada de <nombres> del usuario autenticado.",
        parameters = {
            @Parameter(name = "status", description = "Filtrar por estado", schema = @Schema(implementation = <Nombre>Status.class)),
            @Parameter(name = "page",   description = "Número de página (0-indexed)", example = "0"),
            @Parameter(name = "size",   description = "Elementos por página (máx 100)", example = "20")
        },
        responses = {
            @ApiResponse(responseCode = "200", description = "Lista de <nombres>",
                content = @Content(schema = @Schema(implementation = PageResponse.class))),
            @ApiResponse(responseCode = "401", description = "No autenticado")
        }
    )
    @GetMapping
    public ResponseEntity<ApiResponse<PageResponse<<Nombre>SummaryResponse>>> list(...) { ... }
}
```

---

## Fase 7 — Verificar el contrato con un test de contrato

Antes de entregar el contrato al frontend, escribe un test que verifique la estructura exacta de la respuesta:

```java
@WebMvcTest(<Nombre>Controller.class)
class <Nombre>ContractTest {

    @Test
    void list_response_matches_contract() throws Exception {
        // Prepara datos de prueba que cubran todos los campos opcionales
        given(useCase.execute(any())).willReturn(/* datos completos */);

        mockMvc.perform(get("/api/v1/<recursos>"))
            .andExpect(status().isOk())
            // Envelope
            .andExpect(jsonPath("$.data").exists())
            .andExpect(jsonPath("$.error").value(nullValue()))
            .andExpect(jsonPath("$.meta.timestamp").exists())
            // Paginación
            .andExpect(jsonPath("$.data.page.totalElements").isNumber())
            .andExpect(jsonPath("$.data.page.totalPages").isNumber())
            .andExpect(jsonPath("$.data.content[0].id").isString())
            // Campos requeridos del DTO
            .andExpect(jsonPath("$.data.content[0].status").isString())
            // Campos opcionales presentes como null
            .andExpect(jsonPath("$.data.content[0].descripcion").exists()); // null pero presente
    }
}
```

---

## Entregable final

Al terminar esta skill, el entregable es:

1. **DTOs de request y response** escritos y compilando.
2. **Documentación OpenAPI** completa en el controller.
3. **Test de contrato** que verifica la estructura de la respuesta.
4. **Tabla de errores** documentada (qué `type` devuelve cada situación de error).

El equipo de frontend debe poder arrancar su trabajo usando solo la especificación OpenAPI en `/swagger-ui` sin necesidad de preguntar al backend cómo funciona cada endpoint.

## Criterios de éxito

- [ ] Todos los DTOs son `record` con anotaciones de validación completas.
- [ ] Los campos opcionales son `@Nullable` y siempre presentes en la respuesta (no ausentes).
- [ ] Cada endpoint tiene `@Operation` con sus posibles respuestas documentadas.
- [ ] Hay al menos un test de contrato por endpoint.
- [ ] Los errores de validación incluyen el array `errors` con `field` y `message`.
- [ ] `./mvnw verify` pasa en verde.
