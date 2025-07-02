# RAG Application - High Level Architecture

## Overview
A multi-tenant RAG (Retrieval-Augmented Generation) application that allows users to create knowledge bases from their documents and chat with them using natural language queries. The system provides secure access control, document management, and intelligent retrieval with reranking.

## Core Components

### Authentication & Authorization
- **User Management**: Standard login/logout with session management
- **Project-Based Access Control**: Users create projects and define authorized user groups
- **Permission System**: Role-based access (owner, editor, viewer) with granular permissions
- **Group Management**: Define user groups with email-based membership for project access

### Project Management
- **Project Creation**: Users can create named projects with descriptions
- **Access Control Configuration**: Set project visibility (private, group-restricted, public)
- **User Group Assignment**: Define which users/groups can access each project
- **Project Dashboard**: Overview of documents, usage stats, and settings

### Document Ingestion Pipeline
- **Multi-Modal Upload**: Web UI drag-and-drop interface and API endpoints for bulk upload
- **File Processing**: Support for PDF, DOCX, TXT, Markdown, and other document formats
- **Document Chunking**: Intelligent text splitting with configurable chunk sizes and overlap
- **Embedding Generation**: Convert chunks to vector embeddings using modern embedding models
- **Metadata Extraction**: Capture document title, upload date, file type, and custom tags
- **Storage Layer**: Store original documents, processed chunks, and embeddings in PostgreSQL with pgvector

### RAG Search Engine
- **Query Processing**: User queries converted to embeddings for similarity search
- **Vector Retrieval**: Semantic search using pgvector to find top-K relevant chunks (K=150)
- **Reranking System**: 
  - Option 1: LLM-based relevance scoring with binary classification prompts
  - Option 2: Cross-encoder reranking models for more sophisticated scoring
- **Result Filtering**: Select top-M chunks (M=10) after reranking for context injection
- **Context Assembly**: Combine selected chunks with source attribution

### Chat Interface
- **Project Selection**: Users choose which project/knowledge base to query
- **Access Filtering**: Only show projects user has permission to access
- **Conversational UI**: Real-time chat interface with typing indicators and message history
- **Source Attribution**: Display which documents contributed to each answer
- **Query Refinement**: Suggest follow-up questions based on retrieved content

### Document Management Dashboard
- **Document Library**: Searchable list of all uploaded documents per project
- **Document Preview**: View original documents and their processed chunks
- **Bulk Operations**: Delete multiple documents, re-process with new settings
- **Upload History**: Track when documents were added and by whom
- **Analytics**: Usage metrics, popular queries, and retrieval performance

## Technical Architecture

### Backend Stack
- **API Framework**: FastAPI or Django REST Framework for robust API endpoints
- **Database**: PostgreSQL with pgvector extension for vector storage and search
- **Queue System**: Redis or Celery for background document processing
- **File Storage**: Local filesystem or S3-compatible storage for original documents
- **Authentication**: JWT tokens or session-based auth with refresh tokens

### Frontend Stack
- **Web Application**: React/Vue.js SPA with responsive design
- **Chat Interface**: WebSocket or Server-Sent Events for real-time communication
- **File Upload**: Drag-and-drop interface with progress indicators
- **Dashboard**: Interactive charts and tables for document management

### Configuration Management
- **Environment Variables**: Configurable parameters (K=150, M=10, chunk sizes)
- **Model Configuration**: Swappable embedding models and LLM providers
- **Reranking Options**: Toggle between LLM-based and model-based reranking
- **Performance Tuning**: Adjustable similarity thresholds and retrieval parameters

## Data Flow

1. **User uploads documents** → Document processing queue → Chunking → Embedding → pgvector storage
2. **User submits query** → Query embedding → Vector similarity search (top-K) → Reranking (top-M) → LLM generation → Response with sources
3. **User manages documents** → CRUD operations on document metadata → Reindex if needed

## Security & Privacy
- **Data Isolation**: Projects are completely isolated from each other
- **Audit Logging**: Track all document uploads, queries, and access attempts
- **Rate Limiting**: Prevent abuse with configurable API limits
- **Data Retention**: Configurable document and chat history retention policies

This architecture provides a scalable, secure, and user-friendly RAG application that can handle multiple tenants while maintaining strong access controls and delivering high-quality search results through intelligent retrieval and reranking.