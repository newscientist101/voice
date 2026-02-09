#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import asyncio
import re
import sys
from typing import Tuple, List, Optional

from dotenv import load_dotenv
from pynput import keyboard
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams  # type: ignore
from pipecat.frames.frames import AudioRawFrame, DataFrame, Frame, TranscriptionFrame

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams

from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair, LLMUserAggregatorParams
from pipecat.processors.aggregators.llm_text_processor import LLMTextProcessor
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from pipecat.services.ollama.llm import OLLamaLLMService
from pipecat.services.piper.tts import PiperTTSService
from pipecat.services.whisper.stt import Model, WhisperSTTService

from pipecat.observers.loggers.llm_log_observer import LLMLogObserver
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from pipecat_tail.observer import TailObserver
from pipecat.utils.text.pattern_pair_aggregator import PatternPairAggregator, MatchAction, PatternMatch
from pattern_aggregator_fixed import FixedPatternPairAggregator
from pipecat.adapters.schemas.tools_schema import ToolsSchema

from select_audio_device import AudioDevice, run_device_selector
from tools import *
from environment import ollama_running, start_ollama_process

load_dotenv(override=True)

SYSTEM_PROMPT = "You are a helpful assistant. Your responses should be concise and to the point. "
INSTRUCTIONS = "Do not use the provided tools unless the users' request specifically asks for information that requires them. This does not need to be communicated to the user. Do not use emojis in your responses."

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
        )
    )

    async def fix_markdown(text: str, type: str) -> str:
        replacements = {
            "**": "",
            "*": "",
            "_": "",
            "~": "",
            "```": "",
            "`": "",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    async def fix_units(text: str, type: str) -> str:
        # Fix common unit formatting issues
        # e.g., "10 kg" -> "10 kilograms", "5 m/s" -> "5 meters per second"
        unit_mappings = {
            r"(\d+)\s?kg\b": r"\1 kilograms",
            r"(\d+)\s?g\b": r"\1 grams",
            r"(\d+)\s?m/s\b": r"\1 meters per second",
            r"(\d+)\s?km/h\b": r"\1 kilometers per hour",
            r"(\d+)\s?°C\b": r"\1 degrees Celsius",
            r"(\d+)\s?°F\b": r"\1 degrees Fahrenheit",
            r"(\d+)\s?cm\b": r"\1 centimeters",
            r"(\d+)\s?mm\b": r"\1 millimeters",
            r"(\d+)\s?m\b": r"\1 meters",
            r"(\d+)\s?km\b": r"\1 kilometers",
            r"(\d+)\s?lbs\b": r"\1 pounds",
            r"(\d+)\s?oz\b": r"\1 ounces",
            r"(\d+)\s?ft\b": r"\1 feet",
            r"(\d+)\s?in\b": r"\1 inches"
        }
        for pattern, replacement in unit_mappings.items():
            text = re.sub(pattern, replacement, text)
        return text

    stt = WhisperSTTService(device="cpu", model=Model.SMALL, no_speech_prob=0.2)

    """ 
    current good model choices
    ministral-3:8b-instruct-2512-q4_K_M
    qwen3-vl:8b-instruct-q4_K_M
    qwen3-vl:8b-thinking-q4_K_M # not sure about thinking 
    qwen3-vl:8b-instruct-q8_0 # if speed is more important than quality
    qwen3:8b # as backup
    """
    llm = OLLamaLLMService(model="qwen3-vl:8b-instruct-q4_K_M")


    tts = PiperTTSService(voice_id="en_US-ryan-high")

    tts.add_text_transformer(fix_markdown, "*")
    tts.add_text_transformer(fix_units,"*")

    pattern_aggregator = (
        FixedPatternPairAggregator()
            .add_pattern(type="Bold", start_pattern="**", end_pattern="**", action=MatchAction.KEEP)
            .add_pattern(type="Italic", start_pattern="*", end_pattern="*", action=MatchAction.KEEP)
            .add_pattern(type="Underline", start_pattern="_", end_pattern="_", action=MatchAction.KEEP)
            .add_pattern(type="Strikethrough", start_pattern="~", end_pattern="~", action=MatchAction.KEEP)
            .add_pattern(type="Code", start_pattern="```", end_pattern="```", action=MatchAction.KEEP)
            .add_pattern(type="InlineCode", start_pattern="`", end_pattern="`", action=MatchAction.KEEP)
    )
    
    llm_text_processor = LLMTextProcessor(text_aggregator=pattern_aggregator)

    toolList = [get_current_weather, search_hacker_news, wolframalpha_query, wikipedia_summary, hangup, get_news_headlines, convert_currency, get_ip_info]
    for tool in toolList:
        llm.register_direct_function(tool, cancel_on_interruption=False)
    tools = ToolsSchema(standard_tools=toolList) 

    context = LLMContext(
        messages=[{"role": "system", "content": SYSTEM_PROMPT + INSTRUCTIONS}],
        tools=tools
        )
    context_aggregators = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(
                    stop_secs=0.2,  # Reduced from default 0.8s for faster response
                    start_secs=0.1,  # Quick start detection
                    confidence=0.5,  # Lower threshold for more responsive detection
                    min_volume=0.3,
                )
            )
        ),
    )

    pause_resume = PauseResumeProcessor()

    # Start hotkey listener
    loop = asyncio.get_running_loop()
    listener = start_hotkey_listener(loop, pause_resume)

    # Pipeline: audio input -> pause_resume -> STT -> user aggregator -> LLM -> text processor -> TTS -> audio output -> assistant aggregator
    # VAD detects when speech starts/stops and triggers STT processing
    # The assistant aggregator is at the end to allow streaming text to reach TTS first
    pipeline = Pipeline([
        transport.input(),
        pause_resume,
        stt,
        context_aggregators.user(),
        llm,
        llm_text_processor,
        tts,
        transport.output(),
        context_aggregators.assistant(),
    ])

    task = PipelineTask(
        pipeline, 
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[LLMLogObserver(),TailObserver()])

    runner = PipelineRunner(handle_sigint=False if sys.platform == "win32" else True)

    try:
        await asyncio.gather(runner.run(task))
    finally:
        listener.stop()


if __name__ == "__main__":
    if not os.environ.get("TESTING_AUDIO_DEVICES"):
        res: Tuple[AudioDevice, AudioDevice, int] = asyncio.run(
            run_device_selector()  # runs the textual app that allows to select input device
        )
    else:
        res = (
            AudioDevice(index=5, name="Test Input Device",structVersion=2, maxInputChannels=2, maxOutputChannels=0, defaultLowInputLatency=0.01, defaultLowOutputLatency=0.0, defaultHighInputLatency=0.1, defaultHighOutputLatency=0.0, defaultSampleRate=44100.0, hostApi=0),
            AudioDevice(index=9, name="Test Output Device",structVersion=2, maxInputChannels=0, maxOutputChannels=2, defaultLowInputLatency=0.0, defaultLowOutputLatency=0.0, defaultHighInputLatency=0.0, defaultHighOutputLatency=0.0, defaultSampleRate=44100.0, hostApi=0),
            0,
        )
    if not ollama_running():
        print("Ollama process not running. Starting Ollama...")
        if not start_ollama_process():
            print("Failed to start Ollama process. Please ensure Ollama is installed and accessible.")
            sys.exit(1)
        else:
            print("Ollama process started successfully.")
    asyncio.run(main(res[0].index, res[1].index))
