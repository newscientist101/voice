import tkinter as tk
from tkinter import ttk
import sounddevice as sd

class DeviceSelector(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bluetooth Device Selector")
        self.geometry("400x150")
        self.selected_device = None

        self.label = ttk.Label(self, text="Select an audio input device:")
        self.label.pack(pady=10)

        self.devices = self.get_audio_devices()
        self.device_var = tk.StringVar(self)

        if self.devices:
            self.device_var.set(self.devices[0])
            self.dropdown = ttk.OptionMenu(self, self.device_var, self.devices[0], *self.devices)
            self.dropdown.pack(pady=10)
        else:
            self.no_device_label = ttk.Label(self, text="No input devices found.")
            self.no_device_label.pack(pady=10)

        self.select_button = ttk.Button(self, text="Select", command=self.select_device)
        self.select_button.pack(pady=10)

    def get_audio_devices(self):
        """
        Returns a list of audio input device names.
        """
        devices = sd.query_devices()
        input_devices = [device['name'] for device in devices if device['max_input_channels'] > 0]
        return input_devices

    def select_device(self):
        """
        Stores the selected device and closes the window.
        """
        self.selected_device = self.device_var.get()
        self.destroy()
