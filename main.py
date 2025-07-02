from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from routes import auth_router, api_router
from auth import get_current_user_optional
from config import settings

# Create FastAPI app
app = FastAPI(
    title="FastAPI OAuth App",
    description="A simple FastAPI application with generic OAuth authentication",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def root(current_user: dict = Depends(get_current_user_optional)):
    """
    Home page with simple HTML interface.
    """
    return await get_home_page(current_user)


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """
    Login page with simple UI to start OAuth flow.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - FastAPI OAuth App</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .login-container {
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                text-align: center;
                max-width: 400px;
                width: 90%;
            }
            .logo { font-size: 48px; margin-bottom: 20px; }
            h1 { color: #333; margin-bottom: 10px; font-weight: 300; }
            .subtitle { color: #666; margin-bottom: 30px; }
            .login-btn {
                background: #007bff;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                transition: all 0.3s ease;
                margin: 10px 0;
            }
            .login-btn:hover {
                background: #0056b3;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,123,255,0.3);
            }
            .home-link {
                color: #666;
                text-decoration: none;
                font-size: 14px;
                margin-top: 20px;
                display: inline-block;
            }
            .home-link:hover { color: #007bff; }
            .loading { display: none; margin-top: 20px; color: #666; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">🔐</div>
            <h1>Welcome</h1>
            <p class="subtitle">Sign in to access your account</p>
            
            <button class="login-btn" onclick="startLogin()">
                Sign In with OAuth
            </button>
            
            <div class="loading" id="loading">
                <p>🔄 Redirecting to login...</p>
            </div>
            
            <a href="/" class="home-link">← Back to Home</a>
        </div>

        <script>
            async function startLogin() {
                document.getElementById('loading').style.display = 'block';
                
                try {
                    const response = await fetch('/auth/login');
                    const data = await response.json();
                    
                    if (data.auth_url) {
                        window.location.href = data.auth_url;
                    } else {
                        alert('Error getting login URL');
                        document.getElementById('loading').style.display = 'none';
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                    document.getElementById('loading').style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content


@app.get("/logout", response_class=HTMLResponse)
async def logout_page():
    """
    Logout page with confirmation.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logout - FastAPI OAuth App</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .logout-container {
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                text-align: center;
                max-width: 400px;
                width: 90%;
            }
            .logo { font-size: 48px; margin-bottom: 20px; }
            h1 { color: #333; margin-bottom: 10px; font-weight: 300; }
            .subtitle { color: #666; margin-bottom: 30px; }
            .btn {
                padding: 12px 25px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 5px;
                transition: all 0.3s ease;
            }
            .logout-btn {
                background: #dc3545;
                color: white;
            }
            .logout-btn:hover {
                background: #c82333;
                transform: translateY(-1px);
            }
            .cancel-btn {
                background: #6c757d;
                color: white;
            }
            .cancel-btn:hover {
                background: #545b62;
                transform: translateY(-1px);
            }
            .success-message {
                display: none;
                color: #28a745;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="logout-container">
            <div class="logo">👋</div>
            <h1>Sign Out</h1>
            <p class="subtitle">Are you sure you want to sign out?</p>
            
            <div id="buttons">
                <button class="btn logout-btn" onclick="confirmLogout()">
                    Yes, Sign Out
                </button>
                <a href="/" class="btn cancel-btn">
                    Cancel
                </a>
            </div>
            
            <div class="success-message" id="success">
                <p>✅ You have been signed out successfully!</p>
                <a href="/" class="btn cancel-btn" style="margin-top: 15px;">
                    Go to Home
                </a>
            </div>
        </div>

        <script>
            async function confirmLogout() {
                try {
                    // Clear any stored tokens (if using localStorage)
                    localStorage.removeItem('access_token');
                    sessionStorage.removeItem('access_token');
                    
                    // Call logout endpoint
                    await fetch('/auth/logout', { method: 'POST' });
                    
                    // Show success message
                    document.getElementById('buttons').style.display = 'none';
                    document.getElementById('success').style.display = 'block';
                    
                    // Redirect after delay
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 2000);
                    
                } catch (error) {
                    alert('Error during logout: ' + error.message);
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content


async def get_home_page(current_user: dict = None):
    """
    Generate the home page HTML based on authentication status.
    """
    if current_user:
        user_section = f"""
        <div class="user-info">
            <div class="user-avatar">
                <img src="{current_user.get('picture', '/static/default-avatar.png')}" 
                     alt="Profile" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiNFNUU1RTUiLz4KPGNpcmNsZSBjeD0iMjAiIGN5PSIxNiIgcj0iNiIgZmlsbD0iIzk5OTk5OSIvPgo8cGF0aCBkPSJNMzAgMzJDMzAgMjYuNDc3MSAyNS41MjI5IDIyIDIwIDIyQzE0LjQ3NzEgMjIgMTAgMjYuNDc3MSAxMCAzMiIgZmlsbD0iIzk5OTk5OSIvPgo8L3N2Zz4K'">
            </div>
            <div class="user-details">
                <h3>Welcome back, {current_user.get('name', 'User')}!</h3>
                <p class="user-email">{current_user.get('email', 'N/A')}</p>
                <p class="user-id">ID: {current_user.get('user_id', 'N/A')}</p>
            </div>
        </div>
        
        <div class="actions">
            <a href="/api/protected" class="btn btn-primary">Protected Route</a>
            <a href="/api/profile" class="btn btn-success">My Profile</a>
            <a href="/logout" class="btn btn-danger">Sign Out</a>
        </div>
        """
    else:
        user_section = """
        <div class="welcome-message">
            <h2>Welcome to FastAPI OAuth App</h2>
            <p>A simple demonstration of OAuth 2.0 authentication with FastAPI</p>
        </div>
        
        <div class="actions">
            <a href="/login" class="btn btn-primary btn-large">🔑 Sign In</a>
        </div>
        
        <div class="info-section">
            <h3>Features</h3>
            <ul>
                <li>✅ Generic OAuth 2.0 implementation</li>
                <li>✅ Works with Auth0, Google, GitHub, etc.</li>
                <li>✅ JWT token management</li>
                <li>✅ Protected API routes</li>
            </ul>
        </div>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>FastAPI OAuth App</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
            .header p {{ opacity: 0.9; }}
            .content {{ padding: 40px; }}
            .user-info {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
                display: flex;
                align-items: center;
                gap: 20px;
            }}
            .user-avatar img {{
                width: 60px;
                height: 60px;
                border-radius: 50%;
                border: 3px solid #007bff;
            }}
            .user-details h3 {{ color: #333; margin-bottom: 5px; }}
            .user-email {{ color: #007bff; font-weight: 500; }}
            .user-id {{ color: #666; font-size: 0.9em; }}
            .welcome-message {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .welcome-message h2 {{ 
                color: #333; 
                margin-bottom: 10px; 
                font-weight: 300;
            }}
            .welcome-message p {{ color: #666; }}
            .actions {{
                text-align: center;
                margin: 30px 0;
            }}
            .btn {{
                display: inline-block;
                padding: 12px 25px;
                margin: 8px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 500;
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
            }}
            .btn-large {{ padding: 15px 40px; font-size: 1.1em; }}
            .btn-primary {{ background: #007bff; color: white; }}
            .btn-primary:hover {{ background: #0056b3; transform: translateY(-2px); }}
            .btn-success {{ background: #28a745; color: white; }}
            .btn-success:hover {{ background: #1e7e34; transform: translateY(-2px); }}
            .btn-danger {{ background: #dc3545; color: white; }}
            .btn-danger:hover {{ background: #c82333; transform: translateY(-2px); }}
            .btn-secondary {{ background: #6c757d; color: white; }}
            .btn-secondary:hover {{ background: #545b62; transform: translateY(-2px); }}
            .info-section {{
                background: #f8f9fa;
                padding: 25px;
                border-radius: 10px;
                margin-top: 30px;
            }}
            .info-section h3 {{ 
                color: #333; 
                margin-bottom: 15px; 
                text-align: center;
            }}
            .info-section ul {{
                list-style: none;
                max-width: 400px;
                margin: 0 auto;
            }}
            .info-section li {{
                padding: 8px 0;
                color: #555;
            }}
            .api-links {{
                background: #e9ecef;
                padding: 20px;
                border-radius: 10px;
                margin-top: 20px;
                text-align: center;
            }}
            .api-links h4 {{ color: #333; margin-bottom: 15px; }}
            @media (max-width: 600px) {{
                .user-info {{ flex-direction: column; text-align: center; }}
                .actions {{ flex-direction: column; }}
                .btn {{ display: block; margin: 10px auto; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 FastAPI OAuth</h1>
                <p>Secure authentication made simple</p>
            </div>
            
            <div class="content">
                {user_section}
                
                <div class="api-links">
                    <h4>🔗 Developer Resources</h4>
                    <a href="/docs" class="btn btn-secondary">📚 API Docs (Swagger)</a>
                    <a href="/redoc" class="btn btn-secondary">📖 ReDoc</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug
    )
