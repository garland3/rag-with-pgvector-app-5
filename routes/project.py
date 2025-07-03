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


@router.get("/{project_id}/documents/{document_id}/chunks", response_class=HTMLResponse)
def get_document_chunks(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the chunks view for a specific document.
    """
    from models.document import Document
    from models.chunk import Chunk as ChunkModel
    
    # Check if project exists and belongs to current user
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.project_id == project_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get chunks
    chunks = db.query(ChunkModel).filter(
        ChunkModel.document_id == document_id
    ).all()
    
    return get_document_chunks_html(project, document, chunks)


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
            .chat-section {{
                margin-bottom: 30px;
            }}
            .dashboard-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
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
            .file-list {{
                margin-top: 15px;
                margin-bottom: 20px;
            }}
            .file-item {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 10px;
                background: #e9ecef;
                border-radius: 4px;
                margin: 5px 0;
            }}
            .file-info {{
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .file-icon {{
                font-size: 18px;
            }}
            .file-name {{
                font-weight: 500;
                color: #2c3e50;
            }}
            .file-size {{
                color: #6c757d;
                font-size: 14px;
            }}
            .remove-file {{
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                cursor: pointer;
                font-size: 12px;
            }}
            .remove-file:hover {{
                background: #c82333;
            }}
            .toast {{
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 5px;
                color: white;
                font-weight: 500;
                transform: translateX(100%);
                transition: transform 0.3s ease;
                z-index: 1000;
                min-width: 300px;
            }}
            .toast.show {{
                transform: translateX(0);
            }}
            .toast-success {{
                background-color: #28a745;
            }}
            .toast-error {{
                background-color: #dc3545;
            }}
            .toast-info {{
                background-color: #17a2b8;
            }}
            .progress-container {{
                display: none;
                margin-top: 20px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid #17a2b8;
            }}
            .progress-bar {{
                width: 100%;
                height: 20px;
                background-color: #e9ecef;
                border-radius: 10px;
                overflow: hidden;
                margin: 10px 0;
            }}
            .progress-fill {{
                height: 100%;
                background-color: #007bff;
                transition: width 0.3s ease;
            }}
            .progress-text {{
                text-align: center;
                margin: 10px 0;
                font-weight: 500;
            }}
            .progress-details {{
                font-size: 14px;
                color: #6c757d;
                margin-top: 10px;
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
            .document-list {{
                max-height: 400px;
                overflow-y: auto;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background: white;
            }}
            .document-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 15px;
                border-bottom: 1px solid #f0f0f0;
                transition: background-color 0.2s;
            }}
            .document-item:hover {{
                background-color: #f8f9fa;
            }}
            .document-item:last-child {{
                border-bottom: none;
            }}
            .document-info {{
                display: flex;
                flex-direction: column;
                flex: 1;
                cursor: pointer;
            }}
            .document-info:hover .document-name {{
                color: #007bff;
                text-decoration: underline;
            }}
            .document-name {{
                font-weight: 500;
                color: #2c3e50;
                margin-bottom: 4px;
            }}
            .document-meta {{
                font-size: 12px;
                color: #6c757d;
            }}
            .document-actions {{
                display: flex;
                gap: 8px;
            }}
            .btn-delete {{
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 12px;
                cursor: pointer;
                transition: background-color 0.2s;
            }}
            .btn-delete:hover {{
                background-color: #c82333;
            }}
            .btn-refresh {{
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
                font-size: 14px;
                cursor: pointer;
                transition: background-color 0.2s;
                margin-bottom: 15px;
            }}
            .btn-refresh:hover {{
                background-color: #138496;
            }}
            .no-documents {{
                text-align: center;
                padding: 40px 20px;
                color: #6c757d;
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
            
            <!-- Chat Section - Full Width -->
            <div class="chat-section">
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
            
            <!-- Upload and Library Section - Two Columns -->
            <div class="dashboard-grid">
                <div class="card">
                    <h2>📁 Document Upload</h2>
                    <p>Upload documents to build your knowledge base</p>
                    
                    <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                        <input type="file" id="fileInput" multiple accept=".pdf,.doc,.docx,.txt,.md">
                        <p>📄 Click to upload files</p>
                        <p>Supported formats: PDF, DOC, DOCX, TXT, MD</p>
                    </div>
                    
                    <div id="fileList" class="file-list"></div>
                    <button class="btn btn-primary" onclick="uploadFiles()" id="uploadButton" style="display: none;">Upload Documents</button>
                    
                    <div id="progressContainer" class="progress-container">
                        <h4>Processing Documents...</h4>
                        <div class="progress-bar">
                            <div id="progressFill" class="progress-fill" style="width: 0%"></div>
                        </div>
                        <div id="progressText" class="progress-text">0% Complete</div>
                        <div id="progressDetails" class="progress-details">
                            Processed: <span id="processedCount">0</span> / <span id="totalCount">0</span> files
                            <span id="failedCount" style="display: none;"> • Failed: <span>0</span></span>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>📚 Document Library</h2>
                    <p>Manage your uploaded documents</p>
                    
                    <button class="btn-refresh" onclick="loadDocuments()">🔄 Refresh</button>
                    
                    <div id="documentLibrary" class="document-list">
                        <div class="no-documents">
                            <p>📂 No documents uploaded yet</p>
                            <p>Upload some documents to get started!</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            const projectId = "{project.id}";
            
            let selectedFiles = [];
            let currentJobId = null;
            let pollInterval = null;
            
            // Toast notification system
            function showToast(message, type = 'info') {{
                const toast = document.createElement('div');
                toast.className = `toast toast-${{type}}`;
                toast.textContent = message;
                document.body.appendChild(toast);
                
                setTimeout(() => {{
                    toast.classList.add('show');
                }}, 100);
                
                setTimeout(() => {{
                    toast.classList.remove('show');
                    setTimeout(() => toast.remove(), 300);
                }}, 4000);
            }}
            
            function uploadFiles() {{
                if (selectedFiles.length === 0) {{
                    showToast('Please select files to upload', 'error');
                    return;
                }}
                
                const formData = new FormData();
                selectedFiles.forEach(file => {{
                    formData.append('files', file);
                }});
                
                // Disable upload button and show progress
                document.getElementById('uploadButton').disabled = true;
                document.getElementById('uploadButton').textContent = 'Uploading...';
                
                fetch(`/documents/upload/${{projectId}}`, {{
                    method: 'POST',
                    body: formData
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.job_id) {{
                        currentJobId = data.job_id;
                        showToast(`Upload started! Processing ${{data.total_files}} files...`, 'success');
                        
                        // Clear file selection
                        selectedFiles = [];
                        document.getElementById('fileInput').value = '';
                        document.getElementById('fileList').innerHTML = '';
                        document.getElementById('uploadButton').style.display = 'none';
                        
                        // Show progress and start polling
                        showProgressUI(data.total_files);
                        startPollingJobStatus(currentJobId);
                    }} else {{
                        throw new Error('No job ID received');
                    }}
                }})
                .catch(error => {{
                    showToast('Upload failed: ' + error.message, 'error');
                    resetUploadButton();
                }});
            }}
            
            function resetUploadButton() {{
                document.getElementById('uploadButton').disabled = false;
                document.getElementById('uploadButton').textContent = 'Upload Documents';
            }}
            
            function showProgressUI(totalFiles) {{
                const container = document.getElementById('progressContainer');
                const totalCount = document.getElementById('totalCount');
                
                totalCount.textContent = totalFiles;
                container.style.display = 'block';
                
                // Scroll to progress section
                container.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
            }}
            
            function hideProgressUI() {{
                document.getElementById('progressContainer').style.display = 'none';
                resetUploadButton();
            }}
            
            function updateProgressUI(status) {{
                const progressFill = document.getElementById('progressFill');
                const progressText = document.getElementById('progressText');
                const processedCount = document.getElementById('processedCount');
                const failedCountElement = document.getElementById('failedCount');
                const failedCountSpan = failedCountElement.querySelector('span');
                
                const percentage = status.progress.percentage;
                progressFill.style.width = percentage + '%';
                progressText.textContent = percentage + '% Complete';
                processedCount.textContent = status.progress.processed_files;
                
                if (status.progress.failed_files > 0) {{
                    failedCountSpan.textContent = status.progress.failed_files;
                    failedCountElement.style.display = 'inline';
                }} else {{
                    failedCountElement.style.display = 'none';
                }}
            }}
            
            function startPollingJobStatus(jobId) {{
                pollInterval = setInterval(async () => {{
                    try {{
                        const response = await fetch(`/jobs/${{jobId}}/status`);
                        const status = await response.json();
                        
                        updateProgressUI(status);
                        
                        if (status.status === 'completed') {{
                            clearInterval(pollInterval);
                            const successCount = status.progress.processed_files - status.progress.failed_files;
                            let message = `Processing complete! ${{successCount}} files processed successfully.`;
                            
                            if (status.progress.failed_files > 0) {{
                                message += ` ${{status.progress.failed_files}} files failed.`;
                                showToast(message, 'info');
                            }} else {{
                                showToast(message, 'success');
                            }}
                            
                            setTimeout(() => {{
                                hideProgressUI();
                                refreshDocumentsAfterUpload();
                            }}, 3000);
                            
                        }} else if (status.status === 'failed') {{
                            clearInterval(pollInterval);
                            showToast('Processing failed: ' + (status.error_message || 'Unknown error'), 'error');
                            hideProgressUI();
                        }}
                    }} catch (error) {{
                        clearInterval(pollInterval);
                        showToast('Error checking status: ' + error.message, 'error');
                        hideProgressUI();
                    }}
                }}, 2000); // Poll every 2 seconds
            }}
            
            function removeFile(index) {{
                selectedFiles.splice(index, 1);
                updateFileList();
            }}
            
            function getFileIcon(filename) {{
                const extension = filename.split('.').pop().toLowerCase();
                switch(extension) {{
                    case 'pdf': return '📄';
                    case 'doc':
                    case 'docx': return '📝';
                    case 'txt': return '📰';
                    case 'md': return '📋';
                    default: return '📄';
                }}
            }}
            
            function formatFileSize(bytes) {{
                if (bytes === 0) return '0 Bytes';
                const k = 1024;
                const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }}
            
            function updateFileList() {{
                const fileList = document.getElementById('fileList');
                const uploadButton = document.getElementById('uploadButton');
                
                if (selectedFiles.length === 0) {{
                    fileList.innerHTML = '';
                    uploadButton.style.display = 'none';
                    return;
                }}
                
                fileList.innerHTML = selectedFiles.map((file, index) => {{
                    return `
                        <div class="file-item">
                            <div class="file-info">
                                <span class="file-icon">${{getFileIcon(file.name)}}</span>
                                <div>
                                    <div class="file-name">${{file.name}}</div>
                                    <div class="file-size">${{formatFileSize(file.size)}}</div>
                                </div>
                            </div>
                            <button class="remove-file" onclick="removeFile(${{index}})">Remove</button>
                        </div>
                    `;
                }}).join('');
                
                uploadButton.style.display = 'block';
            }}
            
            function sendMessage() {{
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                
                if (!message) return;
                
                const messagesDiv = document.getElementById('chatMessages');
                messagesDiv.innerHTML += `<div style="margin-bottom: 10px;"><strong>You:</strong> ${{message}}</div>`;
                
                input.value = '';
                
                // Show typing indicator
                const typingIndicator = `<div id="typingIndicator" style="margin-bottom: 10px; color: #6c757d; font-style: italic;">Assistant is typing...</div>`;
                messagesDiv.innerHTML += typingIndicator;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                
                fetch(`/projects/${{projectId}}/chat/`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{ text: message }})
                }})
                .then(response => {{
                    if (!response.ok) {{
                        throw new Error(`HTTP error! status: ${{response.status}}`);
                    }}
                    return response.json();
                }})
                .then(data => {{
                    // Remove typing indicator
                    const typingDiv = document.getElementById('typingIndicator');
                    if (typingDiv) typingDiv.remove();
                    
                    // Add response
                    let responseHtml = `<div style="margin-bottom: 10px; padding: 10px; background: #f0f8ff; border-radius: 4px;"><strong>Assistant:</strong> ${{data.response}}`;
                    
                    // Add sources if available
                    if (data.sources && data.sources.length > 0) {{
                        responseHtml += `<br><small style="color: #6c757d; margin-top: 5px; display: block;"><strong>Sources:</strong></small>`;
                        data.sources.forEach((source, index) => {{
                            responseHtml += `<small style="color: #6c757d; display: block;">• ${{source.document_name}} (Score: ${{source.relevance_score.toFixed(2)}})</small>`;
                        }});
                    }}
                    
                    responseHtml += `</div>`;
                    messagesDiv.innerHTML += responseHtml;
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }})
                .catch(error => {{
                    // Remove typing indicator
                    const typingDiv = document.getElementById('typingIndicator');
                    if (typingDiv) typingDiv.remove();
                    
                    messagesDiv.innerHTML += `<div style="margin-bottom: 10px; color: red; padding: 10px; background: #ffe6e6; border-radius: 4px;"><strong>Error:</strong> ${{error.message}}</div>`;
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }});
            }}
            
            // Handle file selection display
            document.getElementById('fileInput').addEventListener('change', function(e) {{
                selectedFiles = Array.from(e.target.files);
                updateFileList();
            }});
            
            // Handle enter key in chat input
            document.getElementById('chatInput').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    sendMessage();
                }}
            }});
            
            // Document management functions
            async function loadDocuments() {{
                try {{
                    const response = await fetch(`/projects/${{projectId}}/documents/`);
                    const documents = await response.json();
                    
                    displayDocuments(documents);
                }} catch (error) {{
                    showToast('Error loading documents: ' + error.message, 'error');
                }}
            }}
            
            function displayDocuments(documents) {{
                const library = document.getElementById('documentLibrary');
                
                if (!documents || documents.length === 0) {{
                    library.innerHTML = `
                        <div class="no-documents">
                            <p>📂 No documents uploaded yet</p>
                            <p>Upload some documents to get started!</p>
                        </div>
                    `;
                    return;
                }}
                
                library.innerHTML = documents.map(doc => {{
                    const uploadDate = new Date(doc.created_at).toLocaleDateString();
                    
                    return `
                        <div class="document-item" data-doc-id="${{doc.id}}">
                            <div class="document-info" onclick="viewDocumentChunks('${{doc.id}}')">
                                <div class="document-name">${{doc.name}}</div>
                                <div class="document-meta">
                                    📅 ${{uploadDate}}
                                </div>
                            </div>
                            <div class="document-actions">
                                <button class="btn-delete" onclick="deleteDocument('${{doc.id}}', '${{doc.name}}')">
                                    🗑️ Delete
                                </button>
                            </div>
                        </div>
                    `;
                }}).join('');
            }}
            
            async function deleteDocument(documentId, documentName) {{
                if (!confirm(`Are you sure you want to delete "${{documentName}}"?\\n\\nThis will also delete all associated chunks and cannot be undone.`)) {{
                    return;
                }}
                
                try {{
                    const response = await fetch(`/projects/${{projectId}}/documents/${{documentId}}`, {{
                        method: 'DELETE'
                    }});
                    
                    if (response.ok) {{
                        showToast(`Document "${{documentName}}" deleted successfully`, 'success');
                        
                        // Remove from UI immediately
                        const documentElement = document.querySelector(`[data-doc-id="${{documentId}}"]`);
                        if (documentElement) {{
                            documentElement.remove();
                        }}
                        
                        // Reload documents to ensure consistency
                        setTimeout(() => {{
                            loadDocuments();
                        }}, 1000);
                        
                    }} else {{
                        const errorData = await response.json();
                        throw new Error(errorData.detail || 'Failed to delete document');
                    }}
                }} catch (error) {{
                    showToast('Error deleting document: ' + error.message, 'error');
                }}
            }}
            
            // Load documents when page loads
            document.addEventListener('DOMContentLoaded', function() {{
                loadDocuments();
            }});
            
            // Refresh documents after successful upload
            function refreshDocumentsAfterUpload() {{
                setTimeout(() => {{
                    loadDocuments();
                }}, 2000);
            }}
            
            // Navigate to document chunks view
            function viewDocumentChunks(documentId) {{
                window.location.href = `/projects/${{projectId}}/documents/${{documentId}}/chunks`;
            }}
        </script>
    </body>
    </html>
    """
    return html_content


def get_document_chunks_html(project: ProjectModel, document, chunks):
    """
    Generate the HTML for the document chunks view.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{document.name} - Chunks</title>
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
            .document-info h1 {{
                color: #2c3e50;
                margin: 0;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .document-info p {{
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
            .chunks-container {{
                display: grid;
                gap: 20px;
            }}
            .chunk-item {{
                background: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
                border-left: 4px solid #007bff;
                position: relative;
            }}
            .chunk-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }}
            .chunk-number {{
                font-weight: bold;
                color: #007bff;
                font-size: 14px;
            }}
            .chunk-meta {{
                color: #6c757d;
                font-size: 12px;
            }}
            .chunk-content {{
                line-height: 1.6;
                color: #2c3e50;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
            .chunk-stats {{
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid #e9ecef;
                color: #6c757d;
                font-size: 12px;
            }}
            .no-chunks {{
                text-align: center;
                padding: 60px 20px;
                color: #6c757d;
            }}
            .summary-card {{
                background: #e3f2fd;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 30px;
                border-left: 4px solid #2196f3;
            }}
            .summary-stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 20px;
                margin-top: 15px;
            }}
            .stat-item {{
                text-align: center;
            }}
            .stat-value {{
                font-size: 24px;
                font-weight: bold;
                color: #2196f3;
            }}
            .stat-label {{
                font-size: 12px;
                color: #6c757d;
                margin-top: 5px;
            }}
            @media (max-width: 768px) {{
                .header {{
                    flex-direction: column;
                    gap: 15px;
                }}
                .summary-stats {{
                    grid-template-columns: 1fr 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="document-info">
                    <h1>
                        <span>📄</span>
                        {document.name}
                    </h1>
                    <p>Document chunks for {project.name}</p>
                </div>
                <div class="nav-buttons">
                    <a href="/projects/{project.id}/dashboard" class="btn btn-secondary">← Back to Dashboard</a>
                </div>
            </div>
            
            <div class="summary-card">
                <h3>📊 Document Summary</h3>
                <div class="summary-stats">
                    <div class="stat-item">
                        <div class="stat-value">{len(chunks)}</div>
                        <div class="stat-label">Total Chunks</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{sum(len(chunk.content) for chunk in chunks):,}</div>
                        <div class="stat-label">Total Characters</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{int(sum(len(chunk.content) for chunk in chunks) / len(chunks)) if chunks else 0}</div>
                        <div class="stat-label">Avg Chunk Size</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{len(chunks[0].embedding) if chunks and chunks[0].embedding is not None else 0}</div>
                        <div class="stat-label">Embedding Dims</div>
                    </div>
                </div>
            </div>
            
            <div class="chunks-container">
                {get_chunks_html(chunks) if chunks else '<div class="no-chunks"><p>📄 No chunks found for this document</p></div>'}
            </div>
        </div>
    </body>
    </html>
    """
    return html_content


def get_chunks_html(chunks):
    """
    Generate HTML for individual chunks.
    """
    chunks_html = ""
    for i, chunk in enumerate(chunks, 1):
        word_count = len(chunk.content.split())
        char_count = len(chunk.content)
        
        chunks_html += f"""
        <div class="chunk-item">
            <div class="chunk-header">
                <span class="chunk-number">Chunk #{i}</span>
                <span class="chunk-meta">
                    {word_count} words • {char_count} characters
                </span>
            </div>
            <div class="chunk-content">{chunk.content}</div>
            <div class="chunk-stats">
                <strong>Embedding:</strong> {len(chunk.embedding) if chunk.embedding is not None else 0} dimensions
                {"• <strong>Vector ID:</strong> " + str(chunk.id) if chunk.id else ""}
            </div>
        </div>
        """
    
    return chunks_html
