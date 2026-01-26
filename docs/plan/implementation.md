## 5\. Implementation

### Phase 0: WSL2 Setup and GPU Passthrough (Week 1)

**Goal:** Configure WSL2 with CUDA support for secure sandboxing

**Tasks:**

1. Enable WSL2 on Windows 11

```powershell
   wsl --install Ubuntu-22.04
   wsl --set-default-version 2
   ```

2. Install NVIDIA CUDA drivers for WSL2 on Windows

   * Download from: https://developer.nvidia.com/cuda/wsl
   * **IMPORTANT:** Only install Windows driver, NOT Linux driver in WSL2

3. Verify GPU access from WSL2:

```bash
   nvidia-smi  # Should show your RTX 3070 Ti
   ```

4. Install CUDA toolkit in WSL2 (for compilation, not driver):

```bash
   wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86\\\_64/cuda-wsl-ubuntu.pin
   sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
   sudo apt-get update
   sudo apt-get -y install cuda-toolkit-12-2
   ```

5. Configure network access between Windows and WSL2

   * WSL2 gets automatic NAT networking
   * Find WSL2 IP: `ip addr show eth0`
   * Windows can access WSL2 via this IP

6. Set up shared folder (optional, for file transfer):

```bash
   # In WSL2, Windows C: drive is at /mnt/c/
   # Create safe shared folder
   sudo mkdir /mnt/c/WSL2-Safe-Share
   # Set WSL2 ownership
   sudo chown $USER:$USER /home/$USER/shared
   ```

**Deliverable:** WSL2 Ubuntu with GPU access, networked to Windows

### Phase 1: Windows Components (Week 1-2)

**Goal:** Voice input/output and Ollama setup on Windows

**Tasks:**

1. Set up Python environment on Windows (3.11+)

```powershell
   python -m venv voice\\\_assistant\\\_env
   .\\\\voice\\\_assistant\\\_env\\\\Scripts\\\\activate
   ```

2. Install Windows-side dependencies:

```bash
   pip install faster-whisper sounddevice numpy keyboard pyaudio ollama requests
   ```

3. Install and start Ollama on Windows:

```powershell
   # Download from https://ollama.com/download/windows
   # Or if already installed, just pull the model:
   ollama pull qwen3:8b
   
   # Start Ollama service (usually auto-starts)
   # Verify it's running:
   ollama list
   ```

4. Download and test Faster-Whisper:

```python
   from faster\\\_whisper import WhisperModel
   model = WhisperModel("medium", device="cuda", compute\\\_type="int8")
   # Test with sample audio
   ```

5. Test Ollama tool calling:

```python
   import ollama
   
   def test\\\_function():
       return "Tool calling works!"
   
   response = ollama.chat(
       model='qwen3:8b',
       messages=\\\[{'role': 'user', 'content': 'Test the tool'}],
       tools=\\\[test\\\_function]
   )
   print(response)
   ```

6. Download and configure Piper TTS:

   * Download Windows binary from GitHub
   * Download voice model (en\_US-lessac-medium.onnx)
   * Test synthesis

7. Implement media button detection:

```python
   import keyboard
   keyboard.add\\\_hotkey('play/pause media', on\\\_play\\\_press)
   ```

**Deliverable:** Working Windows audio pipeline with Ollama

**Expected Issues:**

* Media key detection may require admin privileges
* First Ollama model pull takes 5-10 minutes
* Whisper first run downloads models (~1.5GB)

### Phase 2: WSL2 Tool Execution Server (Week 2-3)

**Goal:** MCP-like server in WSL2 to execute tool calls safely

**Tasks:**

1. Set up Python in WSL2:

```bash
   sudo apt update
   sudo apt install python3-pip python3-venv
   python3 -m venv ~/tool\\\_server\\\_env
   source ~/tool\\\_server\\\_env/bin/activate
   ```

2. Install WSL2 automation tools:

```bash
   sudo apt install xdotool wmctrl scrot xclip
   pip install flask pyautogui
   ```

3. Create Flask server for tool execution:

```python
   from flask import Flask, request, jsonify
   import subprocess
   import json
   
   app = Flask(\\\_\\\_name\\\_\\\_)
   
   @app.route('/execute', methods=\\\['POST'])
   def execute\\\_tool():
       data = request.json
       tool\\\_name = data\\\['tool']
       args = data\\\['arguments']
       
       # Validate and execute
       result = execute\\\_safely(tool\\\_name, args)
       return jsonify(result)
   
   if \\\_\\\_name\\\_\\\_ == '\\\_\\\_main\\\_\\\_':
       app.run(host='0.0.0.0', port=5000)
   ```

4. Implement tool execution functions:

   * File creation (sandboxed to /home/user/projects/)
   * Terminal commands (with whitelist)
   * Code execution (in isolated environment)
   * Screenshot and OCR

5. Add security controls:

   * Path validation (prevent access outside safe dirs)
   * Command whitelist
   * Resource limits (timeout, memory)
   * Logging all actions

**Deliverable:** WSL2 Flask server accepting tool calls from Windows

### Phase 3: Windows-WSL2 Integration (Week 3-4)

**Goal:** Connect Windows LLM to WSL2 execution environment

**Tasks:**

1. Create Windows orchestrator that:

   * Receives text from Whisper
   * Sends to Ollama for processing
   * Extracts tool calls from Ollama response
   * Forwards tool calls to WSL2 via HTTP
   * Collects results and sends back to Ollama
   * Gets final response for TTS

2. Implement network communication:

```python
   import requests
   
   WSL2\\\_IP = "172.x.x.x"  # Get from 'wsl hostname -I'
   WSL2\\\_PORT = 5000
   
   def execute\\\_in\\\_wsl2(tool\\\_name, arguments):
       response = requests.post(
           f"http://{WSL2\\\_IP}:{WSL2\\\_PORT}/execute",
           json={"tool": tool\\\_name, "arguments": arguments},
           timeout=30
       )
       return response.json()
   ```

3. Define tool schemas for Ollama:

```python
   tools = \\\[
       {
           "type": "function",
           "function": {
               "name": "create\\\_file",
               "description": "Create a file in the WSL2 development environment",
               "parameters": {
                   "type": "object",
                   "properties": {
                       "filepath": {"type": "string"},
                       "content": {"type": "string"}
                   }
               }
           }
       },
       # ... more tools
   ]
   ```

4. Handle conversation flow with tool results
5. Add error handling for network failures
6. Implement retry logic

**Deliverable:** End-to-end voice → LLM → WSL2 execution → response

### Phase 4: Development Workflow Tools (Week 4-5)

**Goal:** Support "create an application" use case in WSL2

**Tasks:**

1. Expand WSL2 tool server with:

   * `create\\\_project(name, type)` - Scaffold projects
   * `write\\\_code(file, code)` - Write source files
   * `install\\\_package(package)` - pip/apt install
   * `run\\\_tests()` - Execute test suites
   * `git\\\_init()` - Initialize git repos
   * `execute\\\_command(cmd)` - Run shell commands (validated)

2. Create development templates:

   * Python Flask app
   * React app (via Node.js in WSL2)
   * FastAPI service
   * CLI tool

3. Implement code execution sandbox:

```bash
   # In WSL2
   docker run --rm -v $(pwd):/workspace python:3.11 python /workspace/script.py
   ```

4. Add file browsing and editing:

   * List directory contents
   * Read file contents
   * Modify existing files
   * Delete files (with confirmation)

5. Create multi-step workflow support:

   * LLM can chain tool calls
   * Maintain execution context
   * Handle errors gracefully

**Deliverable:** Can create and run applications via voice in WSL2

### Phase 5: Refinement \& Production Hardening (Week 5-6)

**Goal:** Polish, optimize, and secure the system

**Tasks:**

1. Optimize latency:

   * Batch audio processing
   * Preload models
   * Cache common responses
   * HTTP/2 for Windows-WSL2 communication

2. Improve security:

   * Rate limiting on WSL2 server
   * Authentication token between Windows/WSL2
   * Audit logging (all tool executions)
   * Resource quotas in WSL2

3. Add user experience features:

   * System tray icon on Windows
   * Visual feedback for recording
   * Progress indicators for long tasks
   * Error notifications

4. Create startup scripts:

```bash
   # start\\\_system.bat (Windows)
   wsl -d Ubuntu-22.04 -e ~/start\\\_wsl2\\\_server.sh
   python voice\\\_assistant.py
   ```

5. Write documentation:

   * Setup guide
   * Available commands
   * Troubleshooting
   * Architecture diagram

6. Implement backup and recovery:

   * WSL2 snapshot before risky operations
   * Command history
   * Undo functionality

**Deliverable:** Production-ready voice control system
