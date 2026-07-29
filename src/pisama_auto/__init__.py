"""Pisama Auto-Instrumentation -- compatibility shim.

As of 0.3.0, ``pisama-auto`` is a thin compatibility shim over ``pisama.auto``
(the ``auto`` submodule of the ``pisama`` package, published on PyPI as
``pisama>=0.6.0``). The auto-instrumentation implementation itself -- OTEL
tracer setup, the anthropic/openai monkeypatches -- now lives in
``pisama.auto``; every module in this distribution forwards to the
equivalent ``pisama.auto`` module so every import path this package has ever
publicly supported (``import pisama_auto``, ``from pisama_auto import
_tracer``, ``from pisama_auto.patches.anthropic_patch import
_traced_stream``, ...) keeps working unchanged, forever.

New code should prefer ``import pisama.auto`` directly. Both spellings are
fully supported and share the same underlying state -- this shim's
``_tracer`` and ``patches`` submodules are literal aliases for the
corresponding ``pisama.auto`` submodules (see the module docstrings there),
not independent copies -- so mixing ``pisama_auto`` and ``pisama.auto``
imports in the same process is safe.

Usage (unchanged):
    import pisama_auto
    pisama_auto.init(api_key="ps_...")

    # All subsequent LLM calls are automatically traced
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(...)  # <-- automatically traced

Plain ``import pisama_auto`` (and ``import pisama_auto.patches``) has always
been, and remains, free of the OTEL and wrapt dependencies -- neither
imports them at module level. Reaching further -- ``pisama_auto._tracer``,
``pisama_auto.patches.anthropic_patch``, ``.openai_patch``, or calling
``init()`` -- has always needed OTEL/wrapt installed; before 0.3.0 that was
guaranteed by this package's own hard dependencies, and since this package
now depends on bare ``pisama`` rather than ``pisama[auto]`` (see
CHANGELOG.md for why), it now needs them installed explicitly instead:
``pip install "pisama-auto[auto]"`` (this package's own passthrough extra)
or ``pip install "pisama[auto]"`` (identical effect, since the passthrough
just depends on it).

``__version__`` here forwards ``pisama.auto.__version__`` -- the version of
the auto-instrumentation *implementation* actually running (also the value
OTEL scope/resource metadata reports) -- which is deliberately decoupled
from this shim distribution's own release version (see CHANGELOG.md). Use
``importlib.metadata.version("pisama-auto")`` if you need the latter.
"""

from pisama.auto import __version__, init, is_initialized, logger

__all__ = ["__version__", "init", "is_initialized", "logger"]
