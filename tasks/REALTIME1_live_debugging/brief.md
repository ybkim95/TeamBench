# REALTIME1: Production Service Debugging

## Your Mission
A critical production service is failing intermittently. Debug and fix the issue while the system continues running.

## Available Information
- Live logs in `/workspace/logs/live.stream`
- System metrics in `/workspace/metrics/`
- Current configuration in `/workspace/config/`
- Application code in `/workspace/src/`

## Requirements
- Fix must be deployed without downtime
- Preserve all active user sessions
- Implement automatic rollback capability

## Success Metrics
- Error rate < 1%
- No service interruption
- Fix deployed within time limit