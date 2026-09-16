# Security configuration

## API authentication

Protected API endpoints fail closed when `REDTEAM_API_KEY` is missing.

- `/scan`: requires `X-API-Key`
- `/metrics`: requires `X-API-Key`
- `/health`: liveness endpoint, intentionally unauthenticated
- missing secret at startup/configuration time: protected requests return HTTP 401
- wrong or missing key: HTTP 401
- key comparison: constant-time `hmac.compare_digest`

There is no anonymous production mode. Local development should set an
explicit development-only key.

## Rate limiting

The `/scan` endpoint uses an in-memory per-IP sliding window. This is a local
process control and is not a distributed rate limiter. Deployments with
multiple replicas should place a shared rate-limit control in front of the
service.

## Scope

The framework is primarily an offline evaluation and red-team harness. Its
`blocked` response is a detector verdict, not proof that an arbitrary downstream
LLM or agent is secure. Production enforcement requires integrating the verdict
at the actual tool/agent execution boundary.
