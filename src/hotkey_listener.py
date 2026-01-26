import asyncio
import threading
from pynput import keyboard

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
import pyaudio
from pipecat.pipeline.task import PipelineTask
from pipecat.frames.frames import Frame, TextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.transports.local.audio import (
    LocalAudioInputTransport,
    LocalAudioTransportParams,
)

runner = None

# We will run the asyncio event loop in a separate thread.
def run_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

loop = asyncio.new_event_loop()
thread = threading.Thread(target=run_async_loop, args=(loop,), daemon=True)
thread.start()

class TranscriptionPrinter(FrameProcessor):
    """A simple processor that prints transcriptions."""
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        if isinstance(frame, TextFrame):
            print(f"{frame.text}", end="", flush=True)
        await self.push_frame(frame)

async def start_transcription(input_device_index, model_name):
    global runner
    pa = pyaudio.PyAudio()
    params = LocalAudioTransportParams(
        input_device_index=input_device_index,
    )
    mic = LocalAudioInputTransport(pa, params)
    stt = OpenAISTTService(
        api_key="ollama",
        model=model_name,
        base_url="http://localhost:11434/v1",
    )
    printer = TranscriptionPrinter()

    pipeline = Pipeline([mic, stt, printer])
    task = PipelineTask(pipeline)
    runner = PipelineRunner()

    await runner.run(task)

async def stop_transcription():
    global runner
    if runner:
        await runner.stop_when_done()
        runner = None

def toggle_recording(input_device_index, model_name):
    global runner
    if runner:
        print("\nStopping transcription...")
        asyncio.run_coroutine_threadsafe(stop_transcription(), loop)
    else:
        print("Starting transcription...")
        asyncio.run_coroutine_threadsafe(start_transcription(input_device_index, model_name), loop)

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
    def on_press(key):
        """
        Handles key press events.
        """
        if key == keyboard.Key.media_play_pause:
            toggle_recording(input_device_index, model_name)
        elif key == keyboard.Key.media_next:
            toggle_smart_mode()
        elif key == keyboard.Key.media_previous:
            halt_task()

    print("Listening for media key presses...")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
