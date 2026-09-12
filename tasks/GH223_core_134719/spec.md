# GH223_core_134719: Fix CCM15 temperature set always changes the ac_mode to cool — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/home-assistant/core

## PR Description

<!--
  You are amazing! Thanks for contributing to our project!
  Please, DO NOT DELETE ANY TEXT from this template! (unless instructed).
-->

## Proposed change
<!--
  Describe the big picture of your changes here to communicate to the
  maintainers why we should accept this pull request. If it fixes a bug
  or resolves a feature request, be sure to link to that issue in the
  additional information section.
-->
fix a problem with ccm15 integration.

Bump py-ccm15 from 0.0.9 to 0.1.2
0.1.2 release notes: https://github.com/ocalvo/py-ccm15/releases/tag/v0.1.2

Changes: https://github.com/ocalvo/py-ccm15/compare/3891d840e69d241c85bf9486e7fe0bb3c7443980...a331424c96a515646aff05aa0f71013ffb71f501

## Type of change
<!--
  What type of change does your PR introduce to Home Assistant?
  NOTE: Please, check only 1! box!
  If your PR requires multiple boxes to be checked, you'll most likely need to
  split it into multiple PRs. This makes things easier and faster to code review.
-->

- [x] Dependency upgrade
- [V] Bugfix (non-breaking change which fixes an issue)
- [ ] New integration (thank you!)
- [ ] New feature (which adds functionality to an existing integration)
- [ ] Deprecation (breaking change to happen in the future)
- [ ] Breaking change (fix/feature causing existing functionality to break)
- [ ] Code quality improvements to existing code or addition of tests

## Additional information
<!--
  Details are important, and help maintainers processing your PR.
  Please be sure to fill out additional details, if applicable.
-->
When I am heating, the origin function int `py-ccm15` is set only the new parameter. but the CCM15 webserver want to receive the all settings of the current A/C. We need to set them again and again, in every change (fan mode, ac mode, temperature).

The other option set the A/C to the default (cooling) and will freeze me and my wife in the rainy winter (true story).
PR for the breaking changes in the `py-ccm15` package:
(withheld: the upstream fix is not part of the task)

(and this: only rename (withheld: the upstream fix is not part of the task) )

py_ccm15 issue with the accepted PR:

- This PR fixes or closes issue: fixes [#](https://github.com/home-assistant/core/issues/133613)
- This PR is related to issue: 
- Link to documentation pull request: 

## Checklist
<!--
  Put an `x` in the boxes that apply. You can also fill these out after
  creating the PR. If you're unsure about any of them, don't hesitate to ask.
  We're here to help! This is simply a reminder of what we are going to look
  for before merging your code.
-->

- [V] The code change is tested and works locally.
- [V] Local tests pass. **Your PR cannot be merged unless tests pass**
- [V] There is no commented out code in this PR.
- [V] I have followed the [development checklist][dev-checklist]
- [V] I have followed the [perfect PR recommendations][perfect-pr]
- [x] The code has been formatted using Ruff (`ruff format homeassistant tests`)
- [ ] Tests have been added to verify that the new code works.

If user exposed functionality or configuration variables are added/changed:

- [ ] Documentation added/updated for [www.home-assistant.io][docs-repository]

If the code communicates with devices, web services, or third-party tools:

- [ ] The [manifest file][manifest-docs] has all fields filled out correctly.  
      Updated and included derived files by running: `python3 -m script.hassfest`.
- [ ] New or updated dependencies have been added to `requirements_all.txt`.  
      Updated by running `python3 -m script.gen_requirements_all`.
- [V] For the updated dependencies - a link to the changelog, or at minimum a diff between library versions is added to the PR description.
breaking-change update for the py_ccm15 dependency: 

(withheld: the upstream fix is not part of the task)

change the version to  0.1.0 (only metafile):
(withheld: the upstream fix is not part of the task)

To help with the load of incoming pull requests:

- [V] I have reviewed two other [open pull requests][prs] in this repository.

[prs]: https://github.com/home-assistant/core/pulls?q=is%3Aopen+is%3Apr+-author%3A%40me+-draft%3Atrue+-label%3Awaiting-for-upstream+sort%3Acreated-desc+review%3Anone+-status%3Afailure

<!--
  Thank you for contributing <3

  Below, some useful links you could explore:
-->
[dev-checklist]: https://developers.home-assistant.io/docs/development_checklist/
[manifest-docs]: https://developers.home-assistant.io/docs/creating_integration_manifest/
[quality-scale]: https://developers.home-assistant.io/docs/integration_quality_scale_index/
[docs-repository]: https://github.com/home-assistant/home-assistant.io
[perfect-pr]: https://developers.home-assistant.io/docs/review-process/#creating-the-perfect-pr

Thanks for the  Home Assistant hard work! I like the product a and use it every day.

## PR Review Comments

**[user]** on `homeassistant/components/ccm15/manifest.json`:

py_ccm15==0.1.1

**[user]** on `requirements_all.txt`:

py_ccm15==0.1.1

**[user]** on `requirements_test_all.txt`:

py_ccm15==0.1.1

**[user]** on `homeassistant/components/ccm15/manifest.json`:

Why did we change from `-` to `_`?

**[user]** on `homeassistant/components/ccm15/manifest.json`:

Request from [user] , the maintainer of the py-ccm15 and origin writer of the ccm15 for HA

Thanks

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
