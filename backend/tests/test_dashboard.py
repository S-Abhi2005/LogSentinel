import pytest

def test_dashboard_summary_and_metrics(client, viewer_headers):
    resp = client.get("/api/v1/dashboard/summary", headers=viewer_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_logs" in data
    assert "error_logs" in data
    assert "active_incidents" in data
    assert "healthy_services" in data

def test_dashboard_log_trends(client, viewer_headers):
    resp = client.get("/api/v1/dashboard/log-trends?hours=24", headers=viewer_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_dashboard_all_consolidated_endpoint(client, viewer_headers):
    resp = client.get("/api/v1/dashboard/all", headers=viewer_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "log_volume" in data
    assert "severity_breakdown" in data
    assert "incident_trends" in data
    assert "service_health" in data
