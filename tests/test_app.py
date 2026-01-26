import tkinter as tk
from tkinter import scrolledtext
import keyboard

class TestApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bluetooth Control Test")
        self.geometry("400x300")

        # Label for the last button pressed
        self.last_key_label = tk.Label(self, text="Last key pressed:", font=("Helvetica", 16))
        self.last_key_label.pack(pady=10)

        self.last_key_var = tk.StringVar()
        self.last_key_display = tk.Label(self, textvariable=self.last_key_var, font=("Helvetica", 24, "bold"))
        self.last_key_display.pack(pady=10)

        # Log of previous button presses
        self.log_label = tk.Label(self, text="Key press log:")
        self.log_label.pack(pady=5)

        self.log_text = scrolledtext.ScrolledText(self, width=40, height=10)
        self.log_text.pack(pady=10)

        # Start listening for hotkeys
        keyboard.on_press(self.on_press)

    def on_press(self, event):
        """
        Handles all key press events and updates the display.
        """
        self.update_display(event.name)

    def update_display(self, key_name):
        self.last_key_var.set(key_name)
        self.log_text.insert(tk.END, f"{key_name}\n")
        self.log_text.see(tk.END) # Scroll to the end

if __name__ == "__main__":
    app = TestApp()
    app.mainloop()
