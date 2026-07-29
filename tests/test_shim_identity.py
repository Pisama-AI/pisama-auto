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
