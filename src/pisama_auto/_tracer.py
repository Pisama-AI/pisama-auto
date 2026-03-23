"""OTEL tracer setup for Pisama auto-instrumentation."""

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger("pisama_auto")

_tracer: Optional[trace.Tracer] = None


def setup_tracer(
    api_key: Optional[str] = None,
    endpoint: str = "https://mao-api.fly.dev/api/v1/traces/ingest",
    service_name: str = "pisama-auto",
) -> trace.Tracer:
    """Set up the OTEL tracer with Pisama exporter."""
    global _tracer

    resource = Resource.create({
        "service.name": service_name,
        "pisama.sdk": "pisama-auto",
        "pisama.sdk.version": "0.1.0",
    })

    provider = TracerProvider(resource=resource)

    if api_key:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            exporter = OTLPSpanExporter(
                endpoint=endpoint,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.debug(f"Pisama OTEL exporter configured: {endpoint}")
        except ImportError:
            logger.warning("OTLP exporter not available, using console exporter")
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        # No API key — still trace locally for debugging
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("pisama_auto", "0.1.0")
    return _tracer


def get_tracer() -> trace.Tracer:
    """Get the Pisama tracer. Sets up a default if not initialized."""
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer("pisama_auto", "0.1.0")
    return _tracer
