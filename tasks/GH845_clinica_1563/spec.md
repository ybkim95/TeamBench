# GH845_clinica_1563: [FIX] IXI-to-BIDS : Setting `participant_id` as the first column of `/participants.tsv` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/aramis-lab/clinica/issues/1560
- Repo: https://github.com/aramis-lab/clinica

## Issue Description

**Describe the bug**
After applying the [BIDS validator](https://bids-standard.github.io/bids-validator/) on the architecture resulting from the BIDS conversion of the CI data, an error occurs indicating that the file `/participants.tsv` has incorrect column order.

**To Reproduce**
Steps to reproduce the behavior:
1. Get the IXI raw subset from the CI data
2. Convert the IXI raw subset into the BIDS format
3. Go to the [BIDS validator](https://bids-standard.github.io/bids-validator/)
4. Select the IXI subset in BIDS format
4. See the error

**Expected behavior**
This error should be thrown :
`Some TSV columns are in the incorrect order:`
`/participants.tsv (Initial column 1 found at index 11.)`

**Screenshots**
<img width="1235" height="131" alt="Image" src="https://github.com/user-attachments/assets/b373d735-c93e-4390-8171-65fdf1da4daf" />

**Desktop:**
 - OS: MacOS Sequoia 15.7.1
 - Browser: Safari
 - Clinica version: 0.10.1

**Additional context**
This error could be explained by the fact that the column named `participant_id` is at the end of the `.tsv` file, while it should be at the beginning.

## PR Review Comments

**[user]** on `clinica/converters/ixi_to_bids/_utils.py`:

I would rather have you specify the column number above (line 391) rather than remove/add again the column.

**[user]** on `clinica/converters/ixi_to_bids/_utils.py`:

It will not remove the column, but reorder it. 
`clinical_data.columns` returns the list of column **names**, `drop` removes the name `participant_id` from this list, and `["participant_id"] + list` places `participant_id` at the front.
Finally, the columns are reordered by using `clinical_data[["participant_id", ...]]`.

I could still find a way to specifically use the index of the column `participant_id`, but I don't think it is really necessary. However, I agree that I can place the reordering part right after the `.assign` at the line 391.

**[user]** on `clinica/converters/ixi_to_bids/_utils.py`:

I read quickly the first time indeed, but the point still stands. At L391 the column `participant_id` is created, so you can modify that line to create it at the right position.

What is currently done is `df.assign(name=values)`. What you can do instead is a  `df.insert(0, name, values)`. This way you combine the creation of the column and the placing at the right position.

**[user]** on `clinica/converters/ixi_to_bids/_utils.py`:

The issue is that the column `participant_id` already exists at the point of the `df.assign` ; It is not created by the command, just filled. This makes it impossible to replace the command by `df.insert`, otherwise throwing this kind of error : `ValueError: cannot insert participant_id, already exists`. 

Do you want me to drop the column before inserting, or to preserve the current logic ?
I could also find the place in the code where it is created to insert it at the first position.

**[user]** on `clinica/converters/ixi_to_bids/_utils.py`:

I am curious as to how you tested that option because df.assign does create the column. Do you mind sharing that ? (privately if you would prefer)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
