from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from crud.project_manager import create_project as create_project_crud, get_projects_by_owner
from database import get_db
from models.user import User
from models.project import Project as ProjectModel
from schemas import Project, ProjectCreate
from typing import List

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=Project)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new project.
    """
    return create_project_crud(db=db, project=project, owner_id=current_user.id)


@router.post("/create")
def create_project_form(
    name: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new project from HTML form submission.
    """
    project_data = ProjectCreate(name=name, description=description)
    create_project_crud(db=db, project=project_data, owner_id=current_user.id)
    return RedirectResponse(url="/", status_code=302)


@router.get("/", response_model=List[Project])
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all projects for the current user.
    """
    return get_projects_by_owner(db=db, owner_id=current_user.id)


@router.get("/{project_id}/dashboard", response_class=HTMLResponse)
def get_project_dashboard(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the project-specific dashboard for document upload and chat.
    """
    # Check if project exists and belongs to current user
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return get_project_dashboard_html(project)


def get_project_dashboard_html(project: ProjectModel):
    """
    Generate the HTML for the project dashboard.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{project.name} - Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                background-color: #f0f2f5;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                padding: 30px;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid #e9ecef;
            }}
            .project-info h1 {{
                color: #2c3e50;
                margin: 0;
            }}
            .project-info p {{
                color: #6c757d;
                margin: 5px 0 0 0;
            }}
            .nav-buttons {{
                display: flex;
                gap: 10px;
            }}
            .btn {{
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                transition: background-color 0.2s;
            }}
            .btn-primary {{
                background-color: #007bff;
                color: white;
            }}
            .btn-primary:hover {{
                background-color: #0056b3;
            }}
            .btn-secondary {{
                background-color: #6c757d;
                color: white;
            }}
            .btn-secondary:hover {{
                background-color: #545b62;
            }}
            .dashboard-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin-top: 30px;
            }}
            .card {{
                background: #f8f9fa;
                border-radius: 8px;
                padding: 25px;
                border-left: 4px solid #007bff;
            }}
            .card h2 {{
                color: #2c3e50;
                margin-top: 0;
            }}
            .card p {{
                color: #6c757d;
                margin-bottom: 20px;
            }}
            .upload-area {{
                border: 2px dashed #007bff;
                border-radius: 8px;
                padding: 40px;
                text-align: center;
                margin-bottom: 20px;
                cursor: pointer;
                transition: background-color 0.2s;
            }}
            .upload-area:hover {{
                background-color: #f0f8ff;
            }}
            .upload-area input[type="file"] {{
                display: none;
            }}
            .chat-area {{
                border: 1px solid #dee2e6;
                border-radius: 8px;
                height: 400px;
                display: flex;
                flex-direction: column;
            }}
            .chat-messages {{
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                background-color: #fff;
            }}
            .chat-input {{
                display: flex;
                padding: 15px;
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
            }}
            .chat-input input {{
                flex: 1;
                padding: 10px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                margin-right: 10px;
            }}
            @media (max-width: 768px) {{
                .dashboard-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="project-info">
                    <h1>{project.name}</h1>
                    <p>{project.description}</p>
                </div>
                <div class="nav-buttons">
                    <a href="/" class="btn btn-secondary">← Back to Home</a>
                </div>
            </div>
            
            <div class="dashboard-grid">
                <div class="card">
                    <h2>📁 Document Upload</h2>
                    <p>Upload documents to build your knowledge base</p>
                    
                    <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                        <input type="file" id="fileInput" multiple accept=".pdf,.doc,.docx,.txt,.md">
                        <p>📄 Click to upload files</p>
                        <p>Supported formats: PDF, DOC, DOCX, TXT, MD</p>
                    </div>
                    
                    <div id="fileList"></div>
                    <button class="btn btn-primary" onclick="uploadFiles()">Upload Documents</button>
                </div>
                
                <div class="card">
                    <h2>💬 Chat with Documents</h2>
                    <p>Ask questions about your uploaded documents</p>
                    
                    <div class="chat-area">
                        <div class="chat-messages" id="chatMessages">
                            <p style="text-align: center; color: #6c757d; margin-top: 50px;">
                                Upload some documents to start chatting!
                            </p>
                        </div>
                        <div class="chat-input">
                            <input type="text" id="chatInput" placeholder="Ask a question about your documents...">
                            <button class="btn btn-primary" onclick="sendMessage()">Send</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            const projectId = {project.id};
            
            function uploadFiles() {{
                const fileInput = document.getElementById('fileInput');
                const files = fileInput.files;
                
                if (files.length === 0) {{
                    alert('Please select files to upload');
                    return;
                }}
                
                const formData = new FormData();
                for (let i = 0; i < files.length; i++) {{
                    formData.append('files', files[i]);
                }}
                
                fetch(`/documents/upload/${{projectId}}`, {{
                    method: 'POST',
                    body: formData
                }})
                .then(response => response.json())
                .then(data => {{
                    alert('Files uploaded successfully!');
                    fileInput.value = '';
                    document.getElementById('fileList').innerHTML = '';
                }})
                .catch(error => {{
                    alert('Error uploading files: ' + error);
                }});
            }}
            
            function sendMessage() {{
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                
                if (!message) return;
                
                const messagesDiv = document.getElementById('chatMessages');
                messagesDiv.innerHTML += `<div style="margin-bottom: 10px;"><strong>You:</strong> ${{message}}</div>`;
                
                input.value = '';
                
                fetch(`/chat/query/${{projectId}}`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{ query: message }})
                }})
                .then(response => response.json())
                .then(data => {{
                    messagesDiv.innerHTML += `<div style="margin-bottom: 10px; padding: 10px; background: #f0f8ff; border-radius: 4px;"><strong>Assistant:</strong> ${{data.response}}</div>`;
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }})
                .catch(error => {{
                    messagesDiv.innerHTML += `<div style="margin-bottom: 10px; color: red;"><strong>Error:</strong> ${{error}}</div>`;
                }});
            }}
            
            // Handle file selection display
            document.getElementById('fileInput').addEventListener('change', function(e) {{
                const fileList = document.getElementById('fileList');
                const files = Array.from(e.target.files);
                
                fileList.innerHTML = files.map(file => 
                    `<div style="padding: 5px; background: #e9ecef; margin: 5px 0; border-radius: 3px;">${{file.name}}</div>`
                ).join('');
            }});
            
            // Handle enter key in chat input
            document.getElementById('chatInput').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    sendMessage();
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html_content
