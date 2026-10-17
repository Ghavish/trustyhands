// TrustyHands: toasts, Back button and page transitions.
// Loaded on every page after base.js.

// --- Toasts ---
// Each toast closes itself after a few seconds (errors stay open).
// Hovering pauses the timer; "Dismiss" closes it straight away.
const TOAST_LIFE_MS = 4500;

function closeToast(toast) {
  if (toast.classList.contains("is-leaving")) return;
  toast.classList.add("is-leaving");
  toast.addEventListener("animationend", () => {
    const stack = toast.parentElement;
    toast.remove();
    if (stack && !stack.children.length) stack.remove();
  });
}

function setupToasts() {
  const stack = document.querySelector("[data-toast-stack]");
  if (!stack) return;
  // Move the stack to <body> so "position: fixed" is never trapped
  // inside an animated container.
  document.body.appendChild(stack);

  stack.querySelectorAll(".toast").forEach((toast) => {
    toast.querySelector("[data-toast-dismiss]").addEventListener("click", () => {
      closeToast(toast);
    });
    if (!toast.hasAttribute("data-autoclose")) return;

    toast.style.setProperty("--toast-life", TOAST_LIFE_MS + "ms");
    let remaining = TOAST_LIFE_MS;
    let started = Date.now();
    let timer = setTimeout(() => closeToast(toast), remaining);
    toast.addEventListener("mouseenter", () => {
      clearTimeout(timer);
      remaining -= Date.now() - started;
    });
    toast.addEventListener("mouseleave", () => {
      started = Date.now();
      timer = setTimeout(() => closeToast(toast), Math.max(remaining, 800));
    });
  });
}

// --- Back button ---
// Go back in history when the previous page was on TrustyHands,
// otherwise follow the link's own fallback address.
function cameFromTrustyHands() {
  try {
    return Boolean(
      document.referrer &&
      new URL(document.referrer).origin === window.location.origin &&
      document.referrer !== window.location.href
    );
  } catch (error) {
    return false;
  }
}

function setupBackButtons() {
  const cameFromUs = cameFromTrustyHands();
  document.querySelectorAll("[data-back]").forEach((link) => {
    // With no earlier TrustyHands page, a fallback pointing at this same
    // screen (e.g. Active Jobs for a provider) would only reload it.
    if (!cameFromUs && new URL(link.href).pathname === window.location.pathname) {
      (link.closest(".back-row") || link).style.display = "none";
      return;
    }
    link.addEventListener("click", (event) => {
      if (cameFromUs && window.history.length > 1) {
        event.preventDefault();
        window.history.back();
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupToasts();
  setupBackButtons();
});
