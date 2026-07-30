# pisama-auto

[![PyPI version](https://img.shields.io/pypi/v/pisama-auto.svg)](https://pypi.org/project/pisama-auto/)
[![Python versions](https://img.shields.io/pypi/pyversions/pisama-auto.svg)](https://pypi.org/project/pisama-auto/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/Pisama-AI/pisama-auto/actions/workflows/ci.yml/badge.svg)](https://github.com/Pisama-AI/pisama-auto/actions/workflows/ci.yml)
[![Downloads](https://img.shields.io/pypi/dm/pisama-auto)](https://pypistats.org/packages/pisama-auto)

Zero-code auto-instrumentation for LLM applications. Add Pisama failure detection with one line.

Requires Python 3.10 or newer. Python 3.10 through 3.13 are tested.

As of 0.3.0, `pisama-auto` is a compatibility shim over `pisama.auto` (part
of the `pisama` package): the implementation lives there now, this
distribution just forwards every import path to it, unchanged. See
[CHANGELOG.md](CHANGELOG.md) for details. Nothing below changes for existing
code.

## Quick Start

```bash
pip install "pisama[auto]"
```

`pisama[auto]` is the recommended install because it keeps the CLI, local
detectors, and auto-instrumentation on one compatible dependency path.
`pip install "pisama-auto[auto]"` is equivalent and keeps the `pisama_auto`
import name. Bare `pip install pisama-auto` still works for `import
pisama_auto` and `import pisama_auto.patches` -- neither has ever needed
OpenTelemetry or wrapt at import time -- but calling `init()`, or importing
`pisama_auto._tracer` / `pisama_auto.patches.anthropic_patch` /
`.openai_patch` directly, needs the `auto` extra installed one way or the
other; before 0.3.0 that was guaranteed by this package's own dependencies
instead -- see [CHANGELOG.md](CHANGELOG.md) for why.

```python
import pisama_auto
pisama_auto.init()  # traces locally; set PISAMA_API_KEY to export to Pisama

# All subsequent LLM calls are automatically traced
import anthropic
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}],
)
# This call is automatically traced and sent to Pisama if export is configured.
```

## Supported Libraries

| Library | Status | What's Traced |
|---------|--------|---------------|
| `anthropic` | GA | `messages.create()`, `messages.stream()` |
| `openai` | GA | `chat.completions.create()` |

## Package lifecycle

`pisama-auto` is a maintained implementation package. Its public API remains
supported, but it is not a separate product entry point. New users should
install `pisama[auto]`. Existing direct installations continue to work.

## How It Works

1. `pisama_auto.init()` sets up an OpenTelemetry tracer that exports to Pisama
2. It then patches supported LLM libraries to emit spans with `gen_ai.*` semantic conventions
3. Pisama's detection engine analyzes the exported traces for failure modes. This
   package ships traces; the detectors live in `pisama-core` and the Pisama platform
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

With an API key and no explicit endpoint, spans go to the Pisama platform (api.pisama.ai). The exporter exchanges the API key for a short-lived token automatically. Without an API key, traces are generated locally but not exported. Set `PISAMA_ENDPOINT` to target a self-hosted instance or a custom OTLP collector instead.

## Selective Patching

```python
import pisama_auto
pisama_auto.init(auto_patch=False)  # don't auto-patch

from pisama_auto.patches import patch
patch("anthropic")  # only patch anthropic
```
