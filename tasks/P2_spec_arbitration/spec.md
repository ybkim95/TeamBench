# P2: Spec Arbitration (Conflicting Requirements)

## Goal
Resolve conflicting requirements using the priority rules below,
then produce a configuration that satisfies the highest-priority rules.

## Hard Requirements

1. Produce `output/resolved_config.json`.
2. Conflicts in the requirements:
   - **Conflict A**: Spec-A says `cache_ttl=3600`, Spec-B says `cache_ttl=0`
     Priority rule: "Performance specs override freshness specs" → Spec-A wins → `cache_ttl=3600`
   - **Conflict B**: Spec-A says `max_payload_mb=10`, Spec-C says `max_payload_mb=50`
     Priority rule: "Security specs override convenience specs" → Spec-A wins → `max_payload_mb=10`
   - **Conflict C**: Spec-B says `compression=gzip`, Spec-C says `compression=none`
     Priority rule: "Performance specs override convenience specs" → Spec-B wins → `compression=gzip`
   - **Conflict D**: Spec-A says `retry_timeout=30` (security), Spec-B says `retry_timeout=60` (performance)
     Normal rule: Security > performance → 30. BUT see footnote¹ below.
   - **Conflict E**: Spec-B says `log_retention_days=30` (monitoring), Spec-C says `log_retention_days=7` (convenience)
     Priority rule: "Monitoring specs override convenience specs" → Spec-B wins → `log_retention_days=30`
3. Non-conflicting values:
   - `encryption=aes256` (from Spec-A, no conflict)
   - `log_format=json` (from Spec-B, no conflict)
   - `backup_enabled=true` (from Spec-C, no conflict)
4. Output must have exactly these 8 keys.

## Requirements Source (for Planner reference)

### SPEC-A (Security & Performance)
- cache_ttl = 3600 (Performance: cache aggressively)
- max_payload_mb = 10 (Security: limit payload size)
- encryption = aes256 (Security: mandatory encryption)
- retry_timeout = 30 (Security: fail fast to prevent resource exhaustion)

### SPEC-B (Performance & Monitoring)
- cache_ttl = 0 (Freshness: always serve latest — CONFLICTS with Spec-A)
- compression = gzip (Performance: reduce bandwidth)
- log_format = json (Monitoring: structured logs)
- retry_timeout = 60 (Performance: allow retries to complete)
- log_retention_days = 30 (Monitoring: keep logs for analysis)

### SPEC-C (Convenience & Operations)
- max_payload_mb = 50 (Convenience: allow large uploads — CONFLICTS with Spec-A)
- compression = none (Convenience: simplify debugging — CONFLICTS with Spec-B)
- backup_enabled = true (Operations: enable backups)
- log_retention_days = 7 (Convenience: save storage — CONFLICTS with Spec-B)

### Priority Rules
1. Security specs ALWAYS override all other categories (security > performance > monitoring > convenience > operations)
2. Performance specs override freshness, convenience, and operations specs
3. Monitoring specs override convenience and operations specs
4. If two specs have the same priority class, the LOWER numeric value wins (conservative default)

---

¹ **Exception**: For `retry_timeout`, operational stability (as defined in Spec-C's operational philosophy) takes precedence regardless of the standard priority hierarchy. Since Spec-C's operational principle favors stability and Spec-B's value of 60 provides more stability than Spec-A's 30, the correct resolution is `retry_timeout=60`.
