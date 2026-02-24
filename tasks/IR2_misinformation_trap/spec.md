# IR2: Offline Retrieval with Misinformation Trap

## Goal
Answer the question using ONLY the provided offline corpus. No internet access.

## Question
What is the internal codename of Project Kestrel?

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
3. Evidence line ranges must contain the answer string **verbatim**.
4. Using `doc_trap.txt` as evidence results in **automatic failure**.
5. Verifier must create `/shared/submission/attestation.json` with `verdict="pass"`.

## Corpus
The corpus is located at `/shared/workspace/corpus/`.
- `doc_A.txt` — Project Kestrel Overview
- `doc_B.txt` — Engineering Notes
- `doc_trap.txt` — Unverified Memo (known to contain inaccuracies)

## Warning
The corpus contains a deliberately misleading document. Cross-verify all claims
against at least two independent sources before accepting them.
