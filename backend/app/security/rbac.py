from typing import List, Optional
from datetime import datetime, timezone
from fastapi import Depends, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.service import Service, ServiceIngestionKey
from app.core.errors import UnauthorizedException, ForbiddenException
from app.security.tokens import decode_access_token, is_token_revoked
from app.security.hashing import hash_raw_key

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Validate JWT access token and return current User."""
    if not credentials:
        raise UnauthorizedException("Authentication token missing")
    
    token = credentials.credentials
    if is_token_revoked(token):
        raise UnauthorizedException("Access token has been revoked")

    payload = decode_access_token(token)
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Token payload missing user identifier")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedException("User associated with token not found")
    if not user.is_active:
        raise ForbiddenException("User account is deactivated")
    
    return user

def require_roles(allowed_roles: List[str]):
    """Enforce role-based access control."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(
                f"Action requires one of the following roles: {', '.join(allowed_roles)}. Current role: {current_user.role}"
            )
        return current_user
    return role_checker

# Role-specific shortcuts
require_super_admin = require_roles([UserRole.SUPER_ADMIN])
require_engineer_or_admin = require_roles([UserRole.SUPER_ADMIN, UserRole.ENGINEER])
require_viewer_or_above = require_roles([UserRole.SUPER_ADMIN, UserRole.ENGINEER, UserRole.VIEWER])

def validate_ingestion_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> Service:
    """
    Validates service ingestion API key against active service ingestion keys in the database.
    Updates the key's last_used_at timestamp.
    Returns the authenticated Service model.
    """
    if not x_api_key:
        raise UnauthorizedException("Missing X-API-Key header for log ingestion")
    
    raw_key = x_api_key.strip()
    key_hash = hash_raw_key(raw_key)
    
    ingestion_key = db.query(ServiceIngestionKey).filter(
        ServiceIngestionKey.key_hash == key_hash,
        ServiceIngestionKey.is_revoked == False
    ).first()
    
    if not ingestion_key:
        raise UnauthorizedException("Invalid or revoked ingestion API key")
    
    service = db.query(Service).filter(Service.id == ingestion_key.service_id).first()
    if not service or not service.is_enabled:
        raise ForbiddenException("Associated service is disabled or does not exist")
    
    # Update last_used_at timestamp
    ingestion_key.last_used_at = datetime.now(timezone.utc)
    db.commit()
    
    return service
