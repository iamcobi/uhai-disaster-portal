# Locally bundled map context

MapLibre GL JS 5.6.2 (BSD), Leaflet 1.9.4 (BSD), Leaflet.heat 0.2.0 (BSD) and Manrope (OFL) are bundled in web/vendor with licenses. No Google services or map keys are needed.

A small downtown Houston building-footprint subset was retrieved from OpenStreetMap via the public Overpass API on 2026-10-23. The region is not a complete street or building inventory. Attempts to cache regional/downtown roads timed out; the roads GeoJSON is an empty placeholder. The rendered map uses county boundaries, real report points, ZIP planning points and 1,135 downtown building footprints. Data © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright . Queries and bounding boxes are in the collection script. MapLibre renders these local GeoJSON snapshots without external map tiles. Building heights use OSM height tags where supplied, otherwise approximate levels × 3.2 m or a 6.4 m default. These are geographic illustrations, not surveyed heights, damaged structures, flood depths or failure predictions. The 3D view focuses on the cached downtown area.

The free public OpenFreeMap style was investigated, but returned HTTP 403 from this environment; it is not required by this app. County boundaries and all scenario layers are cached as well. The only optional live network action in the app is the manually requested utility refresh.
