// Chart helpers for the dashboards (uses Chart.js).
// Data is passed from Django with the json_script filter.

// Read a value written by {{ value|json_script:"some-id" }}
function readJson(id) {
  const element = document.getElementById(id);
  return element ? JSON.parse(element.textContent) : null;
}

// Colours follow the current light / dark theme.
function themeColour(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

// Small line chart without axes, used inside the stat cards.
function drawSparkline(canvasId, values, colour) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !values) return;
  const context = canvas.getContext("2d");
  const fill = context.createLinearGradient(0, 0, 0, canvas.height);
  fill.addColorStop(0, colour + "66");
  fill.addColorStop(1, colour + "00");
  new Chart(canvas, {
    type: "line",
    data: {
      labels: values.map((_, index) => index),
      datasets: [{
        data: values, borderColor: colour, backgroundColor: fill,
        fill: true, tension: 0.45, pointRadius: 0, borderWidth: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: { x: { display: false }, y: { display: false, beginAtZero: true } },
    },
  });
}

// Full line chart with axes (earnings over the year).
function drawLineChart(canvasId, labels, values, label) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const text = themeColour("--text");
  new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: label, data: values, borderColor: "#1b3a8a",
        backgroundColor: "rgba(47, 111, 237, 0.18)", fill: true,
        tension: 0.45, pointRadius: 3, borderWidth: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: text }, grid: { display: false } },
        y: { ticks: { color: text }, beginAtZero: true },
      },
    },
  });
}

// Doughnut chart (admin: active clients per category).
function drawDoughnut(canvasId, labels, values) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: [
          "#ff9189", "#8b7cf6", "#6fcf97", "#4f7df0", "#ffae4a", "#3ec4dc",
        ],
        borderWidth: 0,
      }],
    },
    options: {
      cutout: "55%",
      plugins: { legend: { display: false } },
    },
  });
}
