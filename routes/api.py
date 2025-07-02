from fastapi import APIRouter, Depends
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/")
async def root():
    """
    Public endpoint - no authentication required.
    """
    return {
        "message": "Welcome to the FastAPI OAuth App!",
        "status": "public",
        "endpoints": {
            "login": "/auth/login",
            "protected": "/api/protected",
            "user_info": "/auth/me"
        }
    }


@router.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    """
    Protected endpoint - requires authentication.
    """
    return {
        "message": "This is a protected route",
        "user": current_user,
        "status": "authenticated"
    }


@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get user profile information.
    """
    return {
        "profile": current_user,
        "last_login": "Now",  # You can implement proper last login tracking
        "status": "active"
    }
