import magic
import PyPDF2
from docx import Document as DocxDocument
from io import BytesIO
from typing import Tuple


def detect_file_type(content: bytes, filename: str) -> str:
    """
    Detect file type using python-magic and filename extension.
    """
    try:
        mime_type = magic.from_buffer(content, mime=True)
        
        if mime_type == "application/pdf":
            return "pdf"
        elif mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                          "application/msword"]:
            return "docx"
        elif mime_type.startswith("text/"):
            return "txt"
        else:
            # Fallback to filename extension
            if filename.lower().endswith('.pdf'):
                return "pdf"
            elif filename.lower().endswith(('.docx', '.doc')):
                return "docx"
            elif filename.lower().endswith(('.txt', '.md', '.markdown')):
                return "txt"
            else:
                return "unknown"
    except Exception:
        # Fallback to filename extension if magic fails
        if filename.lower().endswith('.pdf'):
            return "pdf"
        elif filename.lower().endswith(('.docx', '.doc')):
            return "docx"
        elif filename.lower().endswith(('.txt', '.md', '.markdown')):
            return "txt"
        else:
            return "unknown"


def extract_text_from_pdf(content: bytes) -> Tuple[str, bool]:
    """
    Extract text from PDF content.
    Returns (text, success)
    """
    try:
        pdf_file = BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip(), True
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return "", False


def extract_text_from_docx(content: bytes) -> Tuple[str, bool]:
    """
    Extract text from DOCX content.
    Returns (text, success)
    """
    try:
        docx_file = BytesIO(content)
        doc = DocxDocument(docx_file)
        
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip(), True
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return "", False


def extract_text_from_txt(content: bytes) -> Tuple[str, bool]:
    """
    Extract text from plain text content.
    Returns (text, success)
    """
    try:
        text = content.decode('utf-8')
        return text, True
    except UnicodeDecodeError:
        # Try other encodings
        encodings = ['latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                text = content.decode(encoding)
                return text, True
            except Exception:
                continue
        return "", False


def process_document(content: bytes, filename: str) -> Tuple[str, bool, str]:
    """
    Process document content and extract text.
    Returns (text, success, file_type)
    """
    file_type = detect_file_type(content, filename)
    
    if file_type == "pdf":
        text, success = extract_text_from_pdf(content)
    elif file_type == "docx":
        text, success = extract_text_from_docx(content)
    elif file_type == "txt":
        text, success = extract_text_from_txt(content)
    else:
        return "", False, file_type
    
    return text, success, file_type