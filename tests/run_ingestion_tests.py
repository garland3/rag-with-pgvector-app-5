#!/usr/bin/env python3
"""
Script to run ingestion pipeline tests with proper setup and cleanup.
"""

import os
import sys
import subprocess
import pytest
from sqlalchemy import create_engine, text
from database import SessionLocal
from models.user import User
from models.project import Project
from models.document import Document
from models.chunk import Chunk
from models.ingestion_job import IngestionJob


def cleanup_test_data():
    """Clean up any test data from the database."""
    print("🧹 Cleaning up test data...")
    
    db = SessionLocal()
    try:
        # Delete test data in correct order (respecting foreign keys)
        
        # 1. Delete chunks (references documents)
        chunks_deleted = db.query(Chunk).join(Document).join(Project).filter(
            Project.name.like('Test%')
        ).delete(synchronize_session=False)
        
        # 2. Delete ingestion jobs (references projects and users)
        jobs_deleted = db.query(IngestionJob).join(Project).filter(
            Project.name.like('Test%')
        ).delete(synchronize_session=False)
        
        # 3. Delete documents (references projects)
        documents_deleted = db.query(Document).join(Project).filter(
            Project.name.like('Test%')
        ).delete(synchronize_session=False)
        
        # 4. Delete test projects
        projects_deleted = db.query(Project).filter(
            Project.name.like('Test%')
        ).delete()
        
        # 5. Delete test users
        users_deleted = db.query(User).filter(
            User.email.like('%test%@example.com')
        ).delete()
        
        db.commit()
        
        print(f"✅ Cleanup complete:")
        print(f"   - {chunks_deleted} chunks")
        print(f"   - {jobs_deleted} ingestion jobs") 
        print(f"   - {documents_deleted} documents")
        print(f"   - {projects_deleted} projects")
        print(f"   - {users_deleted} users")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()


def check_test_requirements():
    """Check if all required test documents exist."""
    test_docs_dir = "/workspaces/rag-with-pgvector-app-5/tests/test_docs"
    required_files = [
        "sample_document.txt",
        "AI_history.pdf", 
        "Turtles of New Mexico.docx"
    ]
    
    missing_files = []
    for filename in required_files:
        file_path = os.path.join(test_docs_dir, filename)
        if not os.path.exists(file_path):
            missing_files.append(filename)
    
    if missing_files:
        print(f"❌ Missing test documents: {missing_files}")
        print(f"   Please ensure all test documents are in {test_docs_dir}")
        return False
    
    print("✅ All test documents found")
    return True


def check_database_connection():
    """Check if database is accessible."""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def run_tests():
    """Run the ingestion pipeline tests."""
    print("🧪 Running ingestion pipeline tests...")
    
    # Run tests with verbose output
    test_file = "/workspaces/rag-with-pgvector-app-5/tests/test_ingestion_pipeline.py"
    
    result = pytest.main([
        test_file,
        "-v",  # Verbose output
        "-s",  # Don't capture output
        "--tb=short",  # Short traceback format
        "--color=yes"  # Colored output
    ])
    
    return result == 0  # pytest returns 0 on success


def main():
    """Main test runner."""
    print("🚀 Starting Ingestion Pipeline Test Suite")
    print("=" * 50)
    
    # Pre-flight checks
    if not check_test_requirements():
        sys.exit(1)
    
    if not check_database_connection():
        sys.exit(1)
    
    # Clean up any existing test data
    cleanup_test_data()
    
    # Run tests
    try:
        success = run_tests()
        
        if success:
            print("\n🎉 All tests passed!")
        else:
            print("\n❌ Some tests failed!")
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        success = False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        success = False
    
    # Final cleanup
    print("\n🧹 Performing final cleanup...")
    cleanup_test_data()
    
    # Summary
    print("\n" + "=" * 50)
    if success:
        print("✅ Test suite completed successfully!")
        sys.exit(0)
    else:
        print("❌ Test suite completed with failures!")
        sys.exit(1)


if __name__ == "__main__":
    main()