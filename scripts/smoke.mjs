const base = process.env.SMOKE_BASE_URL || 'http://127.0.0.1:3000';

async function check(path, predicate) {
  const response = await fetch(`${base}${path}`);
  const body = await response.text();
  if (!response.ok || !predicate(response, body)) {
    throw new Error(`${path} failed with ${response.status}: ${body.slice(0, 200)}`);
  }
  console.log(`ok ${path}`);
}

await check('/api/health', (_response, body) => JSON.parse(body).status === 'ok');
await check('/manus-routes.json', (response, body) => response.headers.get('content-type')?.includes('json') && JSON.parse(body).routes.length === 7);
console.log('Smoke checks passed.');
