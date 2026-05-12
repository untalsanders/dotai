# Reglas de Arquitectura

## Modelo base: Arquitectura Hexagonal (Ports & Adapters)

El dominio es el centro. Nada del mundo exterior entra al dominio sin pasar por un puerto.

```
Mundo exterior → Adapter (entrada) → Puerto (entrada) → Caso de uso → Puerto (salida) → Adapter (salida) → Mundo exterior
```

### Reglas de dependencia (obligatorias)

```
domain     ←  application  ←  infrastructure
   ↑                                ↑
   └────────────────────────────────┘
         infraestructura conoce el dominio,
         el dominio NO conoce la infraestructura
```

Prueba rápida: si puedes ejecutar los tests de `domain` y `application` sin Spring en el classpath, la arquitectura es correcta.

---

## Capa `domain/`

Es el núcleo del sistema. No depende de ningún framework.

**Lo que vive aquí:**

- **Entidades:** tienen identidad (`id`) y ciclo de vida. Encapsulan comportamiento de dominio.
- **Value Objects:** inmutables, sin identidad, igualdad por valor. Usa `record` de Java 21.
- **Aggregates:** grupo de entidades con un `Aggregate Root` que controla los invariantes del conjunto.
- **Puertos de entrada (`port/in`):** interfaces que declaran los casos de uso. El controller los llama.
- **Puertos de salida (`port/out`):** interfaces que declaran dependencias externas (repositorios, servicios externos). El dominio las declara, la infraestructura las implementa.
- **Excepciones de dominio:** extienden `RuntimeException`. Nunca uses excepciones genéricas de Java para lógica de negocio.

```java
// Value Object con record
public record Money(BigDecimal amount, Currency currency) {
    public Money {
        if (amount.compareTo(BigDecimal.ZERO) < 0)
            throw new InvalidMoneyException("Amount cannot be negative");
    }

    public Money add(Money other) {
        if (!this.currency.equals(other.currency))
            throw new CurrencyMismatchException();
        return new Money(this.amount.add(other.amount), this.currency);
    }
}

// Puerto de entrada
public interface PlaceOrderUseCase {
    OrderId execute(PlaceOrderCommand command);
}

// Puerto de salida
public interface OrderRepository {
    void save(Order order);
    Optional<Order> findById(OrderId id);
}
```

---

## Capa `application/`

Orquesta el dominio. Un caso de uso = una clase.

- Implementa los puertos de entrada.
- Llama a los puertos de salida (nunca a adapters directamente).
- Gestiona las transacciones (`@Transactional`).
- No contiene lógica de negocio — eso vive en el dominio.
- No conoce HTTP, JPA, ni ningún detalle de infraestructura.

```java
@Service
@Transactional
@RequiredArgsConstructor
public class PlaceOrderService implements PlaceOrderUseCase {

    private final OrderRepository orderRepository;
    private final ProductRepository productRepository;
    private final OrderEventPublisher eventPublisher;

    @Override
    public OrderId execute(PlaceOrderCommand command) {
        var product = productRepository.findById(command.productId())
            .orElseThrow(() -> new ProductNotFoundException(command.productId()));

        var order = Order.place(command.customerId(), product, command.quantity());
        orderRepository.save(order);
        eventPublisher.publish(new OrderPlacedEvent(order.id()));

        return order.id();
    }
}
```

---

## Capa `infrastructure/`

Conecta el dominio con el mundo exterior. Aquí sí hay Spring, JPA, Kafka, HTTP.

### `infrastructure/web/`

- Controllers: solo delegan al caso de uso correspondiente. Sin lógica.
- DTOs de request/response separados de las entidades de dominio.
- Un mapper por recurso (usa MapStruct o mapeo manual, nunca ModelMapper).

### `infrastructure/persistence/`

- Entidades JPA separadas de las entidades de dominio.
- Repositorios Spring Data implementan los puertos de salida del dominio.
- Mappers entre entidad JPA ↔ entidad de dominio en la misma carpeta.

### `infrastructure/messaging/`

- Producers publican eventos de dominio.
- Consumers convierten mensajes en comandos y llaman casos de uso.

### `infrastructure/config/`

- Un archivo por tecnología: `SecurityConfig`, `KafkaConfig`, `CacheConfig`.
- Sin lógica de negocio. Solo definición de beans.

---

## Diseño del dominio (DDD táctico)

### Aggregates

- Define un límite de consistencia. Dentro del aggregate, los invariantes siempre se cumplen.
- El `Aggregate Root` es el único punto de entrada para modificar el aggregate.
- Los aggregates se comunican entre sí por `id`, nunca por referencia directa.
- Aggregates pequeños: si un aggregate supera 5 entidades, probablemente está haciendo demasiado.

### Eventos de dominio

Publica eventos cuando algo significativo ocurre en el dominio. Úsalos para desacoplar aggregates entre sí:

```java
public class Order {
    private final List<DomainEvent> domainEvents = new ArrayList<>();

    public static Order place(CustomerId customerId, Product product, int quantity) {
        var order = new Order(/* ... */);
        order.domainEvents.add(new OrderPlacedEvent(order.id, customerId));
        return order;
    }

    public List<DomainEvent> pullDomainEvents() {
        var events = List.copyOf(domainEvents);
        domainEvents.clear();
        return events;
    }
}
```

---

## SOLID en la práctica

| Principio | Señal de violación | Corrección |
|---|---|---|
| **S**ingle Responsibility | Clase con más de una razón para cambiar | Extrae responsabilidades a clases separadas |
| **O**pen/Closed | `if/else` o `switch` sobre tipos para añadir comportamiento | Introduce polimorfismo o Strategy |
| **L**iskov Substitution | Subclase lanza excepciones que la base no declara | Revisión del modelo de herencia |
| **I**nterface Segregation | Interfaz con métodos que los clientes no usan | Divide la interfaz |
| **D**ependency Inversion | Clase concreta inyectada donde debería ir una interfaz | Introduce un puerto/interfaz |

---

## Patrones permitidos y cuándo usarlos

| Patrón | Cuándo | Cuándo NO |
|---|---|---|
| **Strategy** | Algoritmos intercambiables en tiempo de ejecución | Cuando solo hay una implementación |
| **Factory Method** | Creación compleja de objetos de dominio | Creación trivial (usa `new`) |
| **Observer / Events** | Desacoplar reacciones a cambios de estado | Flujos síncronos simples |
| **Decorator** | Añadir comportamiento sin modificar la clase base | Cuando la herencia es más clara |
| **Outbox Pattern** | Garantizar entrega de eventos junto con la transacción de BD | Sistemas sin requisito de consistencia eventual |

---

## Lo que NO hacer

- No implementes `Serializable` en entidades de dominio sin una razón explícita.
- No uses herencia entre entidades de dominio — usa composición.
- No pongas anotaciones de Spring (`@Component`, `@Service`) en clases del paquete `domain`.
- No crees un "ServiceImpl" para cada interfaz de forma refleja — un puerto de salida tiene sentido; una interfaz para cada service no.
- No compartas entidades JPA entre diferentes aggregates.
