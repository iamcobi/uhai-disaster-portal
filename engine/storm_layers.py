"""Historical storm layers and independent resource siting, without fabricated probabilities."""
import json,math,re,urllib.request,gzip
from pathlib import Path
from datetime import datetime,timezone
from functools import lru_cache
import numpy as np
import pandas as pd
import expanded_planner as core
ROOT=Path(__file__).resolve().parent
STORMS={'Beryl':('2024-07-08','2024-08-01'),'Derecho':('2024-05-16','2024-06-07'),'Harvey':('2017-08-25','2017-09-15')}
UTILITY_URL='https://centerpoint.datacapable.com/datacapable/v2/p/centerpoint/map/events'
LAYERS=['Tree removal reports (green-yellow)','Storm debris reports (green-yellow)','Recorded power outages (red counties)','Electrical hazard reports (red)','Flood/drainage reports (blue)','Building safety/code reports (purple)','Utility report snapshot (check dates)','Cleanup help requests (Harvey only)','Medical evacuation requests (Harvey only)','Ambulance drive coverage','Future outage/tree probability — unavailable']
CATEGORIES={'Tree removal reports (green-yellow)':'Tree removal reports','Storm debris reports (green-yellow)':'Storm debris reports','Electrical hazard reports (red)':'Electrical hazard reports','Flood/drainage reports (blue)':'Flood/drainage reports','Building safety/code reports (purple)':'Building safety/code reports','Cleanup help requests (Harvey only)':'Cleanup help requests','Medical evacuation requests (Harvey only)':'Medical evacuation requests'}

def contains_ring(lon,lat,ring):
    inside=False
    for i in range(len(ring)):
        x1,y1=ring[i-1][:2];x2,y2=ring[i][:2]
        if (y1>lat)!=(y2>lat) and lon<(x2-x1)*(lat-y1)/(y2-y1)+x1:inside=not inside
    return inside

def contains(geom,lon,lat):
    polygons=[geom['coordinates']] if geom['type']=='Polygon' else geom['coordinates']
    return any(contains_ring(lon,lat,p[0]) and not any(contains_ring(lon,lat,h) for h in p[1:]) for p in polygons)

@lru_cache(maxsize=1)
def load_hazards():
    base=core.load_inputs();geo=json.loads((ROOT/'data/regional_counties.geojson').read_text(encoding='utf-8'));reports=[]
    for year in ['Harvey','2024']:
        p=ROOT/f'data/311_{year}_relevant.json'
        if p.exists():reports.extend(json.loads(p.read_text(encoding='utf-8'))['rows'])
    extra=ROOT/'data/311_Harvey_additional_requests.json'
    if extra.exists():reports.extend(json.loads(extra.read_text(encoding='utf-8'))['rows'])
    f=pd.DataFrame(reports)
    def category(r):
        t=''.join(c for c in r['service_type'].lower() if c.isalnum())
        if 'treeremoval' in t:return 'Tree removal reports'
        if 'tree' in t:return 'Other tree maintenance requests'
        if 'building' in t:return 'Excluded non-structural complaint' if 'breakin' in t else 'Building safety/code reports'
        return r['category']
    f['category']=f.apply(category,axis=1)
    # Reports keep their actual map points. Only the placement calculation groups them
    # by nearest representative point, explicitly not by true postal-ZIP membership.
    a=base['areas'];xy=a[['latitude','longitude']].to_numpy();pts=f[['latitude','longitude']].to_numpy();assigned=[]
    for start in range(0,len(pts),1000):
        p=pts[start:start+1000];dist=((p[:,None,:]-xy[None,:,:])*np.array([111,96]))**2
        assigned.extend(np.argmin(dist.sum(axis=2),axis=1).tolist())
    f['planning_area']=[a.index[i] for i in assigned]
    county=[]
    for code,r in a.iterrows():county.append(next((x['properties']['GEOID'] for x in geo['features'] if contains(x['geometry'],r.longitude,r.latitude)),None))
    a=a.copy();a['representative_county_fips']=county
    native=[]
    for name in ['regional_raw_outages_2024.csv','regional_raw_outages_harvey.csv']:
        p=ROOT/'data'/name
        if p.exists():
            d=pd.read_csv(p,dtype={'fips_code':str});d['fips_code']=d.fips_code.str.zfill(5);native.append(d)
    outages=pd.concat(native,ignore_index=True) if native else pd.DataFrame()
    evidence=json.loads((ROOT/'data/damage_evidence.json').read_text(encoding='utf-8'))['rows']
    return {'base':base,'areas':a,'reports':f,'counties':geo,'outages':outages,'evidence':pd.DataFrame(evidence)}

def outage_history(storm):
    h=load_hazards();start,end=STORMS[storm];f=h['outages'];columns=['fips_code','county','peak_customers_out','peak_time_UTC','recorded_intervals','source_record_availability_pct','total_customers_at_peak','exceeds_supplied_customer_denominator']
    if f.empty:return pd.DataFrame(columns=columns)
    f=f[(f.run_start_time>=start)&(f.run_start_time<end)].copy();rows=[]
    expected=int((pd.Timestamp(end)-pd.Timestamp(start)).total_seconds()/900)
    for code,g in f.groupby('fips_code'):
        # Unique source county/time rows, not sums of repeated outage snapshots.
        if g.run_start_time.duplicated().any():raise ValueError('Duplicate source county/timestamp records')
        peak=g.loc[g.customers_out.idxmax()]
        denominator=float(peak.get('total_customers',np.nan))
        inconsistent=bool(np.isfinite(denominator) and denominator>0 and peak.customers_out>denominator)
        rows.append({'fips_code':code,'county':peak['county'],'peak_customers_out':float(peak.customers_out),'peak_time_UTC':peak.run_start_time,'recorded_intervals':len(g),'source_record_availability_pct':100*len(g)/expected,'total_customers_at_peak':denominator,'exceeds_supplied_customer_denominator':inconsistent})
    return pd.DataFrame(rows,columns=columns)

def choose_resources(storm='Beryl',ambulances=2,dispatch=2,cooling=3,community=3,slowdown=1.0,closed='None'):
    h=load_hazards();b=h['base'];a=h['areas'].copy();r=b['routes'];s=h['reports'];s=s[s.storm==storm]
    if slowdown<1:raise ValueError('Travel slowdown must be at least one.')
    grouped=s.groupby(['planning_area','category']).size().unstack(fill_value=0).reindex(a.index,fill_value=0)
    def count(category):return grouped[category].astype(float) if category in grouped else pd.Series(0.0,index=a.index)
    tree=count('Tree removal reports');debris=count('Storm debris reports');electrical=count('Electrical hazard reports');flood=count('Flood/drainage reports')
    a['Tree removal report count (nearest-point grouping)']=tree
    a['Storm debris report count (nearest-point grouping)']=debris
    a['Electrical hazard report count (nearest-point grouping)']=electrical
    a['Flood/drainage report count (nearest-point grouping)']=flood
    history=outage_history(storm);outage_lookup=history.set_index('fips_code').peak_customers_out.to_dict() if len(history) else {}
    a['County peak reported customers out']=a.representative_county_fips.map(outage_lookup)
    # All cross-source priority combinations are explicit planning proxies, not learned
    # outage likelihoods or estimates of actual service users.
    med=a.Power_Dependent_Devices_DME.fillna(0).astype(float)
    ranks=a['County peak reported customers out'];valid=ranks.notna()
    trustworthy=history[~history.exceeds_supplied_customer_denominator] if len(history) else history
    county_ranks=trustworthy.set_index('fips_code').peak_customers_out.rank(pct=True).to_dict() if len(trustworthy) else {}
    outage_rank=a.representative_county_fips.map(county_ranks).fillna(0)
    cooling_w=med*outage_rank
    weights={
        'Ambulance staging':med,
        'Repair dispatch':tree+debris+electrical,
        'Cooling hubs':cooling_w,
        'Community/medical posts':a.reported_household_members_sum.fillna(0).astype(float),
    }
    counts={'Ambulance staging':ambulances,'Repair dispatch':dispatch,'Cooling hubs':cooling,'Community/medical posts':community}
    available=[n for n in b['eligible'] if n!=closed];pos=[r['site_names'].index(n) for n in available]
    outbound=np.asarray(r['base_to_area_minutes'],float)[pos]*float(slowdown)
    inbound=np.asarray(r['area_to_hub_minutes'],float)[:,pos].T*float(slowdown)
    table=a[['population_2020','Power_Dependent_Devices_DME','representative_county_fips','County peak reported customers out','Tree removal report count (nearest-point grouping)','Storm debris report count (nearest-point grouping)','Electrical hazard report count (nearest-point grouping)','Flood/drainage report count (nearest-point grouping)']].copy();choices={};summary=[]
    for role,w in weights.items():
        matrix=outbound if role in ['Ambulance staging','Repair dispatch'] else inbound
        b = min(int(counts[role]), len(available))
        ids,score=core.optimize(matrix,w.to_numpy(float),b,target=15);names=[available[i] for i in ids];choices[role]=names;m=matrix[ids];near=m.min(axis=0)
        table[role+' site']=[names[i] for i in m.argmin(axis=0)];table[role+' drive (min)']=near
        summary.append({'Role':role,'Selected candidates':', '.join(names),'10-min coverage of role weight (%)':100*score[0]/w.sum()})
    table.index.name='Planning ZIP point'
    return {**h,'areas':a,'table':table,'choices':choices,'role_summary':pd.DataFrame(summary),'storm':storm,'reports_selected':s,'history':history,'closed':closed,'weights':weights,'assumptions':{'storm_window_dates_end_exclusive':STORMS[storm],'ambulance_weight':'Published HHS electricity-dependent Medicare count; not injury or dispatch demand','repair_weight':'Historical tree removal + storm debris + electrical hazard report counts assigned to nearest representative point, not actual utility faults','cooling_weight':'Published HHS count multiplied by percentile rank of county historical peak outage customer count; a proxy, not persons affected or outage probability','community_weight':'Harvey reported household-member sums; a fixed historical context layer, not selected-storm outcomes','response_target':'10 modeled minutes base to area','hub_target':'10 modeled minutes area to hub, an additional illustrative objective','slowdown':float(slowdown),'capacity':'Unverified. Selected roles may co-locate without shared capacity accounting.'}}

def normalize_utility(raw):
    if not isinstance(raw,list):raise ValueError('Utility feed returned an unexpected format.')
    rows=[]
    for r in raw:
        if not isinstance(r,dict):continue
        try:lat=float(r['latitude']);lon=float(r['longitude']);stamp=float(r['lastUpdatedTime'])
        except (TypeError,ValueError,KeyError):continue
        if not (28<=lat<=32 and -98<=lon<=-93):continue
        props={x.get('property'):x.get('value') for x in r.get('additionalProperties',[]) if isinstance(x,dict)}
        rows.append({k:r.get(k) for k in ['id','startTime','lastUpdatedTime','etrTime','numPeople','status','latitude','longitude','cause']} | {'reported_zips':props.get('AREA_ZIP',r.get('reported_zips',[])),'reported_counties':props.get('AREA_COUNTY',r.get('reported_counties',[]))})
    return rows

def load_utility(refresh=False):
    p=ROOT/'data/utility_snapshot.json';rows=json.loads(p.read_text(encoding='utf-8'));error=None;retrieved=None
    if refresh:
        try:
            response=urllib.request.urlopen(urllib.request.Request(UTILITY_URL,headers={'User-Agent':'CodeCoogs-Hurricane-Hackathon-Prototype/0.1'}),timeout=15);raw=response.read(10000000)
            if raw[:2]==b'\x1f\x8b':raw=gzip.decompress(raw)
            rows=normalize_utility(json.loads(raw));p.write_text(json.dumps(rows,separators=(',',':')));retrieved=datetime.now(timezone.utc).isoformat()
        except Exception as e:error=str(e)
    if not rows:return {'rows':[],'latest':None,'age_hours':None,'refresh_error':error,'retrieved':retrieved}
    stamp=max(float(r.get('lastUpdatedTime') or 0) for r in rows);latest=datetime.fromtimestamp(stamp/1000,timezone.utc);age=(datetime.now(timezone.utc)-latest).total_seconds()/3600
    return {'rows':rows,'latest':latest.isoformat(),'age_hours':age,'refresh_error':error,'retrieved':retrieved}

def launch_storm_planner():
    import folium
    from folium.plugins import HeatMap
    import ipywidgets as widgets
    from IPython.display import display,HTML
    try:
        from google.colab import output
        output.enable_custom_widget_manager()
    except ImportError:pass
    key=''
    try:
        from google.colab import userdata
        key=userdata.get('CARTO_API_KEY').strip()
    except Exception:pass
    h=load_hazards();state={'utility':load_utility()};common={'style':{'description_width':'220px'},'layout':widgets.Layout(width='680px')}
    display(HTML('<h2>Houston Storm Impact & Resource Planner</h2><p>Explore recorded power outages, tree/debris reports and source damage descriptions. Choose separate ambulance, repair, cooling and community/medical staging candidates.</p><p><b>Color means recorded intensity or report density. Future outage/tree probabilities have not been fitted or validated.</b> Reports during a storm window do not establish its cause.</p>'))
    controls={
      'storm':widgets.Dropdown(options=list(STORMS),description='Storm/recovery window:',**common),
      'layer':widgets.Dropdown(options=LAYERS,description='Map filter:',**common),
      'mechanism':widgets.Dropdown(options=['All source narratives','Flood/water','Tree mentions','Building/roof mentions','Power/pole mentions'],description='Damage evidence mentions:',**common),
      'inspect_zip':widgets.Dropdown(options=['All areas']+list(h['areas'].index),description='Inspect planning ZIP point:',**common),
      'ambulances':widgets.IntSlider(value=2,min=1,max=5,description='Ambulance staging sites:',continuous_update=False,**common),
      'dispatch':widgets.IntSlider(value=2,min=1,max=5,description='Repair dispatch sites:',continuous_update=False,**common),
      'cooling':widgets.IntSlider(value=3,min=1,max=5,description='Cooling hubs:',continuous_update=False,**common),
      'community':widgets.IntSlider(value=3,min=1,max=5,description='Community/medical posts:',continuous_update=False,**common),
      'slowdown':widgets.FloatSlider(value=1,min=1,max=2,step=.25,description='Travel slowdown (assumed):',continuous_update=False,**common),
      'closed':widgets.Dropdown(options=['None']+h['base']['eligible'],description='Unavailable candidate:',**common),
    }
    refresh=widgets.Button(description='Refresh utility snapshot',layout=widgets.Layout(width='230px'))
    download=widgets.Button(description='Download placements + evidence',button_style='info',layout=widgets.Layout(width='280px'))
    notice=widgets.Output();result=widgets.Output()
    def render(**kw):
        try:plan=choose_resources(**{k:v for k,v in kw.items() if k not in ['layer','mechanism','inspect_zip']})
        except ValueError as e:print(e);state.pop('plan',None);return
        state['plan']=plan;storm=kw['storm'];layer=kw['layer'];s=plan['reports_selected'];history=plan['history'];a=plan['areas'];sites=plan['base']['sites']
        print('SELECTED WINDOW:',storm,*STORMS[storm],'(end date excluded)')
        print('These are historical observations. The derecho was a windstorm, not a hurricane.')
        display(plan['role_summary'].round(1))
        print('Role weights: ambulance = HHS medical-equipment counts; repair = tree/debris/electrical reports; cooling = HHS × historical county-outage rank; community/medical = Harvey household-member context.')
        print('Weights are planning proxies. They do not count actual injuries, utility faults, or predicted clients. Site counts do not establish staffing or capacity.')
        tiles=('https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key='+key) if key else None
        m=folium.Map(location=[29.8,-95.4],zoom_start=9,height=520,tiles=tiles,attr='<a href="https://www.openstreetmap.org/copyright">© OpenStreetMap contributors</a>, <a href="https://carto.com/attributions">© CARTO</a>; routing <a href="https://project-osrm.org/">OSRM</a>/OpenStreetMap' )
        if not key:print('Street background is off. Enable the saved CARTO_API_KEY Secret for this notebook; no key-entry prompt is used.')
        if layer in CATEGORIES:
            category=CATEGORIES[layer];selected=s[s.category==category]
            if '(Harvey only)' in layer and storm!='Harvey':print('This additional category was extracted only for Harvey. No data for the selected 2024 window; do not interpret the empty layer as zero requests.')
            palette={0.1:'#176b31',0.5:'#a8d65a',1.0:'#ffff33'} if 'green-yellow' in layer else {0.1:'#fee5d9',0.5:'#fb6a4a',1:'#a50f15'} if '(red)' in layer else {0.1:'#c6dbef',0.5:'#4292c6',1:'#084594'} if '(blue)' in layer else {0.1:'#dadaeb',0.5:'#9e9ac8',1:'#54278f'}
            if len(selected):
                # Count co-located service records; do not infer a damage probability.
                points=selected.groupby(['latitude','longitude']).size().reset_index(name='weight')
                points['weight']=points.weight/points.weight.max()
                HeatMap(points[['latitude','longitude','weight']].values.tolist(),radius=18,blur=14,min_opacity=.2,gradient=palette,name=category).add_to(m)
            print(f'{category}: {len(selected):,} reports. Heat represents report density, not tree-failure probability, injured people or verified structural collapse.')
        elif layer=='Recorded power outages (red counties)':
            lookup=history.set_index('fips_code').to_dict('index') if len(history) else {};peak=max([r['peak_customers_out'] for r in lookup.values()],default=1)
            for feature in plan['counties']['features']:
                code=feature['properties']['GEOID'];r=lookup.get(code)
                ratio=math.log1p(r['peak_customers_out'])/math.log1p(peak) if r and not r['exceeds_supplied_customer_denominator'] else None
                color='#bdbdbd' if ratio is None else '#fee5d9' if ratio<.4 else '#fcae91' if ratio<.65 else '#fb6a4a' if ratio<.85 else '#a50f15'
                label=feature['properties']['NAME']
                details='No source records in this window. Unknown, not zero.' if r is None else f"Peak reported customers out: {r['peak_customers_out']:,.0f}<br>Peak UTC: {r['peak_time_UTC']}<br>Native-record availability: {r['source_record_availability_pct']:.1f}% (not customer coverage)"
                if r and r['exceeds_supplied_customer_denominator']:details+=' <br>QUALITY FLAG: reported outages exceed the supplied total customer count. Shown gray; omitted from cooling priority.'
                folium.GeoJson(feature,name=label,style_function=lambda _,c=color:{'fillColor':c,'color':'#666','weight':1,'fillOpacity':.52},tooltip=label,popup=folium.Popup(label+'<br>'+details+'<br>County observation, not a ZIP-level or future probability.',max_width=350)).add_to(m)
            print('Red = larger recorded county peak (log-scaled color); gray = missing or flagged source data. Counts are electric customers/accounts, not people. Missing intervals and historic utility coverage limit comparisons. County totals are never painted as ZIP outage probabilities.')
            if storm=='Harvey':print('Older Harvey source coverage can severely underrepresent actual outages. A low recorded count is not evidence of low true impact or safety.')
            display(history.round(1))
        elif layer=='Utility report snapshot (check dates)':
            utility=state['utility'];print('Newest event update UTC:',utility['latest']);print('Hours since newest event update:',None if utility['age_hours'] is None else round(utility['age_hours'],1))
            stale=utility['age_hours'] is None or utility['age_hours']>2 or utility['age_hours']<-.25
            if stale:print('DATE WARNING: this snapshot has no recent confirmed event update. Do not read these markers as current outages. Refresh may still return old data.')
            if utility['refresh_error']:print('Refresh failed; retained cached snapshot:',utility['refresh_error'])
            for r in utility['rows']:
                update=datetime.fromtimestamp(float(r['lastUpdatedTime'])/1000,timezone.utc).isoformat()
                report_age=(datetime.now(timezone.utc).timestamp()*1000-float(r['lastUpdatedTime']))/3600000
                old_report=report_age>2 or report_age<-.25
                folium.CircleMarker([r['latitude'],r['longitude']],radius=5,color='#777777' if old_report else '#d73027',fill=True,tooltip=str(r.get('status')),popup=folium.Popup(f"Provider reported affected count: {r.get('numPeople')} (not a resident count)<br>Status: {r.get('status')}<br>Event update UTC: {update}<br>Provider cause: {r.get('cause') or 'Unknown; do not infer'}",max_width=350)).add_to(m)
            print('This is a manually refreshed public map feed, not continuous monitoring. Map points may be generalized; a dot is not an exact failed asset or every affected property.')
        elif layer=='Ambulance drive coverage':
            times=plan['table'].get('Ambulance staging drive (min)')
            if times is not None:
                for code,row in a.iterrows():
                    value=float(times.loc[code]);color='green' if value<=10 else 'red'
                    folium.CircleMarker([row.latitude,row.longitude],radius=5,color=color,fill=True,tooltip=f'Planning ZIP {code}: {value:.1f} modeled driving minutes').add_to(m)
            print('Green/red only means the ten-minute modeled base-to-area drive target is met/missed. It is unrelated to outage likelihood.')
        else:
            print('UNAVAILABLE: no validated future neighborhood outage or tree-strike probability model is included. Red cannot mean high future probability here. We need labeled outages/non-outages, storm forecasts, tree exposure and event-separated validation. No fabricated probability surface is drawn.')
        roles={'Ambulance staging':('red','plus-sign'),'Repair dispatch':('blue','wrench'),'Cooling hubs':('orange','home'),'Community/medical posts':('purple','home')}
        for role,(color,icon) in roles.items():
            fg=folium.FeatureGroup(name=role,show=True).add_to(m)
            for name in plan['choices'][role]:
                row=sites.loc[name];folium.Marker([row.latitude,row.longitude],tooltip=role+': '+name,popup=folium.Popup(role+'<br>'+name+'<br>Hypothetical activated candidate; safety, staffing, capacity and permission unverified.',max_width=320),icon=folium.Icon(color=color,icon=icon)).add_to(fg)
        excluded=folium.FeatureGroup(name='Excluded candidate sites',show=False).add_to(m)
        for name,row in sites.iterrows():
            if name not in plan['base']['eligible'] or name==kw['closed']:folium.Marker([row.latitude,row.longitude],tooltip=name+' — excluded',icon=folium.Icon(color='black')).add_to(excluded)
        hospitals=folium.FeatureGroup(name='Two fixed existing ER examples (partial inventory)',show=False).add_to(m)
        for r in plan['base']['facilities']['hospital_examples']:folium.Marker([r['latitude'],r['longitude']],tooltip=r['name'],popup='Existing ER example. No capacity, clinical assignment or real-time activation check.',icon=folium.Icon(color='darkred',icon='plus-sign')).add_to(hospitals)
        folium.LayerControl(collapsed=False).add_to(m);m.fit_bounds(a[['latitude','longitude']].values.tolist());display(m)
        display(HTML('<p><b>Site colors:</b> red ambulance staging · blue repair dispatch · orange cooling · purple community/medical. Roles can share a location. Use the layer checkboxes to see overlapping markers. Existing hospitals stay fixed.</p><p><a href="https://tracker.centerpointenergy.com/map/" target="_blank">Open CenterPoint’s official outage map</a></p>'))
        if kw['inspect_zip']!='All areas':
            print('Chosen representative area. Report counts are grouped by nearest point, not exact ZIP membership.');display(plan['table'].loc[[kw['inspect_zip']]].T)
        print('HISTORICAL DAMAGE EVIDENCE — weather event type plus source narrative; mention tags are not a confirmed engineering diagnosis.')
        evidence=plan['evidence'];evidence=evidence[evidence.storm==storm]
        if kw['mechanism']!='All source narratives':evidence=evidence[evidence.mention_tags.apply(lambda tags:kw['mechanism'] in tags)]
        if len(evidence):
            show=evidence[['date','event_type','county_or_zone','geography_type','flood_cause','narrative','source_url']].copy();display(show.head(12))
        else:print('No matching source narratives in this subset. This does not establish that no damage occurred.')
        state['evidence_selected']=evidence
        print('All source rows and placement assumptions are included in the export. The original people/supply planner is available in the next notebook section.')
    def redraw():
        with result:
            result.clear_output(wait=True);render(**{k:v.value for k,v in controls.items()})
    for control in controls.values():control.observe(lambda change:redraw(),names='value')
    def on_refresh(_):
        with notice:
            notice.clear_output(wait=True);print('Reading the public utility feed...')
        state['utility']=load_utility(refresh=True)
        with notice:
            notice.clear_output(wait=True);print('Refresh checked. Inspect the newest event timestamp; retrieval does not prove the reports are current.')
        if controls['layer'].value!='Utility report snapshot (check dates)':controls['layer'].value='Utility report snapshot (check dates)'
        else:redraw()
    refresh.on_click(on_refresh)
    def export(_):
        if 'plan' not in state:return
        import zipfile
        plan=state['plan'];path=ROOT/'storm_scenario_results.zip'
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('placements_by_representative_area.csv',plan['table'].round(2).to_csv());z.writestr('selected_roles.csv',plan['role_summary'].round(2).to_csv(index=False));z.writestr('county_outage_peaks.csv',plan['history'].to_csv(index=False));z.writestr('source_damage_evidence.csv',state['evidence_selected'].to_csv(index=False));z.writestr('assumptions.json',json.dumps({'storm':plan['storm'],'selected_sites':plan['choices'],'assumptions':plan['assumptions'],'utility_newest_event_UTC':state['utility']['latest'],'no_validated_future_probability_model':True},indent=2))
        try:
            from google.colab import files
            files.download(str(path))
        except ImportError:
            with notice:print('Saved',path)
    download.on_click(export)
    global _storm_view
    _storm_view=widgets.VBox(list(controls.values())+[widgets.HBox([refresh,download]),notice,result]);display(_storm_view);redraw()
if __name__=='__main__':launch_storm_planner()
