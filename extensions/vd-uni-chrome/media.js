/* Pure helpers shared by the extension worker and its Node regression tests. */
(() => {
  const manifests = new Set(['m3u8', 'mpd']);
  const segments = new Set(['ts', 'm4s', 'cmfv', 'cmfa']);
  const videos = new Set(['mp4', 'mkv', 'mov', 'webm', 'avi', 'm4v', 'flv', 'wmv',
    'asf', 'mpg', 'mpeg', 'ogv', '3gp', '3g2', 'mts', 'm2ts', 'vob', 'mxf',
    'f4v', 'rm', 'rmvb', 'divx', 'm2v', 'hevc', 'h264', 'av1', 'nut']);
  function classifyMedia(url, contentType = '') {
    let parsed;
    try { parsed = new URL(url); } catch { return null; }
    if (!['http:', 'https:'].includes(parsed.protocol)) return null;
    const extension = parsed.pathname.toLowerCase().split('.').pop();
    const mime = contentType.toLowerCase().split(';')[0].trim();
    if (manifests.has(extension) || ['application/vnd.apple.mpegurl',
      'application/x-mpegurl', 'audio/mpegurl', 'audio/x-mpegurl',
      'application/dash+xml'].includes(mime)) return 'manifest';
    if (segments.has(extension) || mime === 'video/mp2t') return 'segment';
    if (videos.has(extension) || mime.startsWith('video/')) return 'video';
    return null;
  }
  function addCaptured(existing, url, limit = 500) {
    const urls = Array.isArray(existing) ? existing.filter(x => typeof x === 'string') : [];
    if (urls.includes(url)) return urls.slice(-limit);
    return [...urls, url].slice(-limit);
  }
  const api = { classifyMedia, addCaptured };
  globalThis.VDMedia = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})();
