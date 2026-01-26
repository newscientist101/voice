## 1\. Model Selection

### RECOMMENDED: Local Pipeline with Ollama (Zero Cost)

Given your cost concerns, technical capabilities, and existing Ollama setup, a local 3-component pipeline is the best solution:

**Architecture: Faster-Whisper (ASR) + Ollama/Qwen3-8B (LLM) + Piper TTS**

#### Component 1: Faster-Whisper (Speech Recognition)

**Why Faster-Whisper:**

* 4x faster than standard Whisper with same accuracy
* Runs efficiently on your RTX 3070 Ti with 8GB VRAM
* Uses CTranslate2 optimization (quantization support)
* Real-time capable with batched processing
* Supports Voice Activity Detection (VAD)

**VRAM Usage:** ~1-2GB for medium model with 8-bit quantization
**Latency:** ~200-500ms for typical voice commands
**Quality:** Excellent transcription accuracy

#### Component 2: Ollama with Qwen3-8B (Language Model with Tool Calling)

**Why Ollama:**

* **You already have it installed with WSL2 experience!**
* Native tool calling support (critical requirement met!)
* Simple API (http://localhost:11434)
* Easy model management (`ollama pull qwen3:8b`)
* Can run on Windows OR WSL2 (your choice)
* Excellent Python library with tool support
* Can pass Python functions directly as tools

**Why Qwen3-8B:**

* 8B parameters fits perfectly in remaining 6GB VRAM with 4-bit quantization
* Best-in-class tool calling performance for local models
* Native support in Ollama
* Can switch between thinking mode and fast response mode

**VRAM Usage:** ~5-6GB with 4-bit quantization (Q4\_K\_M)
**Latency:**

* Simple queries: 2-5 seconds
* Complex reasoning: 10-30 seconds
  **Quality:** Rivals cloud models for tool calling accuracy

#### Component 3: Piper TTS (Text-to-Speech)

**Why Piper:**

* Fastest local TTS with natural-sounding voices
* Near-zero latency (<100ms) for typical responses
* Uses ONNX optimization, minimal resource usage
* Runs entirely on CPU, doesn't compete for GPU
* MIT license, fully open source
* Multiple voice options available

**CPU Usage:** Low (runs on separate thread)
**VRAM Usage:** 0GB (CPU only)
**Latency:** <100ms for sentence-level synthesis
**Quality:** Natural sounding, better than robotic alternatives

### Total Resource Usage (Local Pipeline)

* **VRAM:** ~7GB total (well within 8GB limit)
* **System RAM:** ~8GB
* **Monthly Cost:** $0 (electricity only)
* **Latency:**

  * Quick questions: 3-6 seconds total
  * Complex tasks: 15-35 seconds

* **Privacy:** 100% local, no data leaves your machine
* **Simplicity:** Uses tools you already know (Ollama!)
