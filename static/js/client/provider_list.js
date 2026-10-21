// Service Provider screen (Khushi): "Closest" district picker and the
// "Project Scale" slider. The filter form submits itself on change
// (see setupAutoSubmit in base.js).

function setupDistrictPicker() {
  const toggle = document.querySelector("[data-closest-toggle]");
  const box = document.querySelector("[data-district-box]");
  if (!toggle || !box) return;
  const select = box.querySelector("select");

  toggle.addEventListener("change", (event) => {
    if (toggle.checked) {
      // Ask for the district first; the form is sent once one is picked.
      event.stopPropagation();
      box.hidden = false;
      select.disabled = false;
      select.focus();
    } else {
      box.hidden = true;
      select.disabled = true;
    }
  });
}

function setupScaleSlider() {
  const wrap = document.querySelector("[data-scale]");
  if (!wrap) return;
  const range = wrap.querySelector("[data-scale-range]");
  const hidden = wrap.querySelector("[data-scale-value]");
  const stops = wrap.querySelectorAll("[data-scale-stop]");
  const max = Number(range.max);

  function show(index) {
    range.style.setProperty("--fill", (index / max) * 100 + "%");
    stops.forEach((stop) => {
      stop.classList.toggle("active", Number(stop.dataset.scaleStop) === index);
    });
    hidden.value = stops[index].dataset.value;
  }

  range.addEventListener("input", () => show(Number(range.value)));
  stops.forEach((stop) => {
    stop.addEventListener("click", () => {
      range.value = stop.dataset.scaleStop;
      show(Number(range.value));
      range.dispatchEvent(new Event("change", { bubbles: true }));
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupDistrictPicker();
  setupScaleSlider();
});
