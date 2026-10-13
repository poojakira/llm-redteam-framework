# Local verification — 2026-10-13

Status: PARTIALLY COMPLETE. Independent functional review performed by a separate agent; remote CI, Docker, exhaustive file-by-file review, dependency vulnerability scans, and poster regeneration are not established by these local tests.

- Starting revision: `b6e46b157a22b63bd1427bd4baaf0d2a38bdd40d` plus the remediation diff committed with this record.
- Environment: Linux, Python 3.12.14, pytest 9.1.1, pytest-cov 7.1.0, coverage 7.16.2.
- Local suite: **184 passed, 1 skipped**.
- Statement coverage: **94.2636% (1216/1290)**; not branch coverage.
- Command: `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest --cov=redteam --cov-report=term --cov-report=json`.
- UTC execution date: 2026-10-13. Exact start time was not captured; do not infer it from commit time.
- No production traffic or external paid services were used. No effectiveness benchmark was rerun.

## Remediation

Live endpoint transport and response-schema failures now produce ERROR with a separate errors count. Compliance rate uses successful model responses only; reports with only errors have rate 0.0 and must be interpreted with errors/total. Error strings retain exception class without embedding potentially sensitive transport messages. Null/empty/nontext content is an error.

## Evidence limitations

Full test logs and coverage JSON were retained in the audit execution workspace. This document records their summary; it does not claim CI passed on this revision. Existing dated benchmark artifacts and posters remain historical snapshots, not current reruns. See [historical runs](../previos_runs.md).
