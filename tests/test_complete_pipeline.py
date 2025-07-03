#!/usr/bin/env python3
"""
Complete ingestion pipeline test with your uploaded documents.
This script tests the entire pipeline and cleans up automatically.
"""

import os
import sys
import asyncio
import tempfile
from unittest.mock import patch, MagicMock

# Add the project root to Python path
sys.path.insert(0, '/workspaces/rag-with-pgvector-app-5')

from database import SessionLocal
from models.user import User
from models.project import Project
from models.document import Document
from models.chunk import Chunk
from models.ingestion_job import IngestionJob
from crud.ingestion_manager import create_ingestion_job
from rag.document_processors import process_document
from rag.processing import get_text_chunks
from routes.document import process_single_document_async


def cleanup_all_test_data():
    """Clean up all test data."""
    print("🧹 Cleaning up all test data...")
    
    db = SessionLocal()
    try:
        # Delete in correct order (foreign key constraints)
        chunks_deleted = db.query(Chunk).join(Document).join(Project).filter(
            Project.name.like('%Test%')
        ).delete(synchronize_session=False)
        
        jobs_deleted = db.query(IngestionJob).join(Project).filter(
            Project.name.like('%Test%')
        ).delete(synchronize_session=False)
        
        documents_deleted = db.query(Document).join(Project).filter(
            Project.name.like('%Test%')
        ).delete(synchronize_session=False)
        
        projects_deleted = db.query(Project).filter(
            Project.name.like('%Test%')
        ).delete()
        
        users_deleted = db.query(User).filter(
            User.email.like('%test%')
        ).delete()
        
        db.commit()
        
        print(f"✅ Cleanup complete: {chunks_deleted} chunks, {jobs_deleted} jobs, {documents_deleted} docs, {projects_deleted} projects, {users_deleted} users")
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        db.rollback()
    finally:
        db.close()


def create_test_data():
    """Create test user and project."""
    print("👤 Creating test user and project...")
    
    db = SessionLocal()
    try:
        # Create test user
        user = User(
            auth0_id="test_pipeline_user",
            email="test_pipeline@example.com",
            name="Pipeline Test User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create test project
        project = Project(
            name="Test Pipeline Project",
            description="Testing complete ingestion pipeline",
            owner_id=user.id
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        print(f"✅ Created user {user.id} and project {project.id}")
        return user, project
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def test_document_processing():
    """Test document processing for both uploaded files."""
    print("\n📄 Testing document processing...")
    
    test_docs = {
        "AI_history.pdf": "/workspaces/rag-with-pgvector-app-5/tests/test_docs/AI_history.pdf",
        "Turtles of New Mexico.docx": "/workspaces/rag-with-pgvector-app-5/tests/test_docs/Turtles of New Mexico.docx"
    }
    
    results = {}
    
    for filename, filepath in test_docs.items():
        print(f"\n📋 Processing {filename}...")
        
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            
            # Test document processing
            text, success, file_type = process_document(content, filename)
            
            if not success:
                print(f"❌ Failed to process {filename}")
                continue
            
            # Test text chunking
            chunks = get_text_chunks(text)
            
            results[filename] = {
                "success": True,
                "file_type": file_type,
                "text_length": len(text),
                "chunk_count": len(chunks),
                "content": content
            }
            
            print(f"✅ {filename} processed successfully")
            print(f"   - Type: {file_type}")
            print(f"   - Text length: {len(text)} characters")
            print(f"   - Chunks: {len(chunks)}")
            print(f"   - Preview: {text[:100]}...")
            
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            results[filename] = {"success": False, "error": str(e)}
    
    return results


@patch('rag.processing.requests.post')
def test_full_pipeline(mock_post, user, project, processing_results):
    """Test the complete ingestion pipeline."""
    print("\n🔄 Testing complete ingestion pipeline...")
    
    # Mock OpenAI API responses
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [{"embedding": [0.1] * 1536} for _ in range(10)]  # Mock embeddings
    }
    mock_post.return_value = mock_response
    
    db = SessionLocal()
    successful_documents = []
    
    try:
        for filename, result in processing_results.items():
            if not result.get("success"):
                print(f"⏭️  Skipping {filename} (processing failed)")
                continue
            
            print(f"\n🔄 Running full pipeline for {filename}...")
            
            # Create ingestion job
            job = create_ingestion_job(
                db=db,
                project_id=str(project.id),
                user_id=str(user.id),
                total_files=1,
                file_metadata=[{
                    "filename": filename,
                    "size": len(result["content"])
                }]
            )
            
            # Create temporary file
            file_ext = os.path.splitext(filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                tmp_file.write(result["content"])
                tmp_file_path = tmp_file.name
            
            try:
                # Process the document through the pipeline
                asyncio.run(process_single_document_async(
                    db,
                    tmp_file_path,
                    str(project.id),
                    str(job.id)
                ))
                
                # Verify document was created
                document = db.query(Document).filter(
                    Document.project_id == project.id,
                    Document.name == filename
                ).first()
                
                if not document:
                    print(f"❌ Document {filename} not found in database")
                    continue
                
                # Verify chunks were created
                chunks = db.query(Chunk).filter(
                    Chunk.document_id == document.id
                ).all()
                
                if not chunks:
                    print(f"❌ No chunks created for {filename}")
                    continue
                
                # Verify chunk data
                valid_chunks = 0
                for chunk in chunks:
                    if (chunk.content and 
                        len(chunk.content) > 0 and 
                        chunk.embedding and 
                        len(chunk.embedding) == 1536):
                        valid_chunks += 1
                
                successful_documents.append({
                    "filename": filename,
                    "document_id": str(document.id),
                    "total_chunks": len(chunks),
                    "valid_chunks": valid_chunks,
                    "api_calls": mock_post.call_count
                })
                
                print(f"✅ {filename} pipeline completed successfully")
                print(f"   - Document ID: {document.id}")
                print(f"   - Total chunks: {len(chunks)}")
                print(f"   - Valid chunks: {valid_chunks}")
                
            finally:
                # Clean up temp file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
    
    finally:
        db.close()
    
    return successful_documents


def main():
    """Main test function."""
    print("🚀 Starting Complete Ingestion Pipeline Test")
    print("=" * 60)
    
    # Clean up any existing test data
    cleanup_all_test_data()
    
    try:
        # Create test data
        user, project = create_test_data()
        
        # Test document processing
        processing_results = test_document_processing()
        
        # Test full pipeline
        pipeline_results = test_full_pipeline(user, project, processing_results)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        print("\n📄 Document Processing Results:")
        for filename, result in processing_results.items():
            status = "✅ SUCCESS" if result.get("success") else "❌ FAILED"
            print(f"   {status} {filename}")
            if result.get("success"):
                print(f"      - {result['text_length']} chars, {result['chunk_count']} chunks")
        
        print("\n🔄 Pipeline Results:")
        if pipeline_results:
            for doc in pipeline_results:
                print(f"   ✅ {doc['filename']}")
                print(f"      - Document ID: {doc['document_id']}")
                print(f"      - Chunks: {doc['valid_chunks']}/{doc['total_chunks']} valid")
        else:
            print("   ❌ No documents completed the full pipeline")
        
        success = len(pipeline_results) > 0
        
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        success = False
    
    finally:
        # Final cleanup
        print("\n🧹 Final cleanup...")
        cleanup_all_test_data()
    
    # Final result
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED! The ingestion pipeline is working correctly.")
    else:
        print("❌ TESTS FAILED! Check the errors above.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)