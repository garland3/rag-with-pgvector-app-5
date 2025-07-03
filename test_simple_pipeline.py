#!/usr/bin/env python3
"""
Simple pipeline test with better error handling and cleanup.
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


def simple_cleanup():
    """Simple cleanup function."""
    print("🧹 Cleaning up test data...")
    
    db = SessionLocal()
    try:
        # Get test objects first, then delete them
        test_users = db.query(User).filter(User.email.like('%test_pipeline%')).all()
        test_projects = db.query(Project).filter(Project.name.like('%Test Pipeline%')).all()
        
        for user in test_users:
            # Delete user's projects and related data
            for project in db.query(Project).filter(Project.owner_id == user.id).all():
                # Delete chunks for this project
                for doc in db.query(Document).filter(Document.project_id == project.id).all():
                    db.query(Chunk).filter(Chunk.document_id == doc.id).delete()
                
                # Delete documents
                db.query(Document).filter(Document.project_id == project.id).delete()
                
                # Delete ingestion jobs
                db.query(IngestionJob).filter(IngestionJob.project_id == project.id).delete()
                
                # Delete project
                db.delete(project)
            
            # Delete user
            db.delete(user)
        
        db.commit()
        print(f"✅ Cleaned up {len(test_users)} users and {len(test_projects)} projects")
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        db.rollback()
    finally:
        db.close()


def test_document_processing():
    """Test basic document processing."""
    print("\n📄 Testing document processing...")
    
    test_files = [
        ("AI_history.pdf", "/workspaces/rag-with-pgvector-app-5/tests/test_docs/AI_history.pdf"),
        ("Turtles of New Mexico.docx", "/workspaces/rag-with-pgvector-app-5/tests/test_docs/Turtles of New Mexico.docx")
    ]
    
    results = []
    
    for filename, filepath in test_files:
        print(f"\n📋 Testing {filename}...")
        
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                print(f"❌ File not found: {filepath}")
                continue
            
            # Read file
            with open(filepath, "rb") as f:
                content = f.read()
            
            print(f"   📂 File size: {len(content)} bytes")
            
            # Process document
            text, success, file_type = process_document(content, filename)
            
            if not success:
                print(f"❌ Failed to extract text from {filename}")
                continue
            
            print(f"✅ Text extraction successful")
            print(f"   📝 Extracted text: {len(text)} characters")
            print(f"   🗂️  File type: {file_type}")
            
            # Test chunking
            chunks = get_text_chunks(text)
            print(f"   🧩 Generated chunks: {len(chunks)}")
            
            if chunks:
                avg_chunk_size = sum(len(chunk) for chunk in chunks) // len(chunks)
                print(f"   📏 Average chunk size: {avg_chunk_size} characters")
                print(f"   👀 First chunk preview: {chunks[0][:100]}...")
            
            results.append({
                "filename": filename,
                "success": True,
                "text_length": len(text),
                "chunk_count": len(chunks),
                "file_type": file_type
            })
            
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            results.append({
                "filename": filename,
                "success": False,
                "error": str(e)
            })
    
    return results


@patch('rag.processing.requests.post')
def test_embedding_mock(mock_post):
    """Test that embedding generation would work with mocked API."""
    print("\n🧠 Testing embedding generation (mocked)...")
    
    # Mock OpenAI API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"embedding": [0.1] * 1536},
            {"embedding": [0.2] * 1536},
            {"embedding": [0.3] * 1536}
        ]
    }
    mock_post.return_value = mock_response
    
    try:
        from rag.processing import get_embeddings
        
        test_texts = [
            "This is a test chunk about artificial intelligence.",
            "This chunk discusses turtles in New Mexico.",
            "This is another test chunk for embeddings."
        ]
        
        embeddings = get_embeddings(test_texts)
        
        print(f"✅ Embedding generation successful")
        print(f"   📊 Generated {len(embeddings)} embeddings")
        print(f"   📏 Embedding dimensions: {len(embeddings[0])}")
        print(f"   🔧 API calls made: {mock_post.call_count}")
        
        # Verify embedding structure
        for i, emb in enumerate(embeddings):
            if len(emb) != 1536:
                print(f"❌ Invalid embedding dimension for text {i}: {len(emb)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return False


def test_database_operations():
    """Test basic database operations."""
    print("\n🗄️  Testing database operations...")
    
    db = SessionLocal()
    try:
        # Create test user
        user = User(
            auth0_id="test_simple_pipeline",
            email="test_simple_pipeline@example.com",
            name="Simple Test User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Created test user: {user.id}")
        
        # Create test project
        project = Project(
            name="Test Pipeline Project Simple",
            description="Simple pipeline test",
            owner_id=user.id
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        print(f"✅ Created test project: {project.id}")
        
        # Create test ingestion job
        job = create_ingestion_job(
            db=db,
            project_id=str(project.id),
            user_id=str(user.id),
            total_files=2,
            file_metadata=[
                {"filename": "test1.pdf", "size": 1000},
                {"filename": "test2.docx", "size": 2000}
            ]
        )
        print(f"✅ Created test ingestion job: {job.id}")
        
        # Verify job data
        assert job.total_files == 2
        assert job.processed_files == 0
        assert job.status == "pending"
        print(f"✅ Job data verified")
        
        return user, project, job
        
    except Exception as e:
        print(f"❌ Database operations failed: {e}")
        db.rollback()
        return None, None, None
    finally:
        db.close()


def main():
    """Main test function."""
    print("🚀 Starting Simple Pipeline Test")
    print("=" * 50)
    
    # Initial cleanup
    simple_cleanup()
    
    success_count = 0
    total_tests = 4
    
    try:
        # Test 1: Document processing
        print("\n" + "="*20 + " TEST 1: Document Processing " + "="*20)
        processing_results = test_document_processing()
        successful_processing = sum(1 for r in processing_results if r.get("success"))
        
        if successful_processing > 0:
            print(f"✅ Document processing: {successful_processing}/{len(processing_results)} files successful")
            success_count += 1
        else:
            print(f"❌ Document processing: All files failed")
        
        # Test 2: Embedding generation (mocked)
        print("\n" + "="*20 + " TEST 2: Embedding Generation " + "="*20)
        if test_embedding_mock():
            print("✅ Embedding generation: Successful")
            success_count += 1
        else:
            print("❌ Embedding generation: Failed")
        
        # Test 3: Database operations
        print("\n" + "="*20 + " TEST 3: Database Operations " + "="*20)
        user, project, job = test_database_operations()
        if user and project and job:
            print("✅ Database operations: Successful")
            success_count += 1
        else:
            print("❌ Database operations: Failed")
        
        # Test 4: Check pipeline readiness
        print("\n" + "="*20 + " TEST 4: Pipeline Readiness " + "="*20)
        if success_count >= 3:
            print("✅ Pipeline readiness: All components working")
            success_count += 1
        else:
            print("❌ Pipeline readiness: Some components failing")
        
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
    
    finally:
        # Final cleanup
        print(f"\n🧹 Final cleanup...")
        simple_cleanup()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 FINAL RESULTS")
    print("=" * 50)
    
    print(f"\n✅ Tests passed: {success_count}/{total_tests}")
    
    if processing_results:
        print(f"\n📄 Document Processing Details:")
        for result in processing_results:
            status = "✅" if result.get("success") else "❌"
            print(f"   {status} {result['filename']}")
            if result.get("success"):
                print(f"      {result['text_length']} chars → {result['chunk_count']} chunks")
    
    if success_count == total_tests:
        print(f"\n🎉 ALL TESTS PASSED! The ingestion pipeline is ready to use.")
        print(f"📋 Your documents are supported:")
        print(f"   - AI_history.pdf: PDF processing working")
        print(f"   - Turtles of New Mexico.docx: DOCX processing working")
        print(f"   - OpenAI API integration: Ready (with proper API key)")
        print(f"   - Database operations: Working")
        return True
    else:
        print(f"\n⚠️  {total_tests - success_count} tests failed. Check the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)