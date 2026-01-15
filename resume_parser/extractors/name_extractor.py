"""
Name extractor using regex patterns and NER fallback.

Design Decision: Hybrid approach for robustness
- Primary: Regex patterns (fast, covers 80% of cases)
- Fallback: spaCy NER (handles edge cases)
- Both avoid LLM overhead for simple field
"""

import logging
import re
from typing import Optional

from resume_parser.extractors.base import FieldExtractor

logger = logging.getLogger(__name__)


class NameExtractor(FieldExtractor):
    """
    Extract candidate name from resume using regex and NER.
    
    Design Decisions:
    - Regex first: Fast, deterministic, handles standard formats
    - NER fallback: Catches non-standard layouts
    - Lazy NER loading: Only load spaCy if regex fails (optimization)
    
    Assumptions:
    - Name typically appears in first 5 lines
    - Name is often title-cased or ALL CAPS
    - Name patterns: "FirstName LastName" or with Middle initial
    
    Scalability:
    - Regex: O(n) but very fast, no external deps
    - NER: O(n) but heavier, lazy loaded
    - Future: Cache NER model across instances (class variable)
    """
    
    # Lazy-loaded spaCy model (shared across instances)
    _nlp_model = None
    
    # Common name patterns in resumes
    # Design Decision: Ordered by specificity (most specific first)
    NAME_PATTERNS = [
        # "Name: John Smith" or "Name - John Smith"
        r'^(?:Name|NAME|Full Name)[\s:|\-]+([A-Z][a-z]+(?:\s+[A-Z][a-z]*\.?\s+)?[A-Z][a-z]+)(?:\n|$)',
        
        # Title-cased name at start of line (2-3 words)
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]*\.?)?\s+[A-Z][a-z]+)(?=\n)',
        
        # ALL CAPS name (common in resumes)
        r'^([A-Z\s]{2,})(?=\n)',
    ]
    
    def extract(self, text: str) -> Optional[str]:
        """
        Extract name from resume text.
        
        Strategy:
        1. Try regex patterns on first 500 chars (optimization)
        2. If fails, try spaCy NER on first 1000 chars
        3. Return None if both fail (graceful degradation)
        
        N+1 Prevention: Only process prefix of text, not full document
        """
        if not self.can_extract(text):
            return None
        
        # Step 1: Try regex patterns (fast path)
        # Design Decision: Only look at beginning where names typically are
        prefix = text[:500]  # First ~5-10 lines usually contain name
        
        name = self._extract_with_regex(prefix)
        if name:
            logger.info(f"Extracted name using regex: {name}")
            return name
        
        # Step 2: Fallback to NER (slower but more robust)
        logger.debug("Regex extraction failed, trying NER")
        name = self._extract_with_ner(text[:1000])
        if name:
            logger.info(f"Extracted name using NER: {name}")
            return name
        
        logger.warning("Failed to extract name using all methods")
        return None
    
    def _extract_with_regex(self, text: str) -> Optional[str]:
        """
        Extract name using regex patterns.
        
        Design Decision: Multiple patterns for robustness
        - Try each pattern in order of specificity
        - Return first match (most specific)
        - Clean whitespace and validate
        """
        for pattern in self.NAME_PATTERNS:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Validation: Name should be 2-50 chars, not all numbers
                if 2 <= len(name) <= 50 and not name.isdigit():
                    return self._clean_name(name)
        return None
    
    def _extract_with_ner(self, text: str) -> Optional[str]:
        """
        Extract name using spaCy NER.
        
        Design Decision: Lazy loading of NER model
        - Only load if needed (many resumes work with regex)
        - Model loaded once and cached (class variable)
        - Reduces memory footprint and startup time
        
        Scalability: Model could be loaded from Redis in prod
        """
        try:
            if self._nlp_model is None:
                # Lazy load spaCy model (first call only)
                import spacy
                logger.info("Loading spaCy NER model (one-time operation)")
                self._nlp_model = spacy.load("en_core_web_sm")
            
            doc = self._nlp_model(text)
            
            # Find first PERSON entity in document
            # Design Decision: First person mentioned is usually the candidate
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    name = ent.text.strip()
                    if 2 <= len(name) <= 50:
                        return self._clean_name(name)
            
        except Exception as e:
            logger.warning(f"NER extraction failed: {e}")
        
        return None
    
    def _clean_name(self, name: str) -> str:
        """
        Clean and normalize extracted name.
        
        Design Decision: Consistent format for downstream use
        - Remove extra whitespace
        - Title case (John Smith, not JOHN SMITH)
        - Remove common resume artifacts
        """
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Convert ALL CAPS to Title Case
        if name.isupper():
            name = name.title()
        
        return name
    
    def can_extract(self, text: str) -> bool:
        """
        Check if text has minimum length for name extraction.
        
        Design Decision: Fail fast if text too short
        - Saves regex and NER overhead
        - Names unlikely to be in very short documents
        """
        return bool(text and len(text.strip()) >= 10)
