# Security Policy

## Supported Versions
Security fixes target the default branch.

## Reporting a Vulnerability
Report vulnerabilities privately to poojakiranbhardwaj@gmail.com. Include affected commit, reproduction steps, and impact.

## Notes
This project is an offline research framework. It does not call live LLM APIs. Detector persistence uses Python pickle and must only load artifacts created by the user with `trusted=True`.