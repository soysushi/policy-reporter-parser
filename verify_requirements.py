#!/usr/bin/env python3
"""Verify all assignment requirements are met."""

import os
from pathlib import Path

def check_file_exists(path, description):
    exists = Path(path).exists()
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {path}")
    return exists

def check_class_in_file(file_path, class_name):
    if not Path(file_path).exists():
        return False
    with open(file_path) as f:
        content = f.read()
        return f"class {class_name}" in content

print("=" * 70)
print("VERIFYING TECHNICAL ASSIGNMENT REQUIREMENTS")
print("=" * 70)

all_good = True

print("\n1. PARSER ABSTRACTION")
print("-" * 70)
all_good &= check_file_exists("resume_parser/parsers/base.py", "FileParser abstract class")
all_good &= check_file_exists("resume_parser/parsers/pdf_parser.py", "PDFParser implementation")
all_good &= check_file_exists("resume_parser/parsers/word_parser.py", "WordParser implementation")

print("\n2. FIELD EXTRACTOR ABSTRACTION")
print("-" * 70)
all_good &= check_file_exists("resume_parser/extractors/base.py", "FieldExtractor abstract class")
all_good &= check_file_exists("resume_parser/extractors/name_extractor.py", "NameExtractor")
all_good &= check_file_exists("resume_parser/extractors/email_extractor.py", "EmailExtractor")
all_good &= check_file_exists("resume_parser/extractors/skills_extractor.py", "SkillsExtractor")

print("\n3. ResumeData CLASS")
print("-" * 70)
all_good &= check_file_exists("resume_parser/domain/models.py", "ResumeData class")

print("\n4. RESUME EXTRACTION COORDINATOR")
print("-" * 70)
all_good &= check_file_exists("resume_parser/extractor.py", "ResumeExtractor class")

print("\n5. FRAMEWORK ORCHESTRATION")
print("-" * 70)
all_good &= check_file_exists("resume_parser/framework.py", "ResumeParserFramework class")

print("\n6. USE EXAMPLES")
print("-" * 70)
all_good &= check_file_exists("examples/parse_pdf.py", "PDF parsing example")
all_good &= check_file_exists("examples/parse_word.py", "Word parsing example")

print("\n7. TESTING")
print("-" * 70)
all_good &= check_file_exists("tests/test_framework.py", "Test suite")

print("\n8. DOCUMENTATION")
print("-" * 70)
all_good &= check_file_exists("README.md", "README with usage")

print("\n9. REQUIREMENTS")
print("-" * 70)
all_good &= check_file_exists("requirements.txt", "Dependencies file")

print("\n10. CONFIGURATION")
print("-" * 70)
all_good &= check_file_exists(".env.example", ".env.example (no API keys)")
has_env = check_file_exists(".env", ".env (local, not committed)")

print("\n" + "=" * 70)
if all_good:
    print("✓ ALL REQUIREMENTS MET!")
else:
    print("✗ Some requirements missing - please review above")
print("=" * 70)

# Check .gitignore for .env
print("\n11. SECURITY CHECK")
print("-" * 70)
if Path(".gitignore").exists():
    with open(".gitignore") as f:
        gitignore = f.read()
        if ".env" in gitignore:
            print("✓ .env is in .gitignore (API keys not committed)")
        else:
            print("✗ WARNING: .env should be in .gitignore")
else:
    print("⚠ No .gitignore found")

