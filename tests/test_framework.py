"""
Comprehensive test suite for Resume Parser Framework.

Tests cover all major components with edge cases and integration scenarios.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from resume_parser.domain.models import ResumeData
from resume_parser.domain.exceptions import (
    FileParsingError,
    UnsupportedFileFormatError,
    FieldExtractionError,
)
from resume_parser.parsers.base import FileParser
from resume_parser.parsers.factory import ParserFactory
from resume_parser.extractors.base import FieldExtractor
from resume_parser.extractors.name_extractor import NameExtractor
from resume_parser.extractors.email_extractor import EmailExtractor
from resume_parser.extractors.skills_extractor import SkillsExtractor
from resume_parser.extractor import ResumeExtractor
from resume_parser.framework import ResumeParserFramework


# ============================================================================
# Domain Model Tests
# ============================================================================

class TestResumeData:
    """Test ResumeData domain model."""
    
    def test_create_valid_resume_data(self):
        """Test creating valid ResumeData instance."""
        data = ResumeData(
            name="Jane Doe",
            email="jane@example.com",
            skills=["Python", "Django"]
        )
        assert data.name == "Jane Doe"
        assert data.email == "jane@example.com"
        assert data.skills == ["Python", "Django"]
    
    def test_create_empty_resume_data(self):
        """Test creating empty ResumeData (all fields None/empty)."""
        data = ResumeData()
        assert data.name is None
        assert data.email is None
        assert data.skills == []
    
    def test_skills_deduplication(self):
        """Test that duplicate skills are removed (case-insensitive)."""
        data = ResumeData(
            skills=["Python", "python", "PYTHON", "Django", "Python"]
        )
        # Should keep only first occurrence
        assert len(data.skills) == 2
        assert "Python" in data.skills
        assert "Django" in data.skills
    
    def test_whitespace_stripping(self):
        """Test that whitespace is stripped from name and email."""
        data = ResumeData(
            name="  Jane Doe  ",
            email="  jane@example.com  "
        )
        assert data.name == "Jane Doe"
        assert data.email == "jane@example.com"
    
    def test_is_complete(self):
        """Test is_complete() method."""
        # Complete data
        complete = ResumeData(
            name="Jane", email="jane@test.com", skills=["Python"]
        )
        assert complete.is_complete() is True
        
        # Missing name
        incomplete1 = ResumeData(email="jane@test.com", skills=["Python"])
        assert incomplete1.is_complete() is False
        
        # Missing skills
        incomplete2 = ResumeData(name="Jane", email="jane@test.com")
        assert incomplete2.is_complete() is False
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        data = ResumeData(
            name="Jane", email="jane@test.com", skills=["Python"]
        )
        result = data.to_dict()
        assert result == {
            "name": "Jane",
            "email": "jane@test.com",
            "skills": ["Python"]
        }


# ============================================================================
# Parser Tests
# ============================================================================

class TestParserFactory:
    """Test parser factory pattern."""
    
    def test_get_parser_for_pdf(self):
        """Test getting PDF parser."""
        parser = ParserFactory.get_parser("test.pdf")
        assert parser is not None
        assert ".pdf" in parser.get_supported_extensions()
    
    def test_get_parser_for_docx(self):
        """Test getting Word parser."""
        parser = ParserFactory.get_parser("test.docx")
        assert parser is not None
        assert ".docx" in parser.get_supported_extensions()
    
    def test_get_parser_case_insensitive(self):
        """Test that file extension matching is case-insensitive."""
        parser1 = ParserFactory.get_parser("test.PDF")
        parser2 = ParserFactory.get_parser("test.pdf")
        assert type(parser1) == type(parser2)
    
    def test_unsupported_format(self):
        """Test error on unsupported file format."""
        with pytest.raises(UnsupportedFileFormatError):
            ParserFactory.get_parser("test.txt")
    
    def test_no_extension(self):
        """Test error on file without extension."""
        with pytest.raises(UnsupportedFileFormatError):
            ParserFactory.get_parser("test")
    
    def test_get_supported_formats(self):
        """Test getting list of supported formats."""
        formats = ParserFactory.get_supported_formats()
        assert ".pdf" in formats
        assert ".docx" in formats


# ============================================================================
# Extractor Tests
# ============================================================================

class TestNameExtractor:
    """Test name extraction logic."""
    
    def test_extract_name_with_label(self):
        """Test extracting name with 'Name:' label."""
        text = "Name: John Smith\nEmail: john@example.com"
        extractor = NameExtractor()
        name = extractor.extract(text)
        assert name == "John Smith"
    
    def test_extract_name_title_case(self):
        """Test extracting title-cased name."""
        text = "John Smith\nSoftware Engineer"
        extractor = NameExtractor()
        name = extractor.extract(text)
        assert name == "John Smith"
    
    def test_extract_name_all_caps(self):
        """Test extracting all-caps name (converts to title case)."""
        text = "JOHN SMITH\nDeveloper"
        extractor = NameExtractor()
        name = extractor.extract(text)
        assert name == "John Smith"
    
    def test_extract_name_empty_text(self):
        """Test extraction from empty text."""
        extractor = NameExtractor()
        name = extractor.extract("")
        assert name is None
    
    def test_extract_name_too_short(self):
        """Test that very short text returns None."""
        extractor = NameExtractor()
        name = extractor.extract("Hi")
        assert name is None


class TestEmailExtractor:
    """Test email extraction logic."""
    
    def test_extract_valid_email(self):
        """Test extracting valid email address."""
        text = "Contact: john.doe@example.com for more info"
        extractor = EmailExtractor()
        email = extractor.extract(text)
        assert email == "john.doe@example.com"
    
    def test_extract_email_lowercase(self):
        """Test that email is converted to lowercase."""
        text = "Email: John.Doe@Example.COM"
        extractor = EmailExtractor()
        email = extractor.extract(text)
        assert email == "john.doe@example.com"
    
    def test_multiple_emails(self):
        """Test that first email is extracted when multiple present."""
        text = "first@test.com and second@test.com"
        extractor = EmailExtractor()
        email = extractor.extract(text)
        assert email == "first@test.com"
    
    def test_blacklisted_email(self):
        """Test that blacklisted placeholder emails are skipped."""
        text = "Email: example@example.com or real@test.com"
        extractor = EmailExtractor()
        email = extractor.extract(text)
        assert email == "real@test.com"
    
    def test_no_email(self):
        """Test extraction when no email present."""
        text = "This is text without any email address"
        extractor = EmailExtractor()
        email = extractor.extract(text)
        assert email is None
    
    def test_invalid_email_format(self):
        """Test that malformed emails are rejected."""
        text = "Contact: not-an-email"
        extractor = EmailExtractor()
        email = extractor.extract(text)
        assert email is None


class TestSkillsExtractor:
    """Test skills extraction (mocked LLM)."""
    
    def test_extract_skills_success(self):
        """Test successful skills extraction via LLM."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.text = '{"skills": ["Python", "Django", "PostgreSQL"]}'
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel', return_value=mock_model):
                with patch('google.generativeai.types.GenerationConfig', return_value=Mock()):
                    # Create extractor with mock API key
                    extractor = SkillsExtractor(api_key="test_key")
                    
                    # Text must be at least 50 chars for can_extract() to return True
                    text = "Skills: Python, Django, PostgreSQL, React, and more technical skills"
                    skills = extractor.extract(text)
                    
                    assert skills == ["Python", "Django", "PostgreSQL"]
    
    def test_extract_skills_empty_response(self):
        """Test handling of empty LLM response."""
        with patch('google.generativeai.configure') as mock_configure:
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                with patch('google.generativeai.types') as mock_types:
                    # Mock LLM response
                    mock_response = Mock()
                    mock_response.text = '{"skills": []}'
                    mock_model = Mock()
                    mock_model.generate_content.return_value = mock_response
                    mock_model_class.return_value = mock_model
                    
                    # Mock GenerationConfig
                    mock_types.GenerationConfig = Mock(return_value=Mock())
                    
                    extractor = SkillsExtractor(api_key="test_key")
                    skills = extractor.extract("No skills here but needs to be at least 50 characters long")
                    
                    assert skills == []  # Returns empty list instead of None
    
    def test_api_key_required(self):
        """Test that API key is required."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                SkillsExtractor()
    
    def test_extract_skills_text_too_short(self):
        """Test that very short text is rejected."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel'):
                with patch('google.generativeai.types'):
                    extractor = SkillsExtractor(api_key="test_key")
                    skills = extractor.extract("Hi")
                    assert skills == []  # Returns empty list for text that's too short


# ============================================================================
# Integration Tests
# ============================================================================

class TestResumeExtractor:
    """Test resume extraction coordinator."""
    
    def test_extract_all_fields(self):
        """Test extracting all fields with mock extractors."""
        # Create mock extractors
        name_extractor = Mock(spec=FieldExtractor)
        name_extractor.extract.return_value = "John Doe"
        name_extractor.get_name.return_value = "NameExtractor"
        
        email_extractor = Mock(spec=FieldExtractor)
        email_extractor.extract.return_value = "john@test.com"
        email_extractor.get_name.return_value = "EmailExtractor"
        
        skills_extractor = Mock(spec=FieldExtractor)
        skills_extractor.extract.return_value = ["Python", "Django"]
        skills_extractor.get_name.return_value = "SkillsExtractor"
        
        extractors = {
            'name': name_extractor,
            'email': email_extractor,
            'skills': skills_extractor,
        }
        
        extractor = ResumeExtractor(extractors)
        resume_data = extractor.extract("Sample text")
        
        assert resume_data.name == "John Doe"
        assert resume_data.email == "john@test.com"
        assert resume_data.skills == ["Python", "Django"]
        assert resume_data.is_complete()
    
    def test_extract_with_failures(self):
        """Test graceful degradation when some extractors fail."""
        name_extractor = Mock(spec=FieldExtractor)
        name_extractor.extract.return_value = "John Doe"
        name_extractor.get_name.return_value = "NameExtractor"
        
        email_extractor = Mock(spec=FieldExtractor)
        email_extractor.extract.side_effect = Exception("Failed")
        email_extractor.get_name.return_value = "EmailExtractor"
        
        skills_extractor = Mock(spec=FieldExtractor)
        skills_extractor.extract.return_value = ["Python"]
        skills_extractor.get_name.return_value = "SkillsExtractor"
        
        extractors = {
            'name': name_extractor,
            'email': email_extractor,
            'skills': skills_extractor,
        }
        
        extractor = ResumeExtractor(extractors)
        resume_data = extractor.extract("Sample text")
        
        # Should return partial data
        assert resume_data.name == "John Doe"
        assert resume_data.email is None  # Failed extractor
        assert resume_data.skills == ["Python"]
        assert not resume_data.is_complete()


class TestResumeParserFramework:
    """Test main framework facade."""
    
    def test_validate_file(self):
        """Test file validation logic."""
        mock_extractor = Mock(spec=ResumeExtractor)
        framework = ResumeParserFramework(mock_extractor)
        
        # Valid format (not checking existence in this test)
        # We can't test actual files without fixtures
        assert framework.get_supported_formats() == ['.docx', '.pdf']
    
    def test_get_extractable_fields(self):
        """Test getting list of extractable fields."""
        mock_extractor = Mock(spec=ResumeExtractor)
        mock_extractor.get_available_fields.return_value = ['name', 'email', 'skills']
        
        framework = ResumeParserFramework(mock_extractor)
        fields = framework.get_extractable_fields()
        
        assert 'name' in fields
        assert 'email' in fields
        assert 'skills' in fields
    
    def test_parse_nonexistent_file(self):
        """Test error handling for non-existent file."""
        mock_extractor = Mock(spec=ResumeExtractor)
        framework = ResumeParserFramework(mock_extractor)
        
        with pytest.raises(FileNotFoundError):
            framework.parse_resume("/nonexistent/file.pdf")


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_text_extraction(self):
        """Test extraction from empty text."""
        name_ext = NameExtractor()
        email_ext = EmailExtractor()
        
        assert name_ext.extract("") is None
        assert email_ext.extract("") is None
    
    def test_very_long_text(self):
        """Test extraction from very long text."""
        # Create long text
        long_text = "John Doe\njohn@test.com\n" + ("X" * 10000)
        
        name_ext = NameExtractor()
        email_ext = EmailExtractor()
        
        # Should still extract from beginning
        name = name_ext.extract(long_text)
        email = email_ext.extract(long_text)
        
        assert name == "John Doe"
        assert email == "john@test.com"
    
    def test_special_characters(self):
        """Test handling of special characters."""
        text = "Name: João Silva\nEmail: joão@example.com"
        
        name_ext = NameExtractor()
        email_ext = EmailExtractor()
        
        # Should handle unicode
        name = name_ext.extract(text)
        assert name is not None
    
    def test_concurrent_extraction(self):
        """Test that extractors are thread-safe."""
        import threading
        
        extractor = EmailExtractor()
        results = []
        
        def extract():
            result = extractor.extract("test@example.com")
            results.append(result)
        
        threads = [threading.Thread(target=extract) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All threads should get same result
        assert len(results) == 10
        assert all(r == "test@example.com" for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
