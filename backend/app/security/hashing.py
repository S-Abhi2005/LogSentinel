import hashlib
import secrets
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def generate_ingestion_key() -> tuple[str, str, str]:
    """
    Generates a secure service ingestion key.
    Returns:
        (raw_key, key_prefix, key_hash)
    The raw_key is only shown once to the user upon creation.
    """
    raw_token = secrets.token_urlsafe(32)
    raw_key = f"ls_live_{raw_token}"
    key_prefix = raw_key[:16]
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return raw_key, key_prefix, key_hash

def hash_raw_key(raw_key: str) -> str:
    """Hashes a raw API key using SHA-256."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
