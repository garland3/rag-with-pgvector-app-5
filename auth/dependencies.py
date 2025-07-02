from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from auth.token_manager import token_manager
from crud.user_manager import get_user_by_auth0_id
from database import get_db
from models.user import User

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user from the database.
    """
    # Try to get token from cookie first, then from Authorization header
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token provided",
        )

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
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Optional dependency to get the current user if authenticated.
    Returns None if not authenticated.
    """
    # Try to get token from cookie first, then from Authorization header
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        return None

    try:
        payload = token_manager.verify_token(token)
        auth0_id = payload.get("sub")
        if not auth0_id:
            return None
        return get_user_by_auth0_id(db, auth0_id)
    except HTTPException:
        return None
