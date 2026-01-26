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

def check_asr_model(model_name: str):
    """Checks if the specified ASR model is available in Ollama."""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True)
        return model_name in result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_environment(model_name: str):
    """Checks the environment for Ollama and the ASR model."""
    if not check_ollama_process():
        print("Ollama is not running. Please start Ollama and try again.")
        sys.exit(1)

    if not check_asr_model(model_name):
        print(f"The '{model_name}' ASR model is not available in Ollama.")
        print("Please make sure the model is installed by running `ollama pull <model_name>`.")
        sys.exit(1)
