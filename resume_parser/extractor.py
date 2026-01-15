"""
Resume extraction coordinator.

Design Decision: Coordinator pattern for:
- Centralized orchestration of field extractors
- Graceful degradation if some extractors fail
- Single point of configuration for extraction strategy
- Dependency injection of extractors (testability)
"""

import logging
from typing import Dict

from resume_parser.domain.exceptions import FieldExtractionError
from resume_parser.domain.models import ResumeData
from resume_parser.extractors.base import FieldExtractor

logger = logging.getLogger(__name__)


class ResumeExtractor:
    """
    Coordinator for extracting structured data from resume text.
    
    Design Decisions:
    - Dependency injection: Extractors passed as dict (flexible)
    - Graceful degradation: Failed extractors don't halt process
    - Single text pass: All extractors work on same text (N+1 prevention)
    - Fail-safe: Returns partial ResumeData even if some fields fail
    
    Scalability:
    - Extractors are independent: Can parallelize with ThreadPoolExecutor
    - Stateless: Thread-safe, can process multiple resumes concurrently
    - Future: Async/await for I/O-bound extractors (LLM API calls)
    
    System Design:
    - In microservices: This could be orchestrator service
    - Database: Log per-field extraction success/failure metrics
    - Monitoring: Track extraction latencies per field type
    
    CAP Theorem (if distributed):
    - Favor CP (Consistency + Partition tolerance)
    - All extractors must use same text version (consistency)
    - If one extractor service fails, continue with others (partition tolerance)
    - Don't sacrifice availability for single field failure
    """
    
    def __init__(self, extractors: Dict[str, FieldExtractor]):
        """
        Initialize extractor with field extraction strategies.
        
        Args:
            extractors: Dict mapping field name -> extractor instance
                       Expected keys: 'name', 'email', 'skills'
        
        Design Decision: Dict parameter for flexibility
        - Easy to add/remove extractors
        - Clear mapping of field -> strategy
        - Supports multiple strategies per field (A/B testing)
        - Type hints enforce FieldExtractor interface
        
        Example:
            extractors = {
                'name': NameExtractor(),
                'email': EmailExtractor(),
                'skills': SkillsExtractor()
            }
        """
        self.extractors = extractors
        
        # Validate expected fields
        expected_fields = {'name', 'email', 'skills'}
        provided_fields = set(extractors.keys())
        
        if not expected_fields.issubset(provided_fields):
            missing = expected_fields - provided_fields
            logger.warning(f"Missing extractors for fields: {missing}")
        
        logger.info(f"Initialized ResumeExtractor with {len(extractors)} extractors")
    
    def extract(self, text: str) -> ResumeData:
        """
        Extract all fields from resume text.
        
        Args:
            text: Raw text extracted from resume file
            
        Returns:
            ResumeData instance with extracted fields
            
        Design Decision: Always returns ResumeData, never None
        - Graceful degradation: Failed fields are None
        - Partial results are useful (some data better than none)
        - Caller can check is_complete() for validation
        
        N+1 Prevention: Single text input, multiple extractors
        - Text is passed to all extractors (not parsed multiple times)
        - Each extractor is independent (no sequential dependencies)
        - Can parallelize extractor calls in future
        
        Error Handling:
        - Individual extractor failures are caught and logged
        - Process continues even if some extractors fail
        - All exceptions are logged with context
        """
        extracted_data = {}
        
        # Extract each field independently
        # Design Decision: Sequential for now, could parallelize later
        for field_name, extractor in self.extractors.items():
            try:
                logger.debug(f"Extracting field '{field_name}' using {extractor.get_name()}")
                
                # Call extractor
                value = extractor.extract(text)
                extracted_data[field_name] = value
                
                if value is None:
                    logger.warning(f"Failed to extract '{field_name}' - returned None")
                else:
                    logger.info(f"Successfully extracted '{field_name}'")
                    
            except FieldExtractionError as e:
                # Expected exception type
                logger.error(f"Extraction error for '{field_name}': {e}")
                extracted_data[field_name] = None
                
            except Exception as e:
                # Unexpected exception - log with full traceback
                logger.exception(f"Unexpected error extracting '{field_name}': {e}")
                extracted_data[field_name] = None
        
        # Create ResumeData instance
        # Design Decision: Pydantic handles validation and normalization
        resume_data = ResumeData(**extracted_data)
        
        # Log completeness for monitoring
        if resume_data.is_complete():
            logger.info("Successfully extracted all fields")
        else:
            missing = []
            if not resume_data.name:
                missing.append('name')
            if not resume_data.email:
                missing.append('email')
            if not resume_data.skills:
                missing.append('skills')
            logger.warning(f"Incomplete extraction - missing fields: {missing}")
        
        return resume_data
    
    def extract_field(self, text: str, field_name: str) -> str | list | None:
        """
        Extract a single field from resume text.
        
        Args:
            text: Raw text from resume
            field_name: Name of field to extract ('name', 'email', or 'skills')
            
        Returns:
            Extracted field value, or None if extraction fails
            
        Design Decision: Utility method for targeted extraction
        - Useful for re-extracting single field without full parse
        - API endpoint: PATCH /resumes/{id}/fields/{field_name}
        - Cost optimization: Skip expensive extractors if not needed
        """
        if field_name not in self.extractors:
            raise ValueError(
                f"No extractor configured for field '{field_name}'. "
                f"Available fields: {list(self.extractors.keys())}"
            )
        
        extractor = self.extractors[field_name]
        
        try:
            return extractor.extract(text)
        except Exception as e:
            logger.error(f"Failed to extract '{field_name}': {e}")
            return None
    
    def get_available_fields(self) -> list[str]:
        """
        Get list of fields this extractor can extract.
        
        Design Decision: Introspection for API documentation
        - OpenAPI schema generation
        - Client SDK generation
        - Runtime validation
        """
        return list(self.extractors.keys())
