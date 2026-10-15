from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest, TokenResponse, UserCreate, UserUpdate, 
    ChangePasswordRequest, UserResponse
)
from app.security.hashing import hash_password, verify_password
from app.security.tokens import create_access_token
from app.security.rbac import (
    get_current_user, require_super_admin, require_viewer_or_above
)
from app.core.errors import UnauthorizedException, ConflictException, NotFoundException, BadRequestException
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication & Users"])

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if not user or not verify_password(data.password, user.hashed_password):
        log_audit_event(
            db=db,
            actor_email=data.email,
            actor_role="unknown",
            action="LOGIN_FAILED",
            target_type="auth",
            ip_address=request.client.host if request.client else None
        )
        db.commit()
        raise UnauthorizedException("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedException("Account is deactivated. Contact an administrator.")

    token = create_access_token(subject=user.id, role=user.role)
    
    log_audit_event(
        db=db,
        actor_email=user.email,
        actor_role=user.role,
        action="LOGIN_SUCCESS",
        target_type="auth",
        target_id=user.id,
        ip_address=request.client.host if request.client else None
    )
    db.commit()

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise BadRequestException("Current password does not match")
    
    current_user.hashed_password = hash_password(data.new_password)
    current_user.updated_at = datetime.now(timezone.utc)
    
    log_audit_event(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="PASSWORD_CHANGED",
        target_type="user",
        target_id=current_user.id
    )
    db.commit()
    return {"message": "Password updated successfully"}

@router.get("/users", response_model=List[UserResponse])
def list_users(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    return db.query(User).order_by(User.created_at.desc()).all()

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if existing:
        raise ConflictException(f"User with email '{data.email}' already exists")
    
    if data.role not in UserRole.ALL:
        raise BadRequestException(f"Invalid role. Allowed roles: {UserRole.ALL}")

    user = User(
        email=data.email.lower().strip(),
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        is_active=True
    )
    db.add(user)
    db.flush()

    log_audit_event(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="USER_CREATED",
        target_type="user",
        target_id=user.id,
        details={"created_email": user.email, "role": user.role}
    )
    db.commit()
    db.refresh(user)
    return user

@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    data: UserUpdate,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User", user_id)

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role is not None:
        if data.role not in UserRole.ALL:
            raise BadRequestException(f"Invalid role. Allowed: {UserRole.ALL}")
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active

    user.updated_at = datetime.now(timezone.utc)
    
    log_audit_event(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="USER_UPDATED",
        target_type="user",
        target_id=user.id,
        details={"updated_fields": data.dict(exclude_unset=True)}
    )
    db.commit()
    db.refresh(user)
    return user
