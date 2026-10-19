import pytest
from datetime import datetime, timezone
from app.models.incident import Incident, IncidentStatus, IncidentSeverity


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

def test_list_assignees_permissions_and_fields(client, engineer_headers, viewer_headers, admin_headers, test_users):
    # 1. Engineer can list assignees
    resp = client.get("/api/v1/auth/assignees", headers=engineer_headers)
    assert resp.status_code == 200
    assignees = resp.json()
    assert isinstance(assignees, list)
    assert len(assignees) >= 2  # Super admin and engineer

    # Ensure sensitive fields are never present
    for a in assignees:
        assert "id" in a
        assert "email" in a
        assert "full_name" in a
        assert "role" in a
        assert "hashed_password" not in a
        assert "password" not in a
        assert a["role"] in ["super_admin", "engineer"]

    # 2. Super admin can list assignees
    admin_resp = client.get("/api/v1/auth/assignees", headers=admin_headers)
    assert admin_resp.status_code == 200

    # 3. Viewer is denied (403 Forbidden)
    viewer_resp = client.get("/api/v1/auth/assignees", headers=viewer_headers)
    assert viewer_resp.status_code == 403

    # 4. Unauthenticated is denied (401 Unauthorized)
    unauth_resp = client.get("/api/v1/auth/assignees")
    assert unauth_resp.status_code == 401

def test_incident_assignment_validation_and_boundaries(client, engineer_headers, viewer_headers, admin_headers, test_users, test_incident, db_session):
    inc_id = test_incident.id
    eng = test_users["engineer"]
    admin = test_users["super_admin"]
    viewer = test_users["viewer"]

    # 1. Viewer cannot assign incident (403 Forbidden)
    resp = client.post(f"/api/v1/incidents/{inc_id}/assign", headers=viewer_headers, json={
        "assigned_user_id": eng.id
    })
    assert resp.status_code == 403

    # 2. Super admin can assign incident (200 OK)
    resp = client.post(f"/api/v1/incidents/{inc_id}/assign", headers=admin_headers, json={
        "assigned_user_id": eng.id
    })
    assert resp.status_code == 200
    assert resp.json()["assigned_user_id"] == eng.id

    # 3. Engineer can reassign to super admin (200 OK)
    resp = client.post(f"/api/v1/incidents/{inc_id}/assign", headers=engineer_headers, json={
        "assigned_user_id": admin.id
    })
    assert resp.status_code == 200
    assert resp.json()["assigned_user_id"] == admin.id

    # 4. Assigning to viewer is rejected (400 Bad Request)
    resp = client.post(f"/api/v1/incidents/{inc_id}/assign", headers=engineer_headers, json={
        "assigned_user_id": viewer.id
    })
    assert resp.status_code == 400
    assert "viewer" in resp.json()["detail"]["message"].lower()

    # 5. Assigning to non-existent user returns 404 Not Found
    resp = client.post(f"/api/v1/incidents/{inc_id}/assign", headers=engineer_headers, json={
        "assigned_user_id": "00000000-0000-0000-0000-000000000000"
    })
    assert resp.status_code == 404

    # 6. Assigning to deactivated user is rejected (400 Bad Request)
    from app.models.user import User, UserRole
    from app.security.hashing import hash_password
    deactivated = User(
        email="inactive.eng@test.local",
        hashed_password=hash_password("InactivePass123!"),
        full_name="Inactive Eng",
        role=UserRole.ENGINEER,
        is_active=False
    )
    db_session.add(deactivated)
    db_session.flush()

    resp = client.post(f"/api/v1/incidents/{inc_id}/assign", headers=engineer_headers, json={
        "assigned_user_id": deactivated.id
    })
    assert resp.status_code == 400
    assert "deactivated" in resp.json()["detail"]["message"].lower()

    # 7. Unassigning incident succeeds (200 OK)
    resp = client.post(f"/api/v1/incidents/{inc_id}/assign", headers=engineer_headers, json={
        "assigned_user_id": None
    })
    assert resp.status_code == 200
    assert resp.json()["assigned_user_id"] is None
def test_viewer_cannot_change_incident_status(
    client, viewer_headers, test_incident
):
    inc_id = test_incident.id

    endpoints = [
        f"/api/v1/incidents/{inc_id}/acknowledge",
        f"/api/v1/incidents/{inc_id}/investigate",
        f"/api/v1/incidents/{inc_id}/resolve?reason=RBAC+test",
        f"/api/v1/incidents/{inc_id}/reopen?reason=RBAC+test",
    ]

    for endpoint in endpoints:
        response = client.post(endpoint, headers=viewer_headers)
        assert response.status_code == 403, (
            f"Viewer should not access {endpoint}; "
            f"received {response.status_code}: {response.text}"
        )
