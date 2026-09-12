# REALTIME1: Live System Debugging with Evolving State

## Context
A production web service is experiencing intermittent failures. The system state changes every 30 seconds as new requests arrive and background jobs execute. Your team must diagnose and fix the issue while the system continues to run.

## System Architecture
- API Gateway (port 8080)
- Application Server (port 3000)
- Cache Layer (Redis, port 6379)
- Database (PostgreSQL, port 5432)
- Message Queue (RabbitMQ, port 5672)

## Live Monitoring Feed
The system provides real-time logs in `/workspace/logs/live.stream` that update every 5 seconds with new events. Error patterns change based on system load and time of day.

## Critical Constraints
1. **No Downtime**: The fix must be deployed without stopping the service
2. **State Preservation**: Current user sessions must not be disrupted
3. **Rollback Ready**: Solution must include automatic rollback on failure

## The Problem
Users report that approximately 15% of API requests are failing with 500 errors, but the pattern is non-deterministic. The errors started 2 hours ago after a deployment.

## Hidden Information (Planner Only)
The actual root cause is a race condition in the connection pool manager that only manifests when:
1. Connection pool size exceeds 80% capacity
2. A background job triggers database maintenance
3. New connections are requested within a 100ms window

The fix requires:
1. Implementing exponential backoff in the connection retry logic
2. Adding a circuit breaker pattern to the pool manager
3. Configuring pool overflow handling to queue rather than fail

## Executor Traps
- The obvious solution (increasing pool size) will make the problem worse
- Restarting services will temporarily fix it but cause data loss
- The error messages are misleading - they point to timeout issues but it's actually a race condition

## Real-Time Events
Every 30 seconds, the system will inject new events:
- T+0: Normal traffic
- T+30: Spike in connections (triggers race condition)  
- T+60: Background job starts
- T+90: Error rate increases to 25%
- T+120: Auto-scaling triggers (makes it worse)
- T+150: Circuit breaker opportunity window
- T+180: System stabilizes if fix is correct

## Success Criteria
1. Error rate reduced to < 1% within 3 minutes
2. No service interruption during fix deployment  
3. Solution handles future traffic spikes
4. Monitoring alerts configured for early detection
5. Runbook created for incident response

## Verification Requirements
The Verifier must confirm:
- Live metrics show error rate below threshold
- No user sessions were terminated
- Rollback mechanism is tested and functional
- Performance degradation < 5%
- All components remain healthy during fix

## Note on Timing
This task simulates real-time pressure. The Executor has a maximum of 10 turns to implement the fix before the system enters critical failure mode where recovery becomes much harder.