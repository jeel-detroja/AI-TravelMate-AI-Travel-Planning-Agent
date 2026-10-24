// Auto-dismiss success/info alerts after a few seconds.
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".alert-success, .alert-info").forEach(function (el) {
    setTimeout(function () {
      if (window.bootstrap) {
        bootstrap.Alert.getOrCreateInstance(el).close();
      }
    }, 6000);
  });
});
