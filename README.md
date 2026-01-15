# Resume Parser Framework

A production-grade, pluggable resume parsing framework that supports multiple file formats and configurable field extraction strategies, including ML/LLM-based extraction.

## Features

- **Multiple File Formats**: PDF and Word (.docx) support with extensible parser architecture
- **Pluggable Extractors**: Configurable extraction strategies per field (regex, NER, LLM)
- **LLM Integration**: Google Gemini API for intelligent skills extraction
- **Production-Ready**: Comprehensive error handling, logging, and graceful degradation
- **Scalable Architecture**: Stateless design, ready for horizontal scaling
- **Well-Tested**: Comprehensive unit and integration tests

## Architecture

The framework follows SOLID principles and uses industry-standard design patterns:

```
resume_parser/
├── domain/           # Domain models and exceptions
│   ├── models.py     # ResumeData (Pydantic model)
│   └── exceptions.py # Custom exception hierarchy
├── parsers/          # File format parsers
│   ├── base.py       # FileParser ABC
│   ├── pdf_parser.py # PDF parsing (pdfplumber + PyPDF2 fallback)
│   ├── word_parser.py# Word document parsing
│   └── factory.py    # Parser factory (O(1) lookup)
├── extractors/       # Field extraction strategies
│   ├── base.py       # FieldExtractor ABC
│   ├── name_extractor.py    # Regex + NER
│   ├── email_extractor.py   # Regex-based
│   └── skills_extractor.py  # LLM-based (Gemini)
├── extractor.py      # ResumeExtractor (coordinator)
└── framework.py      # ResumeParserFramework (main entry)
```

### Design Patterns

- **Strategy Pattern**: Pluggable extractors per field
- **Factory Pattern**: Automatic parser selection by file type
- **Facade Pattern**: Simple unified interface (ResumeParserFramework)
- **Coordinator Pattern**: ResumeExtractor orchestrates field extraction
- **Dependency Injection**: Testable, flexible configuration

### System Design Decisions

1. **N+1 Query Prevention**:
   - Parse file once, extract all fields from result
   - Single text input to all extractors
   - Bulk operations, no sequential dependencies

2. **Scalability**:
   - Stateless components (horizontal scaling)
   - Async-ready architecture
   - Redis caching layer (future)
   - Celery queue integration (future)

3. **CAP Theorem** (if distributed):
   - Favor **CP** (Consistency + Partition tolerance) for core data
   - **AP** (Availability + Partition tolerance) for LLM service
   - Graceful degradation on extractor failures

4. **Future Database Schema**:
   ```sql
   CREATE TABLE resumes (
       id UUID PRIMARY KEY,
       file_hash VARCHAR(64) UNIQUE NOT NULL,
       uploaded_at TIMESTAMP NOT NULL,
       processed_at TIMESTAMP
   );
   
   CREATE TABLE resume_data (
       id UUID PRIMARY KEY,
       resume_id UUID REFERENCES resumes(id),
       name VARCHAR(255),
       email VARCHAR(255),
       skills JSONB,  -- PostgreSQL JSONB for flexible querying
       created_at TIMESTAMP NOT NULL
   );
   
   CREATE INDEX idx_resume_file_hash ON resumes(file_hash);
   CREATE INDEX idx_resume_data_email ON resume_data(email) WHERE email IS NOT NULL;
   CREATE INDEX idx_resume_data_skills ON resume_data USING GIN(skills);
   ```

## Installation

### Prerequisites

- Python 3.9+
- Google Gemini API key (for skills extraction)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/soysushi/policy-reporter-parser
   cd policy-reporter-parser
   ```

2. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Download spaCy model (for name extraction):
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

## Usage

### Quick Start - Web Demo

The easiest way to try the framework is with the web interface:

```bash
# Install gradio (optional dependency)
pip install gradio

# Start web demo
python web_demo.py
```

This will open a web interface at `http://localhost:7860` where you can:
- Upload PDF or Word resumes
- See extracted information in real-time
- View JSON output

No API key needed for testing (tests use mocks)!

### Basic Example

```python
from resume_parser import ResumeParserFramework, ResumeExtractor
from resume_parser.extractors import NameExtractor, EmailExtractor, SkillsExtractor

# Configure extractors with your strategies
extractors = {
    'name': NameExtractor(),
    'email': EmailExtractor(),
    'skills': SkillsExtractor()  # Uses GEMINI_API_KEY from .env
}

# Create framework
extractor = ResumeExtractor(extractors)
framework = ResumeParserFramework(extractor)

# Parse resume
resume_data = framework.parse_resume('path/to/resume.pdf')

# Access extracted data
print(f"Name: {resume_data.name}")
print(f"Email: {resume_data.email}")
print(f"Skills: {', '.join(resume_data.skills)}")

# Export as JSON
print(resume_data.to_dict())
```

### PDF Resume Example

```python
# See examples/parse_pdf.py
framework = ResumeParserFramework(extractor)
resume_data = framework.parse_resume('resume.pdf')
```

### Word Resume Example

```python
# See examples/parse_word.py
framework = ResumeParserFramework(extractor)
resume_data = framework.parse_resume('resume.docx')
```

### Custom Extractor

```python
from resume_parser.extractors.base import FieldExtractor

class CustomPhoneExtractor(FieldExtractor):
    def extract(self, text: str) -> str | None:
        import re
        pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        match = re.search(pattern, text)
        return match.group(0) if match else None
    
    def get_supported_extensions(self) -> list[str]:
        return []  # Not applicable for extractors

# Use custom extractor
extractors['phone'] = CustomPhoneExtractor()
```

## Configuration

### Environment Variables

Create a `.env` file with:

```env
# Required: Google Gemini API Key
GEMINI_API_KEY=your_api_key_here

# Optional: Model configuration
GEMINI_MODEL=gemini-pro
GEMINI_TEMPERATURE=0.3
GEMINI_MAX_TOKENS=2048

# Optional: Logging
LOG_LEVEL=INFO
```

### Getting Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

**Note**: 
- The free tier is sufficient for testing
- The Gemini API key is **only required for running the framework**, not for running tests
- All tests use mocked LLM responses and don't make real API calls
- Your interviewer can run tests without an API key

## Testing

**Important**: Use the virtual environment's pytest to avoid import issues.

### Run All Tests

```bash
# Using venv pytest (recommended)
venv/bin/pytest -v

# Or use the convenience script
./run_tests.sh -v
```

### Run with Coverage

```bash
venv/bin/pytest --cov=resume_parser --cov-report=html
```

### Run Specific Tests

```bash
# Specific test file
venv/bin/pytest tests/test_framework.py -v

# Specific test class
venv/bin/pytest tests/test_framework.py::TestNameExtractor -v

# Specific test
venv/bin/pytest tests/test_framework.py::TestNameExtractor::test_extract_name_with_label -v
```

### Test Structure

- All tests are in `tests/test_framework.py`
- Tests cover domain models, parsers, extractors, and integration
- LLM-based tests use mocks (no API calls)

### Troubleshooting Tests

If you encounter "ModuleNotFoundError" when running tests:

1. **Make sure you're using the venv pytest**:
   ```bash
   which pytest  # Should show: /path/to/policy_reporter/venv/bin/pytest
   ```

2. **If pytest is from a different environment** (e.g., conda):
   ```bash
   # Use venv pytest explicitly
   venv/bin/pytest -v
   ```

3. **If spaCy model is missing**:
   ```bash
   venv/bin/python -m spacy download en_core_web_sm
   ```

## Error Handling

The framework uses a structured exception hierarchy:

- `ResumeParserError`: Base exception
  - `FileParsingError`: File cannot be parsed
    - `UnsupportedFileFormatError`: File format not supported
  - `FieldExtractionError`: Field extraction failed
    - `LLMExtractionError`: LLM API call failed
  - `ValidationError`: Extracted data failed validation

All exceptions include context (file_path, field_name) for debugging.

## Performance Considerations

### Optimization Strategies

1. **Caching**: Cache parsed text by file hash
   ```python
   from functools import lru_cache
   import hashlib
   
   @lru_cache(maxsize=100)
   def parse_cached(file_hash: str) -> str:
       return parser.parse(file_path)
   ```

2. **Parallel Extraction**: Use ThreadPoolExecutor for multiple resumes
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   with ThreadPoolExecutor() as executor:
       results = executor.map(framework.parse_resume, file_paths)
   ```

3. **Async Processing**: Queue heavy operations (LLM calls)
   ```python
   # With Celery
   @app.task
   def parse_resume_async(file_path):
       return framework.parse_resume(file_path)
   ```

### Complexity Analysis

- **File Parsing**: O(n) where n = file size
- **Parser Lookup**: O(1) dictionary lookup
- **Field Extraction**: O(n) where n = text length
- **Total**: O(n) linear in file size

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY . .
CMD ["python", "app.py"]
```

### API Endpoint (FastAPI)

```python
from fastapi import FastAPI, UploadFile, HTTPException
from resume_parser import ResumeParserFramework, ResumeExtractor
from resume_parser.extractors import *

app = FastAPI()
framework = ResumeParserFramework(extractor)

@app.post("/api/v1/resumes/parse")
async def parse_resume(file: UploadFile):
    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        
        # Parse resume
        data = framework.parse_resume(temp_path)
        return data.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Monitoring

Key metrics to track:

- Parse success rate by file format
- Average extraction time per field
- LLM API latency and cost
- Field extraction success rates
- Error rates by exception type

## Contributing

### Code Style

- **Format**: black (line length 100)
- **Lint**: ruff
- **Type Check**: mypy
- **Tests**: pytest (>90% coverage required)

### Running Quality Checks

```bash
# Format code
black resume_parser/

# Lint
ruff check resume_parser/

# Type check
mypy resume_parser/

# Tests
pytest --cov=resume_parser --cov-report=term-missing
```

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions, please:

1. Check existing issues
2. Create a new issue with detailed information
3. Include sample files (if applicable)
4. Provide error logs and stack traces

## Acknowledgments

- **Google Gemini**: LLM-based skills extraction
- **spaCy**: NER for name extraction
- **pdfplumber & PyPDF2**: PDF parsing
- **python-docx**: Word document parsing
- **Pydantic**: Data validation

---

**Note**: This is a technical assignment demonstrating OOD principles, system design, and production-grade code organization. The framework is designed to be extended and scaled for real-world use cases.
