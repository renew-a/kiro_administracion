# Project Steering — Flask Admin API

## Stack

- Python 3.13 · Flask 3.1 · SQLAlchemy 3.1 · Flask-Migrate 4 · Flask-Bcrypt 1.0
- pytest 8.3 · Hypothesis 6.13
- Dev DB: SQLite (`sqlite:///app.db`) · Prod DB: PostgreSQL (via `db.py`)
- Venv: `venv/Scripts/python.exe` (Windows)

## Project Structure

```
admin/
├── app.py                  # application factory (create_app)
├── extensions.py           # shared extension instances: db, migrate, bcrypt
├── db.py                   # one-off PostgreSQL DB creation script
├── conftest.py             # pytest fixtures (app, client)
├── requirements.txt        # pinned dependencies
├── auth/
│   ├── __init__.py
│   ├── models.py           # User SQLAlchemy model
│   ├── schemas.py          # RegisterSchema, LoginSchema (input validation)
│   ├── repository.py       # UserRepository (data access)
│   ├── password_hasher.py  # PasswordHasher (bcrypt wrapper)
│   ├── register_service.py # RegisterService (business logic)
│   ├── login_service.py    # LoginService (business logic)
│   └── routes.py           # auth_bp Blueprint at /auth
└── tests/
    ├── test_models.py
    ├── test_password_hasher.py
    ├── test_repository.py
    ├── test_schemas.py
    └── test_routes_integration.py
```

## Architecture

Strict layered architecture. Each layer has one responsibility:

```
routes → schemas → services → repository → models
                 ↘ password_hasher ↗
```

- **routes**: HTTP in/out only. Parses JSON, maps exceptions to status codes, returns JSON.
- **schemas**: Input validation. `from_dict(data)` collects all errors before raising `ValueError(dict)`.
- **services**: Business logic. One class per use case (SRP). Constructor-injected `repo` + `hasher`.
- **repository**: DB queries only via SQLAlchemy ORM. No raw SQL.
- **models**: SQLAlchemy models. No business logic.
- **password_hasher**: Sole point of bcrypt usage. No other file imports bcrypt directly.
- **extensions.py**: Single source of truth for `db`, `migrate`, `bcrypt` instances.

## Coding Principles

- **SOLID**: one class per use case, constructor injection for dependencies.
- **DRY**: extract repeated logic to helpers (e.g. `_str_field`, `_deps`, `_SERVER_ERROR`).
- **KISS**: no over-engineering — no DI framework, no base classes unless genuinely needed.
- **No comments or docstrings**: code must be self-explanatory through naming.

## Adding a New Feature

1. Create a new package `feature_name/` with `__init__.py`.
2. Add the model to `feature_name/models.py`, import it in `create_app` before `migrate.init_app`.
3. Follow the layer order: `models → repository → schemas → service(s) → routes`.
4. Register the blueprint in `create_app` via `from feature_name.routes import feature_bp`.
5. Run `flask db migrate -m "description"` then `flask db upgrade`.

## Error Handling Convention

| Source | Exception | HTTP |
|---|---|---|
| Schema `from_dict` | `ValueError(dict)` | 422 |
| Service (duplicate/conflict) | `ValueError(dict)` | 409 (register) / 401 (login) |
| SQLAlchemy `IntegrityError` | caught in route | 409 |
| Any other `Exception` | caught in route | 500 — never leak internals |

Response envelope:
- Success: `{"message": "...", ...fields}`
- Error: `{"errors": {"field": "message"}}` or `{"errors": {"server": "..."}}`

## Testing

Run tests: `venv\Scripts\python.exe -m pytest --tb=short`

- **conftest.py** provides `app` and `client` fixtures using in-memory SQLite + `BCRYPT_LOG_ROUNDS=4`.
- Unit tests go in `tests/test_<module>.py`.
- Integration tests use `client.post(url, data=json.dumps(payload), content_type="application/json")`.
- Property-based tests use Hypothesis `@given` with the tag `# Feature: <name>, Property <N>: <text>`.
- No mocking of the DB layer in unit tests — use in-memory SQLite with a real app context.

## Dependencies

Add to `requirements.txt` with exact pinned versions (`package==x.y.z`).
Do not use open ranges (`>=`, `~=`).
