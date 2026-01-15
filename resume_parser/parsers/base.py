"""
Base abstraction for file parsers.

Design Decision: ABC (Abstract Base Class) pattern for:
- Contract enforcement: All parsers must implement parse()
- Type safety: MyPy ensures compliance
- LSP (Liskov Substitution): Any FileParser can replace another
- Open/Closed Principle: Open for extension (new parsers), closed for modification
"""

from abc import ABC, abstractmethod


class FileParser(ABC):
    """
    Abstract base class defining the contract for file parsers.
    
    Design Decisions:
    - Single method interface: Adheres to Interface Segregation Principle
    - Returns str, not structured data: Separation of concerns (parsing != extraction)
    - Stateless: No instance variables, pure functions for horizontal scaling
    
    Scalability:
    - Can add async variant: parse_async() for concurrent processing
    - Future: Streaming support for large files: parse_stream(file_path) -> Iterator[str]
    - Cache-friendly: file_path -> text mapping can be memoized by hash
    """
    
    @abstractmethod
    def parse(self, file_path: str) -> str:
        """
        Parse file and extract raw text content.
        
        Args:
            file_path: Absolute path to the file to parse
            
        Returns:
            Raw text content extracted from the file
            
        Raises:
            FileParsingError: If file cannot be parsed
            FileNotFoundError: If file doesn't exist
            PermissionError: If file cannot be read
            
        Design Decision: Return plain string, not structured data
        - Keeps parser responsibility narrow (file -> text)
        - Text extraction is separate from field extraction
        - Easier to test, cache, and compose
        
        N+1 Prevention: Parse once, extract multiple fields from result
        - Caller should cache parse() result to avoid re-reading file
        - In DB scenario: Store extracted text in `resume_text` column
        """
        pass
    
    def supports_file(self, file_path: str) -> bool:
        """
        Check if this parser supports the given file.
        
        Default implementation checks file extension.
        Subclasses can override for more sophisticated detection.
        
        Design Decision: Optional method for validation before parsing
        - Factory can use this for automatic parser selection
        - Fail fast before attempting expensive parse operations
        """
        supported_extensions = self.get_supported_extensions()
        return any(file_path.lower().endswith(ext) for ext in supported_extensions)
    
    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        """
        Return list of file extensions this parser supports.
        
        Returns:
            List of extensions including dot (e.g., ['.pdf', '.PDF'])
            
        Design Decision: Used by factory for O(1) parser lookup
        - Maintains registry: extension -> parser class
        - Case-insensitive matching for better UX
        """
        pass
