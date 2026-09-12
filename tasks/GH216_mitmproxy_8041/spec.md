# GH216_mitmproxy_8041: Fix mitmweb blank page on Windows due to incorrect JavaScript MIME type — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/mitmproxy/mitmproxy

## PR Description

#### Description

On Windows systems with `text/plain` registry entries for `.js` files, mitmweb serves JavaScript with the wrong MIME type. Browsers enforce strict MIME type checking for ES6 module scripts, rejecting `text/plain` and rendering a blank page.

**Changes:**
- Override JavaScript MIME type at module import in `app.py`:
  ```python
  mimetypes.add_type("text/javascript", ".js")
  ```
- Add integration test that makes an actual HTTP request through Tornado to verify the Content-Type header is correctly set to `text/javascript`
- Add changelog entry documenting the fix

**Root cause:** Python's `mimetypes` module queries the OS registry on Windows. Some Windows versions incorrectly map `.js` → `text/plain`. Tornado inherits this when serving static files.

**MIME type selection:** Uses `text/javascript` per RFC 9239, which is the standard MIME type for JavaScript content (not `application/javascript`).

**Test implementation:** The test dynamically finds JavaScript files in the static directory using pathlib to avoid brittleness when build artifacts are regenerated with different content hashes.

#### Checklist

 - [x] I have updated tests where applicable.
 - [x] I have added an entry to the CHANGELOG.

<!-- START COPILOT ORIGINAL PROMPT -->

<details>

<summary>Original prompt</summary>

> 
> ----
> 
> *This section details on the original issue you should resolve*
> 
> <issue_title>mitmweb: web did not show anything</issue_title>
> <issue_description>### Problem Description
> 
> command: mitmweb
> 
> <img width="1417" height="119" alt="Image" src="https://github.com/user-attachments/assets/5dfee435-05be-443b-ab5d-4f6eea5b9423" />
> 
> <img width="870" height="336" alt="Image" src="https://github.com/user-attachments/assets/1386135c-e673-4200-9e52-02bec840dba6" />
> 
> console error:
> - Failed to load module script: Expected a JavaScript-or-Wasm module script but the server responded with a MIME type of "text/plain". Strict MIME type checking is enforced for module scripts per HTML spec.
> - Loading the image 'blob:http://127.0.0.1:8081/xxx' violates the following Content Security Policy directive: "img-src 'self' data:". The action has been blocked.
> 
> <img width="1853" height="265" alt="Image" src="https://github.com/user-attachments/assets/4ef683fe-6813-43b8-b6e3-dac195f8ba24" />
> 
> 
> ### System Information
> 
> ```raw
> 
> ```
> 
> ### Checklist
> 
> - [x] This bug affects the [latest mitmproxy release](https://github.com/mitmproxy/mitmproxy/releases).</issue_description>
> 
> ## Comments on the Issue (you are [user] in this section)
> 
> <comments>
> <comment_new><author>[user]</author><body>
> Hi,
> 
> Thanks! Which is your system? And your browser?</body></comment_new>
> <comment_new><author>[user]</author><body>
> Please paste the output of the following command here: `mitmproxy --version`
> Also, let us know which browser you are currently using. Thanks!</body></comment_new>
> <comment_new><author>[user]</author><body>
> I haven't been able to reproduce this either. It works fine for me on macOS and Windows, using both Windows Store and other installs. Is there anything special in your folks' setup?</body></comment_new>
> <comment_new><author>[user]</author><body>
> I went down a rabbit hole and came back with
> 
> https://github.com/jupyterlite/jupyterlite/issues/569
> https://github.com/python/cpython/issues/76643
> https://github.com/python/cpython/issues/88141
> https://github.com/golang/go/issues/32350
> 
> TIL some libraries / languages use the OS to figure out mime types instead of shipping their own mapping. And some Windows versions seem to have text/plain set for js in the registry.
> 
> Did we change anything regarding Tornado / mitmweb in the breaking release that might have caused this to surface?</body></comment_new>
> <comment_new><author>[user]</author><body>
> [user] [user] can you run the following to confirm that the issue is the entry in your windows registry?
> 
> ```sh
> C:\>reg query HKCR\.js /v "Content Type"
> ```</body></comment_new>
> <comment_new><author>[user]</author><body>
> > Did we change anything regarding Tornado / mitmweb in the breaking release that might have caused this to surface?
> 
> It probably surfaced because of (withheld: the upstream fix is not part of the task) . Now with `<script type="module" crossorigin src></script>` it won't silently accept `text/plain` any longer.
> 
> Maybe we should just use `mimetypes.add_type` to override it for `.js`. [user] thoughts?</body></comment_new>
> <comment_new><author>[user]</author><body>
> > Maybe we should just use `mimetypes.add_type` to override it for `.js`. [user] thoughts?
> 
> That sounds like the right thing to do, thank you for digging into it. PRs welcome!</body></comment_new>
> </comments>
> 

</details>

<!-- START COPILOT CODING AGENT SUFFIX -->

- Fixes mitmproxy/mitmproxy#8024

<!-- START COPILOT CODING AGENT TIPS -->
---

💡 You can make Copilot smarter by setting up custom instructions, customizing its development environment and configuring Model Context Protocol (MCP) servers. Learn more [Copilot coding agent tips](https://gh.io/copilot-coding-agent-tips) in the docs.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
