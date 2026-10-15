import sys
import os
import random
from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.service import Service, ServiceIngestionKey
from app.models.rule import IncidentRule, RuleType, RuleSeverity
from app.security.hashing import hash_password, generate_ingestion_key
from app.services.log_service import ingest_single_log
from app.schemas.log import LogIngestRequest

def seed_database():
    db = SessionLocal()
    print("=" * 60)
    print("LogSentinel Sample Data Seeder")
    print("=" * 60)

    try:
        # 1. Seed Users
        print("\n[1/5] Seeding Users...")
        users_data = [
            ("admin@logsentinel.local", "AdminSecurePass123!", "Alice Admin (Lead Architect)", UserRole.SUPER_ADMIN),
            ("engineer@logsentinel.local", "EngineerSecurePass123!", "Bob Engineer (SRE On-Call)", UserRole.ENGINEER),
            ("viewer@logsentinel.local", "ViewerSecurePass123!", "Charlie Viewer (Product Manager)", UserRole.VIEWER),
        ]
        created_users = {}
        for email, pwd, name, role in users_data:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    email=email,
                    hashed_password=hash_password(pwd),
                    full_name=name,
                    role=role,
                    is_active=True
                )
                db.add(user)
                db.flush()
                print(f"  + Created User: {email} ({role})")
            else:
                print(f"  * User exists: {email}")
            created_users[role] = user

        # 2. Seed Services & Ingestion Keys
        print("\n[2/5] Seeding Registered Services & API Keys...")
        services_data = [
            ("payment-service", "production", "Core payment processing pipeline", "Payments & Billing"),
            ("auth-service", "production", "OAuth2 & JWT user session service", "Identity & Security"),
            ("order-api", "staging", "Order intake and catalog checkout", "E-Commerce Team"),
            ("notification-worker", "development", "Async SMS and email dispatch worker", "Platform Operations"),
        ]
        created_services = {}
        api_keys_map = {}
        for name, env, desc, team in services_data:
            svc = db.query(Service).filter(Service.name == name, Service.environment == env).first()
            if not svc:
                svc = Service(
                    name=name,
                    environment=env,
                    description=f"[SAMPLE] {desc}",
                    owner_team=team,
                    is_enabled=True,
                    last_log_at=datetime.now(timezone.utc) - timedelta(minutes=5)
                )
                db.add(svc)
                db.flush()
                print(f"  + Registered Service: {name} [{env}] (Owner: {team})")
            created_services[name] = svc

            # Ensure Ingestion Key exists
            key_entry = db.query(ServiceIngestionKey).filter(
                ServiceIngestionKey.service_id == svc.id,
                ServiceIngestionKey.is_revoked == False
            ).first()
            if not key_entry:
                raw_key, prefix, key_hash = generate_ingestion_key()
                key_entry = ServiceIngestionKey(
                    service_id=svc.id,
                    key_name=f"{name}-primary-key",
                    key_prefix=prefix,
                    key_hash=key_hash,
                    is_revoked=False
                )
                db.add(key_entry)
                db.flush()
                api_keys_map[name] = raw_key
                print(f"    -> Issued API Key: {raw_key} (prefix: {prefix})")

        # 3. Seed Detection Rules
        print("\n[3/5] Seeding Detection Rules...")
        rules_data = [
            {
                "name": "High Error Frequency Threshold",
                "desc": "Triggers incident if service records >= 5 errors in 5 minutes",
                "type": RuleType.ERROR_THRESHOLD,
                "sev": RuleSeverity.HIGH,
                "threshold": 5.0,
                "window": 300,
                "cooldown": 600,
                "pattern": None
            },
            {
                "name": "Critical Failure Immediate Alert",
                "desc": "Triggers immediate high-priority incident on any CRITICAL severity log",
                "type": RuleType.CRITICAL_LOG,
                "sev": RuleSeverity.CRITICAL,
                "threshold": 1.0,
                "window": 60,
                "cooldown": 300,
                "pattern": None
            },
            {
                "name": "Repeated Database Pool Exhaustion",
                "desc": "Identifies recurring connection pool exhaustion errors (>= 3 times in 5m)",
                "type": RuleType.REPEATED_FAILURE,
                "sev": RuleSeverity.HIGH,
                "threshold": 3.0,
                "window": 300,
                "cooldown": 600,
                "pattern": "connection pool exhausted"
            },
            {
                "name": "Elevated Error Rate Exceeded",
                "desc": "Alerts if error proportion exceeds 20% over 5 minutes with active traffic",
                "type": RuleType.ERROR_RATE,
                "sev": RuleSeverity.MEDIUM,
                "threshold": 0.20,
                "window": 300,
                "cooldown": 600,
                "pattern": None
            },
            {
                "name": "Worker Heartbeat Inactivity Monitor",
                "desc": "Detects background worker silence exceeding 10 minutes",
                "type": RuleType.SERVICE_INACTIVITY,
                "sev": RuleSeverity.MEDIUM,
                "threshold": 1.0,
                "window": 600,
                "cooldown": 900,
                "pattern": None
            }
        ]

        admin_user = created_users[UserRole.SUPER_ADMIN]
        for rdata in rules_data:
            rule = db.query(IncidentRule).filter(IncidentRule.name == rdata["name"]).first()
            if not rule:
                rule = IncidentRule(
                    name=rdata["name"],
                    description=f"[SAMPLE] {rdata['desc']}",
                    rule_type=rdata["type"],
                    severity=rdata["sev"],
                    threshold=rdata["threshold"],
                    time_window_seconds=rdata["window"],
                    cooldown_seconds=rdata["cooldown"],
                    error_signature_pattern=rdata["pattern"],
                    is_enabled=True,
                    created_by_id=admin_user.id
                )
                db.add(rule)
                db.flush()
                print(f"  + Created Rule: '{rdata['name']}' (Type: {rdata['type']}, Sev: {rdata['sev']})")

        db.commit()

        # 4. Generate Telemetry Logs & Trigger Incidents
        print("\n[4/5] Generating Initial Synthetic Telemetry Logs...")
        payment_svc = created_services["payment-service"]
        auth_svc = created_services["auth-service"]

        now = datetime.now(timezone.utc)
        
        # A) Normal activity logs across past 6 hours
        for h in range(6, 0, -1):
            t = now - timedelta(hours=h)
            for s_name in ["payment-service", "auth-service", "order-api"]:
                svc_obj = created_services[s_name]
                for _ in range(random.randint(3, 8)):
                    log_req = LogIngestRequest(
                        service_name=s_name,
                        environment=svc_obj.environment,
                        severity=random.choice(["INFO", "DEBUG"]),
                        message=f"[SAMPLE] Processed event trace {random.randint(1000, 9999)} successfully",
                        timestamp=t + timedelta(minutes=random.randint(1, 55)),
                        source=f"{s_name}-worker",
                        trace_id=f"trc-{random.randint(100000, 999999)}",
                        metadata={"latency_ms": random.randint(15, 120), "status": 200}
                    )
                    ingest_single_log(db, svc_obj, log_req, "seed-corr")

        # B) Trigger Repeated Failure rule on payment-service
        print("  -> Ingesting 4 repeated database error logs to trigger Rule #3...")
        for i in range(4):
            log_req = LogIngestRequest(
                service_name="payment-service",
                environment="production",
                severity="ERROR",
                message="[SAMPLE] Fatal DB connection pool exhausted during transaction commit",
                timestamp=now - timedelta(seconds=120 - i*15),
                source="payment-worker",
                trace_id=f"trc-db-fail-{i}",
                metadata={"pool_size": 20, "active_conns": 20, "error_code": "DB_POOL_EMPTY"}
            )
            ingest_single_log(db, payment_svc, log_req, "seed-corr-db")

        # C) Trigger Critical Log rule on auth-service
        print("  -> Ingesting CRITICAL log on auth-service to trigger Rule #2...")
        crit_req = LogIngestRequest(
            service_name="auth-service",
            environment="production",
            severity="CRITICAL",
            message="[SAMPLE] Hardware Security Module (HSM) signature verification failure",
            timestamp=now - timedelta(minutes=1),
            source="crypto-engine",
            trace_id="trc-hsm-panic-01",
            metadata={"hsm_node": "us-east-1a-hsm-03", "alarm": "CRITICAL_KEY_MISMATCH"}
        )
        ingest_single_log(db, auth_svc, crit_req, "seed-corr-crit")

        print("\n[5/5] Seed Completed Successfully!")
        print("=" * 60)
        print("Demo Accounts:")
        print("  Super Admin: admin@logsentinel.local / AdminSecurePass123!")
        print("  Engineer:    engineer@logsentinel.local / EngineerSecurePass123!")
        print("  Viewer:      viewer@logsentinel.local / ViewerSecurePass123!")
        if api_keys_map:
            print("\nIssued Ingestion API Keys (keep safe for curl / generator testing):")
            for name, key in api_keys_map.items():
                print(f"  {name}: {key}")
        print("=" * 60)

    except Exception as e:
        print(f"\n[-] Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
