"""OTEL tracer setup for Pisama auto-instrumentation -- compatibility shim.

The real implementation lives in ``pisama.auto._tracer``. This module *is*
that module at runtime, not a copy of its names: the final line below
replaces this module's entry in ``sys.modules`` with the real one.

Why the aggressive swap (rather than plain ``from pisama.auto._tracer import
name1, name2, ...``, as used elsewhere in this shim): the module-level
``_tracer`` singleton is *reassigned* (not mutated in place) by
``setup_tracer()``/``get_tracer()``, and pisama-auto's own test suite
reassigns it directly too (``_tracer._tracer = provider.get_tracer(...)`` in
``captured_spans``). A plain re-export would copy today's value once at
import time and never see later reassignments from either side -- the two
modules' ``_tracer`` globals would silently diverge, and the tracer that
``anthropic_patch``/``openai_patch`` actually emit spans through (they
always resolve ``get_tracer`` via the canonical ``pisama.auto._tracer``
path) would stop matching whatever a caller reads or sets via
``pisama_auto._tracer``. The ``sys.modules`` swap makes both import paths
resolve to one module object, so there is exactly one ``_tracer`` global,
observed and mutated identically either way.

The ``from pisama.auto._tracer import *`` plus the explicit private-name
import below exist purely so static analysis (mypy, IDEs) sees a real,
concrete export list for this module; they have no runtime effect beyond
that, since the swap below replaces this module's whole namespace before
any caller can observe it.
"""

import sys

from pisama.auto import _tracer as _real_tracer
from pisama.auto._tracer import *  # noqa: F401,F403
from pisama.auto._tracer import (
    _tracer,  # noqa: F401 -- private, but the test suite pokes at it
)

sys.modules[__name__] = _real_tracer
