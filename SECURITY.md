# Security Policy

## Reporting a vulnerability

If you've found a security issue in `pisama-auto`, please do **not**
open a public GitHub issue. Instead:

- Email **security@pisama.ai** with a description, reproducer, and
  the affected version.
- We'll acknowledge within 2 business days and aim to ship a fix or
  mitigation within 7 business days for high-severity issues.

## What counts as a security issue

- The auto-patcher modifying an LLM client library in a way that
  allows attacker-controlled trace data to alter request behavior.
- OTEL exporter leaking data to an unintended endpoint.
- Dependency vulnerabilities that affect the instrumentation surface.

## Supported versions

Only the latest 0.x release line is supported. When 1.0 ships we'll
document an LTS policy.

## Credit

We'll credit reporters in release notes unless you prefer to stay
anonymous.
