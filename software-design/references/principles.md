# Design Principles — Deep Dive

## Table of Contents

- [Single Responsibility Principle (SRP)](#single-responsibility-principle-srp)
- [Open/Closed Principle (OCP)](#openclosed-principle-ocp)
- [Liskov Substitution Principle (LSP)](#liskov-substitution-principle-lsp)
- [Interface Segregation Principle (ISP)](#interface-segregation-principle-isp)
- [Dependency Inversion Principle (DIP)](#dependency-inversion-principle-dip)
- [DRY — Don't Repeat Yourself](#dry--dont-repeat-yourself)
- [KISS — Keep It Simple](#kiss--keep-it-simple)
- [YAGNI — You Aren't Gonna Need It](#yagni--you-arent-gonna-need-it)
- [Composition Over Inheritance](#composition-over-inheritance)
- [Separation of Concerns](#separation-of-concerns)
- [Law of Demeter](#law-of-demeter)
- [Tell, Don't Ask](#tell-dont-ask)

---

## Single Responsibility Principle (SRP)

**A module should have one, and only one, reason to change.**

"Reason to change" means one stakeholder or actor whose requirements drive modifications.

### Anti-pattern

```go
type UserService struct {
    db   *sql.DB
    smtp *SMTPClient
}

func (s *UserService) Register(u User) error {
    // validates user
    // inserts into database
    // sends welcome email
    // logs audit trail
    return nil
}
```

Four reasons to change: validation rules, persistence schema, email provider, audit format.

### Applied

```go
type UserRegistrar struct {
    validator Validator
    repo      UserRepository
    notifier  Notifier
    auditor   Auditor
}

func (r *UserRegistrar) Register(u User) error {
    if err := r.validator.Validate(u); err != nil {
        return err
    }
    if err := r.repo.Save(u); err != nil {
        return err
    }
    r.notifier.Welcome(u)
    r.auditor.Log("user_registered", u.ID)
    return nil
}
```

Each collaborator changes for one reason. The orchestrator's only job is coordination.

### When to skip

If the "separated" pieces are 5-line functions used nowhere else, keep them as private methods. Premature extraction into separate types adds navigational complexity with no reuse benefit.

---

## Open/Closed Principle (OCP)

**Open for extension, closed for modification.**

Achieve via interfaces, strategy pattern, or plugin architectures — not by predicting every future need.

### Anti-pattern

```go
func CalculateDiscount(customerType string, amount float64) float64 {
    switch customerType {
    case "regular":
        return amount * 0.05
    case "premium":
        return amount * 0.10
    case "vip":
        return amount * 0.15
    // every new type requires modifying this function
    default:
        return 0
    }
}
```

### Applied

```go
type DiscountStrategy interface {
    Calculate(amount float64) float64
}

type PremiumDiscount struct{}
func (d PremiumDiscount) Calculate(amount float64) float64 { return amount * 0.10 }

func ApplyDiscount(s DiscountStrategy, amount float64) float64 {
    return s.Calculate(amount)
}
```

New customer types add a struct, not modify existing code.

### When to skip

If there are only 2-3 cases and they rarely change, a switch statement is simpler and more readable. Apply OCP when you see the switch growing or when the variation is a genuine extension point.

---

## Liskov Substitution Principle (LSP)

**Subtypes must be usable through the base type interface without surprises.**

Violations: throwing unexpected errors, ignoring method contracts, changing preconditions/postconditions.

### Classic violation

```go
type Rectangle struct {
    Width, Height float64
}

func (r *Rectangle) SetWidth(w float64)  { r.Width = w }
func (r *Rectangle) SetHeight(h float64) { r.Height = h }
func (r *Rectangle) Area() float64       { return r.Width * r.Height }

type Square struct{ Rectangle }

func (s *Square) SetWidth(w float64)  { s.Width = w; s.Height = w }
func (s *Square) SetHeight(h float64) { s.Width = h; s.Height = h }
// Breaks caller expectation: SetWidth shouldn't change Height
```

### Fix

Model by behavior, not taxonomy. Use a `Shape` interface with `Area()` instead of inheritance.

---

## Interface Segregation Principle (ISP)

**No client should be forced to depend on methods it does not use.**

### Anti-pattern

```go
type DataStore interface {
    Read(id string) ([]byte, error)
    Write(id string, data []byte) error
    Delete(id string) error
    Backup() error
    Migrate() error
}

// A read-only consumer must accept Backup() and Migrate() it never calls
func ProcessData(store DataStore) { /* only calls Read */ }
```

### Applied

```go
type Reader interface {
    Read(id string) ([]byte, error)
}

type Writer interface {
    Write(id string, data []byte) error
}

type ReadWriter interface {
    Reader
    Writer
}

func ProcessData(r Reader) { /* depends only on what it needs */ }
```

Go's implicit interface satisfaction makes ISP natural — define interfaces where they're consumed, not where they're implemented.

---

## Dependency Inversion Principle (DIP)

**High-level modules should not depend on low-level modules. Both should depend on abstractions.**

### Anti-pattern

```go
type OrderService struct {
    db *PostgresDB  // concrete dependency
}

func (s *OrderService) Place(o Order) error {
    return s.db.Insert("orders", o)  // tightly coupled to Postgres
}
```

### Applied

```go
type OrderRepository interface {
    Save(o Order) error
}

type OrderService struct {
    repo OrderRepository  // depends on abstraction
}

func (s *OrderService) Place(o Order) error {
    return s.repo.Save(o)  // testable, swappable
}
```

### When to skip

If there's genuinely only one implementation and no test double is needed, an interface adds ceremony. Introduce the abstraction when you need it (test doubles, second implementation).

---

## DRY — Don't Repeat Yourself

**Every piece of knowledge must have a single, unambiguous representation in the system.**

DRY is about knowledge duplication, not code duplication. Two identical-looking code blocks that change for different reasons are NOT violations.

### True violation

```go
// Tax rate hardcoded in three places
func CalcOrderTax(amount float64) float64  { return amount * 0.08 }
func CalcRefundTax(amount float64) float64  { return amount * 0.08 }
func DisplayTax(amount float64) string      { return fmt.Sprintf("%.2f", amount*0.08) }
```

### Not a violation

```go
// These look similar but serve different domains with different change reasons
func ValidateUserEmail(email string) bool   { return strings.Contains(email, "@") }
func ValidateVendorEmail(email string) bool { return strings.Contains(email, "@") }
// User validation may add domain whitelist; vendor may add verification step
```

### The Rule of Three

Wait until you see the same pattern three times before extracting. Two occurrences might be coincidence; three suggests a real abstraction.

---

## KISS — Keep It Simple

**The simplest solution that correctly handles current requirements wins.**

### Signals you've over-complicated

- You need a diagram to explain a single function
- Generic type parameters for a function called with one type
- Factory that produces one product
- Abstraction layers with no behavioral variation
- Config-driven behavior that's never reconfigured

### Applying KISS

Before adding complexity, ask: "What specific, current problem does this solve?" If the answer is "it might be useful later," apply YAGNI instead.

---

## YAGNI — You Aren't Gonna Need It

**Don't build functionality until it's needed.**

### Common YAGNI violations

- Adding a plugin system when there's one plugin
- Building a generic "event bus" for two events
- Creating an admin dashboard before there are users
- Adding caching before measuring performance
- Supporting multiple databases when you use one

### YAGNI does NOT mean

- Skip error handling
- Ignore security
- Write no tests
- Avoid good structure

It means: don't build features, abstractions, or extension points for requirements that don't exist yet.

---

## Composition Over Inheritance

**Favor composing objects from smaller pieces over extending base classes.**

### Why

- Inheritance creates tight coupling to parent implementation
- Deep hierarchies are fragile — changes at the top cascade
- Go has no traditional inheritance; composition is the idiomatic approach

### Pattern

```go
// Instead of inheriting from a base "Animal"
type Mover struct{ Speed float64 }
func (m Mover) Move() { /* ... */ }

type Eater struct{ Diet string }
func (e Eater) Eat() { /* ... */ }

type Dog struct {
    Mover
    Eater
    Name string
}
// Dog composes behaviors; easy to mix and match
```

---

## Separation of Concerns

**Each module addresses a distinct concern — a cohesive set of responsibilities.**

Classic separations: business logic vs persistence vs presentation vs transport vs configuration.

### Test: Can you describe the module without "and"?

- "Handles user authentication" — good
- "Handles user authentication and sends emails and logs analytics" — SoC violation

---

## Law of Demeter

**A method should only call methods on: itself, its parameters, objects it creates, its direct fields.**

### Violation

```go
user.GetAddress().GetCity().GetZipCode()  // "train wreck"
```

### Applied

```go
user.ZipCode()  // encapsulate the traversal
```

### When to skip

For data-transfer objects / value types where the chain is stable and carries no behavior, strict Demeter adds boilerplate with no encapsulation benefit.

---

## Tell, Don't Ask

**Tell objects what to do rather than asking for their state and deciding for them.**

### Ask (procedural)

```go
if account.Balance() >= amount {
    account.SetBalance(account.Balance() - amount)
}
```

### Tell (object-oriented)

```go
err := account.Withdraw(amount)
```

The object owns its invariants and enforces them internally.
