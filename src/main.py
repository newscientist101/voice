from device_selector import DeviceSelector
from hotkey_listener import start_hotkey_listener

if __name__ == "__main__":
    # Step 1: Show the device selector GUI
    selector = DeviceSelector()
    selector.mainloop()

    # Step 2: Get the selected devices after the GUI is closed
    selected_input = selector.selected_input_device
    selected_output = selector.selected_output_device

    # Step 3: If an input device was selected, start the hotkey listener
    if selected_input:
        print(f"Input device selected: {selected_input}")
        if selected_output:
            print(f"Output device selected: {selected_output}")
        else:
            print("No output device selected.")
        print("Starting the hotkey listener...")
        start_hotkey_listener()
    else:
        print("No input device selected. Exiting.")
