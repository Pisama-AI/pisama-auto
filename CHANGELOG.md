# Changelog

## Unreleased

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
