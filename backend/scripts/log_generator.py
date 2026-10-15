import sys
import os
import time
import random
import argparse
import requests
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.models.service import Service, ServiceIngestionKey

def fetch_active_service_key(db, service_name: str) -> tuple[str, str]:
    """Finds service and an active raw key for simulation, or generates a fresh one."""
    svc = db.query(Service).filter(Service.name == service_name).first()
    if not svc:
        raise ValueError(f"Service '{service_name}' not found. Run seed_data.py first.")
    
    # We query the most recently created key or prompt user
    key_entry = db.query(ServiceIngestionKey).filter(
        ServiceIngestionKey.service_id == svc.id,
        ServiceIngestionKey.is_revoked == False
    ).first()
    
    if not key_entry:
        from app.services.service_registry import issue_service_key
        _, raw = issue_service_key(db, svc.id, f"{service_name}-generator-key")
        return svc.environment, raw
    
    # In production, raw keys cannot be recovered from hash; for generator convenience, we create a generator key if needed
    from app.services.service_registry import issue_service_key
    _, raw = issue_service_key(db, svc.id, f"{service_name}-cli-sim-key")
    return svc.environment, raw

def run_generator(base_url: str, service_name: str, scenario: str, count: int, delay_sec: float):
    print("=" * 60)
    print(f"LogSentinel Telemetry Generator -> [{scenario.upper()}]")
    print(f"Target: {base_url}/api/v1/logs/ingest | Service: {service_name}")
    print("=" * 60)

    db = SessionLocal()
    try:
        env, api_key = fetch_active_service_key(db, service_name)
    finally:
        db.close()

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    scenarios = {
        "normal": [
            ("INFO", "GET /api/v1/checkout 200 OK", 45),
            ("DEBUG", "Cache hit on key user_session_4921", 2),
            ("INFO", "Payment intent authorized successfully", 110),
            ("INFO", "Background order confirmation email enqueued", 25),
        ],
        "warning": [
            ("WARNING", "Slow query detected on orders table (duration: 1450ms)", 1450),
            ("WARNING", "High memory usage watermark reached: 82%", 5),
            ("WARNING", "Downstream payment gateway latency elevated: 850ms", 850),
        ],
        "error_burst": [
            ("ERROR", "Unhandled NullReferenceException in PaymentProcessor.cs line 142", 500),
            ("ERROR", "Failed to deserialize JSON response from upstream provider", 502),
            ("ERROR", "Database transaction rolled back due to lock acquisition timeout", 504),
        ],
        "critical": [
            ("CRITICAL", "Hardware Security Module (HSM) signature verification failure", 500),
            ("CRITICAL", "Data corruption detected in transaction block WAL index", 500),
        ],
        "repeated_failure": [
            ("ERROR", "Fatal DB connection pool exhausted during transaction commit", 503),
            ("ERROR", "Fatal DB connection pool exhausted during transaction commit", 503),
        ]
    }

    events_pool = scenarios.get(scenario, scenarios["normal"])

    for i in range(count):
        sev, msg, lat = random.choice(events_pool)
        payload = {
            "service_name": service_name,
            "environment": env,
            "severity": sev,
            "message": f"[{scenario.upper()}] {msg} (iter {i+1}/{count})",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": f"{service_name}-sim",
            "trace_id": f"sim-trc-{random.randint(100000, 999999)}",
            "metadata": {"latency_ms": lat, "iteration": i + 1, "scenario": scenario}
        }

        try:
            resp = requests.post(f"{base_url}/api/v1/logs/ingest", json=payload, headers=headers, timeout=5)
            if resp.status_code in [200, 201]:
                data = resp.json()
                print(f"[{i+1}/{count}] HTTP {resp.status_code} | {sev:<8} | ID: {data.get('id')} | Msg: {msg[:40]}...")
            else:
                print(f"[{i+1}/{count}] HTTP {resp.status_code} | Error: {resp.text}")
        except Exception as e:
            print(f"[{i+1}/{count}] Connection error: {e}")

        if delay_sec > 0 and i < count - 1:
            time.sleep(delay_sec)

    print("\nFinished generator run.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LogSentinel Synthetic Log Generator")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--service", default="payment-service", help="Target registered service")
    parser.add_argument("--scenario", default="normal", choices=["normal", "warning", "error_burst", "critical", "repeated_failure"], help="Scenario to simulate")
    parser.add_argument("--count", type=int, default=10, help="Number of log events to send")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay in seconds between logs")

    args = parser.parse_args()
    run_generator(args.url, args.service, args.scenario, args.count, args.delay)
