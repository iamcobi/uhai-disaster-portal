'use strict';

const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const fmt = (v, d = 0) => v == null ? 'Unknown' : Number(v).toLocaleString(undefined, { maximumFractionDigits: d });
const safe = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const roleConfig = {
  ambulance: { name: 'Ambulance Standby Base', color: '#ffffff', markerClass: 'marker-amb', icon: '🚑' },
  cooling: { name: 'Cooling & Power Hub', color: '#ffffff', markerClass: 'marker-cool', icon: '❄️' },
  community: { name: 'Community Relief Hub', color: '#ffffff', markerClass: 'marker-comm', icon: '🏠' },
  dispatch: { name: 'Emergency Incident Building', color: '#ffffff', markerClass: 'marker-disp', icon: '🚨' }
};

const layerDefs = [
  ['coverage', '15m Reach', '#ffffff', null, 'ZIP centroids within 15 modeled rapid minutes.'],
  ['outages', 'Power Outages', '#a1a1aa', null, 'County peaks of reported customer grid outages.'],
  ['flood', 'Flooding Calls', '#e4e4e7', 'Flood/drainage reports', 'Density of recorded flood and drainage calls.'],
  ['tree', 'Fallen Trees', '#d4d4d8', 'Tree removal reports', 'Density of fallen tree obstructions.'],
  ['debris', 'Road Debris', '#a1a1aa', 'Storm debris reports', 'Structural and road debris reports.'],
  ['electrical', 'Downed Wires', '#ffffff', 'Electrical hazard reports', 'Downed live wires and transformer hazards.']
];

const state = {
  mainTab: 'predictor',
  analyticsTab: 'placements',
  layer: 'coverage',
  storm: 'Beryl',
  boot: null,
  data: null,
  plan: null,
  supplies: null,
  utility: null,
  zip: '77002',
  selectedSite: null,
  selectedRole: 'ambulance',
  map: null,
  markers: [],
  is3d: false,
  request: 0,
  gl: false,
  mapReady: false
};

async function api(path, opts) {
  const r = await fetch(path, opts);
  const d = await r.json();
  if (!r.ok) throw Error(d.error || `Request failed (${r.status})`);
  return d;
}

function error(e) {
  const el = $('#error');
  el.hidden = !e;
  if (e) el.textContent = e.message || String(e);
}

function params() {
  return new URLSearchParams({
    storm: state.storm,
    ambulances: $('#ambulance')?.value || 2,
    dispatch: $('#dispatch')?.value || 2,
    cooling: $('#cooling')?.value || 3,
    community: $('#community')?.value || 3,
    slowdown: 2, // Fixed 2x hurricane flood delay as requested
    closed: $('#closed') ? $('#closed').value : 'None'
  });
}

function busy(v, msg) {
  const el = $('#loading');
  el.hidden = !v;
  if (msg) el.textContent = msg;
  $('#calculate').disabled = v;
  $('#storm').disabled = v;
}

function table(headers, rows) {
  return `<div class="table-wrap"><table><thead><tr>${headers.map(h => `<th scope="col">${safe(h)}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`;
}

function pointFC(rows, fn) {
  return { type: 'FeatureCollection', features: rows.map(fn) };
}

/* INITIALIZE CONTROLS */
function initControls() {
  $('#tab-btn-predictor').onclick = () => switchMainView('predictor');
  $('#tab-btn-analytics').onclick = () => switchMainView('analytics');

  $$('.subtab').forEach(btn => {
    btn.onclick = async () => {
      state.analyticsTab = btn.dataset.analytics;
      $$('.subtab').forEach(b => b.classList.toggle('active', b === btn));
      await renderAnalytics();
    };
  });

  $('#layer-list').innerHTML = layerDefs.map(d => 
    `<button class="layer-chip ${d[0] === state.layer ? 'active' : ''}" data-layer="${d[0]}"><span class="chip-dot" style="background:${d[2]}"></span>${d[1]}</button>`
  ).join('');

  $$('#layer-list button').forEach(b => b.onclick = () => {
    state.layer = b.dataset.layer;
    $$('#layer-list button').forEach(x => x.classList.toggle('active', x === b));
    renderLayer();
  });

  // Numeric input steppers (unlimited capacity)
  ['ambulance', 'dispatch', 'cooling', 'community'].forEach(id => {
    const input = $('#' + id);
    if (!input) return;
    input.addEventListener('input', e => {
      let val = parseInt(e.target.value) || 1;
      if (val < 1) val = 1;
      e.target.value = val;
    });
  });

  $$('.btn-step').forEach(btn => {
    btn.onclick = () => {
      const id = btn.dataset.step;
      const input = $('#' + id);
      if (!input) return;
      let val = (parseInt(input.value) || 1) + parseInt(btn.dataset.dir);
      if (val < 1) val = 1;
      input.value = val;
      input.dispatchEvent(new Event('input'));
    };
  });

  $('#calculate').onclick = () => loadScenario(false);
  $('#storm').onchange = () => {
    state.storm = $('#storm').value;
    loadScenario(true);
  };

  $('#zip').onchange = () => {
    const z = $('#zip').value.trim();
    if (state.boot && state.boot.areas.some(x => x.zip === z)) {
      selectZip(z, true);
    }
  };

  $('#hospitals').onchange = renderMarkers;
  if ($('#show-candidates')) $('#show-candidates').onchange = renderMarkers;

  // Print Staging Directive modal controls
  if ($('#print-plan')) $('#print-plan').onclick = showPrintDirective;
  if ($('#close-print')) $('#close-print').onclick = () => $('#print-modal').close();
  if ($('#do-print')) $('#do-print').onclick = () => window.print();
  if ($('#print-modal')) $('#print-modal').onclick = e => { if (e.target === $('#print-modal')) $('#print-modal').close(); };
  if ($('#close-popup')) $('#close-popup').onclick = () => { $('#prediction-popup').hidden = true; };

  // Outer Houston Sector Camera Navigation
  const sectorPresets = {
    all: { center: [-95.42, 29.80], zoom: 9.3 },
    west: { center: [-95.73, 29.80], zoom: 11.2 }, // Katy, Addicks, Cinco Ranch
    north: { center: [-95.45, 30.14], zoom: 11.2 }, // The Woodlands, Conroe, Spring
    southwest: { center: [-95.63, 29.60], zoom: 11.2 }, // Sugar Land, Missouri City, Fort Bend
    south: { center: [-95.26, 29.56], zoom: 11.0 }, // Pearland, Clear Lake, NASA
    east: { center: [-95.14, 29.74], zoom: 11.0 }, // Baytown, Pasadena, Ship Channel
    northwest: { center: [-95.65, 29.96], zoom: 11.0 }, // Cypress, Tomball
    core: { center: [-95.38, 29.75], zoom: 12.0 } // Central Urban Core
  };

  if ($('#sector-select')) {
    $('#sector-select').onchange = () => {
      const s = sectorPresets[$('#sector-select').value] || sectorPresets.all;
      if (state.gl) state.map.flyTo({ center: s.center, zoom: s.zoom, duration: 1200 });
      else state.map.setView([s.center[1], s.center[0]], Math.floor(s.zoom));
    };
  }

  $('#region').onclick = () => {
    if ($('#sector-select')) $('#sector-select').value = 'all';
    if (state.gl) state.map.fitBounds([[-96.02, 29.4], [-94.9, 30.25]], { padding: 40, pitch: 0, bearing: 0 });
    else state.map.fitBounds([[29.4, -96.02], [30.25, -94.9]]);
  };

  $('#close-xai').onclick = () => {
    $('#xai-inspector').classList.remove('open');
  };

  $('#sources').onclick = () => showDoc('sources', 'Technical Methodology & AI Staging');
  $('#pitch').onclick = () => showDoc('presentation', 'How to Explain UHAI AI Staging');
  $('#close-docs').onclick = () => $('#docs').close();
  $('#docs').onclick = e => { if (e.target === $('#docs')) $('#docs').close(); };
}

function switchMainView(tab) {
  state.mainTab = tab;
  $('#tab-btn-predictor').classList.toggle('active', tab === 'predictor');
  $('#tab-btn-analytics').classList.toggle('active', tab === 'analytics');

  $('#view-predictor').hidden = (tab !== 'predictor');
  $('#view-predictor').classList.toggle('active', tab === 'predictor');
  $('#view-analytics').hidden = (tab !== 'analytics');
  $('#view-analytics').classList.toggle('active', tab === 'analytics');

  if (tab === 'predictor' && state.map) {
    setTimeout(() => {
      if (state.gl) state.map.resize();
      else state.map.invalidateSize();
    }, 100);
  } else if (tab === 'analytics') {
    renderAnalytics();
  }
}

async function showDoc(name, title) {
  try {
    $('#docs-title').textContent = title;
    $('#docs-text').textContent = 'Loading methodology…';
    $('#docs').showModal();
    const d = await api('/api/docs?name=' + name);
    $('#docs-text').textContent = d.text;
  } catch (e) {
    $('#docs-text').textContent = e.message;
  }
}

async function initialize() {
  initControls();
  try {
    state.boot = await api('/api/bootstrap');
    $('#total-records').textContent = `${fmt(state.boot.counts.reports)} reports loaded`;
    $('#zip-list').innerHTML = state.boot.areas.map(a => `<option value="${a.zip}"></option>`).join('');
    $('#closed').innerHTML = '<option value="None">All 12 eligible sites active</option>' +
      state.boot.sites.filter(s => s.eligible).map(s => `<option value="${safe(s.name)}">${safe(s.name)}</option>`).join('');

    state.zip = state.boot.areas.find(a => a.zip === '77002')?.zip || state.boot.areas[0].zip;
    await initMap();
    await loadScenario(true);
  } catch (e) {
    busy(false);
    error(e);
    $('#map-status').textContent = 'Could not initialize database.';
  }
}

async function loadScenario(includeStorm) {
  const id = ++state.request;
  error(null);
  busy(true, 'Calculating disaster placement…');
  try {
    const reqs = [api('/api/plan?' + params())];
    if (includeStorm || !state.data) reqs.push(api('/api/storm?storm=' + state.storm));
    const values = await Promise.all(reqs);
    if (id !== state.request) return;

    state.plan = values[0];
    if (values[1]) state.data = values[1];

    $('#export').href = '/api/export?' + params();
    const w = state.data.window;
    $('#dates').textContent = `${w[0]} → ${w[1]}`;

    updateKPIs();
    renderStagedPills();
    renderLayer();
    renderMarkers();
    showPredictionPopup(true);

    const firstAmbulance = state.plan.roles.find(r => r.id === 'ambulance')?.sites[0];
    if (firstAmbulance && (!state.selectedSite || !state.selectedSite.is_selected)) {
      inspectSite(firstAmbulance, 'ambulance');
    }

    selectZip(state.zip, false);
    if (state.mainTab === 'analytics') await renderAnalytics();
    $('#footer-status').textContent = 'Calculated locally on laptop CPU';
  } catch (e) {
    error(e);
  } finally {
    if (id === state.request) busy(false);
  }
}

function updateKPIs() {
  if (!state.plan) return;
  const ambRole = state.plan.roles.find(r => r.id === 'ambulance');
  $('#kpi-ambulances').textContent = ambRole ? ambRole.sites.length : '0';
  $('#kpi-coverage').textContent = ambRole ? fmt(ambRole.coverage, 1) + '%' : '--%';

  let popCovered = 0;
  state.plan.rows.forEach(r => {
    if (r.ambulance_minutes != null && r.ambulance_minutes <= 15) {
      const a = state.boot.areas.find(x => x.zip === r.zip);
      if (a && a.population) popCovered += a.population;
    }
  });
  $('#kpi-pop').textContent = popCovered > 0 ? (popCovered / 1000000).toFixed(2) + 'M' : fmt(popCovered);
  $('#kpi-flood-safe').textContent = '100%';
}

/* ROBUST MAP ENGINE SETUP WITH 3D EXTRUSIONS */
async function initMap() {
  let webgl = false;
  try {
    const canvas = document.createElement('canvas');
    webgl = !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl') || canvas.getContext('webgl2')));
  } catch (e) {}

  if (window.maplibregl && webgl) {
    state.gl = true;
    state.map = new maplibregl.Map({
      container: 'map',
      center: [-95.42, 29.80],
      zoom: 9.3,
      attributionControl: false,
      style: {
        version: 8,
        sources: {
          'carto-dark': {
            type: 'raster',
            tiles: [
              'https://a.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png?key=cb1_4t2x_1_c071ca1b5e6c8dc1ff85a97b',
              'https://b.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png?key=cb1_4t2x_1_c071ca1b5e6c8dc1ff85a97b',
              'https://c.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png?key=cb1_4t2x_1_c071ca1b5e6c8dc1ff85a97b',
              'https://d.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png?key=cb1_4t2x_1_c071ca1b5e6c8dc1ff85a97b'
            ],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors, © CARTO'
          }
        },
        layers: [
          { id: 'background', type: 'background', paint: { 'background-color': '#09090b' } },
          { id: 'carto-dark-tiles', type: 'raster', source: 'carto-dark', minzoom: 0, maxzoom: 19 }
        ]
      }
    });

    state.map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'bottom-right');
    await new Promise((resolve, reject) => {
      state.map.once('load', resolve);
      state.map.once('error', e => reject(Error('Map load error: ' + e.error.message)));
    });

    const m = state.map;
    const empty = { type: 'FeatureCollection', features: [] };

    // County boundaries (Overlaid cleanly on Carto basemap)
    m.addSource('counties', { type: 'geojson', data: empty });
    m.addLayer({ id: 'county-fill', type: 'fill', source: 'counties', paint: { 'fill-color': '#050505', 'fill-opacity': 0.0 } });
    m.addLayer({ id: 'county-line', type: 'line', source: 'counties', paint: { 'line-color': '#71717a', 'line-width': 1.5, 'line-opacity': 0.6 } });

    // Load full Greater Houston road network
    try {
      const roads = await fetch('/mapdata/roads.geojson').then(r => r.json());
      m.addSource('roads', { type: 'geojson', data: roads });
      m.addLayer({
        id: 'roads',
        type: 'line',
        source: 'roads',
        paint: {
          'line-color': [
            'case',
            ['==', ['get', 'tier'], 1], '#ffffff',
            '#52525b'
          ],
          'line-opacity': [
            'case',
            ['==', ['get', 'tier'], 1], 0.9,
            0.6
          ],
          'line-width': [
            'interpolate', ['linear'], ['zoom'],
            7, ['case', ['==', ['get', 'tier'], 1], 1.8, 0.8],
            14, ['case', ['==', ['get', 'tier'], 1], 3.8, 2.0]
          ]
        }
      });
    } catch (e) {}

    // Reports heatmap (Monochrome)
    m.addSource('reports', { type: 'geojson', data: empty });
    m.addLayer({
      id: 'heat',
      type: 'heatmap',
      source: 'reports',
      paint: {
        'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 7, 12, 13, 30],
        'heatmap-intensity': 0.85,
        'heatmap-opacity': 0.65,
        'heatmap-color': [
          'interpolate', ['linear'], ['heatmap-density'],
          0, 'rgba(0,0,0,0)',
          0.2, '#27272a',
          0.5, '#71717a',
          0.8, '#d4d4d8',
          1, '#ffffff'
        ]
      }
    });

    // ZIP centroids across all 189 Houston areas (Monochrome)
    m.addSource('areas', { type: 'geojson', data: empty });
    m.addLayer({
      id: 'areas',
      type: 'circle',
      source: 'areas',
      paint: {
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 7, 3, 12, 6],
        'circle-color': [
          'case',
          ['boolean', ['get', 'selected'], false], '#ffffff',
          ['boolean', ['get', 'covered'], false], '#ffffff',
          '#3f3f46'
        ],
        'circle-opacity': [
          'case',
          ['boolean', ['get', 'selected'], false], 1.0,
          ['boolean', ['get', 'covered'], false], 0.85,
          0.4
        ],
        'circle-stroke-color': '#000000',
        'circle-stroke-width': 1.5
      }
    });

    m.on('click', 'areas', e => selectZip(e.features[0].properties.zip, false));
    m.on('mouseenter', 'areas', () => m.getCanvas().style.cursor = 'pointer');
    m.on('mouseleave', 'areas', () => m.getCanvas().style.cursor = '');
  } else {
    // 2D Leaflet Fallback (Monochrome Carto basemap with Key)
    state.gl = false;
    state.map = L.map('map', { zoomControl: true }).setView([29.80, -95.42], 9);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png?key=cb1_4t2x_1_c071ca1b5e6c8dc1ff85a97b', {
      maxZoom: 19,
      subdomains: 'abcd',
      attribution: '© OpenStreetMap contributors, © CARTO'
    }).addTo(state.map);
    try {
      const roads = await fetch('/mapdata/roads.geojson').then(r => r.json());
      L.geoJSON(roads, {
        style: f => ({
          color: f.properties?.tier === 1 ? '#ffffff' : '#52525b',
          weight: f.properties?.tier === 1 ? 2 : 1,
          opacity: 0.8
        })
      }).addTo(state.map);
    } catch (e) {}
  }
  state.mapReady = true;
}

function areaFeatures() {
  return pointFC(state.boot.areas, a => {
    const p = state.plan ? state.plan.rows.find(r => r.zip === a.zip) : null;
    const covered = p && p.ambulance_minutes != null && p.ambulance_minutes <= 15;
    return {
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [a.lon, a.lat] },
      properties: { zip: a.zip, covered, selected: a.zip === state.zip }
    };
  });
}

async function renderLayer() {
  if (!state.data || !state.mapReady) return;
  const d = layerDefs.find(x => x[0] === state.layer) || layerDefs[0];
  $('#layer-help').textContent = d[1];

  $('#legend').style.background = 'linear-gradient(90deg, #18181b, #71717a, #ffffff)';

  const reports = d[3] ? state.data.reports.features.filter(f => f.properties.category === d[3]) : [];

  if (state.gl) {
    const m = state.map;
    m.getSource('counties').setData(state.data.counties);
    m.setPaintProperty('county-fill', 'fill-color', state.layer === 'outages' ?
      ['case', ['any', ['get', 'flagged'], ['!', ['get', 'available']]], '#27272a',
      ['interpolate', ['linear'], ['get', 'intensity'], 0, '#09090b', 0.5, '#52525b', 1, '#ffffff']] :
      'transparent'
    );
    m.setPaintProperty('county-fill', 'fill-opacity', state.layer === 'outages' ? 0.75 : 0.0);
    m.getSource('reports').setData({ type: 'FeatureCollection', features: reports });
    m.getSource('areas').setData(areaFeatures());
    m.setPaintProperty('areas', 'circle-color', state.layer === 'coverage' ?
      ['case', ['get', 'covered'], '#ffffff', '#3f3f46'] :
      ['case', ['get', 'selected'], '#ffffff', '#71717a']
    );
    m.setPaintProperty('areas', 'circle-radius', ['case', ['get', 'selected'], 6.5, 3]);
  } else {
    for (const key of ['countyLayer', 'heatLayer', 'areaLayer']) {
      if (state[key]) state.map.removeLayer(state[key]);
    }
    state.countyLayer = L.geoJSON(state.data.counties, {
      style: f => ({
        color: '#71717a',
        weight: 1.5,
        fillColor: state.layer === 'outages' ? (f.properties.flagged || !f.properties.available ? '#27272a' : `hsl(0 0% ${20 + f.properties.intensity * 60}%)`) : '#050505',
        fillOpacity: state.layer === 'outages' ? 0.75 : 0.0
      })
    }).addTo(state.map);

    if (reports.length) {
      state.heatLayer = L.heatLayer(reports.map(f => [f.geometry.coordinates[1], f.geometry.coordinates[0], 0.5]), { radius: 22, blur: 16 }).addTo(state.map);
    }
    state.areaLayer = L.geoJSON(areaFeatures(), {
      pointToLayer: (f, ll) => L.circleMarker(ll, {
        radius: f.properties.selected ? 6 : 3,
        color: '#000000',
        weight: 1.5,
        fillColor: state.layer === 'coverage' ? (f.properties.covered ? '#ffffff' : '#3f3f46') : '#71717a',
        fillOpacity: 0.95
      }),
      onEachFeature: (f, l) => l.on('click', () => selectZip(f.properties.zip, false))
    }).addTo(state.map);
  }

  $('#map-status').textContent = state.layer === 'coverage' ? 'White = ≤15 min rapid response target · Charcoal = Outside target' :
    state.layer === 'outages' ? `${state.data.history.length} counties · White = Peak grid outages` :
    `${fmt(reports.length)} 311 hurricane distress reports`;
}

/* CLICKABLE SITE MARKERS WITH REAL TACTICAL BADGE ICONS */
function renderMarkers() {
  if (!state.plan || !state.mapReady) return;
  state.markers.forEach(m => state.gl ? m.remove() : state.map.removeLayer(m));
  state.markers = [];

  const combined = new Map();
  state.plan.roles.forEach(r => {
    r.sites.forEach(name => {
      if (!combined.has(name)) combined.set(name, []);
      combined.get(name).push(r);
    });
  });

  for (const [name, roles] of combined) {
    const s = state.boot.sites.find(x => x.name === name);
    if (!s) continue;
    const primaryRole = roles[0].id;
    const label = roles.map(r => ({ ambulance: '🚑', cooling: '❄️', community: '🏠', dispatch: '🚨' }[r.id])).join(' ');
    addSiteMarker(s.lon, s.lat, label, name, roles);
  }

  // Show candidate staging sites across outskirts and distant areas
  if ($('#show-candidates')?.checked && state.boot?.sites) {
    state.boot.sites.forEach(s => {
      if (combined.has(s.name)) return;
      addCandidateMarker(s.lon, s.lat, s.eligible ? '⌖' : '⚠️', s.name, !s.eligible);
    });
  }

  if ($('#hospitals').checked) {
    state.boot.hospitals.forEach(h => {
      addHospitalMarker(h.longitude, h.latitude, '🏥', h.name);
    });
  }
}

function addCandidateMarker(lon, lat, iconText, name, isDisqualified) {
  const shortName = name
    .replace(' Multi-Service Center', ' MSC')
    .replace(' Community Center', ' CC')
    .replace(' Health and Multi-Service Center', ' MSC');

  const el = document.createElement('button');
  el.className = `site-marker ${isDisqualified ? 'marker-disqualified' : 'marker-candidate'}`;
  el.innerHTML = `
    <div class="marker-badge">
      <span class="marker-icon">${iconText}</span>
      <span class="marker-label">${safe(shortName)}${isDisqualified ? ' (Zone AE)' : ' (Outskirts)'}</span>
    </div>
    <div class="marker-pin-stem"></div>
  `;
  el.title = `${name}\n${isDisqualified ? 'Disqualified (FEMA Zone AE 100-Year Flood Risk)' : 'Potential Staging / Build Location for Outskirts'}\nClick to inspect AI placement evaluation`;

  el.onclick = e => {
    e.stopPropagation();
    inspectSite(name, 'ambulance');
  };

  if (state.gl) {
    const marker = new maplibregl.Marker({ element: el, anchor: 'bottom' }).setLngLat([lon, lat]).addTo(state.map);
    state.markers.push(marker);
  } else {
    const marker = L.marker([lat, lon], {
      icon: L.divIcon({ className: '', html: el.outerHTML, iconSize: [120, 36], iconAnchor: [60, 36] })
    }).addTo(state.map);
    marker.on('click', () => inspectSite(name, 'ambulance'));
    state.markers.push(marker);
  }
}

function addSiteMarker(lon, lat, iconText, name, roles) {
  const primaryRoleId = roles[0].id;
  const cfg = roleConfig[primaryRoleId] || roleConfig.ambulance;
  const shortName = name
    .replace(' Multi-Service Center', ' MSC')
    .replace(' Community Center', ' CC')
    .replace(' Health and Multi-Service Center', ' MSC');

  const el = document.createElement('button');
  el.className = `site-marker ${cfg.markerClass}`;
  el.innerHTML = `
    <div class="marker-badge best-placement">
      <span class="marker-green-x" title="AI Predicted Best Place">✖</span>
      <span class="marker-icon">${iconText}</span>
      <span class="marker-label">${safe(shortName)}</span>
    </div>
    <div class="marker-pin-stem green-stem"></div>
  `;
  el.title = `[BEST PLACE ✖] ${name}\nRoles: ${roles.map(r => r.name).join(', ')}\nClick to inspect AI placement rationale`;

  el.onclick = e => {
    e.stopPropagation();
    inspectSite(name, primaryRoleId);
  };

  if (state.gl) {
    const marker = new maplibregl.Marker({ element: el, anchor: 'bottom' }).setLngLat([lon, lat]).addTo(state.map);
    state.markers.push(marker);
  } else {
    const marker = L.marker([lat, lon], {
      icon: L.divIcon({ className: '', html: el.outerHTML, iconSize: [120, 36], iconAnchor: [60, 36] })
    }).addTo(state.map);
    marker.on('click', () => inspectSite(name, primaryRoleId));
    state.markers.push(marker);
  }
}

function addHospitalMarker(lon, lat, iconText, name) {
  const el = document.createElement('div');
  el.className = 'site-marker marker-hospital';
  const shortName = name.replace(' Hospital', '').replace(' Medical Center', ' Med');
  el.innerHTML = `
    <div class="marker-badge hospital-badge">
      <span class="marker-icon">🏥</span>
      <span class="marker-label">${safe(shortName)}</span>
    </div>
    <div class="marker-pin-stem"></div>
  `;
  el.title = `${name}\nFixed Regional Hospital Anchor`;

  if (state.gl) {
    const marker = new maplibregl.Marker({ element: el, anchor: 'bottom' }).setLngLat([lon, lat]).addTo(state.map);
    state.markers.push(marker);
  } else {
    const marker = L.marker([lat, lon], {
      icon: L.divIcon({ className: '', html: el.outerHTML, iconSize: [100, 32], iconAnchor: [50, 32] })
    }).addTo(state.map);
    state.markers.push(marker);
  }
}

/* EXPLAINABLE AI (XAI) DRAWER */
async function inspectSite(siteName, roleId) {
  state.selectedSiteName = siteName;
  state.selectedRole = roleId || 'ambulance';

  const drawer = $('#xai-inspector');
  drawer.classList.add('open');

  $('#xai-site-name').textContent = siteName;
  const cfg = roleConfig[state.selectedRole] || roleConfig.ambulance;
  $('#xai-site-role').textContent = `${cfg.icon} ${cfg.name}`;
  $('#xai-site-role').style.color = cfg.color;
  $('#xai-site-role').style.borderColor = cfg.color;

  try {
    const exp = await api(`/api/explain?site=${encodeURIComponent(siteName)}&role=${state.selectedRole}&${params()}`);
    state.selectedSite = exp;
    renderExplainabilityUI(exp);
  } catch (e) {
    $('#xai-why-chosen').textContent = `Could not load explanation: ${e.message}`;
  }

  const s = state.boot.sites.find(x => x.name === siteName);
  if (s && state.map) {
    if (state.gl) state.map.flyTo({ center: [s.lon, s.lat], zoom: 12.0, pitch: 0 });
    else state.map.setView([s.lat, s.lon], 12);
  }
}

function renderExplainabilityUI(exp) {
  const banner = $('#xai-flood-banner');
  if (exp.is_flood_excluded) {
    banner.className = 'status-badge-flood danger';
    $('#xai-flood-title').textContent = '⚠️ FEMA Zone AE · 100-Year Flood Risk';
    $('#xai-flood-desc').textContent = 'Disqualified due to high probability of submerged access roads.';
  } else {
    banner.className = 'status-badge-flood';
    $('#xai-flood-title').textContent = '🛡️ FEMA Zone X · Elevated Safe Ground';
    $('#xai-flood-desc').textContent = '0.2% annual chance minimal hazard. Continuous dry egress.';
  }

  $('#xai-why-chosen').textContent = exp.why_chosen;
  $('#xai-waiting-strategy').textContent = exp.tactical_waiting_strategy;

  $('#xai-factors').innerHTML = exp.decision_factors.map(f => `
    <div class="factor-item">
      <div class="factor-head">
        <span>${safe(f.factor)}</span>
        <b style="color:var(--c-mint)">${f.weight}%</b>
      </div>
      <div class="factor-bar-track">
        <div class="factor-bar-fill" style="width:${f.weight * 2.5}%;background:${f.status.includes('FAIL') ? '#f43f5e' : 'var(--c-mint)'}"></div>
      </div>
      <div class="factor-desc">${safe(f.desc)}</div>
    </div>
  `).join('');

  $('#xai-runner-up').textContent = exp.runner_up_comparison;
  $('#xai-m-pop').textContent = fmt(exp.metrics.population_covered);
  $('#xai-m-dme').textContent = fmt(exp.metrics.dme_patients_covered);
  $('#xai-m-time').textContent = fmt(exp.metrics.average_response_minutes, 1);
  $('#xai-m-zips').textContent = fmt(exp.metrics.assigned_zip_count);
}

function renderStagedPills() {
  if (!state.plan) return;
  const list = $('#xai-staged-list');
  const items = [];

  state.plan.roles.forEach(r => {
    r.sites.forEach(siteName => {
      const cfg = roleConfig[r.id];
      items.push(`
        <button class="staged-site-btn" data-site="${safe(siteName)}" data-role="${r.id}">
          <span>${cfg.icon}</span>
          <span>${safe(siteName)}</span>
        </button>
      `);
    });
  });

  items.push(`
    <button class="staged-site-btn" style="border-color:#f43f5e33;color:#ff94a6" data-site="Kashmere Multi-Service Center" data-role="ambulance">
      <span>⚠️</span>
      <span>Kashmere MSC (Flood AE)</span>
    </button>
  `);

  list.innerHTML = items.join('');
  $$('#xai-staged-list button').forEach(b => {
    b.onclick = () => inspectSite(b.dataset.site, b.dataset.role);
  });
}

function selectZip(zip, fly) {
  state.zip = zip;
  $('#zip').value = zip;
  const a = state.boot.areas.find(x => x.zip === zip);
  const p = state.plan ? state.plan.rows.find(r => r.zip === zip) : null;
  if (!a || !p) return;

  const facts = [
    ['Population', fmt(a.population)],
    ['Medicare DME (Devices)', fmt(a.medical)],
    ['Flooding Reports', fmt(p.flood)],
    ['Debris / Electrical', `${fmt(p.tree)} / ${fmt(p.electrical)}`]
  ];

  $('#area-detail').innerHTML = `
    <div style="font-weight:700;color:#fff;margin-bottom:4px">ZIP ${safe(zip)}</div>
    ${facts.map(([k, v]) => `<div class="fact-row"><span>${safe(k)}</span><b>${safe(v)}</b></div>`).join('')}
    <div style="margin-top:6px;font-size:9px;color:var(--text-dim);text-transform:uppercase">Nearest Placements:</div>
    ${state.plan.roles.map(r => `
      <div class="fact-row">
        <span>${safe(r.name)}</span>
        <b class="${p[r.id + '_minutes'] <= 15 ? 'within' : 'outside'}">${fmt(p[r.id + '_minutes'], 1)}m</b>
      </div>
    `).join('')}
  `;

  if (state.gl) {
    state.map.getSource('areas').setData(areaFeatures());
    if (fly) state.map.flyTo({ center: [a.lon, a.lat], zoom: 11.5, pitch: 0 });
  } else if (fly) {
    state.map.setView([a.lat, a.lon], 11);
  }
}

/* VIEW 2: REGIONAL ANALYTICS HUB */
async function renderAnalytics() {
  if (!state.plan) return;
  const content = $('#analytics-content');
  const tab = state.analyticsTab;
  $('#analytics-meta').textContent = '189 Regional ZIP Areas · 14 Staging Candidates';

  if (tab === 'placements') {
    content.innerHTML = `
      <div class="table-note">Complete disaster staging matrix. Times reflect drive minutes under 2.0× hurricane road slowdown (15-minute response target).</div>
      ${table(
        ['ZIP Centroid', 'Ambulance Site', 'EMS (min)', 'Incident Outpost', 'Rescue (min)', 'Cooling Hub', 'Cooling (min)', 'Community Hub', 'Relief (min)'],
        state.plan.rows.map(r => `
          <tr data-zip="${r.zip}">
            <td><strong>${r.zip}</strong></td>
            <td>${safe(r.ambulance_site || 'Unassigned')}</td>
            <td class="${r.ambulance_minutes <= 15 ? 'within' : 'outside'}">${fmt(r.ambulance_minutes, 1)}</td>
            <td>${safe(r.dispatch_site || 'Unassigned')}</td>
            <td class="${r.dispatch_minutes <= 15 ? 'within' : 'outside'}">${fmt(r.dispatch_minutes, 1)}</td>
            <td>${safe(r.cooling_site || 'Unassigned')}</td>
            <td class="${r.cooling_minutes <= 15 ? 'within' : 'outside'}">${fmt(r.cooling_minutes, 1)}</td>
            <td>${safe(r.community_site || 'Unassigned')}</td>
            <td class="${r.community_minutes <= 15 ? 'within' : 'outside'}">${fmt(r.community_minutes, 1)}</td>
          </tr>
        `)
      )}
    `;
    $$('tr[data-zip]').forEach(r => r.onclick = () => {
      switchMainView('predictor');
      selectZip(r.dataset.zip, true);
    });
  } else if (tab === 'evidence') {
    content.innerHTML = `
      <div class="evidence-tools">
        <input id="evidence-search" aria-label="Search damage descriptions" placeholder="Search fallen trees, roof damage, bayou flooding, county…">
      </div>
      <div id="evidence-table"></div>
    `;
    $('#evidence-search').oninput = renderEvidence;
    renderEvidence();
  } else if (tab === 'supplies') {
    content.innerHTML = `
      <div class="supply-tools">
        <label>Cooling %<input id="cooling-pct" type="number" value="30" min="0" max="100"></label>
        <label>Community %<input id="community-pct" type="number" value="50" min="0" max="100"></label>
        <label>Health %<input id="health-pct" type="number" value="10" min="0" max="100"></label>
        <label>Days<input id="supply-days" type="number" value="3" min="1" max="14"></label>
        <button id="update-supplies" class="btn-primary">Calculate Rations</button>
        <button id="download-supplies" class="btn-ghost">Download CSV</button>
      </div>
      <div class="table-note">Hot meals calculated at 3 rations/person/day for displaced residents.</div>
      <div id="supply-table">Loading supplies…</div>
    `;
    $('#update-supplies').onclick = loadSupplies;
    $('#download-supplies').onclick = downloadSupplies;
    await loadSupplies();
  } else if (tab === 'model') {
    renderModel();
  }
}

function renderEvidence() {
  const q = ($('#evidence-search')?.value || '').toLowerCase();
  const rows = state.data.evidence.filter(r => JSON.stringify(r).toLowerCase().includes(q));
  $('#analytics-meta').textContent = `${rows.length} Reports`;
  $('#evidence-table').innerHTML = rows.length ? table(
    ['Date', 'Jurisdiction', 'Observed Narrative', 'Source'],
    rows.map(r => `
      <tr>
        <td><strong>${safe(r.date)}</strong></td>
        <td>${safe(r.event_type)}<br><span style="color:var(--text-dim)">${safe(r.county_or_zone)}</span></td>
        <td style="max-width:650px">${safe(r.narrative)}</td>
        <td>${/^https:\/\//.test(r.source_url) ? `<a href="${safe(r.source_url)}" target="_blank" rel="noopener">${safe(r.source || 'Source')} ↗</a>` : safe(r.source)}</td>
      </tr>
    `)
  ) : '<div class="table-note">No matching field reports found.</div>';
}

async function loadSupplies() {
  try {
    $('#update-supplies').disabled = true;
    const p = new URLSearchParams({
      cooling_pct: $('#cooling-pct').value,
      community_pct: $('#community-pct').value,
      health_pct: $('#health-pct').value,
      days: $('#supply-days').value
    });
    state.supplies = await api('/api/supplies?' + p);
    const keys = [
      'ML flood-household members (scenario)',
      'Cooling visitors (assumed)',
      'Community visitors (assumed)',
      'Health-service users (assumed)',
      'Community meals (3/person/day assumption)'
    ];
    $('#supply-table').innerHTML = table(
      ['ZIP Area', 'Displaced Members', 'Cooling Visitors', 'Community Relief', 'Health Triage', 'Hot Meals (3/day)'],
      state.supplies.rows.map(r => `
        <tr>
          <td><strong>${safe(r.zip)}</strong></td>
          ${keys.map(k => `<td>${fmt(r[k])}</td>`).join('')}
        </tr>
      `)
    );
  } catch (e) {
    error(e);
  } finally {
    if ($('#update-supplies')) $('#update-supplies').disabled = false;
  }
}

function downloadSupplies() {
  if (!state.supplies) return;
  const rows = state.supplies.rows;
  const keys = Object.keys(rows[0]);
  const quote = v => '"' + String(v ?? '').replace(/"/g, '""') + '"';
  const csv = [keys.map(quote).join(','), ...rows.map(r => keys.map(k => quote(r[k])).join(','))].join('\r\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = `UHAI-Disaster-Supplies-${state.storm}.csv`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

function renderModel() {
  const m = state.boot.model;
  $('#analytics-content').innerHTML = `
    <div class="model-grid">
      <div>
        <div style="font-size:9px;color:var(--c-mint);font-weight:700">MACHINE LEARNING EVALUATION</div>
        <h3>Post-Disaster Household Displacement Model</h3>
        <p>${safe(m.task)}. Predicts displaced household member volumes from FEMA Harvey registrations.</p>
        <button id="train" class="btn-primary" style="margin:8px 0">Retrain Model Locally</button>
        <span id="train-status" style="font-size:10px;color:var(--text-dim);margin-left:8px"></span>
        <div style="margin-top:12px;font-size:9px;color:var(--text-dim);text-transform:uppercase">Scientific Boundaries:</div>
        <ul>${m.limitations.map(x => `<li>${safe(x)}</li>`).join('')}</ul>
      </div>
      <div>
        <div style="font-size:9px;color:var(--text-dim);text-transform:uppercase">Holdout Test Comparison:</div>
        ${[
          ['FEMA Source Records', fmt(m.source_records)],
          ['Train / Test Split', `${m.train_zip_codes} train / ${m.test_zip_codes} test`],
          ['Baseline MAE Error', `${fmt(m.baseline_mae_reported_members_per_zip, 1)} members / ZIP`],
          ['Random Forest MAE Error', `${fmt(m.model_mae_reported_members_per_zip, 1)} members / ZIP`],
          ['Error Reduction vs Baseline', `${fmt(m.mae_reduction_percent, 2)}%`]
        ].map(([k, v]) => `
          <div class="metric"><span>${safe(k)}</span><b>${safe(v)}</b></div>
        `).join('')}
        <p style="margin-top:12px;font-size:10px">${safe(m.validation)}.</p>
      </div>
    </div>
  `;
  $('#train').onclick = async () => {
    const b = $('#train');
    b.disabled = true;
    $('#train-status').textContent = 'Training on laptop CPU…';
    try {
      state.boot.model = await api('/api/train', { method: 'POST' });
      renderModel();
      $('#train-status').textContent = 'Retraining complete.';
      state.supplies = null;
    } catch (e) {
      error(e);
      b.disabled = false;
      $('#train-status').textContent = 'Training failed.';
    }
  };
}

function showPrintDirective() {
  if (!state.plan || !state.boot) return;
  const modal = $('#print-modal');
  const body = $('#print-body');

  const ambRole = state.plan.roles.find(r => r.id === 'ambulance');
  const dispRole = state.plan.roles.find(r => r.id === 'dispatch');
  const coolRole = state.plan.roles.find(r => r.id === 'cooling');
  const commRole = state.plan.roles.find(r => r.id === 'community');

  let popCovered = 0;
  let dmeCovered = 0;
  state.plan.rows.forEach(r => {
    if (r.ambulance_minutes != null && r.ambulance_minutes <= 15) {
      const a = state.boot.areas.find(x => x.zip === r.zip);
      if (a) {
        if (a.population) popCovered += a.population;
        if (a.medical) dmeCovered += a.medical;
      }
    }
  });

  const selectedSiteRows = [];
  const assignedBySite = new Map();
  state.plan.rows.forEach(r => {
    ['ambulance', 'dispatch', 'cooling', 'community'].forEach(roleId => {
      const sName = r[roleId + '_site'];
      if (!sName) return;
      if (!assignedBySite.has(sName)) assignedBySite.set(sName, { zips: 0, pop: 0, dme: 0, maxDrive: 0 });
      const stats = assignedBySite.get(sName);
      stats.zips++;
      const a = state.boot.areas.find(x => x.zip === r.zip);
      if (a) {
        stats.pop += a.population || 0;
        stats.dme += a.medical || 0;
      }
      const dr = r[roleId + '_minutes'] || 0;
      if (dr > stats.maxDrive) stats.maxDrive = dr;
    });
  });

  state.boot.sites.filter(s => s.eligible).forEach(s => {
    const rolesActive = [];
    if (ambRole?.sites.includes(s.name)) rolesActive.push('🚑 Ambulance');
    if (dispRole?.sites.includes(s.name)) rolesActive.push('🚨 Emergency Outpost');
    if (coolRole?.sites.includes(s.name)) rolesActive.push('❄️ Cooling Hub');
    if (commRole?.sites.includes(s.name)) rolesActive.push('🏠 Community Hub');

    const stats = assignedBySite.get(s.name) || { zips: 0, pop: 0, dme: 0, maxDrive: 0 };
    if (rolesActive.length > 0) {
      selectedSiteRows.push(`
        <tr>
          <td><strong>${safe(s.name)}</strong><br><span style="font-size:10px;color:var(--text-dim)">${safe(s.address)}</span></td>
          <td>${rolesActive.join(', ')}</td>
          <td><span class="status-badge" style="background:#27272a;color:#fff;padding:2px 6px;border-radius:4px;font-size:10px">Zone X (Dry Ground)</span></td>
          <td>${fmt(stats.zips)} ZIPs</td>
          <td>${fmt(stats.pop)}</td>
          <td>${fmt(stats.maxDrive, 1)}m</td>
        </tr>
      `);
    }
  });

  const candidateOutskirtsRows = state.boot.sites.map(s => `
    <tr>
      <td><strong>${safe(s.name)}</strong></td>
      <td>${safe(s.address)}</td>
      <td>${s.eligible ? '<span style="color:#ffffff">🛡️ Zone X (Eligible)</span>' : '<span style="color:#a1a1aa">⚠️ Zone AE (100-Yr Floodway)</span>'}</td>
      <td>${s.eligible ? 'Available Outskirts Staging / Build Zone' : 'Disqualified (Surface Flood Ingress Risk)'}</td>
    </tr>
  `).join('');

  body.innerHTML = `
    <div class="print-section">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
        <div>
          <h2 style="font-size:16px;color:#fff;margin:0 0 4px 0">INCIDENT DISASTER STAGING DIRECTIVE</h2>
          <div style="font-size:11px;color:var(--text-dim)">Scenario: Hurricane ${state.storm} · Slowdown: 2.0× Flood Delay · Target: 15-Minute Response Window</div>
        </div>
        <div style="text-align:right;font-size:11px;color:var(--text-dim)">
          Generated: ${new Date().toLocaleDateString()}<br>
          UHAI AI Optimization Model
        </div>
      </div>

      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0;background:#141416;padding:12px;border-radius:6px;border:1px solid #27272a">
        <div><small style="color:var(--text-dim);font-size:10px">AMBULANCES</small><div style="font-size:18px;font-weight:700;color:#fff">${$('#ambulance')?.value || 2} Predicted</div></div>
        <div><small style="color:var(--text-dim);font-size:10px">EMERGENCY BUILDINGS</small><div style="font-size:18px;font-weight:700;color:#fff">${$('#dispatch')?.value || 2} Predicted</div></div>
        <div><small style="color:var(--text-dim);font-size:10px">COMMUNITY HUBS</small><div style="font-size:18px;font-weight:700;color:#fff">${$('#community')?.value || 3} Predicted</div></div>
        <div><small style="color:var(--text-dim);font-size:10px">COOLING &amp; POWER HUBS</small><div style="font-size:18px;font-weight:700;color:#fff">${$('#cooling')?.value || 3} Predicted</div></div>
      </div>

      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:12px;background:#18181b;padding:10px;border-radius:6px">
        <div><small style="color:var(--text-dim);font-size:10px">15-MIN EMS REACH</small><div style="font-size:14px;font-weight:700;color:#fff">${$('#kpi-coverage').textContent} of Demand</div></div>
        <div><small style="color:var(--text-dim);font-size:10px">POPULATION REACHED</small><div style="font-size:14px;font-weight:700;color:#fff">${fmt(popCovered)} Residents</div></div>
        <div><small style="color:var(--text-dim);font-size:10px">MEDICARE DME PATIENTS</small><div style="font-size:14px;font-weight:700;color:#fff">${fmt(dmeCovered)} Fragile Patients</div></div>
      </div>
    </div>

    <div class="print-section">
      <h3>1. Primary Predicted Resource Staging Locations (Active Plan)</h3>
      <div style="font-size:11px;color:var(--text-dim);margin-bottom:8px">These locations optimize survival rates under simulated 2.0× bayou and arterial flooding delays.</div>
      ${table(
        ['Facility / Location', 'Assigned Roles', 'FEMA Elevation', 'Assigned Coverage', 'Residents Served', 'Max Drive (min)'],
        selectedSiteRows
      )}
    </div>

    <div class="print-section">
      <h3>2. Complete Regional Outskirts &amp; Distant Staging Capacity</h3>
      <div style="font-size:11px;color:var(--text-dim);margin-bottom:8px">Candidate staging and build zones evaluated by AI across Greater Houston outskirts and suburban perimeter.</div>
      ${table(
        ['Candidate Facility / Staging Zone', 'Full Address', 'FEMA Flood Zone Elevation', 'AI Evaluation &amp; Recommendation'],
        candidateOutskirtsRows.split('</tr>').filter(Boolean).map(x => x + '</tr>')
      )}
    </div>

    <div class="print-section">
      <h3>3. Operational Standby &amp; Tactical Instructions</h3>
      <ul style="font-size:11px;line-height:1.6;margin:0;padding-left:18px;color:#d4d4d8">
        <li><strong>FEMA Flood Zone AE Exclusion:</strong> Kashmere Multi-Service Center and Alief Center must NOT be used for vehicle staging or resident shelters due to 100-year flood plain submergence.</li>
        <li><strong>15-Minute Response Corridor Target:</strong> Units staged at outer anchors (Radack CC in West Houston/Katy, Sunnyside in South Houston, Acres Homes in Northwest) provide dry highway access via I-10, Beltway 8, and US-290 without crossing flooded bayous.</li>
        <li><strong>DME Medical Vulnerability Priority:</strong> HHS Medicare power-dependent patients are targeted first with auxiliary generators and rapid paramedic dispatch.</li>
      </ul>
    </div>
  `;

  modal.showModal();
}

function showPredictionPopup(autoOpen = false) {
  if (!state.plan || !state.boot) return;
  const popup = $('#prediction-popup');
  const content = $('#prediction-popup-content');
  if (!popup || !content) return;

  const combined = new Map();
  state.plan.roles.forEach(r => {
    r.sites.forEach(name => {
      if (!combined.has(name)) combined.set(name, []);
      combined.get(name).push(r);
    });
  });

  const cards = [];
  for (const [name, roles] of combined) {
    const shortName = name
      .replace(' Multi-Service Center', ' MSC')
      .replace(' Community Center', ' CC')
      .replace(' Health and Multi-Service Center', ' MSC');
    const roleIcons = roles.map(r => ({ ambulance: '🚑', cooling: '❄️', community: '🏠', dispatch: '🚨' }[r.id])).join(' ');
    const roleNames = roles.map(r => r.name).join(', ');

    cards.push(`
      <div class="popup-site-card" data-site="${safe(name)}" data-role="${roles[0].id}">
        <div class="popup-site-left">
          <span class="marker-green-x" style="width:16px;height:16px;font-size:11px">✖</span>
          <div>
            <div class="popup-card-name">${safe(shortName)}</div>
            <div class="popup-card-roles">${roleIcons} ${safe(roleNames)}</div>
          </div>
        </div>
        <button class="popup-btn-inspect">Inspect ↗</button>
      </div>
    `);
  }

  content.innerHTML = `
    <div style="font-size:10px;color:var(--text-sub);margin-bottom:6px">
      ${combined.size} optimal locations predicted by AI model. Marked on map with <strong style="color:#22c55e">Green ✖</strong>:
    </div>
    ${cards.join('')}
  `;

  $$('#prediction-popup-content .popup-site-card').forEach(card => {
    card.onclick = () => {
      inspectSite(card.dataset.site, card.dataset.role);
    };
  });

  if (autoOpen || !popup.hidden) {
    popup.hidden = false;
  }
}

// Start portal
initialize();
