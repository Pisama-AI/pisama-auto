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

Two more names carry live-identity guarantees beyond a plain re-export, for
the same reason ``_tracer.py`` documents its ``sys.modules`` swap: a plain
copy would let this shim silently drift from the state ``pisama.auto`` (and
every module reached through it) actually reads and writes.

* ``logger`` -- ``pisama.auto`` and every submodule reached through this
  shim (``_tracer``, ``patches``, ``patches.anthropic_patch``,
  ``patches.openai_patch``) each call ``logging.getLogger("pisama.auto")``;
  the stdlib logging registry hands back the exact same ``Logger`` object
  for every call with that name, so all five already share this one object.
  But every ``pisama-auto`` release from 0.1.0 through 0.2.0 used
  ``logging.getLogger("pisama_auto")`` (flat, no dot -- unrelated to any
  ``"pisama"`` parent hierarchy), which is the name existing callers
  configure by (``logging.getLogger("pisama_auto").setLevel(...)``,
  ``.addHandler(...)``). Below, the shared object is renamed in place
  (``Logger.debug``/``.info``/``.warning`` read ``self.name`` fresh on every
  call, so this changes what every future ``LogRecord`` from any of the five
  modules reports) and registered under that historical name in the stdlib
  registry, so ``logging.getLogger("pisama_auto") is pisama_auto.logger``
  and every record any of them emits carries ``.name == "pisama_auto"``.
* ``_initialized`` -- a plain module-level bool in ``pisama.auto``,
  *rebound* (not mutated) by ``init()``. Unlike ``_tracer``/the patch
  leaves, ``pisama.auto`` can't be swapped wholesale into
  ``sys.modules[__name__]`` to share one namespace: that would also hijack
  this package's own ``__path__``, silently routing ``pisama_auto.patches``
  to ``pisama.auto.patches`` instead of this shim's own forwarder files
  (see ``patches/__init__.py``'s docstring for the identical hazard one
  level down, already avoided there). So it's wired directly instead: this
  module's ``__class__`` is reassigned to a ``ModuleType`` subclass with a
  ``_initialized`` property, turning both reads and writes of
  ``pisama_auto._initialized`` into direct reads/writes of
  ``pisama.auto._initialized`` -- a live view, not a snapshot -- so
  ``pisama_auto._initialized = False`` followed by ``init()`` genuinely
  reinitializes instead of silently no-opping.
"""

import logging
import sys
import types

import pisama.auto as _pisama_auto
from pisama.auto import __version__, init, is_initialized, logger

logger.name = "pisama_auto"
logging.Logger.manager.loggerDict["pisama_auto"] = logger


class _ShimModule(types.ModuleType):
    """See the ``_initialized`` bullet in the module docstring above."""

    @property
    def _initialized(self) -> bool:
        return _pisama_auto._initialized

    @_initialized.setter
    def _initialized(self, value: bool) -> None:
        _pisama_auto._initialized = value


sys.modules[__name__].__class__ = _ShimModule

__all__ = ["__version__", "init", "is_initialized", "logger"]
