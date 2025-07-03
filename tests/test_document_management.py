"""
Test document management functionality including deletion and chunk viewing.
"""
import pytest
from uuid import uuid4
from unittest.mock import patch


@pytest.fixture
def sample_project(db_session, authenticated_user):
    """Create a sample project for testing."""
    from models.project import Project
    from datetime import datetime
    
    project = Project(
        id=uuid4(),
        name="Document Test Project",
        description="Project for testing document management",
        owner_id=authenticated_user.id,
        created_at=datetime.utcnow()
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
        name="test_document.txt",
        content=b"This is test content for document management testing. It contains multiple sentences to create chunks.",
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
            content="This is test content for document management testing.",
            embedding=[0.1] * 1536
        ),
        Chunk(
            id=uuid4(),
            document_id=document.id,
            content="It contains multiple sentences to create chunks.",
            embedding=[0.2] * 1536
        ),
        Chunk(
            id=uuid4(),
            document_id=document.id,
            content="Additional content for testing chunk operations.",
            embedding=[0.3] * 1536
        )
    ]
    
    for chunk in chunks:
        db_session.add(chunk)
    db_session.commit()
    
    return document, chunks


# Document Deletion Tests

@pytest.mark.api
def test_delete_document_unauthenticated(client, sample_document_with_chunks):
    """Test deleting document without authentication."""
    document, _ = sample_document_with_chunks
    response = client.delete(f"/projects/{document.project_id}/documents/{document.id}")
    assert response.status_code == 401


@pytest.mark.api
def test_delete_document_nonexistent_project(client, auth_headers):
    """Test deleting document from non-existent project."""
    fake_project_id = uuid4()
    fake_document_id = uuid4()
    response = client.delete(f"/projects/{fake_project_id}/documents/{fake_document_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.api
def test_delete_document_nonexistent_document(client, auth_headers, sample_project):
    """Test deleting non-existent document."""
    fake_document_id = uuid4()
    response = client.delete(f"/projects/{sample_project.id}/documents/{fake_document_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.api
def test_delete_document_unauthorized_project(client, auth_headers, db_session):
    """Test deleting document from project belonging to another user."""
    from models.project import Project
    from models.user import User
    from models.document import Document
    from datetime import datetime
    
    # Create another user
    other_user = User(
        auth0_id="other-user-123",
        email="other@example.com",
        name="Other User",
        created_at=datetime.utcnow()
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
    
    # Create document in other user's project
    other_document = Document(
        id=uuid4(),
        name="other_document.txt",
        content=b"Content from other user",
        project_id=other_project.id,
        created_at=datetime.utcnow()
    )
    db_session.add(other_document)
    db_session.commit()
    
    response = client.delete(f"/projects/{other_project.id}/documents/{other_document.id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.api
def test_delete_document_success(client, auth_headers, sample_document_with_chunks, db_session):
    """Test successful document deletion with chunks cleanup."""
    from models.document import Document
    from models.chunk import Chunk
    
    document, chunks = sample_document_with_chunks
    initial_chunk_count = len(chunks)
    
    # Verify document and chunks exist before deletion
    assert db_session.query(Document).filter(Document.id == document.id).first() is not None
    assert db_session.query(Chunk).filter(Chunk.document_id == document.id).count() == initial_chunk_count
    
    response = client.delete(f"/projects/{document.project_id}/documents/{document.id}", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Document deleted successfully"
    assert data["document_id"] == str(document.id)
    assert data["chunks_deleted"] == initial_chunk_count
    
    # Verify document and chunks are deleted
    assert db_session.query(Document).filter(Document.id == document.id).first() is None
    assert db_session.query(Chunk).filter(Chunk.document_id == document.id).count() == 0


@pytest.mark.api
def test_delete_document_without_chunks(client, auth_headers, sample_project, db_session):
    """Test deleting document that has no chunks."""
    from models.document import Document
    from models.chunk import Chunk
    from datetime import datetime
    
    # Create document without chunks
    document = Document(
        id=uuid4(),
        name="empty_document.txt",
        content=b"Document with no chunks",
        project_id=sample_project.id,
        created_at=datetime.utcnow()
    )
    db_session.add(document)
    db_session.commit()
    
    response = client.delete(f"/projects/{sample_project.id}/documents/{document.id}", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["chunks_deleted"] == 0
    
    # Verify document is deleted
    assert db_session.query(Document).filter(Document.id == document.id).first() is None


# Document Chunk Viewing Tests

@pytest.mark.api
def test_view_document_chunks_unauthenticated(client, sample_document_with_chunks):
    """Test viewing document chunks without authentication."""
    document, _ = sample_document_with_chunks
    response = client.get(f"/projects/{document.project_id}/documents/{document.id}/chunks")
    assert response.status_code == 401


@pytest.mark.api
def test_view_document_chunks_nonexistent_project(client, auth_headers):
    """Test viewing chunks for document in non-existent project."""
    fake_project_id = uuid4()
    fake_document_id = uuid4()
    response = client.get(f"/projects/{fake_project_id}/documents/{fake_document_id}/chunks", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.api
def test_view_document_chunks_nonexistent_document(client, auth_headers, sample_project):
    """Test viewing chunks for non-existent document."""
    fake_document_id = uuid4()
    response = client.get(f"/projects/{sample_project.id}/documents/{fake_document_id}/chunks", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.api
def test_view_document_chunks_unauthorized_project(client, auth_headers, db_session):
    """Test viewing chunks for document in unauthorized project."""
    from models.project import Project
    from models.user import User
    from models.document import Document
    from datetime import datetime
    
    # Create another user and project
    other_user = User(
        auth0_id="other-user-123",
        email="other@example.com",
        name="Other User",
        created_at=datetime.utcnow(),
    )
    db_session.add(other_user)
    db_session.commit()
    
    other_project = Project(
        id=uuid4(),
        name="Other User's Project",
        description="Project owned by another user",
        owner_id=other_user.id,
        created_at=datetime.utcnow(),
    )
    db_session.add(other_project)
    db_session.commit()
    
    other_document = Document(
        id=uuid4(),
        name="other_document.txt",
        content=b"Content from other user",
        project_id=other_project.id,
        created_at=datetime.utcnow()
    )
    db_session.add(other_document)
    db_session.commit()
    
    response = client.get(f"/projects/{other_project.id}/documents/{other_document.id}/chunks", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.api
def test_view_document_chunks_success(client, auth_headers, sample_document_with_chunks):
    """Test successful viewing of document chunks."""
    document, chunks = sample_document_with_chunks
    
    response = client.get(f"/projects/{document.project_id}/documents/{document.id}/chunks", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    
    # Verify HTML content contains expected elements
    html_content = response.text
    assert document.name in html_content
    assert "Document Summary" in html_content
    assert "Total Chunks" in html_content
    assert "Embedding Dims" in html_content
    
    # Verify chunk content is present
    for chunk in chunks:
        assert chunk.content in html_content


@pytest.mark.api
def test_view_document_chunks_no_chunks(client, auth_headers, sample_project, db_session):
    """Test viewing chunks for document with no chunks."""
    from models.document import Document
    from datetime import datetime
    
    # Create document without chunks
    document = Document(
        id=uuid4(),
        name="empty_document.txt",
        content=b"Document with no chunks",
        project_id=sample_project.id,
        created_at=datetime.utcnow()
    )
    db_session.add(document)
    db_session.commit()
    
    response = client.get(f"/projects/{sample_project.id}/documents/{document.id}/chunks", headers=auth_headers)
    assert response.status_code == 200
    
    html_content = response.text
    assert "No chunks found for this document" in html_content
    assert document.name in html_content


# Document Listing Tests

@pytest.mark.api
def test_list_documents_unauthenticated(client, sample_project):
    """Test listing documents without authentication."""
    response = client.get(f"/projects/{sample_project.id}/documents/")
    assert response.status_code == 401


@pytest.mark.api
def test_list_documents_nonexistent_project(client, auth_headers):
    """Test listing documents for non-existent project."""
    fake_project_id = uuid4()
    response = client.get(f"/projects/{fake_project_id}/documents/", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.api
def test_list_documents_unauthorized_project(client, auth_headers, db_session):
    """Test listing documents for unauthorized project."""
    from models.project import Project
    from models.user import User
    from datetime import datetime
    
    # Create another user and project
    other_user = User(
        auth0_id="other-user-123",
        email="other@example.com",
        name="Other User",
        created_at=datetime.utcnow(),
    )
    db_session.add(other_user)
    db_session.commit()
    
    other_project = Project(
        id=uuid4(),
        name="Other User's Project",
        description="Project owned by another user",
        owner_id=other_user.id,
        created_at=datetime.utcnow(),
    )
    db_session.add(other_project)
    db_session.commit()
    
    response = client.get(f"/projects/{other_project.id}/documents/", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.api
def test_list_documents_empty_project(client, auth_headers, sample_project):
    """Test listing documents for project with no documents."""
    response = client.get(f"/projects/{sample_project.id}/documents/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.api
def test_list_documents_with_documents(client, auth_headers, sample_document_with_chunks):
    """Test listing documents for project with documents."""
    document, _ = sample_document_with_chunks
    
    response = client.get(f"/projects/{document.project_id}/documents/", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(document.id)
    assert data[0]["name"] == document.name
    assert data[0]["project_id"] == str(document.project_id)
    assert "created_at" in data[0]


@pytest.mark.api
def test_list_documents_multiple_documents(client, auth_headers, sample_project, db_session):
    """Test listing multiple documents."""
    from models.document import Document
    from datetime import datetime
    
    # Create multiple documents
    documents = []
    for i in range(3):
        document = Document(
            id=uuid4(),
            name=f"document_{i}.txt",
            content=f"Content for document {i}".encode(),
            project_id=sample_project.id,
            created_at=datetime.utcnow()
        )
        documents.append(document)
        db_session.add(document)
    
    db_session.commit()
    
    response = client.get(f"/projects/{sample_project.id}/documents/", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3
    
    # Verify all documents are returned
    returned_names = {doc["name"] for doc in data}
    expected_names = {f"document_{i}.txt" for i in range(3)}
    assert returned_names == expected_names