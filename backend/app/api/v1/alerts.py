from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.models.user import User
from app.models.alert import Alert
from app.schemas.alert import AlertResponse, AlertListResponse
from app.security.rbac import require_viewer_or_above
from app.core.errors import NotFoundException

router = APIRouter(prefix="/alerts", tags=["In-App Alerts"])

@router.get("", response_model=AlertListResponse)
def list_alerts(
    is_read: Optional[bool] = None,
    limit: int = 50,
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)
    
    total = query.count()
    items = query.order_by(desc(Alert.created_at)).limit(limit).all()
    unread_count = db.query(Alert).filter(Alert.is_read == False).count()

    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in items],
        unread_count=unread_count,
        total=total
    )

@router.post("/{alert_id}/read", response_model=AlertResponse)
def mark_alert_read(
    alert_id: str,
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise NotFoundException("Alert", alert_id)
    
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert

@router.post("/read-all")
def mark_all_alerts_read(
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    db.query(Alert).filter(Alert.is_read == False).update({"is_read": True})
    db.commit()
    return {"message": "All alerts marked as read"}
