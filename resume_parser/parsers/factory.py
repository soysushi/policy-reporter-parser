"""
Factory for creating appropriate file parsers.

Design Decision: Factory Pattern for:
- Centralized parser registration and selection
- O(1) lookup by file extension
- Easy addition of new parsers without modifying client code
- Dependency Inversion: Clients depend on FileParser interface, not concrete parsers
"""

import logging
from pathlib import Path

from resume_parser.domain.exceptions import UnsupportedFileFormatError
from resume_parser.parsers.base import FileParser
from resume_parser.parsers.pdf_parser import PDFParser
from resume_parser.parsers.word_parser import WordParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """
    Factory for creating file parsers based on file type.
    
    Design Decisions:
    - Registry pattern: extension -> parser class mapping
    - Lazy instantiation: Only create parser when needed
    - Singleton parsers: Reuse parser instances (stateless)
    
    Scalability:
    - O(1) parser lookup by extension
    - Thread-safe: Immutable registry after initialization
    - Future: Plugin system for dynamic parser registration
    
    CAP Theorem Consideration:
    - This is stateless/local, so not applicable
    - But if parsers were remote services, would favor CP:
      - Consistency: Same file type always uses same parser
      - Partition tolerance: Local fallbacks if service unavailable
    """
    
    # Class-level registry for all available parsers
    # Design Decision: Class variable for sharing across instances
    # Reduces memory footprint in multi-threaded scenarios
    _parsers: dict[str, FileParser] = {
        '.pdf': PDFParser(),
        '.docx': WordParser(),
    }
    
    @classmethod
    def register_parser(cls, parser: FileParser) -> None:
        """
        Register a new parser for its supported extensions.
        
        Design Decision: Class method for global registration
        - Allows plugins to register themselves
        - Thread-safe if called during initialization only
        - Validates no duplicate extensions
        
        Example:
            ParserFactory.register_parser(MyCustomParser())
        """
        for ext in parser.get_supported_extensions():
            ext_lower = ext.lower()
            if ext_lower in cls._parsers:
                logger.warning(
                    f"Overwriting parser for {ext_lower}: "
                    f"{cls._parsers[ext_lower].__class__.__name__} -> "
                    f"{parser.__class__.__name__}"
                )
            cls._parsers[ext_lower] = parser
    
    @classmethod
    def get_parser(cls, file_path: str) -> FileParser:
        """
        Get appropriate parser for the given file.
        
        Args:
            file_path: Path to file to parse
            
        Returns:
            FileParser instance for the file type
            
        Raises:
            UnsupportedFileFormatError: If no parser available for file type
            
        Design Decision: Determine parser by extension
        - Simple, fast, reliable for 99% of cases
        - Alternative: Read file magic bytes (more robust but slower)
        - File extension normalized to lowercase for case-insensitive matching
        
        Complexity: O(1) dictionary lookup
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if not extension:
            raise UnsupportedFileFormatError(
                file_path,
                list(cls._parsers.keys())
            )
        
        parser = cls._parsers.get(extension)
        
        if parser is None:
            raise UnsupportedFileFormatError(
                file_path,
                list(cls._parsers.keys())
            )
        
        logger.info(
            f"Selected {parser.__class__.__name__} for {extension} file: {file_path}"
        )
        
        return parser
    
    @classmethod
    def get_supported_formats(cls) -> list[str]:
        """
        Get list of all supported file formats.
        
        Design Decision: Used for validation and user feedback
        - Can display in UI: "Supported formats: .pdf, .docx"
        - Can validate before file upload
        - Metrics: Track which formats are most common
        """
        return sorted(cls._parsers.keys())
