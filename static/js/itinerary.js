// Show a spinner and disable the button while the itinerary is generated.
document.addEventListener("DOMContentLoaded", function () {
  var form = document.getElementById("trip-form");
  if (!form) return;
  form.addEventListener("submit", function () {
    var btn = document.getElementById("submit-btn");
    var spin = document.getElementById("spin");
    var label = document.getElementById("submit-label");
    // Disable on next tick so the form still submits.
    setTimeout(function () {
      btn.disabled = true;
      spin.classList.remove("d-none");
      label.textContent = "Generating...";
    }, 0);
  });
});
