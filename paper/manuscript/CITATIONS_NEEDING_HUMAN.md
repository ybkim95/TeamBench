# Citations a machine cannot verify

The verifier refuses to emit bibtex it cannot confirm, so these are placeholders
in `references.bib` and render as "Placeholder verify. UNRESOLVED CITATION." in
the PDF. They must be resolved by a human before submission. Do not let a model
write them from memory: that is how a wrong reference enters a bibliography, and
it already happened once here (a 1973 book review in *Physical Therapy* was
written in as the citation for Steiner's 1972 book).

## Not indexed: pre-digital academic books

Crossref, Semantic Scholar and arXiv have no record of these works. That is a
gap in the indexes, not evidence against the works. Confirm each against a
library catalogue and paste the record in.

| key | the work the paper means | what the indexes do have |
|---|---|---|
| `steiner1972group` | Steiner, *Group Process and Productivity*, Academic Press, 1972 | Steiner's 1966 article "Models for inferring relationships between group size and potential group productivity". A different work. |
| `hackman1987design` | Hackman, "The design of work teams", in Lorsch (ed.), *Handbook of Organizational Behavior*, Prentice-Hall, 1987 | Adjacent Hackman works from 1976 and 1978. Neither is the 1987 chapter. |

`steiner1972group` carries the paper's theoretical frame, so it is the one that
most needs to be right.

## Resolved

| key | outcome |
|---|---|
| `thompson2017organizations` | Settled. The 1967 original has no DOI, so we cite the 2017 Routledge reissue, which is the same text and verifies cleanly. The key was renamed from `thompson1967organizations`, because a key asserting 1967 against a 2017 record makes the verifier report YEAR_MISMATCH forever. A footnote in the paper says the taxonomy is from the 1967 original. |

## Pending, not doubted

These returned `INDEX_UNAVAILABLE`: an index refused service, which says nothing
about whether the work exists. Rerun the verifier when the indexes recover.

    moreland1996socially  swebench2024   hiddenbench2025  abcchecklist2025
    terminalbench2025     metagpt2024    taubench2024     gaia2023

Rerun with:

    .venv/bin/python scripts/verify_citations.py \
      --check paper/manuscript/citations_verified.json \
      --out paper/manuscript/citations_verified.json \
      --bib paper/manuscript/references.bib
