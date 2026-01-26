import sounddevice as sd
from device_selector import DeviceSelector
from hotkey_listener import start_hotkey_listener
from environment import check_environment

ASR_MODEL = "karanchopda333/whisper"

if __name__ == "__main__":
    # Step 1: Check the environment
    check_environment(ASR_MODEL)

    # Step 2: Show the device selector GUI
    selector = DeviceSelector()
    selector.mainloop()

    # Step 3: Get the selected devices after the GUI is closed
    selected_input = selector.selected_input_device
    selected_output = selector.selected_output_device

    # Step 4: If an input device was selected, start the hotkey listener
    if selected_input:
        print(f"Input device selected: {selected_input}")
        if selected_output:
            print(f"Output device selected: {selected_output}")
        else:
            print("No output device selected.")

        # Get the index of the selected input device
        devices = sd.query_devices()
        input_device_index = None
        for i, device in enumerate(devices):
            if device['name'] == selected_input and device['max_input_channels'] > 0:
                input_device_index = i
                break

        if input_device_index is not None:
            print("Starting the hotkey listener...")
            start_hotkey_listener(input_device_index, ASR_MODEL)
        else:
            print(f"Could not find input device: {selected_input}")

    else:
        print("No input device selected. Exiting.")
