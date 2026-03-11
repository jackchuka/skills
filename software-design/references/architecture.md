# Architectural Patterns — Deep Dive

## Table of Contents

- [Clean / Hexagonal Architecture](#clean--hexagonal-architecture)
- [Domain-Driven Design (DDD)](#domain-driven-design-ddd)
- [Event-Driven Architecture](#event-driven-architecture)
- [CQRS](#cqrs)
- [Monolith-First](#monolith-first)
- [Microservices](#microservices)
- [Vertical Slice Architecture](#vertical-slice-architecture)
- [Choosing an Architecture](#choosing-an-architecture)

---

## Clean / Hexagonal Architecture

**Core idea:** Business logic at the center, infrastructure at the edges. Dependencies point inward.

### Layer structure

```
┌──────────────────────────────────┐
│  Infrastructure (DB, HTTP, CLI)  │  ← adapters, frameworks
├──────────────────────────────────┤
│  Application (use cases)         │  ← orchestration, no business rules
├──────────────────────────────────┤
│  Domain (entities, value objects) │  ← pure business logic, no imports from outer layers
└──────────────────────────────────┘
```

### Go project layout

```
myapp/
├── cmd/server/main.go          # wiring, configuration
├── internal/
│   ├── domain/                 # entities, value objects, domain services
│   │   ├── order.go
│   │   └── order_repository.go # interface, NOT implementation
│   ├── application/            # use cases
│   │   └── place_order.go
│   └── infrastructure/         # adapters
│       ├── postgres/
│       │   └── order_repo.go   # implements domain.OrderRepository
│       └── http/
│           └── handler.go
```

### Key rules

- Domain layer has ZERO imports from application or infrastructure
- Interfaces defined in the domain, implemented in infrastructure
- Use cases orchestrate domain objects; they don't contain business rules
- `main.go` is the composition root — the only place that knows all concrete types

### Code example

```go
// domain/order.go — pure logic, no framework imports
type Order struct {
    ID     string
    Items  []Item
    Status Status
}

func (o *Order) Place() error {
    if len(o.Items) == 0 {
        return errors.New("order must have at least one item")
    }
    o.Status = StatusPlaced
    return nil
}

// domain/order_repository.go — interface only
type OrderRepository interface {
    Save(ctx context.Context, order *Order) error
    FindByID(ctx context.Context, id string) (*Order, error)
}

// application/place_order.go — orchestration
type PlaceOrderUseCase struct {
    repo   domain.OrderRepository
    notify Notifier
}

func (uc *PlaceOrderUseCase) Execute(ctx context.Context, items []domain.Item) error {
    order := &domain.Order{ID: uuid.New(), Items: items}
    if err := order.Place(); err != nil {
        return err
    }
    if err := uc.repo.Save(ctx, order); err != nil {
        return err
    }
    uc.notify.OrderPlaced(order)
    return nil
}
```

### Trade-offs

| Pro                                                             | Con                        |
| --------------------------------------------------------------- | -------------------------- |
| Domain logic is testable without infrastructure                 | More files and indirection |
| Swap databases, HTTP frameworks without touching business logic | Overkill for simple CRUD   |
| Clear dependency direction                                      | Learning curve for team    |

### When to use

- Systems expected to live 2+ years
- Complex domain logic beyond simple CRUD
- Multiple delivery mechanisms (HTTP, gRPC, CLI)
- Teams that value testability

### When to skip

- Prototypes, hackathons, throwaway scripts
- Pure CRUD with no business rules (just use a framework)

---

## Domain-Driven Design (DDD)

**Core idea:** Model the software after the business domain. Use ubiquitous language shared between developers and domain experts.

### Strategic patterns

| Pattern             | Purpose                                                                                  |
| ------------------- | ---------------------------------------------------------------------------------------- |
| Bounded Context     | Explicit boundary around a domain model with its own language                            |
| Context Map         | How bounded contexts relate (shared kernel, anti-corruption layer, etc.)                 |
| Ubiquitous Language | Shared vocabulary between code and business — same terms in code, docs, and conversation |

### Tactical patterns

| Pattern        | What it is                                                         |
| -------------- | ------------------------------------------------------------------ |
| Entity         | Object with identity that persists across changes (User, Order)    |
| Value Object   | Immutable object defined by its attributes (Money, Email, Address) |
| Aggregate      | Cluster of entities with a root that enforces invariants           |
| Repository     | Abstraction for aggregate persistence                              |
| Domain Service | Logic that doesn't naturally belong to a single entity             |
| Domain Event   | Record of something that happened in the domain                    |

### Aggregate example

```go
// Order is the aggregate root
type Order struct {
    id     OrderID
    items  []LineItem
    status Status
}

// All mutations go through the root to enforce invariants
func (o *Order) AddItem(product ProductID, qty int, price Money) error {
    if o.status != StatusDraft {
        return errors.New("cannot modify a placed order")
    }
    if qty <= 0 {
        return errors.New("quantity must be positive")
    }
    o.items = append(o.items, LineItem{Product: product, Qty: qty, Price: price})
    return nil
}

func (o *Order) Total() Money {
    var total Money
    for _, item := range o.items {
        total = total.Add(item.Price.Multiply(item.Qty))
    }
    return total
}
```

### Value Object example

```go
type Money struct {
    Amount   int64  // cents
    Currency string
}

func NewMoney(amount int64, currency string) (Money, error) {
    if currency == "" {
        return Money{}, errors.New("currency required")
    }
    return Money{Amount: amount, Currency: currency}, nil
}

func (m Money) Add(other Money) Money {
    if m.Currency != other.Currency {
        panic("cannot add different currencies") // invariant
    }
    return Money{Amount: m.Amount + other.Amount, Currency: m.Currency}
}
```

### When to use

- Complex business domains with expert stakeholders
- Large teams where shared language prevents miscommunication
- Systems where business rules are the primary source of complexity

### When to skip

- Infrastructure-heavy systems (ETL pipelines, proxies)
- Small teams with simple domains
- When "the domain" is just CRUD operations

---

## Event-Driven Architecture

**Core idea:** Components communicate by producing and reacting to events rather than direct calls.

### Patterns

| Pattern                      | Description                                                     |
| ---------------------------- | --------------------------------------------------------------- |
| Event Notification           | Fire-and-forget; consumers react independently                  |
| Event-Carried State Transfer | Events carry enough data for consumers to act without callbacks |
| Event Sourcing               | Store events as the source of truth; derive state by replaying  |

### Simple event bus example

```go
type Event interface{ EventName() string }

type OrderPlaced struct {
    OrderID string
    Total   Money
}
func (e OrderPlaced) EventName() string { return "order.placed" }

type Bus struct {
    handlers map[string][]func(Event)
}

func (b *Bus) Subscribe(event string, handler func(Event)) {
    b.handlers[event] = append(b.handlers[event], handler)
}

func (b *Bus) Publish(e Event) {
    for _, h := range b.handlers[e.EventName()] {
        h(e)
    }
}
```

### Trade-offs

| Pro                                            | Con                                       |
| ---------------------------------------------- | ----------------------------------------- |
| Loose coupling between producers and consumers | Harder to trace execution flow            |
| Natural audit trail                            | Eventual consistency complexity           |
| Easy to add new reactions                      | Debugging distributed events is difficult |

---

## CQRS

**Core idea:** Separate the read model (queries) from the write model (commands).

### When it shines

- Read and write patterns differ significantly (e.g., write normalized, read denormalized)
- Read-heavy systems needing optimized query models
- Combined with event sourcing for complex domains

### Simple structure

```go
// Command side
type PlaceOrderCommand struct {
    CustomerID string
    Items      []ItemRequest
}

type CommandHandler struct {
    repo OrderRepository // write-optimized store
}

func (h *CommandHandler) Handle(cmd PlaceOrderCommand) error { /* ... */ }

// Query side
type OrderSummary struct {
    ID        string
    Total     string
    ItemCount int
    Status    string
}

type QueryHandler struct {
    db *sql.DB // read-optimized store, possibly denormalized
}

func (h *QueryHandler) OrdersByCustomer(customerID string) ([]OrderSummary, error) { /* ... */ }
```

### When to skip

- Uniform read/write patterns
- Simple CRUD where the read model mirrors the write model
- Small systems where the overhead of two models isn't justified

---

## Monolith-First

**Core idea:** Start with a well-structured monolith. Extract services only when there's a proven need.

### Why

- Monoliths are simpler to develop, deploy, test, and debug
- Service boundaries are hard to get right upfront — easier to refactor a monolith than merge services
- Most systems never need microservices

### Well-structured monolith

```
myapp/
├── cmd/server/main.go
├── internal/
│   ├── auth/          # bounded context as a package
│   │   ├── handler.go
│   │   ├── service.go
│   │   └── repo.go
│   ├── billing/       # another bounded context
│   │   ├── handler.go
│   │   ├── service.go
│   │   └── repo.go
│   └── shared/        # truly shared utilities
│       └── middleware.go
```

Each package has clear boundaries. If `billing` later needs independent scaling, extract it — the boundaries already exist.

### Extraction signals

Extract a service when:

- A component needs independent scaling
- A component needs independent deployment cadence
- A team needs full ownership and autonomy
- Different runtime requirements (language, resource profile)

---

## Microservices

**Core idea:** Independently deployable services organized around business capabilities.

### Prerequisites (be honest about these)

- Automated deployment pipeline
- Container orchestration
- Distributed tracing and logging
- Team structure aligned to services (Conway's Law)
- Operational maturity to handle distributed systems failure modes

### Common mistakes

- Distributed monolith: services tightly coupled via synchronous calls
- Shared database: negates independent deployability
- Too small: "nano-services" that add network overhead with no benefit
- Premature adoption: microservices before the domain is understood

### Right-sizing a service

A service should:

- Be owned by one team
- Be deployable independently
- Encapsulate a bounded context
- Communicate via well-defined APIs or events

---

## Vertical Slice Architecture

**Core idea:** Organize by feature, not by technical layer. Each slice contains everything needed for one use case.

### Structure

```
features/
├── place_order/
│   ├── handler.go      # HTTP handler
│   ├── command.go       # request/command struct
│   ├── service.go       # business logic
│   └── repo.go          # data access for this feature
├── cancel_order/
│   ├── handler.go
│   ├── command.go
│   └── service.go
└── list_orders/
    ├── handler.go
    ├── query.go
    └── read_model.go
```

### Trade-offs

| Pro                                             | Con                                       |
| ----------------------------------------------- | ----------------------------------------- |
| Changes are localized to one directory          | Some code duplication across slices       |
| Easy to understand a feature in isolation       | Shared concerns need careful handling     |
| Slices can be deleted without cascading changes | Less natural in framework-heavy codebases |

---

## Choosing an Architecture

### Decision matrix

| Factor               | Simple monolith | Clean/Hex | DDD      | Microservices |
| -------------------- | --------------- | --------- | -------- | ------------- |
| Team size            | 1-5             | 3-15      | 5-20     | 10+           |
| Domain complexity    | Low             | Medium    | High     | Varies        |
| Expected lifespan    | < 2 years       | 2-5 years | 5+ years | 5+ years      |
| Deployment needs     | Single          | Single    | Single   | Independent   |
| Operational maturity | Low             | Low-Med   | Medium   | High          |

### General guidance

1. **Start simple** — A well-organized monolith serves most projects
2. **Add structure as complexity grows** — Introduce Clean Architecture layers when you feel pain, not before
3. **Apply DDD for complex domains** — When business rules are the hard part, not the infrastructure
4. **Extract services for operational reasons** — Not for "cleanliness" or resume-driven development
5. **Combine patterns** — Clean Architecture inside a monolith with DDD tactical patterns is common and effective
