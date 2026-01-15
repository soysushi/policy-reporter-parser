"""
Domain models for resume parsing framework.

Design Decision: Using Pydantic instead of plain dataclass for:
- Runtime validation with clear error messages
- JSON serialization out of the box
- Type coercion and validation rules
- Better integration with APIs (FastAPI ready)
"""

from typing import List

from pydantic import BaseModel, Field, field_validator, ConfigDict


class ResumeData(BaseModel):
    """
    Rich domain model encapsulating parsed resume data.
    
    Design Decisions:
    - Pydantic BaseModel: Validates data at runtime, prevents invalid state
    - EmailStr: Ensures email format validity at construction time
    - Optional fields with None default: Graceful degradation if extraction fails
    - Immutable by default: Can enable frozen=True for thread-safety
    - JSON serialization: Built-in via model_dump_json() for API responses
    
    Scalability:
    - This model can be easily mapped to DB tables (ORM models)
    - JSONB storage in PostgreSQL for skills array (indexed for search)
    - Can add computed properties (e.g., skill_count) without breaking API
    """
    
    name: str | None = Field(
        None,
        description="Full name extracted from resume",
        examples=["Jane Doe", "John Smith"],
    )
    
    email: str | None = Field(
        None,
        description="Email address extracted from resume",
        examples=["jane.doe@gmail.com"],
    )
    
    skills: List[str] = Field(
        default_factory=list,
        description="List of technical skills extracted from resume",
        examples=[["Python", "Machine Learning", "Django"]],
    )
    
    @field_validator('skills')
    @classmethod
    def deduplicate_skills(cls, v: List[str]) -> List[str]:
        """
        Deduplicate skills while preserving order.
        
        Design Decision: Use dict.fromkeys() instead of set() to maintain 
        insertion order for better UX (skills appear in resume order).
        
        N+1 Prevention: Deduplication happens once at model construction,
        not on every access.
        """
        if not v:
            return []
        # Preserve order while removing duplicates (case-insensitive)
        seen = {}
        result = []
        for skill in v:
            skill_lower = skill.lower().strip()
            if skill_lower and skill_lower not in seen:
                seen[skill_lower] = True
                result.append(skill.strip())
        return result
    
    @field_validator('name', 'email')
    @classmethod
    def strip_whitespace(cls, v: str | None) -> str | None:
        """Strip leading/trailing whitespace from string fields."""
        return v.strip() if v else None
    
    def to_dict(self) -> dict:
        """
        Convert to plain dictionary for JSON serialization.
        
        Design Decision: Explicit method name instead of __dict__ for clarity.
        Handles None values consistently (keeps them, not omits).
        """
        return {
            "name": self.name,
            "email": self.email,
            "skills": self.skills,
        }
    
    def is_complete(self) -> bool:
        """
        Check if all required fields were successfully extracted.
        
        Use case: Quality metrics, retry logic, manual review flagging.
        """
        return bool(self.name and self.email and self.skills)
    
    # Pydantic V2 configuration
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "name": "Jane Doe",
                "email": "jane.doe@gmail.com",
                "skills": ["Machine Learning", "Python", "LLM"],
            }
        }
    )
