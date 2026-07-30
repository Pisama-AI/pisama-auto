"""Shim-specific tests: prove pisama_auto really forwards to pisama.auto.

The rest of tests/ is pisama-auto's original test suite, carried over
unmodified to prove *behavioral* identity (same assertions, same results,
now running against the shim). This file adds coverage the mirrored suite
never needed before there were two packages: that every pisama_auto import
path actually resolves to -- not just resembles -- its pisama.auto
equivalent, including the module-level mutable state a plain re-export
would silently fail to share (see pisama_auto/_tracer.py's docstring).
"""
from __future__ import annotations

import logging
import subprocess
import sys
import textwrap

import pisama.auto
import pisama.auto._tracer
import pisama.auto.patches
import pisama.auto.patches.anthropic_patch
import pisama.auto.patches.openai_patch

import pisama_auto
import pisama_auto._tracer
import pisama_auto.patches
import pisama_auto.patches.anthropic_patch
import pisama_auto.patches.openai_patch


def test_tracer_and_patch_submodules_are_the_same_module_object():
    """`_tracer.py` and the two patch leaves alias pisama.auto's modules
    outright (sys.modules swap) -- `is`, not just `==`."""
    assert pisama_auto._tracer is pisama.auto._tracer
    assert pisama_auto.patches.anthropic_patch is pisama.auto.patches.anthropic_patch
    assert pisama_auto.patches.openai_patch is pisama.auto.patches.openai_patch


def test_patches_package_shares_state_by_reference_without_a_full_swap():
    """`patches/__init__.py` deliberately stays its own module object (see
    its docstring) so its own __path__ still finds this shim's leaf files --
    but _patched/_PATCHABLE must still be the exact same list/dict."""
    assert pisama_auto.patches is not pisama.auto.patches
    assert pisama_auto.patches._patched is pisama.auto.patches._patched
    assert pisama_auto.patches._PATCHABLE is pisama.auto.patches._PATCHABLE
    assert pisama_auto.patches.patch is pisama.auto.patches.patch
    assert pisama_auto.patches.patch_all is pisama.auto.patches.patch_all


def test_top_level_functions_and_version_are_forwarded_by_reference():
    assert pisama_auto.init is pisama.auto.init
    assert pisama_auto.is_initialized is pisama.auto.is_initialized
    assert pisama_auto.logger is pisama.auto.logger
    assert pisama_auto.__version__ == pisama.auto.__version__


def test_tracer_reassignment_is_observed_through_either_import_path():
    """The specific hazard a plain re-export would miss: `_tracer` is
    *reassigned* (not mutated in place) by setup_tracer()/get_tracer(). A
    write through one name must be visible by reading the other."""
    previous = pisama.auto._tracer._tracer
    try:
        sentinel = object()
        pisama_auto._tracer._tracer = sentinel
        assert pisama.auto._tracer._tracer is sentinel
        assert pisama.auto._tracer.get_tracer() is sentinel

        pisama.auto._tracer._tracer = None
        assert pisama_auto._tracer.get_tracer() is pisama_auto._tracer.get_tracer()
    finally:
        pisama.auto._tracer._tracer = previous


def test_logger_resolves_by_its_historical_flat_name(monkeypatch):
    """Every pisama-auto release from 0.1.0 through 0.2.0 logged through
    ``logging.getLogger("pisama_auto")`` (flat name, no dot) -- the name
    existing callers configure by (``.setLevel(...)``, ``.addHandler(...)``).
    ``pisama.auto`` and everything reached through it internally logs
    through ``logging.getLogger("pisama.auto")`` instead; identity alone
    (``pisama_auto.logger is pisama.auto.logger``) doesn't prove the
    *name* the caller configures by is right -- only a real emitted
    LogRecord does.

    This is the "post-import" ordering: ``pisama_auto`` is already imported
    (at this file's module level, above) by the time the handler below is
    attached. See ``test_pre_existing_pisama_auto_logger_survives_import_
    ordering`` below for the other ordering -- a caller who configures
    logging *before* ``import pisama_auto`` runs -- which needs a fresh
    interpreter to test meaningfully and is exactly the ordering the old
    ``logger.name = "pisama_auto"`` fix silently broke.
    """
    assert pisama_auto.logger.name == "pisama_auto"
    assert logging.getLogger("pisama_auto") is pisama_auto.logger

    monkeypatch.delenv("PISAMA_API_KEY", raising=False)
    monkeypatch.delenv("PISAMA_ENDPOINT", raising=False)

    records: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _Capture()
    previous_level = pisama_auto.logger.level
    previous_initialized = pisama.auto._initialized
    pisama_auto.logger.addHandler(handler)
    pisama_auto.logger.setLevel(logging.DEBUG)
    try:
        # Force a real (re-)initialization so pisama.auto.init()'s internal
        # `logger.warning(...)` call -- a real call into pisama.auto's
        # internal code, reached only through the pisama_auto import path --
        # actually fires.
        pisama_auto._initialized = False
        pisama_auto.init(service_name="logger-name-probe", auto_patch=False)
    finally:
        pisama_auto.logger.removeHandler(handler)
        pisama_auto.logger.setLevel(previous_level)
        pisama.auto._initialized = previous_initialized

    assert records, "no LogRecord captured"
    assert all(r.name == "pisama_auto" for r in records)


def test_initialized_flag_round_trips_through_the_shim(monkeypatch):
    """``pisama_auto._initialized = False`` must reach the real
    ``pisama.auto._initialized`` global that ``init()``/``is_initialized()``
    actually read -- not just set a stray attribute in this module's own
    ``__dict__``. Proven via a side effect a genuine no-op second ``init()``
    call does not produce: ``setup_tracer()`` only runs when ``init()``
    actually (re)initializes.
    """
    monkeypatch.delenv("PISAMA_API_KEY", raising=False)
    monkeypatch.delenv("PISAMA_ENDPOINT", raising=False)

    calls: list[object] = []
    original_setup_tracer = pisama_auto._tracer.setup_tracer

    def _counting_setup_tracer(*args, **kwargs):
        calls.append((args, kwargs))
        return original_setup_tracer(*args, **kwargs)

    monkeypatch.setattr(pisama_auto._tracer, "setup_tracer", _counting_setup_tracer)

    previous = pisama.auto._initialized
    try:
        pisama_auto._initialized = False
        # The write above must be visible on the real global, not just on
        # this module's own namespace -- and reading it back *through the
        # shim* (not just via pisama.auto directly) must also see it.
        assert pisama.auto._initialized is False
        assert pisama_auto._initialized is False
        assert not pisama_auto.is_initialized()

        pisama_auto.init(service_name="round-trip-1", auto_patch=False)
        assert pisama_auto._initialized is True
        assert pisama_auto.is_initialized()
        assert len(calls) == 1, "first call after a real reset must actually initialize"

        pisama_auto.init(service_name="round-trip-1-ignored", auto_patch=False)
        assert len(calls) == 1, "second call while still initialized must be a genuine no-op"

        # The exact idiom the package's own (unmodified) test suite uses to
        # reset state between test runs.
        pisama_auto._initialized = False
        pisama_auto.init(service_name="round-trip-2", auto_patch=False)
        assert pisama_auto._initialized is True
        assert pisama_auto.is_initialized()
        assert len(calls) == 2, (
            "reset-then-init did not actually reinitialize -- silent no-op regression"
        )
    finally:
        pisama.auto._initialized = previous


def _run_isolated(script: str) -> subprocess.CompletedProcess:
    """Run ``script`` in a brand-new interpreter with a clean logging
    registry and no ambient Pisama env vars.

    Both ordering proofs below are meaningless inside this test process:
    pytest has already imported ``pisama_auto`` (and ``pisama.auto``) at
    collection time, above, so there is no "before import" left to
    observe here. A fresh subprocess is the only way to actually exercise
    import order.
    """
    import os

    env = dict(os.environ)
    env.pop("PISAMA_API_KEY", None)
    env.pop("PISAMA_ENDPOINT", None)
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def test_pre_existing_pisama_auto_logger_survives_import_ordering():
    """The "before import" ordering the old fix broke: a caller who runs
    ``logging.config.dictConfig(...)`` (or any other pre-configuration) on
    ``"pisama_auto"`` *before* ``import pisama_auto`` -- the standard
    configure-then-import app-startup pattern -- must keep that exact
    Logger object, with its handlers/level/propagate untouched, and it
    must actually capture a real internal log record once ``init()`` runs.

    The old ``logging.Logger.manager.loggerDict["pisama_auto"] = logger``
    line unconditionally overwrote whatever was already registered there,
    silently orphaning this caller's handler.
    """
    result = _run_isolated(
        """
        import logging
        import logging.config

        captured = []

        class Capture(logging.Handler):
            def emit(self, record):
                captured.append(record)

        handler = Capture()
        logging.config.dictConfig({
            "version": 1,
            "disable_existing_loggers": False,
            "loggers": {"pisama_auto": {"level": "DEBUG", "propagate": False}},
        })
        pre_logger = logging.getLogger("pisama_auto")
        pre_logger.addHandler(handler)
        pre_handlers = list(pre_logger.handlers)
        pre_level = pre_logger.level
        pre_propagate = pre_logger.propagate
        assert pre_level == logging.DEBUG
        assert pre_propagate is False

        import pisama_auto

        assert pisama_auto.logger is pre_logger, "pre-configured Logger object was replaced"
        assert pisama_auto.logger.handlers == pre_handlers, "handlers lost"
        assert pisama_auto.logger.level == pre_level == logging.DEBUG
        assert pisama_auto.logger.propagate is pre_propagate is False

        pisama_auto._initialized = False
        pisama_auto.init(service_name="pre-import-probe", auto_patch=False)

        assert captured, "no LogRecord captured by the pre-existing handler"
        assert all(r.name == "pisama_auto" for r in captured)
        print("OK")
        """
    )
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "OK" in result.stdout


def test_bare_pisama_auto_reference_is_never_mutated_by_shim_import():
    """A caller who only ever does ``import pisama.auto`` (never touches
    the shim) must be completely unaffected by ``pisama_auto`` also being
    imported elsewhere in the same process: the old
    ``logger.name = "pisama_auto"`` line renamed the *shared* Logger
    object in place, so a bare caller's own reference silently started
    reporting ``.name == "pisama_auto"`` through no action of their own.
    """
    result = _run_isolated(
        """
        import logging
        import pisama.auto

        bare_ref = pisama.auto.logger
        bare_id_before = id(bare_ref)
        assert bare_ref.name == "pisama.auto"

        import pisama_auto  # elsewhere in the process

        assert bare_ref.name == "pisama.auto", (
            f"cross-contamination: bare_ref.name mutated to {bare_ref.name!r}"
        )
        assert id(bare_ref) == bare_id_before

        fresh = logging.getLogger("pisama.auto")
        assert fresh is bare_ref
        assert fresh.name == "pisama.auto"
        assert pisama_auto.logger is not bare_ref
        assert pisama_auto.logger.name == "pisama_auto"
        print("OK")
        """
    )
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "OK" in result.stdout
