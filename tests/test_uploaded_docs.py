import pytest
import asyncio
import tempfile
import os
from unittest.mock import patch, MagicMock
from database import SessionLocal
from models.user import User
from models.project import Project
from models.document import Document
from models.chunk import Chunk
from crud.ingestion_manager import create_ingestion_job
from rag.document_processors import process_document
from rag.processing import get_text_chunks


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
        auth0_id="test_user_docs",
        email="test_docs@example.com",
        name="Test User for Documents"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_project(db_session, test_user):
    """Create a test project."""
    project = Project(
        name="Test Project for Uploaded Docs",
        description="Testing with AI_history.pdf and Turtles of New Mexico.docx",
        owner_id=test_user.id
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


class TestUploadedDocuments:
    """Test processing of user-uploaded documents."""
    
    def test_ai_history_pdf_processing(self):
        """Test processing of AI_history.pdf."""
        pdf_path = "/workspaces/rag-with-pgvector-app-5/tests/test_docs/AI_history.pdf"
        
        with open(pdf_path, "rb") as f:
            content = f.read()
        
        text, success, file_type = process_document(content, "AI_history.pdf")
        
        assert success is True, "Failed to process AI_history.pdf"
        assert file_type == "pdf", f"Expected file_type 'pdf', got '{file_type}'"
        assert len(text) > 100, f"Extracted text too short: {len(text)} characters"
        
        print("✅ AI_history.pdf processed successfully")
        print(f"   - Extracted {len(text)} characters")
        print(f"   - First 200 chars: {text[:200]}...")
        
        # Test chunking
        chunks = get_text_chunks(text)
        assert len(chunks) > 0, "No chunks generated from PDF"
        
        print(f"   - Generated {len(chunks)} chunks")
        print(f"   - Average chunk size: {sum(len(c) for c in chunks) // len(chunks)} characters")
    
    def test_turtles_docx_processing(self):
        """Test processing of Turtles of New Mexico.docx."""
        docx_path = "/workspaces/rag-with-pgvector-app-5/tests/test_docs/Turtles of New Mexico.docx"
        
        with open(docx_path, "rb") as f:
            content = f.read()
        
        text, success, file_type = process_document(content, "Turtles of New Mexico.docx")
        
        assert success is True, "Failed to process Turtles of New Mexico.docx"
        assert file_type == "docx", f"Expected file_type 'docx', got '{file_type}'"
        assert len(text) > 100, f"Extracted text too short: {len(text)} characters"
        
        print("✅ Turtles of New Mexico.docx processed successfully")
        print(f"   - Extracted {len(text)} characters")
        print(f"   - First 200 chars: {text[:200]}...")
        
        # Test chunking
        chunks = get_text_chunks(text)
        assert len(chunks) > 0, "No chunks generated from DOCX"
        
        print(f"   - Generated {len(chunks)} chunks")
        print(f"   - Average chunk size: {sum(len(c) for c in chunks) // len(chunks)} characters")
        
        # Check for turtle-related content
        full_text_lower = text.lower()
        turtle_keywords = ["turtle", "reptile", "new mexico", "habitat"]
        found_keywords = [kw for kw in turtle_keywords if kw in full_text_lower]
        print(f"   - Found keywords: {found_keywords}")
    
    @patch('rag.processing.requests.post')
    def test_full_pipeline_ai_history(self, mock_post, db_session, test_project, test_user):
        """Test full pipeline with AI_history.pdf."""
        # Mock OpenAI API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1] * 1536} for _ in range(5)]  # Mock multiple embeddings
        }
        mock_post.return_value = mock_response
        
        pdf_path = "/workspaces/rag-with-pgvector-app-5/tests/test_docs/AI_history.pdf"
        
        with open(pdf_path, "rb") as f:
            content = f.read()
        
        # Create ingestion job
        job = create_ingestion_job(
            db=db_session,
            project_id=str(test_project.id),
            user_id=str(test_user.id),
            total_files=1,
            file_metadata=[{"filename": "AI_history.pdf", "size": len(content)}]
        )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Import and run the processing function
            from routes.document import process_single_document_async
            
            asyncio.run(process_single_document_async(
                db_session,
                tmp_file_path,
                str(test_project.id),
                str(job.id)
            ))
            
            # Verify document was created
            document = db_session.query(Document).filter(
                Document.project_id == test_project.id,
                Document.name == "AI_history.pdf"
            ).first()
            
            assert document is not None, "Document not created in database"
            
            # Verify chunks were created
            chunks = db_session.query(Chunk).filter(
                Chunk.document_id == document.id
            ).all()
            
            assert len(chunks) > 0, "No chunks created for document"
            
            print("✅ Full pipeline test for AI_history.pdf completed")
            print(f"   - Document ID: {document.id}")
            print(f"   - Number of chunks: {len(chunks)}")
            print(f"   - OpenAI API calls: {mock_post.call_count}")
            
            # Verify chunk content
            for i, chunk in enumerate(chunks[:3]):  # Check first 3 chunks
                assert chunk.content is not None
                assert len(chunk.content) > 0
                assert chunk.embedding is not None
                assert len(chunk.embedding) == 1536
                print(f"   - Chunk {i+1}: {len(chunk.content)} chars, {len(chunk.embedding)} dims")
            
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)
    
    @patch('rag.processing.requests.post')
    def test_full_pipeline_turtles_docx(self, mock_post, db_session, test_project, test_user):
        """Test full pipeline with Turtles of New Mexico.docx."""
        # Mock OpenAI API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [0.2] * 1536} for _ in range(5)]  # Mock multiple embeddings
        }
        mock_post.return_value = mock_response
        
        docx_path = "/workspaces/rag-with-pgvector-app-5/tests/test_docs/Turtles of New Mexico.docx"
        
        with open(docx_path, "rb") as f:
            content = f.read()
        
        # Create ingestion job
        job = create_ingestion_job(
            db=db_session,
            project_id=str(test_project.id),
            user_id=str(test_user.id),
            total_files=1,
            file_metadata=[{"filename": "Turtles of New Mexico.docx", "size": len(content)}]
        )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Import and run the processing function
            from routes.document import process_single_document_async
            
            asyncio.run(process_single_document_async(
                db_session,
                tmp_file_path,
                str(test_project.id),
                str(job.id)
            ))
            
            # Verify document was created
            document = db_session.query(Document).filter(
                Document.project_id == test_project.id,
                Document.name == "Turtles of New Mexico.docx"
            ).first()
            
            assert document is not None, "Document not created in database"
            
            # Verify chunks were created
            chunks = db_session.query(Chunk).filter(
                Chunk.document_id == document.id
            ).all()
            
            assert len(chunks) > 0, "No chunks created for document"
            
            print("✅ Full pipeline test for Turtles of New Mexico.docx completed")
            print(f"   - Document ID: {document.id}")
            print(f"   - Number of chunks: {len(chunks)}")
            print(f"   - OpenAI API calls: {mock_post.call_count}")
            
            # Verify chunk content and check for turtle-related terms
            turtle_mentions = 0
            for i, chunk in enumerate(chunks):
                assert chunk.content is not None
                assert len(chunk.content) > 0
                assert chunk.embedding is not None
                assert len(chunk.embedding) == 1536
                
                if "turtle" in chunk.content.lower():
                    turtle_mentions += 1
                
                if i < 3:  # Print details for first 3 chunks
                    print(f"   - Chunk {i+1}: {len(chunk.content)} chars, {len(chunk.embedding)} dims")
            
            print(f"   - Chunks mentioning 'turtle': {turtle_mentions}")
            
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)


def cleanup_test_data():
    """Clean up test data created by these tests."""
    print("\n🧹 Cleaning up test data...")
    
    db = SessionLocal()
    try:
        # Delete chunks
        chunks_deleted = db.query(Chunk).join(Document).join(Project).filter(
            Project.name == "Test Project for Uploaded Docs"
        ).delete(synchronize_session=False)
        
        # Delete documents
        documents_deleted = db.query(Document).join(Project).filter(
            Project.name == "Test Project for Uploaded Docs"
        ).delete(synchronize_session=False)
        
        # Delete project
        projects_deleted = db.query(Project).filter(
            Project.name == "Test Project for Uploaded Docs"
        ).delete()
        
        # Delete user
        users_deleted = db.query(User).filter(
            User.email == "test_docs@example.com"
        ).delete()
        
        db.commit()
        
        print(f"   ✅ Cleaned up: {chunks_deleted} chunks, {documents_deleted} documents, {projects_deleted} projects, {users_deleted} users")
        
    except Exception as e:
        print(f"   ❌ Cleanup error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
    
    # Clean up
    cleanup_test_data()