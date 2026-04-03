"""
Authentication utilities for JWT handling and password management.
"""
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from config.settings import get_settings


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with salt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}${password_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a password against a stored hash.

    Args:
        password: Plain text password to verify
        stored_hash: Stored password hash

    Returns:
        True if password matches, False otherwise
    """
    try:
        salt, password_hash = stored_hash.split("$")
        computed_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return secrets.compare_digest(computed_hash, password_hash)
    except (ValueError, AttributeError):
        return False


def generate_token(user_id: str, email: str) -> str:
    """
    Generate a JWT token for a user.

    Args:
        user_id: User ID
        email: User email

    Returns:
        JWT token string
    """
    settings = get_settings()
    expiration = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)

    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expiration,
        "iat": datetime.utcnow(),
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload or None if invalid
    """
    try:
        settings = get_settings()
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def extract_token_from_header(auth_header: str) -> Optional[str]:
    """
    Extract JWT token from Authorization header.

    Args:
        auth_header: Authorization header value

    Returns:
        Token string or None if invalid format
    """
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


def get_user_from_event(event: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Extract user information from Lambda event.

    Args:
        event: Lambda event dictionary

    Returns:
        User info dictionary or None if not authenticated
    """
    headers = event.get("headers", {}) or {}
    auth_header = headers.get("Authorization") or headers.get("authorization")

    token = extract_token_from_header(auth_header)
    if not token:
        return None

    payload = decode_token(token)
    if not payload:
        return None

    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
    }