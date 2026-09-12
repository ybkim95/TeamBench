# GH561_flagsmith_6929: fix(Segments): Fix project reference in segment creation — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/Flagsmith/flagsmith/issues/6914
- Repo: https://github.com/Flagsmith/flagsmith

## Issue Description

We received a report that indicates a potential vulnerability: 

"The application has a functionality that allows users to add segments.
However, it does not implement an authorization check for the "project"
parameter, which allows users to add segments in all users account by
replacing the "project" parameter.

By exploiting this vulnerability, an attacker can add segments. As the
"project" parameter is numeric, the Attacker can do a brute force attack on
this endpoint. As a result, an attacker account can add segments in all
users account."

## PR Review Comments

**[user]** on `api/tests/unit/segments/test_unit_segments_views.py`:

### Test doesn't verify successful creation, masks failures

**Low Severity**

<!-- DESCRIPTION START -->
The test discards the response from `admin_client.post(...)` without asserting the status code or verifying the segment was created in the correct `project`. The sole assertion (`not Segment.objects.filter(project=other_project).exists()`) would pass even if the request returned a 500 or 400 error. This means the test could silently pass while the create functionality is completely broken, providing a false sense of security for this fix.
<!-- DESCRIPTION END -->

<!-- BUGBOT_BUG_ID: 41650702-0afd-450a-9e4c-11e2c6178f65 -->

<!-- LOCATIONS START
api/tests/unit/segments/test_unit_segments_views.py#L1897-L1909
LOCATIONS END -->
<div><a href="https://cursor.com/open?data=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImJ1Z2JvdC12MiJ9.eyJ2ZXJzaW9uIjoxLCJ0eXBlIjoiQlVHQk9UX0ZJWF9JTl9DVVJTT1IiLCJkYXRhIjp7InJlZGlzS2V5IjoiYnVnYm90Ojc2ZTY2MWNkLTIxODUtNDNjNy04OGMyLTdmM2FkZjc5Y2Y0ZSIsImVuY3J5cHRpb25LZXkiOiJhU3FfeGpmcXJwNGU2bXVyNnlVd2h3TFZVdHJGajBsRDIxdUF1bnNRd2dJIiwiYnJhbmNoIjoiZml4L2NyZWF0ZS1zZWdtZW50LXByb2plY3QtcmVmZXJlbmNlIiwicmVwb093bmVyIjoiRmxhZ3NtaXRoIiwicmVwb05hbWUiOiJmbGFnc21pdGgifSwiaWF0IjoxNzczMjc1OTEwLCJleHAiOjE3NzU4Njc5MTB9.qm8kw0nNjUaXGBYUHyRf2bOBTKlMU6qSqKTDFEKVTk0UsyHLj3zJMIL9NKPXTFN7ZQ2UuZnwjxSh4B8yvqIRMgMecxPHTKUzCkr_hPi5YR6n2XEzl4yt-GVT08Knk1mRFbSO8lHRtZ70kl5tmATaI75iPQfhNkfaKBVIQQJ8-ZkgwTb0A0WJy8BrFjK-ieGOXvA25Vd93YlAeeFrnRiTVnq0aXjQGPzv0d4W2PGAHEW_giWWZj8SQwRkx8ge2rTuMnGe7ckDlufe4tkG-_LInH_OwPV5pTxtokIn2HrRHT2h5QyU-Os8J-XB4bKgKf-wcG8sT6MDMDzpZBJseQ5u3A" target="_blank" rel="noopener noreferrer"><picture><source media="(prefers-color-scheme: dark)" srcset="https://cursor.com/assets/images/fix-in-cursor-dark.png"><source media="(prefers-color-scheme: light)" srcset="https://cursor.com/assets/images/fix-in-cursor-light.png"><img alt="Fix in Cursor" width="115" height="28" src="https://cursor.com/assets/images/fix-in-cursor-dark.png"></picture></a>&nbsp;<a href="https://cursor.com/agents?data=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImJ1Z2JvdC12MiJ9.eyJ2ZXJzaW9uIjoxLCJ0eXBlIjoiQlVHQk9UX0ZJWF9JTl9XRUIiLCJkYXRhIjp7InJlZGlzS2V5IjoiYnVnYm90Ojc2ZTY2MWNkLTIxODUtNDNjNy04OGMyLTdmM2FkZjc5Y2Y0ZSIsImVuY3J5cHRpb25LZXkiOiJhU3FfeGpmcXJwNGU2bXVyNnlVd2h3TFZVdHJGajBsRDIxdUF1bnNRd2dJIiwiYnJhbmNoIjoiZml4L2NyZWF0ZS1zZWdtZW50LXByb2plY3QtcmVmZXJlbmNlIiwicmVwb093bmVyIjoiRmxhZ3NtaXRoIiwicmVwb05hbWUiOiJmbGFnc21pdGgiLCJwck51bWJlciI6NjkyOSwiY29tbWl0U2hhIjoiOWQ2NjljZmJhYWQzNmNhMzcwOGJkZmQ2MWVkZDkyOTc4NTJmMGE0ZSIsInByb3ZpZGVyIjoiZ2l0aHViIn0sImlhdCI6MTc3MzI3NTkxMCwiZXhwIjoxNzc1ODY3OTEwfQ.ll-OrnKIv7ImnK5C44VZTQv9uglzdCzJC3pwk33QaU8vp3aqC9wxCAMH4jurAcSV3w3zi4UCZLLrL8V-4jmvjNHe4ScoLBd45cjNK-SpeqAdDrflJkRtRSoT4q3BeqfF-Mn_Khh6Ilbp18-_L2wf8TGt4onH5Q7Mj7HlkhVZ1BjuFklqcJwkzeV64GbRTTTEYzF_ggNfOlxfIeVVmTRSZuPSs8OUrPLFEG4FVXLaRxDw2BY09-fL2ZFFeQPOxCNvrjjyBYtfrPak8EtK3cCrzS0sBS_jFEd78QM41KYZS6C3rJhM7Krb_b0Z6voXgZqvLqDhYo6W4sUQn1hwqBwW3g" target="_blank" rel="noopener noreferrer"><picture><source media="(prefers-color-scheme: dark)" srcset="https://cursor.com/assets/images/fix-in-web-dark.png"><source media="(prefers-color-scheme: light)" srcset="https://cursor.com/assets/images/fix-in-web-light.png"><img alt="Fix in Web" width="99" height="28" src="https://cursor.com/assets/images/fix-in-web-dark.png"></picture></a></div>

**[user]** on `api/segments/serializers.py`:

### Wrong project object persists in validated_data alongside correct project_id

**Medium Severity**

<!-- DESCRIPTION START -->
The `project` field in the serializer is still writable and required, so `validated_data` carries the attacker-supplied `Project` object from the request body. `perform_create` adds `project_id` (correct) alongside this wrong `project`. The fix relies on Django's `Model.__init__` processing `project_id` *after* `project` in dict iteration order to override the FK value — a correct but fragile implicit dependency for a security-critical operation. Making `project` read-only (or popping it from `validated_data` before creation) would eliminate the wrong value entirely rather than relying on override ordering.
<!-- DESCRIPTION END -->

<!-- BUGBOT_BUG_ID: df1bd285-0bc0-47c9-a8e3-73aa2bf40166 -->

<!-- LOCATIONS START
api/segments/serializers.py#L109-L110
api/segments/views.py#L137-L139
LOCATIONS END -->
<details>
<summary>Additional Locations (1)</summary>

- [`api/segments/views.py#L137-L139`](https://github.com/Flagsmith/flagsmith/blob/9d8eb8eac2ea2d8fca4f0e2e0e945b6b95a16953/api/segments/views.py#L137-L139)

</details>

<div><a href="https://cursor.com/open?data=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImJ1Z2JvdC12MiJ9.eyJ2ZXJzaW9uIjoxLCJ0eXBlIjoiQlVHQk9UX0ZJWF9JTl9DVVJTT1IiLCJkYXRhIjp7InJlZGlzS2V5IjoiYnVnYm90OmMyNDk2ZjY0LTdiNTgtNGI0ZC05MjU2LWZiNDE4YWZiNWQzZSIsImVuY3J5cHRpb25LZXkiOiJGQlNOOFBEQl9lc1dJQW1rVzMwTkFUQzIxb1pnZG51RmttLUZaZ0U2SUljIiwiYnJhbmNoIjoiZml4L2NyZWF0ZS1zZWdtZW50LXByb2plY3QtcmVmZXJlbmNlIiwicmVwb093bmVyIjoiRmxhZ3NtaXRoIiwicmVwb05hbWUiOiJmbGFnc21pdGgifSwiaWF0IjoxNzczMjg0MzEzLCJleHAiOjE3NzU4NzYzMTN9.K5rvMj4TjWEHf-sSNRYnxs4SJUhXQ68uKfou5VHq7k1mnn8vqq1P4lwVnUVG9Vs_kDWv5VB_vwLDkkc4ZUgpnvSyNMJtb3iFbdbwXZKgj6sSSWZduCNv4U_79w8fUHCMxAAIQ8khaK1JMNuj0pvHRIa9IxIDXWCrKhkRc0ZaqBYts_QV-p6Np2ICSqyTRkwAz5yv-KMa2dil5c1_wH81aSOeQdxASr--nrfjSiRgJfRMHQt8thRm_zd7d9J-MM8fBbTh854TSTTafqeTNZF_z_4ilyFlQWa4okfvDZ6I6ufiYDySgCXU7zu77v2BOd2I_j1ewbF7TcccWB8oUQj8Cw" target="_blank" rel="noopener noreferrer"><picture><source media="(prefers-color-scheme: dark)" srcset="https://cursor.com/assets/images/fix-in-cursor-dark.png"><source media="(prefers-color-scheme: light)" srcset="https://cursor.com/assets/images/fix-in-cursor-light.png"><img alt="Fix in Cursor" width="115" height="28" src="https://cursor.com/assets/images/fix-in-cursor-dark.png"></picture></a>&nbsp;<a href="https://cursor.com/agents?data=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImJ1Z2JvdC12MiJ9.eyJ2ZXJzaW9uIjoxLCJ0eXBlIjoiQlVHQk9UX0ZJWF9JTl9XRUIiLCJkYXRhIjp7InJlZGlzS2V5IjoiYnVnYm90OmMyNDk2ZjY0LTdiNTgtNGI0ZC05MjU2LWZiNDE4YWZiNWQzZSIsImVuY3J5cHRpb25LZXkiOiJGQlNOOFBEQl9lc1dJQW1rVzMwTkFUQzIxb1pnZG51RmttLUZaZ0U2SUljIiwiYnJhbmNoIjoiZml4L2NyZWF0ZS1zZWdtZW50LXByb2plY3QtcmVmZXJlbmNlIiwicmVwb093bmVyIjoiRmxhZ3NtaXRoIiwicmVwb05hbWUiOiJmbGFnc21pdGgiLCJwck51bWJlciI6NjkyOSwiY29tbWl0U2hhIjoiOWQ4ZWI4ZWFjMmVhMmQ4ZmNhNGYwZTJlMGU5NDViNmI5NWExNjk1MyIsInByb3ZpZGVyIjoiZ2l0aHViIn0sImlhdCI6MTc3MzI4NDMxMywiZXhwIjoxNzc1ODc2MzEzfQ.RRffBVEUaUi2XwYV7KFdiFeNvA3v5zxioHhuV7DZ3hX2GT_IbTYZJaDMboN8K1pbAjNSugr_rpa-Wbe55n9K4Kbbsh65nXixrnT8lPm9rd_x3GlQKeCkq6zn2HWvjazRhhj5EwhMjTt4rkTd7DoS8n3oUcN16SQ0sFhbgKvyVr87w5twwAGVnr6igpJO66vyOAzsq0ySzfNwfxtlx1EyHw9u6FdX7vERxbEr1joD9HqcdRbvK2zV05lY23zK3g9FX9peHq2Sclz7XSrOOVBNyN2aNI0_263gMH0LfrbAXqqUZLqLeVj7v6qV8LKdFuaxYHWnWwLa_SG15ejY8ZWOCQ" target="_blank" rel="noopener noreferrer"><picture><source media="(prefers-color-scheme: dark)" srcset="https://cursor.com/assets/images/fix-in-web-dark.png"><source media="(prefers-color-scheme: light)" srcset="https://cursor.com/assets/images/fix-in-web-light.png"><img alt="Fix in Web" width="99" height="28" src="https://cursor.com/assets/images/fix-in-web-dark.png"></picture></a></div>

**[user]** on `api/segments/serializers.py`:

[user]  this sounds reasonable? Maybe mark project as read only?

**[user]** on `api/segments/serializers.py`:

Making `project` read only in the serialiser was my first approach (9d669cfbaad36ca3708bdfd61edd9297852f0a4e), but it led to a test failure in flagsmith-workflows. I made a compromise (6e5a7099b1d10b182149f47f5f429a50fad90dfd) so that the behaviour in SaaS is correct for now, and added a new issue (https://github.com/Flagsmith/flagsmith-workflows/issues/102) to follow up.

**[user]** on `api/segments/serializers.py`:

Would it be a good idea for now (at least from a documentation perspective) to also add a line in `validate` like: 

```python 
# ignore the project attribute in the request body in favour of the URL arg
# TODO: make project read-only as per https://github.com/Flagsmith/flagsmith-workflows/issues/102
del attrs["project"]
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
