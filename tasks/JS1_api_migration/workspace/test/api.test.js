'use strict';

/**
 * api.test.js — Integration tests for the Task API.
 *
 * Tests are written against observable HTTP behaviour only (status codes +
 * JSON body shape), so they pass with a correctly-migrated Express v5 server
 * and would also pass with a correctly-written Express v4 server.
 *
 * Run: node test/api.test.js
 * Exit 0 on all pass, exit 1 on any failure.
 */

const http = require('http');
const { spawn } = require('child_process');
const path = require('path');
const assert = require('assert');

const PORT = 3000;
const BASE = `http://localhost:${PORT}`;

// ── Helpers ────────────────────────────────────────────────────────────────────

function request(method, urlPath, body) {
  return new Promise((resolve, reject) => {
    const payload = body ? JSON.stringify(body) : null;
    const options = {
      hostname: 'localhost',
      port: PORT,
      path: urlPath,
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(payload ? { 'Content-Length': Buffer.byteLength(payload) } : {}),
      },
    };
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        let parsed = null;
        try { parsed = data.length ? JSON.parse(data) : null; } catch (_) {}
        resolve({ status: res.statusCode, body: parsed, raw: data });
      });
    });
    req.on('error', reject);
    if (payload) req.write(payload);
    req.end();
  });
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

// ── Test runner ────────────────────────────────────────────────────────────────

const results = [];

async function test(name, fn) {
  try {
    await fn();
    results.push({ name, pass: true });
    console.log(`  PASS  ${name}`);
  } catch (err) {
    results.push({ name, pass: false, error: err.message });
    console.log(`  FAIL  ${name}`);
    console.log(`        ${err.message}`);
  }
}

// ── Tests ──────────────────────────────────────────────────────────────────────

async function runTests() {
  let createdId;

  // 1. GET /tasks returns 200 and a JSON array (possibly empty)
  await test('GET /tasks returns 200 with array', async () => {
    const res = await request('GET', '/tasks');
    assert.strictEqual(res.status, 200, `expected 200, got ${res.status}`);
    assert.ok(Array.isArray(res.body), `expected array, got ${JSON.stringify(res.body)}`);
  });

  // 2. POST /tasks creates a task and returns 201
  await test('POST /tasks creates a task (201)', async () => {
    const res = await request('POST', '/tasks', { title: 'Write tests', done: false });
    assert.strictEqual(res.status, 201, `expected 201, got ${res.status}`);
    assert.ok(res.body && typeof res.body.id === 'number', 'expected body.id to be a number');
    assert.strictEqual(res.body.title, 'Write tests', 'title mismatch');
    assert.strictEqual(res.body.done, false, 'done should be false');
    createdId = res.body.id;
  });

  // 3. GET /tasks/:id returns the created task
  await test('GET /tasks/:id returns the created task (200)', async () => {
    assert.ok(createdId !== undefined, 'createdId must be set by previous test');
    const res = await request('GET', `/tasks/${createdId}`);
    assert.strictEqual(res.status, 200, `expected 200, got ${res.status}`);
    assert.strictEqual(res.body.id, createdId, 'id mismatch');
    assert.strictEqual(res.body.title, 'Write tests', 'title mismatch');
  });

  // 4. PUT /tasks/:id updates the task and returns 200
  await test('PUT /tasks/:id updates the task (200)', async () => {
    assert.ok(createdId !== undefined, 'createdId must be set by previous test');
    const res = await request('PUT', `/tasks/${createdId}`, { title: 'Write tests', done: true });
    assert.strictEqual(res.status, 200, `expected 200, got ${res.status}`);
    assert.strictEqual(res.body.done, true, 'done should now be true');
    assert.strictEqual(res.body.id, createdId, 'id mismatch');
  });

  // 5. DELETE /tasks/:id removes the task and returns 204
  await test('DELETE /tasks/:id removes the task (204)', async () => {
    assert.ok(createdId !== undefined, 'createdId must be set by previous test');
    const res = await request('DELETE', `/tasks/${createdId}`);
    assert.strictEqual(res.status, 204, `expected 204, got ${res.status}`);
  });
}

// ── Main ───────────────────────────────────────────────────────────────────────

(async () => {
  const serverPath = path.resolve(__dirname, '..', 'server.js');

  // Start server subprocess
  const server = spawn(process.execPath, [serverPath], {
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, PORT: String(PORT) },
  });

  let startupOutput = '';
  server.stdout.on('data', (d) => (startupOutput += d));
  server.stderr.on('data', (d) => (startupOutput += d));

  // Wait for server to be ready
  let ready = false;
  for (let i = 0; i < 20; i++) {
    await sleep(300);
    try {
      await request('GET', '/tasks');
      ready = true;
      break;
    } catch (_) {}
  }

  if (!ready) {
    console.error('Server did not start within 6 s.');
    console.error(startupOutput);
    server.kill();
    process.exit(1);
  }

  try {
    await runTests();
  } finally {
    server.kill();
  }

  const passed = results.filter((r) => r.pass).length;
  const total = results.length;
  console.log(`\n${passed}/${total} tests passed`);

  if (passed !== total) {
    process.exit(1);
  }
})();
