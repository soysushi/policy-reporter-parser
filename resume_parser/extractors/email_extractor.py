"""
Email extractor using regex patterns.

Design Decision: Regex-only approach for emails
- Email formats are well-defined (RFC 5322)
- Regex is fast, deterministic, and accurate
- No need for LLM/ML overhead
"""

import logging
import re
from typing import Optional

from resume_parser.extractors.base import FieldExtractor

logger = logging.getLogger(__name__)


class EmailExtractor(FieldExtractor):
    """
    Extract email address from resume using regex.
    
    Design Decisions:
    - Single strategy: Regex is sufficient for email extraction
    - RFC 5322 subset: Practical pattern covering 99.9% of emails
    - First match: Assumes first email is candidate's primary contact
    
    Assumptions:
    - Resume contains at least one email address
    - First email in document is most relevant
    - Email format follows standard conventions
    
    Performance:
    - Regex: O(n) where n = text length
    - Early termination: Returns first match
    - No external dependencies or API calls
    """
    
    # Email regex pattern
    # Design Decision: Practical subset of RFC 5322
    # - Matches 99.9% of real-world emails
    # - Avoids overly complex full RFC implementation
    # - Case-insensitive matching
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        re.IGNORECASE
    )
    
    # Blacklist of common false positives
    # Design Decision: Filter out template/placeholder emails
    BLACKLIST = {
        'example@example.com',
        'test@test.com',
        'email@email.com',
        'name@example.com',
        'your.email@example.com',
    }
    
    def extract(self, text: str) -> Optional[str]:
        """
        Extract email address from resume text.
        
        Strategy:
        1. Find all email matches in text
        2. Filter out blacklisted placeholders
        3. Return first valid email
        
        N+1 Prevention: Single regex pass over text
        
        Design Decision: Return first email
        - Primary email typically appears first (header/contact section)
        - If multiple emails, could extend to return list
        - For MVP, single email is sufficient
        """
        if not self.can_extract(text):
            return None
        
        # Find all potential email matches
        matches = self.EMAIL_PATTERN.findall(text)
        
        if not matches:
            logger.warning("No email address found in resume")
            return None
        
        # Filter and return first valid email
        for email in matches:
            email_lower = email.lower().strip()
            
            # Skip blacklisted placeholder emails
            if email_lower in self.BLACKLIST:
                logger.debug(f"Skipping blacklisted email: {email}")
                continue
            
            # Additional validation
            if self._is_valid_email(email_lower):
                logger.info(f"Extracted email: {email_lower}")
                return email_lower
        
        logger.warning("All emails found were invalid or blacklisted")
        return None
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Additional validation for email addresses.
        
        Design Decision: Extra checks beyond regex
        - Length: Reasonable bounds (6-254 chars per RFC)
        - TLD validation: At least 2 chars
        - No spaces: Should have been caught by regex, but double-check
        
        Prevents false positives from edge cases
        """
        # Length check (RFC 5322: max 254 chars, min ~6 for "a@b.co")
        if not (6 <= len(email) <= 254):
            return False
        
        # Must contain @ and . in right order
        if '@' not in email or '.' not in email.split('@')[1]:
            return False
        
        # No whitespace
        if ' ' in email:
            return False
        
        # TLD should be at least 2 chars
        tld = email.split('.')[-1]
        if len(tld) < 2:
            return False
        
        return True
    
    def can_extract(self, text: str) -> bool:
        """
        Check if text has minimum length for email extraction.
        
        Design Decision: Very minimal check
        - Emails can appear anywhere in resume
        - Don't want to skip short resumes
        """
        return bool(text and len(text.strip()) >= 6)  # Shortest email: "a@b.co"
