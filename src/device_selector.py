import tkinter as tk
from tkinter import ttk
import sounddevice as sd

class DeviceSelector(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bluetooth Device Selector")
        self.geometry("400x250")
        self.selected_input_device = None
        self.selected_output_device = None

        # Input device selector
        self.input_label = ttk.Label(self, text="Select an audio input device:")
        self.input_label.pack(pady=5)

        self.input_devices = self.get_input_devices()
        self.input_device_var = tk.StringVar(self)

        if self.input_devices:
            self.input_device_var.set(self.input_devices[0])
            self.input_dropdown = ttk.OptionMenu(self, self.input_device_var, self.input_devices[0], *self.input_devices)
            self.input_dropdown.pack(pady=5)
        else:
            self.no_input_device_label = ttk.Label(self, text="No input devices found.")
            self.no_input_device_label.pack(pady=5)

        # Output device selector
        self.output_label = ttk.Label(self, text="Select an audio output device:")
        self.output_label.pack(pady=5)

        self.output_devices = self.get_output_devices()
        self.output_device_var = tk.StringVar(self)

        if self.output_devices:
            self.output_device_var.set(self.output_devices[0])
            self.output_dropdown = ttk.OptionMenu(self, self.output_device_var, self.output_devices[0], *self.output_devices)
            self.output_dropdown.pack(pady=5)
        else:
            self.no_output_device_label = ttk.Label(self, text="No output devices found.")
            self.no_output_device_label.pack(pady=5)

        self.select_button = ttk.Button(self, text="Select", command=self.select_devices)
        self.select_button.pack(pady=20)

    def get_input_devices(self):
        """
        Returns a list of audio input device names.
        """
        devices = sd.query_devices()
        input_devices = [device['name'] for device in devices if device['max_input_channels'] > 0]
        return input_devices

    def get_output_devices(self):
        """
        Returns a list of audio output device names.
        """
        devices = sd.query_devices()
        output_devices = [device['name'] for device in devices if device['max_output_channels'] > 0]
        return output_devices

    def select_devices(self):
        """
        Stores the selected input and output devices and closes the window.
        """
        if self.input_devices:
            self.selected_input_device = self.input_device_var.get()
        if self.output_devices:
            self.selected_output_device = self.output_device_var.get()
        self.destroy()
