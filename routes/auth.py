from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from auth import oauth_client, token_manager, get_current_user
import secrets

router = APIRouter(prefix="/auth", tags=["authentication"])

# Store states temporarily (in production, use Redis or database)
_states = {}


@router.get("/login")
async def login():
    """
    Initiate OAuth login flow.
    """
    try:
        auth_url, state = oauth_client.get_authorization_url()
        
        # Store state temporarily (in production, use proper session management)
        _states[state] = True
        
        return {
            "auth_url": auth_url,
            "message": "Redirect to this URL to begin authentication"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate login URL: {str(e)}"
        )


@router.get("/callback")
async def auth_callback(code: str = None, state: str = None, error: str = None):
    """
    Handle OAuth callback and exchange code for tokens.
    """
    if error:
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .error {{ color: #dc3545; background: #f8d7da; padding: 20px; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h2>❌ Authentication Error</h2>
                <p>OAuth error: {error}</p>
                <a href="/">← Back to Home</a>
            </div>
        </body>
        </html>
        """)
    
    if not code or not state:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Error</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .error { color: #dc3545; background: #f8d7da; padding: 20px; border-radius: 8px; }
            </style>
        </head>
        <body>
            <div class="error">
                <h2>❌ Authentication Error</h2>
                <p>Missing code or state parameter</p>
                <a href="/">← Back to Home</a>
            </div>
        </body>
        </html>
        """)
    
    # Verify state (in production, use proper session management)
    if state not in _states:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Error</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .error { color: #dc3545; background: #f8d7da; padding: 20px; border-radius: 8px; }
            </style>
        </head>
        <body>
            <div class="error">
                <h2>❌ Authentication Error</h2>
                <p>Invalid state parameter - possible CSRF attack</p>
                <a href="/">← Back to Home</a>
            </div>
        </body>
        </html>
        """)
    
    # Remove used state
    del _states[state]
    
    try:
        # Exchange code for tokens and get user info
        oauth_result = await oauth_client.exchange_code_for_tokens(code)
        user_info = oauth_result["user_info"]
        
        # Create our own JWT token
        token_data = {
            "sub": user_info.get("sub") or user_info.get("user_id") or user_info.get("id"),
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
        }
        
        access_token = token_manager.create_access_token(token_data)
        
        # Return success page with token
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Success</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}
                .success-container {{
                    background: white;
                    padding: 40px;
                    border-radius: 15px;
                    box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 500px;
                    width: 100%;
                }}
                .success-icon {{ font-size: 64px; margin-bottom: 20px; }}
                h1 {{ color: #333; margin-bottom: 10px; }}
                .user-info {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                    text-align: left;
                }}
                .user-info h3 {{ color: #333; margin-bottom: 10px; }}
                .user-info p {{ color: #666; margin: 5px 0; }}
                .token-section {{
                    background: #e9ecef;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .token-section h4 {{ color: #333; margin-bottom: 10px; }}
                .token {{ 
                    font-family: monospace; 
                    font-size: 12px; 
                    word-break: break-all; 
                    background: white; 
                    padding: 10px; 
                    border-radius: 5px;
                    margin: 10px 0;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 25px;
                    margin: 10px 5px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 500;
                    transition: all 0.3s ease;
                }}
                .btn-primary {{ background: #007bff; color: white; }}
                .btn-primary:hover {{ background: #0056b3; }}
                .btn-success {{ background: #28a745; color: white; }}
                .btn-success:hover {{ background: #1e7e34; }}
                .copy-btn {{
                    background: #6c757d;
                    color: white;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                }}
                .copy-btn:hover {{ background: #545b62; }}
            </style>
        </head>
        <body>
            <div class="success-container">
                <div class="success-icon">✅</div>
                <h1>Login Successful!</h1>
                <p>Welcome to FastAPI OAuth App</p>
                
                <div class="user-info">
                    <h3>User Information:</h3>
                    <p><strong>Name:</strong> {token_data.get('name', 'N/A')}</p>
                    <p><strong>Email:</strong> {token_data.get('email', 'N/A')}</p>
                    <p><strong>User ID:</strong> {token_data.get('sub', 'N/A')}</p>
                </div>
                
                <div class="token-section">
                    <h4>🔑 Your Access Token:</h4>
                    <div class="token" id="token">{access_token}</div>
                    <button class="copy-btn" onclick="copyToken()">📋 Copy Token</button>
                    <p style="font-size: 12px; color: #666; margin-top: 10px;">
                        Use this token in the Authorization header: <code>Bearer &lt;token&gt;</code>
                    </p>
                </div>
                
                <div>
                    <a href="/" class="btn btn-primary">🏠 Go to Home</a>
                    <a href="/api/protected" class="btn btn-success">🔒 Try Protected Route</a>
                </div>
            </div>

            <script>
                function copyToken() {{
                    const token = document.getElementById('token').textContent;
                    navigator.clipboard.writeText(token).then(function() {{
                        const btn = document.querySelector('.copy-btn');
                        btn.textContent = '✅ Copied!';
                        setTimeout(() => {{
                            btn.textContent = '📋 Copy Token';
                        }}, 2000);
                    }});
                }}
                
                // Store token in localStorage for demo purposes
                localStorage.setItem('access_token', '{access_token}');
                
                // Auto-redirect after 10 seconds
                setTimeout(() => {{
                    window.location.href = '/';
                }}, 10000);
            </script>
        </body>
        </html>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .error {{ color: #dc3545; background: #f8d7da; padding: 20px; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h2>❌ Authentication Error</h2>
                <p>Authentication failed: {str(e)}</p>
                <a href="/">← Back to Home</a>
            </div>
        </body>
        </html>
        """)


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client should discard the token).
    """
    return {"message": "Logged out successfully. Please discard your access token."}


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user information.
    """
    return {
        "user": current_user,
        "message": "User authenticated successfully"
    }
