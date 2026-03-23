"""Auto-instrumentation patch for the Anthropic Python SDK.

Wraps anthropic.Anthropic.messages.create() and .stream() to emit
OTEL spans with gen_ai.* semantic conventions.
"""

import json
import logging
from typing import Any

import wrapt

logger = logging.getLogger("pisama_auto")

_original_create = None
_original_stream = None


def patch() -> None:
    """Patch the Anthropic SDK to emit OTEL spans."""
    import anthropic

    messages_cls = anthropic.resources.Messages

    global _original_create, _original_stream
    _original_create = messages_cls.create
    _original_stream = getattr(messages_cls, "stream", None)

    wrapt.wrap_function_wrapper(messages_cls, "create", _traced_create)

    if _original_stream:
        wrapt.wrap_function_wrapper(messages_cls, "stream", _traced_stream)

    logger.debug("Anthropic SDK patched")


def _traced_create(wrapped, instance, args, kwargs) -> Any:
    """Wrapper for messages.create that adds OTEL tracing."""
    from pisama_auto._tracer import get_tracer

    tracer = get_tracer()
    model = kwargs.get("model", "unknown")
    span_name = f"gen_ai.chat {model}"

    with tracer.start_as_current_span(span_name) as span:
        # Set gen_ai.* attributes
        span.set_attribute("gen_ai.system", "anthropic")
        span.set_attribute("gen_ai.request.model", model)
        span.set_attribute("gen_ai.operation.name", "chat")

        max_tokens = kwargs.get("max_tokens")
        if max_tokens:
            span.set_attribute("gen_ai.request.max_tokens", max_tokens)

        temperature = kwargs.get("temperature")
        if temperature is not None:
            span.set_attribute("gen_ai.request.temperature", temperature)

        # Record input messages count
        messages = kwargs.get("messages", [])
        span.set_attribute("gen_ai.request.messages_count", len(messages))

        system = kwargs.get("system")
        if system:
            span.set_attribute("gen_ai.request.has_system", True)

        try:
            response = wrapped(*args, **kwargs)

            # Record response attributes
            span.set_attribute("gen_ai.response.model", getattr(response, "model", model))
            span.set_attribute("gen_ai.response.stop_reason", getattr(response, "stop_reason", ""))

            usage = getattr(response, "usage", None)
            if usage:
                span.set_attribute("gen_ai.usage.prompt_tokens", getattr(usage, "input_tokens", 0))
                span.set_attribute("gen_ai.usage.completion_tokens", getattr(usage, "output_tokens", 0))

            return response

        except Exception as e:
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e)[:500])
            span.set_status(
                __import__("opentelemetry.trace", fromlist=["StatusCode"]).StatusCode.ERROR,
                str(e)[:200],
            )
            raise


def _traced_stream(wrapped, instance, args, kwargs) -> Any:
    """Wrapper for messages.stream that adds OTEL tracing."""
    from pisama_auto._tracer import get_tracer

    tracer = get_tracer()
    model = kwargs.get("model", "unknown")
    span_name = f"gen_ai.chat.stream {model}"

    span = tracer.start_span(span_name)
    span.set_attribute("gen_ai.system", "anthropic")
    span.set_attribute("gen_ai.request.model", model)
    span.set_attribute("gen_ai.operation.name", "chat.stream")

    messages = kwargs.get("messages", [])
    span.set_attribute("gen_ai.request.messages_count", len(messages))

    try:
        result = wrapped(*args, **kwargs)
        # Stream result will be consumed by the caller; span ends when context exits
        return result
    except Exception as e:
        span.set_attribute("error.type", type(e).__name__)
        span.end()
        raise
