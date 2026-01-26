# Voice-Controlled Computer System - Implementation Plan

## System Overview

A voice-controlled computer automation system using speech-to-speech LLM with tool calling capabilities, controlled via Bluetooth media buttons (play for push-to-talk, next/previous for additional functions).

**Architecture:** Sandboxed WSL2 VM with GPU passthrough for secure task execution

**Target Hardware:**

* Windows 11 PC (Host)
* 16GB System RAM
* NVIDIA RTX 3070 Ti (8GB VRAM) - Shared between Windows and WSL2
* Bluetooth device with media control buttons
* WSL2 Ubuntu VM (isolated execution environment)

**Security Model:**

* LLM hosted on Windows (GPU access, no system control)
* All LLM tool execution happens inside WSL2 VM only
* Windows PC remains isolated from direct LLM access
* Files created stay in WSL2 filesystem (or mounted safe directories)

**Operating Modes:**

* **Local Mode (Default):** Ollama/Qwen3-8B on Windows GPU (free, private, 3-6s latency)
* **Smart Mode:** Cloud AI via OpenRouter (pay-as-you-go, <2s latency, activated by Next Track button)
