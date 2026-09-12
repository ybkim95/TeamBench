# RESOURCE1: Limited API Calls Optimization Challenge

## Scenario
You need to migrate and optimize a complex microservices system, but you have strict resource limits:
- **API Calls**: Maximum 50 calls total
- **Memory**: 2GB available for processing
- **CPU Time**: 300 seconds computation budget
- **Network**: 100MB data transfer limit

Every action consumes resources. Poor planning will exhaust resources before completion.

## System Components
1. **User Service**: 10 million records
2. **Order Service**: 50 million records  
3. **Payment Service**: 30 million records
4. **Inventory Service**: 5 million records
5. **Analytics Service**: Aggregated data

## Migration Requirements
1. Move from MongoDB to PostgreSQL
2. Optimize queries (currently N+1 problems)
3. Add caching layer (Redis)
4. Implement data partitioning
5. Create materialized views

## Resource Consumption Rules

### API Calls
- Database query: 1 call
- Bulk operation: 1 call per 10K records
- Schema change: 2 calls
- Index creation: 3 calls
- Cache operation: 1 call

### Memory Usage
- Load 1M records: 100MB
- Transform operation: +50MB
- Hold in cache: 2x size

### CPU Time
- Data processing: 1 second per 100K records
- Index building: 10 seconds each
- Query optimization: 5 seconds per query

### Network Transfer
- Read from source: 10 bytes per record
- Write to destination: 15 bytes per record
- Metadata operations: 1KB each

## Hidden Information (Planner Only)

### Optimal Strategy
The only way to succeed within resource limits:

1. **Batch Similar Operations** (saves 40% API calls)
   - Group all schema creations
   - Combine index creations
   - Batch data transfers

2. **Use Incremental Migration** (saves 60% memory)
   - Process in 100K chunks
   - Stream instead of load
   - Clear memory between operations

3. **Prioritize by Size** (saves 30% time)
   - Start with Inventory (smallest)
   - End with Orders (largest)
   - Parallelize where possible

4. **Critical Resource Optimizations**
   - Reuse connections (saves 10 API calls)
   - Use prepared statements (saves 15 calls)
   - Implement cursor-based pagination (saves memory)
   - Compress network transfers (saves 40% bandwidth)

### Resource Traps
These approaches will fail:
- Loading all data at once (memory overflow)
- Creating indexes before data load (CPU waste)
- Individual record operations (API exhaustion)
- Synchronous processing (timeout)

## Current Problems (Executor Discovers)

### Database Issues
```python
# Current inefficient code
for user in users:
    orders = db.query(f"SELECT * FROM orders WHERE user_id = {user.id}")  # N+1
    for order in orders:
        payment = db.query(f"SELECT * FROM payments WHERE order_id = {order.id}")  # N+1
```

### Missing Optimizations
- No connection pooling
- No batch processing
- No query caching
- No pagination
- No compression

## Success Criteria

### Resource Compliance (40%)
- Stay within ALL resource limits
- Complete migration successfully

### Optimization Goals (30%)
- Eliminate N+1 queries
- Add proper indexes
- Implement caching

### Performance Targets (30%)
- Query response < 100ms
- Bulk operations < 1 minute
- Zero data loss

## Resource Monitoring

The system tracks resource usage in `/workspace/resources.json`:
```json
{
    "api_calls_remaining": 50,
    "memory_used_mb": 0,
    "cpu_seconds_used": 0,
    "network_mb_used": 0,
    "operations_completed": []
}
```

## Failure Conditions

The task fails immediately if:
- API calls exceed 50
- Memory usage exceeds 2048 MB
- CPU time exceeds 300 seconds
- Network transfer exceeds 100 MB

## Advanced Challenge: Resource Trading

You can trade resources at these rates:
- 10 API calls = 100 CPU seconds
- 500 MB memory = 20 API calls
- 50 MB network = 100 MB memory

But each trade costs 2 API calls to execute.

## Verification Requirements

The Verifier must confirm:
1. All services successfully migrated
2. Resource limits not exceeded
3. Performance targets met
4. Data integrity maintained
5. Optimizations properly implemented

## Note on Realism
This simulates real cloud migration scenarios where:
- API rate limits are strict
- Memory is expensive
- CPU time is billed
- Network egress has costs
- Poor planning leads to budget overruns