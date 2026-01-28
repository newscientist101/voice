# Copilot Instructions for Voice-Controlled System

## Project Overview
A voice-controlled computer automation system using speech-to-speech LLM with tool calling. **Architecture**: Sandboxed WSL2 VM with GPU passthrough for secure LLM execution, separate from Windows host that handles audio I/O and inference.

- **Local inference**: Ollama + Qwen3-8B on Windows GPU (3-6s latency, default mode)
- **Smart mode**: Cloud AI via OpenRouter triggered by Next Track button (<2s latency)
- **Control**: Bluetooth media buttons (Play=push-to-talk, Next=smart mode toggle, Prev=halt)
- **Security model**: LLM has NO system access; all tool execution sandboxed in WSL2

## Key Architecture Components

### Audio & Device Layer (`src/device_selector.py`, `src/main.py`)
- **DeviceSelector**: Tkinter GUI for selecting input/output audio devices at startup
- Uses `sounddevice.query_devices()` to enumerate hardware
- Selected device indices passed to STTService for recording
- Device queries key pattern: `device['max_input_channels'] > 0` and `device['max_output_channels'] > 0`

### STT Pipeline (`src/stt_service.py`)
- **Thread-safe async bridge** between sync hotkey listener and pipecat async pipeline
- Uses `threading.Lock()` for `_is_running` state synchronization
- Creates new `PipelineRunner` per transcription cycle; cannot be reused after stopping
- Connects: LocalAudioInputTransport → OpenAISTTService → TranscriptionPrinter
- Important: Ollama served at `http://localhost:11434/v1` with API key "ollama"
- Custom `FrameProcessor` subclass handles TextFrame printing and EndFrame line breaks

### Hotkey Listener (`src/hotkey_listener.py`)
- Pynput keyboard listener for media keys: `keyboard.Key.media_play_pause`, `media_next`, `media_previous`
- Toggles STTService start/stop via `toggle_recording()`
- Placeholder functions `toggle_smart_mode()` and `halt_task()` ready for expansion
- Pattern: media key → service state toggle without blocking

### Environment Validation (`src/environment.py`)
- **Must execute before startup**: Validates Ollama process running + model availability
- Platform-aware: `ollama.exe` on Windows, `ollama` on Unix
- Uses `psutil.process_iter()` to check process, `ollama list` to verify model
- Exit codes: Process missing → exit 1; Model missing → suggest `ollama pull` then exit 1

## Critical Development Patterns

### Threading & Async Integration
- **Context**: Pynput keyboard listener is synchronous; STTService uses asyncio pipeline
- **Solution**: Dedicated daemon thread running `asyncio.new_event_loop()` in `_run_async_loop()`
- **Pattern**: Use `asyncio.run_coroutine_threadsafe()` to schedule coroutines from sync context
- **Lock usage**: All access to `_is_running` protected with `threading.Lock()` to prevent race conditions

### Pipeline Lifecycle
- **Limitation**: `PipelineRunner` is one-time-use; must create new instance per transcription session
- **After stop**: Always set `self._runner = None` to prevent reuse attempts
- **Frame flow**: FrameProcessor subclasses receive frames, process, then `await self.push_frame(frame)`
- **Signal end**: EndFrame marks transcription completion; used to flush output and reset state

### Dependency Expectations
- **pipecat-ai**: Provides Pipeline, LocalAudioInputTransport, OpenAISTTService, FrameProcessor
- **pynput**: Handles keyboard input; doesn't include media keys on all platforms—test on target device
- **sounddevice**: Query and record from audio devices; synchronous API
- **Ollama**: External service on localhost:11434; must be running before app starts

## Testing & Validation
- `tests/test_app.py`: Standalone hotkey tester—prints detected media key presses to GUI
- **Manual testing workflow**: Start Ollama → run `check_environment()` → launch GUI → select devices → validate hotkey presses
- **Common issues**: Missing Ollama process exits immediately; mismatched model name requires `ollama pull`

## File Organization
```
src/
  main.py              # Entry point: device selection → hotkey listener startup
  device_selector.py   # Tkinter GUI for audio device selection
  stt_service.py       # STT pipeline + async/sync bridge
  hotkey_listener.py   # Media key handler
  environment.py       # Ollama validation
tests/
  test_app.py          # Hotkey listener test harness
docs/plan/
  architecture.md      # WSL2 sandboxing design & component diagram
  overview.md          # System overview & operating modes
```

## When Adding Features
1. **Transcription toggle**: Modify `toggle_recording()` in `hotkey_listener.py`; logic is `is_running() ? stop() : start()`
2. **New LLM provider**: Replace `OpenAISTTService` in pipeline; honor `base_url` param for non-OpenAI endpoints
3. **Additional tool functions**: Expand `toggle_smart_mode()` and `halt_task()`; keep synchronous signatures
4. **Device persistence**: Extend DeviceSelector to save `selected_input_device` to config file before exit

## When Testing
1. All test scripts must be created under `tests/` directory
2. Use the existing virtual environment with `requirements.txt` when running tests

## Known Constraints
- **WSL2 integration**: Currently Windows-only implementation; tool execution sandboxed separately (see architecture.md for MCP layer)
- **Async/sync boundary**: All external APIs (keyboard, audio) are sync; pipecat is async—threading bridge required
- **Ollama requirement**: No fallback inference; system hard-stops if Ollama unavailable
- **Pynput platform support**: Media keys may not trigger on all Bluetooth devices—verify with test_app.py
