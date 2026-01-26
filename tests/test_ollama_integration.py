#!/usr/bin/env python3
"""
Test script to verify Ollama transcription integration.
"""
import sys
import requests
import subprocess

def test_ollama_connection():
    """Test if Ollama is accessible."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        print(f"✓ Ollama API is accessible")
        models = response.json().get("models", [])
        model_names = [m.get("name") for m in models]
        
        # Check for whisper model
        whisper_models = [m for m in model_names if "whisper" in m.lower()]
        if whisper_models:
            print(f"✓ Whisper model found: {whisper_models[0]}")
            return True, whisper_models[0]
        else:
            print(f"✗ No Whisper model found in Ollama")
            print(f"  Available models: {model_names[:5]}...")
            return False, None
    except Exception as e:
        print(f"✗ Ollama API not accessible: {e}")
        return False, None

def test_openai_compatible_api(model_name):
    """Test if the model is accessible via OpenAI-compatible API."""
    try:
        # Try a simple text completion to test the API
        response = requests.post(
            "http://localhost:11434/v1/chat/completions",
            json={
                "model": model_name,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10,
            },
            headers={"Authorization": "Bearer ollama"},
            timeout=10,
        )
        if response.status_code == 200:
            print(f"✓ OpenAI-compatible API works for model: {model_name}")
            return True
        else:
            print(f"✗ OpenAI-compatible API error: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ OpenAI-compatible API not accessible: {e}")
        return False

def check_ollama_process():
    """Check if Ollama process is running."""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✓ Ollama process is running")
            return True
        else:
            print(f"✗ Ollama process check failed")
            return False
    except Exception as e:
        print(f"✗ Could not verify Ollama process: {e}")
        return False

if __name__ == "__main__":
    print("Testing Ollama Integration for Transcription...")
    print("=" * 50)
    
    # Test 1: Ollama process
    if not check_ollama_process():
        print("\n✗ Ollama is not running. Please start Ollama before running this test.")
        sys.exit(1)
    
    # Test 2: API connection
    connected, model_name = test_ollama_connection()
    if not connected:
        print("\n✗ Could not connect to Ollama API.")
        sys.exit(1)
    
    # Test 3: OpenAI-compatible endpoint
    if not test_openai_compatible_api(model_name):
        print("\n✗ OpenAI-compatible API not working.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✓ All tests passed! Ollama is configured correctly.")
    print(f"  Model: {model_name}")
    print(f"  API endpoint: http://localhost:11434/v1")
