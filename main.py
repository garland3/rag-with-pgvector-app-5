from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from routes import auth_router, api_router, user_router, project_router, document_router, search_router, chat_router
from auth import get_current_user_optional
from config import settings
from database import Base, engine, SessionLocal
# Import models to register them with Base
from models.project import Project  
from utils.logging import setup_logging, get_logger, log_api_request, log_error
import time

# Set up logging
setup_logging(
    log_level="INFO",
    log_file="logs/app.log"
)
logger = get_logger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="RAG Application",
    description="A multi-tenant RAG application with project-based access control.",
    version="1.0.0"
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log successful requests
        log_api_request(
            logger,
            method=request.method,
            endpoint=str(request.url.path),
            duration=process_time
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        
        # Log errors
        log_error(logger, e, {
            "method": request.method,
            "endpoint": str(request.url.path),
            "duration": process_time
        })
        
        # Re-raise the exception
        raise

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
app.include_router(user_router)
app.include_router(project_router)
app.include_router(document_router)
app.include_router(search_router)
app.include_router(chat_router)


@app.get("/", response_class=HTMLResponse)
async def root(current_user = Depends(get_current_user_optional)):
    """
    Home page with a modern UI for the RAG application.
    """
    db = SessionLocal()
    projects = []
    if current_user:
        projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    db.close()
    
    return await get_rag_home_page(current_user, projects)


@app.get("/login")
async def login_redirect():
    """
    Redirect /login to /auth/login for convenience.
    """
    return RedirectResponse(url="/auth/login", status_code=302)


@app.get("/logout")
async def logout_redirect():
    """
    Redirect /logout to home page (simple logout for now).
    """
    return RedirectResponse(url="/", status_code=302)


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify system configuration.
    """
    from config import settings
    
    config_status = {
        "oauth_configured": bool(settings.oauth_client_id and settings.oauth_client_secret and settings.oauth_domain),
        "jwt_configured": bool(settings.jwt_secret_key),
        "gemini_configured": bool(settings.gemini_api_key),
        "database_configured": bool(settings.database_url),
    }
    
    # Test database connection
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        config_status["database_connected"] = True
    except Exception as e:
        config_status["database_connected"] = False
        config_status["database_error"] = str(e)
    
    all_configured = all([
        config_status["oauth_configured"],
        config_status["jwt_configured"], 
        config_status["gemini_configured"],
        config_status["database_connected"]
    ])
    
    return {
        "status": "healthy" if all_configured else "configuration_needed",
        "config": config_status
    }


async def get_rag_home_page(current_user: dict = None, projects: list = []):
    """
    Generate the home page HTML for the RAG application.
    """
    if current_user:
        project_list_items = ""
        if projects:
            for project in projects:
                project_list_items += f"<li class='project-item'><a href='/projects/{project.id}/dashboard' class='project-link'><strong>{project.name}</strong>: {project.description}</a></li>"
        else:
            project_list_items = "<p>No projects found. Create one below!</p>"

        user_section = f"""
        <div class="dashboard">
            <div class="user-info">
                <img src="{current_user.picture or ''}" alt="User" class="avatar">
                <div>
                    <h2>Welcome, {current_user.name or 'User'}!</h2>
                    <p>{current_user.email or ''}</p>
                </div>
                <a href="/logout" class="btn btn-danger">Logout</a>
            </div>

            <div class="projects-section">
                <h3>Your Projects</h3>
                <ul class="project-list">
                    {project_list_items}
                </ul>
            </div>

            <div class="create-project-form">
                <h3>Create a New Project</h3>
                <form action="/projects/create" method="post">
                    <input type="text" name="name" placeholder="Project Name" required>
                    <input type="text" name="description" placeholder="Project Description" required>
                    <button type="submit" class="btn btn-primary">Create Project</button>
                </form>
            </div>
        </div>
        """
    else:
        user_section = """
        <div class="landing-page">
            <h1>Welcome to the RAG Application</h1>
            <p>Create knowledge bases from your documents and chat with them.</p>
            <a href="/login" class="btn btn-primary btn-large">Get Started</a>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAG Application</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                background-color: #f0f2f5;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }}
            .container {{
                width: 100%;
                max-width: 900px;
                margin: 20px;
                padding: 40px;
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .btn {{
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
            }}
            .btn-primary {{
                background-color: #007bff;
                color: white;
            }}
            .btn-danger {{
                background-color: #dc3545;
                color: white;
            }}
            .btn-large {{
                padding: 15px 30px;
                font-size: 18px;
            }}
            .landing-page {{
                text-align: center;
            }}
            .dashboard .user-info {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 30px;
            }}
            .dashboard .avatar {{
                width: 50px;
                height: 50px;
                border-radius: 50%;
                margin-right: 15px;
            }}
            .projects-section, .create-project-form {{
                margin-bottom: 30px;
            }}
            .project-list {{
                list-style: none;
                padding: 0;
            }}
            .project-item {{
                padding: 10px;
                border-bottom: 1px solid #eeeeee;
            }}
            .project-link {{
                color: #007bff;
                text-decoration: none;
                display: block;
                padding: 5px;
                border-radius: 4px;
                transition: background-color 0.2s;
            }}
            .project-link:hover {{
                background-color: #f8f9fa;
                text-decoration: none;
            }}
            .create-project-form input[type="text"] {{
                width: 100%;
                padding: 10px;
                margin-bottom: 10px;
                border: 1px solid #cccccc;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            {user_section}
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
