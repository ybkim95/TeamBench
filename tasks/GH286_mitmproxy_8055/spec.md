# GH286_mitmproxy_8055: Use fastest compression settings for content-encoding — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/mitmproxy/mitmproxy

## PR Description

#### Description

Changed all content-encoding compression algorithms to use fastest settings instead of defaults optimized for compression ratio. When users assign to `message.content`, encoding happens transparently and slow compression directly impacts addon runtime.

**Compression settings updated:**
- Brotli: `quality=0` (was 11) - 80x faster
- Gzip: `compresslevel=1` (was 9) - 4x faster  
- Deflate: `level=1` (was 6) - 6x faster
- Zstd: `level=1` (was 3) - 4x faster

Trade-off: 10-70% larger compressed output (still compressed) for significantly faster encoding. Appropriate for proxy use case where throughput matters more than optimal compression.

#### Checklist

 - [ ] I have updated tests where applicable.
 - [x] I have added an entry to the CHANGELOG.

<!-- START COPILOT ORIGINAL PROMPT -->

<details>

<summary>Original prompt</summary>

> 
> ----
> 
> *This section details on the original issue you should resolve*
> 
> <issue_title>Add a flag/option that will switch to faster compression for content-encoding</issue_title>
> <issue_description>#### Problem Description
> 
> This came up in https://github.com/mitmproxy/mitmproxy/discussions/8040
> 
> We are using `brotli.compress` which yields best compression but is much slower with default options (https://github.com/google/brotli/blob/5fa73e23bee34f84148719576a7a434f0fc43dc8/python/brotli.py#L25C1-L25C74). We might want to add an option that will allow switching to fastest compression (not just for br, but gzip as well).
> 
> Given that this happens transparently when people are assigning to `.content` they might not realize the impact on addon runtime.
> 
> #### Proposal
> 
> Boolean `--fast-content-encoding` that will make all our compression calls use the lowest compression but fastest speed.
> 
> #### Alternatives
> 
> The question is if we should just switch to fastest compression by default? This would negatively impact people using mitmproxy on a remote network. But then we could just add a flag to switch to best compression.
> </issue_description>
> 
> <agent_instructions>all encoding algorithms should use options with the lowest but fastest compression in mitmproxy/net/encoding.py</agent_instructions>
> 
> ## Comments on the Issue (you are [user] in this section)
> 
> <comments>
> <comment_new><author>[user]</author><body>
> > The question is if we should just switch to fastest compression by default?
> 
> +1 to this.</body></comment_new>
> </comments>
> 

</details>

<!-- START COPILOT CODING AGENT SUFFIX -->

- Fixes mitmproxy/mitmproxy#8053

<!-- START COPILOT CODING AGENT TIPS -->
---

💬 We'd love your input! Share your thoughts on Copilot coding agent in our [2 minute survey](https://gh.io/copilot-coding-agent-survey).

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
