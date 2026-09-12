# GH848_urllib3_3732: Restore `getheaders()` and `getheader()` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/urllib3/urllib3/issues/3731
- Repo: https://github.com/urllib3/urllib3

## Issue Description

### Subject

The recent change to 2.6.0, included this change:

Removed the HTTPResponse.getheaders() method in favor of HTTPResponse.headers. Removed the HTTPResponse.getheader(name, default) method in favor of HTTPResponse.headers.get(name, default). (https://github.com/urllib3/urllib3/issues/3622)

This API change will most likely impact other libraries from easily updating to this version. Its not clear why a method would be removed in favour of using a variable. Couldn't both be supported so it doesn't break users of this object?

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Kubernetes client affected kubernetes-client/python#2280

### Comment 2 ([user]):

This led us down a 4 hour rabbit hole trying to figure out if the problem was anvil, docraptor, but no it was just this...

<img width="220" height="224" alt="Image" src="https://github.com/user-attachments/assets/2b007375-8455-41ba-af8b-d849b80250d2" />

### Comment 3 ([user]):

I can confirm this breaks the kubernetes package.

### Comment 4 ([user]):

It seems like there is a governance issue here. Since this is a breaking change, it would necessitate moving to 3.0 under semver.

The PR with the change has no information, it doesn't explain why (no PR body at all), no discussion on what problem it solves and why it's worth breaking most of the python ecosystem. It's literally just a naked change and then a merge. This suggests that probably there are other significant changes without oversight.

In turn this makes me wonder about security. since there was no oversight on this change, what if it was to introduce a back door? Would it too just get merged w/o comment?

Does the development process not require at least some rationale when opening a PR?

I understand the interface in question was marked as deprecated. Normally this means when you break it by removing it you move to the next major rather than just bump the minor.

### Comment 5 ([user]):

Seems people can find the PR and the warnings that were emitted prior to this that clearly identified when the deprecation was scheduled to take effect but are insistent on treating the maintainers of the project as if they're malicious and committing a treacherous act of malfeasance. 

Maybe, just maybe folks could listen to the warnings in their systems and treat other humans as if they're competent and doing their best

### Comment 6 ([user]):

> It seems like there is a governance issue here. Since this is a breaking change, it would necessitate moving to 3.0 under semver.

I don't think this is a valid claim and it's a bit unfair assessment [user] . One could ask how much you already contributed to urllib3 and tried to improve and introduce "different" governance and decision making.

Nowhere in the documentation of urllib they promise a SemVer compliance. There are many projects and libraries that choose not to use semver for their versioning. One glaring example is Python. Python does NOT Use semver. 3.13, 3.14 contain quite a number of removals. Same `pip`, and many other libraries and tools. 

And that's a choice library maintainers might make or not to follow SemVer. It's neither "expected" nor "demanded". You should never "expect" particular convention from someone, because *you* think someone else should do, but they never committed to it.

Even if we were (indirectly - via k8s client) affected in Apache Airflow, this is clearly a problem with users of urllib who have not updated. K8S client maintainers have to just roll their sleeves up  and fix the issue - they are using a feature that is **clearly** marked as removal in changelog and has been deprecated for more than 2.5 years: https://github.com/urllib3/urllib3/blob/main/CHANGES.rst#200-2023-04-26

There is absolutely nothing wrong Maintainers of urllib3 done here, they are simply doing what they are supposed to do - responsibly maintaining their library - with clear information, deprecation strategy and LOTS of time to update.

If you want to improve things - I suggest you comment on the issues in the libraries and tools that are still using a feature deprecated 2.5 years ago and lecture them on how they should fix their deprecations earlier. That would be a proper lecturing direction.

### Comment 7 ([user]):

The fastly client is affected as well. I opened a PR: (withheld: the upstream fix is not part of the task)

### Comment 8 ([user]):

> The fastly client is affected as well. I opened a PR: [fastly/fastly-py#112]((withheld: the upstream fix is not part of the task))

Thanks - commented there. I think this is really - as an interested community should do now - help urllib3 maintainers and put a little pressure on those who have not fixed the 2.5 old deprecation yet and let them know that their users expect it. My comment is that it enables the users to upgrade to 2.6.0 to get rid of those two vulnerabilities assessed as "high" severity - 8.9/10 both:

https://nvd.nist.gov/vuln/detail/CVE-2025-66471
https://nvd.nist.gov/vuln/detail/CVE-2025-66418

That might help the maintainers to prioritise their efforts - we all know that open-source maintainers have often other obligations - life, family, friends - or simply just being busy at work, so priority should be higher.

### Comment 9 ([user]):

While it's *absolutely* the prerogative of `urllib3` maintainers to make a call on what to deprecate and remove, removing a method in a minor version bump is going to cause widespread issues. Figuring out which 3rd party packages need upgrading is non-trivial in a complex codebase, and organisations typically have to work within fairly short SLOs for fixing `HIGH` vulnerabilities.

Would it be possible to consider a v2.6.1 that re-adds the deprecated methods? Looking at the code, the maintenance burden for these simple method shims seems low, as they're just proxies to the underlying attribute.

I'm sure there are a lot of security engineers right now that would be extremely grateful for this accommodation. ❤️

### Comment 10 ([user]):

> Yes - the [airflow-python-sdk](https://pypi.org/project/airflow-python-sdk/) is also affected. Took and hour to identify the issue. If I may ask - why was the method dropped?

Just FYI  this package is very old, unmaintained package by one of the commmunity members [user]  - who is very active in Airflow community and Apache Airflow for years releases an official, generated client https://pypi.org/project/apache-airflow-client/#history. But even our client - because it uses open-api generator - uses the "getheaders()" method in one place. 

I opened an issue in openapi-generator: https://github.com/OpenAPITools/openapi-generator/issues/22514  to let them know, We mightl patch it shortly if they won't fix it quickly  (we have been patched the generated code before) but indeed the impact is quite widespread I think because openapi-generator generates the code. It looks like kubernetes-client also uses getHeaders because of the same openapi-generator issue.

Again - I think we should help to pressurise those who have not removed their deprecations yet and a lot of people depend on it. Also - taking into accoun that openapi-generator is quite popular and even main version has the issue, maybe indeed maintainers should consider some remediations - but it's really up to them to decide, not any of us here. 

We can - however - help with just pushing those who are behind.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
