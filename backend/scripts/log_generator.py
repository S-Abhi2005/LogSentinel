import sys
import os
import time
import random
import argparse
import requests
from typing import Optional
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.models.service import Service, ServiceIngestionKey

def fetch_active_service_key(
    db,
    service_name: str,
    api_key: Optional[str] = None,
    issue_key: bool = False
) -> tuple[str, str]:
    """Finds service and resolves the active raw ingestion key for simulation."""
    svc = db.query(Service).filter(Service.name == service_name).first()
    if not svc:
        raise ValueError(f"Service '{service_name}' not found. Please register the service first.")

    # 1. If key is supplied through argument or environment variable, use it directly
    resolved_key = (api_key or "").strip()
    if not resolved_key:
        resolved_key = (os.getenv("LOGSENTINEL_API_KEY") or "").strip()
    if resolved_key:
        return svc.environment, resolved_key

    # 2. Check if an active key already exists in the database
    key_entry = db.query(ServiceIngestionKey).filter(
        ServiceIngestionKey.service_id == svc.id,
        ServiceIngestionKey.is_revoked == False
    ).first()

    # 3. If explicit issuance was requested via --issue-key, issue a new key
    if issue_key:
        from app.services.service_registry import issue_service_key
        _, raw = issue_service_key(db, svc.id, f"{service_name}-cli-key")
        return svc.environment, raw

    # 4. If no key is supplied and the database stores only hashed keys, explain that the original secret cannot be recovered.
    # Ask the user to supply an existing key or explicitly request issuance of a new key. Do not issue keys implicitly.
    if key_entry:
        raise ValueError(
            f"No ingestion API key supplied for service '{service_name}' (active key prefix: '{key_entry.key_prefix}...'). "
            "LogSentinel stores keys as one-way cryptographic hashes, so the original secret cannot be recovered from the database. "
            "Please supply an existing key using the '--api-key' option or the 'LOGSENTINEL_API_KEY' environment variable, "
            "or explicitly request issuance of a new key by passing '--issue-key'."
        )

    raise ValueError(
        f"No active ingestion API key found for service '{service_name}'. "
        "Please supply an existing key using the '--api-key' option or the 'LOGSENTINEL_API_KEY' environment variable, "
        "or explicitly request issuance of a new key by passing '--issue-key'."
    )

def run_generator(
    base_url: str,
    service_name: str,
    scenario: str,
    count: int,
    delay_sec: float,
    api_key: Optional[str] = None,
    issue_key: bool = False
):
    print("=" * 60)
    print(f"LogSentinel Telemetry Generator -> [{scenario.upper()}]")
    print(f"Target: {base_url}/api/v1/logs/ingest | Service: {service_name}")
    print("=" * 60)

    db = SessionLocal()
    try:
        env, resolved_key = fetch_active_service_key(db, service_name, api_key=api_key, issue_key=issue_key)
    finally:
        db.close()

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": resolved_key
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

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LogSentinel Synthetic Log Generator")
    parser.add_argument("--url", default=os.getenv("BACKEND_URL", "http://localhost:8001"), help="Backend base URL")
    parser.add_argument("--service", default="payment-service", help="Target registered service")
    parser.add_argument("--scenario", default="normal", choices=["normal", "warning", "error_burst", "critical", "repeated_failure"], help="Scenario to simulate")
    parser.add_argument("--count", type=int, default=10, help="Number of log events to send")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay in seconds between logs")
    parser.add_argument("--api-key", default=None, help="Service ingestion API key (or set LOGSENTINEL_API_KEY env var)")
    parser.add_argument("--issue-key", action="store_true", default=False, help="Explicitly issue and save a new ingestion key for this service if none is provided")
    return parser

def main(argv: Optional[list[str]] = None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        run_generator(
            args.url,
            args.service,
            args.scenario,
            args.count,
            args.delay,
            api_key=args.api_key,
            issue_key=args.issue_key
        )
    except ValueError as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
