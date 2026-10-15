from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.service import Service
from app.models.log import LogEntry
from app.models.rule import IncidentRule, RuleType
from app.models.incident import Incident
from app.detection.rules import (
    evaluate_error_threshold_rule,
    evaluate_critical_log_rule,
    evaluate_repeated_failure_rule,
    evaluate_error_rate_rule,
    evaluate_service_inactivity_rule
)

class IncidentDetectionEngine:
    def __init__(self):
        pass

    def evaluate_ingested_logs(
        self,
        db: Session,
        service: Service,
        logs: List[LogEntry]
    ) -> List[Incident]:
        """
        Evaluates active rules applicable to the given service and newly ingested logs.
        Applies deduplication and returns list of new or updated incidents.
        """
        if not logs or not service.is_enabled:
            return []

        # Find distinct environments present in this batch
        environments = list({log.environment for log in logs})
        reference_time = max((log.timestamp for log in logs), default=datetime.now(timezone.utc))

        results: List[Incident] = []

        for env in environments:
            # Query enabled rules matching this service (or global NULL) and environment (or global NULL)
            rules = db.query(IncidentRule).filter(
                IncidentRule.is_enabled == True,
                or_(IncidentRule.service_id == service.id, IncidentRule.service_id == None),
                or_(IncidentRule.environment == env, IncidentRule.environment == None)
            ).all()

            for rule in rules:
                incident_res: Optional[tuple[Incident, bool]] = None
                
                if rule.rule_type == RuleType.CRITICAL_LOG:
                    incident_res = evaluate_critical_log_rule(
                        db=db, rule=rule, service=service, environment=env,
                        ingested_logs=logs, reference_time=reference_time
                    )
                elif rule.rule_type == RuleType.ERROR_THRESHOLD:
                    incident_res = evaluate_error_threshold_rule(
                        db=db, rule=rule, service=service, environment=env,
                        ingested_logs=logs, reference_time=reference_time
                    )
                elif rule.rule_type == RuleType.REPEATED_FAILURE:
                    incident_res = evaluate_repeated_failure_rule(
                        db=db, rule=rule, service=service, environment=env,
                        ingested_logs=logs, reference_time=reference_time
                    )
                elif rule.rule_type == RuleType.ERROR_RATE:
                    incident_res = evaluate_error_rate_rule(
                        db=db, rule=rule, service=service, environment=env,
                        ingested_logs=logs, reference_time=reference_time
                    )

                if incident_res:
                    incident, _ = incident_res
                    if incident not in results:
                        results.append(incident)

        return results

    def check_service_inactivity(self, db: Session) -> List[Incident]:
        """
        Scans all active services and evaluates enabled service_inactivity rules.
        """
        now = datetime.now(timezone.utc)
        inactivity_rules = db.query(IncidentRule).filter(
            IncidentRule.is_enabled == True,
            IncidentRule.rule_type == RuleType.SERVICE_INACTIVITY
        ).all()

        triggered: List[Incident] = []
        for rule in inactivity_rules:
            if rule.service_id:
                services = db.query(Service).filter(
                    Service.id == rule.service_id,
                    Service.is_enabled == True
                ).all()
            else:
                services = db.query(Service).filter(Service.is_enabled == True).all()

            for service in services:
                res = evaluate_service_inactivity_rule(db, rule, service, now)
                if res:
                    inc, _ = res
                    if inc not in triggered:
                        triggered.append(inc)

        return triggered

detection_engine = IncidentDetectionEngine()
