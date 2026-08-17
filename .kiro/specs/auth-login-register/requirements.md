# Requirements Document

## Introduction

Esta funcionalidad agrega autenticación de usuarios a la aplicación Flask mediante dos endpoints REST (JSON): registro (`POST /auth/register`) e inicio de sesión (`POST /auth/login`). El código base ya cuenta con la estructura de capas (modelo, repositorio, servicio, esquema, rutas), por lo que los requisitos cubren el comportamiento observable end-to-end de ambas operaciones.

## Glossary

- **API**: La aplicación Flask que expone los endpoints REST.
- **User**: Entidad persistida en la base de datos con los campos `id`, `username`, `email` y `password_hash`.
- **RegisterSchema**: Objeto de validación que recibe `username`, `email` y `password` desde el cuerpo JSON de la petición de registro.
- **LoginSchema**: Objeto de validación que recibe `email` y `password` desde el cuerpo JSON de la petición de inicio de sesión.
- **UserRepository**: Capa de acceso a datos responsable de consultar y persistir entidades `User`.
- **PasswordHasher**: Componente responsable de generar y verificar hashes de contraseña usando bcrypt.
- **RegisterService**: Servicio que orquesta la lógica de negocio del registro.
- **LoginService**: Servicio que orquesta la lógica de autenticación.

---

## Requirements

### Requirement 1: Registro de usuario

**User Story:** As a Client, I want to create a new account by providing a username, email, and password, so that I can access the application with my own credentials.

#### Acceptance Criteria

1. WHEN the Client sends a `POST /auth/register` request with a valid `username` (6–20 characters), a valid `email` (contains `@`, max 120 characters), and a valid `password` (6–23 characters), 

THE API SHALL persist a new User with the provided `username` and `email`, and store the bcrypt hash of `password` in `password_hash`.

2. WHEN a new User is successfully persisted, THE API SHALL return HTTP 201 with a JSON body containing `"message": "Usuario registrado."` and the new `"id"` of the User.

3. WHEN the Client sends a `POST /auth/register` request with an `email` that already exists in the database, THE API SHALL return HTTP 409 with a JSON body containing `{"errors": {"email": "El correo ya está registrado."}}` and SHALL NOT persist a duplicate User.

4. WHEN the Client sends a `POST /auth/register` request with a `username` that already exists in the database, THE API SHALL return HTTP 409 with a JSON body containing `{"errors": {"username": "El nombre de usuario ya existe."}}` and SHALL NOT persist a duplicate User.

5. IF the Client sends a `POST /auth/register` request with a missing, empty, or whitespace-only `username`, or a `username` exceeding 80 characters, THEN THE API SHALL return HTTP 422 with a JSON body containing `{"errors": {"username": "El nombre de usuario es obligatorio."}}`.

6. IF the Client sends a `POST /auth/register` request with a missing, empty, malformed `email` (no `@` character), or an `email` exceeding 120 characters, THEN THE API SHALL return HTTP 422 with a JSON body containing `{"errors": {"email": "Correo electrónico inválido."}}`.

7. IF the Client sends a `POST /auth/register` request with a `password` shorter than 6 characters or longer than 72 characters, THEN THE API SHALL return HTTP 422 with a JSON body containing `{"errors": {"password": "La contraseña debe tener al menos 6 caracteres."}}`.

8. IF the Client sends a `POST /auth/register` request where multiple fields are invalid simultaneously, THEN THE API SHALL return HTTP 422 with a JSON body containing `{"errors": {...}}` with a key for each invalid field, and SHALL NOT persist any User.

9. IF the Client sends a `POST /auth/register` request with a non-JSON body or an absent body, THEN THE API SHALL return HTTP 422 with a JSON body containing `{"errors": {...}}` listing all required fields as missing.

10. THE API SHALL store the `password` exclusively as a bcrypt hash in `password_hash` and SHALL NOT persist the plain-text password anywhere.

---

### Requirement 2: Inicio de sesión

**User Story:** As a Client, I want to authenticate with my email and password, so that I can confirm my identity and receive my user information.

#### Acceptance Criteria

1. WHEN the Client sends a `POST /auth/login` request with an `email` that matches an existing User and a `password` that matches the stored `password_hash`, THE API SHALL return HTTP 200 with a JSON body containing `"message": "Login exitoso."`, `"id"` of the User, and `"username"` of the User.

2. IF the Client sends a `POST /auth/login` request with an `email` that does not match any existing User, THEN THE API SHALL return HTTP 401 with a JSON body containing `{"errors": {"credentials": "Correo o contraseña incorrectos."}}`.

3. IF the Client sends a `POST /auth/login` request with a correct `email` but an incorrect `password`, THEN THE API SHALL return HTTP 401 with a JSON body containing `{"errors": {"credentials": "Correo o contraseña incorrectos."}}`.

4. IF the Client sends a `POST /auth/login` request with a missing, empty, or malformed `email` (no `@` character), THEN THE API SHALL return HTTP 422 with a JSON body containing `{"errors": {"email": "Correo electrónico inválido."}}`.

5. IF the Client sends a `POST /auth/login` request with a missing or empty `password`, THEN THE API SHALL return HTTP 422 with a JSON body containing `{"errors": {"password": "La contraseña es obligatoria."}}`.

6. IF the Client sends a `POST /auth/login` request where both `email` and `password` are invalid simultaneously, THEN THE API SHALL return HTTP 422 with a JSON body containing `{"errors": {...}}` with a key for each invalid field.

7. THE API SHALL verify passwords by comparing the provided value against the stored bcrypt hash and SHALL NOT store or compare plain-text passwords at any layer.

8. IF the database is unavailable when processing a `POST /auth/login` request, THEN THE API SHALL return HTTP 500 and SHALL NOT expose internal error details in the response body.

---

### Requirement 3: Integridad del modelo de datos

**User Story:** As a developer, I want the User model to enforce uniqueness and non-null constraints at the database level, so that data integrity is guaranteed even outside of the application layer.

#### Acceptance Criteria

1. THE User model SHALL define the `username` column as `String(80)` with `unique=True` and `nullable=False` constraints at the database level.

2. THE User model SHALL define the `email` column as `String(120)` with `unique=True` and `nullable=False` constraints at the database level.

3. THE User model SHALL define the `password_hash` column as `String(128)` with `nullable=False` at the database level.

4. IF the RegisterService has confirmed no duplicate `email` or `username` exists, THEN THE UserRepository SHALL persist the User to the database.

5. IF a database-level unique constraint violation occurs during a `POST /auth/register` request (e.g., a race condition bypasses the service check), THEN THE API SHALL return HTTP 409 and SHALL NOT persist partial User data.

---

### Requirement 4: Hashing y seguridad de contraseñas

**User Story:** As a security-conscious developer, I want all password hashing and verification to go through a single dedicated component, so that the algorithm can be changed in one place without modifying other layers.

#### Acceptance Criteria

1. THE PasswordHasher SHALL generate password hashes using the bcrypt algorithm provided by Flask-Bcrypt.

2. WHEN `PasswordHasher.hash` is called with a plain-text password of 1–72 characters, THE PasswordHasher SHALL return a non-empty UTF-8 decoded bcrypt hash string.

3. IF `PasswordHasher.hash` is called with an empty string or `None`, THEN THE PasswordHasher SHALL raise a `ValueError`.

4. WHEN `PasswordHasher.verify` is called with a plain-text password and a previously generated hash of that same password, THE PasswordHasher SHALL return `True`.

5. WHEN `PasswordHasher.verify` is called with a plain-text password and a hash generated from a different password, THE PasswordHasher SHALL return `False`.

6. IF `PasswordHasher.verify` is called with a string that is not a valid bcrypt hash, THEN THE PasswordHasher SHALL return `False` without raising an exception.

7. FOR ALL valid plain-text passwords (1–72 characters), hashing and then verifying SHALL return `True` (round-trip property).
