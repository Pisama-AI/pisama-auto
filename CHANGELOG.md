# Changelog

## Unreleased

## 0.3.0

`pisama-auto` becomes a compatibility shim over `pisama.auto`.

The auto-instrumentation implementation that used to live in this
distribution (OTEL tracer setup, the anthropic/openai monkeypatches) is now
original code inside the `pisama` package, at `pisama.auto` (published as
`pisama>=0.6.0`). Nothing here was unpublished -- 0.1.0 through 0.2.0 stay on
PyPI as historical releases with their standalone implementation intact.
This release replaces that implementation with thin forwarders so every
import path this package has ever publicly supported keeps working, forever,
with identical behavior:

- `pisama_auto` re-exports `init`, `is_initialized`, `__version__`, `logger`
  from `pisama.auto` by reference (same function/value objects).
  `logger` additionally carries a name fix: `pisama.auto` and everything
  reached through it log via `logging.getLogger("pisama.auto")` internally,
  but every `pisama-auto` release from 0.1.0 through 0.2.0 used
  `logging.getLogger("pisama_auto")` (flat, no dot) -- the name existing
  callers configure by (`logging.getLogger("pisama_auto").setLevel(...)`).
  Each of the five internal modules' own `logger` name binding is
  *reassigned* (not the shared `"pisama.auto"`-registered `Logger` object
  itself, which is never renamed or otherwise mutated) to point at
  `logging.getLogger("pisama_auto")` instead -- the same "swap what the
  name resolves to, not what the object is" idea already applied to the
  `_tracer` singleton below, via plain attribute assignment rather than a
  full `sys.modules` swap. Since every internal call site resolves `logger`
  as a global against its own module's namespace at call time, this
  redirects what every `LogRecord` any of the five modules emits reports,
  without needing to wrap or copy those functions. `logging.getLogger` is
  idempotent, so this works regardless of whether a caller configures
  `"pisama_auto"` before or after `import pisama_auto`, and never clobbers
  a pre-existing `"pisama_auto"` logger -- and a bare, non-shim
  `import pisama.auto` caller is completely unaffected by whether
  `pisama_auto` also happens to be imported elsewhere in the same process,
  since the real `"pisama.auto"`-registered object is never touched.
  (An earlier version of this fix instead renamed the shared object in
  place and force-registered it under `"pisama_auto"` in the stdlib
  registry -- simple, but it silently orphaned any handler a caller had
  already attached to a pre-existing `"pisama_auto"` logger, and mutated
  the real `pisama.auto` object process-wide even for callers who never
  touch this shim. See the `logger` bullet in `pisama_auto/__init__.py`'s
  module docstring for the full mechanism.)
  `_initialized` gets an analogous fix: it's a live view onto
  `pisama.auto._initialized` (via a `ModuleType.__class__` swap on this
  module, since `pisama.auto` itself can't be aliased wholesale the way
  `_tracer`/the patch leaves are -- see the module docstring), so
  `pisama_auto._initialized = False` followed by `init()` genuinely
  reinitializes instead of silently no-opping.
- `pisama_auto._tracer`, `pisama_auto.patches.anthropic_patch`, and
  `pisama_auto.patches.openai_patch` are now literal aliases for their
  `pisama.auto` equivalents (a `sys.modules` swap to the same module
  object) -- not copies. This matters for the handful of module-level
  globals those specific modules *reassign* rather than mutate in place
  (the tracer singleton, in particular): a plain re-export would let
  `pisama_auto`'s copy silently drift from the state `pisama.auto`'s own
  functions actually read and write. `pisama_auto.patches` itself stays a
  distinct module object re-exporting `patch`/`patch_all`/`_patched`/
  `_PATCHABLE` by reference (sufficient here since those are mutated in
  place, not reassigned) so that its own `__path__` keeps pointing at this
  shim's own `anthropic_patch.py`/`openai_patch.py` files rather than
  short-circuiting past them. Either way, this forwards the private helpers
  this package's own test suite imports directly (`_traced_stream`,
  `_TracedStream`, `_tracer`, `_patched`, `_PATCHABLE`, ...), so mixing
  `import pisama_auto` and `import pisama.auto` in the same process is safe.
- **Dependencies changed.** `dependencies` is now just `["pisama>=0.6.0"]` --
  the direct `opentelemetry-*`/`wrapt` pins are dropped; that functionality
  now lives behind `pisama`'s own `auto` extra. This package never depends
  on `pisama[auto]` (or `pisama[agents]`) directly -- only on bare `pisama`
  -- to keep the dependency graph a DAG: an extra of the package this shim
  forwards to is exactly the shape a real cycle would take. Instead, this
  release adds `pisama-auto[auto]` as an optional passthrough extra
  (`pisama[auto]>=0.6.0`), so **`pip install "pisama-auto[auto]"`** is the
  fewest-surprises way to keep getting a fully functional `init()`,
  equivalent to `pip install "pisama[auto]"` (recommended for new code).
  `pip install pisama-auto` (bare) still gets you `import pisama_auto` and
  `import pisama_auto.patches` working exactly as they always have (neither
  ever needed OTEL/wrapt at import time). `pisama_auto._tracer` and
  `pisama_auto.patches.anthropic_patch`/`.openai_patch` specifically *have*
  always needed OTEL/wrapt -- before 0.3.0 that was guaranteed by this
  package's own hard dependencies; now, like calling `init()` itself, it
  needs the `auto` extra installed instead, and raises `ImportError` (not
  a silent gap) if it isn't.
- **`__version__` now means something narrower.** It forwards
  `pisama.auto.__version__` -- the auto-instrumentation implementation
  version actually running, which is also what OTEL scope/resource metadata
  reports -- rather than this shim distribution's own release version (a
  distinction that didn't exist before there were two numbers). Use
  `importlib.metadata.version("pisama-auto")` for the distribution version.
  CI's built-wheel and release smoke tests, which previously asserted
  `pisama_auto.__version__ == <packaged/tagged version>` (added in 0.2.1
  specifically to catch the two drifting apart), are updated accordingly:
  they now check the distribution version via `importlib.metadata`
  independently, rather than through `__version__`.
- CI (`ci.yml`, `publish.yml`) installs `.[auto]` (or `.[dev]`, which now
  pulls `auto` in transitively via a self-referential extra) wherever it
  needs a working `init()`, and separately verifies a bare install still
  gives a working `import pisama_auto` -- so it exercises both the
  always-worked-before path and the newly-explicit opt-in path, instead of
  silently only covering one.

## 0.2.1

- Correct the README description of the detection step. It previously claimed
  Pisama analyzed traces for "50 failure modes", a number that matches no detector
  set in the project. `pisama-auto` is an OTLP auto-instrumentation shim: it patches
  supported LLM clients and exports spans, and implements no detectors of its own.
  The step now describes the behavior without asserting a count.
- Fix the built-wheel CI check, which hardcoded `assert pisama_auto.__version__ ==
  '0.2.0'` and so failed on every version bump, requiring a workflow edit per
  release. It now compares `__version__` against the installed distribution
  metadata, which is the actual intent (catching drift between the two) and is
  version-agnostic.

## 0.2.0

- Add protocol-level tests against the real OpenAI and Anthropic Python clients.
- Enforce at least 96 percent statement coverage in CI.
- Add CodeQL and pull request dependency review.
- Recommend `pisama[auto]` as the canonical installation path while preserving
  direct `pisama-auto` compatibility.
- Report the package version consistently in OpenTelemetry resource and scope
  metadata.
- Add typed-package metadata, type checking, exporter contract coverage, and a
  built-wheel smoke test.
- Add automatic Anthropic and OpenAI instrumentation.
- Add Pisama platform export with short-lived token exchange.
- Add local-only operation when no API key is configured.
- Add Python 3.10 through 3.13 consumer and release checks.
