#!/usr/bin/env python3
"""
Quick test to verify your Gemini API key is working.
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def test_api_key():
    print("=" * 60)
    print("Gemini API Key Test")
    print("=" * 60)
    
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("\n❌ No API key found!")
        print("\nPlease:")
        print("1. Get a key from: https://makersuite.google.com/app/apikey")
        print("2. Add it to your .env file")
        return False
    
    if api_key == "your_api_key_here":
        print("\n❌ API key not configured!")
        print("\nPlease replace 'your_api_key_here' in .env with your actual key")
        return False
    
    print(f"\n✓ API key found: {api_key[:20]}...")
    
    # Test the API
    try:
        import google.generativeai as genai
        
        print("\n✓ google-generativeai package installed")
        print("\nTesting API connection...")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Simple test prompt
        response = model.generate_content("Say 'API key works!' in 3 words")
        
        print("\n✓ API connection successful!")
        print(f"Response: {response.text}")
        print("\n" + "=" * 60)
        print("✓ Everything is working! You're ready to parse resumes.")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ API test failed: {e}")
        print("\nPossible issues:")
        print("- Invalid API key")
        print("- Network connectivity")
        print("- API quota exceeded")
        return False

if __name__ == "__main__":
    test_api_key()
