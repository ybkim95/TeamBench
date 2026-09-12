# GH397_napari_7053: Bump the settings schema version — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/napari/napari/issues/5316
- Repo: https://github.com/napari/napari

## Issue Description

## 🐛 Bug

In #5103 we changed the schema of napari settings, but did not bump the [schema version number](https://github.com/napari/napari/blob/1cc90a74211c6cbf3fc644da5866f9752cf1ac78/napari/settings/_napari_settings.py#L19).

If I understand the implementation correctly, I believe we also need to provide a migrator from 0.5.0 to 0.6.0, in order for the new schema version to actually be written to the new settings file.

We should probably write at least one test to cover this migration path.

This is somewhat related to #5314, as I would expect older versions of napari to respond in some useful way to future versions of the schema (e.g. by warning and ignoring them).

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[user] any chance you could handle this before the release? Seems important 😅 but I don't really know what needs doing 😅😅😅

### Comment 2 ([user]):

When I said "we", I didn't me the royal we - I didn't write much of this and don't have an immediate idea of how to fix this! Seems like past-me had some ideas, but it would take a little while for me to catch back up with them.

I also think one of the main issues here was fixed in (withheld: the upstream fix is not part of the task) , so I'm not sure if this is still a high priority.

### Comment 3 ([user]):

[user] ok your cluelessness prompted me to read things in a bit more detail. 😂 

Looking at #5103, it only *added* functionality, and it seems to do that "outside" of the schema anyway (?) for pydantic-y reasons that I don't understand, and this message in the schema:

https://github.com/napari/napari/blob/1cc90a74211c6cbf3fc644da5866f9752cf1ac78/napari/settings/_napari_settings.py#L25-L30

says

> You don't need to touch this value if you're just adding a new option

so I think actually we *don't* need to update the schema version?

### Comment 4 ([user]):

But the representation changed? If you look at a settings file from before and after they are not compatible.
Which, prior to silo'ing settings (withheld: the upstream fix is not part of the task), meant that the changes from (withheld: the upstream fix is not part of the task) made napari not launchable if you had `main` installed anywhere, see: 
https://napari.zulipchat.com/#narrow/stream/320379-core-devs/topic/Keybind.20breaking.20change

Now I suspect though that if you do an upgrade in place from 0.4.19 to 0.5.0 the issue will return.

### Comment 5 ([user]):

Oh, interesting, thanks for the background [user]! So would an update to the schema number magically fix things? Or is there work to do re migration of the settings? 🤔

### Comment 6 ([user]):

So I tried this:
- install 0.4.19 from pypi as normal (napari[all])
- checked that it worked and set some keybinds and theme to ensure that settings were used
- then I did `pip install -U .` in my napari repo (main checked out)
So napari launches, which is good, but there a buncha warnings:
```
/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/utils/action_manager.py:322: UserWarning: `` does not seem to be a valid shortcut Key.
  shorts = jstr.join(f'{Shortcut(s)}' for s in self._shortcuts[name])
/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/_qt/widgets/qt_welcome.py:105: UserWarning: `` does not seem to be a valid shortcut Key.
  self._shortcut_label.setText(Shortcut(shortcut_list[0]).platform)
/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/utils/action_manager.py:322: UserWarning: `` does not seem to be a valid shortcut Key.
  shorts = jstr.join(f'{Shortcut(s)}' for s in self._shortcuts[name])
/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/utils/action_manager.py:322: UserWarning: `` does not seem to be a valid shortcut Key.
  shorts = jstr.join(f'{Shortcut(s)}' for s in self._shortcuts[name])
```

~~The custom setting I used does appear to work as do other shortcuts.~~

Edit: Striking the above, I dunno what I did before, but upgrading in place to the alpha from pypi, I actually see issues with the shortcuts, see: https://github.com/napari/napari/issues/5316#issuecomment-2204506577

### Comment 7 ([user]):

Aha! If I then in the same env downgrade napari, then I'm screwed: it doesn't launch:
```
/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/_qt/qt_viewer.py:426: UserWarning: Attempting to unbind an action which does not exists (napari:activate_labels_polygon_mode), this may have no effects. This can happen if your settings are out of date, if you upgraded napari, upgraded or deactivated a plugin, or made a typo in in your custom keybinding.
  action_manager.unbind_shortcut(action)
/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/_qt/qt_viewer.py:426: UserWarning: Attempting to unbind an action which does not exists (napari:swap_selected_and_background_labels), this may have no effects. This can happen if your settings are out of date, if you upgraded napari, upgraded or deactivated a plugin, or made a typo in in your custom keybinding.
  action_manager.unbind_shortcut(action)
/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/_qt/qt_viewer.py:426: UserWarning: Attempting to unbind an action which does not exists (napari:reset_polygon), this may have no effects. This can happen if your settings are out of date, if you upgraded napari, upgraded or deactivated a plugin, or made a typo in in your custom keybinding.
  action_manager.unbind_shortcut(action)
/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/_qt/qt_viewer.py:426: UserWarning: Attempting to unbind an action which does not exists (napari:complete_polygon), this may have no effects. This can happen if your settings are out of date, if you upgraded napari, upgraded or deactivated a plugin, or made a typo in in your custom keybinding.
  action_manager.unbind_shortcut(action)
Traceback (most recent call last):
  File "/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/bin/napari", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/__main__.py", line 570, in main
    _run()
  File "/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/__main__.py", line 326, in _run
    viewer = Viewer()
             ^^^^^^^^
  File "/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/viewer.py", line 67, in __init__
    self._window = Window(self, show=show)
                   ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/_qt/qt_main_window.py", line 638, in __init__
    self._qt_window = _QtMainWindow(viewer, self)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/_qt/qt_main_window.py", line 114, in __init__
    self._qt_viewer = QtViewer(viewer, show_welcome_screen=True)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/_qt/qt_viewer.py", line 296, in __init__
    self._bind_shortcuts()
  File "/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/_qt/qt_viewer.py", line 428, in _bind_shortcuts
    action_manager.bind_shortcut(action, shortcut)
  File "/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/utils/action_manager.py", line 268, in bind_shortcut
    self._update_shortcut_bindings(name)
  File "/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/utils/action_manager.py", line 187, in _update_shortcut_bindings
    km_provider.bind_key(shortcut, action.injected, overwrite=True)
  File "/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/utils/key_bindings.py", line 283, in bind_key
    key = normalize_key_combo(key)
          ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/piotrsobolewski/Dev/miniforge3/envs/nap-settings/lib/python3.11/site-packages/napari/utils/key_bindings.py", line 185, in normalize_key_combo
    raise TypeError(
TypeError: invalid key 
```

### Comment 8 ([user]):

Also, it's not just keybinds. Octree is removed, some other settings related to the lasso tool have been added.

We could revisit something like 
(withheld: the upstream fix is not part of the task)
where within a per-env settings folder there would be versioned settings. So if you changed versions in the same env you'd be covered.

### Comment 9 ([user]):

[user] thanks for doing that experiment! 🧑‍🔬 So what happens if you do the same thing, but before installing main, you change the schema version number to 0.6.0?

tbh though I'm less concerned about downgrades. In the words of Thomas Wade from Three Body Problem: Always Advance! 😜

### Comment 10 ([user]):

OK, not sure what I did previously but what I just did:
- make a fresh 3.12 env
- install napari[all]
- run napari, change theme and set some shortcuts
- `pip install --pre napari -U`
- got the new alpha
- Run it, get warnings:
```
/Users/piotrsobolewski/Dev/miniforge3/envs/napari-419/lib/python3.12/site-packages/napari/utils/action_manager.py:322: UserWarning: `` does not seem to be a valid shortcut Key.
  shorts = jstr.join(f'{Shortcut(s)}' for s in self._shortcuts[name])
/Users/piotrsobolewski/Dev/miniforge3/envs/napari-419/lib/python3.12/site-packages/napari/_qt/widgets/qt_welcome.py:105: UserWarning: `` does not seem to be a valid shortcut Key.
  self._shortcut_label.setText(Shortcut(shortcut_list[0]).platform)
/Users/piotrsobolewski/Dev/miniforge3/envs/napari-419/lib/python3.12/site-packages/napari/utils/action_manager.py:322: UserWarning: `` does not seem to be a valid shortcut Key.
  shorts = jstr.join(f'{Shortcut(s)}' for s in self._shortcuts[name])
/Users/piotrsobolewski/Dev/miniforge3/envs/napari-419/lib/python3.12/site-packages/napari/utils/action_manager.py:322: UserWarning: `` does not seem to be a valid shortcut Key.
  shorts = jstr.join(f'{Shortcut(s)}' for s in self._shortcuts[name])
/Users/piotrsobolewski/Dev/miniforge3/envs/napari-419/lib/python3.12/site-packages/napari/_qt/widgets/qt_keyboard_settings.py:260: UserWarning: `` does not seem to be a valid shortcut Key.!
```
But now the new keybind I set doesn't work and in fact anything that used Command previously is broken:
<img width="1232" alt="image" src="https://github.com/napari/napari/assets/76622105/a36168b3-8699-4d73-9ee8-276dcba4d25b">

## PR Review Comments

**[user]** on `napari/utils/key_bindings.py`:

I don't fully understand how this interacts with the 0.5.0 -> 0.6.0 migrator.

But this addition seems reasonable, assuming we want cross-platform consistency.

**[user]** on `napari/utils/key_bindings.py`:

Oh sorry this line specifically is ancillary, I'm not even sure Command is a valid shortcut currently, *but* I wanted to be able to write Command in a config file and have it work 😂 Sorry that is a red herring in review!

**[user]** on `napari/utils/key_bindings.py`:

An explicit test would probably be enough for me to understand though.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
