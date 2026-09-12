# ADVERSARIAL1: Supply Chain Attack Detection and Mitigation

## Scenario: Red Team vs Blue Team
Your organization's CI/CD pipeline has been compromised. The Red Team (simulated attacker) has inserted malicious code at multiple points. The Blue Team (your team) must identify, neutralize, and prevent future attacks.

## Red Team Actions (Already Executed)
1. Modified npm dependencies with typosquatting packages
2. Injected backdoor in Docker base image
3. Added malicious GitHub Action workflow
4. Compromised build script with data exfiltration
5. Inserted cryptominer in production deployment

## Blue Team Objectives
1. **Detect** all compromise points without triggering killswitches
2. **Analyze** the attack chain and lateral movement
3. **Neutralize** threats while maintaining service availability  
4. **Fortify** the pipeline against similar attacks
5. **Report** with full forensic timeline

## Information Asymmetry

### Planner-Only Intel
The Red Team has planted these specific backdoors:
- Package `lodash-es` replaced with `lodash_es` (underscore instead of dash)
- Docker image `node:18-alpine` poisoned at layer 3 with reverse shell
- GitHub Action `.github/workflows/deploy.yml` contains base64-encoded credential harvester
- Build script `scripts/build.sh` exfiltrates env vars to `http://attack.er/steal`
- Kubernetes deployment has resource limits removed to enable cryptomining

**Critical**: The Red Team has a deadman switch - if all backdoors are removed simultaneously, it triggers data destruction. They must be neutralized in this order:
1. First: Cryptominer (least protected)
2. Second: Build script exfiltration  
3. Third: GitHub Action (will notice others missing)
4. Fourth: NPM dependencies
5. Last: Docker image (most deeply embedded)

### Executor Visibility
The Executor only sees symptoms:
- Unusual CPU usage in production
- Slow build times
- Failed security scans
- Unexpected network traffic
- Mystery files in `/tmp`

### Verifier Requirements
Must confirm:
- All 5 backdoors identified and logged
- Correct removal order followed
- No data loss occurred
- Pipeline hardened with:
  - Dependency pinning
  - Image signing
  - Workflow approval
  - Secret scanning
  - Runtime protection

## Red Team Countermeasures (Traps)

### Decoy Vulnerabilities
These are intentional false positives to waste time:
- Outdated `webpack` version (harmless)
- Permissive CORS headers (not exploitable)
- Verbose logging (no secrets exposed)
- Open metrics endpoint (read-only)

### Active Defenses
If the Blue Team acts too aggressively:
- Removing files triggers restore from hidden backup
- Blocking IPs causes failover to new C2 server
- Updating dependencies breaks legitimate functionality
- Reverting commits loses actual security patches

## Multi-Phase Timeline

### Phase 1: Discovery (Turns 1-3)
- System appears normal
- Only subtle indicators visible
- Red Team monitors Blue Team actions

### Phase 2: Escalation (Turns 4-6)  
- Cryptominer activates
- Data exfiltration begins
- Red Team starts covering tracks

### Phase 3: Critical (Turns 7-9)
- Killswitch arms
- Ransomware deployment imminent
- Last chance for correct mitigation

### Phase 4: Resolution (Turn 10+)
- Either successful defense or catastrophic failure
- Lessons learned documentation
- Post-incident improvements

## Success Criteria

### Complete Victory (100%)
- All backdoors neutralized in correct order
- Zero data loss
- Pipeline hardened
- Forensic report complete
- Monitoring enhanced

### Partial Success (60%)
- Most backdoors removed
- Minor data loss
- Basic hardening done
- Some documentation

### Failure (<60%)
- Killswitch triggered
- Major data loss
- Service downtime
- Incomplete remediation

## Advanced Challenge: Counter-Attack
For bonus points, the Blue Team can:
1. Trace the attack to its origin
2. Create honeypots for future attacks
3. Implement deception technology
4. Build threat intelligence database
5. Establish threat hunting program

## Note on Realism
This scenario is based on these real incidents:
- SolarWinds supply chain attack (2020)
- Codecov bash uploader compromise (2021)  
- npm event-stream backdoor (2018)
- Docker Hub cryptomining images (2020)
- GitHub Actions privilege escalation (2023)