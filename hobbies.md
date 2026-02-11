---
layout: page
title: "Hobbies"
sidebar:  |
  * [Involvement in KemiRevy](#involvement-in-kemirevy)
    * [KemiRevy](#kemi-revy)
    * [Sikke et koncept](#sikke-et-koncept)
    * [Hvad lytter du til?](#hvad-lytter-du-til)
    * [KSBogen er skrevet i word](#ksbogen-er-skrevet-i-word)
    * [Nissen](#nissen)
---

## Involvement in KemiRevy {#kemi-revy}
I was an active member of the chemistry revue at the University of Copenhagen called **KemiRevy** from 2022 to 2024. During this time, I contributed to various film projects and helped promote the event, which combines science and entertainment. 


Warning: They are all in Danish and might contain references which are not easily understood without knowledge of the study environment at CHEM KU. Also all the videos are not to be taken seriously, they are just for fun.

---

### Sikke et koncept (What a concept) – 2023 {#sikke-et-koncept}
A humorous take on the different study programs at the Department of Chemistry at KU. This series includes the following episodes:

#### Chemistry
<iframe width="560" height="315" 
src="https://www.youtube.com/embed/a5aQpFaq2-c" 
title="YouTube video player" frameborder="0" 
allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
allowfullscreen>
</iframe>

#### Medicinal Chemistry
<iframe width="560" height="315" 
src="https://www.youtube.com/embed/fWjQoZDjFpg" 
title="YouTube video player" frameborder="0" 
allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
allowfullscreen>
</iframe>

#### Nanoscience
<iframe width="560" height="315" 
src="https://www.youtube.com/embed/3pHQCSOthXE" 
title="YouTube video player" frameborder="0" 
allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
allowfullscreen>
</iframe>

> Many thanks to Jerik Lauridsen for his help with the editing and Elias Rangel Aabye and Amalie Skinne for being camera operators.

---

### Hvad lytter du til? (What are you listening to?) – 2023 {#hvad-lytter-du-til}
A comedic take on the different study programs at the Department of Chemistry at KU. This is in two parts:

<iframe width="560" height="315" 
src="https://www.youtube.com/embed/_0hGB4YofqI" 
title="YouTube video player" frameborder="0" 
allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
allowfullscreen>
</iframe>

<iframe width="560" height="315" 
src="https://www.youtube.com/embed/Y24kgzmolbU" 
title="YouTube video player" frameborder="0" 
allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
allowfullscreen>
</iframe>

> Many thanks to Amalie Skinne for being the main actress in this series.

---

### KSBogen er skrevet i word (The KSBook is written in Word) – 2024 {#ksbogen-er-skrevet-i-word}
Elas Rangel Aabye and I thought the KS–Book (a great book of notes about quantum chemistry and spectroscopy) written by our lovely professor Stephan Sauer had a Word format.

<video width="560" height="315" controls>
  <source src="assets/KSBogen.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

> Many thanks to Elas Rangel Aabye for his contributions to this project, this was a two-man effort.

---
### Nissen (The Gnome) – 2025 {#nissen}
Elias Rangel Aabye playing the Gnome in a comedic sketch about the life at the Department of Chemistry at KU. The Gnome is the reason why nothing works at the department.

<iframe width="560" height="315" 
src="https://www.youtube.com/embed/KewpAqUgww4" 
title="YouTube video player" frameborder="0" 
allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
allowfullscreen>
</iframe>

> Many thanks to Elias Rangel Aabye for his fantastic performance in this sketch, idea generation, editing help, and overall creativity.

## Running
Apart from my involvement in KemiRevy, I also enjoy running as a hobby. It helps me stay fit and clear my mind. If you're interested in running or want to share tips, feel free to reach out! You can find me on Strava:
<!-- Include in your GitHub Pages page where you want the map + elevation profile -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.3.0/dist/chart.umd.min.js"></script>

<style>
  #strava-widget { display:flex; gap:20px; align-items:flex-start; }
  #map { height: 420px; width: 60%; }
  #elevation { width: 40%; height: 420px; }
  .run-summary { margin-bottom: 10px; font-family: sans-serif; }
</style>

<div id="strava-widget">
  <div id="map"></div>
  <div style="width: 40%;">
    <div class="run-summary" id="run-summary"></div>
    <canvas id="elevation"></canvas>
  </div>
</div>

<script>
(async function() {
  const runResp = await fetch('/data/latest_run.json');
  const run = await runResp.json();

  const geoResp = await fetch('/data/latest_route.geojson');
  const geo = await geoResp.json();

  // Build summary text
  const summaryEl = document.getElementById('run-summary');
  const start = new Date(run.start_date_local);
  const distKm = (run.distance_km || 0).toFixed(2);
  const movingMin = Math.round((run.moving_time_s||0)/60);
  const avgPace = run.average_pace_s_per_km ? Math.round(run.average_pace_s_per_km) : null;

  summaryEl.innerHTML = `
    <strong>${run.name || 'Latest Run'}</strong><br/>
    ${start.toLocaleString()}<br/>
    Distance: ${distKm} km<br/>
    Moving time: ${movingMin} min<br/>
    ${avgPace ? ('Avg pace: ' + Math.floor(avgPace/60) + ':' + String(avgPace%60).padStart(2,'0') + ' /km') : '' }
  `;

  // Leaflet map
  const map = L.map('map', {zoomControl: true});
  // Use OSM tiles (works without keys)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  // Add route
  const coords = geo.geometry.coordinates.map(c => {
    // geo coords: [lon, lat, alt?]
    return (c.length >= 3) ? [c[1], c[0], c[2]] : [c[1], c[0], null];
  });

  // Line (use lat,lon only)
  const latlngs = coords.map(c => [c[0], c[1]]);
  const routeLine = L.polyline(latlngs, {color: 'red', weight: 4, opacity: 0.8}).addTo(map);
  map.fitBounds(routeLine.getBounds(), {padding:[20,20]});

  // Pace markers (km markers)
  if (run.km_markers && run.km_markers.length > 0) {
    run.km_markers.forEach(m => {
      const popup = `Km ${m.km} — ${m.pace_str || ''}`;
      L.circleMarker([m.lat, m.lon], {radius:6, fillColor:'white', color:'black', weight:1})
        .bindPopup(popup)
        .addTo(map);
    });
  }

  // Elevation chart using Chart.js
  // Derive elevation samples from geo coordinates (3rd element)
  const elevationSamples = coords
    .map(c => c[2] !== null ? c[2] : null)
    .filter(e => e !== null);

  // If no altitude samples in raw coords, try to skip chart
  if (elevationSamples.length === 0) {
    document.getElementById('elevation').style.display = 'none';
  } else {
    // Convert to distances for x axis (approx)
    // compute cumulative distance between coords
    function haversine(lat1, lon1, lat2, lon2) {
      const R = 6371000.0;
      const toRad = Math.PI / 180;
      const dLat = (lat2 - lat1) * toRad;
      const dLon = (lon2 - lon1) * toRad;
      const a = Math.sin(dLat/2)*Math.sin(dLat/2) + Math.cos(lat1*toRad)*Math.cos(lat2*toRad) * Math.sin(dLon/2)*Math.sin(dLon/2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
      return R * c;
    }
    const dists = [0];
    for (let i=1; i<coords.length; i++){
      const [lat1, lon1] = [coords[i-1][0], coords[i-1][1]];
      const [lat2, lon2] = [coords[i][0], coords[i][1]];
      dists.push(dists[dists.length-1] + haversine(lat1, lon1, lat2, lon2));
    }

    // If some coords had null altitude, map to nearest alt or drop them
    const altSeries = [];
    const xLabels = [];
    for (let i=0; i<coords.length; i++){
      const alt = coords[i][2];
      if (alt === null) continue;
      altSeries.push(alt);
      xLabels.push((dists[i]/1000).toFixed(2)); // km
    }

    const ctx = document.getElementById('elevation').getContext('2d');
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: xLabels,
        datasets: [{
          label: 'Elevation (m)',
          data: altSeries,
          fill: true,
          tension: 0.2,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { title: { display: true, text: 'Distance (km)' } },
          y: { title: { display: true, text: 'Elevation (m)' } }
        }
      }
    });
  }

})();
</script>
---