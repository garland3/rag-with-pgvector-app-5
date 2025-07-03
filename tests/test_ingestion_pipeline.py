import pytest
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock
from database import SessionLocal
from models.user import User
from models.project import Project
from models.document import Document
from models.chunk import Chunk
from models.ingestion_job import IngestionJob
from crud.ingestion_manager import (
    create_ingestion_job,
    get_ingestion_job,
    update_job_status,
    increment_job_progress
)
from rag.processing import get_text_chunks, get_embeddings, get_completion
from rag.document_processors import process_document


@pytest.fixture
def db_session():
    """Create a database session for testing."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        auth0_id="test_auth0_id",
        email="test@example.com",
        name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_project(db_session, test_user):
    """Create a test project."""
    project = Project(
        name="Test Project",
        description="A project for testing ingestion",
        owner_id=test_user.id
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_documents():
    """Provide paths to test documents."""
    base_path = "/workspaces/rag-with-pgvector-app-5/tests/test_docs"
    return {
        "txt": os.path.join(base_path, "sample_document.txt"),
        "pdf": os.path.join(base_path, "AI_history.pdf"),
        "docx": os.path.join(base_path, "Turtles of New Mexico.docx")
    }


@pytest.fixture
def mock_openai_responses():
    """Mock OpenAI API responses."""
    mock_embedding_response = {
        "data": [
            {"embedding": [0.1] * 1536},  # Mock 1536-dimensional embedding
            {"embedding": [0.2] * 1536},
            {"embedding": [0.3] * 1536}
        ]
    }
    
    mock_chat_response = {
        "choices": [
            {
                "message": {
                    "content": "This is a test response from the AI assistant based on the provided context."
                }
            }
        ]
    }
    
    return {
        "embedding": mock_embedding_response,
        "chat": mock_chat_response
    }


class TestDocumentProcessing:
    """Test document processing functionality."""
    
    def test_process_txt_document(self, test_documents):
        """Test processing of text documents."""
        with open(test_documents["txt"], "rb") as f:
            content = f.read()
        
        text, success, file_type = process_document(content, "sample_document.txt")
        
        assert success is True
        assert file_type == "txt"
        assert len(text) > 0
        assert "Sample Document for Testing" in text
        assert "RAG ingestion pipeline" in text
    
    def test_process_pdf_document(self, test_documents):
        """Test processing of PDF documents."""
        with open(test_documents["pdf"], "rb") as f:
            content = f.read()
        
        text, success, file_type = process_document(content, "AI_history.pdf")
        
        assert success is True
        assert file_type == "pdf"
        assert len(text) > 0
        # PDF should contain some text content
        assert len(text.strip()) > 100
    
    def test_process_docx_document(self, test_documents):
        """Test processing of DOCX documents."""
        with open(test_documents["docx"], "rb") as f:
            content = f.read()
        
        text, success, file_type = process_document(content, "Turtles of New Mexico.docx")
        
        assert success is True
        assert file_type == "docx"
        assert len(text) > 0
        # DOCX should contain some text content
        assert len(text.strip()) > 100
    
    def test_process_unsupported_document(self):
        """Test processing of unsupported document types."""
        content = b"fake binary content"
        text, success, file_type = process_document(content, "unsupported.xyz")
        
        assert success is False
        assert file_type == "unknown"
        assert text == ""


class TestTextChunking:
    """Test text chunking functionality."""
    
    def test_get_text_chunks_basic(self):
        """Test basic text chunking."""
        text = "This is a test document. " * 100  # Create text longer than chunk size
        chunks = get_text_chunks(text)
        
        assert len(chunks) > 1  # Should be split into multiple chunks
        assert all(len(chunk) <= 1200 for chunk in chunks)  # Respect max chunk size (with overlap)
        assert all(len(chunk) > 0 for chunk in chunks)  # No empty chunks
    
    def test_get_text_chunks_short_text(self):
        """Test chunking of short text."""
        text = "This is a short text."
        chunks = get_text_chunks(text)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_get_text_chunks_with_real_document(self, test_documents):
        """Test chunking with real document content."""
        with open(test_documents["txt"], "rb") as f:
            content = f.read()
        
        text, success, _ = process_document(content, "sample_document.txt")
        assert success
        
        chunks = get_text_chunks(text)
        
        assert len(chunks) >= 1
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk.strip()) > 0 for chunk in chunks)


class TestEmbeddingGeneration:
    """Test embedding generation with mocked OpenAI API."""
    
    @patch('rag.processing.requests.post')
    def test_get_embeddings_success(self, mock_post, mock_openai_responses):
        """Test successful embedding generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openai_responses["embedding"]
        mock_post.return_value = mock_response
        
        texts = ["This is test text 1", "This is test text 2", "This is test text 3"]
        embeddings = get_embeddings(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)
        assert all(isinstance(emb, list) for emb in embeddings)
        
        # Verify API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "embeddings" in call_args[0][0]
        assert call_args[1]["json"]["input"] == texts
    
    @patch('rag.processing.requests.post')
    def test_get_embeddings_api_error(self, mock_post):
        """Test embedding generation with API error."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response
        
        texts = ["Test text"]
        
        with pytest.raises(Exception) as exc_info:
            get_embeddings(texts)
        
        assert "Embedding API error: 429" in str(exc_info.value)


class TestChatCompletion:
    """Test chat completion functionality with mocked OpenAI API."""
    
    @patch('rag.processing.requests.post')
    def test_get_completion_success(self, mock_post, mock_openai_responses):
        """Test successful chat completion."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openai_responses["chat"]
        mock_post.return_value = mock_response
        
        query = "What is artificial intelligence?"
        context = "Artificial intelligence is a field of computer science..."
        
        response = get_completion(query, context)
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert response == "This is a test response from the AI assistant based on the provided context."
        
        # Verify API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "chat/completions" in call_args[0][0]
        
        messages = call_args[1]["json"]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert query in messages[1]["content"]
        assert context in messages[1]["content"]


class TestIngestionJobManagement:
    """Test ingestion job CRUD operations."""
    
    def test_create_ingestion_job(self, db_session, test_project, test_user):
        """Test creating an ingestion job."""
        file_metadata = [
            {"filename": "test1.txt", "size": 1000},
            {"filename": "test2.pdf", "size": 2000}
        ]
        
        job = create_ingestion_job(
            db=db_session,
            project_id=str(test_project.id),
            user_id=str(test_user.id),
            total_files=2,
            file_metadata=file_metadata
        )
        
        assert job.id is not None
        assert job.project_id == test_project.id
        assert job.user_id == test_user.id
        assert job.total_files == 2
        assert job.processed_files == 0
        assert job.failed_files == 0
        assert job.status == "pending"
        assert job.job_metadata["files"] == file_metadata
    
    def test_get_ingestion_job(self, db_session, test_project, test_user):
        """Test retrieving an ingestion job."""
        job = create_ingestion_job(
            db=db_session,
            project_id=str(test_project.id),
            user_id=str(test_user.id),
            total_files=1
        )
        
        retrieved_job = get_ingestion_job(db_session, str(job.id))
        
        assert retrieved_job is not None
        assert retrieved_job.id == job.id
        assert retrieved_job.project_id == job.project_id
        assert retrieved_job.user_id == job.user_id
    
    def test_update_job_status(self, db_session, test_project, test_user):
        """Test updating job status."""
        job = create_ingestion_job(
            db=db_session,
            project_id=str(test_project.id),
            user_id=str(test_user.id),
            total_files=1
        )
        
        success = update_job_status(db_session, str(job.id), "processing")
        assert success is True
        
        updated_job = get_ingestion_job(db_session, str(job.id))
        assert updated_job.status == "processing"
    
    def test_increment_job_progress(self, db_session, test_project, test_user):
        """Test incrementing job progress."""
        job = create_ingestion_job(
            db=db_session,
            project_id=str(test_project.id),
            user_id=str(test_user.id),
            total_files=2
        )
        
        # Increment with success
        success = increment_job_progress(db_session, str(job.id), success=True)
        assert success is True
        
        updated_job = get_ingestion_job(db_session, str(job.id))
        assert updated_job.processed_files == 1
        assert updated_job.failed_files == 0
        assert updated_job.status == "pending"  # Not completed yet
        
        # Increment with failure
        increment_job_progress(db_session, str(job.id), success=False)
        
        updated_job = get_ingestion_job(db_session, str(job.id))
        assert updated_job.processed_files == 2
        assert updated_job.failed_files == 1
        assert updated_job.status == "completed"  # Auto-completed when all files processed


class TestEndToEndIngestion:
    """Test end-to-end ingestion pipeline."""
    
    @patch('rag.processing.requests.post')
    def test_single_document_processing_pipeline(self, mock_post, db_session, test_project, test_user, test_documents, mock_openai_responses):
        """Test complete processing of a single document."""
        # Mock OpenAI API responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openai_responses["embedding"]
        mock_post.return_value = mock_response
        
        # Load test document
        with open(test_documents["txt"], "rb") as f:
            content = f.read()
        
        # Import the processing function
        from routes.document import process_single_document_async
        
        # Create ingestion job
        job = create_ingestion_job(
            db=db_session,
            project_id=str(test_project.id),
            user_id=str(test_user.id),
            total_files=1,
            file_metadata=[{"filename": "sample_document.txt", "size": len(content)}]
        )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Process the document
            import asyncio
            asyncio.run(process_single_document_async(
                db_session,
                tmp_file_path,
                str(test_project.id),
                str(job.id)
            ))
            
            # Verify document was created
            document = db_session.query(Document).filter(
                Document.project_id == test_project.id
            ).first()
            
            assert document is not None
            assert document.name == "sample_document.txt"
            
            # Verify chunks were created
            chunks = db_session.query(Chunk).filter(
                Chunk.document_id == document.id
            ).all()
            
            assert len(chunks) > 0
            for chunk in chunks:
                assert chunk.content is not None
                assert len(chunk.content) > 0
                assert chunk.embedding is not None
                assert len(chunk.embedding) == 1536  # OpenAI embedding dimension
            
            # Verify OpenAI API was called
            assert mock_post.called
            
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)
    
    @patch('rag.processing.requests.post')
    def test_multiple_document_processing(self, mock_post, db_session, test_project, test_user, test_documents, mock_openai_responses):
        """Test processing multiple documents."""
        # Mock OpenAI API responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openai_responses["embedding"]
        mock_post.return_value = mock_response
        
        # Load all test documents
        document_data = []
        for doc_type, doc_path in test_documents.items():
            with open(doc_path, "rb") as f:
                content = f.read()
            document_data.append({
                "path": doc_path,
                "content": content,
                "filename": os.path.basename(doc_path)
            })
        
        # Create ingestion job
        file_metadata = [
            {"filename": doc["filename"], "size": len(doc["content"])}
            for doc in document_data
        ]
        
        job = create_ingestion_job(
            db=db_session,
            project_id=str(test_project.id),
            user_id=str(test_user.id),
            total_files=len(document_data),
            file_metadata=file_metadata
        )
        
        # Create temporary files and process each
        temp_files = []
        from routes.document import process_single_document_async
        
        try:
            for doc in document_data:
                # Create temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(doc["filename"])[1]) as tmp_file:
                    tmp_file.write(doc["content"])
                    temp_files.append(tmp_file.name)
                
                # Process the document
                import asyncio
                asyncio.run(process_single_document_async(
                    db_session,
                    tmp_file.name,
                    str(test_project.id),
                    str(job.id)
                ))
            
            # Verify all documents were created
            documents = db_session.query(Document).filter(
                Document.project_id == test_project.id
            ).all()
            
            assert len(documents) == len(document_data)
            
            # Verify chunks were created for all documents
            total_chunks = 0
            for document in documents:
                chunks = db_session.query(Chunk).filter(
                    Chunk.document_id == document.id
                ).all()
                
                assert len(chunks) > 0
                total_chunks += len(chunks)
                
                for chunk in chunks:
                    assert chunk.content is not None
                    assert len(chunk.content) > 0
                    assert chunk.embedding is not None
                    assert len(chunk.embedding) == 1536
            
            assert total_chunks > len(document_data)  # Should have multiple chunks per document
            
        finally:
            # Clean up temp files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)


class TestCleanup:
    """Test cleanup functionality."""
    
    def test_cleanup_ingestion_data(self, db_session, test_project, test_user):
        """Test cleaning up test data after ingestion tests."""
        # Create some test data
        create_ingestion_job(
            db=db_session,
            project_id=str(test_project.id),
            user_id=str(test_user.id),
            total_files=1
        )
        
        # Clean up ingestion jobs
        deleted_jobs = db_session.query(IngestionJob).filter(
            IngestionJob.project_id == test_project.id
        ).delete()
        
        # Clean up chunks
        chunks_deleted = db_session.query(Chunk).join(Document).filter(
            Document.project_id == test_project.id
        ).delete(synchronize_session=False)
        
        # Clean up documents
        documents_deleted = db_session.query(Document).filter(
            Document.project_id == test_project.id
        ).delete()
        
        # Clean up project
        projects_deleted = db_session.query(Project).filter(
            Project.id == test_project.id
        ).delete()
        
        # Clean up user
        users_deleted = db_session.query(User).filter(
            User.id == test_user.id
        ).delete()
        
        db_session.commit()
        
        # Verify cleanup
        assert deleted_jobs >= 1
        print(f"Cleaned up: {deleted_jobs} jobs, {chunks_deleted} chunks, {documents_deleted} documents, {projects_deleted} projects, {users_deleted} users")


def test_temp_directory_cleanup():
    """Test that temporary directories are properly cleaned up."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix="test_ingestion_")
    
    # Create some files in it
    test_file = os.path.join(temp_dir, "test_file.txt")
    with open(test_file, "w") as f:
        f.write("test content")
    
    assert os.path.exists(temp_dir)
    assert os.path.exists(test_file)
    
    # Clean up (simulating the cleanup in the ingestion pipeline)
    shutil.rmtree(temp_dir)
    
    assert not os.path.exists(temp_dir)
    assert not os.path.exists(test_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])