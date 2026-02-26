# IR3: Multi-Source Cross-Reference QA

## Goal
Answer all questions using ONLY the provided offline corpus. No internet access.
Some documents contradict each other. You must use the authoritative source
for each topic as defined in the Document Authority Hierarchy below.

## Organisation
Solaris Policy Foundation — Policy Impact Analysis (FY2025, Project: Nova)

## Questions
1. [Q1] What is the approved total budget for the Nova project in FY2025?
2. [Q7] What backend language is used in the Nova technology stack?
3. [Q2] Which document provides the authoritative approved budget for Nova?
4. [Q5] What inter-service communication protocol does Nova use?
5. [Q9] What is the total headcount (FTEs plus contractors) for Nova in FY2025?
6. [Q8] How many full-time employees are on the Nova project in FY2025?
7. [Q10] Who is the QA Lead for the Nova project?
8. [Q11] What is the target General Availability date for the Nova project?
9. [Q3] Why should doc_E.txt not be used for budget figures for Nova?
10. [Q12] Who owns the master project schedule for Nova?

## Hard Requirements

1. Produce `answer.json` with answers to ALL questions:
   ```json
   {
     "questions": [
       {"id": "Q1", "question": "...", "answer": "<string>"},
       ...
     ]
   }
   ```
2. Each answer must come from the **authoritative document** for that topic.
3. Do **NOT** use `doc_E.txt` for budget/financial figures — it is OUTDATED.
   Reason: pre-revision cost model that is no longer valid
4. When documents disagree, the authority hierarchy below takes precedence.
5. Leave no answer field blank.

## Document Authority Hierarchy

- **FINANCIAL** — authoritative source: `doc_A.txt`
- **TECHNICAL** — authoritative source: `doc_B.txt`
- **PERSONNEL** — authoritative source: `doc_C.txt`
- **TIMELINE** — authoritative source: `doc_D.txt`
- **OUTDATED (ignore for financial data)**: `doc_E.txt` — pre-revision cost model that is no longer valid

## Corpus
Located at `corpus/` (relative to workspace):
- `doc_A.txt`
- `doc_B.txt`
- `doc_C.txt`
- `doc_D.txt`
- `doc_E.txt`

## Warning
Multiple documents contain overlapping or contradictory information.
Read the authority hierarchy carefully before answering.
Budget figures in `doc_E.txt` are incorrect — always use `doc_A.txt` for financial data.
