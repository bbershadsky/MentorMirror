#!/usr/bin/env python3
"""
Test API Keys Script
- Reads .env
- Validates GOOGLE_API_KEY with a test prompt
- Optionally validates OPENAI_API_KEY if present
"""
import os
import sys
from dotenv import dotenv_values

# For Google API test
import requests

# For OpenAI test
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

def test_google_api_key(api_key: str) -> bool:
    """
    Test the Google API key by making a simple request to the Google Gemini API.
    """
    # Using the Gemini 2.0 Flash model as requested from the rate limits screenshot
    model_name = "gemini-2.0-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [{"text": "Say hello in one sentence."}]
        }]
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if "candidates" in result and result["candidates"][0]["content"]["parts"][0]["text"]:
            text_response = result['candidates'][0]['content']['parts'][0]['text']
            print(f"✅ GOOGLE_API_KEY is valid. Test response: {text_response.strip()}")
            return True
        else:
            print(f"❌ GOOGLE_API_KEY test failed. Response format was unexpected: {result}")
            return False
            
    except Exception as e:
        print(f"❌ GOOGLE_API_KEY test failed: {e}")
        return False

def test_openai_api_key(api_key: str) -> bool:
    """
    Test the OpenAI API key by making a simple chat completion request using the v1.x client.
    """
    if not OPENAI_AVAILABLE:
        print("⚠️  openai package not installed. Skipping OpenAI API test.")
        return False
    
    try:
        # Use the new v1.x client
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say hello in one sentence."}
            ],
            max_tokens=20,
            temperature=0.2
        )
        if response and response.choices:
            text_response = response.choices[0].message.content
            print(f"✅ OPENAI_API_KEY is valid. Test response: {text_response.strip()}")
            return True
        else:
            print(f"❌ OPENAI_API_KEY test failed. No choices returned.")
            return False
    except Exception as e:
        print(f"❌ OPENAI_API_KEY test failed: {e}")
        return False

def main():
    env_path = ".env"
    if not os.path.exists(env_path):
        print(f"❌ {env_path} not found.")
        sys.exit(1)
    
    config = dotenv_values(env_path)
    google_api_key = config.get("GOOGLE_API_KEY")
    openai_api_key = config.get("OPENAI_API_KEY")
    
    print(f"🔍 Loaded {env_path}. Keys found:")
    print(f"   GOOGLE_API_KEY: {'SET' if google_api_key else 'NOT SET'}")
    print(f"   OPENAI_API_KEY: {'SET' if openai_api_key else 'NOT SET'}")
    
    if google_api_key:
        print("\n🧪 Testing GOOGLE_API_KEY...")
        test_google_api_key(google_api_key)
    else:
        print("⚠️  GOOGLE_API_KEY not set in .env.")
    
    if openai_api_key:
        print("\n🧪 Testing OPENAI_API_KEY...")
        test_openai_api_key(openai_api_key)
    else:
        print("ℹ️  OPENAI_API_KEY not set in .env. Skipping OpenAI test.")

if __name__ == "__main__":
    main() 