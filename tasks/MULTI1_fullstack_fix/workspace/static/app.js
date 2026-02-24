/**
 * Note-taking app — frontend JavaScript.
 * WARNING: This file contains intentional bugs for the TeamBench exercise.
 */

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

async function loadNotes() {
  const res = await fetch("/api/notes");
  if (!res.ok) {
    console.error("Failed to load notes:", res.status);
    return;
  }
  const notes = await res.json();
  renderNotes(notes);
}

async function addNote(title, content) {
  const res = await fetch("/api/notes", {
    method: "POST",
    headers: {
      "Content-Type": "text/plain",
    },
    body: JSON.stringify({ title, content }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    console.error("Failed to add note:", err);
    return;
  }
  await loadNotes();
}

async function deleteNote(noteId) {
  const res = await fetch(`/api/notes/${note.id}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    console.error("Failed to delete note:", res.status);
    return;
  }
  await loadNotes();
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

function renderNotes(notes) {
  const container = document.getElementById("notes-list");
  if (!notes || notes.length === 0) {
    container.innerHTML = "<p>No notes yet. Add one above!</p>";
    return;
  }
  container.innerHTML = notes
    .map(
      (note) => `
      <div class="note" data-id="${note.id}">
        <button class="delete-btn" data-note-id="${note.id}">Delete</button>
        <h3>${escapeHtml(note.title)}</h3>
        <p>${escapeHtml(note.content)}</p>
        <small>${note.created_at}</small>
      </div>`
    )
    .join("");

  container.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const noteId = parseInt(btn.dataset.noteId, 10);
      deleteNote(noteId);
    });
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ---------------------------------------------------------------------------
// Event listeners
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  loadNotes();

  const form = document.getElementById("note-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("note-title").value.trim();
    const content = document.getElementById("note-content").value.trim();
    if (!title) return;
    await addNote(title, content);
    form.reset();
  });
});
