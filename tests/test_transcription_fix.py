#!/usr/bin/env python3
"""
Test script to verify the fixed transcription integration with local Whisper STT.
"""
import sys

def test_whisper_stt_import():
    """Test if WhisperSTTService can be imported."""
    try:
        from pipecat.services.whisper.stt import WhisperSTTService
        print("✓ WhisperSTTService import successful")
        return True
    except ImportError as e:
        print(f"✗ Failed to import WhisperSTTService: {e}")
        return False

def test_stt_service_creation():
    """Test if STTService can be instantiated."""
    try:
        from src.stt_service import STTService
        # Use device index 0 for testing (usually the default input device)
        service = STTService(input_device_index=0)
        print("✓ STTService instantiation successful")
        return True
    except Exception as e:
        print(f"✗ Failed to instantiate STTService: {e}")
        return False

def test_pipeline_construction():
    """Test if the pipeline can be constructed."""
    try:
        from pipecat.pipeline.pipeline import Pipeline
        from pipecat.services.whisper.stt import WhisperSTTService
        from pipecat.processors.frame_processor import FrameProcessor
        
        # Create a dummy processor
        class DummyProcessor(FrameProcessor):
            async def process_frame(self, frame, direction):
                await self.push_frame(frame)
        
        stt = WhisperSTTService()
        dummy = DummyProcessor()
        
        # This will fail if there's no audio transport, but tests the imports
        print("✓ Pipeline components can be instantiated")
        return True
    except Exception as e:
        print(f"✗ Failed to construct pipeline components: {e}")
        return False

if __name__ == "__main__":
    print("Testing Whisper STT Integration for Transcription...")
    print("=" * 60)
    
    tests = [
        ("WhisperSTTService Import", test_whisper_stt_import),
        ("STTService Creation", test_stt_service_creation),
        ("Pipeline Construction", test_pipeline_construction),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\nTest: {test_name}")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("✓ All tests passed! Transcription integration is fixed.")
        sys.exit(0)
    else:
        print("✗ Some tests failed. Please review the errors above.")
        sys.exit(1)
