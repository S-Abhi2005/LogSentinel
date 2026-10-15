# LogSentinel — Security Architecture

## 1. Authentication & Session Management
- **Passwords**: Hashed using `bcrypt` with 12 salt rounds. Plaintext passwords are never logged or stored.
- **JWT Access Tokens**: Cryptographically signed with HMAC-SHA256 (`HS256`).
- **Claims**: Contain user ID (`sub`), role, issuance timestamp (`iat`), and expiration (`exp`).

---

## 2. Ingestion Key Architecture
Microservices authenticate via service-specific ingestion keys:
- **Format**: `ls_live_<32_random_urlsafe_bytes>`
- **Storage**: Only the SHA-256 hash (`key_hash`) and a short prefix (`key_prefix`, first 16 characters) are stored in the database.
- **One-time Secret Display**: The raw key is returned exactly once during creation.
- **Revocation**: Keys can be individually revoked in the Service Registry without affecting other keys for that service.
- **Service Identity Isolation**: The ingestion gateway verifies that the log payload `service_name` strictly matches the service associated with the API key, preventing spoofing across services.

---

## 3. Role-Based Access Control (RBAC) Matrix

| Action | Super Admin | Engineer | Viewer |
| :--- | :---: | :---: | :---: |
| View Dashboards & Charts | ✅ | ✅ | ✅ |
| Query & Search Logs | ✅ | ✅ | ✅ |
| Export Logs as CSV | ✅ | ✅ | ✅ |
| View Incidents & Timeline | ✅ | ✅ | ✅ |
| Acknowledge / Investigate Incident | ✅ | ✅ | ❌ |
| Resolve / Reopen Incident | ✅ | ✅ | ❌ |
| Assign Incident to Engineer | ✅ | ✅ | ❌ |
| Add Investigation Comment | ✅ | ✅ | ❌ |
| Create / Edit Services | ✅ | ✅ | ❌ |
| Issue / Revoke Ingestion Keys | ✅ | ❌ | ❌ |
| Create / Edit Detection Rules | ✅ | ❌ | ❌ |
| View Audit Logs | ✅ | ❌ | ❌ |
| User Administration | ✅ | ❌ | ❌ |

---

## 4. Rate Limiting & Input Protection
- **Sliding Window Rate Limiter**: Limits requests per IP (default 1,200 requests/minute) with `HTTP 429 Too Many Requests`.
- **Payload Size Limits**:
  - Maximum log message length: 32 KB.
  - Maximum metadata JSON length: 64 KB.
  - Maximum batch ingestion size: 500 events.
- **CORS Configuration**: Restricts origins using configurable environment variables.
