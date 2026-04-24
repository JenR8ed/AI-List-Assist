# Legacy Quarantine

This folder contains deprecated and non-production files moved out of the repository root to reduce accidental usage.

## What belongs here
- One-off patch scripts
- Ad-hoc manual test scripts
- Temporary PR description artifacts

## Policy
- Do not import from this folder in runtime code.
- If a file is needed again, copy it back intentionally and refactor it before reuse.
- Prefer replacing these artifacts with tested code under `services/`, `tests/`, or other active project paths.
