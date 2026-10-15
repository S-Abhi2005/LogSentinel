import pytest
from app.models.user import UserRole
from app.security.hashing import verify_password

def test_login_success(client, test_users):
    resp = client.post("/api/v1/auth/login", json={
        "email": "admin@test.local",
        "password": "AdminTestPass123!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == UserRole.SUPER_ADMIN
    assert data["email"] == "admin@test.local"

def test_login_invalid_credentials(client, test_users):
    resp = client.post("/api/v1/auth/login", json={
        "email": "admin@test.local",
        "password": "WrongPassword!"
    })
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]["message"]

def test_current_user_profile(client, admin_headers):
    resp = client.get("/api/v1/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "admin@test.local"
    assert data["role"] == UserRole.SUPER_ADMIN

def test_unauthenticated_access_rejected(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401

def test_rbac_role_enforcement(client, viewer_headers, admin_headers):
    # Viewers cannot list users (Super Admin only)
    resp = client.get("/api/v1/auth/users", headers=viewer_headers)
    assert resp.status_code == 403

    # Super Admin can list users
    resp2 = client.get("/api/v1/auth/users", headers=admin_headers)
    assert resp2.status_code == 200
    assert len(resp2.json()) >= 3

def test_change_password(client, test_users, admin_headers, db_session):
    resp = client.post("/api/v1/auth/change-password", headers=admin_headers, json={
        "current_password": "AdminTestPass123!",
        "new_password": "NewSecurePassword456!"
    })
    assert resp.status_code == 200
    
    # Verify new password works
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "admin@test.local",
        "password": "NewSecurePassword456!"
    })
    assert login_resp.status_code == 200
