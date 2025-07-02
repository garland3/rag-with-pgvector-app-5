from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.token_manager import token_manager


security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get the current authenticated user from JWT token.
    """
    token = credentials.credentials
    payload = token_manager.verify_token(token)
    user_info = token_manager.extract_user_info(payload)
    
    if not user_info.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    return user_info


async def get_current_user_optional(request: Request) -> Optional[dict]:
    """
    Optional dependency to get the current user if authenticated.
    Returns None if not authenticated instead of raising an exception.
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        payload = token_manager.verify_token(token)
        user_info = token_manager.extract_user_info(payload)
        
        if not user_info.get("user_id"):
            return None
            
        return user_info
    except:
        return None
