// Enhanced Interactive Leaflet Map with Day Routes, Numbered Markers & Day Filtering
document.addEventListener("DOMContentLoaded", function () {
  var el = document.getElementById("map");
  if (!el || typeof L === "undefined") return;

  function read(id) {
    var node = document.getElementById(id);
    try {
      return node ? JSON.parse(node.textContent) : null;
    } catch (e) {
      return null;
    }
  }

  var markersData = read("map-markers") || [];
  var routesData = read("map-routes") || [];
  var center = read("map-center");

  var start = center ? [center.lat, center.lon] : [20, 0];
  var map = L.map("map", { scrollWheelZoom: false }).setView(start, center ? 13 : 2);

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors",
  }).addTo(map);

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s || "";
    return d.innerHTML;
  }

  function safeUrl(u) {
    if (!u || typeof u !== "string") return "#";
    var clean = u.trim();
    if (clean.startsWith("https://") || clean.startsWith("http://")) {
      return encodeURI(clean);
    }
    return "#";
  }

  // Layer groups for filtering
  var markerLayers = {};
  var routeLayers = {};
  var allBounds = [];
  var markerInstances = {};

  // Draw Route Polylines
  routesData.forEach(function (r) {
    if (!r.coordinates || r.coordinates.length < 2) return;
    var day = r.day;
    var poly = L.polyline(r.coordinates, {
      color: r.color || "#0d9488",
      weight: 4,
      opacity: 0.85,
      lineCap: "round",
      lineJoin: "round",
    }).addTo(map);

    if (!routeLayers[day]) routeLayers[day] = [];
    routeLayers[day].push(poly);
  });

  // Draw Custom Numbered Markers
  markersData.forEach(function (m, idx) {
    var day = m.day;
    var color = m.color || "#2563eb";
    var order = m.order || (idx + 1);

    var customIcon = L.divIcon({
      className: "custom-day-pin",
      iconSize: [30, 30],
      iconAnchor: [15, 15],
      popupAnchor: [0, -15],
      html: '<div style="background-color:' + esc(color) + '; color:#ffffff; border-radius:50%; width:28px; height:28px; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:12px; border:2px solid #ffffff; box-shadow:0 3px 8px rgba(0,0,0,0.35); cursor:pointer;">' +
        esc(String(order)) + '</div>',
    });

    var popupHtml =
      '<div style="min-width:180px; font-family:inherit;">' +
      '<div style="font-size:11px; font-weight:700; text-transform:uppercase; color:' + esc(color) + ';">Day ' + esc(String(day)) + ' · Stop #' + esc(String(order)) + '</div>' +
      '<strong style="font-size:14px; display:block; margin:2px 0 4px;">' + esc(m.name) + '</strong>' +
      (m.activity && m.activity !== m.name ? '<div style="font-size:12px; color:#475569; margin-bottom:4px;">' + esc(m.activity) + '</div>' : '') +
      '<span class="badge bg-light text-dark border me-1" style="font-size:10px;">' + esc(m.cat) + '</span>' +
      (m.suggested_time ? '<span class="badge bg-secondary-subtle text-secondary" style="font-size:10px;">' + esc(m.suggested_time) + '</span>' : '') +
      (m.tip ? '<div style="font-size:11px; color:#0f766e; margin-top:6px; background:#f0fdfa; padding:4px 6px; border-radius:4px;">💡 ' + esc(m.tip) + '</div>' : '') +
      '<div style="margin-top:8px; display:flex; gap:8px;">' +
      '<a href="' + safeUrl(m.nav) + '" target="_blank" rel="noopener" style="font-size:11px; text-decoration:none; color:#0284c7; font-weight:600;">OpenStreetMap ↗</a>' +
      '</div></div>';

    var marker = L.marker([m.lat, m.lon], { icon: customIcon }).addTo(map).bindPopup(popupHtml);

    if (!markerLayers[day]) markerLayers[day] = [];
    markerLayers[day].push(marker);
    allBounds.push([m.lat, m.lon]);

    // Key for click-to-focus from activity cards
    var key = m.lat.toFixed(4) + "," + m.lon.toFixed(4);
    markerInstances[key] = marker;
  });

  // Fit bounds to show all markers
  if (allBounds.length > 1) {
    map.fitBounds(allBounds, { padding: [40, 40] });
  } else if (allBounds.length === 1) {
    map.setView(allBounds[0], 14);
  }

  // Day Filter Button Controls
  var filterBtns = document.querySelectorAll("[data-filter-day]");
  filterBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      filterBtns.forEach(function (b) { b.classList.remove("active"); });
      this.classList.add("active");

      var targetDay = this.getAttribute("data-filter-day");
      var visibleBounds = [];

      Object.keys(markerLayers).forEach(function (d) {
        var show = (targetDay === "all" || targetDay === String(d));
        markerLayers[d].forEach(function (mk) {
          if (show) {
            if (!map.hasLayer(mk)) map.addLayer(mk);
            visibleBounds.push(mk.getLatLng());
          } else {
            if (map.hasLayer(mk)) map.removeLayer(mk);
          }
        });
      });

      Object.keys(routeLayers).forEach(function (d) {
        var show = (targetDay === "all" || targetDay === String(d));
        routeLayers[d].forEach(function (poly) {
          if (show) {
            if (!map.hasLayer(poly)) map.addLayer(poly);
          } else {
            if (map.hasLayer(poly)) map.removeLayer(poly);
          }
        });
      });

      if (visibleBounds.length > 1) {
        map.fitBounds(visibleBounds, { padding: [40, 40] });
      } else if (visibleBounds.length === 1) {
        map.setView(visibleBounds[0], 15);
      }
    });
  });

  // Interactive focus from itinerary cards
  document.querySelectorAll("[data-activity-focus]").forEach(function (card) {
    card.addEventListener("click", function () {
      var lat = parseFloat(this.getAttribute("data-lat"));
      var lon = parseFloat(this.getAttribute("data-lon"));
      if (!isNaN(lat) && !isNaN(lon)) {
        var key = lat.toFixed(4) + "," + lon.toFixed(4);
        var marker = markerInstances[key];
        if (marker) {
          map.setView([lat, lon], 15, { animate: true });
          marker.openPopup();
          el.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }
    });
  });
});
