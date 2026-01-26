from pynput import keyboard
from stt_service import STTService

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

def start_hotkey_listener(input_device_index, model_name):
    """
    Starts the hotkey listener.
    """
    stt_service = STTService(input_device_index, model_name)

    def toggle_recording():
        if stt_service.is_running():
            stt_service.stop()
        else:
            stt_service.start()

    def on_press(key):
        """
        Handles key press events.
        """
        if key == keyboard.Key.media_play_pause:
            toggle_recording()
        elif key == keyboard.Key.media_next:
            toggle_smart_mode()
        elif key == keyboard.Key.media_previous:
            halt_task()

    print("Listening for media key presses...")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
