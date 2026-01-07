// Minimal fallback for jsQR used when CDN is blocked.
// Implements a stub jsQR(data, width, height, opts) that returns null (no QR found).
function jsQR(data, width, height, options) {
  // Fallback: can't decode in this lightweight fallback.
  return null;
}
if (typeof module !== 'undefined') { module.exports = jsQR; }
