## What this changes

<!-- 1–3 sentences. What's different after this PR and why. -->

## Type

- [ ] New library patch
- [ ] Bug fix (patch missing a call path, span attribute wrong, etc.)
- [ ] API change
- [ ] Docs

## Checklist

- [ ] Clean-venv install works: `pip install .` in a fresh env,
      `pisama_auto.init(auto_patch=False)` succeeds.
- [ ] New patches register via `pisama_auto.patches.register(...)` and
      can be disabled via `auto_patch=False`.
- [ ] Spans emit `gen_ai.*` attributes per OTEL semantic conventions.
- [ ] No hard dep on the wrapped library — the patch skips cleanly
      when the library isn't installed.
- [ ] README patch matrix updated if a new library is added.

## Reproducer or before/after (for bug fixes)

```python
# Before: ...
# After: ...
```
