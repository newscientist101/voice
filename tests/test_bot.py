#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import pytest
import os
import asyncio
from bot import main, TranscriptionLogger
from file_transport import FileAudioTransport
from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams
from pipecat.frames.frames import TranscriptionFrame, Frame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection

class TranscriptionCollector(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.transcriptions = []

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, TranscriptionFrame):
            self.transcriptions.append(frame.text)
        await self.push_frame(frame, direction)

@pytest.mark.asyncio
async def test_transcription():
    # Set environment variable for bot.py's own logic (though we call main directly here)
    audio_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data/Recording_1.m4a"))

    transport = FileAudioTransport(
        audio_path,
        vad_analyzer=SileroVADAnalyzer(
            params=VADParams(
                stop_secs=0.2,
                start_secs=0.1,
                confidence=0.5,
                min_volume=0.1, # Lowered for test audio reliability
            )
        )
    )

    collector = TranscriptionCollector()

    # Run the bot's main function
    # We pass the collector as an extra processor to capture the output
    await main(transport, extra_processors=[collector])

    full_transcript = " ".join(collector.transcriptions).strip()
    print(f"Captured transcript: '{full_transcript}'")

    # The expected transcript is " This is a test. This is only a test."
    # We check for core text as agreed.
    assert "This is a test" in full_transcript
    assert "This is only a test" in full_transcript
