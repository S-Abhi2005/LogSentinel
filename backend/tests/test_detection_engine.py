import pytest
from datetime import datetime, timezone
from app.models.rule import IncidentRule, RuleType, RuleSeverity
from app.models.incident import Incident, IncidentStatus
from app.models.alert import Alert

def test_ingest_single_log_success(client, registered_service):
    svc, api_key = registered_service
    resp = client.post("/api/v1/logs/ingest", headers={"X-API-Key": api_key}, json={
        "service_name": svc.name,
        "environment": svc.environment,
        "severity": "INFO",
        "message": "User session token refreshed",
        "source": "api-gateway",
        "trace_id": "trc-abc-123",
        "metadata": {"user_id": "usr-99", "ip": "192.168.1.1"}
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["service_name"] == svc.name
    assert data["severity"] == "INFO"
    assert data["trace_id"] == "trc-abc-123"

def test_ingest_rejected_without_key(client, registered_service):
    svc, _ = registered_service
    resp = client.post("/api/v1/logs/ingest", json={
        "service_name": svc.name,
        "environment": svc.environment,
        "severity": "INFO",
        "message": "Unauthenticated log"
    })
    assert resp.status_code == 401

def test_ingest_rejected_on_service_mismatch(client, registered_service):
    svc, api_key = registered_service
    resp = client.post("/api/v1/logs/ingest", headers={"X-API-Key": api_key}, json={
        "service_name": "different-unauthorized-service",
        "environment": svc.environment,
        "severity": "INFO",
        "message": "Impersonated log attempt"
    })
    assert resp.status_code == 400
    assert "authorized for service" in resp.json()["detail"]["message"]

def test_critical_log_rule_detection(client, registered_service, db_session):
    svc, api_key = registered_service
    
    # Create critical log detection rule
    rule = IncidentRule(
        name="Test Critical Alert Rule",
        rule_type=RuleType.CRITICAL_LOG,
        severity=RuleSeverity.CRITICAL,
        service_id=svc.id,
        threshold=1.0,
        time_window_seconds=300,
        cooldown_seconds=600,
        is_enabled=True
    )
    db_session.add(rule)
    db_session.commit()

    # Ingest CRITICAL log
    resp = client.post("/api/v1/logs/ingest", headers={"X-API-Key": api_key}, json={
        "service_name": svc.name,
        "environment": svc.environment,
        "severity": "CRITICAL",
        "message": "Kernel memory allocation panic",
        "source": "kernel-driver",
        "trace_id": "trc-crit-001"
    })
    assert resp.status_code == 201

    # Verify incident was created
    incident = db_session.query(Incident).filter(
        Incident.service_id == svc.id,
        Incident.rule_id == rule.id
    ).first()
    assert incident is not None
    assert incident.severity == "CRITICAL"
    assert incident.status == IncidentStatus.OPEN
    assert "Kernel memory allocation panic" in incident.title

    # Verify alert was created
    alert = db_session.query(Alert).filter(Alert.incident_id == incident.id).first()
    assert alert is not None
    assert alert.severity == "CRITICAL"

def test_error_threshold_and_deduplication(client, registered_service, db_session):
    svc, api_key = registered_service
    
    # Rule: >= 3 errors in 300s triggers HIGH incident
    rule = IncidentRule(
        name="Test Error Burst Rule",
        rule_type=RuleType.ERROR_THRESHOLD,
        severity=RuleSeverity.HIGH,
        service_id=svc.id,
        threshold=3.0,
        time_window_seconds=300,
        cooldown_seconds=600,
        is_enabled=True
    )
    db_session.add(rule)
    db_session.commit()

    # Send 2 errors: should not trigger yet
    for i in range(2):
        client.post("/api/v1/logs/ingest", headers={"X-API-Key": api_key}, json={
            "service_name": svc.name,
            "environment": svc.environment,
            "severity": "ERROR",
            "message": f"Query timeout #{i}",
        })
    incidents_count = db_session.query(Incident).filter(Incident.rule_id == rule.id).count()
    assert incidents_count == 0

    # Send 3rd error: MUST trigger incident!
    client.post("/api/v1/logs/ingest", headers={"X-API-Key": api_key}, json={
        "service_name": svc.name,
        "environment": svc.environment,
        "severity": "ERROR",
        "message": "Query timeout #3",
    })
    incidents = db_session.query(Incident).filter(Incident.rule_id == rule.id).all()
    assert len(incidents) == 1
    assert incidents[0].status == IncidentStatus.OPEN
    initial_event_count = incidents[0].event_count

    # Send 4th error: MUST DEDUPLICATE into the existing active incident, NOT create a second incident!
    client.post("/api/v1/logs/ingest", headers={"X-API-Key": api_key}, json={
        "service_name": svc.name,
        "environment": svc.environment,
        "severity": "ERROR",
        "message": "Query timeout #4 (subsequent)",
    })
    incidents_after = db_session.query(Incident).filter(Incident.rule_id == rule.id).all()
    assert len(incidents_after) == 1  # Still exactly 1 active incident!
    assert incidents_after[0].event_count >= initial_event_count + 1
