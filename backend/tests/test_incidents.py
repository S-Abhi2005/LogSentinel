import pytest
from datetime import datetime, timezone
from app.models.incident import Incident, IncidentStatus, IncidentSeverity

@pytest.fixture
def test_incident(db_session, registered_service):
    svc, _ = registered_service
    inc = Incident(
        title="Test Database Failure",
        description="Database connection dropped",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.OPEN,
        service_id=svc.id,
        environment=svc.environment,
        fingerprint="test-fingerprint-123",
        first_detected_at=datetime.now(timezone.utc),
        last_detected_at=datetime.now(timezone.utc),
        event_count=1
    )
    db_session.add(inc)
    db_session.commit()
    db_session.refresh(inc)
    return inc

def test_incident_lifecycle_transitions(client, engineer_headers, test_incident):
    inc_id = test_incident.id

    # 1. Acknowledge
    resp = client.post(f"/api/v1/incidents/{inc_id}/acknowledge", headers=engineer_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == IncidentStatus.ACKNOWLEDGED
    assert resp.json()["acknowledged_at"] is not None

    # 2. Investigate
    resp = client.post(f"/api/v1/incidents/{inc_id}/investigate", headers=engineer_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == IncidentStatus.INVESTIGATING

    # 3. Resolve
    resp = client.post(f"/api/v1/incidents/{inc_id}/resolve?reason=Fixed+connection+string", headers=engineer_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == IncidentStatus.RESOLVED
    assert resp.json()["resolved_at"] is not None

    # 4. Reopen
    resp = client.post(f"/api/v1/incidents/{inc_id}/reopen?reason=Recurred+after+deploy", headers=engineer_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == IncidentStatus.OPEN

def test_incident_comment_and_assignment(client, engineer_headers, test_users, test_incident):
    inc_id = test_incident.id
    eng = test_users["engineer"]

    # Assign to engineer
    resp = client.post(f"/api/v1/incidents/{inc_id}/assign", headers=engineer_headers, json={
        "assigned_user_id": eng.id
    })
    assert resp.status_code == 200
    assert resp.json()["assigned_user_id"] == eng.id

    # Post comment
    resp_comm = client.post(f"/api/v1/incidents/{inc_id}/comments", headers=engineer_headers, json={
        "comment": "Examining application heap dump and connection pool metrics."
    })
    assert resp_comm.status_code == 201
    assert "heap dump" in resp_comm.json()["comment"]

    # Verify detail includes comments and timeline
    detail = client.get(f"/api/v1/incidents/{inc_id}", headers=engineer_headers).json()
    assert len(detail["comments"]) >= 1
    assert len(detail["timeline"]) >= 2
