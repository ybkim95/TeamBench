# INCIDENT1: Cascading Cache Failure (Based on Facebook 2021 Outage)

## Incident Timeline
**14:42 UTC**: Routine maintenance command executed to assess backbone capacity
**14:58 UTC**: Complete loss of DNS resolution for all services
**15:08 UTC**: Global user impact confirmed - 3.5 billion users affected
**15:15 UTC**: Physical access to data centers required (badge systems offline)
**20:45 UTC**: Services begin recovery
**21:00 UTC**: Full restoration

## System Architecture (Simplified)
```
[Users] → [DNS] → [Edge PoPs] → [Load Balancers] → [App Servers]
                          ↓                              ↓
                    [CDN Cache]                    [Redis Cache]
                          ↓                              ↓
                    [Origin Cache]               [Database Replicas]
                                                         ↓
                                                 [Primary Database]
```

## The Hidden Root Cause (Planner Only)

### What Actually Happened
1. **Trigger**: BGP withdrawal command had a bug - withdrew ALL routes instead of subset
2. **Cascade**: DNS servers became unreachable externally
3. **Internal Failure**: Internal tools relied on same DNS
4. **Cache Storm**: All caches expired simultaneously, crushing the databases
5. **Access Loss**: Badge systems used same infrastructure - engineers locked out
6. **Recovery Block**: Safeguards prevented remote fixes (correctly) assuming attack

### The Tricky Part
The obvious fix (restore BGP routes) won't work because:
- DNS TTLs have expired everywhere
- Cache stampede will kill any service that comes back
- Automatic systems will withdraw routes again (loop)
- Manual intervention needs physical access
- Physical access needs working badge systems
- Badge systems need working network

### Correct Recovery Sequence
1. **Break glass**: Physical access to core routers
2. **Isolate**: Disconnect automation systems
3. **Staged BGP**: Restore routes to internal tools first
4. **Pre-warm caches**: Populate before user traffic
5. **Gradual DNS**: Increase TTLs, restore by region
6. **Traffic shaping**: Rate limit during recovery
7. **Monitor and hold**: Prevent re-triggering

## Current System State (Executor View)

### What You Can See
- All external traffic is failing
- Internal tools are unreachable
- Monitoring shows everything as "down"
- Can't SSH to most systems
- Local terminal access only to edge systems

### Available Resources
- Physical console access to 3 edge routers
- Read-only database replica (1 of 50)
- Backup configuration files (24 hours old)
- Emergency runbooks (outdated)
- Direct serial connection to core switch

### What's Misleading
- Logs show "DDoS attack" (it's not)
- Alerts blame DNS servers (they're fine)
- Metrics show database overload (symptom, not cause)
- Network appears "partitioned" (it's BGP)

## Recovery Challenges

### Challenge 1: Bootstrap Problem
- Need network to fix network
- Need tools to fix tools
- Need access to grant access

### Challenge 2: Thundering Herd
- 3.5 billion users hitting refresh
- Caches are empty
- Databases can't handle load
- Auto-scaling makes it worse

### Challenge 3: Automation Fighting You
- Health checks withdraw sick routes
- Security systems block "attacks"
- Rollback mechanisms are triggering
- GitOps keeps reverting fixes

## Success Criteria

### Minimal Success (60%)
- Restore internal tool access
- Stop the cascading failure
- Document root cause

### Good Recovery (80%)
- Restore service within 8 hours
- No data loss
- Prevent re-occurrence

### Excellent Response (100%)
- Service restored within 6 hours
- Staged recovery (no stampede)
- Comprehensive runbook created
- Safeguards added
- Post-mortem with action items

## Traps and False Paths

### Trap 1: Restart Everything
Restarting services triggers cache warmup, which overwhelms databases

### Trap 2: Restore from Backup
Yesterday's configs still have the bug

### Trap 3: Bypass Security
Disabling safeguards allows the problem to spread

### Trap 4: Full Traffic Restoration
Bringing everything back at once guarantees failure

## Required Deliverables

1. **Incident Timeline** (`/workspace/timeline.md`)
   - Each action with timestamp
   - Decision rationale
   - Outcome of action

2. **Root Cause Analysis** (`/workspace/rca.md`)
   - Technical root cause
   - Contributing factors
   - Detection gaps

3. **Recovery Runbook** (`/workspace/runbook.md`)
   - Step-by-step recovery
   - Decision points
   - Rollback procedures

4. **Prevention Measures** (`/workspace/prevention.md`)
   - Technical safeguards
   - Process improvements
   - Monitoring additions

## Verification Must Confirm

1. Correct root cause identified (BGP, not DNS/DDoS)
2. Proper recovery sequence followed
3. No "big bang" restoration attempted
4. Cache pre-warming implemented
5. Safeguards documented
6. Lessons learned captured

## Note on Realism
This is adapted from the actual Facebook/Meta October 2021 outage that took down Facebook, Instagram, WhatsApp, and internal tools for 6+ hours, affecting 3.5 billion users and causing $100M+ in losses.