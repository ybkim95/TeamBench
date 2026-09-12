# INDUSTRY1: API Rate Limiting Implementation

## Business Context
Your e-commerce API is experiencing abuse and needs rate limiting to prevent:
- DDoS attacks
- Resource exhaustion
- Fair usage among customers

## Current System
- Flask API with `/products`, `/orders`, `/users` endpoints
- No rate limiting implemented
- Redis available for state storage
- 1000 RPS normal traffic, spikes to 10K+ during attacks

## Requirements
Implement rate limiting with:
- 100 requests per minute per IP for anonymous users
- 1000 requests per minute per API key for authenticated users  
- 429 status code with Retry-After header when exceeded
- Whitelist for internal IPs
- Different limits per endpoint type

## Implementation Strategy (Planner Only)

### Technical Approach
Use Redis-based sliding window rate limiter:
1. Key format: `ratelimit:{ip_or_apikey}:{endpoint}`
2. Store request timestamps in sorted set
3. Remove expired entries before checking count
4. Atomic operations to prevent race conditions

### Code Structure
- `RateLimiter` class with configurable limits
- Flask middleware decorator `@rate_limit()`
- Configuration file for different endpoint limits
- Admin endpoint to view/reset limits

### Edge Cases to Handle
- Redis connection failures (fail open vs fail closed)
- Clock skew between servers
- Burst traffic (allow short bursts within limits)
- API key authentication vs IP-based limiting

## Business Impact
- Prevents service outages from abuse
- Ensures fair access for legitimate users
- Reduces infrastructure costs
- Improves customer experience

## Success Criteria
- All endpoints properly rate limited
- Correct HTTP responses for exceeded limits
- Performance impact < 5ms per request
- Administrative controls working
- Handles Redis failures gracefully