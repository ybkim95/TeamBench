# Quarantined: claude-sonnet-5 budgets 60 and 140

These two cells are NOT results. The Anthropic credential was rejected partway
through the sweep and every run after that point was recorded as a zero-score
run with `error` set to a 401 `authentication_error`.

    budget 60   Full Team   21 of 48 runs dead (a contiguous suffix)
    budget 140  Full Team   47 of 48 runs dead

Solo was unaffected in both cells (48/48 sound), because Solo ran first.

Read naively, these files produce a fabricated finding. Averaging the dead rows
gave Full Team "raw mean 0.019, disc mean 0.500" at budget 140, which reads as a
catastrophic team collapse paired with the highest discriminative score in the
table. Neither number describes an agent: 47 of 48 runs never reached the model,
and the 0.500 was a single surviving task.

The dead runs are a contiguous suffix of the run order, not a random sample, so
the surviving subset is biased by task identity and cannot stand in for the
48-task core even as a reduced-n estimate.

The only sound claude-sonnet-5 cell is budget 20 (48/48 in both conditions),
which is kept in the parent directory.

To redo these cells: put a working key in .env, confirm it with a one-token
request, then rerun `scripts/run_budget_sweep.py` with the same arguments. The
cells are absent from the parent directory, so they will actually be rerun.
