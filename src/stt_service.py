import asyncio
import threading
import pyaudio
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.frames.frames import Frame, TextFrame, EndFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.transports.local.audio import (
    LocalAudioInputTransport,
    LocalAudioTransportParams,
)

class STTService:
    def __init__(self, input_device_index, model_name):
        self._input_device_index = input_device_index
        self._model_name = model_name
        self._runner = None
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._thread.start()
        self._is_running = False
        self._lock = threading.Lock()

    def _run_async_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _start_transcription(self):
        pa = pyaudio.PyAudio()
        params = LocalAudioTransportParams(
            input_device_index=self._input_device_index,
        )
        mic = LocalAudioInputTransport(pa, params)
        stt = OpenAISTTService(
            api_key="ollama",
            model=self._model_name,
            base_url="http://localhost:11434/v1",
        )
        printer = self.TranscriptionPrinter()

        pipeline = Pipeline([mic, stt, printer])
        task = PipelineTask(pipeline)
        # We need to create a new runner for each transcription
        self._runner = PipelineRunner()

        await self._runner.run(task)
        # The runner cannot be reused once stopped, so we clear the reference
        self._runner = None

    async def _stop_transcription(self):
        if self._runner:
            await self._runner.stop_when_done()

    def start(self):
        with self._lock:
            if self._is_running:
                return
            self._is_running = True
            print("Starting transcription...")
            asyncio.run_coroutine_threadsafe(self._start_transcription(), self._loop)

    def stop(self):
        with self._lock:
            if not self._is_running:
                return
            self._is_running = False
            print("\nStopping transcription...")
            asyncio.run_coroutine_threadsafe(self._stop_transcription(), self._loop)

    def is_running(self):
        with self._lock:
            return self._is_running

    class TranscriptionPrinter(FrameProcessor):
        """A simple processor that prints transcriptions."""
        async def process_frame(self, frame: Frame, direction: FrameDirection):
            if isinstance(frame, TextFrame):
                print(f"{frame.text}", end="", flush=True)

            await self.push_frame(frame)

            if isinstance(frame, EndFrame):
                print()
