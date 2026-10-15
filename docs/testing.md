# LogSentinel — Testing Guide & Verification

## 1. Test Architecture

The testing suite utilizes `pytest`, `pytest-asyncio`, and `httpx` (`TestClient`) running against an isolated PostgreSQL database (`logsentinel_test`).

Database isolation guarantees that tests never mutate development data or production logs. Each test transaction automatically rolls back upon completion.

---

## 2. Test Execution Command

Run the full backend test suite:
```powershell
cd backend
python -m pytest tests -v
```

### Verified Test Cases:
1. `test_login_success`: Validates password verification and JWT token structure.
2. `test_login_invalid_credentials`: Validates HTTP 401 on incorrect credentials.
3. `test_current_user_profile`: Validates `/auth/me` with Bearer token.
4. `test_unauthenticated_access_rejected`: Verifies HTTP 401 when token is missing.
5. `test_rbac_role_enforcement`: Asserts Super Admin access vs Viewer rejection (HTTP 403).
6. `test_change_password`: Validates password rotation and subsequent login.
7. `test_dashboard_summary_and_metrics`: Validates SQL metric aggregation.
8. `test_dashboard_log_trends`: Validates time-series window bucketing.
9. `test_dashboard_all_consolidated_endpoint`: Validates composite dashboard response.
10. `test_ingest_single_log_success`: Ingests single log via `X-API-Key`.
11. `test_ingest_rejected_without_key`: Asserts HTTP 401 when key is missing.
12. `test_ingest_rejected_on_service_mismatch`: Asserts HTTP 400 when service identity is spoofed.
13. `test_critical_log_rule_detection`: Validates immediate incident generation on CRITICAL log.
14. `test_error_threshold_and_deduplication`: Validates error burst trigger and asserts deduplication into a single active incident without duplicates.
15. `test_incident_lifecycle_transitions`: Tests `OPEN` -> `ACKNOWLEDGED` -> `INVESTIGATING` -> `RESOLVED` -> `OPEN`.
16. `test_incident_comment_and_assignment`: Validates engineer assignment and comment timeline recording.
17. `test_create_service`: Validates microservice registration.
18. `test_prevent_duplicate_service`: Validates `UNIQUE(name, environment)` constraint (HTTP 409).
19. `test_issue_and_revoke_ingestion_key`: Validates key prefixing, hashing, and revocation.

---

## 3. Frontend Typecheck & Build Verification

Run the TypeScript build verification:
```powershell
cd frontend
npm run build
```
- Validates 100% strict TypeScript typing.
- Confirms zero bundling errors or broken component references.
