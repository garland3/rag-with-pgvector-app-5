from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from auth.token_manager import token_manager
from crud.user_manager import get_user_by_auth0_id
from database import get_db
from models.user import User

security = HTTPBearer()


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    Dependency to get the current authenticated user from the database.
    """
    token = credentials.credentials
    payload = token_manager.verify_token(token)
    auth0_id = payload.get("sub")

    if not auth0_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user = get_user_by_auth0_id(db, auth0_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def get_current_user_optional(
    db: Session = Depends(get_db),
    request: Request = None,
) -> Optional[User]:
    """
    Optional dependency to get the current user if authenticated.
    Returns None if not authenticated.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    try:
        payload = token_manager.verify_token(token)
        auth0_id = payload.get("sub")
        if not auth0_id:
            return None
        return get_user_by_auth0_id(db, auth0_id)
    except HTTPException:
        return None
