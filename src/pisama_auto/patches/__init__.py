"""Auto-patching for LLM libraries -- compatibility shim.

The real implementation lives in ``pisama.auto.patches``: ``patch``/
``patch_all`` below are that module's exact function objects (not copies),
and ``_patched``/``_PATCHABLE`` are that module's exact list/dict objects.
``patch_all()``/``patch()`` always resolve their own ``anthropic_patch``/
``openai_patch`` imports through the canonical ``pisama.auto.patches``
package path regardless of which name reaches them, so a plain re-export --
unlike ``pisama_auto/_tracer.py``, which needs the more aggressive
``sys.modules`` swap because its ``_tracer`` singleton is *reassigned*, not
mutated in place -- is enough here to keep ``_patched``/``_PATCHABLE``
observably identical however a caller reaches them.

Deliberately NOT doing the ``sys.modules`` swap here (unlike ``_tracer.py``)
also keeps this package's own ``__path__`` pointing at this shim's own
directory, so ``pisama_auto.patches.anthropic_patch`` and
``.openai_patch`` resolve to *this shim's own* forwarder files (which each
do the aggressive swap themselves) rather than bypassing them.
"""

import logging

from pisama.auto import patches as _real_patches
from pisama.auto.patches import _PATCHABLE, _patched, patch, patch_all  # noqa: F401

# See pisama_auto/__init__.py's module docstring (`logger` bullet): rebind
# this module's own `logger` name -- not the shared "pisama.auto"-registered
# object -- to `logging.getLogger("pisama_auto")`.
_real_patches.logger = logging.getLogger("pisama_auto")

__all__ = ["patch", "patch_all"]
