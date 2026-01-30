#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import asyncio
import av
from typing import Optional
from loguru import logger

from pipecat.frames.frames import InputAudioRawFrame, StartFrame, EndFrame, Frame
from pipecat.transports.base_input import BaseInputTransport
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.audio.vad.vad_analyzer import VADAnalyzer
from pipecat.processors.frame_processor import FrameDirection

class FileAudioTransportParams(TransportParams):
    audio_in_enabled: bool = True
    audio_out_enabled: bool = False
    audio_in_sample_rate: int = 16000
    audio_in_channels: int = 1

class FileAudioInputTransport(BaseInputTransport):
    def __init__(self, file_path: str, params: FileAudioTransportParams):
        super().__init__(params)
        self._file_path = file_path
        self._params = params
        self._push_task = None

    async def start(self, frame: StartFrame):
        await super().start(frame)
        self._push_task = asyncio.create_task(self._push_audio())
        await self.set_transport_ready(frame)

    async def _push_audio(self):
        try:
            container = av.open(self._file_path)
            stream = container.streams.audio[0]

            resampler = av.AudioResampler(
                format='s16',
                layout='mono',
                rate=16000,
            )

            # 20ms of audio at 16kHz, mono, 16-bit
            # 16000 * 0.02 = 320 samples
            # 320 * 2 bytes = 640 bytes
            samples_per_chunk = 320
            bytes_per_chunk = samples_per_chunk * 2

            audio_buffer = bytearray()

            for frame in container.decode(stream):
                packets = resampler.resample(frame)
                for packet in packets:
                    audio_buffer.extend(packet.to_ndarray().tobytes())

                    while len(audio_buffer) >= bytes_per_chunk:
                        chunk = bytes(audio_buffer[:bytes_per_chunk])
                        del audio_buffer[:bytes_per_chunk]

                        raw_frame = InputAudioRawFrame(
                            audio=chunk,
                            sample_rate=16000,
                            num_channels=1
                        )
                        await self.push_audio_frame(raw_frame)
                        # Minimal sleep to simulate real-time and not overwhelm
                        await asyncio.sleep(0.005)

            # Flush remaining buffer if any
            if len(audio_buffer) > 0:
                # Pad with zeros to match chunk size if needed, or just push
                raw_frame = InputAudioRawFrame(
                    audio=bytes(audio_buffer),
                    sample_rate=16000,
                    num_channels=1
                )
                await self.push_audio_frame(raw_frame)

            logger.info("File audio playback finished, pushing EndFrame")
            await self.push_frame(EndFrame())
        except Exception as e:
            logger.error(f"Error in FileAudioInputTransport: {e}")
            await self.push_frame(EndFrame())

class FileAudioTransport(BaseTransport):
    def __init__(self, file_path: str, vad_analyzer: Optional[VADAnalyzer] = None):
        super().__init__()
        self._file_path = file_path
        self._params = FileAudioTransportParams(vad_analyzer=vad_analyzer)
        self._input = None

    def input(self) -> FileAudioInputTransport:
        if not self._input:
            self._input = FileAudioInputTransport(self._file_path, self._params)
        return self._input

    def output(self):
        # Not implemented for this helper
        raise NotImplementedError("Output not supported in FileAudioTransport")
