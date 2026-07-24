# Changelog

## Unreleased

- Add protocol-level tests against the real OpenAI and Anthropic Python clients.
- Enforce at least 95 percent statement coverage in CI.
- Add CodeQL and pull request dependency review.
- Recommend `pisama[auto]` as the canonical installation path while preserving
  direct `pisama-auto` compatibility.
- Report the package version consistently in OpenTelemetry resource and scope
  metadata.
- Add typed-package metadata, type checking, exporter contract coverage, and a
  built-wheel smoke test.

## 0.2.0

- Add automatic Anthropic and OpenAI instrumentation.
- Add Pisama platform export with short-lived token exchange.
- Add local-only operation when no API key is configured.
- Add Python 3.10 through 3.13 consumer and release checks.
