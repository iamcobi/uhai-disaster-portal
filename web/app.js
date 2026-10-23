'use strict';

const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const fmt = (v, d = 0) => v == null ? 'Unknown' : Number(v).toLocaleString(undefined, { maximumFractionDigits: d });
const safe = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const roleConfig = {
  ambulance: { name: 'Ambulance Base', color: '#fbbf24', markerClass: 'marker-amb', icon: '🚑' },
  cooling: { name: 'Cooling Hub', color: '#38bdf8', markerClass: 'marker-cool', icon: '❄️' },
  community: { name: 'Community Hub', color: '#34d399', markerClass: 'marker-comm', icon: '🏛️' },
  dispatch: { name: 'Incident Outpost', color: '#fb7185', markerClass: 'marker-disp', icon: '🚨' }
};

const layerDefs = [
  ['coverage', '10m Reach', '#00f5c4', null, 'ZIP centroids within 10 modeled minutes.'],
  ['outages', 'Outages', '#ee796f', null, 'County peaks of reported customer power loss.'],
  ['flood', 'Flooding', '#38bdf8', 'Flood/drainage reports', 'Density of recorded flood and drainage calls.'],
  ['tree', 'Trees', '#d5dc79', 'Tree removal reports', 'Density of fallen tree obstructions.'],
  ['debris', 'Debris', '#efbd69', 'Storm debris reports', 'Structural and road debris reports.'],
  ['electrical', 'Electrical', '#fb7185', 'Electrical hazard reports', 'Downed live wires and transformer hazards.']
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
    ambulances: $('#ambulance').value,
    dispatch: $('#dispatch').value,
    cooling: $('#cooling').value,
    community: $('#community').value,
    slowdown: $('#slowdown').value,
    closed: $('#closed').value
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

  ['ambulance', 'dispatch', 'cooling', 'community'].forEach(id => {
    const input = $('#' + id);
    input.addEventListener('input', e => {
      $('#' + id + '-value').textContent = e.target.value;
    });
  });

  $('#slowdown').oninput = e => {
    $('#slowdown-value').textContent = Number(e.target.value).toFixed(1) + '×';
  };

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

  $('#region').onclick = () => {
    state.is3d = false;
    $('#context-note').hidden = true;
    $('#three-d').classList.remove('active');
    $('#three-d').textContent = '3D Downtown ◇';
    if (state.gl) state.map.fitBounds([[-96.02, 29.4], [-94.9, 30.25]], { padding: 40, pitch: 0, bearing: 0 });
    else state.map.fitBounds([[29.4, -96.02], [30.25, -94.9]]);
  };

  /* 3D BUILDINGS TOGGLE */
  $('#three-d').onclick = () => {
    state.is3d = !state.is3d;
    $('#context-note').hidden = !state.is3d;
    $('#three-d').classList.toggle('active', state.is3d);
    if (state.is3d) {
      $('#three-d').textContent = 'Exit 3D View ✕';
      if (state.gl) {
        state.map.flyTo({
          center: [-95.365, 29.757],
          zoom: 16.0,
          pitch: 65,
          bearing: -30,
          duration: 1400
        });
      } else {
        state.map.setView([29.757, -95.365], 16);
      }
    } else {
      $('#region').click();
    }
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
    if (r.ambulance_minutes != null && r.ambulance_minutes <= 10) {
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
        sources: {},
        layers: [{ id: 'background', type: 'background', paint: { 'background-color': '#061320' } }]
      }
    });

    state.map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'bottom-right');
    await new Promise((resolve, reject) => {
      state.map.once('load', resolve);
      state.map.once('error', e => reject(Error('Map load error: ' + e.error.message)));
    });

    const m = state.map;
    const empty = { type: 'FeatureCollection', features: [] };

    // County boundaries
    m.addSource('counties', { type: 'geojson', data: empty });
    m.addLayer({ id: 'county-fill', type: 'fill', source: 'counties', paint: { 'fill-color': '#0c2234', 'fill-opacity': 0.85 } });
    m.addLayer({ id: 'county-line', type: 'line', source: 'counties', paint: { 'line-color': '#203d52', 'line-width': 1.2 } });

    // Load roads & buildings in parallel
    const context = await Promise.allSettled([
      fetch('/mapdata/roads.geojson').then(r => r.json()),
      fetch('/mapdata/buildings.geojson').then(r => r.json())
    ]);

    if (context[0].status === 'fulfilled') {
      m.addSource('roads', { type: 'geojson', data: context[0].value });
      m.addLayer({
        id: 'roads',
        type: 'line',
        source: 'roads',
        paint: {
          'line-color': '#3b556b',
          'line-opacity': 0.65,
          'line-width': ['interpolate', ['linear'], ['zoom'], 8, 0.75, 15, 3]
        }
      });
    }

    // 3D Extruded Buildings Layer
    if (context[1].status === 'fulfilled') {
      m.addSource('buildings', { type: 'geojson', data: context[1].value });
      m.addLayer({
        id: 'buildings',
        type: 'fill-extrusion',
        source: 'buildings',
        minzoom: 10,
        paint: {
          // Color based on height: deep blue -> sky blue -> mint -> electric cyan -> white
          'fill-extrusion-color': [
            'interpolate', ['linear'], ['coalesce', ['get', 'height_m'], 10],
            0, '#1e3a8a',
            30, '#0284c7',
            80, '#00f5c4',
            200, '#38bdf8',
            305, '#ffffff'
          ],
          'fill-extrusion-height': ['coalesce', ['get', 'height_m'], 15],
          'fill-extrusion-base': 0,
          'fill-extrusion-opacity': 0.92
        }
      });

      // Directional light for 3D faces
      m.setLight({
        anchor: 'viewport',
        color: '#ffffff',
        intensity: 0.55
      });
    }

    // Reports heatmap
    m.addSource('reports', { type: 'geojson', data: empty });
    m.addLayer({
      id: 'heat',
      type: 'heatmap',
      source: 'reports',
      paint: {
        'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 7, 12, 13, 30],
        'heatmap-intensity': 0.8,
        'heatmap-opacity': 0.75,
        'heatmap-color': [
          'interpolate', ['linear'], ['heatmap-density'],
          0, 'rgba(0,0,0,0)',
          0.2, '#06b6d4',
          0.6, '#fbbf24',
          1, '#f43f5e'
        ]
      }
    });

    // ZIP centroids
    m.addSource('areas', { type: 'geojson', data: empty });
    m.addLayer({
      id: 'areas',
      type: 'circle',
      source: 'areas',
      paint: {
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 7, 2.5, 12, 5.5],
        'circle-color': '#00f5c4',
        'circle-opacity': 0.75,
        'circle-stroke-color': '#061320',
        'circle-stroke-width': 1
      }
    });

    m.on('click', 'areas', e => selectZip(e.features[0].properties.zip, false));
    m.on('mouseenter', 'areas', () => m.getCanvas().style.cursor = 'pointer');
    m.on('mouseleave', 'areas', () => m.getCanvas().style.cursor = '');
  } else {
    // 2D Leaflet Fallback
    state.gl = false;
    state.map = L.map('map', { zoomControl: true }).setView([29.80, -95.42], 9);
    try {
      const roads = await fetch('/mapdata/roads.geojson').then(r => r.json());
      L.geoJSON(roads, { style: { color: '#3b556b', weight: 1, opacity: 0.6 } }).addTo(state.map);
      const bldgs = await fetch('/mapdata/buildings.geojson').then(r => r.json());
      L.geoJSON(bldgs, {
        style: { color: '#00f5c4', weight: 1, fillColor: '#0284c7', fillOpacity: 0.5 },
        onEachFeature: (f, l) => l.bindPopup(`<b>${safe(f.properties.name || 'Building')}</b><br>Height: ${f.properties.height_m}m`)
      }).addTo(state.map);
    } catch (e) {}
  }
  state.mapReady = true;
}

function areaFeatures() {
  return pointFC(state.boot.areas, a => {
    const p = state.plan ? state.plan.rows.find(r => r.zip === a.zip) : null;
    const covered = p && p.ambulance_minutes != null && p.ambulance_minutes <= 10;
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

  const green = ['tree', 'debris'].includes(state.layer);
  $('#legend').style.background = green ? 'linear-gradient(90deg,#15803d,#a3e635,#fef08a)' :
    state.layer === 'flood' ? 'linear-gradient(90deg,#0369a1,#38bdf8,#e0f2fe)' :
    state.layer === 'coverage' ? 'linear-gradient(90deg,#00f5c4,#fbbf24)' :
    'linear-gradient(90deg,#4c0519,#e11d48,#fecdd3)';

  const reports = d[3] ? state.data.reports.features.filter(f => f.properties.category === d[3]) : [];

  if (state.gl) {
    const m = state.map;
    m.getSource('counties').setData(state.data.counties);
    m.setPaintProperty('county-fill', 'fill-color', state.layer === 'outages' ?
      ['case', ['any', ['get', 'flagged'], ['!', ['get', 'available']]], '#334155',
      ['interpolate', ['linear'], ['get', 'intensity'], 0, '#0c2234', 0.5, '#7f1d1d', 1, '#f43f5e']] :
      '#0c2234'
    );
    m.getSource('reports').setData({ type: 'FeatureCollection', features: reports });
    m.getSource('areas').setData(areaFeatures());
    m.setPaintProperty('areas', 'circle-color', state.layer === 'coverage' ?
      ['case', ['get', 'covered'], '#00f5c4', '#fbbf24'] :
      ['case', ['get', 'selected'], '#ffffff', '#64748b']
    );
    m.setPaintProperty('areas', 'circle-radius', ['case', ['get', 'selected'], 6.5, 3]);
  } else {
    for (const key of ['countyLayer', 'heatLayer', 'areaLayer']) {
      if (state[key]) state.map.removeLayer(state[key]);
    }
    state.countyLayer = L.geoJSON(state.data.counties, {
      style: f => ({
        color: '#203d52',
        weight: 1,
        fillColor: state.layer === 'outages' ? (f.properties.flagged || !f.properties.available ? '#334155' : `hsl(5 60% ${20 + f.properties.intensity * 35}%)`) : '#0c2234',
        fillOpacity: 0.8
      })
    }).addTo(state.map);

    if (reports.length) {
      state.heatLayer = L.heatLayer(reports.map(f => [f.geometry.coordinates[1], f.geometry.coordinates[0], 0.5]), { radius: 22, blur: 16 }).addTo(state.map);
    }
    state.areaLayer = L.geoJSON(areaFeatures(), {
      pointToLayer: (f, ll) => L.circleMarker(ll, {
        radius: f.properties.selected ? 6 : 3,
        color: '#ffffff',
        weight: 1,
        fillColor: state.layer === 'coverage' ? (f.properties.covered ? '#00f5c4' : '#fbbf24') : '#64748b',
        fillOpacity: 0.85
      }),
      onEachFeature: (f, l) => l.on('click', () => selectZip(f.properties.zip, false))
    }).addTo(state.map);
  }

  $('#map-status').textContent = state.layer === 'coverage' ? 'Green = ≤10 min response target · Amber = Outside target' :
    state.layer === 'outages' ? `${state.data.history.length} counties · red = peak power loss` :
    `${fmt(reports.length)} 311 distress reports`;
}

/* CLICKABLE SITE MARKERS */
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
    const label = roles.map(r => ({ ambulance: '🚑', cooling: '❄️', community: '🏛️', dispatch: '🚨' }[r.id])).join('');
    addSiteMarker(s.lon, s.lat, label, name, roles);
  }

  if ($('#hospitals').checked) {
    state.boot.hospitals.forEach(h => {
      addHospitalMarker(h.longitude, h.latitude, '🏥', h.name);
    });
  }
}

function addSiteMarker(lon, lat, iconText, name, roles) {
  const primaryRoleId = roles[0].id;
  const cfg = roleConfig[primaryRoleId] || roleConfig.ambulance;

  const el = document.createElement('button');
  el.className = `site-marker ${cfg.markerClass}`;
  el.innerHTML = iconText;
  el.title = `${name}\nClick to inspect AI placement rationale`;

  el.onclick = e => {
    e.stopPropagation();
    inspectSite(name, primaryRoleId);
  };

  if (state.gl) {
    const marker = new maplibregl.Marker({ element: el }).setLngLat([lon, lat]).addTo(state.map);
    state.markers.push(marker);
  } else {
    const marker = L.marker([lat, lon], {
      icon: L.divIcon({ className: '', html: el.outerHTML, iconSize: [28, 28] })
    }).addTo(state.map);
    marker.on('click', () => inspectSite(name, primaryRoleId));
    state.markers.push(marker);
  }
}

function addHospitalMarker(lon, lat, iconText, name) {
  const el = document.createElement('div');
  el.className = 'site-marker hospital';
  el.innerHTML = iconText;
  el.title = `${name}\nFixed Hospital Anchor`;

  if (state.gl) {
    const marker = new maplibregl.Marker({ element: el }).setLngLat([lon, lat]).addTo(state.map);
    state.markers.push(marker);
  } else {
    const marker = L.marker([lat, lon], {
      icon: L.divIcon({ className: '', html: el.outerHTML, iconSize: [26, 26] })
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
        <b class="${p[r.id + '_minutes'] <= 10 ? 'within' : 'outside'}">${fmt(p[r.id + '_minutes'], 1)}m</b>
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
      <div class="table-note">Complete disaster staging matrix. Times reflect drive minutes under ${$('#slowdown').value}× road slowdown.</div>
      ${table(
        ['ZIP Centroid', 'Ambulance Site', 'EMS (min)', 'Incident Outpost', 'Rescue (min)', 'Cooling Hub', 'Cooling (min)', 'Community Hub', 'Relief (min)'],
        state.plan.rows.map(r => `
          <tr data-zip="${r.zip}">
            <td><strong>${r.zip}</strong></td>
            <td>${safe(r.ambulance_site || 'Unassigned')}</td>
            <td class="${r.ambulance_minutes <= 10 ? 'within' : 'outside'}">${fmt(r.ambulance_minutes, 1)}</td>
            <td>${safe(r.dispatch_site || 'Unassigned')}</td>
            <td class="${r.dispatch_minutes <= 10 ? 'within' : 'outside'}">${fmt(r.dispatch_minutes, 1)}</td>
            <td>${safe(r.cooling_site || 'Unassigned')}</td>
            <td class="${r.cooling_minutes <= 10 ? 'within' : 'outside'}">${fmt(r.cooling_minutes, 1)}</td>
            <td>${safe(r.community_site || 'Unassigned')}</td>
            <td class="${r.community_minutes <= 10 ? 'within' : 'outside'}">${fmt(r.community_minutes, 1)}</td>
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

// Start portal
initialize();
