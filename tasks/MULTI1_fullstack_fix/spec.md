# MULTI1: Fullstack Bug Fix — Full Specification (Planner Only)

## Overview

A simple note-taking web application built with Flask (Python backend), vanilla JS/HTML (frontend), and a bash deploy script. The app has **6 bugs** spread across all 3 layers. All bugs must be fixed so that `python3 test_app.py` passes all 6 tests.

---

## Application Architecture

```
workspace/
  app.py               # Flask backend
  static/
    index.html         # Frontend HTML
    app.js             # Frontend JavaScript
  deploy.sh            # Bash deploy script
  test_app.py          # Test suite (do not modify)
```

The backend uses an in-memory SQLite database (created fresh on app startup). The frontend communicates with the backend via a JSON REST API.

---

## Bug Inventory

### Backend Bugs — `app.py`

**Bug 1: POST /api/notes reads wrong request attribute**
- Location: `POST /api/notes` route handler
- Symptom: `request.args` is used instead of `request.json`
- Effect: The `title` and `content` fields from the JSON body are always `None`; every note is created with null title/content
- Fix: Replace `request.args.get(...)` with `request.json.get(...)`

**Bug 2: GET /api/notes returns notes in wrong order**
- Location: `GET /api/notes` route handler
- Symptom: SQL query orders by `id ASC` (ascending), so oldest notes appear first
- Effect: Notes are returned oldest-first instead of newest-first
- Fix: Change `ORDER BY id` to `ORDER BY id DESC` in the SELECT query

**Bug 3: DELETE /api/notes/<id> uses wrong variable name in SQL binding**
- Location: `DELETE /api/notes/<id>` route handler
- Symptom: SQL parameter tuple uses `note_id` but the route variable is `id` (i.e., `(note_id,)` instead of `(id,)`)
- Effect: `NameError: name 'note_id' is not defined` at runtime; delete always fails
- Fix: Change `(note_id,)` to `(id,)` in the SQL execute call

---

### Frontend Bugs — `static/app.js`

**Bug 4: POST fetch sends wrong Content-Type header**
- Location: `addNote()` function, `fetch` call headers
- Symptom: `'Content-Type': 'text/plain'` is set instead of `'application/json'`
- Effect: Flask's `request.json` returns `None` even after Bug 1 is fixed, because Flask only parses JSON when Content-Type is `application/json`
- Fix: Change `'text/plain'` to `'application/json'`

**Bug 5: Delete button handler references undefined variable**
- Location: `deleteNote()` function or the delete button's event handler
- Symptom: Template literal uses `${note.id}` but the parameter variable is named `noteId`
- Effect: `undefined` is interpolated into the URL — DELETE request goes to `/api/notes/undefined`
- Fix: Change `${note.id}` to `${noteId}` in the fetch URL

---

### Deploy Script Bug — `deploy.sh`

**Bug 6: FLASK_APP points to wrong file**
- Location: `deploy.sh`, line setting `FLASK_APP`
- Symptom: `export FLASK_APP=application.py` — but the actual app file is `app.py`
- Effect: `flask run` fails with "Could not import 'application'"
- Fix: Change `application.py` to `app.py`

---

## Expected Outcome

After all 6 fixes are applied:

```
python3 test_app.py
```

Should produce output like:
```
......
----------------------------------------------------------------------
Ran 6 tests in 0.XXXs

OK
```

All 6 tests pass:
1. `test_create_note` — POST creates a note (201 response)
2. `test_get_notes` — GET returns a JSON list
3. `test_notes_sorted` — newest note appears first
4. `test_delete_note` — DELETE removes a note (200 response)
5. `test_deploy_script_env` — deploy.sh contains `FLASK_APP=app.py`
6. `test_frontend_content_type` — app.js contains `application/json`

---

## Constraints

- Do not modify `test_app.py`
- Only `flask` is available as an external dependency (plus Python stdlib: `sqlite3`, `json`, `unittest`)
- The SQLite database is in-memory (`:memory:`) — no persistent storage needed
