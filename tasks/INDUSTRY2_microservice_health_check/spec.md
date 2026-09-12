# INDUSTRY2: Microservice Health Check System

## Business Problem
Your microservices architecture needs comprehensive health monitoring to:
- Detect service degradation before user impact
- Enable automatic failover and load balancing
- Provide operational visibility for SRE teams
- Meet 99.9% SLA requirements

## Current Architecture
```
[Load Balancer] → [API Gateway] → [User Service]
                                → [Order Service] 
                                → [Payment Service]
                                → [Inventory Service]
```

Each service needs:
- Health check endpoint
- Dependency health monitoring  
- Circuit breaker pattern
- Metrics collection

## Requirements

### Health Check Levels
1. **Basic Health** (`/health`): Service is running
2. **Readiness** (`/health/ready`): Ready to serve traffic
3. **Liveness** (`/health/live`): Process is healthy
4. **Deep Health** (`/health/deep`): All dependencies healthy

### Response Format
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2025-03-29T10:30:00Z",
  "version": "1.2.3",
  "uptime_seconds": 3600,
  "dependencies": {
    "database": {"status": "healthy", "latency_ms": 15},
    "redis": {"status": "healthy", "latency_ms": 2},
    "payment_api": {"status": "degraded", "latency_ms": 500}
  },
  "metrics": {
    "requests_per_second": 150,
    "error_rate_percent": 0.1,
    "memory_usage_percent": 45
  }
}
```

## Implementation Guide (Planner Only)

### Core Components
1. **HealthChecker** class with dependency management
2. **CircuitBreaker** for dependency calls
3. **MetricsCollector** for performance data
4. **HealthEndpoints** Flask/FastAPI routes

### Dependency Monitoring
- Database: Connection pool status + query latency
- External APIs: Response time + error rate
- Message queues: Connection + queue depth
- File systems: Disk space + access

### Circuit Breaker Logic
- Open: Fail fast when dependency consistently fails
- Half-open: Periodic probe attempts
- Closed: Normal operation
- Configurable failure thresholds and timeouts

### Health Status Determination
```python
def determine_health(dependencies):
    critical_down = any(dep.status == "unhealthy" for dep in critical_deps)
    if critical_down:
        return "unhealthy"
    
    degraded = any(dep.status == "degraded" for dep in all_deps)
    return "degraded" if degraded else "healthy"
```

## Business Value
- **Reduced MTTR**: Faster incident detection and resolution
- **Higher Availability**: Proactive failover before total failure
- **Cost Savings**: Prevent cascade failures, optimize resource usage
- **Customer Trust**: Transparent service status, fewer outages

## Industry Standards
- Kubernetes health probes compatibility
- Prometheus metrics integration
- OpenTelemetry tracing support
- 12-factor app methodology

## Success Criteria
- Health endpoints respond < 100ms
- Accurate dependency status reporting
- Circuit breakers prevent cascade failures
- Metrics help predict issues
- Load balancers integrate properly