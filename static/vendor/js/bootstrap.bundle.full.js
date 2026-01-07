/* Full Bootstrap placeholder: replace with official bootstrap.bundle.min.js for full functionality. */
// Minimal shim for common bootstrap behaviors used in templates
window.bootstrap = window.bootstrap || {};
(function(){
  // Provide dropdown toggle/shim if needed (very small subset)
  document.addEventListener('click', function(e){
    var t = e.target;
    if (t && t.matches && t.matches('[data-bs-toggle]')) {
      var target = document.querySelector(t.getAttribute('data-bs-target'));
      if (target) {
        target.classList.toggle('show');
      }
    }
  });
})();
