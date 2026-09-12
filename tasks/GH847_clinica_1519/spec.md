# GH847_clinica_1519: [FIX] UKB-to-BIDS : Scans files creation for UKB-to-BIDS converter — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/aramis-lab/clinica/issues/1508
- Repo: https://github.com/aramis-lab/clinica

## Issue Description

The converter UKB-to-BIDS seems to not produce the scans files required by BIDS specifications. Here is the reference for the converter's output in our CI data : 

```bash
(clinica) alice.joubert@ICM-COLLI-MP013 bids % tree
.
├── README
├── dataset_description.json
├── participants.tsv
├── sub-UKB1000191
│   ├── ses-M000
│   │   └── func
│   │       ├── sub-UKB1000191_ses-M000_task-facesshapesemotion_bold.json
│   │       └── sub-UKB1000191_ses-M000_task-facesshapesemotion_bold.nii.gz
│   └── sub-UKB1000191_sessions.tsv
...
├── sub-UKB5566112
│   ├── ses-M000
│   │   └── anat
│   │       ├── sub-UKB5566112_ses-M000_FLAIR.json
│   │       └── sub-UKB5566112_ses-M000_FLAIR.nii.gz
│   └── sub-UKB5566112_sessions.tsv
└── task-facesshapesemotion_events.tsv
```

There should be a `scans` tsv file written at the root of each session, which is not the case.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Thanks for keeping track of these bugs [user] !

It'd be interesting to know why these are not written indeed.

## PR Review Comments

**[user]** on `clinica/converters/ukb_to_bids/_utils.py`:

To be removed.

**[user]** on `clinica/converters/ukb_to_bids/_utils.py`:

By curiosity, why is the `reset_index()` needed ?

**[user]** on `clinica/converters/ukb_to_bids/_utils.py`:

To be removed ?

**[user]** on `clinica/converters/ukb_to_bids/_utils.py`:

This function is already quite long and already needs some refactoring. I think you can put all your added logic in a dedicated function, something like that:

```python
for bids_full_path, metadata in scans.iterrows():
   ...
   _write_row_in_scans_tsv_file(Path(bids_full_path), metadata)

def _write_row_in_scans_tsv_file(bids_path: Path, row: pd.Series):
    scans_filepath = ...
    row_to_write = _serialize_row(....)
    ...
```

WDYT ?

**[user]** on `clinica/converters/ukb_to_bids/_utils.py`:

```suggestion
            / f"{metadata.participant_id}_{metadata.sessions}_scans.tsv"
```

See the BIDS specifications here: https://bids-specification.readthedocs.io/en/stable/modality-agnostic-files.html#scans-file

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
