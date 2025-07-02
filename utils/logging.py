import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """
    Set up application logging configuration.
    """
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
    
    # Set specific loggers to appropriate levels
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str):
    """
    Get a logger instance for the given name.
    """
    return logging.getLogger(name)


def log_api_request(logger, method: str, endpoint: str, user_id: str = None, 
                   project_id: str = None, duration: float = None):
    """
    Log API request information.
    """
    log_data = {
        "method": method,
        "endpoint": endpoint,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "project_id": project_id,
        "duration_ms": duration * 1000 if duration else None
    }
    
    logger.info(f"API Request: {log_data}")


def log_document_upload(logger, document_id: str, filename: str, file_size: int,
                       processing_time: float, chunk_count: int, user_id: str):
    """
    Log document upload and processing information.
    """
    log_data = {
        "event": "document_upload",
        "document_id": document_id,
        "filename": filename,
        "file_size_bytes": file_size,
        "processing_time_seconds": processing_time,
        "chunk_count": chunk_count,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Document Upload: {log_data}")


def log_search_query(logger, query: str, project_id: str, user_id: str, 
                    result_count: int, search_time: float, reranked: bool = False):
    """
    Log search query information.
    """
    log_data = {
        "event": "search_query",
        "query": query[:100],  # Truncate for privacy
        "project_id": project_id,
        "user_id": user_id,
        "result_count": result_count,
        "search_time_seconds": search_time,
        "reranked": reranked,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Search Query: {log_data}")


def log_error(logger, error: Exception, context: dict = None):
    """
    Log error information with context.
    """
    error_data = {
        "event": "error",
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.error(f"Error: {error_data}", exc_info=True)