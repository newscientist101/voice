## 8\. Security Considerations (WSL2 Sandboxing)

### Security Benefits of WSL2 Architecture

**Isolation Layers:**

1. **Network Boundary:** LLM on Windows cannot directly execute system commands
2. **Filesystem Separation:** WSL2 has its own ext4 filesystem
3. **Process Isolation:** WSL2 runs in separate VM with own kernel
4. **Resource Limits:** Can limit CPU/memory allocated to WSL2

### Critical Security Measures

**1. Path Sandboxing (WSL2 Server):**

```python
# REQUIRED: All file operations must validate paths
SAFE\\\_BASE = Path.home() / "projects"

def is\\\_safe\\\_path(filepath):
    """Prevent directory traversal attacks"""
    try:
        resolved = (SAFE\\\_BASE / filepath).resolve()
        return str(resolved).startswith(str(SAFE\\\_BASE.resolve()))
    except:
        return False

# Example attack prevented:
# filepath = "../../../etc/passwd"  # BLOCKED
# filepath = "my\\\_project/app.py"     # ALLOWED
```

**2. Command Whitelist (WSL2 Server):**

```python
# Only allow specific commands
COMMAND\\\_WHITELIST = \\\[
    "ls", "cat", "pwd", "python3", "pip", "git",
    "mkdir", "touch", "grep", "find"
]

# BLOCKED: rm -rf /
# BLOCKED: sudo apt install malware
# ALLOWED: python3 my\\\_script.py
```

**3. Network Authentication:**

```python
# Add API key between Windows and WSL2
WSL2\\\_API\\\_KEY = "generate-random-key-here"

@app.route('/execute', methods=\\\['POST'])
def execute\\\_tool():
    if request.headers.get('X-API-Key') != WSL2\\\_API\\\_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    # ... process request
```

**4. Resource Limits:**

```python
# WSL2: Limit execution time
import subprocess

result = subprocess.run(
    command,
    timeout=30,  # Kill after 30 seconds
    cwd=SAFE\\\_BASE
)

# WSL2: Limit memory in .wslconfig
# C:\\\\Users\\\\YourName\\\\.wslconfig
\\\[wsl2]
memory=4GB
processors=2
```

**5. Audit Logging:**

```python
# WSL2 Server: Log all tool executions
import logging

logging.basicConfig(
    filename='/home/user/tool\\\_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def execute\\\_tool():
    logging.info(f"Tool: {tool\\\_name}, Args: {arguments}, IP: {request.remote\\\_addr}")
    # ... execute
```

**6. Confirmation for Destructive Actions:**

```python
# LLM should ask before destructive operations
REQUIRES\\\_CONFIRMATION = \\\[
    'delete\\\_file',
    'execute\\\_command',  # If contains rm, sudo, etc.
    'install\\\_package'   # System modifications
]

# In Windows orchestrator:
if tool\\\_name in REQUIRES\\\_CONFIRMATION:
    # Speak to user: "This will delete file X. Confirm?"
    # Wait for voice response
    pass
```

### What the LLM Can and Cannot Do

**✅ LLM CAN (within WSL2 only):**

* Create/edit files in `/home/user/projects/`
* Install Python packages via pip
* Run whitelisted shell commands
* Execute Python/Node.js code
* Use git for version control
* Create web servers (accessible at WSL2 IP)
* Read files it created

**❌ LLM CANNOT:**

* Access Windows C: drive (unless explicitly mounted read-only)
* Control Windows applications
* Move mouse on Windows desktop
* Read Windows files (your documents, photos, etc.)
* Install Windows software
* Modify Windows registry
* Access hardware directly (GPU is managed by Windows)
* Execute arbitrary system commands (whitelist only)
* Escape the WSL2 sandbox

### Shared Folder Security (Optional)

If you want to share files between Windows and WSL2:

```bash
# Option 1: Read-only mount (safest)
# In WSL2, Windows drives auto-mount at /mnt/c/
# Create read-only bind mount:
sudo mount --bind -o ro /mnt/c/Users/You/Shared /home/user/readonly\\\_shared

# Option 2: Specific shared folder
# Create safe shared directory on Windows:
# C:\\\\WSL2-Safe-Share\\\\
# Access from WSL2:
ls /mnt/c/WSL2-Safe-Share/

# Recommendation: Don't share folders if possible
# Use network transfer instead (copy files manually when needed)
```

### WSL2 Snapshot for Recovery

```powershell
# Before risky operations, export WSL2 state
wsl --export Ubuntu-22.04 C:\\\\WSL2-Backups\\\\ubuntu-backup-2025-01-24.tar

# Restore if something goes wrong
wsl --unregister Ubuntu-22.04
wsl --import Ubuntu-22.04 C:\\\\WSL2\\\\Ubuntu C:\\\\WSL2-Backups\\\\ubuntu-backup-2025-01-24.tar
```

### Monitoring WSL2 Activity

```bash
# In WSL2: Monitor system resources
htop

# Monitor network connections
sudo netstat -tulpn | grep :5000

# Check audit log
tail -f ~/tool\\\_audit.log
```

### Emergency Shutdown

```python
# Windows: Kill WSL2 if LLM goes rogue
import subprocess

def emergency\\\_shutdown():
    subprocess.run(\\\["wsl", "--shutdown"])
    print("WSL2 terminated")
```

### Best Practices

1. **Principle of Least Privilege:** Only grant tools that are necessary
2. **Input Validation:** Always validate and sanitize LLM tool arguments
3. **Rate Limiting:** Limit requests to WSL2 server (prevent DoS)
4. **Regular Backups:** Export WSL2 state weekly
5. **Network Firewall:** WSL2 firewall to only accept from Windows host IP
6. **Code Review:** Review any code before LLM executes it
7. **Dry Run Mode:** Add flag to simulate tool calls without execution
