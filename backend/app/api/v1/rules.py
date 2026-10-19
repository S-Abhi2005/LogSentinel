from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.rule import IncidentRule, RuleType, RuleSeverity
from app.models.incident import Incident
from app.schemas.rule import RuleCreate, RuleUpdate, RuleResponse
from app.security.rbac import require_viewer_or_above, require_super_admin
from app.core.errors import NotFoundException, ConflictException, BadRequestException
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/rules", tags=["Incident Detection Rules"])

@router.get("", response_model=List[RuleResponse])
def list_rules(
    rule_type: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    query = db.query(IncidentRule)
    if rule_type:
        query = query.filter(IncidentRule.rule_type == rule_type)
    if is_enabled is not None:
        query = query.filter(IncidentRule.is_enabled == is_enabled)
    return query.order_by(IncidentRule.created_at.desc()).all()

@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(
    data: RuleCreate,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(IncidentRule).filter(IncidentRule.name == data.name.strip()).first()
    if existing:
        raise ConflictException(f"Detection rule with name '{data.name}' already exists")

    rule = IncidentRule(
        name=data.name.strip(),
        description=data.description,
        rule_type=data.rule_type,
        severity=data.severity,
        service_id=data.service_id,
        environment=data.environment,
        threshold=data.threshold,
        time_window_seconds=data.time_window_seconds,
        cooldown_seconds=data.cooldown_seconds,
        error_signature_pattern=data.error_signature_pattern,
        is_enabled=data.is_enabled,
        created_by_id=current_user.id
    )
    db.add(rule)
    db.flush()

    log_audit_event(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="RULE_CREATED",
        target_type="incident_rule",
        target_id=rule.id,
        details={"name": rule.name, "rule_type": rule.rule_type, "severity": rule.severity}
    )
    db.commit()
    db.refresh(rule)
    return rule

@router.get("/{rule_id}", response_model=RuleResponse)
def get_rule(
    rule_id: str,
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    rule = db.query(IncidentRule).filter(IncidentRule.id == rule_id).first()
    if not rule:
        raise NotFoundException("Detection rule", rule_id)
    return rule

@router.patch("/{rule_id}", response_model=RuleResponse)
def update_rule(
    rule_id: str,
    data: RuleUpdate,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    rule = db.query(IncidentRule).filter(IncidentRule.id == rule_id).first()
    if not rule:
        raise NotFoundException("Detection rule", rule_id)

    if data.name is not None:
        rule.name = data.name.strip()
    if data.description is not None:
        rule.description = data.description
    if data.severity is not None:
        rule.severity = data.severity
    if data.threshold is not None:
        rule.threshold = data.threshold
    if data.time_window_seconds is not None:
        rule.time_window_seconds = data.time_window_seconds
    if data.cooldown_seconds is not None:
        rule.cooldown_seconds = data.cooldown_seconds
    if data.error_signature_pattern is not None:
        rule.error_signature_pattern = data.error_signature_pattern
    if data.is_enabled is not None:
        rule.is_enabled = data.is_enabled

    rule.updated_at = datetime.now(timezone.utc)

    log_audit_event(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="RULE_UPDATED",
        target_type="incident_rule",
        target_id=rule.id,
        details=data.model_dump(exclude_unset=True)
    )
    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/{rule_id}")
def delete_or_disable_rule(
    rule_id: str,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    rule = db.query(IncidentRule).filter(IncidentRule.id == rule_id).first()
    if not rule:
        raise NotFoundException("Detection rule", rule_id)

    # Check if historical incidents reference this rule
    incident_count = db.query(Incident).filter(Incident.rule_id == rule.id).count()
    if incident_count > 0:
        # Safely disable the rule instead of breaking foreign keys
        rule.is_enabled = False
        rule.updated_at = datetime.now(timezone.utc)
        action = "RULE_DISABLED_DUE_TO_HISTORY"
        msg = f"Rule '{rule.name}' is referenced by {incident_count} incidents and was disabled instead of deleted."
    else:
        db.delete(rule)
        action = "RULE_DELETED"
        msg = f"Rule '{rule.name}' deleted successfully."

    log_audit_event(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action=action,
        target_type="incident_rule",
        target_id=rule_id
    )
    db.commit()
    return {"message": msg, "action": action}
