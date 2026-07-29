"""OpenAI SDK auto-instrumentation patch -- compatibility shim.

The real implementation lives in ``pisama.auto.patches.openai_patch``. This
module *is* that module at runtime (same ``sys.modules`` swap as
``pisama_auto/_tracer.py`` -- see that module's docstring for the full
rationale).
"""

import sys

from pisama.auto.patches import openai_patch as _real_openai_patch
from pisama.auto.patches.openai_patch import *  # noqa: F401,F403
from pisama.auto.patches.openai_patch import (
    _traced_create,  # noqa: F401 -- static-analysis surface
)

sys.modules[__name__] = _real_openai_patch
