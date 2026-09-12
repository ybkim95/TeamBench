# GH307_appsmith_35927: fix: API multipart spec flakiness — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/appsmithorg/appsmith/issues/35137
- Repo: https://github.com/appsmithorg/appsmith

## Issue Description

### SubTasks

Failing Tests: 
7. Checks MultiPart form data for a File Type upload + Bug 12476, 8. Checks MultiPart form data for a Array Type upload results in API error

This test case relies on cloudinary which is currently throwing an error. This is being caused due to being dependent on external API.

Failure Runs: https://internal.appsmith.com/app/cypress-dashboard/run-details-65890b3c81d7400d08fa9ee5?branch=master&workflowId=8718186679&attempt=3&selectiontype=test&testsstatus=failed&specsstatus=fail

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

We have found issues that are potential duplicates:   
  - [#35136] [Task]: Fix flakiness of cypress&#x2F;e2e&#x2F;Sanity&#x2F;Datasources&#x2F;MockDBs_Spec.ts (88.44%)

  - [#35135] [Task]: Fix flakiness of cypress&#x2F;e2e&#x2F;Regression&#x2F;ServerSide&#x2F;OnLoadTests&#x2F;JSOnLoad4_Spec.ts (94.69%)

  - [#35134] [Task]: Fix flakiness of cypress&#x2F;e2e&#x2F;Regression&#x2F;ClientSide&#x2F;Autocomplete&#x2F;BracketNotation_AC_spec.ts (91.14%)
If any of the issues listed above are a duplicate, please consider closing this issue & upvoting the original one.  
Alternatively, if neither of the listed issues addresses your feature/bug, keep this issue open.

### Comment 2 ([user]):

Hey team! Please [add your planning poker estimate](https://app.zenhub.com/workspaces/Data-Integration-Pod-6322a759b3296d249ce5c4ed/issues/appsmithorg/appsmith/35137?planning-poker) with Zenhub [user] [user] [user] [user] [user]

### Comment 3 ([user]):

Adding estimate as 2 as we have reliance external Cloudinary API, in order to get rid of this dependency, we may have to add a new file upload API functionality in TED server and use API from there. Since we have never actively added any datasources or APIs in TED server, we would need to get more context on this.

## PR Review Comments

**[user]** on `app/client/cypress/support/Pages/ApiPage.ts`:

**Consider restoring visibility checks for robustness.**

Dear student, it appears you've removed the visibility check before clicking on elements. While this simplifies the code, it might lead to issues where clicks fail because elements are not yet visible. In the world of testing, especially with asynchronous UI operations, it's prudent to ensure elements are visible and interactable before performing actions on them. This helps in making the tests more reliable and less flaky.

Consider the following adjustment to maintain the robustness of your test interactions:

[Code changes omitted — Planner should analyze the issue and guide the Executor]

This change ensures that the element is visible before we attempt to click on it, thus reducing the likelihood of encountering errors during test execution.

> Committable suggestion was skipped due to low confidence.

<!-- This is an auto-generated comment by CodeRabbit -->

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
