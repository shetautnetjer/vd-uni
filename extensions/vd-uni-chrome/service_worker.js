const STATE_KEY = "vd_capture_state";
const URL_KEY = "vd_captured_urls";

let captureEnabled = true;

const looksLikeMediaSegment = (url) => {
  const lower = url.toLowerCase();
  return (
    lower.endsWith(".ts") ||
    lower.includes(".ts?") ||
    lower.endsWith(".m3u8") ||
    lower.includes(".m3u8?")
  );
};

const loadState = async () => {
  const data = await chrome.storage.local.get([STATE_KEY, URL_KEY]);
  if (data[STATE_KEY] && typeof data[STATE_KEY].enabled === "boolean") {
    captureEnabled = data[STATE_KEY].enabled;
  } else {
    await chrome.storage.local.set({
      [STATE_KEY]: { enabled: true },
      [URL_KEY]: [],
    });
  }
};

chrome.runtime.onInstalled.addListener(() => {
  loadState();
});

chrome.runtime.onStartup.addListener(() => {
  loadState();
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== "local") return;
  if (changes[STATE_KEY]) {
    captureEnabled = !!changes[STATE_KEY].newValue?.enabled;
  }
});

chrome.webRequest.onCompleted.addListener(
  async (details) => {
    if (!captureEnabled) return;
    if (!looksLikeMediaSegment(details.url)) return;

    const data = await chrome.storage.local.get(URL_KEY);
    const existing = Array.isArray(data[URL_KEY]) ? data[URL_KEY] : [];
    if (existing.includes(details.url)) return;

    existing.push(details.url);
    await chrome.storage.local.set({ [URL_KEY]: existing });
  },
  { urls: ["<all_urls>"] }
);
