from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from auth.oauth_client import oauth_client
from auth.token_manager import token_manager
from crud.user_manager import get_user_by_auth0_id, create_user, update_user
from database import get_db
from schemas import UserCreate, UserUpdate

router = APIRouter(prefix="/auth", tags=["authentication"])

# In-memory store for OAuth state (replace with Redis in production)
_states = {}


@router.get("/login")
async def login():
    """
    Initiates the OAuth 2.0 login flow by generating an authorization URL.
    """
    try:
        auth_url, state = oauth_client.get_authorization_url()
        _states[state] = True  # Store state to prevent CSRF
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate login URL: {e}",
        )


@router.get("/callback")
async def auth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
    error: str = None,
):
    """
    Handles the OAuth 2.0 callback, exchanges the code for a token,
    and creates or updates the user in the database.
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error}",
        )
    if state not in _states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )
    del _states[state]

    try:
        # Exchange authorization code for tokens
        oauth_result = await oauth_client.exchange_code_for_tokens(code)
        user_info = oauth_result["user_info"]
        auth0_id = user_info.get("sub")

        if not auth0_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Auth0 user ID not found in token",
            )

        # Check if user exists, otherwise create them
        user = get_user_by_auth0_id(db, auth0_id)
        if user:
            user_update = UserUpdate(
                email=user_info.get("email"),
                name=user_info.get("name"),
                picture=user_info.get("picture"),
            )
            update_user(db, user, user_update)
        else:
            user_create = UserCreate(
                auth0_id=auth0_id,
                email=user_info.get("email"),
                name=user_info.get("name"),
                picture=user_info.get("picture"),
            )
            create_user(db, user_create)

        # Create internal JWT access token
        access_token = token_manager.create_access_token(
            data={"sub": auth0_id}
        )

        # Return a simple success page with the token
        return HTMLResponse(
            content=f"""
            <html>
                <body>
                    <h1>Login Successful</h1>
                    <p>Your access token is: <code>{access_token}</code></p>
                </body>
            </html>
            """
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {e}",
        )

