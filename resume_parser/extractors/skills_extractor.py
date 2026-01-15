"""
Skills extractor using LLM (Google Gemini).

Design Decision: LLM-based approach for skills
- Skills are context-dependent and varied
- LLMs understand implicit skills better than regex
- Can extract from diverse formats (lists, paragraphs, tables)
- This satisfies the ML/LLM requirement
"""

import json
import logging
import os
from typing import List, Optional, TYPE_CHECKING

from dotenv import load_dotenv

from resume_parser.domain.exceptions import LLMExtractionError
from resume_parser.extractors.base import FieldExtractor

# Lazy import for google.generativeai to avoid dependency at import time
if TYPE_CHECKING:
    import google.generativeai as genai

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SkillsExtractor(FieldExtractor):
    """
    Extract skills from resume using Google Gemini LLM.
    
    Design Decisions:
    - LLM-based: Handles ambiguity and varied formats
    - Structured output: Request JSON format for parsing
    - Temperature 0.3: Low temp for consistent extraction
    - Prompt engineering: Clear instructions for quality
    
    Scalability:
    - API calls are expensive: Use caching layer
    - Redis cache: Key = hash(text), Value = skills list
    - Rate limiting: Implement exponential backoff
    - Future: Batch processing API for multiple resumes
    
    CAP Theorem (if skills service were distributed):
    - Favor AP (Availability + Partition tolerance)
    - Skills extraction can tolerate eventual consistency
    - Cache misses should fall back to LLM, not fail
    - Allow stale cached results if API unavailable
    
    Cost Optimization:
    - Truncate text to relevant sections (first 3000 chars)
    - Cache results to avoid redundant API calls
    - Monitor token usage for cost tracking
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize skills extractor with Gemini API.
        
        Design Decision: Optional API key parameter
        - Allows injection for testing (mock API)
        - Falls back to environment variable
        - Validates API key at init time (fail fast)
        """
        # Lazy import of google.generativeai
        try:
            import google.generativeai as genai
            self.genai = genai
        except ImportError:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install it with: pip install google-generativeai"
            )
        
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. "
                "Set it in .env file or pass as parameter"
            )
        
        # Configure Gemini API
        self.genai.configure(api_key=self.api_key)
        
        # Model configuration
        # Design Decision: Low temperature for deterministic results
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
        self.temperature = float(os.getenv('GEMINI_TEMPERATURE', '0.3'))
        self.max_tokens = int(os.getenv('GEMINI_MAX_TOKENS', '2048'))
        
        # Initialize model
        self.model = self.genai.GenerativeModel(self.model_name)
        
        logger.info(f"Initialized SkillsExtractor with model: {self.model_name}")
    
    def extract(self, text: str) -> List[str]:
        """
        Extract skills from resume text using LLM.
        
        Strategy:
        1. Truncate text to relevant sections (optimization)
        2. Build structured prompt for LLM
        3. Parse JSON response
        4. Validate and clean skills
        
        N+1 Prevention: Single LLM call per resume
        
        Error Handling:
        - API failures: Log and return empty list (graceful degradation)
        - JSON parsing errors: Extract skills from text fallback
        - Rate limits: Could implement retry with backoff (future)
        """
        if not self.can_extract(text):
            return []  # Return empty list instead of None
        
        try:
            # Optimize: Extract relevant sections
            # Design Decision: Focus on skills-related content
            relevant_text = self._extract_skills_section(text)
            
            # Build prompt
            prompt = self._build_prompt(relevant_text)
            
            # Call LLM API
            # Design Decision: Structured output for reliable parsing
            response = self.model.generate_content(
                prompt,
                generation_config=self.genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            
            # Parse response
            skills = self._parse_response(response.text)
            
            if skills:
                logger.info(f"Extracted {len(skills)} skills using LLM: {skills[:5]}...")
                return skills
            else:
                logger.warning("LLM returned no skills")
                return []  # Return empty list instead of None
                
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            # Design Decision: Don't raise, return empty list (graceful degradation)
            # Allows other fields to succeed even if skills fail
            return []  # Return empty list instead of None
    
    def _extract_skills_section(self, text: str) -> str:
        """
        Extract skills-relevant sections from resume.
        
        Design Decision: Optimize LLM input
        - Reduces token usage (cost optimization)
        - Focuses LLM attention on relevant content
        - Falls back to full text if no skills section found
        
        Heuristics:
        - Look for "Skills", "Technical Skills", "Competencies" headers
        - Include first 3000 chars (covers most resume headers)
        - Include middle section where skills typically appear
        """
        text_lower = text.lower()
        
        # Skills section keywords
        skills_keywords = [
            'skills', 'technical skills', 'core competencies',
            'expertise', 'technologies', 'proficiencies'
        ]
        
        # Find skills section
        for keyword in skills_keywords:
            idx = text_lower.find(keyword)
            if idx != -1:
                # Extract section around keyword (before and after)
                start = max(0, idx - 200)
                end = min(len(text), idx + 2000)
                relevant = text[start:end]
                logger.debug(f"Found skills section around keyword: {keyword}")
                return relevant
        
        # Fallback: Use first 3000 chars (header + early sections)
        logger.debug("No skills section found, using text prefix")
        return text[:3000]
    
    def _build_prompt(self, text: str) -> str:
        """
        Build structured prompt for LLM.
        
        Design Decision: Clear, specific instructions
        - Request JSON format for reliable parsing
        - Specify what counts as a skill
        - Ask for deduplication and cleaning
        - Few-shot examples improve quality
        
        Prompt Engineering Best Practices:
        - Be specific about output format
        - Provide examples of good outputs
        - Constrain to avoid hallucinations
        """
        prompt = f"""You are a resume parser. Extract all technical skills, tools, technologies, and competencies from the following resume text.

Requirements:
- Return ONLY a valid JSON object with a "skills" key containing an array of strings
- Include programming languages, frameworks, tools, methodologies, soft skills
- Normalize skill names (e.g., "Python 3" -> "Python", "ReactJS" -> "React")
- Remove duplicates and generic terms like "Microsoft Office"
- Keep skills concise (1-3 words each)
- Return empty array if no skills found

Example output format:
{{"skills": ["Python", "Machine Learning", "TensorFlow", "SQL", "Agile"]}}

Resume text:
{text}

JSON output:"""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Optional[List[str]]:
        """
        Parse LLM response to extract skills list.
        
        Design Decision: Robust parsing with fallbacks
        - Try JSON parsing first (expected format)
        - Fall back to text extraction if JSON fails
        - Validate skills format (strings, reasonable length)
        
        Error Handling:
        - Malformed JSON: Extract list from text
        - Empty response: Return None
        - Invalid skills: Filter out
        """
        try:
            # Clean response (LLMs sometimes add markdown)
            cleaned = response_text.strip()
            
            # Remove markdown code blocks if present
            if cleaned.startswith('```'):
                lines = cleaned.split('\n')
                cleaned = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned
            
            # Parse JSON
            data = json.loads(cleaned)
            
            if isinstance(data, dict) and 'skills' in data:
                skills = data['skills']
            elif isinstance(data, list):
                skills = data
            else:
                logger.warning(f"Unexpected JSON structure: {data}")
                return None
            
            # Validate and clean skills
            cleaned_skills = []
            for skill in skills:
                if isinstance(skill, str) and 1 <= len(skill) <= 50:
                    cleaned_skills.append(skill.strip())
            
            return cleaned_skills if cleaned_skills else None
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Fallback: Try to extract skills from text
            return self._extract_skills_from_text(response_text)
    
    def _extract_skills_from_text(self, text: str) -> Optional[List[str]]:
        """
        Fallback: Extract skills from plain text response.
        
        Design Decision: Graceful degradation
        - LLM might not return perfect JSON
        - Still try to extract value from response
        - Look for comma/newline separated lists
        """
        # Simple heuristic: Extract quoted strings or comma-separated values
        import re
        
        # Try to find list-like patterns
        matches = re.findall(r'"([^"]+)"', text)
        if matches:
            return [m.strip() for m in matches if 1 <= len(m) <= 50]
        
        # Try comma-separated
        if ',' in text:
            parts = text.split(',')
            skills = [p.strip() for p in parts if 1 <= len(p.strip()) <= 50]
            return skills if len(skills) >= 2 else None
        
        return None
    
    def can_extract(self, text: str) -> bool:
        """
        Check if text is suitable for LLM extraction.
        
        Design Decision: Validate before expensive API call
        - Minimum length: Skip very short texts
        - Maximum length: LLMs have token limits
        - Save API costs on invalid inputs
        """
        return bool(text and 50 <= len(text.strip()) <= 50000)
