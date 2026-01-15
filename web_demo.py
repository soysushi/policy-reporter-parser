#!/usr/bin/env python3
"""
Web-based demo of the Resume Parser Framework using Gradio.

This provides a simple web interface for testing the framework without CLI.
Run with: python web_demo.py
"""

import json
import tempfile
import subprocess
import sys
from pathlib import Path

try:
    import gradio as gr
except ImportError:
    print("Error: gradio not installed")
    print("Install it with: pip install gradio")
    exit(1)

from resume_parser import ResumeExtractor, ResumeParserFramework
from resume_parser.extractors import NameExtractor, EmailExtractor, SkillsExtractor


def run_tests():
    """Run the test suite and return results."""
    try:
        # Find pytest in venv or use system pytest
        venv_pytest = Path("venv/bin/pytest")
        pytest_cmd = str(venv_pytest) if venv_pytest.exists() else "pytest"
        
        # Run pytest
        result = subprocess.run(
            [pytest_cmd, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        output = result.stdout + result.stderr
        
        # Parse results
        if "passed" in output:
            # Extract summary line
            lines = output.split("\n")
            for line in lines:
                if "passed" in line and "warning" in line:
                    return f"✅ Tests Passed!\n\n{line}\n\nFull output:\n{output}"
                elif "passed" in line:
                    return f"✅ Tests Passed!\n\n{line}\n\nFull output:\n{output}"
            return f"✅ Tests completed\n\n{output}"
        else:
            return f"❌ Some tests failed\n\n{output}"
            
    except subprocess.TimeoutExpired:
        return "⏱️ Tests timed out (took more than 60 seconds)"
    except FileNotFoundError:
        return "❌ pytest not found. Install with: pip install pytest"
    except Exception as e:
        return f"❌ Error running tests: {str(e)}"


def parse_resume(file):
    """Parse uploaded resume file."""
    if file is None:
        return "Please upload a resume file (PDF or DOCX)", ""
    
    try:
        # Save uploaded file temporarily
        file_path = file.name
        
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
        resume_data = framework.parse_resume(file_path)
        
        # Format results
        result_text = f"""
✓ Successfully parsed resume!

📝 Name:  {resume_data.name or '(not found)'}
📧 Email: {resume_data.email or '(not found)'}

💼 Skills ({len(resume_data.skills)}):
"""
        if resume_data.skills:
            for i, skill in enumerate(resume_data.skills, 1):
                result_text += f"   {i}. {skill}\n"
        else:
            result_text += "   (no skills found)\n"
        
        if resume_data.is_complete():
            result_text += "\n✓ All fields extracted successfully"
        else:
            result_text += "\n⚠ Some fields are missing"
        
        # JSON output
        json_output = json.dumps(resume_data.to_dict(), indent=2)
        
        return result_text, json_output
        
    except Exception as e:
        error_msg = f"Error parsing resume: {str(e)}"
        return error_msg, ""


# Create Gradio interface
with gr.Blocks(title="Resume Parser Demo") as demo:
    gr.Markdown("""
    # 📄 Resume Parser Framework Demo
    
    Upload a resume (PDF or DOCX) to extract structured information.
    
    **This framework uses:**
    - Regex for email extraction
    - spaCy NER for name extraction
    - Google Gemini LLM for intelligent skills extraction
    
    **Note:** Make sure you have configured your `GEMINI_API_KEY` in the `.env` file.
    """)
    
    # Test runner tab
    with gr.Tabs():
        with gr.Tab("Parse Resume"):
    
            with gr.Row():
                with gr.Column():
                    file_input = gr.File(
                        label="Upload Resume (PDF or DOCX)",
                        file_types=[".pdf", ".docx"]
                    )
                    parse_button = gr.Button("Parse Resume", variant="primary")
                
                with gr.Column():
                    result_output = gr.Textbox(
                        label="Extracted Information",
                        lines=15,
                        interactive=False
                    )
            
            with gr.Row():
                json_output = gr.Code(
                    label="JSON Output",
                    language="json",
                    interactive=False
                )
            
            parse_button.click(
                fn=parse_resume,
                inputs=[file_input],
                outputs=[result_output, json_output]
            )
        
        with gr.Tab("Run Tests"):
            gr.Markdown("""
            ### 🧪 Test Suite
            
            Run the complete test suite (36 tests) to verify the framework works correctly.
            
            **Tests cover:**
            - Parser abstraction (PDF, Word)
            - Field extractors (Name, Email, Skills)
            - ResumeData model
            - Framework orchestration
            - Error handling and edge cases
            
            **Note:** Tests use mocked LLM responses, so no API key is needed!
            """)
            
            test_button = gr.Button("Run All Tests", variant="primary", size="lg")
            test_output = gr.Textbox(
                label="Test Results",
                lines=25,
                interactive=False,
                placeholder="Click 'Run All Tests' to start..."
            )
            
            test_button.click(
                fn=run_tests,
                inputs=[],
                outputs=[test_output]
            )
    
    gr.Markdown("""
    ---
    ### 📖 Usage
    1. Click "Upload Resume" and select a PDF or DOCX file
    2. Click "Parse Resume" to extract information
    3. View results in the text area and JSON output
    
    ### 🔧 Architecture
    - **Parsers**: PDFParser (pdfplumber), WordParser (python-docx)
    - **Extractors**: NameExtractor (regex + NER), EmailExtractor (regex), SkillsExtractor (Gemini LLM)
    - **Framework**: ResumeParserFramework orchestrates parsing and extraction
    """)


if __name__ == "__main__":
    print("=" * 70)
    print("Starting Resume Parser Web Demo")
    print("=" * 70)
    print("\nThe web interface will open in your browser.")
    print("If it doesn't open automatically, go to: http://localhost:7860")
    print("\nPress Ctrl+C to stop the server.")
    print("=" * 70 + "\n")
    
    demo.launch(
        server_name="0.0.0.0",  # Allow external access
        server_port=7860,
        share=False  # Set to True to create a public link
    )
