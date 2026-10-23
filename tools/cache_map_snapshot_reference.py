import urllib.request,urllib.parse,json,concurrent.futures
from pathlib import Path
V=Path('outputs/UHAI Portal/web/vendor');M=Path('outputs/UHAI Portal/web/mapdata');M.mkdir(exist_ok=True)
urls={
'maplibre-gl.js':'https://cdn.jsdelivr.net/npm/maplibre-gl@5.6.2/dist/maplibre-gl.js',
'maplibre-gl.css':'https://cdn.jsdelivr.net/npm/maplibre-gl@5.6.2/dist/maplibre-gl.css',
'MAPLIBRE-LICENSE.txt':'https://cdn.jsdelivr.net/npm/maplibre-gl@5.6.2/LICENSE.txt',
}
for n,u in urls.items():
 raw=urllib.request.urlopen(u,timeout=35).read();(V/n).write_bytes(raw);print(n,len(raw),flush=True)
queries={
 'roads':'[out:json][timeout:50];way["highway"~"^(motorway|trunk|primary)$"](29.4,-96.1,30.4,-94.8);out tags geom;',
 'buildings':'[out:json][timeout:40];way["building"](29.748,-95.379,29.768,-95.354);out tags geom;'
}
def get(kv):
 name,q=kv
 for endpoint in ['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter']:
  try:
   raw=urllib.request.urlopen(urllib.request.Request(endpoint+'?'+urllib.parse.urlencode({'data':q}),headers={'User-Agent':'UHAI-Portal-Hackathon/1.0'}),timeout=65).read();d=json.loads(raw);features=[]
   import re
   for e in d.get('elements',[]):
    points=[[p['lon'],p['lat']] for p in e.get('geometry',[])];tags=e.get('tags',{})
    if len(points)<2:continue
    props={'name':tags.get('name',''),'kind':tags.get('highway','building')}
    if name=='buildings':
     if len(points)<4 or points[0]!=points[-1]:continue
     height=tags.get('height','');m=re.search(r'\d+(?:\.\d+)?',height)
     if m:meters=float(m.group());estimated=False
     else:
      try:meters=float(tags.get('building:levels',2))*3.2
      except ValueError:meters=6.4
      estimated=True
     props.update(height_m=min(350,max(3,meters)),height_estimated=estimated)
    geom={'type':'Polygon','coordinates':[points]} if name=='buildings' else {'type':'LineString','coordinates':points}
    features.append({'type':'Feature','geometry':geom,'properties':props})
   (M/(name+'.geojson')).write_text(json.dumps({'type':'FeatureCollection','features':features},separators=(',',':')),encoding='utf-8');return name,len(features)
  except Exception as e:last=str(e)
 return name,last
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
 for r in ex.map(get,queries.items()):print(r,flush=True)
Path('outputs/UHAI Portal/docs/MAP_SOURCES.md').write_text('''# Locally bundled map context

MapLibre GL JS 5.6.2 (BSD), Leaflet 1.9.4 (BSD), Leaflet.heat 0.2.0 (BSD) and Manrope (OFL) are bundled in web/vendor with licenses. No Google services or map keys are needed.

Major roads and a small downtown Houston building-footprint subset were retrieved from OpenStreetMap via the public Overpass API on 2026-10-23. The full region is not a complete street or building inventory. Data © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright . Queries and bounding boxes are in the collection script. MapLibre renders these local GeoJSON snapshots without external map tiles. Building heights use OSM height tags where supplied, otherwise approximate levels × 3.2 m or a 6.4 m default. These are geographic illustrations, not surveyed heights, damaged structures, flood depths or failure predictions. The 3D view focuses on the cached downtown area.

The free public OpenFreeMap style was investigated, but returned HTTP 403 from this environment; it is not required by this app. County boundaries and all scenario layers are cached as well. The only optional live network action in the app is the manually requested utility refresh.
''',encoding='utf-8')
