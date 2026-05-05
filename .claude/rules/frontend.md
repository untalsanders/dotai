# Reglas de Contrato Backend-Frontend

Este proyecto es backend. Este archivo define cómo el backend debe diseñar sus APIs y configurar sus servicios para que el frontend pueda consumirlos de forma predecible, eficiente y segura.

---

## CORS

Configura CORS explícitamente. Nunca uses `allowedOrigins("*")` en producción:

```java
@Configuration
public class CorsConfig implements WebMvcConfigurer {

    @Value("${app.cors.allowed-origins}")
    private List<String> allowedOrigins;

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins(allowedOrigins.toArray(String[]::new))
            .allowedMethods("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
            .allowedHeaders("Authorization", "Content-Type", "X-Request-Id", "Idempotency-Key")
            .exposedHeaders("X-Request-Id", "X-Response-Time", "Link")
            .allowCredentials(true)
            .maxAge(3600);
    }
}
```

En `application.yml`:

```yaml
app:
  cors:
    allowed-origins:
      - https://app.tudominio.com
      - https://staging.tudominio.com
```

En desarrollo local, externaliza los orígenes permitidos en `application-local.yml`:

```yaml
app:
  cors:
    allowed-origins:
      - http://localhost:3000
      - http://localhost:5173
```

---

## Autenticación con JWT para SPAs

### Flujo recomendado

```
SPA → POST /api/v1/auth/login → { accessToken, expiresIn }
SPA → almacena accessToken en memoria (NO en localStorage)
SPA → POST /api/v1/auth/refresh (cookie httpOnly con refreshToken) → nuevo accessToken
SPA → POST /api/v1/auth/logout → invalida refreshToken en servidor
```

### Headers de autenticación

```
Authorization: Bearer <accessToken>
```

### Endpoints de autenticación

```java
// Login
POST /api/v1/auth/login
Body: { "email": "...", "password": "..." }
Response: { "data": { "accessToken": "...", "expiresIn": 900 }, ... }
Set-Cookie: refreshToken=...; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth/refresh

// Refresh
POST /api/v1/auth/refresh
Cookie: refreshToken=...
Response: { "data": { "accessToken": "...", "expiresIn": 900 }, ... }

// Logout
POST /api/v1/auth/logout
Response: 204 No Content
Set-Cookie: refreshToken=; Max-Age=0
```

**Por qué refresh token en cookie `httpOnly`:** el frontend nunca puede leerla con JavaScript, lo que elimina el riesgo de robo por XSS.

---

## Contrato de respuesta predecible

El frontend necesita saber qué esperar en cada caso. Mantén el envelope consistente en absolutamente todas las respuestas:

### Éxito con datos

```json
{ "data": { ... }, "error": null, "meta": { "timestamp": "..." } }
```

### Éxito sin datos (DELETE, operaciones void)

```json
{ "data": null, "error": null, "meta": { "timestamp": "..." } }
```

### Error de validación (400)

```json
{
  "data": null,
  "error": {
    "type": "/errors/validation-failed",
    "title": "Validation Failed",
    "status": 400,
    "detail": "Request contains invalid fields",
    "errors": [
      { "field": "email", "message": "must be a valid email" },
      { "field": "name",  "message": "must not be blank" }
    ]
  },
  "meta": { "timestamp": "..." }
}
```

El campo `errors` permite al frontend mostrar errores junto al campo correspondiente sin parsear el `detail`.

### Error de negocio (404, 409, 422)

```json
{
  "data": null,
  "error": {
    "type": "/errors/resource-not-found",
    "title": "Not Found",
    "status": 404,
    "detail": "Order '42' does not exist",
    "instance": "/api/v1/orders/42"
  },
  "meta": { "timestamp": "..." }
}
```

---

## Campos nullable vs ausentes

- Un campo que puede no tener valor debe estar presente con valor `null`, nunca ausente.
- El frontend no debe usar `hasOwnProperty` para detectar campos opcionales — que siempre estén en el schema.

```json
// ✅ Correcto
{ "phone": null, "address": null }

// ❌ Incorrecto — el frontend no sabe si es null o si el campo no existe
{ }
```

Configura Jackson para serializar nulls:

```java
@Bean
public Jackson2ObjectMapperBuilderCustomizer jsonCustomizer() {
    return builder -> builder
        .serializationInclusion(JsonInclude.Include.ALWAYS)  // incluye nulls
        .featuresToDisable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
        .featuresToEnable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES);
}
```

---

## Paginación y colecciones

Estructura de página que el frontend puede consumir directamente:

```json
{
  "data": {
    "content": [ ],
    "page": {
      "size": 20,
      "number": 0,
      "totalElements": 150,
      "totalPages": 8,
      "first": true,
      "last": false
    }
  },
  "meta": { "timestamp": "..." }
}
```

Parámetros de paginación en query string:

```
GET /api/v1/orders?page=0&size=20&sort=createdAt,desc
```

Documenta los valores por defecto en la documentación OpenAPI con `@PageableDefault`.

---

## Eventos en tiempo real (SSE)

Para notificaciones push del servidor al cliente sin WebSocket:

```java
@GetMapping(value = "/api/v1/notifications/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public SseEmitter streamNotifications(@AuthenticationPrincipal UserDetails user) {
    SseEmitter emitter = new SseEmitter(Long.MAX_VALUE);
    notificationService.register(user.getUsername(), emitter);
    return emitter;
}
```

Usa SSE cuando:
- El cliente solo necesita recibir (no enviar) actualizaciones.
- Las actualizaciones son infrecuentes (estado de pedido, notificaciones).

Usa WebSocket cuando:
- Hay comunicación bidireccional en tiempo real (chat, colaboración en vivo).

---

## Documentación OpenAPI para el frontend

La documentación OpenAPI es el contrato con el equipo de frontend. Mantenla actualizada y precisa:

```java
@OpenAPIDefinition(
    info = @Info(
        title = "API de Pedidos",
        version = "1.0",
        description = "API REST para gestión de pedidos. Versión mínima soportada: v1."
    ),
    servers = {
        @Server(url = "https://api.tudominio.com", description = "Producción"),
        @Server(url = "http://localhost:8080",    description = "Local")
    }
)
```

- El equipo de frontend usa el archivo OpenAPI para generar clientes tipados (openapi-generator, orval). Nunca rompas el schema sin avisar.
- Marca los campos deprecados con `@Schema(deprecated = true)` antes de eliminarlos.
- Documenta los posibles `status` de un enum en `@Schema(description = "...")`.

---

## Rate limiting

Protege los endpoints de alto tráfico y los de autenticación:

```java
// Con Bucket4j + Spring Boot Starter
@RateLimiter(name = "loginEndpoint")  // 5 intentos / minuto por IP
@PostMapping("/api/v1/auth/login")
public ResponseEntity<...> login(@Valid @RequestBody LoginRequest request) { ... }
```

Cuando se supera el límite, devuelve `429 Too Many Requests` con el header:

```
Retry-After: 60
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1700000060
```

---

## Lo que NO hacer

- No devuelvas diferentes estructuras de respuesta según el endpoint — el frontend no puede hacer un cliente genérico.
- No uses `Date` de Java en las respuestas — siempre `Instant` serializado como ISO 8601.
- No expongas IDs de base de datos secuenciales — usa UUIDs para evitar enumeración.
- No devuelvas información de stack traces o detalles internos en errores de producción.
- No cambies el nombre de un campo existente sin versionar la API — es un breaking change.
- No configures sesiones del lado del servidor para APIs consumidas por SPAs — usa JWT stateless.
