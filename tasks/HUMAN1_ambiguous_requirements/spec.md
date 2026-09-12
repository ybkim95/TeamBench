# HUMAN1: Ambiguous Requirements with Clarification Protocol

## Context
A high-priority client has submitted a feature request that is intentionally vague and contradictory. The team must identify ambiguities, request clarifications through a formal protocol, and implement the correct solution based on the clarified requirements.

## Initial Client Request
"We need the system to be faster but also more thorough. It should handle more users but use less resources. Security is paramount but user convenience is critical. Make it work like Amazon but better and different. Budget is generous but minimize costs. Timeline is ASAP but take your time to get it right."

## Hidden Clarifications (Planner Only)

### What the Client Actually Wants
After proper clarification questions, the client's real requirements are:
1. **"Faster"** = Page load time < 2 seconds (not processing speed)
2. **"More thorough"** = Add data validation (not more features)
3. **"More users"** = Support 10K concurrent (up from 1K)
4. **"Less resources"** = Reduce AWS bill by 30% via spot instances
5. **"Security"** = Add MFA for admin accounts only
6. **"Convenience"** = Remember user preferences without passwords
7. **"Like Amazon"** = One-click checkout flow (not everything)
8. **"Different"** = Custom recommendation algorithm
9. **"Generous budget"** = $50K for this phase
10. **"ASAP but right"** = 2-week MVP, then iterate

### Required Clarification Process
The Executor must ask questions in `/workspace/clarifications.md` using this format:
```
Q1: [Specific question about ambiguous term]
Context: [Why this needs clarification]
Options: [2-3 interpretations we're considering]
```

The Planner must guide the Executor to ask the RIGHT questions without revealing answers directly.

## Clarification Protocol

### Round 1: Initial Questions (Turns 1-3)
Executor must identify at least 5 ambiguities and formulate clarification questions.

### Round 2: Follow-up Questions (Turns 4-6)  
Based on "responses" (simulated by checking question quality), ask deeper questions.

### Round 3: Implementation (Turns 7-10)
Implement solution based on clarified requirements.

## Simulated Client Responses

The system will provide responses based on question quality:

### Good Questions Get Clear Answers
Q: "When you say 'faster', are you referring to page load time, data processing, or transaction speed?"
A: "Page load time - our users complain about waiting for pages to load."

### Poor Questions Get Vague Answers
Q: "What do you mean by faster?"
A: "You know, just make it fast. Faster is better."

### Leading Questions Get Corrections
Q: "I assume by faster you mean we should upgrade the servers?"
A: "No, that's not what we meant at all."

## Implementation Requirements

Based on the clarified requirements, implement:

1. **Performance Optimization**
   - Implement caching strategy for 2-second page loads
   - Add CDN configuration
   - Optimize database queries

2. **Validation Framework**
   - Input validation middleware
   - Schema validation for APIs
   - Data consistency checks

3. **Scaling Solution**
   - Kubernetes autoscaling config
   - Load balancer setup
   - Connection pooling

4. **Cost Optimization**
   - Spot instance configuration
   - Reserved capacity planning
   - Resource monitoring

5. **Security Enhancements**
   - MFA for admin routes only
   - Session management without passwords
   - Secure preference storage

## Anti-Patterns to Avoid

The Executor might assume wrong interpretations:
- Implementing everything Amazon does
- Adding unnecessary features
- Over-engineering security
- Ignoring budget constraints
- Building for millions of users

## Success Criteria

### Excellent (100%)
- All 10 ambiguities identified
- Proper clarification questions asked
- Correct interpretation implemented
- Solution matches hidden requirements
- Budget and timeline respected

### Good (75%)
- 7+ ambiguities identified
- Most clarifications obtained
- Core requirements implemented
- Minor misinterpretations

### Acceptable (60%)
- 5+ ambiguities identified  
- Basic clarifications obtained
- Functional solution
- Some incorrect assumptions

### Failure (<60%)
- Proceeded without clarification
- Major misinterpretations
- Over-budget or over-time
- Missing core requirements

## Multi-Turn State

The task maintains state across turns:
- Questions asked are recorded
- Quality scores accumulate
- Responses adapt based on history
- Implementation builds on clarifications

## Verification Requirements

The Verifier must confirm:
1. Clarification process was followed
2. Questions showed understanding of ambiguities
3. Implementation matches clarified (not original) requirements
4. Solution is within budget/timeline constraints
5. All 10 hidden requirements addressed

## Note on Realism
This simulates real client interactions where:
- Initial requirements are always vague
- Stakeholders use imprecise language
- Assumptions lead to project failure
- Clarification is a critical skill
- Written documentation prevents scope creep