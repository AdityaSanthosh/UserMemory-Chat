from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..database import User
from .utils import decode_access_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    username = payload.get("username")

    if user_id is None or username is None:
        raise credentials_exception

    # Construct user from JWT payload (no DB call needed)
    return User(
        id=user_id,
        username=username,
        hashed_password="",  # Not needed for authenticated requests
        created_at=None,  # Not needed for authenticated requests
    )
