import pytest

def test_create_service(client, engineer_headers):
    resp = client.post("/api/v1/services", headers=engineer_headers, json={
        "name": "cart-checkout",
        "description": "Cart checkout microservice",
        "environment": "staging",
        "owner_team": "Checkout Squad"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "cart-checkout"
    assert data["environment"] == "staging"
    assert data["is_enabled"] is True

def test_prevent_duplicate_service(client, engineer_headers):
    # Creating with same name and env should conflict
    resp = client.post("/api/v1/services", headers=engineer_headers, json={
        "name": "cart-checkout-unique",
        "description": "First create",
        "environment": "production",
        "owner_team": "Team A"
    })
    assert resp.status_code == 201

    resp2 = client.post("/api/v1/services", headers=engineer_headers, json={
        "name": "cart-checkout-unique",
        "description": "Duplicate create",
        "environment": "production",
        "owner_team": "Team B"
    })
    assert resp2.status_code == 409

def test_issue_and_revoke_ingestion_key(client, admin_headers, registered_service):
    svc, _ = registered_service
    # Issue key
    resp = client.post(f"/api/v1/services/{svc.id}/keys", headers=admin_headers, json={
        "key_name": "worker-key-1"
    })
    assert resp.status_code == 201
    key_data = resp.json()
    assert "raw_key" in key_data
    assert key_data["raw_key"].startswith("ls_live_")
    key_id = key_data["id"]

    # Revoke key
    revoke_resp = client.post(f"/api/v1/services/{svc.id}/keys/{key_id}/revoke", headers=admin_headers)
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["is_revoked"] is True
