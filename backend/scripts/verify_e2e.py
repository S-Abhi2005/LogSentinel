import sys
import os
from fastapi.testclient import TestClient

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

def run_e2e_verification():
    print("=" * 70)
    print("LOGSENTINEL END-TO-END VERIFICATION SUITE")
    print("=" * 70)
    client = TestClient(app)

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

    # 10. Dashboard & Telemetry Verification
    print("\n[Step 10] Checking Consolidated Dashboard Metrics...")
    dash_res = client.get("/api/v1/dashboard/all", headers=admin_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    print(f"  -> Total Logs in System: {dash_data['summary']['total_logs']}")
    print(f"  -> Error Logs: {dash_data['summary']['error_logs']}")
    print(f"  -> Active Incidents: {dash_data['summary']['active_incidents']}")
    print(f"  -> Total Services: {dash_data['summary']['total_services']}")

    print("\n" + "=" * 70)
    print("ALL END-TO-END WORKFLOW CHECKS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_e2e_verification()
