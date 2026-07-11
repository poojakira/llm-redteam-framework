# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-11

### Added
- Six prompt mutators, each covering a distinct jailbreak tactic: direct override,
  role switch, context escape, indirect embedding, character obfuscation (l33tspeak,
  ROT13, Base64), and multi-step (multi-turn) attacks.
- `AdversarialDetector`: an offline TF-IDF + logistic-regression classifier with
  `train`, `predict`, `predict_proba`, `auc`, and pickle-based `save`/`load`.
- `RedTeamGenerator`: orchestrates all mutators, produces labelled datasets, and reads
  seeds from file.
- Seed data: 50 benign prompts and 50 research-safe adversarial seed patterns.
- 15 tests, including the `AUC > 0.85` detector guarantee on synthetic data.
- Continuous integration across Python 3.10-3.12.
