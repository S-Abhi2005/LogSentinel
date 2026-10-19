import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.log_generator import fetch_active_service_key, run_generator
from app.models.service import Service, ServiceIngestionKey

def test_fetch_key_via_cli_argument(db_session, registered_service):
    """Providing --api-key via argument resolves directly without modifying DB keys."""
    svc, _ = registered_service
    initial_key_count = db_session.query(ServiceIngestionKey).filter(
        ServiceIngestionKey.service_id == svc.id
    ).count()

    custom_key = "ls_live_custom_cli_test_key_12345"
    env, key = fetch_active_service_key(db_session, svc.name, api_key=custom_key)

    assert env == svc.environment
    assert key == custom_key

    # DB keys must not be added, modified, or revoked
    current_key_count = db_session.query(ServiceIngestionKey).filter(
        ServiceIngestionKey.service_id == svc.id
    ).count()
    assert current_key_count == initial_key_count

def test_fetch_key_via_env_var(db_session, registered_service, monkeypatch):
    """When --api-key is not provided, LOGSENTINEL_API_KEY environment variable is used."""
    svc, _ = registered_service
    env_key = "ls_live_env_var_test_key_67890"
    monkeypatch.setenv("LOGSENTINEL_API_KEY", env_key)

    initial_key_count = db_session.query(ServiceIngestionKey).filter(
        ServiceIngestionKey.service_id == svc.id
    ).count()

    env, key = fetch_active_service_key(db_session, svc.name, api_key=None)

    assert env == svc.environment
    assert key == env_key

    current_key_count = db_session.query(ServiceIngestionKey).filter(
        ServiceIngestionKey.service_id == svc.id
    ).count()
    assert current_key_count == initial_key_count

def test_cli_argument_overrides_env_var(db_session, registered_service, monkeypatch):
    """CLI --api-key takes precedence over LOGSENTINEL_API_KEY environment variable."""
    svc, _ = registered_service
    monkeypatch.setenv("LOGSENTINEL_API_KEY", "ls_live_env_key_should_be_ignored")

    cli_key = "ls_live_cli_priority_key_9999"
    env, key = fetch_active_service_key(db_session, svc.name, api_key=cli_key)

    assert env == svc.environment
    assert key == cli_key

def test_no_key_provided_with_hashed_db_keys_raises_helpful_error(db_session, registered_service, monkeypatch):
    """
    When no key is provided and DB stores only hashed keys:
    - Explains that the original secret cannot be recovered from one-way hash.
    - Guides user to supply existing key or pass --issue-key.
    - Does not implicitly issue or modify keys.
    """
    svc, _ = registered_service
    monkeypatch.delenv("LOGSENTINEL_API_KEY", raising=False)

    initial_keys = db_session.query(ServiceIngestionKey).filter(
        ServiceIngestionKey.service_id == svc.id
    ).all()
    initial_count = len(initial_keys)
    active_prefix = initial_keys[0].key_prefix

    with pytest.raises(ValueError) as exc_info:
        fetch_active_service_key(db_session, svc.name, api_key=None, issue_key=False)

    error_msg = str(exc_info.value)
    assert "one-way cryptographic hashes" in error_msg
    assert "cannot be recovered" in error_msg
    assert "--api-key" in error_msg
    assert "LOGSENTINEL_API_KEY" in error_msg
    assert "--issue-key" in error_msg
    assert active_prefix in error_msg

    # Verify database was NOT modified
    after_count = db_session.query(ServiceIngestionKey).filter(
        ServiceIngestionKey.service_id == svc.id
    ).count()
    assert after_count == initial_count

def test_no_key_provided_and_no_active_keys_in_db(db_session, monkeypatch):
    """When service exists without any active keys, explains that no key exists and prompts for one."""
    monkeypatch.delenv("LOGSENTINEL_API_KEY", raising=False)

    svc = Service(
        name="empty-key-svc",
        environment="staging",
        description="Service without keys",
        owner_team="Core Ops",
        is_enabled=True
    )
    db_session.add(svc)
    db_session.flush()

    with pytest.raises(ValueError) as exc_info:
        fetch_active_service_key(db_session, svc.name, api_key=None, issue_key=False)

    error_msg = str(exc_info.value)
    assert "No active ingestion API key found" in error_msg
    assert "--api-key" in error_msg
    assert "--issue-key" in error_msg

def test_explicit_key_issuance_via_issue_key_flag(db_session, registered_service, monkeypatch):
    """When --issue-key is explicitly requested, a new ingestion key is issued."""
    svc, _ = registered_service
    monkeypatch.delenv("LOGSENTINEL_API_KEY", raising=False)

    initial_count = db_session.query(ServiceIngestionKey).filter(
        ServiceIngestionKey.service_id == svc.id
    ).count()

    env, raw_key = fetch_active_service_key(db_session, svc.name, api_key=None, issue_key=True)

    assert env == svc.environment
    assert raw_key.startswith("ls_live_")

    after_count = db_session.query(ServiceIngestionKey).filter(
        ServiceIngestionKey.service_id == svc.id
    ).count()
    assert after_count == initial_count + 1

def test_unknown_service_validation(db_session):
    """Validates that non-existent service raises clear ValueError."""
    with pytest.raises(ValueError) as exc_info:
        fetch_active_service_key(db_session, "non-existent-service", api_key="some_key")

    assert "Service 'non-existent-service' not found" in str(exc_info.value)

def test_api_key_never_appears_in_console_output(db_session, registered_service, capsys):
    """Ensures that the API key is passed in HTTP headers and NEVER printed to stdout or stderr."""
    svc, _ = registered_service
    sensitive_secret_key = "ls_live_SUPER_SECRET_TOKEN_DO_NOT_LEAK_998877"

    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"id": "log-entry-123"}

    with patch("scripts.log_generator.SessionLocal", return_value=db_session), \
         patch("scripts.log_generator.requests.post", return_value=mock_resp) as mock_post:

        run_generator(
            base_url="http://127.0.0.1:8001",
            service_name=svc.name,
            scenario="normal",
            count=2,
            delay_sec=0.0,
            api_key=sensitive_secret_key,
            issue_key=False
        )

        # Verify requests.post was called with X-API-Key header containing the key
        assert mock_post.call_count == 2
        for call_item in mock_post.call_args_list:
            headers = call_item.kwargs.get("headers", {})
            assert headers.get("X-API-Key") == sensitive_secret_key

    # Inspect captured output
    captured = capsys.readouterr()
    combined_output = captured.out + captured.err

    # Strictly assert sensitive key never appears in stdout or stderr
    assert sensitive_secret_key not in combined_output
    assert "SUPER_SECRET" not in combined_output

def test_build_parser_options():
    """Verify CLI parser properly recognizes --api-key and --issue-key options."""
    from scripts.log_generator import build_parser

    parser = build_parser()
    args = parser.parse_args([
        "--service", "test-svc",
        "--api-key", "my-secret-key",
        "--issue-key",
        "--scenario", "critical",
        "--count", "5",
        "--delay", "0.5"
    ])

    assert args.service == "test-svc"
    assert args.api_key == "my-secret-key"
    assert args.issue_key is True
    assert args.scenario == "critical"
    assert args.count == 5
    assert args.delay == 0.5

def test_main_cli_error_handling_exits_cleanly(capsys):
    """Verify that main() catches ValueError, writes to stderr with exit code 1, and does not leak keys."""
    from scripts.log_generator import main

    with patch("scripts.log_generator.run_generator", side_effect=ValueError("Service error occurred")):
        with pytest.raises(SystemExit) as exc_info:
            main(["--service", "broken-svc", "--api-key", "my-test-key"])

        assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "[ERROR] Service error occurred" in captured.err
    assert "my-test-key" not in captured.err
    assert "my-test-key" not in captured.out
