## Smart Mode Feature

### Overview

**Smart Mode** provides access to more powerful cloud models when you need maximum intelligence and lowest latency. Activated by pressing the **Next Track** button on your Bluetooth device.

### Why OpenRouter for Smart Mode?

**OpenRouter** is the ideal pay-as-you-go cloud provider because:

* Pure pay-as-you-go pricing with no markup - you pay exactly what the model providers charge
* Full tool calling support using OpenAI-compatible API
* Access to 100+ models from OpenAI, Anthropic, Google, Meta, and more
* Automatic fallback if a model is down
* No minimum commitments or monthly fees
* Simple credit-based system (add $10-50 as needed)

### Cost Comparison: Local vs Smart Mode

**Local Mode (Ollama/Qwen3-8B):**

* Cost: $0
* Latency: 3-6 seconds
* Quality: Excellent for most tasks
* Privacy: 100% local

**Smart Mode (OpenRouter - Recommended Models):**

|Model|Input Cost|Output Cost|Best For|Typical Query Cost|
|-|-|-|-|-|
|**Google Gemini 2.5 Flash**|$0.15/1M tokens|$0.60/1M tokens|Fast responses, coding|$0.0008 per query|
|**Anthropic Claude 3.5 Sonnet**|$3.00/1M tokens|$15.00/1M tokens|Complex reasoning|$0.018 per query|
|**OpenAI GPT-4o-mini**|$0.15/1M tokens|$0.60/1M tokens|General tasks|$0.0008 per query|
|**DeepSeek v3**|$0.27/1M tokens|$1.10/1M tokens|Coding, analysis|$0.0014 per query|

**Example Monthly Costs (Smart Mode only when needed):**

* Light use (20 queries/day, 50% local, 50% smart): ~$5/month
* Moderate use (50 queries/day, 70% local, 30% smart): ~$10/month
* Heavy use (100 queries/day, 50% local, 50% smart): ~$25/month

**Key Insight:** Using local mode for routine tasks and Smart Mode only when needed keeps costs under $10-25/month instead of $1,000+/month with cloud-only solutions.

**Visual/Audio Feedback:**

* Local Mode: "🤖 Local" indicator
* Smart Mode: "⚡ Smart" indicator + beep confirmation
* When you activate Smart Mode, system says: "Smart mode activated"
* When you deactivate, system says: "Local mode"

### Smart Mode Behavior

When Smart Mode is active:

1. Same voice input (Faster-Whisper on Windows GPU)
2. **LLM switches to OpenRouter** instead of Ollama
3. Tool execution still happens in WSL2 (security maintained)
4. Faster response times (1-2s vs 3-6s)
5. Access to more powerful reasoning models
6. Pay only for what you use

### Recommended Smart Mode Models

**For Speed (Default Smart Mode Model):**

```python
SMART\\\_MODE\\\_MODEL = "google/gemini-2.5-flash-exp"
# Cost: ~$0.0008 per query
# Latency: 1-2 seconds
# Best for: Quick questions, simple coding, general assistance
```

**For Complex Reasoning:**

```python
SMART\\\_MODE\\\_MODEL = "anthropic/claude-3.5-sonnet"
# Cost: ~$0.018 per query
# Latency: 2-3 seconds  
# Best for: Complex development tasks, architecture decisions, debugging
```

**For Coding Excellence:**

```python
SMART\\\_MODE\\\_MODEL = "deepseek/deepseek-chat"
# Cost: ~$0.0014 per query
# Latency: 1-2 seconds
# Best for: Code generation, refactoring, technical explanations
```

### When to Use Each Mode

**Use Local Mode (Ollama) for:**

* ✅ General questions ("what is X?")
* ✅ Simple file operations
* ✅ Routine coding tasks
* ✅ When privacy is critical
* ✅ When internet is slow/unavailable
* ✅ Learning/experimentation

**Use Smart Mode (OpenRouter) for:**

* ⚡ Complex multi-step development projects
* ⚡ Architectural decisions requiring deep reasoning
* ⚡ When you need the fastest possible response
* ⚡ Debugging complex issues
* ⚡ Natural language understanding edge cases
* ⚡ When local model struggles with a task
