// Full jsQR placeholder: replace with the official minified jsQR bundle for offline QR decoding.
// For now, this file re-exports a minimal implementation that delegates to any existing jsQR function if present.
// To make scanning work offline, replace this file with the official jsQR minified source.
(function(global){
  // If a real jsQR is present (unlikely for local copy), keep it.
  if (typeof global._real_jsQR !== 'undefined') {
    global.jsQR = global._real_jsQR;
    return;
  }

  // Lightweight compatibility wrapper — this does not implement decoding.
  function jsQR(data, width, height, options) {
    // Attempt to require a real decoder if available via CommonJS (rare in browser context)
    if (typeof require === 'function') {
      try {
        var r = require('jsqr');
        if (r && typeof r === 'function') return r(data, width, height, options);
      } catch (e) {
        // ignore
      }
    }
    // No decoder available: return null (no QR detected)
    return null;
  }

  global.jsQR = jsQR;
})(typeof window !== 'undefined' ? window : this);
