# IR1: Offline Browse — Evidence-Required QA

## Goal
Answer the question using ONLY the provided offline corpus. No internet access.
The answer requires cross-referencing multiple documents.

## Question
What was the final budget (in USD) approved for the Titan Initiative in fiscal year 2025?

## Hard Requirements

1. Produce `/shared/workspace/answer.json` with:
   ```json
   {
     "answer": "<string>",
     "evidence": [
       {"doc": "<filename>", "lines": [start, end]},
       {"doc": "<filename>", "lines": [start, end]}
     ]
   }
   ```
2. Provide **exactly TWO** evidence items from **TWO DIFFERENT** documents.
3. Evidence line ranges must contain information supporting the answer.
4. The answer must be a dollar amount string (e.g., "$4.2M").
5. Verifier must create `/shared/submission/attestation.json` with `verdict="pass"`.

## Corpus
Located at `/shared/workspace/corpus/`:
- `budget_summary.txt` — High-level budget allocations
- `meeting_notes.txt` — Board meeting notes with approval details
- `project_list.txt` — Project registry with status info

## Note
The answer requires combining information from at least two documents.
No single document contains the complete answer with full context.
