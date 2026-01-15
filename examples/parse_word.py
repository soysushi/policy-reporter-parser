"""
Example: Parse a Word (.docx) resume.

This example demonstrates parsing a Word document resume and extracting
structured information (name, email, skills).
"""

import json
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from resume_parser import ResumeExtractor, ResumeParserFramework
from resume_parser.extractors import EmailExtractor, NameExtractor, SkillsExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Parse a Word resume and display extracted information."""
    print("=" * 60)
    print("Word Resume Parser Example")
    print("=" * 60)
    
    # Configure extractors
    extractors = {
        'name': NameExtractor(),
        'email': EmailExtractor(),
        'skills': SkillsExtractor(),
    }
    
    # Create framework
    extractor = ResumeExtractor(extractors)
    framework = ResumeParserFramework(extractor)
    
    # Parse resume
    docx_path = "tests/fixtures/sample_resume.docx"
    
    if not Path(docx_path).exists():
        print(f"\nError: Sample resume not found at {docx_path}")
        print("Please create a sample Word resume or update the path.")
        return
    
    print(f"\nParsing resume: {docx_path}")
    print("-" * 60)
    
    try:
        # Parse resume file
        resume_data = framework.parse_resume(docx_path)
        
        # Display results
        print("\n✓ Parsing successful!")
        print("\nExtracted Information:")
        print("-" * 60)
        print(f"Name:  {resume_data.name or 'Not found'}")
        print(f"Email: {resume_data.email or 'Not found'}")
        print(f"Skills ({len(resume_data.skills)}):")
        if resume_data.skills:
            for i, skill in enumerate(resume_data.skills, 1):
                print(f"  {i}. {skill}")
        else:
            print("  No skills found")
        
        # Show completion status
        print("\n" + "-" * 60)
        if resume_data.is_complete():
            print("✓ All fields extracted successfully")
        else:
            print("⚠ Some fields missing - partial extraction")
        
        # Export as JSON
        print("\nJSON Output:")
        print("-" * 60)
        print(json.dumps(resume_data.to_dict(), indent=2))
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: File not found - {e}")
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
        logging.exception("Parsing failed")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
