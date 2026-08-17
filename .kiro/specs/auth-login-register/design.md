# Design Document — auth-login-register

## Overview

This feature implements a stateless JSON REST authentication layer for the Flask application, exposing two endpoints:

- `POST /auth/register` — creates a new user account
- `POST /auth/login` — authenticates an existing user

The implementation follows a strict layered architecture: routes handle HTTP concerns, schemas validate input, services contain business logic, the repository manages persistence, and a dedicated component handles password hashing. No session tokens or JWTs are issued; the endpoints confirm identity and return the user's `id` and `username`.

The codebase already has all layers scaffolded. The design covers the contracts, data flow, error handling, and correctness properties that govern the complete request lifecycle.

---

## Architecture

```mermaid
flowchart TD
    Client -->|POST /auth/register\nPOST /auth/login| Routes["auth/routes.py\n(Flask Blueprint)"]
    Routes -->|from_dict()| Schemas["auth/schemas.py\n(RegisterSchema / LoginSchema)"]
    Schemas -->|raises ValueError on invalid input| Routes
    Routes -->|execute(schema)| Services["auth/services.py\n(RegisterService / LoginService)"]
    Services -->|find_by_email\nfind_by_username\nsave| Repository["auth/repository.py\n(UserRepository)"]
    Services -->|hash / verify| Hasher["auth/password_hasher.py\n(PasswordHasher)"]
    Repository -->|SQLAlchemy ORM| DB[(SQLite / PostgreSQL)]
    Hasher -->|Flask-Bcrypt| Bcrypt["extensions.bcrypt"]
```

**Request flow — Register:**
1. Route receives JSON body, calls `RegisterSchema.from_dict()`.
2. Schema validates fields; raises `ValueError` with an error dict on failure → 422.
3. Route calls `RegisterService.execute(schema)`.
4. Service checks for duplicate email/username via repository → raises `ValueError` → 409.
5. Service hashes the password via `PasswordHasher.hash()`, constructs a `User`, calls `repository.save()`.
6. Route returns 201 with `{message, id}`.

**Request flow — Login:**
1. Route receives JSON body, calls `LoginSchema.from_dict()`.
2. Schema validates fields → 422 on failure.
3. Route calls `LoginService.execute(schema)`.
4. Service fetches user by email; if not found or password mismatch → raises `ValueError` → 401.
5. Route returns 200 with `{message, id, username}`.

---

## Components and Interfaces

### `auth/routes.py` — Flask Blueprint

Registers the `auth` blueprint at `/auth`. Each route:
- Parses the JSON body with `request.get_json(silent=True) or {}` to handle missing/non-JSON bodies gracefully.
- Delegates all validation and business logic to schemas and services.
- Maps `ValueError` from schemas → 422 and from services → 409 (register) / 401 (login).
- Catches unhandled exceptions for 500 responses without leaking internals.

```python
# Public contract
POST /auth/register  →  201 {"message": "Usuario registrado.", "id": <int>}
                     |   409 {"errors": {"email"|"username": <str>}}
                     |   422 {"errors": {<field>: <message>, ...}}

POST /auth/login     →  200 {"message": "Login exitoso.", "id": <int>, "username": <str>}
                     |   401 {"errors": {"credentials": <str>}}
                     |   422 {"errors": {<field>: <message>, ...}}
                     |   500 {"errors": {"server": "Error interno del servidor."}}
```

### `auth/schemas.py` — Input Validation

**`RegisterSchema.from_dict(data)`**
- Strips and validates `username`: must be non-empty after stripping, 1–80 chars.
- Validates `email`: must be non-empty, contain `@`, max 120 chars.
- Validates `password`: length 6–72 chars (bcrypt hard limit is 72 bytes).
- Collects all field errors before raising; raises `ValueError({field: message, ...})`.

**`LoginSchema.from_dict(data)`**
- Validates `email`: non-empty, contains `@`.
- Validates `password`: non-empty.
- Same multi-error collection pattern.

### `auth/services.py` — Business Logic

**`RegisterService.execute(schema)`**
- Checks `repo.find_by_email(schema.email)` → raises `ValueError({"email": ...})` on duplicate.
- Checks `repo.find_by_username(schema.username)` → raises `ValueError({"username": ...})` on duplicate.
- Constructs `User(username, email, password_hash=hasher.hash(password))`.
- Calls `repo.save(user)` and returns the persisted `User`.

**`LoginService.execute(schema)`**
- Calls `repo.find_by_email(schema.email)`.
- If user not found or `hasher.verify(password, user.password_hash)` returns `False` → raises `ValueError({"credentials": ...})`.
- Returns the authenticated `User`.

### `auth/repository.py` — Data Access

```python
class UserRepository:
    def find_by_email(self, email: str) -> User | None
    def find_by_username(self, username: str) -> User | None
    def save(self, user: User) -> User        # db.session.add + commit
```

The repository is the sole point of database interaction for the auth domain. No raw SQL is used; all queries go through SQLAlchemy ORM.

### `auth/password_hasher.py` — Password Security

```python
class PasswordHasher:
    def hash(self, plain: str) -> str         # bcrypt.generate_password_hash → decode utf-8
    def verify(self, plain: str, hashed: str) -> bool  # bcrypt.check_password_hash
```

Wraps `extensions.bcrypt` (Flask-Bcrypt). All bcrypt operations are isolated here; no other component imports or calls bcrypt directly.

### `extensions.py` — Shared Extension Instances

```python
db       = SQLAlchemy()
migrate  = Migrate()
bcrypt   = Bcrypt()
```

Initialized once in `create_app()` via the application factory pattern.

### `app.py` — Application Factory

`create_app(config=None)` initialises extensions, registers the `auth_bp` blueprint, and sets default SQLite URI for development. Production overrides `SQLALCHEMY_DATABASE_URI` with a PostgreSQL DSN.

---

## Data Models

### `User` (SQLAlchemy model — `auth/models.py`)

| Column          | Type         | Constraints                        |
|-----------------|--------------|------------------------------------|
| `id`            | Integer      | primary key, auto-increment        |
| `username`      | String(80)   | unique=True, nullable=False        |
| `email`         | String(120)  | unique=True, nullable=False        |
| `password_hash` | String(128)  | nullable=False                     |

**Design decisions:**
- `password_hash` length 128 is sufficient for bcrypt output (`$2b$12$...` is 60 chars); the extra headroom accommodates future algorithm migrations.
- Unique constraints exist at both the application layer (service checks) and the database layer (column constraints), providing defence-in-depth against race conditions.
- The plain-text password is never stored; it is hashed immediately in `RegisterService` before the `User` object is constructed.

### Validation Constraints Summary

| Field      | Schema         | Rule                                              |
|------------|----------------|---------------------------------------------------|
| `username` | RegisterSchema | non-empty after strip, max 80 chars               |
| `email`    | Both schemas   | non-empty, contains `@`, max 120 chars            |
| `password` | RegisterSchema | 6–72 chars                                        |
| `password` | LoginSchema    | non-empty                                         |

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Password hash round-trip

*For any* plain-text password of 1–72 characters, hashing it with `PasswordHasher.hash` and then verifying the result with `PasswordHasher.verify` SHALL return `True`.

**Validates: Requirements 4.4, 4.7**

---

### Property 2: Invalid passwords are rejected by the hasher

*For any* plain-text password and a hash that was generated from a *different* plain-text password, `PasswordHasher.verify` SHALL return `False`.

**Validates: Requirements 4.5**

---

### Property 3: Registration rejects whitespace-only or empty usernames

*For any* `POST /auth/register` request whose `username` field is composed entirely of whitespace (or is absent), the API SHALL return HTTP 422 and the task list (user table) SHALL remain unchanged.

**Validates: Requirements 1.5**

---

### Property 4: Registration rejects malformed emails

*For any* `POST /auth/register` request whose `email` field does not contain `@` (or is absent/empty), the API SHALL return HTTP 422 and no new User SHALL be persisted.

**Validates: Requirements 1.6**

---

### Property 5: Registration rejects out-of-range passwords

*For any* `POST /auth/register` request whose `password` field has a length outside [6, 72], the API SHALL return HTTP 422 and no new User SHALL be persisted.

**Validates: Requirements 1.7**

---

### Property 6: Multi-field validation collects all errors

*For any* `POST /auth/register` or `POST /auth/login` request where N fields (N ≥ 2) are simultaneously invalid, the response body SHALL contain exactly N distinct error keys under `"errors"`, one per invalid field.

**Validates: Requirements 1.8, 2.6**

---

### Property 7: Duplicate email is always rejected

*For any* registered User, a subsequent `POST /auth/register` request using the same `email` (regardless of other fields) SHALL return HTTP 409 and SHALL NOT persist a second User with that email.

**Validates: Requirements 1.3**

---

### Property 8: Duplicate username is always rejected

*For any* registered User, a subsequent `POST /auth/register` request using the same `username` (regardless of other fields) SHALL return HTTP 409 and SHALL NOT persist a second User with that username.

**Validates: Requirements 1.4**

---

### Property 9: Successful login returns consistent user data

*For any* User that was registered via `POST /auth/register`, a subsequent `POST /auth/login` with the same `email` and original plain-text `password` SHALL return HTTP 200 with the same `id` and `username` that were stored during registration.

**Validates: Requirements 2.1**

---

### Property 10: Wrong password always produces 401

*For any* existing User and *any* string that differs from their registered password, `POST /auth/login` SHALL return HTTP 401 with `{"errors": {"credentials": ...}}`.

**Validates: Requirements 2.3**

---

## Error Handling

### Validation errors (HTTP 422)

Raised by `Schema.from_dict()` as `ValueError({field: message})`. The route catches this and returns:

```json
{"errors": {"<field>": "<message>", ...}}
```

All field errors are collected before raising (no fail-fast), so the client receives a complete picture in a single response.

### Business logic errors (HTTP 409 / 401)

Raised by services as `ValueError({key: message})`:
- `RegisterService` → 409 for duplicate email or username.
- `LoginService` → 401 for unknown email or wrong password. Both cases return the same generic message to prevent user-enumeration attacks.

### Database errors (HTTP 500)

Unhandled exceptions from SQLAlchemy (e.g., connection failure, unique constraint race condition) propagate to the route handler. The route MUST catch these with a broad `except Exception` guard and return:

```json
{"errors": {"server": "Error interno del servidor."}}
```

No stack traces, query details, or internal state are included in the response body.

### Race condition on unique constraint

If two concurrent requests pass the service-level duplicate check simultaneously, the database unique constraint fires a `sqlalchemy.exc.IntegrityError`. This is caught at the route level and mapped to HTTP 409 — the same response the client would receive from the service-level check.

---

## Testing Strategy

### Test framework

- **pytest** with **pytest-flask** for test fixtures and the application context.
- **Hypothesis** (Python) for property-based tests — each property test runs a minimum of 100 iterations.
- In-memory SQLite (`SQLALCHEMY_DATABASE_URI = "sqlite://"`) for fast, isolated unit/property tests.
- No real bcrypt rounds are needed for pure unit tests; tests that exercise `PasswordHasher` use the real implementation (bcrypt is fast enough for 100 iterations with the default work factor 12 being reducible to 4 in test config).

### Unit tests

Focused on specific examples, edge cases, and error conditions:

- `RegisterSchema.from_dict` with each individual invalid field.
- `LoginSchema.from_dict` with each individual invalid field.
- `RegisterService` duplicate-email path, duplicate-username path, and happy path.
- `LoginService` unknown-email path, wrong-password path, and happy path.
- `UserRepository.save` stores a user and `find_by_email` / `find_by_username` retrieve it.
- Route-level HTTP status codes and response body shapes for all documented outcomes.

### Property-based tests (Hypothesis)

Each property corresponds directly to a Correctness Property above and is tagged:

```
# Feature: auth-login-register, Property <N>: <property_text>
```

| Property | What varies | What is asserted |
|----------|-------------|------------------|
| P1: Password hash round-trip | Any printable string 1–72 chars | `verify(plain, hash(plain)) is True` |
| P2: Wrong password → False | Two distinct passwords | `verify(wrong, hash(correct)) is False` |
| P3: Whitespace username rejected | Strings of only whitespace chars | `from_dict` raises `ValueError`; user table unchanged |
| P4: Malformed email rejected | Strings without `@` | `from_dict` raises `ValueError`; no persistence |
| P5: Out-of-range password rejected | Strings of length 0–5 and 73+ | `from_dict` raises `ValueError`; no persistence |
| P6: Multi-field errors complete | Combinations of invalid fields | `len(errors) == N invalid fields` |
| P7: Duplicate email rejected | Arbitrary valid registration data, re-used email | HTTP 409; user count unchanged |
| P8: Duplicate username rejected | Arbitrary valid registration data, re-used username | HTTP 409; user count unchanged |
| P9: Login round-trip | Any valid registration payload | Login with same credentials returns same `id`/`username` |
| P10: Wrong password → 401 | Any existing user + any differing password string | HTTP 401 with credentials error |

### Integration tests

- Full register → login cycle against a real (test) database.
- Unique constraint enforcement: verify HTTP 409 on duplicate email/username at the database level.
- Database unavailability: mock `db.session.commit` to raise `sqlalchemy.exc.OperationalError` and assert HTTP 500 with no leaked details.
