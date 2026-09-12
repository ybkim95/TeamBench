# GH486_starlette_3145: Version 1.0.0rc1 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/Kludex/starlette

## PR Description

After a long time, here we have the first release candidate for Starlette 1.0! 🎉

Starlette has been stable for years now, so it's only reasonable to finally take this first step. This release removes deprecated features that were marked for removal in 1.0.0, along with some last minute bug fixes. See the full release notes for details.

cc [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] - I've mentioned each of you in the release notes. If you're not okay with being mentioned, please let me know and I'll happily adjust the text or remove your handle. Sorry the ping!

I plan to merge this in a few days.

## PR Review Comments

**[user]** on `docs/release-notes.md`:

```suggestion
## 1.0.0rc1 (February 21, 2026)
```

**[user]** on `docs/release-notes.md`:

```suggestion
* [Kim Christie](https://github.com/lovelydinosaur) - The original creator of Starlette, Uvicorn, and MkDocs, and the
```

**[user]** on `docs/release-notes.md`:

```suggestion
  current maintainer of HTTPX. Tom's work helped lay the foundation for the modern async Python ecosystem.
```

**[user]** on `docs/release-notes.md`:

> so we can gather feedback

I've got mixed feelings about the project name. It's awkward at times[^1], though *shrug*. Perhaps a bit late in the day to discuss a rebrand?

I do also feel like there's options for more of a community model of ownership for `uvicorn` and `starlette`. The 1.0 might be a good time to do that? I don't feel like we really navigated this in the best way previously, and might be an opportunity to reassess?

[^1]: I liked the literal "little star" and nod to [user]'s `datasette` project. Though I've seen it transcribed as "starlet", which is such an archaic diminutive, and projects particularly oddly given the skewed gender representation.

**[user]** on `docs/release-notes.md`:

Kim, it seems we keep getting back to the same subjects over and over again.

1.0 to me doesn't mean anything changes, it means that we show the world it's stable.

---

> I've got mixed feelings about the project name. It's awkward at times[1]((withheld: the upstream fix is not part of the task)#user-content-fn-1-3d47296fb0130947a0ef5ff998ddc634), though shrug. Perhaps a bit late in the day to discuss a rebrand?

I don't think the name of the project should change. It will confuse the ecosystem.

> I do also feel like there's options for more of a community model of ownership for uvicorn and starlette. The 1.0 might be a good time to do that? I don't feel like we really navigated this in the best way previously, and might be an opportunity to reassess?

We discussed this for 2 years. We went around about many different solutions. I was unhappy, we tried some things, I told you the alternative was to fork, which I was fine. I don't want to keep going around, things are good now. The repositories are well maintained.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
