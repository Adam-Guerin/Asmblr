import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';

const port = process.env.SMOKE_PORT || '3100';
const baseUrl = `http://127.0.0.1:${port}`;
const nextBin =
  process.platform === 'win32' ? 'node_modules\\.bin\\next.cmd' : 'node_modules/.bin/next';

const server = spawn(nextBin, ['start', '-p', port], {
  stdio: ['ignore', 'pipe', 'pipe'],
  shell: false,
});

server.stdout.on('data', (data) => process.stdout.write(data));
server.stderr.on('data', (data) => process.stderr.write(data));
server.on('error', (error) => {
  console.error('Smoke: failed to start server.', error);
});

const shutdown = () => {
  if (!server.killed) {
    server.kill();
  }
};

process.on('exit', shutdown);
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

const waitForServer = async () => {
  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${baseUrl}/`);
      if (res.ok) return true;
    } catch {
      // retry until deadline
    }
    await delay(500);
  }
  return false;
};

const assertOk = async (label, url, predicate) => {
  const res = await fetch(url);
  const body = await res.text();
  if (!res.ok) {
    throw new Error(`${label} failed: ${res.status}`);
  }
  if (!(await predicate(body))) {
    throw new Error(`${label} failed validation`);
  }
  return body;
};

const run = async () => {
  const ready = await waitForServer();
  if (!ready) {
    throw new Error('Smoke: server did not respond on /');
  }
  await assertOk('Page', `${baseUrl}/`, async (body) => body.length > 200);
  await assertOk('API', `${baseUrl}/api/status`, async (body) => {
    try {
      const payload = JSON.parse(body);
      return Boolean(payload?.status);
    } catch {
      return false;
    }
  });
  console.log('Smoke: page and API responded successfully.');
};

run()
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(() => {
    shutdown();
  });
