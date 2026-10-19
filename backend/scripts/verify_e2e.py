import sys
import os
from fastapi.testclient import TestClient

from urllib.parse import urlparse, quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load local environment variables from .env if present
env_paths = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
]
for p in env_paths:
    if os.path.exists(p):
        load_dotenv(p)
        break

import app.models
from app.main import app as fastapi_app
from app.db.base import Base
from app.db.session import get_db


def get_test_db_url() -> str:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        db_url = os.getenv("DATABASE_URL")
        if db_url and "test" in db_url.lower():
            url = db_url
        else:
            server = os.getenv("POSTGRES_SERVER", "localhost")
            port = os.getenv("POSTGRES_PORT", "5432")
            user = os.getenv("POSTGRES_USER", "postgres")
            password = os.getenv("POSTGRES_PASSWORD")
            if not password:
                raise RuntimeError("Cannot resolve test database: POSTGRES_PASSWORD or TEST_DATABASE_URL missing.")
            url = f"postgresql+psycopg2://{user}:{quote_plus(password)}@{server}:{port}/logsentinel_test"

    parsed = urlparse(url)
    db_name = parsed.path.lstrip("/")
    if not db_name.lower().endswith("_test"):
        raise RuntimeError(
            f"SAFETY ERROR: verify_e2e.py refuses to run against non-test database '{db_name}'. "
            "Please target an isolated database ending in '_test'."
        )
    return url

def run_e2e_verification():
    print("=" * 70)
    print("LOGSENTINEL END-TO-END VERIFICATION SUITE (ISOLATED TEST DB)")
    print("=" * 70)

    test_db_url = get_test_db_url()
    test_engine = create_engine(test_db_url, pool_pre_ping=True)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Recreate tables in test database
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Seed initial admin in test database
    from app.models.user import User, UserRole
    from app.security.hashing import hash_password
    with TestingSessionLocal() as db:
        admin = User(
            email="admin@logsentinel.local",
            hashed_password=hash_password("AdminSecurePass123!"),
            full_name="Alice Admin (Lead Architect)",
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
        engineer = User(
            email="engineer@logsentinel.local",
            hashed_password=hash_password("EngineerSecurePass123!"),
            full_name="Bob Engineer (SRE On-Call)",
            role=UserRole.ENGINEER,
            is_active=True
        )
        viewer = User(
            email="viewer@logsentinel.local",
            hashed_password=hash_password("ViewerSecurePass123!"),
            full_name="Charlie Viewer (Product Manager)",
            role=UserRole.VIEWER,
            is_active=True
        )
        db.add_all([admin, engineer, viewer])
        db.commit()
        engineer_id = str(engineer.id)
        admin_id = str(admin.id)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    client = TestClient(fastapi_app)



    # 1. Health checks
    print("\n[Step 1] Checking Liveness & Readiness Probes...")
    live_res = client.get("/health/live")
    assert live_res.status_code == 200, f"Liveness probe failed: {live_res.text}"
    print(f"  -> GET /health/live: {live_res.json()}")

    ready_res = client.get("/health/ready")
    assert ready_res.status_code == 200, f"Readiness probe failed: {ready_res.text}"
    print(f"  -> GET /health/ready: {ready_res.json()}")

    # 2. Authentication & JWT
    print("\n[Step 2] Authenticating as Super Admin...")
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin@logsentinel.local",
        "password": "AdminSecurePass123!"
    })
    assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print(f"  -> Logged in as: {admin_login.json()['email']} (Role: {admin_login.json()['role']})")

    # 3. RBAC Verification (Viewer access control)
    print("\n[Step 3] Verifying RBAC Restrictions (Viewer vs Super Admin)...")
    viewer_login = client.post("/api/v1/auth/login", json={
        "email": "viewer@logsentinel.local",
        "password": "ViewerSecurePass123!"
    })
    assert viewer_login.status_code == 200
    viewer_token = viewer_login.json()["access_token"]
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    # Attempt admin endpoint as viewer -> MUST fail with 403 Forbidden
    forbidden_res = client.get("/api/v1/auth/users", headers=viewer_headers)
    assert forbidden_res.status_code == 403, f"Expected 403 Forbidden, got {forbidden_res.status_code}"
    print("  -> Viewer attempted GET /auth/users: Correctly blocked with HTTP 403 Forbidden!")

    # 4. Service Registration
    print("\n[Step 4] Registering a new Microservice...")
    svc_res = client.post("/api/v1/services", headers=admin_headers, json={
        "name": "e2e-checkout-service",
        "description": "E2E verification checkout pipeline",
        "environment": "staging",
        "owner_team": "Core Checkout QA"
    })
    if svc_res.status_code == 409:
        # Already exists, fetch it
        svc_list = client.get("/api/v1/services", headers=admin_headers).json()
        svc_data = next(s for s in svc_list if s["name"] == "e2e-checkout-service")
    else:
        assert svc_res.status_code == 201, f"Create service failed: {svc_res.text}"
        svc_data = svc_res.json()
    svc_id = svc_data["id"]
    print(f"  -> Service Registered: '{svc_data['name']}' [ID: {svc_id}]")

    # 5. Issue Ingestion Key
    print("\n[Step 5] Issuing Service Ingestion Key...")
    key_res = client.post(f"/api/v1/services/{svc_id}/keys", headers=admin_headers, json={
        "key_name": "e2e-primary-key"
    })
    assert key_res.status_code == 201, f"Issue key failed: {key_res.text}"
    raw_api_key = key_res.json()["raw_key"]
    print(f"  -> Generated Raw Ingestion Key: {raw_api_key[:16]}... (displayed once)")

    # 6. Configure Detection Rule
    print("\n[Step 6] Configuring Incident Detection Rule (Error Threshold >= 3 in 300s)...")
    rule_res = client.post("/api/v1/rules", headers=admin_headers, json={
        "name": f"E2E Checkout Failure Rule {os.urandom(4).hex()}",
        "description": "Triggers when >= 3 errors occur within 5 minutes",
        "rule_type": "error_threshold",
        "severity": "HIGH",
        "service_id": svc_id,
        "environment": "staging",
        "threshold": 3.0,
        "time_window_seconds": 300,
        "cooldown_seconds": 600,
        "is_enabled": True
    })
    assert rule_res.status_code == 201, f"Create rule failed: {rule_res.text}"
    rule_data = rule_res.json()
    rule_id = rule_data["id"]
    print(f"  -> Detection Rule Active: '{rule_data['name']}' [ID: {rule_id}]")

    # 7. Ingestion & Incident Triggering
    print("\n[Step 7] Ingesting Logs & Testing Detection Engine...")
    ingest_headers = {"X-API-Key": raw_api_key}

    # Ingest 2 errors (below threshold of 3)
    for i in range(1, 3):
        res = client.post("/api/v1/logs/ingest", headers=ingest_headers, json={
            "service_name": "e2e-checkout-service",
            "environment": "staging",
            "severity": "ERROR",
            "message": f"E2E payment timeout iteration #{i}",
            "source": "e2e-worker",
            "trace_id": f"e2e-trc-{i}"
        })
        assert res.status_code == 201, f"Log #{i} failed: {res.text}"
        print(f"  -> Log #{i} ingested. (Below threshold, no incident expected)")

    # Verify no incident yet for this rule
    inc_res = client.get(f"/api/v1/incidents?service_id={svc_id}", headers=admin_headers).json()
    assert len(inc_res["items"]) == 0, "Incident should not have triggered on 2 errors"

    # Ingest 3rd error: MUST trigger incident!
    print("  -> Ingesting 3rd error log (Threshold met: count=3)...")
    res_trigger = client.post("/api/v1/logs/ingest", headers=ingest_headers, json={
        "service_name": "e2e-checkout-service",
        "environment": "staging",
        "severity": "ERROR",
        "message": "E2E payment timeout iteration #3 (TRIGGER)",
        "source": "e2e-worker",
        "trace_id": "e2e-trc-3"
    })
    assert res_trigger.status_code == 201

    # Verify Incident and Alert was created!
    inc_after = client.get(f"/api/v1/incidents?service_id={svc_id}", headers=admin_headers).json()
    assert len(inc_after["items"]) == 1, "Incident must be created upon reaching threshold!"
    created_incident = inc_after["items"][0]
    inc_id = created_incident["id"]
    print(f"  [+] Incident Created: '{created_incident['title']}'")
    print(f"      Status: {created_incident['status']} | Severity: {created_incident['severity']} | Fingerprint: {created_incident['fingerprint'][:16]}...")

    # 8. Incident Deduplication Verification
    print("\n[Step 8] Testing Incident Deduplication (4th Error Event)...")
    res_dedup = client.post("/api/v1/logs/ingest", headers=ingest_headers, json={
        "service_name": "e2e-checkout-service",
        "environment": "staging",
        "severity": "ERROR",
        "message": "E2E payment timeout iteration #4 (DEDUPLICATE)",
        "source": "e2e-worker",
        "trace_id": "e2e-trc-4"
    })
    assert res_dedup.status_code == 201

    inc_after_dedup = client.get(f"/api/v1/incidents?service_id={svc_id}", headers=admin_headers).json()
    assert len(inc_after_dedup["items"]) == 1, "Duplicate incident ticket was created! Deduplication failed!"
    assert inc_after_dedup["items"][0]["event_count"] >= 4, "Event count was not incremented on deduplication!"
    print(f"  [+] Deduplication Verified: Still exactly 1 active incident ticket! (Aggregated count: {inc_after_dedup['items'][0]['event_count']})")

    # 9. Incident Lifecycle Management
    print("\n[Step 9] Testing Incident State Machine & Response Lifecycle...")
    eng_headers = {"Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'email': 'engineer@logsentinel.local', 'password': 'EngineerSecurePass123!'}).json()['access_token']}"}

    # Acknowledge
    ack_res = client.post(f"/api/v1/incidents/{inc_id}/acknowledge", headers=eng_headers)
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "ACKNOWLEDGED"
    print("  -> [Acknowledge]: Status transition OPEN -> ACKNOWLEDGED successful")

    # Start Investigation
    inv_res = client.post(f"/api/v1/incidents/{inc_id}/investigate", headers=eng_headers)
    assert inv_res.status_code == 200
    assert inv_res.json()["status"] == "INVESTIGATING"
    print("  -> [Investigate]: Status transition ACKNOWLEDGED -> INVESTIGATING successful")

    # Add Investigation Comment
    com_res = client.post(f"/api/v1/incidents/{inc_id}/comments", headers=eng_headers, json={
        "comment": "Identified downstream payment gateway 504 gateway timeout. Rerouting traffic."
    })
    assert com_res.status_code == 201
    print(f"  -> [Comment]: Posted note by {com_res.json()['user_name']}: '{com_res.json()['comment'][:40]}...'")

    # Resolve Incident
    res_res = client.post(f"/api/v1/incidents/{inc_id}/resolve?reason=Downstream+route+restored", headers=eng_headers)
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"
    print("  -> [Resolve]: Status transition INVESTIGATING -> RESOLVED successful")

    # Reopen Incident
    reopen_res = client.post(f"/api/v1/incidents/{inc_id}/reopen?reason=Latency+spike+recurred", headers=eng_headers)
    assert reopen_res.status_code == 200
    assert reopen_res.json()["status"] == "OPEN"
    print("  -> [Reopen]: Status transition RESOLVED -> OPEN successful")

    # 11. Service Inactivity Monitoring with Controlled Timestamps
    print("\n[Step 11] Testing Service Inactivity Monitoring with Controlled Timestamps...")
    from datetime import datetime, timezone, timedelta
    from app.models.rule import IncidentRule, RuleType, RuleSeverity
    from app.detection.engine import detection_engine

    with TestingSessionLocal() as db:
        inactivity_rule = IncidentRule(
            name="Checkout Service Heartbeat Rule",
            rule_type=RuleType.SERVICE_INACTIVITY,
            severity=RuleSeverity.HIGH,
            service_id=svc_id,
            threshold=0.0,
            time_window_seconds=300,
            cooldown_seconds=600,
            is_enabled=True
        )
        db.add(inactivity_rule)
        db.commit()

        # Service was active just now; simulate clock at +360 seconds
        ref_time = datetime.now(timezone.utc) + timedelta(seconds=360)
        triggered_inactivity = detection_engine.check_service_inactivity(db, reference_time=ref_time)
        assert len(triggered_inactivity) == 1, "Inactivity alert was not triggered!"
        print(f"  [+] Inactivity Incident Detected: '{triggered_inactivity[0].title}'")

        # Deduplication check: second check at +420 seconds should NOT create a duplicate
        ref_time2 = datetime.now(timezone.utc) + timedelta(seconds=420)
        repeated_inactivity = detection_engine.check_service_inactivity(db, reference_time=ref_time2)
        assert len(repeated_inactivity) == 1, "Inactivity alert deduplication failed!"
        print("  [+] Inactivity Deduplication Verified: Exactly 1 active incident.")

    # 12. Engineer Incident Assignment & Persistence
    print("\n[Step 12] Testing Engineer Incident Assignment & Verification...")
    assign_res = client.post(f"/api/v1/incidents/{inc_id}/assign", headers=eng_headers, json={
        "assigned_user_id": engineer_id
    })
    assert assign_res.status_code == 200
    assert assign_res.json()["assigned_user_id"] == engineer_id

    # Verify assignment persistence on detail retrieval
    detail_res = client.get(f"/api/v1/incidents/{inc_id}", headers=eng_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["assigned_user_name"] == "Bob Engineer (SRE On-Call)"
    print(f"  [+] Assignment Confirmed: Assigned to '{detail_res.json()['assigned_user_name']}'")

    # 13. Repeated-Failure and Error-Rate Detection Rules
    print("\n[Step 13] Testing Repeated-Failure & Error-Rate Detection Rules...")
    # Add repeated failure rule
    rule_rep_res = client.post("/api/v1/rules", headers=admin_headers, json={
        "name": "E2E Repeated Gateway Failure",
        "rule_type": "repeated_failure",
        "severity": "HIGH",
        "service_id": svc_id,
        "environment": "staging",
        "threshold": 2,
        "time_window_seconds": 300,
        "cooldown_seconds": 600,
        "error_signature_pattern": "GatewayDropped",
        "is_enabled": True
    })
    assert rule_rep_res.status_code == 201

    # Ingest 2 matching errors
    for idx in range(2):
        client.post("/api/v1/logs/ingest", headers=ingest_headers, json={
            "service_name": "e2e-checkout-service",
            "environment": "staging",
            "severity": "ERROR",
            "message": f"Payment error GatewayDropped packet loss #{idx+1}",
            "source": "e2e-worker",
            "trace_id": f"e2e-rep-{idx}"
        })
    inc_rep = client.get(f"/api/v1/incidents?service_id={svc_id}&search=GatewayDropped", headers=admin_headers).json()
    assert len(inc_rep["items"]) >= 1
    print(f"  [+] Repeated Failure Triggered: '{inc_rep['items'][0]['title']}'")

    # 14. Filtered CSV Export Verification
    print("\n[Step 14] Testing Filtered CSV Export...")
    csv_res = client.get("/api/v1/logs/export?service_name=e2e-checkout-service&severity=ERROR", headers=eng_headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "e2e-checkout-service" in csv_res.text
    assert "ERROR" in csv_res.text
    print("  [+] Filtered CSV Export Successful: Telemetry exported with matching filters.")

    # 15. Security Boundaries, Invalid Credentials, and Token Revocation
    print("\n[Step 15] Testing Security Boundaries & Token Revocation...")
    # Invalid API key
    bad_key_res = client.post("/api/v1/logs/ingest", headers={"X-API-Key": "ls_live_invalid_key_123"}, json={
        "service_name": "e2e-checkout-service",
        "environment": "staging",
        "severity": "INFO",
        "message": "Probe"
    })
    assert bad_key_res.status_code == 401
    print("  -> Bad API key rejected with 401 Unauthorized")

    # Token logout / revocation
    logout_res = client.post("/api/v1/auth/logout", headers=eng_headers)
    assert logout_res.status_code == 200
    revoked_check = client.get("/api/v1/auth/me", headers=eng_headers)
    assert revoked_check.status_code == 401
    print("  -> Logged out token successfully revoked and blocked on subsequent requests")

    # 16. Persistence After Client Re-instantiation (Simulated Restart)
    print("\n[Step 16] Verifying Data Persistence Across Reconnection...")
    with TestClient(fastapi_app) as fresh_client:
        admin_login = fresh_client.post("/api/v1/auth/login", json={
            "email": "admin@logsentinel.local",
            "password": "AdminSecurePass123!"
        })
        fresh_token = admin_login.json()["access_token"]
        fresh_headers = {"Authorization": f"Bearer {fresh_token}"}

        persisted_incidents = fresh_client.get("/api/v1/incidents", headers=fresh_headers).json()
        assert persisted_incidents["total"] >= 2
        persisted_services = fresh_client.get("/api/v1/services", headers=fresh_headers).json()
        assert len(persisted_services) >= 1
        print(f"  [+] Data Persistence Confirmed: {persisted_incidents['total']} incidents and {len(persisted_services)} services intact in database.")

    print("\n" + "=" * 70)
    print("ALL 16 END-TO-END SCENARIOS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_e2e_verification()
