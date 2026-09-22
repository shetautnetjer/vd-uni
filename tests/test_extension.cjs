const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../extensions/vd-uni-chrome');

function helper() {
  assert.ok(fs.existsSync(path.join(root, 'media.js')), 'Media classifier must exist');
  return require(path.join(root, 'media.js'));
}

test('recognizes manifests, common files, and extensionless video MIME', () => {
  const { classifyMedia } = helper();
  for (const url of ['https://example.test/LIVE.M3U8?sig=123', 'https://example.test/live.mpd']) {
    assert.equal(classifyMedia(url), 'manifest');
  }
  for (const ext of ['mp4', 'mkv', 'mov', 'webm', 'avi', 'm4v', 'flv', 'wmv', 'mxf', 'vob']) {
    assert.equal(classifyMedia(`https://example.test/video.${ext}?token=123`), 'video');
  }
  assert.equal(classifyMedia('https://example.test/watch/123', 'video/mp4; codecs=avc1'), 'video');
  assert.equal(classifyMedia('https://example.test/watch/123', 'application/dash+xml'), 'manifest');
});

test('distinguishes segments and rejects non-media URLs', () => {
  const { classifyMedia } = helper();
  assert.equal(classifyMedia('https://example.test/part.ts'), 'segment');
  assert.equal(classifyMedia('https://example.test/part.m4s'), 'segment');
  assert.equal(classifyMedia('blob:https://example.test/123', 'video/mp4'), null);
  assert.equal(classifyMedia('https://example.test/page', 'text/html'), null);
  assert.equal(classifyMedia('not a URL'), null);
});

test('bounded URL storage deduplicates without changing signed queries', () => {
  const { addCaptured } = helper();
  assert.deepEqual(addCaptured(['a', 'b'], 'a', 2), ['a', 'b']);
  assert.deepEqual(addCaptured(['a', 'b'], 'c', 2), ['b', 'c']);
  assert.deepEqual(addCaptured(['video?sig=1'], 'video?sig=2'), ['video?sig=1', 'video?sig=2']);
});

function worker(initial = {}) {
  helper();
  let data = structuredClone(initial);
  const events = {};
  const event = (name) => ({ addListener(fn) { events[name] = fn; } });
  const chrome = {
    storage: { local: {
      async get(keys) { await new Promise(r => setImmediate(r)); return structuredClone(data); },
      async set(values) { await new Promise(r => setImmediate(r)); Object.assign(data, structuredClone(values)); },
    } },
    runtime: { onInstalled: event('installed'), onStartup: event('startup'), onMessage: event('message') },
    webRequest: { onHeadersReceived: event('capture') },
  };
  const context = vm.createContext({ chrome, URL, console, Promise });
  context.importScripts = file => vm.runInContext(fs.readFileSync(path.join(root, file), 'utf8'), context);
  vm.runInContext(fs.readFileSync(path.join(root, 'service_worker.js'), 'utf8'), context);
  return {
    data: () => data,
    async flush() { await vm.runInContext('pendingWrites', context); },
    capture(url) { events.capture({ url, statusCode: 200, tabId: 1, responseHeaders: [] }); },
    clear() { return new Promise(resolve => events.message({ type: 'vd-clear' }, {}, resolve)); },
  };
}

test('simultaneous requests do not lose captured URLs', async () => {
  const w = worker({ vd_capture_state: { enabled: true } });
  for (let i = 0; i < 30; i++) w.capture(`https://example.test/${i}.mp4`);
  await w.flush();
  assert.equal(w.data().vd_captured_urls.length, 30);
});

test('capture is opt-in and disabled state survives worker restart', async () => {
  for (const initial of [{}, { vd_capture_state: { enabled: false } }]) {
    const w = worker(initial);
    w.capture('https://example.test/video.mp4');
    await w.flush();
    assert.equal((w.data().vd_captured_urls || []).length, 0);
  }
});

test('segments require explicit opt-in; manifests remain captured', async () => {
  const w = worker({ vd_capture_state: { enabled: true } });
  w.capture('https://example.test/part.ts');
  w.capture('https://example.test/main.m3u8');
  await w.flush();
  assert.deepEqual(w.data().vd_captured_urls, ['https://example.test/main.m3u8']);
});

test('clear serializes with queued captures rather than resurrecting URLs', async () => {
  const w = worker({ vd_capture_state: { enabled: true } });
  w.capture('https://example.test/first.mp4');
  await w.clear();
  await w.flush();
  assert.deepEqual(w.data().vd_captured_urls, []);
});
