# Contributing

Keep security claims reproducible and evaluation splits honest.

- Add tests for behavior changes.
- Run lint, type checks, the full pytest suite, and benchmark scripts affected by your change.
- Do not mix training and evaluation examples or move OOD fixtures into any training corpus.
- Public F1/precision/recall numbers must name the split, seed, fixture source, and claim boundary.
- If methodology changes, invalidate old exact metrics until CI regenerates comparable evidence.

Report security-sensitive issues through [SECURITY.md](SECURITY.md), not a public issue.
