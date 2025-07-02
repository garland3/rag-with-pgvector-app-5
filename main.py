from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from routes import auth_router, api_router, user_router, project_router, document_router, search_router, chat_router
from auth import get_current_user_optional
from config import settings
from database import Base, engine, SessionLocal
from models import User, Project

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="RAG Application",
    description="A multi-tenant RAG application with project-based access control.",
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
app.include_router(user_router)
app.include_router(project_router)
app.include_router(document_router)
app.include_router(search_router)
app.include_router(chat_router)


@app.get("/", response_class=HTMLResponse)
async def root(current_user: dict = Depends(get_current_user_optional)):
    """
    Home page with a modern UI for the RAG application.
    """
    db = SessionLocal()
    projects = []
    if current_user:
        user = db.query(User).filter(User.auth0_id == current_user["user_id"]).first()
        if user:
            projects = db.query(Project).filter(Project.owner_id == user.id).all()
    db.close()
    
    return await get_rag_home_page(current_user, projects)


async def get_rag_home_page(current_user: dict = None, projects: list = []):
    """
    Generate the home page HTML for the RAG application.
    """
    if current_user:
        project_list_items = ""
        if projects:
            for project in projects:
                project_list_items += f"<li class='project-item'><strong>{project.name}</strong>: {project.description}</li>"
        else:
            project_list_items = "<p>No projects found. Create one below!</p>"

        user_section = f"""
        <div class="dashboard">
            <div class="user-info">
                <img src="{current_user.get('picture', '')}" alt="User" class="avatar">
                <div>
                    <h2>Welcome, {current_user.get('name', 'User')}!</h2>
                    <p>{current_user.get('email', '')}</p>
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
                <form action="/projects" method="post">
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
