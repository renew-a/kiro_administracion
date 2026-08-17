# Implementation Plan: auth-login-register

## Overview

Implement a stateless JSON REST authentication layer on the existing Flask application factory. The work is divided into five groups: data model, password hasher, repository, schemas, services, and routes — followed by property-based tests and integration wiring. Each step builds on the previous and leaves no orphaned code.

All implementation uses **Python + Flask + SQLAlchemy + Flask-Bcrypt + pytest + Hypothesis**.

---

## Tasks

- [x] 1. Create the User model and database migration
  - [x] 1.1 Create `auth/models.py` with the `User` SQLAlchemy model
    - Define `id` (Integer, primary key), `username` (String(80), unique, not null), `email` (String(120), unique, not null), `password_hash` (String(128), not null)
    - Import `db` from `extensions`
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ]* 1.2 Write unit tests for the User model constraints
    - Verify that persisting a `User` without `username`, `email`, or `password_hash` raises an `IntegrityError`
    - Verify that persisting two users with the same `email` raises an `IntegrityError`
    - Verify that persisting two users with the same `username` raises an `IntegrityError`
    - _Requirements: 3.1, 3.2, 3.3_

- [x] 2. Implement the PasswordHasher component
  - [x] 2.1 Create `auth/password_hasher.py` with the `PasswordHasher` class
    - Implement `hash(plain: str) -> str` using `extensions.bcrypt.generate_password_hash`, decoded as UTF-8
    - Implement `verify(plain: str, hashed: str) -> bool` using `extensions.bcrypt.check_password_hash`
    - Raise `ValueError` when `hash` is called with an empty string or `None`
    - Return `False` (no exception) when `verify` is called with a non-bcrypt string
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ] 2.2 Write property test for Property 1 — password hash round-trip
    - **Property 1: For any plain-text password of 1–72 characters, `verify(plain, hash(plain))` SHALL return `True`**
    - **Validates: Requirements 4.4, 4.7**
    - Use `hypothesis.strategies.text(min_size=1, max_size=72)` as the strategy
    - Tag: `# Feature: auth-login-register, Property 1: Password hash round-trip`

  - [ ] 2.3 Write property test for Property 2 — wrong password is rejected by the hasher
    - **Property 2: For any two distinct passwords, `verify(wrong, hash(correct))` SHALL return `False`**
    - **Validates: Requirements 4.5**
    - Use `hypothesis.strategies.text` with `assume(p1 != p2)`
    - Tag: `# Feature: auth-login-register, Property 2: Invalid passwords are rejected by the hasher`

  - [ ]* 2.4 Write unit tests for PasswordHasher
    - Test `hash` returns a non-empty string for a valid password
    - Test `hash` raises `ValueError` for empty string and `None`
    - Test `verify` returns `True` for matching plain/hash pair
    - Test `verify` returns `False` for mismatched pair
    - Test `verify` returns `False` (no exception) for a non-bcrypt hash string
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 3. Implement the UserRepository
  - [x] 3.1 Create `auth/repository.py` with the `UserRepository` class
    - Implement `find_by_email(email: str) -> User | None` using SQLAlchemy ORM
    - Implement `find_by_username(username: str) -> User | None` using SQLAlchemy ORM
    - Implement `save(user: User) -> User` using `db.session.add` + `db.session.commit`
    - _Requirements: 3.4_

  - [ ]* 3.2 Write unit tests for UserRepository
    - Test `save` persists a user and assigns an `id`
    - Test `find_by_email` returns the correct user and `None` for missing emails
    - Test `find_by_username` returns the correct user and `None` for missing usernames
    - _Requirements: 3.4_

- [x] 4. Implement input validation schemas
  - [x] 4.1 Create `auth/schemas.py` with `RegisterSchema` and `LoginSchema`
    - `RegisterSchema.from_dict(data)`: validate `username` (non-empty after strip, max 80), `email` (non-empty, contains `@`, max 120), `password` (6–72 chars); collect all errors before raising `ValueError({field: message})`
    - `LoginSchema.from_dict(data)`: validate `email` (non-empty, contains `@`), `password` (non-empty); same multi-error collection pattern
    - Store validated, stripped values as instance attributes
    - _Requirements: 1.5, 1.6, 1.7, 1.8, 1.9, 2.4, 2.5, 2.6_

  - [ ]* 4.2 Write property test for Property 3 — whitespace usernames are rejected
    - **Property 3: For any `username` composed entirely of whitespace, `RegisterSchema.from_dict` SHALL raise `ValueError` and no user is persisted**
    - **Validates: Requirements 1.5**
    - Strategy: `hypothesis.strategies.text(alphabet=hypothesis.strategies.characters(whitelist_categories=("Zs",)), min_size=1)` or `st.just(" " * n)` for n ≥ 1
    - Tag: `# Feature: auth-login-register, Property 3: Registration rejects whitespace-only or empty usernames`

  - [ ]* 4.3 Write property test for Property 4 — malformed emails are rejected
    - **Property 4: For any `email` string without `@`, `RegisterSchema.from_dict` SHALL raise `ValueError` and no user is persisted**
    - **Validates: Requirements 1.6**
    - Strategy: `hypothesis.strategies.text().filter(lambda s: "@" not in s and len(s) > 0)`
    - Tag: `# Feature: auth-login-register, Property 4: Registration rejects malformed emails`

  - [ ]* 4.4 Write property test for Property 5 — out-of-range passwords are rejected
    - **Property 5: For any `password` with length outside [6, 72], `RegisterSchema.from_dict` SHALL raise `ValueError` and no user is persisted**
    - **Validates: Requirements 1.7**
    - Strategy: `st.one_of(st.text(max_size=5), st.text(min_size=73))`
    - Tag: `# Feature: auth-login-register, Property 5: Registration rejects out-of-range passwords`

  - [ ]* 4.5 Write property test for Property 6 — multi-field validation collects all errors
    - **Property 6: For any request with N ≥ 2 simultaneously invalid fields, the response body SHALL contain exactly N distinct error keys under `"errors"`**
    - **Validates: Requirements 1.8, 2.6**
    - Test both `RegisterSchema` and `LoginSchema` with multiple invalid fields at once; assert `len(errors) == N`
    - Tag: `# Feature: auth-login-register, Property 6: Multi-field validation collects all errors`

  - [ ]* 4.6 Write unit tests for RegisterSchema and LoginSchema
    - Test each field individually: missing, empty, too long, malformed
    - Test valid inputs produce schema objects with correct attribute values
    - Test non-JSON / absent body (`{}`) returns all required-field errors
    - _Requirements: 1.5, 1.6, 1.7, 1.8, 1.9, 2.4, 2.5, 2.6_

- [x] 5. Checkpoint — ensure model, hasher, repository, and schemas work end-to-end
  - Ensure all tests pass so far, ask the user if questions arise.

- [x] 6. Implement business logic services
  - [x] 6.1 Create `auth/services.py` with `RegisterService` and `LoginService`
    - `RegisterService.execute(schema)`: check duplicate email → `ValueError({"email": ...})`; check duplicate username → `ValueError({"username": ...})`; hash password via `PasswordHasher`; construct `User`; call `repo.save`; return persisted `User`
    - `LoginService.execute(schema)`: fetch user by email; if not found or `hasher.verify` returns `False` → `ValueError({"credentials": ...})`; return authenticated `User`
    - Accept `UserRepository` and `PasswordHasher` via constructor injection for testability
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.10, 2.1, 2.2, 2.3, 2.7, 3.4_

  - [ ]* 6.2 Write property test for Property 7 — duplicate email is always rejected
    - **Property 7: For any registered User, a subsequent `POST /auth/register` with the same `email` SHALL return HTTP 409 and SHALL NOT persist a second User**
    - **Validates: Requirements 1.3**
    - Use in-memory SQLite; generate arbitrary valid registration data with Hypothesis; call `RegisterService` twice with same email; assert second call raises `ValueError`
    - Tag: `# Feature: auth-login-register, Property 7: Duplicate email is always rejected`

  - [ ]* 6.3 Write property test for Property 8 — duplicate username is always rejected
    - **Property 8: For any registered User, a subsequent `POST /auth/register` with the same `username` SHALL return HTTP 409 and SHALL NOT persist a second User**
    - **Validates: Requirements 1.4**
    - Same pattern as P7, varying username instead of email
    - Tag: `# Feature: auth-login-register, Property 8: Duplicate username is always rejected`

  - [ ]* 6.4 Write property test for Property 9 — successful login returns consistent user data
    - **Property 9: For any User registered via `RegisterService`, a subsequent `LoginService.execute` with the same email and original password SHALL return the same `id` and `username`**
    - **Validates: Requirements 2.1**
    - Generate valid credentials with Hypothesis; register then login; assert `id` and `username` match
    - Tag: `# Feature: auth-login-register, Property 9: Successful login returns consistent user data`

  - [ ]* 6.5 Write property test for Property 10 — wrong password always produces a credentials error
    - **Property 10: For any existing User and any string that differs from their registered password, `LoginService.execute` SHALL raise `ValueError({"credentials": ...})`**
    - **Validates: Requirements 2.3**
    - Use `assume(wrong_password != correct_password)`; assert raised `ValueError` contains `"credentials"` key
    - Tag: `# Feature: auth-login-register, Property 10: Wrong password always produces 401`

  - [ ]* 6.6 Write unit tests for RegisterService and LoginService
    - Test happy-path registration: user is persisted with hashed password, plain text absent
    - Test duplicate email path: `ValueError` raised, no second user persisted
    - Test duplicate username path: `ValueError` raised, no second user persisted
    - Test happy-path login: correct credentials → user returned
    - Test unknown email path: `ValueError` with `credentials` key
    - Test wrong password path: `ValueError` with `credentials` key
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.10, 2.1, 2.2, 2.3, 2.7_

- [x] 7. Implement Flask routes and wire the blueprint
  - [x] 7.1 Create `auth/__init__.py` (empty package marker) and `auth/routes.py` with the `auth_bp` blueprint
    - Register blueprint at prefix `/auth`
    - `POST /auth/register`: parse JSON body with `request.get_json(silent=True) or {}`; call `RegisterSchema.from_dict` → catch `ValueError` → 422; call `RegisterService.execute` → catch `ValueError` → 409; catch `sqlalchemy.exc.IntegrityError` → 409; catch broad `Exception` → 500; on success return 201 `{"message": "Usuario registrado.", "id": <int>}`
    - `POST /auth/login`: same JSON parsing; call `LoginSchema.from_dict` → catch `ValueError` → 422; call `LoginService.execute` → catch `ValueError` → 401; catch broad `Exception` → 500; on success return 200 `{"message": "Login exitoso.", "id": <int>, "username": <str>}`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.8, 3.5_

  - [ ]* 7.2 Write route-level unit tests (pytest-flask)
    - Test 201 on valid register payload
    - Test 409 on duplicate email and duplicate username
    - Test 422 on each invalid field for register
    - Test 422 on missing/non-JSON body for register
    - Test 200 on valid login payload
    - Test 401 on unknown email and wrong password
    - Test 422 on invalid email and missing password for login
    - Test 500 when `db.session.commit` is mocked to raise `OperationalError` (no internal detail leaked)
    - _Requirements: 1.1–1.9, 2.1–2.8, 3.5_

- [x] 8. Generate and apply the database migration
  - [x] 8.1 Verify `app.py` imports `auth.models` so Flask-Migrate detects the `User` table
    - Ensure the `User` model is imported inside `create_app` before `migrate.init_app` is called (or import it at module level in `auth/models.py` so it registers with `db.metadata`)
    - _Requirements: 3.1, 3.2, 3.3_

- [x] 9. Final checkpoint — full test suite must pass
  - Run `pytest --tb=short` (in-memory SQLite config). All unit, property, and integration tests must be green.
  - Ensure all tests pass, ask the user if questions arise.

---

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; they do not block integration.
- Each task references specific requirements for full traceability.
- Property tests use **Hypothesis** with `@given`; the in-memory SQLite URI is `"sqlite://"` and bcrypt work factor can be reduced to 4 in test config for speed.
- The `PasswordHasher`, `UserRepository`, and both services should be instantiated inside the route handlers (or via a simple factory) — no DI framework is required.
- `auth/routes.py` already imported in `app.py` as `from auth.routes import auth_bp`; the blueprint must be created in exactly that module.

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1", "3.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "3.2", "4.1"] },
    { "id": 3, "tasks": ["4.2", "4.3", "4.4", "4.5", "4.6"] },
    { "id": 4, "tasks": ["6.1"] },
    { "id": 5, "tasks": ["6.2", "6.3", "6.4", "6.5", "6.6"] },
    { "id": 6, "tasks": ["7.1"] },
    { "id": 7, "tasks": ["7.2", "8.1"] }
  ]
}
```
