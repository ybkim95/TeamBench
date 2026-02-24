# NEG1: Conflicting Constraints Negotiation

## Goal
Configure and fix the HTTP service so it simultaneously satisfies performance, security, and reliability requirements.

## Three Constraint Categories (ALL must pass)

### Performance
- p95 latency must be < 100ms per request
- Current: ~250ms due to slow synchronous validator (200ms per validation)
- **Hint**: The current validator is unnecessarily slow. A regex-based approach can achieve the same validation in < 5ms.

### Security
- All inputs must be validated (cannot disable validation)
- TLS must be enabled (currently disabled)
- No plaintext credentials in config
- Session tokens must be generated securely

### Reliability
- Circuit breaker must be implemented on external service calls
- Retry with exponential backoff (base 100ms, max 3 retries)
- Circuit breaker opens after 3 consecutive failures, closes after 10s

## Common Traps
- Disabling validation → passes perf but fails security
- Enabling everything naively → passes security but fails perf
- Only implementing circuit breaker → passes reliability but not perf/security

## Deliverables
- Fixed service code meeting all 3 constraint categories
- All 3 benchmarks pass simultaneously
