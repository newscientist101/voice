## 3\. Bluetooth Media Button Integration

### Button Controls

**Bluetooth Device Buttons:**

* **Play/Pause:** Push-to-talk (start/stop recording)
* **Next Track:** Toggle Smart Mode ON (cloud AI with visual indicator)
* **Previous Track:** Toggle Smart Mode OFF (back to local Ollama)

### Approach: Global Hotkey Listener

Since Windows doesn't expose Bluetooth media buttons directly to Python, we'll use a global keyboard hook to detect media key presses.

#### Recommended Library: `keyboard` (Python)

```bash
pip install keyboard
```

**Implementation Strategy:**

```python
import keyboard

def on\\\_play\\\_press():
    # Start/stop voice recording
    toggle\\\_recording()

def on\\\_next\\\_press():
    # Cancel current operation
    cancel\\\_operation()

def on\\\_previous\\\_press():
    # Undo last action
    undo\\\_last\\\_action()

# Register hotkeys (requires admin privileges)
keyboard.add\\\_hotkey('play/pause media', on\\\_play\\\_press)
keyboard.add\\\_hotkey('next track', on\\\_next\\\_press)
keyboard.add\\\_hotkey('previous track', on\\\_previous\\\_press)

keyboard.wait()
```

**Alternative:** Use AutoHotkey script to remap media keys to custom hotkeys that Python can easily catch.

#### Media Key Virtual Codes (Windows)

```python
import win32api
from win32con import VK\\\_MEDIA\\\_PLAY\\\_PAUSE, VK\\\_MEDIA\\\_NEXT\\\_TRACK, VK\\\_MEDIA\\\_PREV\\\_TRACK
```

**Note:** Detecting these requires either:

1. Administrator privileges for global hooks
2. Focused window callback
3. AutoHotkey intermediary
