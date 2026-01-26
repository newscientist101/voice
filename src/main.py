from device_selector import DeviceSelector
from hotkey_listener import start_hotkey_listener

if __name__ == "__main__":
    # Step 1: Show the device selector GUI
    selector = DeviceSelector()
    selector.mainloop()

    # Step 2: Get the selected device after the GUI is closed
    selected_device = selector.selected_device

    # Step 3: If a device was selected, start the hotkey listener
    if selected_device:
        print(f"Device selected: {selected_device}")
        print("Starting the hotkey listener...")
        start_hotkey_listener()
    else:
        print("No device selected. Exiting.")
