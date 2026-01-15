#!/usr/bin/env python3
"""
List available Gemini models for your API key.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def list_models():
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("Error: No API key found in .env")
            return
        
        genai.configure(api_key=api_key)
        
        print("=" * 60)
        print("Available Gemini Models")
        print("=" * 60)
        
        models = genai.list_models()
        
        print("\nModels that support generateContent:")
        print("-" * 60)
        
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f"\n✓ {model.name}")
                print(f"  Display name: {model.display_name}")
                if hasattr(model, 'description'):
                    print(f"  Description: {model.description}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()
