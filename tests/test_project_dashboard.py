"""
Test project dashboard functionality including HTML rendering and navigation.
"""
import pytest
from uuid import uuid4


@pytest.fixture
def sample_project(db_session, authenticated_user):
    """Create a sample project for testing."""
    from models.project import Project
    from datetime import datetime
    
    project = Project(
        id=uuid4(),
        name="Dashboard Test Project",
        description="Project for testing dashboard functionality",
        owner_id=authenticated_user.id,
        created_at=datetime.utcnow(),
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def sample_document_with_chunks(db_session, sample_project):
    """Create a sample document with chunks for testing."""
    from models.document import Document
    from models.chunk import Chunk
    from datetime import datetime
    
    # Create document
    document = Document(
        id=uuid4(),
        name="dashboard_test.pdf",
        content=b"This is test content for dashboard testing with artificial intelligence concepts.",
        project_id=sample_project.id,
        created_at=datetime.utcnow()
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    # Create chunks
    chunks = [
        Chunk(
            id=uuid4(),
            document_id=document.id,
            content="This is test content for dashboard testing.",
            embedding=[0.1] * 1536
        ),
        Chunk(
            id=uuid4(),
            document_id=document.id,
            content="The document covers artificial intelligence concepts.",
            embedding=[0.2] * 1536
        )
    ]
    
    for chunk in chunks:
        db_session.add(chunk)
    db_session.commit()
    
    return document, chunks


# Project Dashboard Tests

@pytest.mark.api
def test_project_dashboard_unauthenticated(client, sample_project):
    """Test accessing project dashboard without authentication."""
    response = client.get(f"/projects/{sample_project.id}/dashboard")
    assert response.status_code == 401


@pytest.mark.api
def test_project_dashboard_nonexistent_project(client, auth_headers):
    """Test accessing dashboard for non-existent project."""
    fake_project_id = uuid4()
    response = client.get(f"/projects/{fake_project_id}/dashboard", headers=auth_headers)
    assert response.status_code == 401  # Should return 401 for unauthorized access to project


@pytest.mark.api
def test_project_dashboard_unauthorized_project(client, auth_headers, db_session):
    """Test accessing dashboard for project belonging to another user."""
    from models.project import Project
    from models.user import User
    from datetime import datetime
    
    # Create another user
    other_user = User(
        auth0_id="other-user-123",
        email="other@example.com",
        name="Other User",
        created_at=datetime.utcnow(),
    )
    db_session.add(other_user)
    db_session.commit()
    
    # Create project owned by other user
    other_project = Project(
        id=uuid4(),
        name="Other User's Project",
        description="Project owned by another user",
        owner_id=other_user.id,
        created_at=datetime.utcnow(),
    )
    db_session.add(other_project)
    db_session.commit()
    
    response = client.get(f"/projects/{other_project.id}/dashboard", headers=auth_headers)
    assert response.status_code == 401  # Should return 401 for unauthorized access to other user's project


@pytest.mark.api
def test_project_dashboard_success(client, auth_headers, sample_project):
    """Test successful access to project dashboard."""
    response = client.get(f"/projects/{sample_project.id}/dashboard", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    
    html_content = response.text
    
    # Verify basic HTML structure
    assert "<!DOCTYPE html>" in html_content
    assert "<html>" in html_content
    assert "</html>" in html_content
    
    # Verify project information is displayed
    assert sample_project.name in html_content
    assert sample_project.description in html_content
    
    # Verify essential dashboard sections are present
    assert "Chat with Documents" in html_content
    assert "Document Upload" in html_content
    assert "Document Library" in html_content
    
    # Verify navigation elements
    assert "Back to Home" in html_content
    
    # Verify JavaScript functionality is included
    assert "function sendMessage()" in html_content
    assert "function uploadFiles()" in html_content
    assert "function loadDocuments()" in html_content
    assert "function viewDocumentChunks(" in html_content


@pytest.mark.api  
def test_project_dashboard_css_styling(client, auth_headers, sample_project):
    """Test that dashboard includes proper CSS styling."""
    response = client.get(f"/projects/{sample_project.id}/dashboard", headers=auth_headers)
    assert response.status_code == 200
    
    html_content = response.text
    
    # Verify CSS styles are included
    assert "<style>" in html_content
    assert "</style>" in html_content
    
    # Verify key CSS classes
    assert ".dashboard-grid" in html_content
    assert ".chat-section" in html_content
    assert ".document-list" in html_content
    assert ".document-item" in html_content
    assert ".btn-primary" in html_content
    
    # Verify responsive design
    assert "@media (max-width: 768px)" in html_content


@pytest.mark.api
def test_project_dashboard_javascript_functions(client, auth_headers, sample_project):
    """Test that dashboard includes necessary JavaScript functions."""
    response = client.get(f"/projects/{sample_project.id}/dashboard", headers=auth_headers)
    assert response.status_code == 200
    
    html_content = response.text
    
    # Verify JavaScript functions are included
    javascript_functions = [
        "function sendMessage()",
        "function uploadFiles()",
        "function loadDocuments()",
        "function displayDocuments(",
        "function deleteDocument(",
        "function viewDocumentChunks(",
        "function showToast(",
        "function refreshDocumentsAfterUpload("
    ]
    
    for function in javascript_functions:
        assert function in html_content


@pytest.mark.api
def test_project_dashboard_api_endpoints(client, auth_headers, sample_project):
    """Test that dashboard includes correct API endpoint references."""
    response = client.get(f"/projects/{sample_project.id}/dashboard", headers=auth_headers)
    assert response.status_code == 200
    
    html_content = response.text
    
    # Verify correct API endpoints are referenced
    assert f"/projects/{sample_project.id}/chat/" in html_content
    assert f"/projects/{sample_project.id}/documents/" in html_content
    assert "/documents/upload/" in html_content
    assert "/jobs/" in html_content


@pytest.mark.api
def test_project_dashboard_layout_structure(client, auth_headers, sample_project):
    """Test that dashboard has the correct layout structure."""
    response = client.get(f"/projects/{sample_project.id}/dashboard", headers=auth_headers)
    assert response.status_code == 200
    
    html_content = response.text
    
    # Verify header section
    assert 'class="header"' in html_content
    assert 'class="project-info"' in html_content
    assert 'class="nav-buttons"' in html_content
    
    # Verify chat section (full width)
    assert 'class="chat-section"' in html_content
    assert 'id="chatMessages"' in html_content
    assert 'id="chatInput"' in html_content
    
    # Verify two-column layout below chat
    assert 'class="dashboard-grid"' in html_content
    
    # Verify upload section
    assert "Document Upload" in html_content
    assert 'id="fileInput"' in html_content
    assert 'id="uploadButton"' in html_content
    
    # Verify document library section
    assert "Document Library" in html_content
    assert 'id="documentLibrary"' in html_content
    assert "Refresh" in html_content


@pytest.mark.api
def test_project_dashboard_toast_notifications(client, auth_headers, sample_project):
    """Test that dashboard includes toast notification system."""
    response = client.get(f"/projects/{sample_project.id}/dashboard", headers=auth_headers)
    assert response.status_code == 200
    
    html_content = response.text
    
    # Verify toast notification CSS
    assert ".toast" in html_content
    assert ".toast-success" in html_content
    assert ".toast-error" in html_content
    assert ".toast-info" in html_content
    
    # Verify toast JavaScript function
    assert "function showToast(" in html_content
    assert "toast.classList.add('show')" in html_content


@pytest.mark.api
def test_project_dashboard_progress_tracking(client, auth_headers, sample_project):
    """Test that dashboard includes progress tracking functionality."""
    response = client.get(f"/projects/{sample_project.id}/dashboard", headers=auth_headers)
    assert response.status_code == 200
    
    html_content = response.text
    
    # Verify progress tracking elements
    assert 'id="progressContainer"' in html_content
    assert 'id="progressFill"' in html_content
    assert 'id="progressText"' in html_content
    assert 'id="processedCount"' in html_content
    assert 'id="failedCount"' in html_content
    
    # Verify progress tracking functions
    assert "function startPollingJobStatus(" in html_content
    assert "function updateProgressUI(" in html_content
    assert "function showProgressUI(" in html_content
    assert "function hideProgressUI(" in html_content


@pytest.mark.api
def test_project_dashboard_file_handling(client, auth_headers, sample_project):
    """Test that dashboard includes proper file handling functionality."""
    response = client.get(f"/projects/{sample_project.id}/dashboard", headers=auth_headers)
    assert response.status_code == 200
    
    html_content = response.text
    
    # Verify file input and handling
    assert 'accept=".pdf,.doc,.docx,.txt,.md"' in html_content
    assert "function updateFileList()" in html_content
    assert "function removeFile(" in html_content
    assert "function formatFileSize(" in html_content
    assert "function getFileIcon(" in html_content
    
    # Verify supported file formats are mentioned
    assert "PDF, DOC, DOCX, TXT, MD" in html_content


@pytest.mark.api
def test_project_dashboard_security_headers(client, auth_headers, sample_project):
    """Test that dashboard response includes appropriate security considerations."""
    response = client.get(f"/projects/{sample_project.id}/dashboard", headers=auth_headers)
    assert response.status_code == 200
    
    # Verify project ID is properly embedded in JavaScript (no XSS)
    html_content = response.text
    assert f'const projectId = "{sample_project.id}";' in html_content
    
    # Verify that user-controlled content is properly handled
    # (In this case, project name and description should be HTML-escaped if containing special chars)
    assert sample_project.name in html_content
    assert sample_project.description in html_content