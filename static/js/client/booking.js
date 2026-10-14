// Booking calendar and photo previews for client/booking.html.

// --- Calendar ---
function setupBookingCalendar() {
  const box = document.getElementById("booking-calendar");
  const input = document.getElementById("id_preferred_date");
  const label = document.getElementById("selected-label");
  const blocked = JSON.parse(document.getElementById("blocked-days").textContent);
  const today = new Date(box.dataset.today + "T00:00:00");
  const locale = box.dataset.lang === "fr" ? "fr-FR" : "en-GB";
  let shown = new Date(today.getFullYear(), today.getMonth(), 1);

  function iso(day) {
    const month = String(day.getMonth() + 1).padStart(2, "0");
    const date = String(day.getDate()).padStart(2, "0");
    return day.getFullYear() + "-" + month + "-" + date;
  }

  function showSelected() {
    if (!input.value) return;
    const picked = new Date(input.value + "T00:00:00");
    label.textContent = picked.toLocaleDateString(locale, {
      day: "numeric", month: "short", year: "numeric",
    });
  }

  function render() {
    box.innerHTML = "";
    const header = document.createElement("div");
    header.className = "bk-cal-header";
    const title = shown.toLocaleDateString(locale, { month: "long", year: "numeric" });
    header.innerHTML =
      '<button type="button" data-step="-1">&lsaquo;</button>' +
      "<strong>" + title + "</strong>" +
      '<button type="button" data-step="1">&rsaquo;</button>';
    box.appendChild(header);

    const grid = document.createElement("div");
    grid.className = "bk-cal-grid";
    // Week starts on Sunday, like the Figma calendar.
    for (let i = 0; i < 7; i++) {
      const name = new Date(2024, 8, 1 + i).toLocaleDateString(locale, { weekday: "short" });
      grid.insertAdjacentHTML("beforeend", '<span class="bk-cal-day-name">' + name + "</span>");
    }
    const first = new Date(shown.getFullYear(), shown.getMonth(), 1);
    for (let i = 0; i < first.getDay(); i++) {
      grid.insertAdjacentHTML("beforeend", "<span></span>");
    }
    const days = new Date(shown.getFullYear(), shown.getMonth() + 1, 0).getDate();
    for (let d = 1; d <= days; d++) {
      const day = new Date(shown.getFullYear(), shown.getMonth(), d);
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = d;
      button.className = "bk-cal-day";
      const value = iso(day);
      if (day < today || blocked.includes(value)) {
        button.disabled = true;
        if (blocked.includes(value)) button.classList.add("blocked");
      }
      if (value === input.value) button.classList.add("selected");
      button.addEventListener("click", () => {
        input.value = value;
        showSelected();
        render();
      });
      grid.appendChild(button);
    }
    box.appendChild(grid);

    header.querySelectorAll("[data-step]").forEach((arrow) => {
      arrow.addEventListener("click", () => {
        shown = new Date(shown.getFullYear(), shown.getMonth() + Number(arrow.dataset.step), 1);
        render();
      });
    });
  }

  showSelected();
  render();
}

// --- Photo previews in the ten dashed boxes ---
function setupPhotoPreview() {
  const picker = document.querySelector('input[type="file"][name="photos"]');
  const slots = document.querySelectorAll("#photo-slots .bk-slot");
  picker.addEventListener("change", () => {
    const files = Array.from(picker.files).slice(0, 10);
    slots.forEach((slot, index) => {
      slot.innerHTML = "";
      if (files[index]) {
        const img = document.createElement("img");
        img.src = URL.createObjectURL(files[index]);
        img.className = "bk-preview";
        slot.appendChild(img);
      }
    });
    if (picker.files.length > 10) {
      alert("Only the first 10 photos will be kept.");
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupBookingCalendar();
  setupPhotoPreview();
});
