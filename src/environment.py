import subprocess
import sys
import psutil
import platform

def check_ollama_process():
    """Checks if the ollama process is running."""
    process_name = "ollama.exe" if platform.system() == "Windows" else "ollama"
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            return True
    return False

def check_environment():
    """Checks the environment for required dependencies."""
    # Note: Ollama is no longer required since we're using local Whisper STT
    # The local Whisper service uses the system's installed whisper model
    print("Environment check: Using local Whisper for STT (no Ollama required)")

