"""
Resume Parser Framework - Main entry point.

Design Decision: Facade pattern for:
- Simple, unified interface for clients
- Encapsulates complexity of parser + extractor coordination
- Single method: parse_resume(file_path) -> ResumeData
- Composition of FileParser and ResumeExtractor
"""

import logging
from pathlib import Path

from resume_parser.domain.exceptions import FileParsingError, UnsupportedFileFormatError
from resume_parser.domain.models import ResumeData
from resume_parser.extractor import ResumeExtractor
from resume_parser.parsers.factory import ParserFactory

logger = logging.getLogger(__name__)


class ResumeParserFramework:
    """
    Main framework for parsing resumes and extracting structured data.
    
    Design Decisions:
    - Facade pattern: Single interface hiding internal complexity
    - Composition: Uses FileParser + ResumeExtractor
    - Factory delegation: Parser selection automated by file extension
    - Single responsibility: File parsing + field extraction coordination
    
    Architecture:
    - This is the "Application Service" layer in DDD
    - Orchestrates domain objects (parsers, extractors, models)
    - Stateless: Can be used as singleton
    - Thread-safe: No shared mutable state
    
    Scalability:
    - Horizontal scaling: Deploy multiple instances
    - Async variant: parse_resume_async() for concurrent processing
    - Queue integration: Celery task wrapper for background jobs
    - API-ready: Can wrap in FastAPI endpoint directly
    
    System Design Example (Production):
    ```
    # API Layer
    @app.post("/api/v1/resumes/parse")
    async def parse_resume_endpoint(file: UploadFile):
        framework = ResumeParserFramework(extractor)
        data = framework.parse_resume(file.filename)
        return data.to_dict()
    
    # With caching
    @cache(key=lambda path: hash_file(path), ttl=3600)
    def parse_resume_cached(file_path: str) -> ResumeData:
        return framework.parse_resume(file_path)
    ```
    """
    
    def __init__(self, extractor: ResumeExtractor):
        """
        Initialize framework with resume extractor.
        
        Args:
            extractor: ResumeExtractor instance with configured extractors
            
        Design Decision: Dependency injection of extractor
        - Flexible: Client configures extraction strategy
        - Testable: Can inject mock extractor
        - Follows SOLID principles (Dependency Inversion)
        
        Example:
            extractors = {
                'name': NameExtractor(),
                'email': EmailExtractor(),
                'skills': SkillsExtractor(api_key='...')
            }
            extractor = ResumeExtractor(extractors)
            framework = ResumeParserFramework(extractor)
        """
        self.extractor = extractor
        
        logger.info("Initialized ResumeParserFramework")
    
    def parse_resume(self, file_path: str) -> ResumeData:
        """
        Parse resume file and extract structured data.
        
        This is the main entry point for the framework.
        
        Args:
            file_path: Path to resume file (.pdf or .docx)
            
        Returns:
            ResumeData instance with extracted fields
            
        Raises:
            FileNotFoundError: If file doesn't exist
            UnsupportedFileFormatError: If file format not supported
            FileParsingError: If file cannot be parsed
            
        Design Decision: End-to-end operation in single method
        - Parse file -> Extract text -> Extract fields -> Return data
        - All error handling unified
        - Logging at each stage for observability
        
        N+1 Prevention: Pipeline execution
        1. Parse file once (file -> text)
        2. Extract all fields from text (text -> fields)
        3. Build data model once (fields -> ResumeData)
        
        Performance: O(n) where n = file size
        - File parsing: O(n)
        - Text extraction: O(n) for each field
        - Model creation: O(1)
        
        Caching Strategy (production):
        - Cache key: SHA256(file_content)
        - Cache value: ResumeData JSON
        - TTL: 1 hour (resumes rarely change)
        - Storage: Redis for distributed cache
        """
        logger.info(f"Starting resume parsing for file: {file_path}")
        
        # Validate file path
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")
        
        # Step 1: Get appropriate parser based on file extension
        # Design Decision: Factory pattern abstracts parser selection
        try:
            parser = ParserFactory.get_parser(file_path)
        except UnsupportedFileFormatError as e:
            logger.error(f"Unsupported file format: {file_path}")
            raise
        
        # Step 2: Parse file to extract text
        # Design Decision: Parse once, use multiple times (N+1 prevention)
        try:
            logger.debug(f"Parsing file with {parser.__class__.__name__}")
            text = parser.parse(file_path)
            logger.info(f"Successfully parsed file, extracted {len(text)} characters")
        except FileParsingError as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error parsing file {file_path}: {e}")
            raise FileParsingError(f"Unexpected error: {str(e)}", file_path) from e
        
        # Step 3: Extract structured fields from text
        # Design Decision: Extractor handles all field extraction
        try:
            logger.debug("Extracting structured fields from text")
            resume_data = self.extractor.extract(text)
            logger.info(f"Successfully extracted resume data: {resume_data.to_dict()}")
        except Exception as e:
            logger.exception(f"Failed to extract fields from text: {e}")
            # Return empty ResumeData rather than fail completely
            # Design Decision: Graceful degradation
            resume_data = ResumeData()
        
        # Step 4: Return structured data
        return resume_data
    
    def get_supported_formats(self) -> list[str]:
        """
        Get list of supported file formats.
        
        Design Decision: Expose parser capabilities
        - Useful for UI validation
        - API documentation
        - Client-side file picker configuration
        
        Returns:
            List of supported file extensions (e.g., ['.pdf', '.docx'])
        """
        return ParserFactory.get_supported_formats()
    
    def get_extractable_fields(self) -> list[str]:
        """
        Get list of fields that can be extracted.
        
        Design Decision: Expose extractor capabilities
        - Dynamic schema generation
        - API documentation
        - Runtime introspection
        
        Returns:
            List of field names (e.g., ['name', 'email', 'skills'])
        """
        return self.extractor.get_available_fields()
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate if file can be parsed by this framework.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            True if file can be parsed, False otherwise
            
        Design Decision: Pre-validation method
        - Fail fast before expensive parsing
        - Useful for batch processing (filter invalid files)
        - API: POST /resumes/validate endpoint
        """
        try:
            path = Path(file_path)
            
            # Check file exists
            if not path.exists() or not path.is_file():
                return False
            
            # Check format is supported
            extension = path.suffix.lower()
            return extension in self.get_supported_formats()
            
        except Exception as e:
            logger.warning(f"File validation failed for {file_path}: {e}")
            return False
