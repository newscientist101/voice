import subprocess
import psutil
import platform

def ollama_running():
    """Checks if the ollama process is running."""
    process_name = "ollama.exe" if platform.system() == "Windows" else "ollama"
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            return True
    return False

def start_ollama_process():
    """Starts the ollama process."""
    try:
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (OSError, FileNotFoundError):
        return False