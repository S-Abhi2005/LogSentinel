
import pytest
from datetime import datetime, timezone
from app.models.rule import IncidentRule, RuleType, RuleSeverity
from app.models.incident import Incident, IncidentStatus, IncidentEvent
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

    resp = client.post("/api/v1/logs/ingest", headers={"X-API-Key": api_key}, json={
        "service_name": svc.name,
        "environment": svc.environment,
        "severity": "CRITICAL",
        "message": "Kernel memory allocation panic",
        "source": "kernel-driver",
        "trace_id": "trc-crit-001"
    })
    assert resp.status_code == 201

    incident = db_session.query(Incident).filter(
        Incident.service_id == svc.id,
        Incident.rule_id == rule.id
    ).first()
    assert incident is not None
    assert incident.severity == "CRITICAL"
    assert incident.status == IncidentStatus.OPEN
    assert "Kernel memory allocation panic" in incident.title

    alert = db_session.query(Alert).filter(
        Alert.incident_id == incident.id
    ).first()
    assert alert is not None
    assert alert.severity == "CRITICAL"


def test_error_threshold_and_deduplication(client, registered_service, db_session):
    svc, api_key = registered_service

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

    for i in range(2):
        client.post("/api/v1/logs/ingest", headers={"X-API-Key": api_key}, json={
            "service_name": svc.name,
            "environment": svc.environment,
            "severity": "ERROR",
            "message": f"Query timeout #{i}",
        })

    incidents_count = db_session.query(Incident).filter(
        Incident.rule_id == rule.id
    ).count()
    assert incidents_count == 0

    client.post("/api/v1/logs/ingest", headers={"X-API-Key": api_key}, json={
        "service_name": svc.name,
        "environment": svc.environment,
        "severity": "ERROR",
        "message": "Query timeout #3",
    })
    incidents = db_session.query(Incident).filter(
        Incident.rule_id == rule.id
    ).all()
    assert len(incidents) == 1
    assert incidents[0].status == IncidentStatus.OPEN
    initial_event_count = incidents[0].event_count

    client.post("/api/v1/logs/ingest", headers={"X-API-Key": api_key}, json={
        "service_name": svc.name,
        "environment": svc.environment,
        "severity": "ERROR",
        "message": "Query timeout #4 (subsequent)",
    })
    incidents_after = db_session.query(Incident).filter(
        Incident.rule_id == rule.id
    ).all()
    assert len(incidents_after) == 1
    assert incidents_after[0].event_count >= initial_event_count + 1


def test_service_inactivity_detection_and_deduplication(
    client, registered_service, db_session
):
    from datetime import timedelta
    from app.detection.engine import detection_engine

    svc, _ = registered_service

    base_time = datetime(2026, 10, 15, 12, 0, 0, tzinfo=timezone.utc)
    svc.last_log_at = base_time
    svc.total_logs_ingested = 10
    db_session.commit()

    rule = IncidentRule(
        name="Test Service Heartbeat Rule",
        rule_type=RuleType.SERVICE_INACTIVITY,
        severity=RuleSeverity.HIGH,
        service_id=svc.id,
        threshold=0.0,
        time_window_seconds=300,
        cooldown_seconds=600,
        is_enabled=True
    )
    db_session.add(rule)
    db_session.commit()

    time_2m = base_time + timedelta(seconds=120)
    triggered_2m = detection_engine.check_service_inactivity(
        db_session, reference_time=time_2m
    )
    assert len(triggered_2m) == 0
    assert db_session.query(Incident).filter(
        Incident.rule_id == rule.id
    ).count() == 0

    time_6m = base_time + timedelta(seconds=360)
    triggered_6m = detection_engine.check_service_inactivity(
        db_session, reference_time=time_6m
    )
    assert len(triggered_6m) == 1
    inc = triggered_6m[0]
    assert inc.status == IncidentStatus.OPEN
    assert "silent" in inc.title.lower() or "inactivity" in inc.title.lower()

    time_7m = base_time + timedelta(seconds=420)
    triggered_7m = detection_engine.check_service_inactivity(
        db_session, reference_time=time_7m
    )
    assert len(triggered_7m) == 1

    all_incidents = db_session.query(Incident).filter(
        Incident.rule_id == rule.id
    ).all()
    assert len(all_incidents) == 1

    svc.last_log_at = time_7m
    db_session.commit()
    time_8m = time_7m + timedelta(seconds=60)
    triggered_8m = detection_engine.check_service_inactivity(
        db_session, reference_time=time_8m
    )
    assert len(triggered_8m) == 0

    svc.is_enabled = False
    svc.last_log_at = base_time
    db_session.commit()
    triggered_disabled = detection_engine.check_service_inactivity(
        db_session, reference_time=time_6m
    )
    assert len(triggered_disabled) == 0


def test_inactivity_repeated_event_respects_cooldown(
    client, registered_service, db_session
):
    from datetime import timedelta
    from app.detection.engine import detection_engine

    svc, _ = registered_service
    base_time = datetime(2026, 10, 15, 12, 0, 0, tzinfo=timezone.utc)

    svc.last_log_at = base_time
    db_session.commit()

    rule = IncidentRule(
        name="Cooldown Regression Rule",
        rule_type=RuleType.SERVICE_INACTIVITY,
        severity=RuleSeverity.HIGH,
        service_id=svc.id,
        threshold=0.0,
        time_window_seconds=300,
        cooldown_seconds=600,
        is_enabled=True,
    )
    db_session.add(rule)
    db_session.commit()

    # First detection creates one incident.
    detection_engine.check_service_inactivity(
        db_session, reference_time=base_time + timedelta(seconds=360)
    )

    incident = db_session.query(Incident).filter(
        Incident.rule_id == rule.id
    ).one()

    def repeated_event_count():
        return db_session.query(IncidentEvent).filter(
            IncidentEvent.incident_id == incident.id,
            IncidentEvent.event_type == "REPEATED",
        ).count()

    assert repeated_event_count() == 0

    # Before the 600-second cooldown: no repeated event.
    detection_engine.check_service_inactivity(
        db_session, reference_time=base_time + timedelta(seconds=420)
    )
    assert repeated_event_count() == 0

    # At 600 seconds after first detection: a repeated event is allowed.
    detection_engine.check_service_inactivity(
        db_session, reference_time=base_time + timedelta(seconds=960)
    )
    assert repeated_event_count() == 1

    # A further check within the next cooldown must not add another event.
    detection_engine.check_service_inactivity(
        db_session, reference_time=base_time + timedelta(seconds=1020)
    )
    assert repeated_event_count() == 1

    # Deduplication must keep exactly one incident.
    assert db_session.query(Incident).filter(
        Incident.rule_id == rule.id
    ).count() == 1


def test_repeated_failure_rule_detection(client, registered_service, db_session):
    svc, api_key = registered_service

    rule = IncidentRule(
        name="Connection Reset Rule",
        rule_type=RuleType.REPEATED_FAILURE,
        severity=RuleSeverity.HIGH,
        service_id=svc.id,
        environment=svc.environment,
        threshold=2.0,
        time_window_seconds=300,
        cooldown_seconds=600,
        error_signature_pattern="ConnectionReset",
        is_enabled=True
    )
    db_session.add(rule)
    db_session.commit()

    headers = {"X-API-Key": api_key}

    resp1 = client.post("/api/v1/logs/ingest", headers=headers, json={
        "service_name": svc.name,
        "environment": svc.environment,
        "severity": "ERROR",
        "message": "Database ConnectionReset by peer [err_code=104]"
    })
    assert resp1.status_code == 201
    incidents = db_session.query(Incident).filter(
        Incident.rule_id == rule.id
    ).all()
    assert len(incidents) == 0

    resp2 = client.post("/api/v1/logs/ingest", headers=headers, json={
        "service_name": svc.name,
        "environment": svc.environment,
        "severity": "ERROR",
        "message": "Payment gateway ConnectionReset [err_code=104]"
    })
    assert resp2.status_code == 201
    incidents = db_session.query(Incident).filter(
        Incident.rule_id == rule.id
    ).all()
    assert len(incidents) == 1
    assert "Repeated Failure" in incidents[0].title
    assert incidents[0].status == IncidentStatus.OPEN


def test_error_rate_rule_detection(client, registered_service, db_session):
    svc, api_key = registered_service

    rule = IncidentRule(
        name="High Error Rate Rule",
        rule_type=RuleType.ERROR_RATE,
        severity=RuleSeverity.CRITICAL,
        service_id=svc.id,
        environment=svc.environment,
        threshold=0.40,
        time_window_seconds=300,
        cooldown_seconds=600,
        is_enabled=True
    )
    db_session.add(rule)
    db_session.commit()

    headers = {"X-API-Key": api_key}

    for i in range(4):
        client.post("/api/v1/logs/ingest", headers=headers, json={
            "service_name": svc.name,
            "environment": svc.environment,
            "severity": "INFO",
            "message": f"Normal traffic #{i}"
        })
    incidents = db_session.query(Incident).filter(
        Incident.rule_id == rule.id
    ).all()
    assert len(incidents) == 0

    client.post("/api/v1/logs/ingest", headers=headers, json={
        "service_name": svc.name,
        "environment": svc.environment,
        "severity": "ERROR",
        "message": "First error event"
    })
    incidents = db_session.query(Incident).filter(
        Incident.rule_id == rule.id
    ).all()
    assert len(incidents) == 0

    for i in range(2):
        client.post("/api/v1/logs/ingest", headers=headers, json={
            "service_name": svc.name,
            "environment": svc.environment,
            "severity": "ERROR",
            "message": f"Elevated error event #{i+2}"
        })

    incidents = db_session.query(Incident).filter(
        Incident.rule_id == rule.id
    ).all()
    assert len(incidents) == 1
    assert "Elevated Error Rate" in incidents[0].title
    assert incidents[0].status == IncidentStatus.OPEN


def test_logs_explorer_search_across_fields_and_csv_export(
    client, registered_service, viewer_headers, db_session
):
    svc, api_key = registered_service

    client.post("/api/v1/logs/ingest", headers={"X-API-Key": api_key}, json={
        "service_name": svc.name,
        "environment": svc.environment,
        "severity": "WARNING",
        "message": "Deadlock detected during batch update",
        "source": "worker-pool-7",
        "trace_id": "tr-custom-deadlock-99"
    })

    resp_svc = client.get(
        f"/api/v1/logs?search={svc.name}", headers=viewer_headers
    )
    assert resp_svc.status_code == 200
    assert resp_svc.json()["total"] >= 1
    assert any(
        log["service_name"] == svc.name
        for log in resp_svc.json()["items"]
    )

    resp_tr = client.get(
        "/api/v1/logs?search=tr-custom-deadlock-99",
        headers=viewer_headers
    )
    assert resp_tr.status_code == 200
    assert resp_tr.json()["total"] >= 1
    assert any(
        log["trace_id"] == "tr-custom-deadlock-99"
        for log in resp_tr.json()["items"]
    )

    resp_src = client.get(
        "/api/v1/logs?search=worker-pool-7", headers=viewer_headers
    )
    assert resp_src.status_code == 200
    assert resp_src.json()["total"] >= 1
    assert any(
        log["source"] == "worker-pool-7"
        for log in resp_src.json()["items"]
    )

    csv_resp = client.get(
        f"/api/v1/logs/export?service_name={svc.name}&severity=WARNING",
        headers=viewer_headers
    )
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "Deadlock detected during batch update" in csv_resp.text
    assert svc.name in csv_resp.text
