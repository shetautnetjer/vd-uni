const STATE_KEY = "vd_capture_state";
const URL_KEY = "vd_captured_urls";

const captureToggle = document.getElementById("capture-toggle");
const segmentsToggle = document.getElementById("segments-toggle");
const urlList = document.getElementById("url-list");
const copyBtn = document.getElementById("copy-btn");
const downloadBtn = document.getElementById("download-btn");
const clearBtn = document.getElementById("clear-btn");

const refresh = async () => {
  const data = await chrome.storage.local.get([STATE_KEY, URL_KEY]);
  const urls = Array.isArray(data[URL_KEY]) ? data[URL_KEY] : [];
  const enabled = data[STATE_KEY]?.enabled ?? false;
  captureToggle.checked = enabled;
  segmentsToggle.checked = data[STATE_KEY]?.includeSegments ?? false;
  urlList.value = urls.join("\n");
};

const setCaptureEnabled = async (enabled) => {
  await chrome.storage.local.set({
    [STATE_KEY]: { enabled, includeSegments: segmentsToggle.checked },
  });
};

captureToggle.addEventListener("change", () => {
  setCaptureEnabled(captureToggle.checked);
});

segmentsToggle.addEventListener("change", () => { setCaptureEnabled(captureToggle.checked); });

copyBtn.addEventListener("click", async () => {
  await navigator.clipboard.writeText(urlList.value);
});

downloadBtn.addEventListener("click", () => {
  const blob = new Blob([urlList.value], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  chrome.downloads.download(
    {
      url,
      filename: "urls.txt",
      saveAs: true,
    },
    () => {
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
  );
});

clearBtn.addEventListener("click", async () => {
  await chrome.runtime.sendMessage({ type: "vd-clear" });
  urlList.value = "";
});

refresh();
chrome.storage.onChanged.addListener(() => {
  refresh();
});
