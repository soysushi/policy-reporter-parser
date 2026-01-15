"""
PDF file parser implementation.

Design Decision: Using pdfplumber as primary, PyPDF2 as fallback
- pdfplumber: Better text extraction, handles complex layouts
- PyPDF2: Faster, good for simple PDFs
- Fallback strategy: If pdfplumber fails, try PyPDF2
"""

import logging
from pathlib import Path

import pdfplumber
import PyPDF2

from resume_parser.domain.exceptions import FileParsingError
from resume_parser.parsers.base import FileParser

logger = logging.getLogger(__name__)


class PDFParser(FileParser):
    """
    Parser for PDF files with fallback mechanism.
    
    Design Decisions:
    - Dual-library approach: Robustness over speed
    - Preserve formatting: Keep newlines and spacing for better extraction
    - Error handling: Specific error messages for debugging
    
    Scalability:
    - Stateless: Can process multiple files concurrently
    - Memory efficient: Reads page-by-page, not entire file
    - Future: Add OCR support for scanned PDFs (Tesseract)
    """
    
    def parse(self, file_path: str) -> str:
        """
        Extract text from PDF file.
        
        Strategy:
        1. Try pdfplumber (better quality)
        2. Fall back to PyPDF2 (more forgiving)
        3. Raise FileParsingError if both fail
        
        N+1 Prevention: Parse once, extract all fields from result
        """
        path = Path(file_path)
        
        # Validate file exists and is readable
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        if not path.is_file():
            raise FileParsingError(f"Path is not a file: {file_path}", file_path)
        
        # Try pdfplumber first (better quality)
        try:
            return self._parse_with_pdfplumber(file_path)
        except Exception as e:
            logger.warning(f"pdfplumber failed for {file_path}, trying PyPDF2: {e}")
            
            # Fallback to PyPDF2
            try:
                return self._parse_with_pypdf2(file_path)
            except Exception as e2:
                logger.error(f"Both PDF parsers failed for {file_path}: {e2}")
                raise FileParsingError(
                    f"Failed to parse PDF: {str(e2)}", 
                    file_path
                ) from e2
    
    def _parse_with_pdfplumber(self, file_path: str) -> str:
        """
        Parse PDF using pdfplumber.
        
        Design Decision: pdfplumber for:
        - Better handling of complex layouts
        - Table extraction capabilities (future use)
        - More accurate text positioning
        """
        text_parts = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Extract text preserving layout
                page_text = page.extract_text()
                if page_text:  # Some pages might be empty or images
                    text_parts.append(page_text)
        
        if not text_parts:
            raise FileParsingError("No text content found in PDF", file_path)
        
        # Join pages with clear separation
        return "\n\n".join(text_parts)
    
    def _parse_with_pypdf2(self, file_path: str) -> str:
        """
        Parse PDF using PyPDF2 as fallback.
        
        Design Decision: PyPDF2 for:
        - More forgiving with malformed PDFs
        - Faster for simple documents
        - Better password-protected PDF handling
        """
        text_parts = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                raise FileParsingError(
                    "PDF is encrypted/password-protected", 
                    file_path
                )
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        if not text_parts:
            raise FileParsingError("No text content found in PDF", file_path)
        
        return "\n\n".join(text_parts)
    
    def get_supported_extensions(self) -> list[str]:
        """
        PDF parser supports .pdf files.
        
        Design Decision: Case-insensitive for better UX
        - Factory will normalize to lowercase before lookup
        """
        return ['.pdf', '.PDF']
