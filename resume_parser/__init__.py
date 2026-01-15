"""Resume Parser Framework - Production-grade resume parsing system.

This framework provides a pluggable architecture for parsing resumes from
multiple file formats and extracting structured information using configurable
extraction strategies.

Usage:
    from resume_parser import ResumeParserFramework, ResumeExtractor
    from resume_parser.extractors import NameExtractor, EmailExtractor, SkillsExtractor
    
    # Configure extractors
    extractors = {
        'name': NameExtractor(),
        'email': EmailExtractor(),
        'skills': SkillsExtractor(api_key='your-api-key')
    }
    
    # Create framework
    extractor = ResumeExtractor(extractors)
    framework = ResumeParserFramework(extractor)
    
    # Parse resume
    resume_data = framework.parse_resume('path/to/resume.pdf')
    print(resume_data.to_dict())
"""

__version__ = "1.0.0"

# Lazy imports to avoid loading all dependencies at import time
def __getattr__(name):
    if name == "ResumeData":
        from resume_parser.domain import ResumeData
        return ResumeData
    elif name == "ResumeExtractor":
        from resume_parser.extractor import ResumeExtractor
        return ResumeExtractor
    elif name == "ResumeParserFramework":
        from resume_parser.framework import ResumeParserFramework
        return ResumeParserFramework
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "ResumeParserFramework",
    "ResumeExtractor",
    "ResumeData",
]
