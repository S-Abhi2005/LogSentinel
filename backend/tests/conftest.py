import os
import sys
import pytest
from datetime import datetime, timezone
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

from urllib.parse import urlparse, quote_plus
from dotenv import load_dotenv

# Load local environment variables from .env if present
env_paths = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
]
for p in env_paths:
    if os.path.exists(p):
        load_dotenv(p)
        break

def get_test_database_url() -> str:
    """
    Safely resolves the test database URL from environment variables.
    Strictly verifies that tests only run against an isolated test database (e.g. ending in _test).
    """
    test_url = os.getenv("TEST_DATABASE_URL")
    if not test_url:
        db_url = os.getenv("DATABASE_URL")
        if db_url and "test" in db_url.lower():
            test_url = db_url
        else:
            server = os.getenv("POSTGRES_SERVER", "localhost")
            port = os.getenv("POSTGRES_PORT", "5432")
            user = os.getenv("POSTGRES_USER", "postgres")
            password = os.getenv("POSTGRES_PASSWORD")
            if not password:
                raise RuntimeError(
                    "Missing test database credentials: TEST_DATABASE_URL, DATABASE_URL, or POSTGRES_PASSWORD must be set in environment."
                )
            test_url = f"postgresql+psycopg2://{user}:{quote_plus(password)}@{server}:{port}/logsentinel_test"

    # Convert generic postgresql:// to postgresql+psycopg2://
    if test_url.startswith("postgresql://"):
        test_url = test_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    # SAFETY CHECK: Strictly prevent test harness from modifying production or development databases
    parsed = urlparse(test_url)
    db_name = parsed.path.lstrip("/")
    if not db_name.endswith("_test") and "test" not in db_name.lower():
        raise RuntimeError(
            f"SAFETY CHECK FAILED: Attempted to run test suite against non-test database '{db_name}'. "
            "Tests must target an isolated database ending in '_test'."
        )

    return test_url

TEST_DATABASE_URL = get_test_database_url()
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

@pytest.fixture
def test_incident(db_session, registered_service):
    """Creates a sample open incident associated with registered test service."""
    from app.models.incident import Incident, IncidentStatus, IncidentSeverity
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
