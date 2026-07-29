"""Anthropic SDK auto-instrumentation patch -- compatibility shim.

The real implementation lives in ``pisama.auto.patches.anthropic_patch``.
This module *is* that module at runtime (same ``sys.modules`` swap as
``pisama_auto/_tracer.py`` -- see that module's docstring for the full
rationale). Forwards every public name plus the private helpers
pisama-auto's own test suite imports directly: ``_traced_stream`` and
``_TracedStream`` (``tests/test_sdk_instrumentation.py`` imports both to
drive the stream wrapper outside of a real ``patch()`` call).
"""

import sys

from pisama.auto.patches import anthropic_patch as _real_anthropic_patch
from pisama.auto.patches.anthropic_patch import *  # noqa: F401,F403
from pisama.auto.patches.anthropic_patch import (  # noqa: F401 -- static-analysis surface
    _original_create,
    _original_stream,
    _traced_create,
    _traced_stream,
    _TracedStream,
)

sys.modules[__name__] = _real_anthropic_patch
