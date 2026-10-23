"""UHAI Portal: laptop-local HTTP service. No Colab or map keys required."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
from functools import lru_cache
import argparse,csv,gzip,io,json,math,sys,threading,subprocess,zipfile,webbrowser,time,logging
ROOT=Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s',handlers=[logging.FileHandler(ROOT/'portal.log',encoding='utf-8'),logging.StreamHandler()])
sys.path.insert(0,str(ROOT/'engine'))
import numpy as np
import storm_layers as engine
import explainability
ROLE_IDS={'Ambulance staging':'ambulance','Repair dispatch':'dispatch','Cooling hubs':'cooling','Community/medical posts':'community'}
LOCK=threading.Lock()
def clean(x):
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,np.generic):return clean(x.item())
 if isinstance(x,float) and not math.isfinite(x):return None
 return x

def records(frame):return json.loads(frame.to_json(orient='records'))
def value(r,key):
 v=r.get(key);return None if v is None or isinstance(v,float) and not math.isfinite(v) else v

@lru_cache(maxsize=1)
def bootstrap():
 h=engine.load_hazards();areas=[]
 for z,r in h['areas'].iterrows():
  areas.append({'zip':z,'lat':r.latitude,'lon':r.longitude,'population':value(r,'population_2020'),'medical':value(r,'Power_Dependent_Devices_DME'),'historical_members':value(r,'reported_household_members_sum'),'estimated_members':value(r,'model_estimated_flood_household_members_sum'),'flood_records':value(r,'flood_damage_registration_records'),'county':value(r,'representative_county_fips')})
 sites=[]
 for name,r in h['base']['sites'].iterrows():sites.append({'name':name,'lat':r.latitude,'lon':r.longitude,'eligible':name in h['base']['eligible'],'flood_zone':h['base']['checks'].loc[name,'flood_zone']})
 report=json.loads((ROOT/'engine/people_model_report.json').read_text(encoding='utf-8'))
 return clean({'app':'UHAI Portal','storms':[{'name':k,'start':v[0],'end':v[1]} for k,v in engine.STORMS.items()],'areas':areas,'sites':sites,'hospitals':h['base']['facilities']['hospital_examples'],'model':report,'counts':{'areas':len(areas),'sites':len(sites),'reports':len(h['reports']),'outage_observations':len(h['outages']),'damage_descriptions':len(h['evidence'])},'roles':ROLE_IDS})

@lru_cache(maxsize=3)
def storm_data(storm):
 h=engine.load_hazards();s=h['reports'][h['reports'].storm==storm];history=engine.outage_history(storm);lookup=history.set_index('fips_code').to_dict('index');geo=json.loads(json.dumps(h['counties']));peaks=[]
 for f in geo['features']:
  r=lookup.get(f['properties']['GEOID']);f['properties'].update(clean(r or {}));f['properties']['available']=bool(r);f['properties']['flagged']=bool(r and r['exceeds_supplied_customer_denominator'])
  if r and not r['exceeds_supplied_customer_denominator']:peaks.append(r['peak_customers_out'])
 maximum=max(peaks,default=1)
 for f in geo['features']:
  p=f['properties'];p['intensity']=math.log1p(p.get('peak_customers_out',0))/math.log1p(maximum) if p['available'] and not p['flagged'] else -1
 features=[]
 for r in records(s[['latitude','longitude','date','service_type','category']]):
  features.append({'type':'Feature','geometry':{'type':'Point','coordinates':[r['longitude'],r['latitude']]},'properties':{k:r[k] for k in ['date','service_type','category']}})
 evidence=records(h['evidence'][h['evidence'].storm==storm])
 return {'reports':{'type':'FeatureCollection','features':features},'counties':geo,'history':records(history),'evidence':evidence,'counts':s.category.value_counts().to_dict(),'window':engine.STORMS[storm]}

def options(q):
 def get(k,d):return q.get(k,[str(d)])[0]
 storm=get('storm','Beryl')
 if storm not in engine.STORMS:raise ValueError('Choose one of the supplied storm windows.')
 counts={k:int(get(k,d)) for k,d in [('ambulances',2),('dispatch',2),('cooling',3),('community',3)]}
 if any(v<1 for v in counts.values()):raise ValueError('Choose at least one site for each role.')
 slowdown=float(get('slowdown',1))
 if not 1<=slowdown<=2:raise ValueError('Slowdown must be between one and two.')
 closed=get('closed','None')
 if closed not in ['None']+engine.load_hazards()['base']['eligible']:raise ValueError('Unknown candidate site.')
 return {'storm':storm,**counts,'slowdown':slowdown,'closed':closed}

@lru_cache(maxsize=64)
def plan_cached(storm,ambulances,dispatch,cooling,community,slowdown,closed):return engine.choose_resources(storm,ambulances,dispatch,cooling,community,slowdown,closed)
def plan_payload(plan):
 rows=[]
 for z,r in plan['table'].iterrows():
  x={'zip':z,'tree':r['Tree removal report count (nearest-point grouping)'],'debris':r['Storm debris report count (nearest-point grouping)'],'electrical':r['Electrical hazard report count (nearest-point grouping)'],'flood':r['Flood/drainage report count (nearest-point grouping)'],'county_peak':r['County peak reported customers out']}
  for role,id in ROLE_IDS.items():x[id+'_site']=r.get(role+' site');x[id+'_minutes']=r.get(role+' drive (min)')
  rows.append(x)
 roles=[{'id':ROLE_IDS[r['Role']],'name':r['Role'],'sites':plan['choices'][r['Role']],'coverage':r['10-min coverage of role weight (%)']} for r in plan['role_summary'].to_dict('records')]
 explanations=explainability.generate_plan_explanations(plan)
 return clean({'rows':rows,'roles':roles,'storm':plan['storm'],'assumptions':plan['assumptions'],'explanations':explanations})

class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT/'web'),**kw)
 def log_message(self,fmt,*args):logging.info(fmt,*args)
 def send_bytes(self,raw,mime='application/json; charset=utf-8',status=200,filename=None):
  self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store' if mime.startswith('application/json') else 'no-cache');self.send_header('X-Content-Type-Options','nosniff')
  if filename:self.send_header('Content-Disposition','attachment; filename="'+filename+'"')
  if len(raw)>2000 and 'gzip' in self.headers.get('Accept-Encoding',''):
   raw=gzip.compress(raw,compresslevel=3);self.send_header('Content-Encoding','gzip');self.send_header('Vary','Accept-Encoding')
  self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def send_json(self,data,status=200):self.send_bytes(json.dumps(clean(data),ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8'),status=status)
 def do_GET(self):
  u=urlparse(self.path);q=parse_qs(u.query)
  try:
   if u.path=='/api/health':return self.send_json({'app':'UHAI Portal','status':'ready','local_only':True})
   if u.path=='/api/bootstrap':return self.send_json(bootstrap())
   if u.path=='/api/storm':
    storm=q.get('storm',['Beryl'])[0]
    if storm not in engine.STORMS:raise ValueError('Unknown storm.')
    return self.send_json(storm_data(storm))
   if u.path=='/api/plan':return self.send_json(plan_payload(plan_cached(**options(q))))
   if u.path=='/api/explain':
    site=q.get('site',['West End Multi-Service Center'])[0]
    role=q.get('role',['ambulance'])[0]
    p=plan_cached(**options(q))
    role_map_rev={'ambulance':'Ambulance staging','dispatch':'Repair dispatch','cooling':'Cooling hubs','community':'Community/medical posts'}
    role_name=role_map_rev.get(role,'Ambulance staging')
    exp=explainability.build_site_explanation(site,role_name,role,site in p['choices'].get(role_name,[]),p['table'],p['storm'],float(q.get('slowdown',[1.0])[0]))
    return self.send_json(exp)
   if u.path=='/api/utility':return self.send_json(engine.load_utility())
   if u.path=='/api/supplies':
    pct={k:int(q.get(k,[str(d)])[0]) for k,d in [('cooling_pct',30),('community_pct',50),('health_pct',10),('days',3)]}
    if any(not 0<=pct[k]<=100 for k in ['cooling_pct','community_pct','health_pct']) or not 1<=pct['days']<=14:raise ValueError('Participation must be 0–100% and supply days 1–14.')
    p=engine.core.build_plan(**pct);t=p['table'];return self.send_json({'rows':records(t.rename_axis('zip').reset_index()),'assumptions':p['assumptions'],'matched_areas':p['matched_model_areas']})
   if u.path=='/api/docs':
    names={'sources':ROOT/'engine/data/STORM_LAYER_SOURCES.md','model':ROOT/'engine/data/SOURCES.md','presentation':ROOT/'docs/PRESENTATION.md','map':ROOT/'docs/MAP_SOURCES.md'}
    p=names.get(q.get('name',['sources'])[0])
    if p is None:raise ValueError('Unknown document.')
    return self.send_json({'text':p.read_text(encoding='utf-8-sig')})
   if u.path=='/api/export':
    p=plan_cached(**options(q));b=io.BytesIO()
    with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
     z.writestr('placements.csv',p['table'].round(2).to_csv());z.writestr('selected_sites.csv',p['role_summary'].round(2).to_csv(index=False));z.writestr('county_outage_peaks.csv',p['history'].to_csv(index=False));z.writestr('damage_evidence.csv',p['evidence'][p['evidence'].storm==p['storm']].to_csv(index=False));z.writestr('assumptions.json',json.dumps(clean(p['assumptions']),indent=2));z.write(ROOT/'engine/people_model_report.json','people_model_report.json');z.write(ROOT/'engine/data/STORM_LAYER_SOURCES.md','SOURCES.md')
    return self.send_bytes(b.getvalue(),'application/zip',filename='UHAI-'+p['storm']+'-scenario.zip')
   if u.path.startswith('/api/'):return self.send_json({'error':'Unknown endpoint'},404)
   target=(ROOT/'web'/u.path.lstrip('/')).resolve()
   if not target.is_relative_to((ROOT/'web').resolve()):return self.send_json({'error':'Invalid file path'},403)
   return super().do_GET()
  except (ValueError,KeyError) as e:return self.send_json({'error':str(e)},400)
  except Exception as e:
   logging.exception('REQUEST ERROR');return self.send_json({'error':'The local calculation failed. Check portal.log and retry.'},500)
 def do_POST(self):
  origin=self.headers.get('Origin');allowed='http://'+self.headers.get('Host','')
  if origin and origin!=allowed:return self.send_json({'error':'Local requests only'},403)
  path=urlparse(self.path).path
  if path=='/api/stop':
   self.send_json({'message':'UHAI Portal stopped. Run START_PORTAL.cmd to reopen.'})
   threading.Thread(target=self.server.shutdown,daemon=True).start();return
  if path=='/api/refresh':return self.send_json(engine.load_utility(refresh=True))
  if path=='/api/train':
   if not LOCK.acquire(blocking=False):return self.send_json({'error':'Training is already running.'},409)
   try:
    r=subprocess.run([sys.executable,str(ROOT/'engine/train_people_model.py')],cwd=ROOT/'engine',capture_output=True,text=True,timeout=90)
    if r.returncode:raise RuntimeError(r.stderr[-600:])
    bootstrap.cache_clear();engine.load_hazards.cache_clear();plan_cached.cache_clear()
    return self.send_json(bootstrap()['model'])
   except Exception as e:return self.send_json({'error':'Training failed: '+str(e)},500)
   finally:LOCK.release()
  return self.send_json({'error':'Unknown action'},404)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);parser.add_argument('--no-browser',action='store_true');args=parser.parse_args()
 if not args.no_browser and (ROOT/'.portal-state.json').exists():
  try:
   from urllib.request import urlopen
   saved=json.loads((ROOT/'.portal-state.json').read_text(encoding='utf-8'));port=int(saved['port'])
   if not 1024<=port<=65535:raise ValueError('Invalid saved port')
   url=f'http://127.0.0.1:{port}/'
   with urlopen(url+'api/health',timeout=1) as response:ready=json.load(response)
   if ready.get('app')=='UHAI Portal':webbrowser.open(url);return
  except Exception:pass
 print('Preparing cached storm datasets...',flush=True);bootstrap()
 for port in range(args.port,args.port+10):
  try:server=ThreadingHTTPServer(('127.0.0.1',port),Handler);break
  except OSError:
   if port==args.port+9:raise
 url=f'http://127.0.0.1:{port}/';(ROOT/'.portal-state.json').write_text(json.dumps({'port':port,'pid':__import__('os').getpid(),'url':url}),encoding='utf-8');print('UHAI Portal ready: '+url,flush=True)
 if not args.no_browser:threading.Timer(.5,lambda:webbrowser.open(url)).start()
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
if __name__=='__main__':main()
