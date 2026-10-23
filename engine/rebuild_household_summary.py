"""Optional network rebuild of the frozen FEMA summary. Not needed to run the demo. May take several minutes. Verifies the original source count; stops if the source changed."""
import urllib.request,urllib.parse,json,concurrent.futures,collections,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'data';CACHE=ROOT/'rebuild_cache';CACHE.mkdir(exist_ok=True)
BASE='https://www.fema.gov/api/open/v1/IndividualAssistanceHousingRegistrantsLargeDisasters'
FILTER="disasterNumber eq 4332 and censusBlockId ge '482010000000000' and censusBlockId lt '482020000000000'"
TOTAL=449932;PAGE=10000
fields='id,damagedZipCode,householdComposition,ownRent,floodDamage,specialNeeds,inspected,rpfvl,censusYear'
def fetch(skip):
 p=CACHE/f'{skip:06}.json'
 if p.exists():return json.loads(p.read_text(encoding='utf-8'))
 params={'$filter':FILTER,'$select':fields,'$top':PAGE,'$skip':skip,'$orderby':'id','\u0024inlinecount':'allpages'}
 u=BASE+'?'+urllib.parse.urlencode(params)
 for attempt in range(5):
  try:
   time.sleep(1.2);raw=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'CodeCoogs-Hurricane-Hackathon-Prototype/0.1'}),timeout=50).read();d=json.loads(raw)
   if d['metadata']['count']!=TOTAL:raise ValueError('Count changed; restart with refreshed count')
   rows=d['IndividualAssistanceHousingRegistrantsLargeDisasters'];p.write_text(json.dumps(rows));return rows
  except Exception:
   if attempt==4:raise
   time.sleep(12 * (attempt+1))
agg={};seen=set();distribution=collections.Counter();n=0
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
 for rows in ex.map(fetch,range(0,TOTAL,PAGE)):
  for r in rows:
   if r['id'] in seen:raise ValueError('Duplicate registration id across pages')
   seen.add(r['id']);z=str(r['damagedZipCode']).zfill(5)
   a=agg.setdefault(z,collections.Counter());a['registration_records']+=1
   size=r.get('householdComposition');distribution[str(size)]+=1
   valid=isinstance(size,(int,float)) and 1<=size<=50
   if valid:a['reported_household_members_sum']+=int(size)
   else:a['records_missing_or_invalid_household_size']+=1
   if r.get('floodDamage') is True:
    a['flood_damage_registration_records']+=1
    if valid:a['members_in_flood_damage_records_sum']+=int(size)
   if r.get('specialNeeds') is True:
    a['special_needs_registration_records']+=1
    if valid:a['members_in_special_needs_households_sum']+=int(size)
   if r.get('inspected') is True:a['inspected_registration_records']+=1
   if r.get('rpfvl') is not None and r['rpfvl']>0:a['positive_real_property_loss_records']+=1
   a['renter_records' if r.get('ownRent')=='Renter' else 'owner_or_other_records']+=1
  n+=len(rows)
  if n%50000==0 or n==TOTAL:print('Processed',n,'of',TOTAL,flush=True)
assert len(seen)==TOTAL
keys=['registration_records','reported_household_members_sum','records_missing_or_invalid_household_size','flood_damage_registration_records','members_in_flood_damage_records_sum','special_needs_registration_records','members_in_special_needs_households_sum','inspected_registration_records','positive_real_property_loss_records','renter_records','owner_or_other_records']
rows=[{'zipCode':z,**{k:int(c[k]) for k in keys}} for z,c in sorted(agg.items())]
out={'source_url':BASE,'filter':FILTER,'select':fields,'retrieved_date':'2026-10-23','source_records':TOTAL,'unique_record_ids':len(seen),'household_size_distribution':dict(distribution),'notes':['Aggregated public registration records, not verified unique persons.','Reported household members are summed within registration records; people may be underrepresented or duplicated across registrations.','Missing or invalid household sizes are not imputed.','Flood-damage records are a cleanup-priority indicator, not labeled cleanup requests.','specialNeeds applies to a household and does not count injured individuals.','County selected from geocoded census block prefix 48201; records with missing or miscoded census blocks are excluded.'],'rows':rows}
(OUT/'harvey_harris_household_summary.json').write_text(json.dumps(out,indent=2));print(json.dumps({'zip_codes':len(rows),'size_distribution':dict(distribution),'totals':{k:sum(r[k] for r in rows) for k in keys}}),flush=True)

