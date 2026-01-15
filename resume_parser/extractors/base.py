"""
Base abstraction for field extractors.

Design Decision: Strategy Pattern for:
- Pluggable extraction algorithms per field
- Easy A/B testing of different strategies
- Independent scaling of expensive extractors (LLM)
- Composition over inheritance (coordinator uses extractors)
"""

from abc import ABC, abstractmethod


class FieldExtractor(ABC):
    """
    Abstract base class for field extraction strategies.
    
    Design Decisions:
    - Single responsibility: Extract one field type
    - Stateless: No instance variables for thread-safety
    - Returns Optional: Graceful handling of extraction failures
    
    Scalability:
    - Each extractor can be optimized independently
    - Future: Async variants for I/O-bound extractors (LLM API calls)
    - Can run extractors in parallel (ThreadPoolExecutor/ProcessPoolExecutor)
    
    System Design:
    - If moved to microservices: Each extractor could be separate service
    - Database: Cache results keyed by (text_hash, extractor_version)
    - Metrics: Track per-extractor success rates and latencies
    """
    
    @abstractmethod
    def extract(self, text: str) -> str | None:
        """
        Extract specific field from resume text.
        
        Args:
            text: Raw text extracted from resume file
            
        Returns:
            Extracted field value, or None if extraction failed
            
        Raises:
            FieldExtractionError: If extraction fails critically
            (subclasses can choose to return None vs raise)
            
        Design Decision: Accept full text, not parsed structure
        - Keeps extractors independent of file format
        - Each extractor decides what patterns to look for
        - Single text parsing pass prevents N+1 file reads
        
        Performance: O(n) where n = text length
        - Most extractors use regex: O(n)
        - NER models: O(n) with constant factor depending on model
        - LLM: O(1) API call, but high latency
        """
        pass
    
    def get_name(self) -> str:
        """
        Get human-readable name of this extractor.
        
        Design Decision: Used for logging and metrics
        - Track which extractors are fastest/most accurate
        - A/B testing: Compare different strategies
        - Error messages: "NameExtractor failed for resume X"
        """
        return self.__class__.__name__
    
    def can_extract(self, text: str) -> bool:
        """
        Check if this extractor can process the given text.
        
        Optional validation before attempting extraction.
        Default: always returns True (attempt extraction).
        
        Design Decision: Fail-fast optimization
        - Skip expensive extraction if prerequisites missing
        - Example: Skip LLM call if text too short
        - Useful for chaining extractors (primary + fallback)
        """
        return bool(text and text.strip())
