import os
import pytest
from pydantic import ValidationError
from app.core.config import Settings
from tests.conftest import get_test_database_url

def test_config_fails_when_credentials_missing(monkeypatch):
    """Verifies Settings fails clearly when neither DATABASE_URL nor POSTGRES_PASSWORD is provided."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)

    # Instantiate Settings with an empty env_file to simulate missing credentials
    class DummySettings(Settings):
        model_config = {
            "env_file": None,
            "extra": "ignore"
        }
        DATABASE_URL: str | None = None
        POSTGRES_PASSWORD: str | None = None

    with pytest.raises(ValidationError) as excinfo:
        DummySettings()
    assert "Database credentials missing" in str(excinfo.value)

def test_config_assembles_database_url_from_password(monkeypatch):
    """Verifies Settings assembles DATABASE_URL when POSTGRES_PASSWORD is provided."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_PASSWORD", "dummy_secure_pwd_123")
    monkeypatch.setenv("POSTGRES_USER", "custom_user")
    monkeypatch.setenv("POSTGRES_SERVER", "db.internal")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "custom_logsentinel")

    class DummySettings(Settings):
        model_config = {
            "env_file": None,
            "extra": "ignore"
        }

    s = DummySettings()
    assert s.DATABASE_URL == "postgresql+psycopg2://custom_user:dummy_secure_pwd_123@db.internal:5432/custom_logsentinel"

def test_harness_safety_check_blocks_production_database(monkeypatch):
    """Verifies that the test harness strictly rejects any attempt to run tests against a non-test database."""
    monkeypatch.setenv("TEST_DATABASE_URL", "postgresql+psycopg2://postgres:secret@localhost:5432/production_logsentinel")

    with pytest.raises(RuntimeError) as excinfo:
        get_test_database_url()
    assert "SAFETY CHECK FAILED" in str(excinfo.value)
    assert "production_logsentinel" in str(excinfo.value)

def test_harness_accepts_test_database(monkeypatch):
    """Verifies that the test harness accepts a test database ending in _test."""
    monkeypatch.setenv("TEST_DATABASE_URL", "postgresql+psycopg2://postgres:secret@localhost:5432/my_app_test")
    url = get_test_database_url()
    assert url == "postgresql+psycopg2://postgres:secret@localhost:5432/my_app_test"
