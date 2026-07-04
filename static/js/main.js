/* =====================================================
   main.js  –  Earthquake Dashboard client-side logic
   ===================================================== */

// ---- helpers ---------------------------------------------------------------

function magColour(mag) {
  if (mag === null || mag === undefined) return "#aaa";
  if (mag >= 7) return "#d32f2f";
  if (mag >= 6) return "#f57c00";
  if (mag >= 5) return "#fbc02d";
  if (mag >= 4) return "#388e3c";
  return "#1565c0";
}

function magRadius(mag) {
  if (mag === null || mag === undefined) return 5;
  return Math.max(4, mag * 3);
}

// ---- Dashboard (index.html) ------------------------------------------------

function initDashboard(earthquakes, analysis) {
  // Leaflet map
  const map = L.map("map").setView([20, 0], 2);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 18,
  }).addTo(map);

  earthquakes.forEach(function (eq) {
    if (eq.latitude === null || eq.longitude === null) return;
    const circle = L.circleMarker([eq.latitude, eq.longitude], {
      radius: magRadius(eq.magnitude),
      color: magColour(eq.magnitude),
      fillColor: magColour(eq.magnitude),
      fillOpacity: 0.65,
      weight: 1,
    }).addTo(map);
    circle.bindPopup(
      "<strong>M " + eq.magnitude + "</strong><br>" +
      eq.place + "<br>" +
      eq.time + "<br>" +
      "Depth: " + eq.depth_km + " km" +
      (eq.id ? '<br><a href="/earthquake/' + eq.id + '">View details</a>' : "")
    );
  });

  // Magnitude distribution bar chart
  const distLabels = Object.keys(analysis.magnitude_distribution || {});
  const distValues = Object.values(analysis.magnitude_distribution || {});
  new Chart(document.getElementById("magChart"), {
    type: "bar",
    data: {
      labels: distLabels,
      datasets: [{
        label: "Events",
        data: distValues,
        backgroundColor: ["#1565c0","#388e3c","#fbc02d","#f57c00","#d32f2f","#6a1b9a","#00838f"],
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
    },
  });

  // Daily event count line chart
  const dailyLabels = Object.keys(analysis.daily_counts || {});
  const dailyValues = Object.values(analysis.daily_counts || {});
  new Chart(document.getElementById("dailyChart"), {
    type: "line",
    data: {
      labels: dailyLabels,
      datasets: [{
        label: "Events/day",
        data: dailyValues,
        borderColor: "#1565c0",
        backgroundColor: "rgba(21,101,192,.15)",
        fill: true,
        tension: 0.3,
        pointRadius: 3,
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
    },
  });
}

// ---- Detail page (detail.html) ---------------------------------------------

function initDetailPage(eq) {
  if (!eq) return;

  // Leaflet map centred on epicentre
  const lat = eq.latitude;
  const lng = eq.longitude;
  if (lat !== null && lng !== null) {
    const map = L.map("detail-map").setView([lat, lng], 6);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    const mag = eq.magnitude;
    L.circleMarker([lat, lng], {
      radius: magRadius(mag) * 1.5,
      color: magColour(mag),
      fillColor: magColour(mag),
      fillOpacity: 0.7,
      weight: 2,
    }).addTo(map).bindPopup(
      "<strong>M " + mag + " – " + eq.place + "</strong><br>" + eq.time
    ).openPopup();

    // Rough impact radius circle (very approximate: 10^(mag-1) km)
    if (mag !== null) {
      const radiusKm = Math.pow(10, mag - 1);
      L.circle([lat, lng], { radius: radiusKm * 1000, color: magColour(mag), fillOpacity: 0.08, weight: 1 })
        .addTo(map);
    }
  }

  // Magnitude effects & radius
  const mag = eq.magnitude;
  const effects = {
    "Micro":    "Rarely felt; detected only by instruments.",
    "Minor":    "Felt by some people near the epicentre; minor damage.",
    "Light":    "Felt by many indoors; rattling of dishes, windows.",
    "Moderate": "Felt by everyone; some structural damage possible.",
    "Strong":   "Significant damage; walls crack; objects fall.",
    "Major":    "Serious damage over large areas; loss of life likely.",
    "Great":    "Severe damage across vast regions; catastrophic.",
  };
  const cat = eq.mag_category;
  const effectsEl = document.getElementById("mag-effects");
  if (effectsEl) effectsEl.textContent = effects[cat] || "—";

  const radiusKm = mag !== null ? Math.round(Math.pow(10, mag - 1)) : null;
  const radiusEl = document.getElementById("mag-radius");
  if (radiusEl) radiusEl.textContent = radiusKm !== null ? "≈ " + radiusKm.toLocaleString() + " km" : "—";

  // Depth classification
  const depth = eq.depth_km;
  let depthCat = "—", depthExplain = "—";
  if (depth !== null) {
    if (depth <= 70) {
      depthCat = "Shallow (≤ 70 km)";
      depthExplain = "Usually causes the most damage at the surface.";
    } else if (depth <= 300) {
      depthCat = "Intermediate (70–300 km)";
      depthExplain = "Felt over a wider area but less surface damage.";
    } else {
      depthCat = "Deep (> 300 km)";
      depthExplain = "Rarely destructive at the surface.";
    }
  }
  const depthCatEl = document.getElementById("depth-cat");
  if (depthCatEl) depthCatEl.textContent = depthCat;
  const depthExEl = document.getElementById("depth-explain");
  if (depthExEl) depthExEl.textContent = depthExplain;
}
