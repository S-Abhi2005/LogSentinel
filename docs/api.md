# LogSentinel — REST API Reference

Base URL Prefix: `/api/v1`

All responses use JSON format. Date-time fields follow ISO 8601 UTC format (`YYYY-MM-DDTHH:MM:SSZ`).

---

## 1. Authentication (`/api/v1/auth`)

### `POST /api/v1/auth/login`
- **Description**: Authenticate with email and password to receive a JWT access token.
- **Request Body**:
  ```json
  {
    "email": "engineer@logsentinel.local",
    "password": "EngineerSecurePass123!"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user_id": "b3e34320-...",
    "email": "engineer@logsentinel.local",
    "full_name": "Bob Engineer",
    "role": "engineer"
  }
  ```

### `GET /api/v1/auth/me`
- **Description**: Return current authenticated user profile.
- **Headers**: `Authorization: Bearer <token>`

### `POST /api/v1/auth/change-password`
- **Description**: Update current user's password.
- **Request Body**: `{"current_password": "...", "new_password": "..."}`

---

## 2. Log Ingestion & Explorer (`/api/v1/logs`)

### `POST /api/v1/logs/ingest`
- **Description**: Ingest a single log event. Requires a service-specific API key.
- **Headers**: `X-API-Key: ls_live_<secret>`
- **Request Body**:
  ```json
  {
    "service_name": "payment-service",
    "environment": "production",
    "severity": "ERROR",
    "message": "Payment gateway timeout connecting to stripe.com",
    "source": "payment-worker",
    "trace_id": "trc-982412",
    "metadata": {
      "duration_ms": 5002,
      "retry_attempt": 3
    }
  }
  ```
- **Response** (`201 Created`): Returns created `LogResponse` object.

### `POST /api/v1/logs/ingest/batch`
- **Description**: Batch ingest up to 500 log events.
- **Headers**: `X-API-Key: ls_live_<secret>`
- **Request Body**:
  ```json
  {
    "events": [ ... ]
  }
  ```
- **Response** (`202 Accepted`): Returns `{"accepted": 20, "failed": 0, "errors": [], "correlation_id": "..."}`.

### `GET /api/v1/logs`
- **Description**: Paginated query of logs with filters.
- **Query Parameters**:
  - `service_name`: string
  - `environment`: `production`, `staging`, etc.
  - `severity`: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  - `search`: string keyword search
  - `trace_id`: string
  - `start_time`, `end_time`: ISO timestamps
  - `page`: integer (default `1`)
  - `page_size`: integer (default `50`, max `200`)
  - `sort_order`: `desc` or `asc`

### `GET /api/v1/logs/export`
- **Description**: Stream authorized filtered logs directly as a CSV file attachment.

---

## 3. Incident Management (`/api/v1/incidents`)

### `GET /api/v1/incidents`
- **Description**: List all triggered incidents with status and severity filters.

### `GET /api/v1/incidents/{incident_id}`
- **Description**: Retrieve incident details including timeline events, comments, and related logs.

### Lifecycle State Transitions:
- `POST /api/v1/incidents/{id}/acknowledge`: Mark incident `ACKNOWLEDGED`.
- `POST /api/v1/incidents/{id}/investigate`: Mark incident `INVESTIGATING`.
- `POST /api/v1/incidents/{id}/resolve?reason=...`: Mark incident `RESOLVED`.
- `POST /api/v1/incidents/{id}/reopen?reason=...`: Reopen resolved incident back to `OPEN`.
- `POST /api/v1/incidents/{id}/assign`: Assign incident to engineer.
- `POST /api/v1/incidents/{id}/comments`: Post investigation note.

---

## 4. Detection Rules (`/api/v1/rules`)

- `GET /api/v1/rules`: List all detection policies.
- `POST /api/v1/rules`: Create a new detection rule (Super Admin).
- `PATCH /api/v1/rules/{rule_id}`: Update rule or toggle `is_enabled`.
- `DELETE /api/v1/rules/{rule_id}`: Disable or delete rule safely.

---

## 5. Services & Ingestion Keys (`/api/v1/services`)

- `GET /api/v1/services`: List services with real-time health indicators.
- `POST /api/v1/services`: Register new service.
- `POST /api/v1/services/{id}/keys`: Issue a new ingestion key (returns one-time raw secret).
- `GET /api/v1/services/{id}/keys`: List active keys and prefixes for service.
- `POST /api/v1/services/{id}/keys/{key_id}/revoke`: Revoke key.

---

## 6. Dashboard Metrics (`/api/v1/dashboard`)

- `GET /api/v1/dashboard/summary`: Summary count cards.
- `GET /api/v1/dashboard/all`: Consolidated bundle for fast dashboard loading.
