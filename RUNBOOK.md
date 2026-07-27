# Runbook

## Engineering Update - 2026-07-27

Repository: llm-redteam-framework
Purpose: Offline LLM red-team detection framework

## Build

- Install: make install
- Lint: make lint
- Format: make format
- Test: make test
- Package build: make build
- Security scan: make security
- Full local gate: make verify

## Dashboard

Static 3D dashboard: dashboard/index.html. Serve with make dashboard.

## Dependencies And Data

Uses ATT&CK mapping builder and canonical v19 technique IDs.

## Validation Snapshot

Validated: Ruff checks passed for mapping/test scope; attack mapping tests passed; dashboard JS syntax/static checks passed.

## Operating Limits

- Re-check Linux and GitHub Actions after pushing to main.
- Treat local dashboard scores as evidence indicators, not certifications.
- Do not cite production readiness until clean CI, dependency audit, license status, and runtime smoke tests are current.