# Contributing to pisama-auto

Thanks for your interest in improving `pisama-auto`. This package
provides zero-code OTEL auto-instrumentation for LLM libraries so
agents emit traces that [Pisama](https://pisama.ai) can analyze.

## What we're looking for

- **New library patches** under `src/pisama_auto/patches/`. Each
  patched library should emit spans following the `gen_ai.*` OTEL
  semantic conventions.
- **Bug reports** with a minimal reproducer — especially cases where
  `auto_patch=True` misses a supported call path.
- **Documentation fixes** on the patch matrix and configuration
  options.

## What we're not looking for

- Patches that alter the wrapped library's observable behavior. The
  instrumentation must be transparent to the caller.
- Credentials or endpoints embedded in code. All config flows through
  environment variables.

## Development setup

```bash
git clone https://github.com/tn-pisama/pisama-auto.git
cd pisama-auto
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

Smoke test:

```bash
python -c "
import pisama_auto
pisama_auto.init(auto_patch=False)
assert pisama_auto.is_initialized()
print('OK')
"
```

## PR checklist

- [ ] New patches register via `pisama_auto.patches.register(...)` and
      can be disabled via `auto_patch=False`.
- [ ] Spans emit `gen_ai.*` attributes per the OTEL semantic conventions.
- [ ] No hard dependency on the library being patched — the patch
      should be skipped cleanly if the library isn't installed.
- [ ] README patch matrix updated if a new library is added.

## Licensing and contributor grant

By submitting a PR you agree that your contribution is licensed under
MIT, the same license as this repo.

## Questions

Open a GitHub Discussion or visit [pisama.ai](https://pisama.ai).
