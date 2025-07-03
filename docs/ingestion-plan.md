# Document Ingestion Pipeline Plan

## Overview

This document outlines the comprehensive plan for implementing an asynchronous document ingestion pipeline that processes multiple documents uploaded to a project, splits them into chunks, generates embeddings, and stores them in the pgvector database.

## Current State Analysis

### Existing Infrastructure
1. **Document Processing**: `rag/document_processors.py` - Handles PDF, DOCX, TXT, MD files
2. **Text Chunking**: `rag/processing.py` - Uses RecursiveCharacterTextSplitter (1000 chars, 200 overlap)
3. **Embeddings**: `rag/processing.py` - Google Generative AI embeddings (768 dimensions)
4. **Database**: `models/chunk.py` - pgvector-enabled chunk storage with UUID, document_id, content, embedding
5. **Single File Upload**: `routes/document.py` - Synchronous processing of single files
6. **Reranking**: `rag/reranking.py` - LLM-based relevance scoring for search results

### Current Limitations
1. **Synchronous Processing**: Blocks UI during processing
2. **Single File Upload**: No bulk processing capability
3. **No Progress Tracking**: Users can't see processing status
4. **UI Alerts**: Uses browser alerts instead of proper notifications
5. **No Temporary Storage**: Files processed directly in memory

## Proposed Solution

### 1. Background Job System

**Technology Choice**: Celery with Redis/PostgreSQL as message broker
- **Pros**: Mature, scalable, good monitoring tools
- **Cons**: Additional infrastructure dependency

**Alternative**: FastAPI Background Tasks
- **Pros**: Built-in, no additional dependencies
- **Cons**: Not persistent across server restarts

**Recommendation**: Start with FastAPI Background Tasks, migrate to Celery if needed

### 2. Architecture Components

#### A. Upload Handler
- **Route**: `POST /documents/upload/{project_id}`
- **Function**: Accept multiple files, create temp directory, queue background job
- **Response**: Job ID and initial status

#### B. Background Worker
- **Process**: Document processing pipeline
- **Steps**:
  1. Create unique temp folder per upload batch
  2. Save files to temp storage
  3. Process each file (extract text, validate)
  4. Split into chunks
  5. Generate embeddings
  6. Store in database with metadata
  7. Update progress status
  8. Clean up temp files

#### C. Progress Tracking
- **Storage**: In-memory cache or database table
- **Updates**: Real-time progress via WebSocket or polling
- **UI**: Progress bar with file-by-file status

#### D. Toast Notifications
- **Library**: Browser-native or lightweight JS library
- **Events**: Upload start, progress updates, completion, errors

### 3. Database Schema Updates

#### Job Status Table
```sql
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    user_id UUID REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    total_files INTEGER DEFAULT 0,
    processed_files INTEGER DEFAULT 0,
    failed_files INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    error_message TEXT,
    metadata JSONB -- Store file names, sizes, etc.
);
```

#### Enhanced Chunk Metadata
```sql
-- Add metadata columns to chunks table
ALTER TABLE chunks ADD COLUMN metadata JSONB;
-- Store: file_name, file_type, file_size, chunk_index, processing_time
```

### 4. File Processing Pipeline

#### Step 1: Upload and Queue
```python
@router.post("/upload/{project_id}")
async def upload_documents(
    project_id: str,
    files: List[UploadFile],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create job record
    job = create_ingestion_job(db, project_id, current_user.id, len(files))
    
    # Create temp directory
    temp_dir = f"/tmp/ingestion_{job.id}"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save files to temp directory
    file_paths = []
    for file in files:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        file_paths.append(file_path)
    
    # Queue background job
    background_tasks.add_task(
        process_documents_pipeline,
        job.id,
        file_paths,
        project_id,
        current_user.id
    )
    
    return {"job_id": job.id, "status": "queued"}
```

#### Step 2: Background Processing
```python
async def process_documents_pipeline(
    job_id: str,
    file_paths: List[str],
    project_id: str,
    user_id: str
):
    db = SessionLocal()
    try:
        job = get_ingestion_job(db, job_id)
        update_job_status(db, job_id, "processing")
        
        for i, file_path in enumerate(file_paths):
            try:
                # Process single file
                await process_single_document(
                    db, file_path, project_id, job_id
                )
                
                # Update progress
                update_job_progress(db, job_id, i + 1)
                
            except Exception as e:
                # Log error, continue with next file
                log_processing_error(db, job_id, file_path, str(e))
                update_job_failed_count(db, job_id)
        
        # Mark job as completed
        update_job_status(db, job_id, "completed")
        
    except Exception as e:
        update_job_status(db, job_id, "failed", str(e))
    finally:
        # Clean up temp files
        cleanup_temp_directory(os.path.dirname(file_paths[0]))
        db.close()
```

#### Step 3: Individual Document Processing
```python
async def process_single_document(
    db: Session,
    file_path: str,
    project_id: str,
    job_id: str
):
    # Read file
    with open(file_path, "rb") as f:
        content = f.read()
    
    filename = os.path.basename(file_path)
    
    # Extract text using existing processor
    text, success, file_type = process_document(content, filename)
    
    if not success:
        raise Exception(f"Failed to process {filename}")
    
    # Create document record
    document = create_document_crud(
        db, DocumentCreate(name=filename), project_id, content
    )
    
    # Process into chunks using existing function
    chunks = get_text_chunks(text)
    embeddings = get_embeddings(chunks)
    
    # Store chunks with enhanced metadata
    for i, chunk_content in enumerate(chunks):
        chunk_metadata = {
            "file_name": filename,
            "file_type": file_type,
            "file_size": len(content),
            "chunk_index": i,
            "total_chunks": len(chunks),
            "job_id": job_id,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        chunk = ChunkModel(
            document_id=document.id,
            content=chunk_content,
            embedding=embeddings[i],
            metadata=chunk_metadata
        )
        db.add(chunk)
    
    db.commit()
```

### 5. Progress Tracking API

#### Status Endpoint
```python
@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = get_ingestion_job(db, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_id,
        "status": job.status,
        "progress": {
            "total_files": job.total_files,
            "processed_files": job.processed_files,
            "failed_files": job.failed_files,
            "percentage": (job.processed_files / job.total_files) * 100
        },
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "error_message": job.error_message
    }
```

### 6. Frontend Updates

#### Toast Notification System
```javascript
// Replace alerts with toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
```

#### Progress Tracking UI
```javascript
async function uploadFiles() {
    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });
    
    try {
        // Start upload
        const response = await fetch(`/documents/upload/${projectId}`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        showToast('Upload started! Processing documents...', 'success');
        
        // Show progress UI
        showProgressUI();
        
        // Poll for progress
        pollJobStatus(result.job_id);
        
    } catch (error) {
        showToast('Upload failed: ' + error.message, 'error');
    }
}

function pollJobStatus(jobId) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/documents/jobs/${jobId}/status`);
            const status = await response.json();
            
            updateProgressUI(status);
            
            if (status.status === 'completed') {
                clearInterval(interval);
                showToast('All documents processed successfully!', 'success');
                hideProgressUI();
                // Refresh document list or chat interface
            } else if (status.status === 'failed') {
                clearInterval(interval);
                showToast('Processing failed: ' + status.error_message, 'error');
                hideProgressUI();
            }
        } catch (error) {
            clearInterval(interval);
            showToast('Error checking status: ' + error.message, 'error');
        }
    }, 2000); // Poll every 2 seconds
}
```

### 7. Implementation Steps

1. **Phase 1: Foundation** (Day 1-2)
   - Create ingestion job model and migration
   - Add toast notification system to UI
   - Update upload endpoint to accept multiple files

2. **Phase 2: Background Processing** (Day 3-4)
   - Implement background task system
   - Create document processing pipeline
   - Add temporary file management

3. **Phase 3: Progress Tracking** (Day 5-6)
   - Add job status API endpoints
   - Implement progress UI components
   - Add WebSocket support (optional)

4. **Phase 4: Testing & Optimization** (Day 7)
   - Test with various file types and sizes
   - Optimize chunk processing performance
   - Add error handling and recovery

### 8. Configuration & Deployment

#### Environment Variables
```
# Background job settings
CELERY_BROKER_URL=redis://localhost:6379/0  # If using Celery
TEMP_UPLOAD_DIR=/tmp/rag_uploads
MAX_CONCURRENT_JOBS=5
CHUNK_BATCH_SIZE=100  # Process chunks in batches

# Processing settings
MAX_FILE_SIZE=50MB
SUPPORTED_FORMATS=pdf,docx,txt,md
MAX_FILES_PER_BATCH=20
```

#### Dependencies to Add
```
# requirements.txt additions
celery[redis]==5.3.4  # If using Celery
aiofiles==23.2.1      # Async file operations
```

### 9. Monitoring & Logging

#### Metrics to Track
- Processing time per file
- Success/failure rates
- Queue length and processing delays
- Memory usage during processing
- Database insertion performance

#### Log Structure
```python
# Enhanced logging for ingestion pipeline
log_ingestion_job_started(job_id, file_count, user_id)
log_document_processing_started(job_id, filename, file_size)
log_document_processing_completed(job_id, filename, chunk_count, processing_time)
log_ingestion_job_completed(job_id, total_files, successful_files, failed_files, total_time)
```

### 10. Future Enhancements

1. **Scalability**: Move to Celery with Redis for production
2. **Smart Chunking**: Implement content-aware chunking strategies
3. **File Deduplication**: Detect and skip duplicate files
4. **Incremental Processing**: Process only changed files
5. **Batch Optimization**: Optimize embedding generation for batches
6. **Retry Logic**: Implement exponential backoff for failed processing
7. **Webhook Support**: Notify external systems when processing completes

## Success Criteria

1. **User Experience**: No blocking UI during document upload
2. **Reliability**: 99%+ success rate for supported file formats
3. **Performance**: Process documents within 30 seconds per MB
4. **Scalability**: Handle 100+ concurrent uploads
5. **Observability**: Full logging and monitoring of the pipeline
6. **Recovery**: Graceful handling of failures with retry mechanisms

This plan provides a comprehensive approach to implementing an asynchronous document ingestion pipeline while leveraging the existing RAG infrastructure and maintaining a great user experience.