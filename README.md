# pisama-auto

Zero-code auto-instrumentation for LLM applications. Add Pisama failure detection with one line.

## Quick Start

```bash
pip install pisama-auto
```

```python
import pisama_auto
pisama_auto.init()  # traces locally; set PISAMA_API_KEY + PISAMA_ENDPOINT to export

# All subsequent LLM calls are automatically traced
import anthropic
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}],
)
# ^ This call is automatically traced (and sent to Pisama if endpoint is configured)
```

## Supported Libraries

| Library | Status | What's Traced |
|---------|--------|---------------|
| `anthropic` | GA | `messages.create()`, `messages.stream()` |
| `openai` | GA | `chat.completions.create()` |

## How It Works

1. `pisama_auto.init()` sets up an OpenTelemetry tracer that exports to Pisama
2. It then patches supported LLM libraries to emit spans with `gen_ai.*` semantic conventions
3. Pisama's detection engine analyzes the traces for 25 failure modes
4. Results appear in your Pisama dashboard

## Configuration

```python
pisama_auto.init(
    api_key="ps_...",                    # or set PISAMA_API_KEY env var
    endpoint="https://your-instance/api/v1/traces/ingest",  # or PISAMA_ENDPOINT env var
    service_name="my-agent",             # OTEL service name
    auto_patch=True,                     # auto-patch all detected libraries
)
```

Without an endpoint, traces are generated locally but not exported. Set `PISAMA_ENDPOINT` to send them to the Pisama platform.

## Selective Patching

```python
import pisama_auto
pisama_auto.init(auto_patch=False)  # don't auto-patch

from pisama_auto.patches import patch
patch("anthropic")  # only patch anthropic
```
