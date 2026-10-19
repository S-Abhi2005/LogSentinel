from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from app.core.config import settings
from app.core.errors import UnauthorizedException

def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Access token has expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedException("Invalid access token")

# In-memory revocation set for active tokens
REVOKED_TOKENS: set[str] = set()

def revoke_token(token: str) -> None:
    """Marks an access token as revoked."""
    REVOKED_TOKENS.add(token.strip())

def is_token_revoked(token: str) -> bool:
    """Checks whether an access token has been revoked."""
    return token.strip() in REVOKED_TOKENS
