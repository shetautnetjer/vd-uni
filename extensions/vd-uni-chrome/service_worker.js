importScripts('media.js');
const STATE_KEY = 'vd_capture_state';
const URL_KEY = 'vd_captured_urls';
let pendingWrites = Promise.resolve();

// Serial read/modify/write prevents simultaneous fragments losing each other.
// Persisted state is checked on every operation, including worker restarts.
function enqueue(operation) {
  pendingWrites = pendingWrites.then(operation).catch(() => {
    console.warn('VD-uni could not update local capture storage.');
  });
  return pendingWrites;
}

chrome.runtime.onInstalled.addListener(() => enqueue(async () => {
  const data = await chrome.storage.local.get([STATE_KEY, URL_KEY]);
  if (!data[STATE_KEY]) {
    await chrome.storage.local.set({
      [STATE_KEY]: { enabled: false, includeSegments: false }, [URL_KEY]: [],
    });
  }
}));

chrome.webRequest.onHeadersReceived.addListener(details => {
  if (details.tabId < 0 || details.statusCode < 200 || details.statusCode >= 300) return;
  const contentType = (details.responseHeaders || [])
    .find(header => header.name.toLowerCase() === 'content-type')?.value || '';
  const kind = VDMedia.classifyMedia(details.url, contentType);
  if (!kind) return;
  enqueue(async () => {
    const data = await chrome.storage.local.get([STATE_KEY, URL_KEY]);
    if (data[STATE_KEY]?.enabled !== true) return;
    if (kind === 'segment' && data[STATE_KEY]?.includeSegments !== true) return;
    const urls = VDMedia.addCaptured(data[URL_KEY], details.url);
    await chrome.storage.local.set({ [URL_KEY]: urls });
  });
}, { urls: ['http://*/*', 'https://*/*'] }, ['responseHeaders']);

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== 'vd-clear') return false;
  enqueue(() => chrome.storage.local.set({ [URL_KEY]: [] }))
    .then(() => sendResponse({ ok: true }));
  return true;
});
