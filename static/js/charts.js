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

function isDark() {
  return document.documentElement.dataset.theme === "dark";
}

// Category colours, in a fixed order (category 1 always gets slot 1).
// Checked for colour-blind separation on the light (#ffffff) and dark
// (#243244) card colours. Dark mode uses its own, slightly shifted steps.
const CATEGORY_COLOURS = {
  light: ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"],
  dark: ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#9085e9"],
};

function categoryColours() {
  return CATEGORY_COLOURS[isDark() ? "dark" : "light"];
}

// Redraw colours when the theme switch is used.
const themedCharts = [];
new MutationObserver(() => {
  themedCharts.forEach((refresh) => refresh());
}).observe(document.documentElement, {
  attributes: true, attributeFilter: ["data-theme"],
});

function formatNumber(value) {
  return Number(value).toLocaleString("en-GB", { maximumFractionDigits: 0 });
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

// Area chart with light axes and a hover tooltip (admin: Transactions).
// It fills the height of its container.
function drawAreaChart(canvasId, labels, values, unit) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !values) return;
  const colour = "#dba844";
  const context = canvas.getContext("2d");

  function gradient() {
    const fill = context.createLinearGradient(0, 0, 0, canvas.clientHeight || 300);
    fill.addColorStop(0, colour + "55");
    fill.addColorStop(1, colour + "00");
    return fill;
  }

  const chart = new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        data: values, borderColor: colour, backgroundColor: gradient(),
        fill: true, tension: 0.35, cubicInterpolationMode: "monotone", borderWidth: 2,
        pointRadius: 0, pointHoverRadius: 5,
        pointHoverBackgroundColor: colour, pointHoverBorderWidth: 2,
        pointHoverBorderColor: themeColour("--surface"),
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          displayColors: false,
          callbacks: {
            label: (item) => unit + " " + formatNumber(item.parsed.y),
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          border: { display: false },
          ticks: {
            color: themeColour("--text-muted"), maxTicksLimit: 5,
            maxRotation: 0, font: { size: 11 },
          },
        },
        y: {
          beginAtZero: true,
          border: { display: false },
          grid: { color: themeColour("--border") },
          ticks: {
            color: themeColour("--text-muted"), maxTicksLimit: 4,
            font: { size: 11 }, callback: (value) => formatNumber(value),
          },
        },
      },
    },
  });

  themedCharts.push(() => {
    chart.options.scales.x.ticks.color = themeColour("--text-muted");
    chart.options.scales.y.ticks.color = themeColour("--text-muted");
    chart.options.scales.y.grid.color = themeColour("--border");
    chart.data.datasets[0].pointHoverBorderColor = themeColour("--surface");
    chart.update("none");
  });
}

// Full line chart with axes (earnings over the year).
// The line is navy in light mode and a lighter blue in dark mode.
function drawLineChart(canvasId, labels, values, label) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const lineColour = () => (isDark() ? "#82aaff" : "#1b3a8a");
  const chart = new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: label, data: values, borderColor: lineColour(),
        pointBackgroundColor: lineColour(),
        backgroundColor: "rgba(47, 111, 237, 0.18)", fill: true,
        tension: 0.4, cubicInterpolationMode: "monotone",
        pointRadius: 3, borderWidth: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: themeColour("--text-muted") }, grid: { display: false } },
        y: {
          ticks: { color: themeColour("--text-muted") },
          grid: { color: themeColour("--border") },
          beginAtZero: true,
        },
      },
    },
  });

  themedCharts.push(() => {
    chart.data.datasets[0].borderColor = lineColour();
    chart.data.datasets[0].pointBackgroundColor = lineColour();
    chart.options.scales.x.ticks.color = themeColour("--text-muted");
    chart.options.scales.y.ticks.color = themeColour("--text-muted");
    chart.options.scales.y.grid.color = themeColour("--border");
    chart.update("none");
  });
}

// Doughnut chart (admin: active clients per category).
// "legendId" is the <ul> next to the chart: its swatches, share bars and
// hover highlight are driven from here, so the colours live in one place.
function drawDoughnut(canvasId, labels, values, legendId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const total = values.reduce((sum, value) => sum + value, 0);
  const legend = legendId ? document.getElementById(legendId) : null;

  const chart = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: categoryColours(),
        borderColor: themeColour("--surface"),
        borderWidth: 2,
        borderRadius: 6,
        spacing: 2,
        hoverOffset: 10,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "70%",
      layout: { padding: 10 },
      animation: { animateRotate: true, duration: 900, easing: "easeOutQuart" },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => {
              const share = total ? Math.round((item.parsed / total) * 100) : 0;
              return " " + item.parsed + " (" + share + "%)";
            },
          },
        },
      },
    },
  });

  function paintLegend() {
    if (!legend) return;
    const colours = categoryColours();
    legend.querySelectorAll("[data-legend-index]").forEach((item) => {
      const index = Number(item.dataset.legendIndex);
      const value = values[index] || 0;
      item.querySelector(".an-swatch").style.background = colours[index % colours.length];
      item.classList.toggle("is-empty", value === 0);
      let share = item.querySelector(".an-legend-share");
      if (!share) {
        share = document.createElement("span");
        share.className = "an-legend-share";
        share.appendChild(document.createElement("span"));
        item.appendChild(share);
      }
      share.firstChild.style.width = (total ? (value / total) * 100 : 0) + "%";
      share.firstChild.style.background = colours[index % colours.length];
    });
  }

  // Hovering a legend row lifts the matching slice.
  if (legend) {
    legend.querySelectorAll("[data-legend-index]").forEach((item) => {
      const index = Number(item.dataset.legendIndex);
      item.addEventListener("mouseenter", () => {
        if (!values[index]) return;
        chart.setActiveElements([{ datasetIndex: 0, index: index }]);
        chart.tooltip.setActiveElements([{ datasetIndex: 0, index: index }], { x: 0, y: 0 });
        item.classList.add("is-active");
        chart.update();
      });
      item.addEventListener("mouseleave", () => {
        chart.setActiveElements([]);
        chart.tooltip.setActiveElements([], { x: 0, y: 0 });
        item.classList.remove("is-active");
        chart.update();
      });
    });
  }

  paintLegend();
  themedCharts.push(() => {
    chart.data.datasets[0].backgroundColor = categoryColours();
    chart.data.datasets[0].borderColor = themeColour("--surface");
    chart.update("none");
    paintLegend();
  });
}
