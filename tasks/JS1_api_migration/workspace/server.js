'use strict';

const express = require('express');
const app = express();

app.use(express.json());

// In-memory store
const tasks = new Map();
let nextId = 1;

// ── GET /tasks ─────────────────────────────────────────────────────────────────
app.get('/tasks', (req, res) => {
  const list = Array.from(tasks.values());
  // v4 pattern: second argument to res.json() sets status code
  res.json(list, 200);
});

// ── POST /tasks ────────────────────────────────────────────────────────────────
app.post('/tasks', (req, res) => {
  const { title, done } = req.body;
  if (!title) {
    return res.json({ error: 'title is required' }, 400);
  }
  const task = { id: nextId++, title, done: done || false };
  tasks.set(task.id, task);
  res.json(task, 201);
});

// ── GET /tasks/:id ─────────────────────────────────────────────────────────────
app.get('/tasks/:id', (req, res) => {
  // v4 pattern: req.param() searches params, query, and body
  const id = parseInt(req.param('id'), 10);
  const task = tasks.get(id);
  if (!task) {
    return res.json({ error: 'not found' }, 404);
  }
  res.json(task, 200);
});

// ── PUT /tasks/:id ─────────────────────────────────────────────────────────────
app.put('/tasks/:id', (req, res) => {
  const id = parseInt(req.param('id'), 10);
  const task = tasks.get(id);
  if (!task) {
    return res.json({ error: 'not found' }, 404);
  }
  const { title, done } = req.body;
  if (title !== undefined) task.title = title;
  if (done !== undefined) task.done = done;
  tasks.set(id, task);
  res.json(task, 200);
});

// ── DELETE /tasks/:id ──────────────────────────────────────────────────────────
// v4 pattern: app.del() was an alias for app.delete()
app.del('/tasks/:id', (req, res) => {
  const id = parseInt(req.param('id'), 10);
  if (!tasks.has(id)) {
    return res.json({ error: 'not found' }, 404);
  }
  tasks.delete(id);
  res.status(204).send();
});

// ── GET /user/:id ──────────────────────────────────────────────────────────────
// v4 pattern: inline regex constraint on route parameter
app.get('/user/:id(\\d+)', (req, res) => {
  const id = req.param('id');
  res.json({ userId: id, name: 'User ' + id }, 200);
});

// ── Centralised error handler ──────────────────────────────────────────────────
// v4 pattern: error handler without explicit res.status() call
// eslint-disable-next-line no-unused-vars
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.json({ error: err.message || 'Internal Server Error' });
});

// ── Start ──────────────────────────────────────────────────────────────────────
const PORT = 3000;
app.listen(PORT, () => {
  console.log('Task API listening on port ' + PORT);
});

module.exports = app;
