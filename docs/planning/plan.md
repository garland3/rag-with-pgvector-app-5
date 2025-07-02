# RAG Application - High Level Architecture

## Overview
A multi-tenant RAG (Retrieval-Augmented Generation) application that allows users to create knowledge bases from their documents and chat with them using natural language queries. The system provides secure access control, document management, and intelligent retrieval with reranking.

## Implementation Status 🚀

### ✅ COMPLETED Features
- **Basic Authentication**: OAuth 2.0 with JWT tokens (Auth0, Google, GitHub)
- **User Management**: User registration, login, profile management  
- **Project Management**: Create projects, owner-based access control
- **Document Upload**: Text file upload with basic processing
- **Document Chunking**: 1000 char chunks with 200 char overlap
- **Vector Embeddings**: Google Gemini embedding-001 (768 dimensions)
- **Vector Storage**: PostgreSQL with pgvector extension
- **Basic RAG**: Semantic search + context retrieval + Gemini completion
- **API Endpoints**: Full REST API with FastAPI
- **Basic UI**: HTML interface for login and project management

### 🔄 IN PROGRESS / NEEDS IMPROVEMENT
- **Search Quality**: Currently uses basic similarity search without reranking
- **File Support**: Only handles .txt files, needs PDF/DOCX support
- **UI/UX**: Basic HTML interface, needs modern React/Vue.js frontend
- **Error Handling**: Basic error handling needs enhancement

### ❌ NOT YET IMPLEMENTED 
- **Advanced Access Control**: Role-based permissions (owner/editor/viewer), user groups
- **Enhanced RAG Pipeline**: Vector retrieval (K=150) → Reranking → Context selection (M=10)
- **Reranking System**: LLM-based relevance scoring or cross-encoder models
- **Rich Document Support**: PDF, DOCX, Markdown processing
- **Modern Frontend**: React/Vue.js SPA with real-time chat interface
- **Background Processing**: Queue system for document processing
- **Analytics Dashboard**: Usage metrics, popular queries, performance stats
- **Advanced Features**: Bulk operations, document preview, query refinement

## Core Components (Current + Planned)

### ✅ Authentication & Authorization (Basic Implementation)
- **User Management**: OAuth login/logout with JWT session management ✅
- **Project-Based Access Control**: Users create projects with owner-only access ✅
- **Permission System**: Role-based access (owner, editor, viewer) with granular permissions ❌
- **Group Management**: Define user groups with email-based membership for project access ❌

### ✅ Project Management (Basic Implementation)
- **Project Creation**: Users can create named projects with descriptions ✅
- **Access Control Configuration**: Set project visibility (private, group-restricted, public) ❌
- **User Group Assignment**: Define which users/groups can access each project ❌
- **Project Dashboard**: Overview of documents, usage stats, and settings ❌

### ✅ Document Ingestion Pipeline (Partial Implementation)
- **Multi-Modal Upload**: Web UI drag-and-drop interface and API endpoints for bulk upload ❌
- **File Processing**: Support for PDF, DOCX, TXT, Markdown, and other document formats (TXT only ✅)
- **Document Chunking**: Intelligent text splitting with configurable chunk sizes and overlap (Fixed 1000/200 ✅)
- **Embedding Generation**: Convert chunks to vector embeddings using modern embedding models ✅
- **Metadata Extraction**: Capture document title, upload date, file type, and custom tags (Basic ✅)
- **Storage Layer**: Store original documents, processed chunks, and embeddings in PostgreSQL with pgvector ✅

### ✅ RAG Search Engine (Basic Implementation)
- **Query Processing**: User queries converted to embeddings for similarity search ✅
- **Vector Retrieval**: Basic similarity search (K=10, not optimized) ✅
- **Reranking System**: ❌
  - Option 1: LLM-based relevance scoring with binary classification prompts ❌
  - Option 2: Cross-encoder reranking models for more sophisticated scoring ❌
- **Result Filtering**: Select top-M chunks (M=10) after reranking for context injection (Basic ✅)
- **Context Assembly**: Combine selected chunks with source attribution (No attribution ✅)

### ✅ Chat Interface (Basic Implementation)
- **Project Selection**: Users choose which project/knowledge base to query ✅
- **Access Filtering**: Only show projects user has permission to access ✅
- **Conversational UI**: Real-time chat interface with typing indicators and message history ❌
- **Source Attribution**: Display which documents contributed to each answer ❌
- **Query Refinement**: Suggest follow-up questions based on retrieved content ❌

### ❌ Document Management Dashboard (Not Implemented)
- **Document Library**: Searchable list of all uploaded documents per project ❌
- **Document Preview**: View original documents and their processed chunks ❌
- **Bulk Operations**: Delete multiple documents, re-process with new settings ❌
- **Upload History**: Track when documents were added and by whom ❌
- **Analytics**: Usage metrics, popular queries, and retrieval performance ❌

## Technical Architecture

### ✅ Backend Stack (Current Implementation)
- **API Framework**: FastAPI for robust API endpoints ✅
- **Database**: PostgreSQL with pgvector extension for vector storage and search ✅
- **Queue System**: Redis or Celery for background document processing ❌
- **File Storage**: Local filesystem storage for original documents ✅
- **Authentication**: JWT tokens with OAuth 2.0 ✅

### ❌ Frontend Stack (Planned)
- **Web Application**: React/Vue.js SPA with responsive design ❌ (Basic HTML ✅)
- **Chat Interface**: WebSocket or Server-Sent Events for real-time communication ❌
- **File Upload**: Drag-and-drop interface with progress indicators ❌
- **Dashboard**: Interactive charts and tables for document management ❌

### ✅ Configuration Management (Partial)
- **Environment Variables**: Configurable parameters (K=150, M=10, chunk sizes) (Fixed values ✅)
- **Model Configuration**: Swappable embedding models and LLM providers (Google Gemini only ✅)
- **Reranking Options**: Toggle between LLM-based and model-based reranking ❌
- **Performance Tuning**: Adjustable similarity thresholds and retrieval parameters ❌

## Data Flow

### ✅ Current Implementation
1. **User uploads documents** → ~~Document processing queue~~ → Chunking → Embedding → pgvector storage ✅
2. **User submits query** → Query embedding → Vector similarity search (top-K=10) → ~~Reranking (top-M)~~ → LLM generation → Response ~~with sources~~ ✅
3. **User manages documents** → Basic CRUD operations on document metadata → ~~Reindex if needed~~ ✅

### ❌ Planned Enhancements
1. **Enhanced Upload Flow**: Background processing queue for large documents ❌
2. **Advanced RAG Pipeline**: K=150 retrieval → Reranking → M=10 selection → Response with source attribution ❌  
3. **Advanced Management**: Bulk operations, reindexing, analytics ❌

## Security & Privacy

### ✅ Current Implementation
- **Data Isolation**: Projects are completely isolated from each other ✅
- **Audit Logging**: Track all document uploads, queries, and access attempts ❌
- **Rate Limiting**: Prevent abuse with configurable API limits ❌
- **Data Retention**: Configurable document and chat history retention policies ❌

## Next Steps & Priority Roadmap

### 🔥 High Priority (Core Functionality)
1. **Enhanced File Support**: Add PDF, DOCX, Markdown processing
2. **Improved RAG Pipeline**: Implement reranking system (K=150 → M=10)
3. **Source Attribution**: Show which documents contributed to answers
4. **Better Search**: Use pgvector native similarity search instead of NumPy

### 🔶 Medium Priority (User Experience)
1. **Modern Frontend**: React/Vue.js SPA with real-time chat
2. **Document Management**: Searchable document library, preview, bulk operations
3. **User Groups**: Role-based access control and project sharing
4. **Background Processing**: Queue system for document processing

### 🔵 Low Priority (Advanced Features)
1. **Analytics Dashboard**: Usage metrics, popular queries, performance stats
2. **Advanced Configuration**: Configurable chunk sizes, similarity thresholds
3. **Query Refinement**: Suggest follow-up questions
4. **Audit & Compliance**: Comprehensive logging, data retention policies

This architecture provides a foundation for a scalable, secure, and user-friendly RAG application. The current implementation covers the core MVP functionality, with a clear roadmap for enhanced features and improved user experience.