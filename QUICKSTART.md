# Quick Start Guide for Reviewers

This guide helps you quickly test the Resume Parser Framework without any complex setup.

## Option 1: Web Demo (Easiest) 🌐

**Best for reviewers who want to see everything without CLI!**

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd policy_reporter
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download spaCy model
python -m spacy download en_core_web_sm

# 4. Start web demo
python web_demo.py
```

Open http://localhost:7860 in your browser!

**The web interface has 2 tabs:**

1. **"Parse Resume" tab**: Upload PDF/DOCX and see extraction (requires API key)
2. **"Run Tests" tab**: Click to run all 36 tests in the browser (NO API key needed!)

This lets you verify everything works without any command line!

## Option 2: Run Tests (Fastest) ⚡

**No API key needed! Tests use mocked LLM responses.**

```bash
# 1. Setup (same as above)
git clone <your-repo-url>
cd policy_reporter
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download spaCy model
python -m spacy download en_core_web_sm

# 4. Run tests
venv/bin/pytest -v
```

You should see: **36 passed, 3 warnings** ✅

## Option 3: CLI Demo 💻

**Requires Gemini API key (free tier available)**

```bash
# 1. Setup (same as above)

# 2. Get API key
# Go to: https://makersuite.google.com/app/apikey
# Create a free API key

# 3. Configure
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 4. Parse a resume
python demo.py path/to/resume.pdf
```

## What You'll See

### Name Extraction
Uses **regex patterns** and **spaCy NER** (ML) as fallback:
```
📝 Name: Oscar Chi
```

### Email Extraction
Uses **regex patterns**:
```
📧 Email: chi_oscar@hotmail.com
```

### Skills Extraction
Uses **Google Gemini LLM** for intelligent extraction:
```
💼 Skills (14):
   1. Python
   2. C++
   3. TypeScript
   4. JavaScript
   5. Django
   ...
```

## Architecture Highlights

### Design Patterns Used:
- **Strategy Pattern**: Pluggable extractors per field
- **Factory Pattern**: Automatic parser selection by file type
- **Facade Pattern**: Simple unified interface (ResumeParserFramework)
- **Dependency Injection**: Flexible configuration

### Key Files:
```
resume_parser/
├── parsers/
│   ├── base.py           # FileParser abstract class
│   ├── pdf_parser.py     # PDF implementation
│   └── word_parser.py    # Word implementation
├── extractors/
│   ├── base.py           # FieldExtractor abstract class
│   ├── name_extractor.py # Regex + NER
│   ├── email_extractor.py# Regex
│   └── skills_extractor.py# Gemini LLM
├── domain/
│   └── models.py         # ResumeData class
├── extractor.py          # ResumeExtractor coordinator
└── framework.py          # ResumeParserFramework main entry
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'pdfplumber'"
Make sure you're using the virtual environment's pytest:
```bash
venv/bin/pytest -v
```

### "Can't find model 'en_core_web_sm'"
Download the spaCy model:
```bash
venv/bin/python -m spacy download en_core_web_sm
```

### Gemini API quota exceeded
The free tier has limits. Wait a minute or get a new API key.

### Tests failing
Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Questions?

See the full [README.md](README.md) for comprehensive documentation including:
- Detailed architecture
- System design decisions
- Production deployment guide
- Performance considerations
- API documentation

---

**Estimated review time**: 15-30 minutes to test all features
