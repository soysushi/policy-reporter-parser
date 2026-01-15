#!/usr/bin/env python3
"""
Quick demo script to parse a resume.

Usage:
    python demo.py path/to/resume.pdf
    python demo.py path/to/resume.docx
"""

import sys
import json
import logging
from pathlib import Path

from resume_parser import ResumeExtractor, ResumeParserFramework
from resume_parser.extractors import NameExtractor, EmailExtractor, SkillsExtractor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

def main():
    if len(sys.argv) < 2:
        print("Usage: python demo.py <path_to_resume.pdf|docx>")
        print("\nExample:")
        print("  python demo.py resume.pdf")
        print("  python demo.py /path/to/resume.docx")
        sys.exit(1)
    
    resume_path = sys.argv[1]
    
    # Check file exists
    if not Path(resume_path).exists():
        print(f"Error: File not found: {resume_path}")
        sys.exit(1)
    
    print("=" * 70)
    print("Resume Parser Demo")
    print("=" * 70)
    print(f"\nFile: {resume_path}")
    print("-" * 70)
    
    # Configure extractors
    extractors = {
        'name': NameExtractor(),      # Regex + spaCy NER
        'email': EmailExtractor(),     # Regex
        'skills': SkillsExtractor(),   # Google Gemini LLM
    }
    
    # Create framework
    extractor = ResumeExtractor(extractors)
    framework = ResumeParserFramework(extractor)
    
    # Parse resume
    try:
        print("\nParsing resume...")
        resume_data = framework.parse_resume(resume_path)
        
        print("\n✓ Success!\n")
        print("=" * 70)
        print("EXTRACTED DATA")
        print("=" * 70)
        
        print(f"\n📝 Name:  {resume_data.name or '(not found)'}")
        print(f"📧 Email: {resume_data.email or '(not found)'}")
        
        print(f"\n💼 Skills ({len(resume_data.skills)}):")
        if resume_data.skills:
            for i, skill in enumerate(resume_data.skills, 1):
                print(f"   {i:2d}. {skill}")
        else:
            print("   (no skills found)")
        
        # Completeness check
        print("\n" + "-" * 70)
        if resume_data.is_complete():
            print("✓ All fields extracted successfully")
        else:
            print("⚠ Partial extraction - some fields are missing")
        
        # JSON export
        print("\n" + "=" * 70)
        print("JSON OUTPUT")
        print("=" * 70)
        print(json.dumps(resume_data.to_dict(), indent=2))
        
    except FileNotFoundError:
        print(f"\n✗ Error: File not found: {resume_path}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
        logging.exception("Failed to parse resume")
        sys.exit(1)
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
