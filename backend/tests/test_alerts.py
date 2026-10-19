import pytest
from app.models.alert import Alert
from datetime import datetime, timezone

def test_alerts_lifecycle(client, viewer_headers, test_incident, db_session):
    # Create two test alerts
    alert1 = Alert(
        incident_id=test_incident.id,
        title="[CRITICAL] Test Alert 1",
        message="Service crashed",
        severity="CRITICAL",
        is_read=False,
        created_at=datetime.now(timezone.utc)
    )
    alert2 = Alert(
        incident_id=test_incident.id,
        title="[HIGH] Test Alert 2",
        message="High memory usage",
        severity="HIGH",
        is_read=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(alert1)
    db_session.add(alert2)
    db_session.commit()

    # 1. List all alerts
    resp = client.get("/api/v1/alerts", headers=viewer_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["unread_count"] >= 2
    assert any(a["id"] == alert1.id for a in data["items"])
    assert any(a["id"] == alert2.id for a in data["items"])

    # 2. Mark single alert as read
    read_resp = client.post(f"/api/v1/alerts/{alert1.id}/read", headers=viewer_headers)
    assert read_resp.status_code == 200
    assert read_resp.json()["is_read"] is True

    # 3. Verify unread count decreased and filter by is_read=False
    unread_resp = client.get("/api/v1/alerts?is_read=false", headers=viewer_headers)
    assert unread_resp.status_code == 200
    assert not any(a["id"] == alert1.id for a in unread_resp.json()["items"])
    assert any(a["id"] == alert2.id for a in unread_resp.json()["items"])

    # 4. Filter by is_read=true
    read_list_resp = client.get("/api/v1/alerts?is_read=true", headers=viewer_headers)
    assert read_list_resp.status_code == 200
    assert any(a["id"] == alert1.id for a in read_list_resp.json()["items"])

    # 5. Mark all as read
    mark_all_resp = client.post("/api/v1/alerts/read-all", headers=viewer_headers)
    assert mark_all_resp.status_code == 200

    # Verify unread count is now 0
    final_resp = client.get("/api/v1/alerts", headers=viewer_headers)
    assert final_resp.json()["unread_count"] == 0

def test_alerts_error_and_auth_boundaries(client, viewer_headers):
    # 1. Non-existent alert returns 404
    resp = client.post("/api/v1/alerts/00000000-0000-0000-0000-000000000000/read", headers=viewer_headers)
    assert resp.status_code == 404

    # 2. Unauthenticated access is rejected
    unauth_resp = client.get("/api/v1/alerts")
    assert unauth_resp.status_code == 401
