#!/usr/bin/env python3
"""Test Ollama OpenAI-compatible API with actual models."""

from openai import OpenAI

client = OpenAI(api_key='ollama', base_url='http://localhost:11434/v1')

# List available models
try:
    models = client.models.list()
    print("Available models via OpenAI API:")
    for model in models.data:
        print(f"  - {model.id}")
except Exception as e:
    print(f"Error listing models: {e}")
