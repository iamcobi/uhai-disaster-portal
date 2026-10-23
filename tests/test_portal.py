"""Integration checks against a running, loopback-only portal."""
import json,urllib.request,urllib.error,urllib.parse,io,zipfile,csv,sys,unittest
BASE=(sys.argv.pop(1) if len(sys.argv)>1 and sys.argv[1].startswith('http') else 'http://127.0.0.1:8765').rstrip('/')
def raw(path,method='GET',headers=None):
 with urllib.request.urlopen(urllib.request.Request(BASE+path,method=method,headers=headers or {}),timeout=100) as r:return r.read(),r.headers
def get(path):return json.loads(raw(path)[0])
class PortalTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.boot=get('/api/bootstrap');cls.plan=get('/api/plan')
 def test_01_dataset_counts_and_missing_values(self):
  self.assertEqual(len(self.boot['areas']),189);self.assertEqual(len(self.boot['sites']),14)
  self.assertEqual(sum(s['eligible'] for s in self.boot['sites']),12)
  self.assertEqual(self.boot['counts']['reports'],48318)
  self.assertEqual(self.boot['counts']['outage_observations'],273399)
  self.assertEqual(sum(a['estimated_members'] is not None for a in self.boot['areas']),151)
 def test_02_roles_and_targets(self):
  self.assertEqual(len(self.plan['rows']),189);eligible={s['name'] for s in self.boot['sites'] if s['eligible']}
  for role,budget in zip(self.plan['roles'],[2,2,3,3]):
   self.assertEqual(len(role['sites']),budget);self.assertTrue(set(role['sites'])<=eligible)
   self.assertTrue(0<=role['coverage']<=100)
  for row in self.plan['rows']:
   for role in self.plan['roles']:self.assertGreaterEqual(row[role['id']+'_minutes'],0)
 def test_03_closed_site_is_never_selected(self):
  closed=self.plan['roles'][0]['sites'][0];p=get('/api/plan?'+urllib.parse.urlencode({'closed':closed}))
  self.assertTrue(all(closed not in r['sites'] for r in p['roles']))
 def test_04_slowdown_does_not_improve_optimal_coverage(self):
  slower=get('/api/plan?slowdown=2')
  for a,b in zip(self.plan['roles'],slower['roles']):self.assertLessEqual(b['coverage'],a['coverage']+1e-8)
 def test_05_storms_and_quality_flags(self):
  for storm in ['Beryl','Derecho','Harvey']:
   s=get('/api/storm?storm='+storm);self.assertEqual(len(s['counties']['features']),9)
   self.assertGreater(len(s['reports']['features']),0);self.assertGreater(len(s['evidence']),0)
   self.assertEqual(sum(s['counts'].values()),len(s['reports']['features']))
   if storm=='Derecho':
    flagged=[f for f in s['counties']['features'] if f['properties']['flagged']]
    self.assertGreaterEqual(len(flagged),2)
    self.assertTrue(all(f['properties']['intensity']==-1 for f in flagged))
 def test_06_supply_assumptions_and_unknowns(self):
  p=get('/api/supplies?cooling_pct=0&community_pct=50&health_pct=100&days=2')
  self.assertEqual(p['matched_areas'],151);self.assertEqual(len(p['rows']),189)
  for r in p['rows']:
   if r['ML flood-household members (scenario)'] is None:self.assertIsNone(r['Cooling visitors (assumed)'])
   else:
    self.assertEqual(r['Cooling visitors (assumed)'],0)
    self.assertEqual(r['Community meals (3/person/day assumption)'],r['Community visitors (assumed)']*6)
 def test_07_export_complete(self):
  b,h=raw('/api/export?storm=Derecho')
  with zipfile.ZipFile(io.BytesIO(b)) as z:
   self.assertTrue({'placements.csv','selected_sites.csv','county_outage_peaks.csv','damage_evidence.csv','assumptions.json','people_model_report.json','SOURCES.md'}<=set(z.namelist()))
   self.assertEqual(len(list(csv.DictReader(io.StringIO(z.read('placements.csv').decode())))),189)
   self.assertEqual(json.loads(z.read('assumptions.json'))['response_target'],'10 modeled minutes base to area')
 def test_08_invalid_inputs_and_cross_origin_rejected(self):
  for path in ['/api/plan?storm=Fake','/api/plan?ambulances=0','/api/plan?slowdown=nan','/api/supplies?days=0','/api/docs?name=../../app.py']:
   with self.assertRaises(urllib.error.HTTPError) as e:raw(path)
   self.assertEqual(e.exception.code,400)
  with self.assertRaises(urllib.error.HTTPError) as e:raw('/api/train','POST',{'Origin':'https://example.com'})
  self.assertEqual(e.exception.code,403)
 def test_09_local_assets_and_documents(self):
  for p in ['/','/app.js','/app.css','/vendor/maplibre-gl.js','/vendor/leaflet.js','/vendor/manrope-400.woff2','/mapdata/buildings.geojson','/mapdata/roads.geojson']:
   self.assertGreater(len(raw(p)[0]),20)
  for name in ['sources','model','presentation','map']:self.assertGreater(len(get('/api/docs?name='+name)['text']),50)
  html=raw('/')[0].decode();self.assertNotIn('https://',html)
 def test_10_model_report_and_stale_utility(self):
  m=self.boot['model'];self.assertEqual(m['test_zip_codes'],38);self.assertLess(m['mae_reduction_percent'],1)
  u=get('/api/utility');self.assertTrue(u['latest']);self.assertGreater(len(u['rows']),0)
  self.assertEqual(get('/api/health')['local_only'],True)
if __name__=='__main__':unittest.main(verbosity=2)
