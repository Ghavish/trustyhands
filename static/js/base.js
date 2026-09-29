// TrustyHands shared behaviour, loaded on every page.

// --- Read the CSRF token Django puts in a cookie ---
function getCookie(name) {
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith(name + "="));
  return match ? decodeURIComponent(match.split("=")[1]) : "";
}

// --- Light / dark mode switch ---
// Changes the page instantly, then saves the choice:
// in MongoDB for logged-in users, in a cookie for guests.
function setupThemeSwitch() {
  const buttons = document.querySelectorAll("[data-theme-toggle]");
  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const root = document.documentElement;
      const next = root.dataset.theme === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      document.cookie = "th_theme=" + next + "; path=/; max-age=31536000";
      const body = new FormData();
      body.append("theme", next);
      fetch(button.dataset.url, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "fetch",
        },
        body: body,
      });
    });
  });
}

// --- Dropdown menus: click to open, click outside to close ---
function setupDropdowns() {
  document.querySelectorAll("[data-dropdown]").forEach((dropdown) => {
    const trigger = dropdown.querySelector("[data-dropdown-trigger]");
    trigger.addEventListener("click", (event) => {
      event.stopPropagation();
      document.querySelectorAll(".dropdown.open").forEach((other) => {
        if (other !== dropdown) other.classList.remove("open");
      });
      dropdown.classList.toggle("open");
    });
  });
  document.addEventListener("click", () => {
    document.querySelectorAll(".dropdown.open").forEach((dropdown) => {
      dropdown.classList.remove("open");
    });
  });
}

// --- Mobile menu button in the navbar ---
function setupMobileNav() {
  const nav = document.querySelector(".site-nav");
  const toggle = document.querySelector(".nav-toggle");
  if (nav && toggle) {
    toggle.addEventListener("click", () => nav.classList.toggle("open"));
  }
}

// --- Ask before destructive actions: <form data-confirm="Sure?"> ---
function setupConfirmForms() {
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });
}

// --- Submit a form as soon as one of its fields changes ---
function setupAutoSubmit() {
  document.querySelectorAll("[data-auto-submit]").forEach((form) => {
    form.addEventListener("change", () => form.submit());
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupThemeSwitch();
  setupDropdowns();
  setupMobileNav();
  setupConfirmForms();
  setupAutoSubmit();
});
