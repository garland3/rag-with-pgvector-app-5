"""
Test chat functionality endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4


@pytest.fixture
def sample_project(db_session, authenticated_user):
    """Create a sample project for testing."""
    from models.project import Project
    from datetime import datetime
    
    project = Project(
        id=uuid4(),
        name="Chat Test Project",
        description="Project for testing chat functionality",
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
        content=b"This is test content for chat testing. The document contains information about artificial intelligence.",
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
            content="This is test content for chat testing.",
            embedding=[0.1] * 1536  # Mock embedding
        ),
        Chunk(
            id=uuid4(),
            document_id=document.id,
            content="The document contains information about artificial intelligence.",
            embedding=[0.2] * 1536  # Mock embedding
        )
    ]
    
    for chunk in chunks:
        db_session.add(chunk)
    db_session.commit()
    
    return document, chunks


@pytest.mark.api
def test_chat_unauthenticated(client, sample_project):
    """Test chat without authentication."""
    chat_data = {"text": "What is this document about?"}
    response = client.post(f"/projects/{sample_project.id}/chat/", json=chat_data)
    assert response.status_code == 401


@pytest.mark.api  
def test_chat_nonexistent_project(client, auth_headers):
    """Test chat with non-existent project."""
    fake_project_id = uuid4()
    chat_data = {"text": "What is this document about?"}
    response = client.post(f"/projects/{fake_project_id}/chat/", json=chat_data, headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.api
def test_chat_unauthorized_project(client, auth_headers, db_session):
    """Test chat with project belonging to another user."""
    from models.project import Project
    from models.user import User
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
        created_at=datetime.utcnow()
    )
    db_session.add(other_project)
    db_session.commit()
    
    chat_data = {"text": "What is this document about?"}
    response = client.post(f"/projects/{other_project.id}/chat/", json=chat_data, headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.api
def test_chat_empty_project(client, auth_headers, sample_project):
    """Test chat with project that has no documents."""
    chat_data = {"text": "What is this document about?"}
    
    with patch("crud.chat_manager.get_chat_response") as mock_chat:
        mock_chat.return_value = {
            "response": "I couldn't find any relevant information to answer your question.",
            "sources": []
        }
        
        response = client.post(f"/projects/{sample_project.id}/chat/", json=chat_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "sources" in data
        assert data["sources"] == []
        assert "couldn't find any relevant information" in data["response"]


@pytest.mark.api
def test_chat_with_documents(client, auth_headers, sample_document_with_chunks):
    """Test chat with project that has documents and chunks."""
    document, chunks = sample_document_with_chunks
    project_id = document.project_id
    
    chat_data = {"text": "What is this document about?"}
    
    with patch("crud.chat_manager.get_chat_response") as mock_chat:
        mock_chat.return_value = {
            "response": "Based on the provided sources, this document is about artificial intelligence. [Source 1] mentions test content for chat testing.",
            "sources": [
                {
                    "id": 1,
                    "document_name": "test_document.txt",
                    "document_id": str(document.id),
                    "chunk_content": "This is test content for chat testing.",
                    "relevance_score": 0.95
                }
            ]
        }
        
        response = client.post(f"/projects/{project_id}/chat/", json=chat_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "sources" in data
        assert len(data["sources"]) == 1
        assert data["sources"][0]["document_name"] == "test_document.txt"
        assert data["sources"][0]["relevance_score"] == 0.95
        assert "artificial intelligence" in data["response"]


@pytest.mark.api
def test_chat_invalid_message_format(client, auth_headers, sample_project):
    """Test chat with invalid message format."""
    # Missing 'text' field
    invalid_data = {"message": "What is this document about?"}
    response = client.post(f"/projects/{sample_project.id}/chat/", json=invalid_data, headers=auth_headers)
    assert response.status_code == 422  # Validation error


@pytest.mark.api
def test_chat_empty_message(client, auth_headers, sample_project):
    """Test chat with empty message."""
    chat_data = {"text": ""}
    response = client.post(f"/projects/{sample_project.id}/chat/", json=chat_data, headers=auth_headers)
    assert response.status_code == 422  # Validation error


@pytest.mark.api
@patch("crud.chat_manager.hybrid_search_and_rerank")
@patch("crud.chat_manager.get_completion")
def test_chat_integration_with_search(mock_completion, mock_search, client, auth_headers, sample_document_with_chunks):
    """Test chat integration with search and completion."""
    document, chunks = sample_document_with_chunks
    project_id = document.project_id
    
    # Mock search results
    mock_search.return_value = chunks
    
    # Mock completion response
    mock_completion.return_value = "This document discusses artificial intelligence and testing methodologies."
    
    chat_data = {"text": "What technologies are discussed?"}
    response = client.post(f"/projects/{project_id}/chat/", json=chat_data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify search was called
    mock_search.assert_called_once()
    
    # Verify completion was called
    mock_completion.assert_called_once()
    
    # Verify response structure
    assert "response" in data
    assert "sources" in data
    assert len(data["sources"]) == 2  # Two chunks
    
    # Verify source information
    for source in data["sources"]:
        assert "id" in source
        assert "document_name" in source
        assert "document_id" in source
        assert "chunk_content" in source
        assert "relevance_score" in source
        assert source["document_name"] == "test_document.txt"


@pytest.mark.api
def test_chat_message_validation(client, auth_headers, sample_project):
    """Test various chat message validation scenarios."""
    test_cases = [
        # Valid cases
        ({"text": "Valid question"}, 200),
        ({"text": "?" * 1000}, 200),  # Long but valid message
        
        # Invalid cases  
        ({}, 422),  # Missing text field
        ({"text": None}, 422),  # Null text
        ({"message": "wrong field"}, 422),  # Wrong field name
    ]
    
    for test_data, expected_status in test_cases:
        with patch("crud.chat_manager.get_chat_response") as mock_chat:
            mock_chat.return_value = {"response": "Test response", "sources": []}
            
            response = client.post(f"/projects/{sample_project.id}/chat/", json=test_data, headers=auth_headers)
            assert response.status_code == expected_status


@pytest.mark.api  
@patch("crud.chat_manager.get_chat_response")
def test_chat_error_handling(mock_chat, client, auth_headers, sample_project):
    """Test chat error handling when chat_manager raises exception."""
    mock_chat.side_effect = Exception("Chat service error")
    
    chat_data = {"text": "What is this document about?"}
    response = client.post(f"/projects/{sample_project.id}/chat/", json=chat_data, headers=auth_headers)
    
    # Should return 500 on internal error
    assert response.status_code == 500