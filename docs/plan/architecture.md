## 4\. System Architecture (WSL2 Sandboxed Design)

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     WINDOWS 11 HOST                                 │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │             User Interface Layer (Windows)                  │    │
│  │  ┌──────────────────┐    ┌──────────────────────────────┐   │    │
│  │  │ Bluetooth Device │────│ Media Button Handler         │   │    │
│  │  │ (Play/Next/Prev) │    │ (Python on Windows)          │   │    │
│  │  └──────────────────┘    └──────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                  │                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │          Audio Processing Layer (Windows)                   │    │
│  │  ┌──────────────────┐    ┌──────────────────────────────┐   │    │
│  │  │ Microphone Input │────│ Audio Buffer Manager         │   │    │
│  │  │ (sounddevice)    │    │ (16kHz mono, push-to-talk)   │   │    │
│  │  └──────────────────┘    └──────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                  │                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │     Speech Recognition Layer (Windows GPU)                  │    │
│  │  ┌──────────────────────────────────────────────────────┐   │    │
│  │  │    Faster-Whisper (CTranslate2 - CUDA)               │   │    │
│  │  │    • ~1-2GB VRAM usage                               │   │    │
│  │  │    • 200-500ms latency                               │   │    │
│  │  └──────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                  │                                  │
│                                  ▼ (transcribed text)               │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │      Language Model Layer (Windows GPU)                     │    │
│  │  ┌──────────────────────────────────────────────────────┐   │    │
│  │  │    Ollama Server - Qwen3-8B (CUDA)                   │   │    │
│  │  │    • Listens on: 0.0.0.0:8000                        │   │    │
│  │  │    • 4-bit quantization (Q4\\\_K\\\_M)               │   │    │
│  │  │    • Tool calling enabled                            │   │    │
│  │  │    • ~5-6GB VRAM usage                               │   │    │
│  │  │    • NO DIRECT SYSTEM ACCESS                         │   │    │
│  │  └──────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                  │                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │      Text-to-Speech Layer (Windows CPU)                     │    │
│  │  ┌──────────────────────────────────────────────────────┐   │    │
│  │  │    Piper TTS (ONNX Runtime)                          │   │    │
│  │  │    • <100ms latency                                  │   │    │
│  │  └──────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                  │                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │           Network Bridge (Windows)                          │    │
│  │  HTTP/WebSocket connection to WSL2: 172.x.x.x:5000          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                  │                                  │
└──────────────────────────────────┼──────────────────────────────────┘
                                   │ Network boundary
                    ╔══════════════╧════════════════╗
                    ║   ISOLATION LAYER - WSL2      ║
                    ╚══════════════╤════════════════╝
                                   │
┌──────────────────────────────────┼───────────────────────────────────┐
│                     WSL2 UBUNTU VM (SANDBOXED)                       │
│                                  │                                   │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │          MCP Client Layer (Ubuntu)                          │     │
│  │  Receives tool calls from Windows Ollama via HTTP           │     │
│  │  Executes in isolated environment                           │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                                  │                                   │
│                       ┌──────────┴──────────┐                        │
│                       ▼                     ▼                        │
│  ┌────────────────────────────┐  ┌──────────────────────────┐        │
│  │  Tool Execution Layer      │  │  Custom Dev Tools        │        │
│  │  ┌──────────────────────┐  │  │  ┌────────────────────┐  │        │
│  │  │ Linux Automation     │  │  │  │ File Creation      │  │        │
│  │  │ • xdotool (mouse)    │  │  │  │ Code Execution     │  │        │
│  │  │ • xdotool (keyboard) │  │  │  │ Terminal Commands  │  │        │
│  │  │ • wmctrl (windows)   │  │  │  │ Package Install    │  │        │
│  │  │ • scrot (screenshot) │  │  │  │ Git Operations     │  │        │
│  │  └──────────────────────┘  │  │  └────────────────────┘  │        │
│  └────────────────────────────┘  └──────────────────────────┘        │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │       Filesystem (Isolated - WSL2 ext4)                     │     │
│  │  /home/user/projects/  - LLM can create/modify files here   │     │
│  │  /home/user/workspace/ - Development workspace              │     │
│  │  /mnt/c/  - OPTIONAL shared folder (read-only recommended)  │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Data Flow (WSL2 Architecture)

1. **Voice Input (Windows):**

   * User presses Play button on Bluetooth device
   * Media button handler detects event via global hook
   * Audio recording starts (microphone → 16kHz buffer)

2. **Speech Recognition (Windows GPU):**

   * Audio buffer sent to Faster-Whisper on Windows GPU
   * VAD detects speech boundaries
   * Transcribed text returned (~200-500ms)

3. **Language Processing (Windows GPU):**

   * Text sent to Ollama server running on Windows
   * Qwen3-8B processes request with tool definitions
   * Model returns tool calls OR text response
   * **CRITICAL: Ollama model has NO direct access to Windows system**

4. **Tool Execution Request (Network to WSL2):**

   * Windows orchestrator sends tool call to WSL2 via HTTP
   * Request crosses network boundary (e.g., http://172.x.x.x:5000/execute)
   * WSL2 MCP server receives and validates request

5. **Sandboxed Execution (WSL2):**

   * Tool executed within WSL2 Ubuntu environment
   * File operations limited to WSL2 filesystem
   * System commands affect only the VM
   * Results returned to Windows

6. **Response Synthesis (Windows):**

   * Tool results sent back to Ollama for natural language response
   * Response text sent to Piper TTS (CPU)
   * Audio generated and played to user

7. **User Feedback (Windows):**

   * Audio streamed to speakers
   * User can interrupt with Play button

**Total Typical Latency:**

* Simple query: 3-6 seconds (ASR: 0.5s + LLM: 2-4s + TTS: 0.1s)
* With WSL2 tool use: 5-12 seconds (add 2-7s for network + execution)
* Complex reasoning: 15-35 seconds (LLM thinking mode)

### Security Boundaries

**What LLM CAN access:**

* ✅ WSL2 Linux filesystem
* ✅ Linux applications in WSL2
* ✅ Files in /home/user/projects/ (sandboxed)
* ✅ Network tools within WSL2
* ✅ Development tools (git, compilers, etc.) in WSL2

**What LLM CANNOT access:**

* ❌ Windows filesystem directly
* ❌ Windows applications
* ❌ Windows system settings
* ❌ Your personal files on C:\\
* ❌ Windows Registry
* ❌ Host GPU control (managed by Windows)
