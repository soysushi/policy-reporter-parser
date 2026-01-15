"""
Example: Parse a PDF resume.

This example demonstrates parsing a PDF resume file and extracting
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

# Configure logging to see extraction process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """
    Parse a PDF resume and display extracted information.
    
    Design Decision: Dependency injection of extractors
    - Allows customization of extraction strategies
    - Easy to swap implementations for testing/benchmarking
    - Clear separation of concerns
    """
    print("=" * 60)
    print("PDF Resume Parser Example")
    print("=" * 60)
    
    # Step 1: Configure field extractors
    # Design Decision: Dict-based configuration for flexibility
    extractors = {
        'name': NameExtractor(),          # Regex + NER fallback
        'email': EmailExtractor(),         # Regex-based
        'skills': SkillsExtractor(),       # LLM-based (Gemini)
    }
    
    # Step 2: Create extraction coordinator
    extractor = ResumeExtractor(extractors)
    
    # Step 3: Create framework facade
    framework = ResumeParserFramework(extractor)
    
    # Step 4: Parse resume
    # Note: Replace with your actual PDF file path
    pdf_path = "tests/fixtures/sample_resume.pdf"
    
    if not Path(pdf_path).exists():
        print(f"\nError: Sample resume not found at {pdf_path}")
        print("Please create a sample PDF resume or update the path.")
        return
    
    print(f"\nParsing resume: {pdf_path}")
    print("-" * 60)
    
    try:
        # Parse resume file
        resume_data = framework.parse_resume(pdf_path)
        
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
