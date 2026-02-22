"""
Apple Music token generator service.
Generates JWT bearer tokens for Apple Music API using .p8 private key.
"""

import jwt
import time
from pathlib import Path
from typing import Optional

from app.config import get_settings


def generate_apple_music_token(
    key_path: Optional[str] = None,
    key_id: Optional[str] = None,
    team_id: Optional[str] = None
) -> str:
    """
    Generate JWT bearer token for Apple Music API.
    
    Args:
        key_path: Path to .p8 private key file
        key_id: Apple Music key ID
        team_id: Apple Developer team ID
    
    Returns:
        JWT token string
    """
    settings = get_settings()
    
    # Use provided values or fall back to settings
    key_path = key_path or settings.apple_music_key_path
    key_id = key_id or settings.apple_music_key_id
    team_id = team_id or settings.apple_music_team_id
    
    if not key_path or not key_id or not team_id:
        raise ValueError(
            "Apple Music configuration missing. "
            "Please set apple_music_key_path, apple_music_key_id, and apple_music_team_id"
        )
    
    # Read private key
    with open(key_path, "r") as f:
        private_key = f.read()
    
    # Create JWT payload
    payload = {
        "iss": team_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + (3600 * 24 * 30),  # 30 days max
    }
    
    # Generate token with ES256 algorithm
    token = jwt.encode(
        payload,
        private_key,
        algorithm="ES256",
        headers={"kid": key_id},
    )
    
    return token


def is_token_valid(token: str) -> bool:
    """
    Check if a token is still valid based on expiration claim.
    
    Args:
        token: JWT token string
    
    Returns:
        True if token is valid (not expired), False otherwise
    """
    try:
        # Decode without verification to check exp claim
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = payload.get("exp", 0)
        return int(time.time()) < exp
    except Exception:
        return False
