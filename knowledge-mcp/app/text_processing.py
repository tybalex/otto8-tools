import base64
import re
from typing import List, Tuple
from io import BytesIO

def extract_text_from_content(content: bytes, content_type: str) -> str:
    """Extract text from file content based on content type."""
    
    if content_type == "text/plain":
        try:
            decoded = content.decode('utf-8')
            return decoded
        except:
            # If base64 decode fails, assume it's already plain text
            return content
    
    elif content_type == "application/pdf":
        # For PDF files, you'd typically use PyPDF2 or pdfplumber
        # For now, assume content is base64 encoded PDF text
        try:
            decoded = content.decode('utf-8')
            return decoded
        except:
            raise ValueError("Failed to decode PDF content")
    
    elif content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        # For DOCX/DOC files, you'd use python-docx
        try:
            decoded = content.decode('utf-8')
            return decoded
        except:
            raise ValueError("Failed to decode document content")
    
    else:
        # For unsupported types, try to decode as text
        try:
            decoded = content.decode('utf-8')
            return decoded
        except:
            return content

def chunk_text(text: str) -> List[Tuple[str, int]]:
    """
    Split text into overlapping chunks.
    
    Returns:
        List of tuples (chunk_text, start_offset)
    """
    chunk_size = 1000
    chunk_overlap = 200
    
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Calculate end position
        end = start + chunk_size
        
        # If this isn't the last chunk, try to break at a sentence or word boundary
        if end < len(text):
            # Look for sentence endings within the last 100 characters
            sentence_end = text.rfind('.', start, end)
            if sentence_end > start + chunk_size - 100:
                end = sentence_end + 1
            else:
                # If no sentence ending, look for word boundary
                word_boundary = text.rfind(' ', start, end)
                if word_boundary > start + chunk_size - 50:
                    end = word_boundary
        
        # Extract chunk
        chunk = text[start:end].strip()
        if chunk:
            chunks.append((chunk, start))
        
        # Move start position (with overlap)
        start = max(start + 1, end - chunk_overlap)
        
        # Prevent infinite loop
        if start >= len(text):
            break
    
    return chunks

def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters that might cause issues
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    return text.strip() 