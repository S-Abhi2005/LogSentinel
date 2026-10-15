import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.base import Base
import app.models  # load all models
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole
from app.security.hashing import hash_password, generate_ingestion_key
from app.security.tokens import create_access_token
from app.models.service import Service, ServiceIngestionKey

TEST_DATABASE_URL = "postgresql+psycopg2://postgres:abhi%40321@localhost:5432/logsentinel_test"

test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create clean tables in test database once for the test session."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    """Provides a transactional database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """Provides a TestClient overriding get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_users(db_session):
    """Creates sample users across all roles."""
    users = {}
    roles = [
        ("admin@test.local", "AdminTestPass123!", "Super Admin", UserRole.SUPER_ADMIN),
        ("engineer@test.local", "EngineerTestPass123!", "On-Call Engineer", UserRole.ENGINEER),
        ("viewer@test.local", "ViewerTestPass123!", "Viewer Only", UserRole.VIEWER),
    ]
    for email, pwd, name, role in roles:
        u = User(
            email=email,
            hashed_password=hash_password(pwd),
            full_name=name,
            role=role,
            is_active=True
        )
        db_session.add(u)
        db_session.flush()
        users[role] = u

    return users

@pytest.fixture
def admin_headers(test_users):
    admin = test_users[UserRole.SUPER_ADMIN]
    token = create_access_token(subject=admin.id, role=admin.role)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def engineer_headers(test_users):
    eng = test_users[UserRole.ENGINEER]
    token = create_access_token(subject=eng.id, role=eng.role)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def viewer_headers(test_users):
    viewer = test_users[UserRole.VIEWER]
    token = create_access_token(subject=viewer.id, role=viewer.role)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def registered_service(db_session):
    """Creates a registered test service and active ingestion key."""
    svc = Service(
        name="billing-test-svc",
        environment="development",
        description="Test service for unit tests",
        owner_team="Billing QA",
        is_enabled=True
    )
    db_session.add(svc)
    db_session.flush()

    raw_key, prefix, key_hash = generate_ingestion_key()
    key_entry = ServiceIngestionKey(
        service_id=svc.id,
        key_name="test-ingest-key",
        key_prefix=prefix,
        key_hash=key_hash,
        is_revoked=False
    )
    db_session.add(key_entry)
    db_session.flush()

    return svc, raw_key
