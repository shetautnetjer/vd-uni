const STATE_KEY = "vd_capture_state";
const URL_KEY = "vd_captured_urls";

const captureToggle = document.getElementById("capture-toggle");
const urlList = document.getElementById("url-list");
const copyBtn = document.getElementById("copy-btn");
const downloadBtn = document.getElementById("download-btn");
const clearBtn = document.getElementById("clear-btn");

const refresh = async () => {
  const data = await chrome.storage.local.get([STATE_KEY, URL_KEY]);
  const urls = Array.isArray(data[URL_KEY]) ? data[URL_KEY] : [];
  const enabled = data[STATE_KEY]?.enabled ?? true;
  captureToggle.checked = enabled;
  urlList.value = urls.join("\n");
};

const setCaptureEnabled = async (enabled) => {
  await chrome.storage.local.set({
    [STATE_KEY]: { enabled },
  });
};

captureToggle.addEventListener("change", () => {
  setCaptureEnabled(captureToggle.checked);
});

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
  await chrome.storage.local.set({ [URL_KEY]: [] });
  urlList.value = "";
});

refresh();
chrome.storage.onChanged.addListener(() => {
  refresh();
});
