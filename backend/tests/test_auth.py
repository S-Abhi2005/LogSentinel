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

def test_audit_logs_role_access_boundary(client, admin_headers, engineer_headers, viewer_headers):
    # 1. Super Admin can access audit logs
    admin_resp = client.get("/api/v1/audit-logs", headers=admin_headers)
    assert admin_resp.status_code == 200
    assert "items" in admin_resp.json()

    # 2. Engineer is denied access (403 Forbidden)
    eng_resp = client.get("/api/v1/audit-logs", headers=engineer_headers)
    assert eng_resp.status_code == 403
    assert "forbidden" in eng_resp.json()["detail"]["code"].lower()

    # 3. Viewer is denied access (403 Forbidden)
    viewer_resp = client.get("/api/v1/audit-logs", headers=viewer_headers)
    assert viewer_resp.status_code == 403
    assert "forbidden" in viewer_resp.json()["detail"]["code"].lower()

    # 4. Unauthenticated is denied access (401 Unauthorized)
    unauth_resp = client.get("/api/v1/audit-logs")
    assert unauth_resp.status_code == 401

def test_logout_and_token_revocation(client, test_users):
    # 1. Login to obtain a fresh access token
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "engineer@test.local",
        "password": "EngineerTestPass123!"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 2. Token works before logout
    me_resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "engineer@test.local"

    # 3. Perform logout
    logout_resp = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert logout_resp.status_code == 200
    assert "successfully" in logout_resp.json()["message"].lower()

    # 4. Token is revoked and rejected on subsequent requests
    subsequent_resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert subsequent_resp.status_code == 401
    assert "revoked" in subsequent_resp.json()["detail"]["message"].lower()

def test_update_current_user_profile(client, engineer_headers):
    # 1. Update own profile name
    update_resp = client.patch("/api/v1/auth/me", headers=engineer_headers, json={
        "full_name": "Updated Engineer Name"
    })
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["full_name"] == "Updated Engineer Name"

    # 2. Verify subsequent GET /me reflects the new name
    me_resp = client.get("/api/v1/auth/me", headers=engineer_headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["full_name"] == "Updated Engineer Name"

def test_update_profile_validation(client, engineer_headers):
    # Name too short should fail validation
    resp = client.patch("/api/v1/auth/me", headers=engineer_headers, json={
        "full_name": "A"
    })
    assert resp.status_code in [400, 422]
