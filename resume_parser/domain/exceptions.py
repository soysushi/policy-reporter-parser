"""
Custom exceptions for resume parsing framework.

Design Decision: Structured exception hierarchy for:
- Granular error handling and recovery strategies
- Clear separation between file parsing vs extraction errors
- Contextual error messages with recovery hints
- Logging integration (exceptions carry context)
"""


class ResumeParserError(Exception):
    """
    Base exception for all resume parsing errors.
    
    Design Decision: Common base class allows:
    - Catch-all handling: except ResumeParserError
    - Consistent error structure across framework
    - Easy addition of common attributes (timestamp, context)
    """
    
    def __init__(self, message: str, file_path: str | None = None):
        self.message = message
        self.file_path = file_path
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Include file path in error message for debugging."""
        if self.file_path:
            return f"{self.message} (file: {self.file_path})"
        return self.message


class FileParsingError(ResumeParserError):
    """
    Raised when file cannot be parsed (corrupt, unsupported format, etc).
    
    Recovery Strategy: 
    - Log error with file hash
    - Flag for manual review
    - Try alternative parser if available
    """
    pass


class UnsupportedFileFormatError(FileParsingError):
    """
    Raised when file format is not supported.
    
    Design Decision: Separate from generic parsing error for:
    - Clear user feedback (not corrupt, just unsupported)
    - Metrics tracking (identify missing parsers)
    - Future: Auto-suggest format conversion
    """
    
    def __init__(self, file_path: str, supported_formats: list[str]):
        self.supported_formats = supported_formats
        message = (
            f"Unsupported file format. "
            f"Supported formats: {', '.join(supported_formats)}"
        )
        super().__init__(message, file_path)


class FieldExtractionError(ResumeParserError):
    """
    Raised when a specific field cannot be extracted.
    
    Design Decision: Non-fatal by default (graceful degradation)
    - Extraction coordinator catches and logs
    - Returns partial ResumeData with None for failed fields
    - Metrics: track per-field failure rates
    """
    
    def __init__(self, field_name: str, reason: str, file_path: str | None = None):
        self.field_name = field_name
        self.reason = reason
        message = f"Failed to extract '{field_name}': {reason}"
        super().__init__(message, file_path)


class LLMExtractionError(FieldExtractionError):
    """
    Raised when LLM-based extraction fails.
    
    Recovery Strategy:
    - Retry with exponential backoff (rate limits)
    - Fall back to regex/rule-based extractor
    - Cache successful results to avoid re-processing
    """
    
    def __init__(
        self, 
        field_name: str, 
        reason: str, 
        file_path: str | None = None,
        retryable: bool = True
    ):
        self.retryable = retryable
        super().__init__(field_name, reason, file_path)


class ValidationError(ResumeParserError):
    """
    Raised when extracted data fails validation.
    
    Example: Email format invalid, name contains numbers, etc.
    
    Design Decision: Separate from extraction errors because:
    - Data WAS extracted, but doesn't meet quality bar
    - Different handling: may want to store raw + validated versions
    - Useful for monitoring extraction quality over time
    """
    
    def __init__(self, field_name: str, value: str, reason: str):
        self.field_name = field_name
        self.value = value
        message = f"Validation failed for '{field_name}': {reason} (value: {value})"
        super().__init__(message)
