"""Pisama Auto-Instrumentation.

Zero-code instrumentation for LLM applications.
Automatically patches supported libraries to emit OTEL traces
that Pisama can analyze for failure detection.

Usage:
    import pisama_auto
    pisama_auto.init(api_key="ps_...")

    # All subsequent LLM calls are automatically traced
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(...)  # <-- automatically traced
"""

import logging
from typing import Optional

logger = logging.getLogger("pisama_auto")

_initialized = False


def init(
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    service_name: str = "pisama-auto",
    auto_patch: bool = True,
) -> None:
    """Initialize Pisama auto-instrumentation.

    Sets up OTEL tracing and patches supported LLM libraries to automatically
    emit traces that Pisama can analyze.

    Args:
        api_key: Pisama API key (ps_...). Also reads PISAMA_API_KEY env var.
        endpoint: Pisama OTEL ingestion endpoint. Also reads PISAMA_ENDPOINT env var.
            If not set, traces are generated locally but not exported.
        service_name: Service name for OTEL resource.
        auto_patch: If True, automatically patch all detected libraries.
    """
    global _initialized
    if _initialized:
        logger.debug("Pisama auto-instrumentation already initialized")
        return

    import os
    api_key = api_key or os.environ.get("PISAMA_API_KEY")
    endpoint = endpoint or os.environ.get("PISAMA_ENDPOINT")

    if not api_key:
        logger.warning(
            "No Pisama API key provided. Set PISAMA_API_KEY or pass api_key to init(). "
            "Traces will be generated but not exported."
        )

    # Set up OTEL tracer
    from ._tracer import setup_tracer
    setup_tracer(
        api_key=api_key,
        endpoint=endpoint,
        service_name=service_name,
    )

    # Auto-patch detected libraries
    if auto_patch:
        from .patches import patch_all
        patched = patch_all()
        if patched:
            logger.info(f"Pisama: auto-instrumented {', '.join(patched)}")
        else:
            logger.info("Pisama: initialized (no patchable libraries detected yet)")

    _initialized = True


def is_initialized() -> bool:
    """Check if Pisama auto-instrumentation is initialized."""
    return _initialized
