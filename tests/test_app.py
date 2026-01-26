import tkinter as tk
from tkinter import scrolledtext
from pynput import keyboard

class TestApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bluetooth Control Test")
        self.geometry("400x300")

        # Label for the last button pressed
        self.last_key_label = tk.Label(self, text="Last button pressed:", font=("Helvetica", 16))
        self.last_key_label.pack(pady=10)

        self.last_key_var = tk.StringVar()
        self.last_key_display = tk.Label(self, textvariable=self.last_key_var, font=("Helvetica", 24, "bold"))
        self.last_key_display.pack(pady=10)

        # Log of previous button presses
        self.log_label = tk.Label(self, text="Button press log:")
        self.log_label.pack(pady=5)

        self.log_text = scrolledtext.ScrolledText(self, width=40, height=10)
        self.log_text.pack(pady=10)

        # Start listening for hotkeys
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def on_press(self, key):
        key_name = ""
        if key == keyboard.Key.media_play_pause:
            key_name = "Play/Pause"
            self.update_display(key_name)
        elif key == keyboard.Key.media_next:
            key_name = "Next Track"
            self.update_display(key_name)
        elif key == keyboard.Key.media_previous:
            key_name = "Previous Track"
            self.update_display(key_name)

    def update_display(self, key_name):
        self.last_key_var.set(key_name)
        self.log_text.insert(tk.END, f"{key_name}\n")
        self.log_text.see(tk.END) # Scroll to the end

if __name__ == "__main__":
    app = TestApp()
    app.mainloop()
