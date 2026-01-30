#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import asyncio
import sys
from typing import Tuple

from dotenv import load_dotenv
from pynput import keyboard
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams  # type: ignore
from pipecat.frames.frames import AudioRawFrame, DataFrame, Frame, TranscriptionFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.observers.loggers.llm_log_observer import LLMLogObserver
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.ollama.llm import OLLamaLLMService
from pipecat.services.piper.tts import PiperTTSService
from pipecat.services.whisper.stt import Model, WhisperSTTService
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams


from select_audio_device import AudioDevice, run_device_selector

load_dotenv(override=True)

SYSTEM_PROMPT = ""
INSTRUCTIONS = ""

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

class PauseResumeProcessor(FrameProcessor):
    """Processor that can be toggled to pause/resume the pipeline by dropping data frames."""
    def __init__(self):
        super().__init__()
        self._paused = False

    async def set_paused(self, paused: bool):
        self._paused = paused
        if self._paused:
            logger.info("Pipeline Paused")
        else:
            logger.info("Pipeline Resumed")

    async def toggle_paused(self):
        await self.set_paused(not self._paused)

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if self._paused and (isinstance(frame, DataFrame) or isinstance(frame, AudioRawFrame)):
            return
        await self.push_frame(frame, direction)


def start_hotkey_listener(loop: asyncio.AbstractEventLoop, processor: PauseResumeProcessor):
    def on_press(key):
        try:
            if key == keyboard.Key.media_play_pause:
                asyncio.run_coroutine_threadsafe(processor.toggle_paused(), loop)
        except Exception as e:
            logger.error(f"Error in hotkey listener: {e}")

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    return listener


async def main(input_device: int, output_device: int):
    transport = LocalAudioTransport(
        LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            input_device_index=input_device,
            output_device_index=output_device,
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(
                    stop_secs=0.2,  # Reduced from default 0.8s for faster response
                    start_secs=0.1,  # Quick start detection
                    confidence=0.5,  # Lower threshold for more responsive detection
                    min_volume=0.3,
                )
            ),
        )
    )

    stt = WhisperSTTService(device="cpu", model=Model.SMALL, no_speech_prob=0.2)

    llm = OLLamaLLMService(model="qwen3:8b")

    tts = PiperTTSService(voice_id="en_US-ryan-high")

    context = LLMContext([{"role": "system", "content": SYSTEM_PROMPT + INSTRUCTIONS}])
    context_aggregators = LLMContextAggregatorPair(context)

    pause_resume = PauseResumeProcessor()

    # Start hotkey listener
    loop = asyncio.get_running_loop()
    listener = start_hotkey_listener(loop, pause_resume)

    # Pipeline: audio input -> pause_resume -> STT -> user aggregator -> LLM -> assistant aggregator -> TTS -> audio output
    # VAD detects when speech starts/stops and triggers STT processing
    pipeline = Pipeline([
        transport.input(),
        pause_resume,
        stt,
        context_aggregators.user(),
        llm,
        context_aggregators.assistant(),
        tts,
        transport.output(),
    ])

    task = PipelineTask(pipeline, observers=[LLMLogObserver()])

    runner = PipelineRunner(handle_sigint=False if sys.platform == "win32" else True)

    try:
        await asyncio.gather(runner.run(task))
    finally:
        listener.stop()


if __name__ == "__main__":
    res: Tuple[AudioDevice, AudioDevice, int] = asyncio.run(
        run_device_selector()  # runs the textual app that allows to select input device
    )

    asyncio.run(main(res[0].index, res[1].index))
