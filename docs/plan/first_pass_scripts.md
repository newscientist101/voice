

## 6\. First Draft

### 6.1 Faster-Whisper Setup

```python
from faster\\\\\\\_whisper import WhisperModel
import numpy as np

class SpeechRecognizer:
    def \\\_\\\_init\\\_\\\_(self):
        # Use medium model with 8-bit quantization on Windows GPU
        # VRAM usage: ~1-2GB
        self.model = WhisperModel(
            "medium",
            device="cuda",
            compute\\\_type="int8", # 8-bit quantization for speed
            device\\\_index=0
        )
        
        # Enable VAD for better segmentation
        self.vad\\\_filter = True
    
    def transcribe(self, audio\\\_data):
        """
        Transcribe audio to text
        audio\\\_data: numpy array, 16kHz sample rate
        """
        segments, info = self.model.transcribe(
            audio\\\_data,
            vad\\\_filter=self.vad\\\_filter,
            vad\\\_parameters={
                "threshold": 0.5,
                "min\\\_speech\\\_duration\\\_ms": 250,
                "min\\\_silence\\\_duration\\\_ms": 100
            },
            language="en",  # or None for auto-detect
            beam\\\_size=5
        )
        
        # Combine segments
        transcription = " ".join(\\\[segment.text for segment in segments])
        return transcription.strip()
```

### 6.2 Windows: OpenRouter Client for Smart Mode

```python
# windows\\\_components/openrouter\\\_client.py
from openai import OpenAI
import os

class OpenRouterClient:
    """
    Cloud LLM client using OpenRouter for Smart Mode
    Pay-as-you-go, no monthly fees
    """
    def \\\_\\\_init\\\_\\\_(self, wsl2\\\_ip, model="google/gemini-2.5-flash-exp"):
        self.model = model
        self.wsl2\\\_ip = wsl2\\\_ip
        self.wsl2\\\_port = 5000
        
        # OpenRouter uses OpenAI-compatible API
        self.client = OpenAI(
            base\\\_url="https://openrouter.ai/api/v1",
            api\\\_key=os.environ.get("OPENROUTER\\\_API\\\_KEY"),
        )
        
        # Same tool definitions as Ollama
        self.tools = \\\[
            {
                "type": "function",
                "function": {
                    "name": "create\\\_file",
                    "description": "Create a new file in the WSL2 development environment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Path relative to /home/user/projects/"
                            },
                            "content": {
                                "type": "string",
                                "description": "File content"
                            }
                        },
                        "required": \\\["filepath", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute\\\_command",
                    "description": "Execute a shell command in WSL2 Ubuntu",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute"
                            }
                        },
                        "required": \\\["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read\\\_file",
                    "description": "Read contents of a file in WSL2",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Path to file"
                            }
                        },
                        "required": \\\["filepath"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "install\\\_package",
                    "description": "Install a Python package via pip in WSL2",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "package": {
                                "type": "string",
                                "description": "Package name"
                            }
                        },
                        "required": \\\["package"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list\\\_directory",
                    "description": "List contents of a directory in WSL2",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path"
                            }
                        }
                    }
                }
            }
        ]
    
    def process\\\_query(self, user\\\_text, conversation\\\_history=\\\[]):
        """Send query to OpenRouter, handle tool calls via WSL2"""
        messages = conversation\\\_history + \\\[
            {"role": "user", "content": user\\\_text}
        ]
        
        # Call OpenRouter (OpenAI-compatible API)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
            tool\\\_choice="auto",
            temperature=0.7,
            max\\\_tokens=2000
        )
        
        return response.choices\\\[0].message
    
    def execute\\\_tool\\\_in\\\_wsl2(self, tool\\\_name, arguments):
        """Forward tool execution to WSL2 server (same as Ollama)"""
        import requests
        
        try:
            response = requests.post(
                f"http://{self.wsl2\\\_ip}:{self.wsl2\\\_port}/execute",
                json={
                    "tool": tool\\\_name,
                    "arguments": arguments
                },
                timeout=60
            )
            
            if response.status\\\_code == 200:
                return response.json()
            else:
                return {
                    "error": f"WSL2 server error: {response.status\\\_code}",
                    "details": response.text
                }
        except Exception as e:
            return {
                "error": f"Failed to connect to WSL2: {str(e)}"
            }

# Available OpenRouter Models for Smart Mode:
SMART\\\_MODE\\\_MODELS = {
    "fast": "google/gemini-2.5-flash-exp",          # Fastest, cheapest (~$0.0008/query)
    "smart": "anthropic/claude-3.5-sonnet",         # Best reasoning (~$0.018/query)
    "code": "deepseek/deepseek-chat",               # Best for coding (~$0.0014/query)
    "balanced": "openai/gpt-4o-mini",               # Good all-rounder (~$0.0008/query)
}
```

### 6.3 Windows: Unified LLM Client (Supports Both Modes)

```python
# windows\\\_components/unified\\\_llm\\\_client.py
from windows\\\_components.llm\\\_client import OllamaLLMClient
from windows\\\_components.openrouter\\\_client import OpenRouterClient, SMART\\\_MODE\\\_MODELS
import json

class UnifiedLLMClient:
    """
    Unified client that can switch between Local (Ollama) and Smart (OpenRouter) modes
    """
    def \\\_\\\_init\\\_\\\_(self, wsl2\\\_ip):
        self.wsl2\\\_ip = wsl2\\\_ip
        
        # Initialize both clients
        self.ollama\\\_client = OllamaLLMClient(wsl2\\\_ip, model="qwen3:8b")
        self.openrouter\\\_client = OpenRouterClient(wsl2\\\_ip, model=SMART\\\_MODE\\\_MODELS\\\["fast"])
        
        # Default to local mode
        self.smart\\\_mode = False
        self.current\\\_client = self.ollama\\\_client
    
    def toggle\\\_smart\\\_mode(self):
        """Toggle between local and smart mode"""
        self.smart\\\_mode = not self.smart\\\_mode
        
        if self.smart\\\_mode:
            self.current\\\_client = self.openrouter\\\_client
            return "⚡ Smart mode activated"
        else:
            self.current\\\_client = self.ollama\\\_client
            return "🤖 Local mode"
    
    def set\\\_smart\\\_model(self, model\\\_key):
        """Change the smart mode model (fast/smart/code/balanced)"""
        if model\\\_key in SMART\\\_MODE\\\_MODELS:
            self.openrouter\\\_client.model = SMART\\\_MODE\\\_MODELS\\\[model\\\_key]
            return f"Smart mode model set to: {model\\\_key}"
        else:
            return f"Unknown model: {model\\\_key}"
    
    def process\\\_query(self, user\\\_text, conversation\\\_history=\\\[]):
        """Process query using current mode (local or smart)"""
        return self.current\\\_client.process\\\_query(user\\\_text, conversation\\\_history)
    
    def execute\\\_tool\\\_in\\\_wsl2(self, tool\\\_name, arguments):
        """Execute tool in WSL2 (same for both modes)"""
        return self.current\\\_client.execute\\\_tool\\\_in\\\_wsl2(tool\\\_name, arguments)
    
    def get\\\_current\\\_mode(self):
        """Get current mode as string"""
        if self.smart\\\_mode:
            return f"⚡ Smart Mode ({self.openrouter\\\_client.model})"
        else:
            return f"🤖 Local Mode ({self.ollama\\\_client.model})"
```

```python
# windows\\\_components/llm\\\_client.py
import ollama
import json

class OllamaLLMClient:
    def \\\_\\\_init\\\_\\\_(self, wsl2\\\_ip, model="qwen3:8b"):
        self.model = model
        self.wsl2\\\_ip = wsl2\\\_ip
        self.wsl2\\\_port = 5000
        
        # Ensure model is pulled
        try:
            ollama.show(model)
        except:
            print(f"Pulling {model}... (this may take a few minutes)")
            ollama.pull(model)
        
        # Tool definitions - execution happens in WSL2
        # Ollama supports passing Python functions directly!
        self.tools = \\\[
            {
                "type": "function",
                "function": {
                    "name": "create\\\_file",
                    "description": "Create a new file in the WSL2 development environment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Path relative to /home/user/projects/"
                            },
                            "content": {
                                "type": "string",
                                "description": "File content"
                            }
                        },
                        "required": \\\["filepath", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute\\\_command",
                    "description": "Execute a shell command in WSL2 Ubuntu",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute"
                            }
                        },
                        "required": \\\["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read\\\_file",
                    "description": "Read contents of a file in WSL2",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Path to file"
                            }
                        },
                        "required": \\\["filepath"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "install\\\_package",
                    "description": "Install a Python package via pip in WSL2",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "package": {
                                "type": "string",
                                "description": "Package name"
                            }
                        },
                        "required": \\\["package"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list\\\_directory",
                    "description": "List contents of a directory in WSL2",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path (defaults to projects/)"
                            }
                        }
                    }
                }
            }
        ]
    
    def process\\\_query(self, user\\\_text, conversation\\\_history=\\\[]):
        """Send query to Ollama, handle tool calls via WSL2"""
        messages = conversation\\\_history + \\\[
            {"role": "user", "content": user\\\_text}
        ]
        
        # Call Ollama with tools
        response = ollama.chat(
            model=self.model,
            messages=messages,
            tools=self.tools
        )
        
        return response\\\['message']
    
    def execute\\\_tool\\\_in\\\_wsl2(self, tool\\\_name, arguments):
        """Forward tool execution to WSL2 server"""
        import requests
        
        try:
            response = requests.post(
                f"http://{self.wsl2\\\_ip}:{self.wsl2\\\_port}/execute",
                json={
                    "tool": tool\\\_name,
                    "arguments": arguments
                },
                timeout=60  # Allow up to 60s for execution
            )
            
            if response.status\\\_code == 200:
                return response.json()
            else:
                return {
                    "error": f"WSL2 server error: {response.status\\\_code}",
                    "details": response.text
                }
        except Exception as e:
            return {
                "error": f"Failed to connect to WSL2: {str(e)}"
            }

# Example usage:
# client = OllamaLLMClient(wsl2\\\_ip="172.x.x.x")
# response = client.process\\\_query("Create a Python hello world script")
# if response.get('tool\\\_calls'):
#     for call in response\\\['tool\\\_calls']:
#         result = client.execute\\\_tool\\\_in\\\_wsl2(
#             call\\\['function']\\\['name'],
#             call\\\['function']\\\['arguments']
#         )
```

### 6.4 Windows: Piper TTS

```python
# windows\\\_components/text\\\_to\\\_speech.py
import subprocess
from pathlib import Path

class TextToSpeech:
    def \\\_\\\_init\\\_\\\_(self):
        # Assumes piper.exe and model are in models/
        self.piper\\\_exe = Path("models/piper.exe")
        self.model\\\_path = Path("models/en\\\_US-lessac-medium.onnx")
        
    def speak(self, text):
        """Convert text to speech and play immediately"""
        # Use piper with direct audio output
        process = subprocess.Popen(
            \\\[
                str(self.piper\\\_exe),
                "--model", str(self.model\\\_path),
                "--output\\\_raw"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        audio\\\_data, \\\_ = process.communicate(input=text.encode())
        
        # Play audio
        self.\\\_play\\\_audio(audio\\\_data)
    
    def \\\_play\\\_audio(self, raw\\\_audio):
        """Play raw audio using sounddevice"""
        import sounddevice as sd
        import numpy as np
        
        audio\\\_array = np.frombuffer(raw\\\_audio, dtype=np.int16)
        sd.play(audio\\\_array, samplerate=22050)
        sd.wait()
```

### 6.5 WSL2: Tool Execution Server

```python
# wsl2\\\_components/tool\\\_server.py (run in WSL2)
from flask import Flask, request, jsonify
import subprocess
import os
from pathlib import Path
import json

app = Flask(\\\_\\\_name\\\_\\\_)

# Security: Define safe base directory
SAFE\\\_BASE = Path.home() / "projects"
SAFE\\\_BASE.mkdir(exist\\\_ok=True)

def is\\\_safe\\\_path(filepath):
    """Ensure path is within safe directory"""
    try:
        resolved = (SAFE\\\_BASE / filepath).resolve()
        return str(resolved).startswith(str(SAFE\\\_BASE.resolve()))
    except:
        return False

@app.route('/execute', methods=\\\['POST'])
def execute\\\_tool():
    """Execute tool calls from Windows LLM"""
    data = request.json
    tool\\\_name = data.get('tool')
    arguments = data.get('arguments', {})
    
    try:
        if tool\\\_name == "create\\\_file":
            return jsonify(create\\\_file(\\\*\\\*arguments))
        elif tool\\\_name == "read\\\_file":
            return jsonify(read\\\_file(\\\*\\\*arguments))
        elif tool\\\_name == "execute\\\_command":
            return jsonify(execute\\\_command(\\\*\\\*arguments))
        elif tool\\\_name == "install\\\_package":
            return jsonify(install\\\_package(\\\*\\\*arguments))
        else:
            return jsonify({"error": f"Unknown tool: {tool\\\_name}"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def create\\\_file(filepath, content):
    """Create file in safe directory"""
    if not is\\\_safe\\\_path(filepath):
        return {"error": "Path outside safe directory"}
    
    full\\\_path = SAFE\\\_BASE / filepath
    full\\\_path.parent.mkdir(parents=True, exist\\\_ok=True)
    
    full\\\_path.write\\\_text(content, encoding='utf-8')
    
    return {
        "status": "success",
        "message": f"Created {full\\\_path}",
        "path": str(full\\\_path)
    }

def read\\\_file(filepath):
    """Read file from safe directory"""
    if not is\\\_safe\\\_path(filepath):
        return {"error": "Path outside safe directory"}
    
    full\\\_path = SAFE\\\_BASE / filepath
    
    if not full\\\_path.exists():
        return {"error": "File not found"}
    
    content = full\\\_path.read\\\_text(encoding='utf-8')
    
    return {
        "status": "success",
        "content": content,
        "path": str(full\\\_path)
    }

# Whitelist of safe commands
COMMAND\\\_WHITELIST = \\\[
    "ls", "cat", "pwd", "echo", "python3", "pip", "git",
    "mkdir", "touch", "grep", "find", "wc", "head", "tail"
]

def execute\\\_command(command):
    """Execute whitelisted shell command"""
    # Parse command
    cmd\\\_parts = command.split()
    base\\\_cmd = cmd\\\_parts\\\[0]
    
    if base\\\_cmd not in COMMAND\\\_WHITELIST:
        return {"error": f"Command '{base\\\_cmd}' not whitelisted"}
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=SAFE\\\_BASE,
            capture\\\_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out"}

def install\\\_package(package):
    """Install Python package via pip"""
    try:
        result = subprocess.run(
            \\\["pip3", "install", package],
            capture\\\_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "status": "success" if result.returncode == 0 else "failed",
            "output": result.stdout,
            "errors": result.stderr
        }
    except Exception as e:
        return {"error": str(e)}

if \\\_\\\_name\\\_\\\_ == '\\\_\\\_main\\\_\\\_':
    print(f"Tool server running. Safe directory: {SAFE\\\_BASE}")
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### 6.6 Windows: Main Orchestrator (with Smart Mode Support)

```python
# voice\\\_assistant.py (run on Windows)
import sounddevice as sd
import numpy as np
import keyboard
import subprocess
import json
from threading import Thread
from windows\\\_components.speech\\\_recognizer import SpeechRecognizer
from windows\\\_components.unified\\\_llm\\\_client import UnifiedLLMClient
from windows\\\_components.text\\\_to\\\_speech import TextToSpeech

class VoiceAssistant:
    def \\\_\\\_init\\\_\\\_(self):
        # Get WSL2 IP address
        self.wsl2\\\_ip = self.\\\_get\\\_wsl2\\\_ip()
        
        self.asr = SpeechRecognizer()
        self.llm = UnifiedLLMClient(self.wsl2\\\_ip)  # Supports both modes
        self.tts = TextToSpeech()
        
        self.recording = False
        self.audio\\\_buffer = \\\[]
        self.sample\\\_rate = 16000
        self.conversation\\\_history = \\\[]
    
    def \\\_get\\\_wsl2\\\_ip(self):
        """Get WSL2 IP address"""
        result = subprocess.run(
            \\\["wsl", "hostname", "-I"],
            capture\\\_output=True,
            text=True
        )
        ip = result.stdout.strip().split()\\\[0]
        print(f"WSL2 IP: {ip}")
        return ip
    
    def audio\\\_callback(self, indata, frames, time, status):
        if self.recording:
            self.audio\\\_buffer.append(indata.copy())
    
    def start\\\_recording(self):
        self.recording = True
        self.audio\\\_buffer = \\\[]
        mode = "⚡ SMART" if self.llm.smart\\\_mode else "🤖 LOCAL"
        print(f"🎤 Listening... \\\[{mode}]")
    
    def stop\\\_recording(self):
        self.recording = False
        print("⏸️  Processing...")
        
        if not self.audio\\\_buffer:
            return
        
        audio\\\_data = np.concatenate(self.audio\\\_buffer)
        Thread(target=self.process\\\_audio, args=(audio\\\_data,)).start()
    
    def toggle\\\_smart\\\_mode(self):
        """Toggle between local and smart mode"""
        message = self.llm.toggle\\\_smart\\\_mode()
        print(f"\\\\n🔄 {message}")
        self.tts.speak(message)
    
    def process\\\_audio(self, audio\\\_data):
        """Full processing pipeline with mode switching support"""
        try:
            mode\\\_indicator = "⚡" if self.llm.smart\\\_mode else "🤖"
            
            # 1. Speech Recognition (Windows GPU)
            print(f"{mode\\\_indicator} Transcribing...")
            text = self.asr.transcribe(audio\\\_data)
            print(f"You: {text}")
            
            if not text.strip():
                self.tts.speak("I didn't catch that.")
                return
            
            # 2. LLM Processing (Local=Ollama or Smart=OpenRouter)
            print(f"{mode\\\_indicator} Thinking...")
            response\\\_msg = self.llm.process\\\_query(text, self.conversation\\\_history)
            
            # 3. Handle tool calls (execute in WSL2)
            # Tool calling works the same for both Ollama and OpenRouter
            tool\\\_calls = None
            
            # Handle both Ollama and OpenRouter response formats
            if hasattr(response\\\_msg, 'tool\\\_calls') and response\\\_msg.tool\\\_calls:
                # OpenRouter format (OpenAI-compatible)
                tool\\\_calls = response\\\_msg.tool\\\_calls
            elif isinstance(response\\\_msg, dict) and response\\\_msg.get('tool\\\_calls'):
                # Ollama format
                tool\\\_calls = response\\\_msg\\\['tool\\\_calls']
            
            if tool\\\_calls:
                print(f"🔧 Executing {len(tool\\\_calls)} tool(s) in WSL2...")
                
                # Add assistant message with tool calls to history
                self.conversation\\\_history.append({
                    "role": "assistant",
                    "content": response\\\_msg.get('content', '') if isinstance(response\\\_msg, dict) else (response\\\_msg.content or ''),
                    "tool\\\_calls": tool\\\_calls
                })
                
                # Execute each tool call
                for tool\\\_call in tool\\\_calls:
                    if isinstance(tool\\\_call, dict):
                        # Ollama format
                        function\\\_name = tool\\\_call\\\['function']\\\['name']
                        arguments = tool\\\_call\\\['function']\\\['arguments']
                    else:
                        # OpenRouter/OpenAI format
                        function\\\_name = tool\\\_call.function.name
                        arguments = json.loads(tool\\\_call.function.arguments)
                    
                    # Execute in WSL2
                    result = self.llm.execute\\\_tool\\\_in\\\_wsl2(function\\\_name, arguments)
                    print(f"  ✓ {function\\\_name}: {result.get('message', result)}")
                    
                    # Add tool result to history
                    tool\\\_call\\\_id = tool\\\_call.get('id') if isinstance(tool\\\_call, dict) else tool\\\_call.id
                    self.conversation\\\_history.append({
                        "role": "tool",
                        "tool\\\_call\\\_id": tool\\\_call\\\_id,
                        "content": json.dumps(result)
                    })
                
                # Get final response after tool execution
                print(f"{mode\\\_indicator} Generating final response...")
                final\\\_response = self.llm.process\\\_query("", self.conversation\\\_history)
                
                if isinstance(final\\\_response, dict):
                    response\\\_text = final\\\_response.get('content', '')
                else:
                    response\\\_text = final\\\_response.content
            else:
                # No tool calls, direct response
                if isinstance(response\\\_msg, dict):
                    response\\\_text = response\\\_msg.get('content', '')
                else:
                    response\\\_text = response\\\_msg.content
            
            # 4. Text to Speech (Windows CPU)
            print(f"💬 {response\\\_text}")
            print("🔊 Speaking...")
            self.tts.speak(response\\\_text)
            
            # Update history
            self.conversation\\\_history.append({"role": "user", "content": text})
            self.conversation\\\_history.append({"role": "assistant", "content": response\\\_text})
            
            # Keep history manageable
            if len(self.conversation\\\_history) > 20:
                self.conversation\\\_history = self.conversation\\\_history\\\[-20:]
            
            print("✅ Done!\\\\n")
            
        except Exception as e:
            import traceback
            print(f"❌ Error: {e}")
            traceback.print\\\_exc()
            self.tts.speak("Sorry, I encountered an error.")
    
    def run(self):
        """Main loop"""
        print("=" \\\* 70)
        print("           🎙️  VOICE ASSISTANT WITH SMART MODE 🎙️")
        print("=" \\\* 70)
        print(f"WSL2 IP: {self.wsl2\\\_ip}")
        print(f"Current Mode: {self.llm.get\\\_current\\\_mode()}")
        print()
        print("CONTROLS:")
        print("  ▶️  Play/Pause - Toggle voice recording")
        print("  ⏭️  Next Track - Activate Smart Mode (cloud AI)")
        print("  ⏮️  Previous Track - Deactivate Smart Mode (local AI)")
        print("=" \\\* 70)
        print()
        
        # Audio stream
        stream = sd.InputStream(
            channels=1,
            samplerate=self.sample\\\_rate,
            callback=self.audio\\\_callback
        )
        stream.start()
        
        # Media button handlers
        def on\\\_play\\\_press():
            if not self.recording:
                self.start\\\_recording()
            else:
                self.stop\\\_recording()
        
        def on\\\_next\\\_press():
            """Next Track = Activate Smart Mode"""
            if not self.llm.smart\\\_mode:
                self.toggle\\\_smart\\\_mode()
        
        def on\\\_prev\\\_press():
            """Previous Track = Deactivate Smart Mode"""
            if self.llm.smart\\\_mode:
                self.toggle\\\_smart\\\_mode()
        
        # Register hotkeys (requires admin privileges)
        try:
            keyboard.add\\\_hotkey('play/pause media', on\\\_play\\\_press)
            keyboard.add\\\_hotkey('next track', on\\\_next\\\_press)
            keyboard.add\\\_hotkey('previous track', on\\\_prev\\\_press)
            print("✅ Media keys registered successfully")
        except:
            print("⚠️  Could not register media keys. Using keyboard alternatives:")
            print("   Space - Toggle recording")
            print("   Right Arrow - Smart Mode ON")
            print("   Left Arrow - Smart Mode OFF")
            keyboard.add\\\_hotkey('space', on\\\_play\\\_press)
            keyboard.add\\\_hotkey('right', on\\\_next\\\_press)
            keyboard.add\\\_hotkey('left', on\\\_prev\\\_press)
        
        print("\\\\nSystem ready! Start speaking...\\\\n")
        
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            print("\\\\nShutting down...")
            stream.stop()
            stream.close()

if \\\_\\\_name\\\_\\\_ == "\\\_\\\_main\\\_\\\_":
    assistant = VoiceAssistant()
    assistant.run()
```

### Environment Variables Setup

```bash
# .env file (Windows)
# OpenRouter API Key (get from https://openrouter.ai/)
OPENROUTER\\\_API\\\_KEY=sk-or-v1-your-key-here

# Optional: Set default smart mode model
# Options: fast, smart, code, balanced
SMART\\\_MODE\\\_MODEL=fast
```

### Cost Tracking Script

```python
# track\\\_costs.py - Monitor your OpenRouter spending
import requests
import os
from datetime import datetime

def check\\\_openrouter\\\_balance():
    """Check remaining credits and usage"""
    api\\\_key = os.environ.get("OPENROUTER\\\_API\\\_KEY")
    
    if not api\\\_key:
        print("❌ OPENROUTER\\\_API\\\_KEY not set")
        return
    
    headers = {
        "Authorization": f"Bearer {api\\\_key}"
    }
    
    # Get credits info
    response = requests.get(
        "https://openrouter.ai/api/v1/auth/key",
        headers=headers
    )
    
    if response.status\\\_code == 200:
        data = response.json()\\\['data']
        print("=" \\\* 50)
        print("💳 OpenRouter Account Status")
        print("=" \\\* 50)
        print(f"Credits Remaining: ${data.get('limit', 0):.4f}")
        print(f"Usage This Month: ${data.get('usage', 0):.4f}")
        print(f"Key Name: {data.get('label', 'N/A')}")
        print("=" \\\* 50)
    else:
        print(f"❌ Error checking balance: {response.status\\\_code}")

if \\\_\\\_name\\\_\\\_ == "\\\_\\\_main\\\_\\\_":
    check\\\_openrouter\\\_balance()
```

```python
# voice\\\_assistant.py (run on Windows)
import sounddevice as sd
import numpy as np
import keyboard
import subprocess
import ollama
import json
from threading import Thread
from windows\\\_components.speech\\\_recognizer import SpeechRecognizer
from windows\\\_components.llm\\\_client import OllamaLLMClient
from windows\\\_components.text\\\_to\\\_speech import TextToSpeech

class VoiceAssistant:
    def \\\_\\\_init\\\_\\\_(self):
        # Get WSL2 IP address
        self.wsl2\\\_ip = self.\\\_get\\\_wsl2\\\_ip()
        
        self.asr = SpeechRecognizer()
        self.llm = OllamaLLMClient(self.wsl2\\\_ip, model="qwen3:8b")
        self.tts = TextToSpeech()
        
        self.recording = False
        self.audio\\\_buffer = \\\[]
        self.sample\\\_rate = 16000
        self.conversation\\\_history = \\\[]
    
    def \\\_get\\\_wsl2\\\_ip(self):
        """Get WSL2 IP address"""
        result = subprocess.run(
            \\\["wsl", "hostname", "-I"],
            capture\\\_output=True,
            text=True
        )
        ip = result.stdout.strip().split()\\\[0]
        print(f"WSL2 IP: {ip}")
        return ip
    
    def audio\\\_callback(self, indata, frames, time, status):
        if self.recording:
            self.audio\\\_buffer.append(indata.copy())
    
    def start\\\_recording(self):
        self.recording = True
        self.audio\\\_buffer = \\\[]
        print("🎤 Listening...")
    
    def stop\\\_recording(self):
        self.recording = False
        print("⏸️  Processing...")
        
        if not self.audio\\\_buffer:
            return
        
        audio\\\_data = np.concatenate(self.audio\\\_buffer)
        Thread(target=self.process\\\_audio, args=(audio\\\_data,)).start()
    
    def process\\\_audio(self, audio\\\_data):
        """Full processing pipeline with Ollama"""
        try:
            # 1. Speech Recognition (Windows GPU)
            print("🔤 Transcribing...")
            text = self.asr.transcribe(audio\\\_data)
            print(f"You: {text}")
            
            if not text.strip():
                self.tts.speak("I didn't catch that.")
                return
            
            # 2. Ollama Processing (Windows GPU)
            print("🤖 Thinking...")
            response\\\_msg = self.llm.process\\\_query(text, self.conversation\\\_history)
            
            # 3. Handle tool calls (execute in WSL2)
            if response\\\_msg.get('tool\\\_calls'):
                print(f"🔧 Executing {len(response\\\_msg\\\['tool\\\_calls'])} tool(s) in WSL2...")
                
                # Add assistant message with tool calls to history
                self.conversation\\\_history.append({
                    "role": "assistant",
                    "content": response\\\_msg.get('content', ''),
                    "tool\\\_calls": response\\\_msg\\\['tool\\\_calls']
                })
                
                # Execute each tool call
                for tool\\\_call in response\\\_msg\\\['tool\\\_calls']:
                    function\\\_name = tool\\\_call\\\['function']\\\['name']
                    arguments = tool\\\_call\\\['function']\\\['arguments']
                    
                    # Execute in WSL2
                    result = self.llm.execute\\\_tool\\\_in\\\_wsl2(function\\\_name, arguments)
                    print(f"  ✓ {function\\\_name}: {result.get('message', result)}")
                    
                    # Add tool result to history
                    self.conversation\\\_history.append({
                        "role": "tool",
                        "content": json.dumps(result)
                    })
                
                # Get final response from Ollama after tool execution
                print("🤖 Generating final response...")
                final\\\_response = ollama.chat(
                    model=self.llm.model,
                    messages=self.conversation\\\_history
                )
                response\\\_text = final\\\_response\\\['message']\\\['content']
            else:
                # No tool calls, direct response
                response\\\_text = response\\\_msg.get('content', '')
            
            # 4. Text to Speech (Windows CPU)
            print(f"💬 {response\\\_text}")
            print("🔊 Speaking...")
            self.tts.speak(response\\\_text)
            
            # Update history
            self.conversation\\\_history.append({"role": "user", "content": text})
            self.conversation\\\_history.append({"role": "assistant", "content": response\\\_text})
            
            # Keep history manageable
            if len(self.conversation\\\_history) > 20:
                self.conversation\\\_history = self.conversation\\\_history\\\[-20:]
            
            print("✅ Done!\\\\n")
            
        except Exception as e:
            import traceback
            print(f"❌ Error: {e}")
            traceback.print\\\_exc()
            self.tts.speak("Sorry, I encountered an error.")
    
    def run(self):
        """Main loop"""
        print("=" \\\* 60)
        print("Voice Assistant Ready!")
        print(f"WSL2 IP: {self.wsl2\\\_ip}")
        print(f"Ollama Model: {self.llm.model}")
        print("Press Play/Pause to toggle recording")
        print("=" \\\* 60)
        print()
        
        # Audio stream
        stream = sd.InputStream(
            channels=1,
            samplerate=self.sample\\\_rate,
            callback=self.audio\\\_callback
        )
        stream.start()
        
        # Media button handler
        def on\\\_play\\\_press():
            if not self.recording:
                self.start\\\_recording()
            else:
                self.stop\\\_recording()
        
        # Note: Requires running as administrator on Windows
        try:
            keyboard.add\\\_hotkey('play/pause media', on\\\_play\\\_press)
        except:
            print("⚠️  Could not register media key. Run as administrator or use alternative key.")
            print("Using Spacebar as alternative...")
            keyboard.add\\\_hotkey('space', on\\\_play\\\_press)
        
        print("System ready! Start speaking...\\\\n")
        
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            print("\\\\nShutting down...")
            stream.stop()
            stream.close()

if \\\_\\\_name\\\_\\\_ == "\\\_\\\_main\\\_\\\_":
    assistant = VoiceAssistant()
    assistant.run()
```

### Quick Test Script

```python
# test\\\_ollama\\\_tools.py - Test Ollama tool calling before full integration
import ollama

# Define a simple test tool
def get\\\_current\\\_time():
    """Get the current time"""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

# Test tool calling with Ollama
print("Testing Ollama tool calling...")
response = ollama.chat(
    model='qwen3:8b',
    messages=\\\[{'role': 'user', 'content': 'What time is it?'}],
    tools=\\\[get\\\_current\\\_time]  # Ollama can use Python functions directly!
)

print("\\\\n" + "="\\\*50)
print("Response Message:")
print("="\\\*50)

# Ollama response structure:
# response.message or response\\\['message'] both work
message = response.message if hasattr(response, 'message') else response\\\['message']

print(f"Content: {message.content if hasattr(message, 'content') else message.get('content')}")
print(f"Tool Calls: {message.tool\\\_calls if hasattr(message, 'tool\\\_calls') else message.get('tool\\\_calls')}")

if hasattr(message, 'tool\\\_calls') and message.tool\\\_calls:
    print("\\\\n✅ Tool calling works!")
    for call in message.tool\\\_calls:
        print(f"  Called: {call.function.name}")
        print(f"  Args: {call.function.arguments}")
        
        # Execute the function
        result = get\\\_current\\\_time()
        print(f"  Result: {result}")
else:
    print("\\\\n⚠️  No tool calls returned")
    print("This might mean:")
    print("  1. Model chose not to use tools")
    print("  2. Model doesn't support tools (try: ollama pull qwen3:8b)")
    print("  3. Response was direct text instead")
```

### Test WSL2 Connection

```python
# test\\\_wsl2\\\_connection.py - Test Windows to WSL2 communication
import subprocess
import requests

# 1. Get WSL2 IP
print("Getting WSL2 IP address...")
result = subprocess.run(
    \\\["wsl", "hostname", "-I"],
    capture\\\_output=True,
    text=True
)
wsl2\\\_ip = result.stdout.strip().split()\\\[0]
print(f"WSL2 IP: {wsl2\\\_ip}")

# 2. Test connection to WSL2 tool server
print(f"\\\\nTesting connection to http://{wsl2\\\_ip}:5000...")
try:
    response = requests.get(f"http://{wsl2\\\_ip}:5000/health", timeout=5)
    if response.status\\\_code == 200:
        print("✅ WSL2 tool server is running!")
    else:
        print(f"⚠️  Server responded with status: {response.status\\\_code}")
except requests.exceptions.RequestException as e:
    print(f"❌ Cannot connect to WSL2 server: {e}")
    print("\\\\nMake sure:")
    print("  1. WSL2 is running: wsl")
    print("  2. Tool server is started in WSL2: python3 tool\\\_server.py")
    print("  3. Server is listening on 0.0.0.0:5000")

# 3. Test a simple tool execution
print("\\\\nTesting tool execution...")
try:
    response = requests.post(
        f"http://{wsl2\\\_ip}:5000/execute",
        json={
            "tool": "execute\\\_command",
            "arguments": {"command": "echo 'Hello from WSL2'"}
        },
        timeout=10
    )
    
    if response.status\\\_code == 200:
        result = response.json()
        print("✅ Tool execution successful!")
        print(f"Result: {result}")
    else:
        print(f"❌ Tool execution failed: {response.status\\\_code}")
except Exception as e:
    print(f"❌ Error testing tool execution: {e}")
```

### 6.2 Qwen3-8B with Tool Calling (vLLM)

```python
from openai import OpenAI
import json

class LocalLLM:
    def \\\_\\\_init\\\_\\\_(self):
        # Connect to local vLLM server
        self.client = OpenAI(
            base\\\_url="http://localhost:8000/v1",
            api\\\_key="not-needed"
        )
        
        # Define available tools for MCP
        self.tools = \\\[
            {
                "type": "function",
                "function": {
                    "name": "move\\\_mouse",
                    "description": "Move the mouse cursor to specified screen coordinates",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {
                                "type": "integer",
                                "description": "X coordinate on screen"
                            },
                            "y": {
                                "type": "integer",
                                "description": "Y coordinate on screen"
                            }
                        },
                        "required": \\\["x", "y"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "type\\\_text",
                    "description": "Type text at current cursor position",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to type"
                            }
                        },
                        "required": \\\["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "click\\\_mouse",
                    "description": "Click mouse button at current or specified position",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "button": {
                                "type": "string",
                                "enum": \\\["left", "right", "middle"],
                                "description": "Which mouse button to click"
                            },
                            "x": {"type": "integer", "description": "X coordinate (optional)"},
                            "y": {"type": "integer", "description": "Y coordinate (optional)"}
                        },
                        "required": \\\["button"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open\\\_application",
                    "description": "Open an application or program",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app\\\_name": {
                                "type": "string",
                                "description": "Name of application to open (e.g., 'chrome', 'vscode', 'notepad')"
                            }
                        },
                        "required": \\\["app\\\_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create\\\_file",
                    "description": "Create a new file with specified content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Full path where file should be created"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to file"
                            }
                        },
                        "required": \\\["filepath", "content"]
                    }
                }
            }
        ]
    
    def process\\\_query(self, user\\\_text, conversation\\\_history=\\\[]):
        """
        Process user query with tool calling support
        """
        messages = conversation\\\_history + \\\[
            {"role": "user", "content": user\\\_text}
        ]
        
        response = self.client.chat.completions.create(
            model="Qwen3-8B",
            messages=messages,
            tools=self.tools,
            tool\\\_choice="auto",  # Let model decide
            temperature=0.7,
            max\\\_tokens=1000
        )
        
        return response.choices\\\[0].message

# Start vLLM server (run this separately):
"""
vllm serve Qwen/Qwen3-8B-GGUF:Q4\\\_K\\\_M \\\\
    --enable-auto-tool-choice \\\\
    --tool-call-parser hermes \\\\
    --gpu-memory-utilization 0.8 \\\\
    --max-model-len 8192
"""
```

### 6.3 Piper TTS Setup

```python
import subprocess
import threading
import queue
from pathlib import Path

class TextToSpeech:
    def \\\_\\\_init\\\_\\\_(self):
        # Download Piper voice model first:
        # https://github.com/rhasspy/piper/releases/
        # Example: en\\\_US-lessac-medium.onnx
        self.model\\\_path = Path("models/en\\\_US-lessac-medium.onnx")
        self.piper\\\_exe = "piper.exe"  # or "piper" on Linux
        
    def speak(self, text, blocking=False):
        """
        Convert text to speech and play
        """
        # Piper command: echo "text" | piper --model model.onnx --output\\\_file -
        cmd = \\\[
            self.piper\\\_exe,
            "--model", str(self.model\\\_path),
            "--output\\\_raw"  # Output raw audio for immediate playback
        ]
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Send text to Piper
        audio\\\_data, \\\_ = process.communicate(input=text.encode())
        
        # Play audio immediately
        self.\\\_play\\\_audio(audio\\\_data)
        
        return audio\\\_data
    
    def \\\_play\\\_audio(self, raw\\\_audio):
        """Play raw audio using sounddevice"""
        import sounddevice as sd
        import numpy as np
        
        # Convert raw audio to numpy array
        audio\\\_array = np.frombuffer(raw\\\_audio, dtype=np.int16)
        
        # Play at 22050 Hz (Piper default)
        sd.play(audio\\\_array, samplerate=22050)
        sd.wait()
    
    def speak\\\_streaming(self, text\\\_generator):
        """
        Stream TTS for real-time generation
        Useful for long responses from LLM
        """
        for sentence in text\\\_generator:
            self.speak(sentence, blocking=True)
```

### 6.4 MCP Integration

```python
import pyautogui
import subprocess
from pathlib import Path

class MCPToolExecutor:
    """
    Execute tool calls via MCP or direct implementation
    """
    def \\\_\\\_init\\\_\\\_(self):
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.1
    
    def execute\\\_tool(self, tool\\\_name, arguments):
        """
        Execute a tool call and return results
        """
        try:
            if tool\\\_name == "move\\\_mouse":
                return self.move\\\_mouse(\\\*\\\*arguments)
            elif tool\\\_name == "click\\\_mouse":
                return self.click\\\_mouse(\\\*\\\*arguments)
            elif tool\\\_name == "type\\\_text":
                return self.type\\\_text(\\\*\\\*arguments)
            elif tool\\\_name == "open\\\_application":
                return self.open\\\_application(\\\*\\\*arguments)
            elif tool\\\_name == "create\\\_file":
                return self.create\\\_file(\\\*\\\*arguments)
            else:
                return {"error": f"Unknown tool: {tool\\\_name}"}
        except Exception as e:
            return {"error": str(e)}
    
    def move\\\_mouse(self, x, y):
        pyautogui.moveTo(x, y)
        return {"status": "success", "message": f"Moved mouse to ({x}, {y})"}
    
    def click\\\_mouse(self, button, x=None, y=None):
        if x and y:
            pyautogui.click(x, y, button=button)
        else:
            pyautogui.click(button=button)
        return {"status": "success", "message": f"Clicked {button} button"}
    
    def type\\\_text(self, text):
        pyautogui.write(text, interval=0.01)
        return {"status": "success", "message": f"Typed: {text\\\[:50]}..."}
    
    def open\\\_application(self, app\\\_name):
        # Windows-specific
        app\\\_map = {
            "chrome": "chrome.exe",
            "notepad": "notepad.exe",
            "vscode": "code.exe",
            "explorer": "explorer.exe"
        }
        
        app\\\_exe = app\\\_map.get(app\\\_name.lower(), app\\\_name)
        subprocess.Popen(app\\\_exe, shell=True)
        return {"status": "success", "message": f"Opened {app\\\_name}"}
    
    def create\\\_file(self, filepath, content):
        # Ensure path is safe (sandbox to specific directories)
        safe\\\_base = Path("C:/VoiceAssistant/Projects")
        full\\\_path = safe\\\_base / filepath
        
        # Security check
        if not str(full\\\_path).startswith(str(safe\\\_base)):
            return {"error": "Path outside allowed directory"}
        
        # Create directories if needed
        full\\\_path.parent.mkdir(parents=True, exist\\\_ok=True)
        
        # Write file
        full\\\_path.write\\\_text(content, encoding='utf-8')
        return {"status": "success", "message": f"Created file: {full\\\_path}"}
```

### 6.5 Complete Integration

```python
import sounddevice as sd
import numpy as np
import keyboard
from threading import Thread, Event

class VoiceAssistant:
    def \\\_\\\_init\\\_\\\_(self):
        self.asr = SpeechRecognizer()
        self.llm = LocalLLM()
        self.tts = TextToSpeech()
        self.tool\\\_executor = MCPToolExecutor()
        
        self.recording = False
        self.audio\\\_buffer = \\\[]
        self.sample\\\_rate = 16000
        
        self.conversation\\\_history = \\\[]
        
    def audio\\\_callback(self, indata, frames, time, status):
        """Callback for audio recording"""
        if self.recording:
            self.audio\\\_buffer.append(indata.copy())
    
    def start\\\_recording(self):
        """Start recording audio"""
        self.recording = True
        self.audio\\\_buffer = \\\[]
        print("🎤 Listening...")
    
    def stop\\\_recording(self):
        """Stop recording and process"""
        self.recording = False
        print("⏸️  Processing...")
        
        if not self.audio\\\_buffer:
            return
        
        # Combine audio chunks
        audio\\\_data = np.concatenate(self.audio\\\_buffer)
        
        # Process in separate thread to avoid blocking
        Thread(target=self.process\\\_audio, args=(audio\\\_data,)).start()
    
    def process\\\_audio(self, audio\\\_data):
        """Full processing pipeline"""
        try:
            # 1. Speech Recognition
            print("🔤 Transcribing...")
            text = self.asr.transcribe(audio\\\_data)
            print(f"You said: {text}")
            
            if not text.strip():
                self.tts.speak("I didn't catch that. Could you repeat?")
                return
            
            # 2. LLM Processing
            print("🤖 Thinking...")
            response\\\_message = self.llm.process\\\_query(text, self.conversation\\\_history)
            
            # 3. Handle tool calls if any
            if response\\\_message.tool\\\_calls:
                print(f"🔧 Executing {len(response\\\_message.tool\\\_calls)} tool(s)...")
                
                tool\\\_results = \\\[]
                for tool\\\_call in response\\\_message.tool\\\_calls:
                    result = self.tool\\\_executor.execute\\\_tool(
                        tool\\\_call.function.name,
                        json.loads(tool\\\_call.function.arguments)
                    )
                    tool\\\_results.append(result)
                    print(f"  ✓ {tool\\\_call.function.name}: {result.get('message', result)}")
                
                # Send results back to LLM for final response
                self.conversation\\\_history.append({
                    "role": "assistant",
                    "content": None,
                    "tool\\\_calls": response\\\_message.tool\\\_calls
                })
                
                for tool\\\_call, result in zip(response\\\_message.tool\\\_calls, tool\\\_results):
                    self.conversation\\\_history.append({
                        "role": "tool",
                        "tool\\\_call\\\_id": tool\\\_call.id,
                        "content": json.dumps(result)
                    })
                
                # Get final response
                final\\\_response = self.llm.process\\\_query("", self.conversation\\\_history)
                response\\\_text = final\\\_response.content
            else:
                response\\\_text = response\\\_message.content
            
            # 4. Text to Speech
            print(f"💬 Response: {response\\\_text}")
            print("🔊 Speaking...")
            self.tts.speak(response\\\_text)
            
            # Update conversation history
            self.conversation\\\_history.append({"role": "user", "content": text})
            self.conversation\\\_history.append({"role": "assistant", "content": response\\\_text})
            
            # Keep history manageable (last 10 exchanges)
            if len(self.conversation\\\_history) > 20:
                self.conversation\\\_history = self.conversation\\\_history\\\[-20:]
            
            print("✅ Done!\\\\n")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            self.tts.speak("Sorry, I encountered an error processing that request.")
    
    def run(self):
        """Main loop with media button control"""
        print("Voice Assistant Ready!")
        print("Press Play/Pause to toggle recording")
        print("Press Ctrl+C to exit\\\\n")
        
        # Set up audio stream
        stream = sd.InputStream(
            channels=1,
            samplerate=self.sample\\\_rate,
            callback=self.audio\\\_callback
        )
        stream.start()
        
        # Media button handler
        def on\\\_play\\\_press():
            if not self.recording:
                self.start\\\_recording()
            else:
                self.stop\\\_recording()
        
        # Register hotkey (requires admin privileges)
        keyboard.add\\\_hotkey('play/pause media', on\\\_play\\\_press)
        
        try:
            keyboard.wait()  # Keep running
        except KeyboardInterrupt:
            print("\\\\nShutting down...")
            stream.stop()
            stream.close()

# Run the assistant
if \\\_\\\_name\\\_\\\_ == "\\\_\\\_main\\\_\\\_":
    assistant = VoiceAssistant()
    assistant.run()
```

---





---




---

## 11\. Recommended Starting Point

### Quick Start Implementation

**Step 1:** Install dependencies

```bash
pip install openai websockets sounddevice keyboard numpy pyaudio
pip install computer-control-mcp
```

**Step 2:** Set up OpenAI API key

```bash
export OPENAI\\\_API\\\_KEY="your-key-here"
```

**Step 3:** Test basic voice recording

```python
# test\\\_audio.py
import sounddevice as sd
print("Recording for 5 seconds...")
audio = sd.rec(int(5 \\\* 16000), samplerate=16000, channels=1)
sd.wait()
sd.play(audio, 16000)
sd.wait()
```

**Step 4:** Test Realtime API connection

```python
# test\\\_realtime.py
# Simple echo test with OpenAI Realtime API
```

**Step 5:** Test MCP server

```bash
computer-control-mcp
# In another terminal, test tool execution
```

**Step 6:** Integrate components incrementally

---

## 13\. Next Steps

1. **Immediate Actions:**

   * Set up OpenAI account and get API key
   * Install Python dependencies
   * Test Bluetooth button detection
   * Verify microphone quality

2. **Week 1 Goals:**

   * Working push-to-talk system
   * Basic OpenAI Realtime connection
   * Simple voice echo test

3. **Questions to Answer:**

   * Budget for API costs?
   * Acceptable latency for different task types?
   * Specific development workflows to prioritize?
   * Security requirements for your environment?

---

## Appendix A: Required Libraries (Local + Smart Mode)

```txt
# requirements.txt (Windows)

# Speech Recognition
faster-whisper>=1.0.0

# Language Models
ollama>=0.4.0          # For Local Mode
openai>=1.0.0          # For Smart Mode (OpenRouter uses OpenAI-compatible API)

# Audio I/O
sounddevice>=0.4.6
numpy>=1.24.0
pyaudio>=0.2.14

# Computer Control
keyboard>=0.13.5
pywin32>=306  # Windows-specific

# HTTP client for WSL2 communication
requests>=2.31.0

# Environment variables
python-dotenv>=1.0.0
```

```txt
# requirements.txt (WSL2 Ubuntu)

# Web server for tool execution
flask>=3.0.0

# Linux automation tools (install via apt, not pip)
# sudo apt install xdotool wmctrl scrot xclip

# Python automation (if needed as fallback)
pyautogui>=0.9.54
```

### Installation Steps (with Smart Mode!)

**Windows Setup:**

```powershell
# 1. Create virtual environment
python -m venv voice\\\_assistant\\\_env
.\\\\voice\\\_assistant\\\_env\\\\Scripts\\\\activate

# 2. Install Python dependencies
pip install faster-whisper sounddevice numpy keyboard pyaudio ollama openai requests python-dotenv

# 3. Install Ollama for Windows (Local Mode)
# Download from: https://ollama.com/download/windows
# Or via winget:
winget install Ollama.Ollama

# 4. Pull Qwen3 model for Local Mode
ollama pull qwen3:8b
# This downloads ~5GB, takes 5-10 minutes

# 5. Set up OpenRouter for Smart Mode
# a. Sign up at https://openrouter.ai/
# b. Add $10-20 credits (pay-as-you-go, lasts months)
# c. Get API key from https://openrouter.ai/settings/keys
# d. Create .env file:
echo OPENROUTER\\\_API\\\_KEY=sk-or-v1-your-key-here > .env

# 6. Verify OpenRouter connection
python -c "import openai; import os; from dotenv import load\\\_dotenv; load\\\_dotenv(); client = openai.OpenAI(base\\\_url='https://openrouter.ai/api/v1', api\\\_key=os.environ\\\['OPENROUTER\\\_API\\\_KEY']); print('OpenRouter connected!' if os.environ.get('OPENROUTER\\\_API\\\_KEY') else 'No API key')"

# 7. Download Piper TTS
# From: https://github.com/rhasspy/piper/releases
# Extract to: .\\\\models\\\\piper.exe

# 8. Download Piper voice model
# From: https://huggingface.co/rhasspy/piper-voices
# Download: en\\\_US-lessac-medium.onnx and .json file
# Save to: .\\\\models\\\\

# 9. Test all components
python test\\\_components.py
```

**WSL2 Ubuntu Setup (unchanged):**

```bash
# 1. Update system
sudo apt update \\\&\\\& sudo apt upgrade -y

# 2. Install Python and tools
sudo apt install python3-pip python3-venv -y

# 3. Create virtual environment
python3 -m venv ~/tool\\\_server\\\_env
source ~/tool\\\_server\\\_env/bin/activate

# 4. Install Python packages
pip install flask requests

# 5. Install Linux automation tools
sudo apt install xdotool wmctrl scrot xclip -y

# 6. Create projects directory
mkdir -p ~/projects

# 7. Test WSL2 server
python3 tool\\\_server.py
```

### Quick Start Guide (with Smart Mode)

**1. Start WSL2 Tool Server:**

```bash
# In WSL2 Ubuntu terminal:
cd ~/voice\\\_assistant
source tool\\\_server\\\_env/bin/activate
python3 tool\\\_server.py
```

**2. Start Windows Voice Assistant:**

```powershell
# In Windows PowerShell:
cd C:\\\\voice\\\_assistant
.\\\\voice\\\_assistant\\\_env\\\\Scripts\\\\activate
python voice\\\_assistant.py
```

**3. Test Both Modes:**

**Local Mode Test:**

* Press Play/Pause button (or Spacebar)
* Say: "Create a Python file that prints hello world"
* Should use Ollama (free, 3-6s response)

**Smart Mode Test:**

* Press Next Track button (or Right Arrow)
* System says: "Smart mode activated"
* Press Play/Pause
* Say: "Write a complex FastAPI application with authentication"
* Should use OpenRouter (~$0.001 cost, 1-2s response)
* Press Previous Track to return to Local Mode

### Startup Script (Windows - Both Modes)

```batch
@echo off
REM start\\\_voice\\\_assistant.bat

echo Starting WSL2 Tool Server...
start "WSL2 Server" wsl -d Ubuntu-22.04 bash -c "cd ~/voice\\\_assistant \\\&\\\& source tool\\\_server\\\_env/bin/activate \\\&\\\& python3 tool\\\_server.py"

timeout /t 3

echo Starting Voice Assistant (Local + Smart Mode Support)...
cd C:\\\\voice\\\_assistant
call voice\\\_assistant\\\_env\\\\Scripts\\\\activate

REM Load environment variables
if exist .env (
    echo Loading .env file...
    for /f "tokens=\\\*" %%i in (.env) do set %%i
)

python voice\\\_assistant.py

pause
```

### Cost Monitoring

```python
# monitor\\\_costs.py - Run this weekly to track spending
import os
from dotenv import load\\\_dotenv
import requests

load\\\_dotenv()

api\\\_key = os.environ.get("OPENROUTER\\\_API\\\_KEY")
headers = {"Authorization": f"Bearer {api\\\_key}"}

response = requests.get(
    "https://openrouter.ai/api/v1/auth/key",
    headers=headers
)

if response.status\\\_code == 200:
    data = response.json()\\\['data']
    usage = data.get('usage', 0)
    limit = data.get('limit', 0)
    
    print("=" \\\* 60)
    print("💰 OpenRouter Usage Report")
    print("=" \\\* 60)
    print(f"Credits Used This Month: ${usage:.4f}")
    print(f"Remaining Credits: ${limit:.4f}")
    print(f"Estimated Monthly Cost: ${usage:.2f}")
    print()
    
    if usage < 5:
        print("✅ Light usage - excellent cost control!")
    elif usage < 20:
        print("✅ Moderate usage - within budget")
    else:
        print("⚠️  Heavy usage - consider using Local Mode more")
    
    print("=" \\\* 60)
else:
    print("❌ Could not fetch usage data")
```

```txt
# requirements.txt (Windows)

# Speech Recognition
faster-whisper>=1.0.0

# Language Model
ollama>=0.4.0

# Audio I/O
sounddevice>=0.4.6
numpy>=1.24.0
pyaudio>=0.2.14

# Computer Control
keyboard>=0.13.5
pywin32>=306  # Windows-specific

# HTTP client for WSL2 communication
requests>=2.31.0
```

```txt
# requirements.txt (WSL2 Ubuntu)

# Web server for tool execution
flask>=3.0.0

# Linux automation tools (install via apt, not pip)
# sudo apt install xdotool wmctrl scrot xclip

# Python automation (if needed as fallback)
pyautogui>=0.9.54
```

### Installation Steps (Simplified with Ollama!)

**Windows Setup:**

```powershell
# 1. Create virtual environment
python -m venv voice\\\_assistant\\\_env
.\\\\voice\\\_assistant\\\_env\\\\Scripts\\\\activate

# 2. Install Python dependencies
pip install faster-whisper sounddevice numpy keyboard pyaudio ollama requests

# 3. Install Ollama for Windows
# Download from: https://ollama.com/download/windows
# Or via winget:
winget install Ollama.Ollama

# 4. Pull Qwen3 model
ollama pull qwen3:8b
# This downloads ~5GB, takes 5-10 minutes

# 5. Verify Ollama is working
ollama list
ollama run qwen3:8b "Hello, how are you?"

# 6. Download Piper TTS
# From: https://github.com/rhasspy/piper/releases
# Extract to: .\\\\models\\\\piper.exe

# 7. Download Piper voice model
# From: https://huggingface.co/rhasspy/piper-voices
# Download: en\\\_US-lessac-medium.onnx and .json file
# Save to: .\\\\models\\\\

# 8. Test components
python test\\\_components.py
```

**WSL2 Ubuntu Setup:**

```bash
# 1. Update system
sudo apt update \\\&\\\& sudo apt upgrade -y

# 2. Install Python and tools
sudo apt install python3-pip python3-venv -y

# 3. Create virtual environment
python3 -m venv ~/tool\\\_server\\\_env
source ~/tool\\\_server\\\_env/bin/activate

# 4. Install Python packages
pip install flask requests

# 5. Install Linux automation tools
sudo apt install xdotool wmctrl scrot xclip -y

# 6. Create projects directory
mkdir -p ~/projects

# 7. Test WSL2 server
python3 tool\\\_server.py
# Should show: "Tool server running on http://0.0.0.0:5000"

# 8. From Windows, get WSL2 IP:
# In PowerShell: wsl hostname -I
# Test connection: curl http://172.x.x.x:5000/health
```

### Quick Start Guide

**1. Start WSL2 Tool Server:**

```bash
# In WSL2 Ubuntu terminal:
cd ~/voice\\\_assistant
source tool\\\_server\\\_env/bin/activate
python3 tool\\\_server.py
```

**2. Start Windows Voice Assistant:**

```powershell
# In Windows PowerShell:
cd C:\\\\voice\\\_assistant
.\\\\voice\\\_assistant\\\_env\\\\Scripts\\\\activate
python voice\\\_assistant.py
```

**3. Test the System:**

* Press Play/Pause button (or Spacebar if admin privileges unavailable)
* Say: "Create a Python file that prints hello world"
* System should:

  1. Transcribe your speech
  2. Ollama processes the request
  3. Calls create\_file tool in WSL2
  4. Returns confirmation via speech

### Startup Script (Windows)

```batch
@echo off
REM start\\\_voice\\\_assistant.bat

echo Starting WSL2 Tool Server...
start "WSL2 Server" wsl -d Ubuntu-22.04 bash -c "cd ~/voice\\\_assistant \\\&\\\& source tool\\\_server\\\_env/bin/activate \\\&\\\& python3 tool\\\_server.py"

timeout /t 3

echo Starting Voice Assistant...
cd C:\\\\voice\\\_assistant
call voice\\\_assistant\\\_env\\\\Scripts\\\\activate
python voice\\\_assistant.py

pause
```


