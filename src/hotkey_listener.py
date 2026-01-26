import keyboard
import time

def toggle_recording():
    """
    Placeholder for toggling recording.
    """
    print("Toggling recording...")

def toggle_smart_mode():
    """
    Placeholder for toggling smart mode.
    """
    print("Toggling smart mode...")

def halt_task():
    """
    Placeholder for halting the current task.
    """
    print("Halting task...")

def start_hotkey_listener():
    """
    Registers the hotkeys and keeps the script running.
    """
    # Register hotkeys
    keyboard.add_hotkey('play/pause media', toggle_recording)
    keyboard.add_hotkey('next track', toggle_smart_mode)
    keyboard.add_hotkey('previous track', halt_task)

    print("Listening for media key presses... (requires admin privileges)")

    # Keep the script running
    while True:
        time.sleep(1)
