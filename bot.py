#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import asyncio
import os
import sys
from typing import List, Tuple

from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams  # type: ignore
from pipecat.frames.frames import Frame, TranscriptionFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.whisper.stt import Model, WhisperSTTService
from pipecat.transports.base_transport import BaseTransport
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams


from select_audio_device import AudioDevice, run_device_selector

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")


class TranscriptionLogger(FrameProcessor):
    """Logs transcription results from the pipeline."""
    def __init__(self, extra_logger: bool = False):
        super().__init__()
        self.extra_logger = extra_logger
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, TranscriptionFrame):
            logger.info(f"✓ Transcription: {frame.text}")

        await self.push_frame(frame, direction)


async def main(transport: BaseTransport, extra_processors: List[FrameProcessor] = []):
    stt = WhisperSTTService(device="cpu", model=Model.SMALL, no_speech_prob=0.2)

    logger_processor = TranscriptionLogger()

    # Pipeline: input (with VAD) -> STT -> logger
    # VAD detects when speech starts/stops and triggers STT processing
    pipeline = Pipeline([transport.input(), stt, logger_processor] + extra_processors)

    task = PipelineTask(pipeline)

    runner = PipelineRunner(handle_sigint=False if sys.platform == "win32" else True)

    await runner.run(task)


if __name__ == "__main__":
    test_audio_path = os.getenv("TEST_AUDIO_PATH")
    if test_audio_path:
        from file_transport import FileAudioTransport
        transport = FileAudioTransport(
            test_audio_path,
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(
                    stop_secs=0.2,
                    start_secs=0.1,
                    confidence=0.5,
                    min_volume=0.3,
                )
            )
        )
        asyncio.run(main(transport))
    else:
        res: Tuple[AudioDevice, AudioDevice, int] = asyncio.run(
            run_device_selector()  # runs the textual app that allows to select input device
        )

        transport = LocalAudioTransport(
            LocalAudioTransportParams(
                audio_in_enabled=True,
                audio_out_enabled=False,
                input_device_index=res[0].index,
                output_device_index=res[1].index,
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
        asyncio.run(main(transport))
