"""Expanded historical hurricane resource planning GUI for Colab."""
import json
from pathlib import Path
from itertools import combinations
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent
PRIORITIES={
 'ML: flood-household member estimate':'model_estimated_flood_household_members_sum',
 'Historical: reported household members':'reported_household_members_sum',
 'Medical: electricity-dependent Medicare count':'Power_Dependent_Devices_DME',
 'Context: 2020 population':'population_2020',
}
def read(name):return json.loads((ROOT/'data'/name).read_text(encoding='utf-8'))
def load_inputs():
    areas=pd.DataFrame(read('study_areas.json')['rows']).set_index('zipCode')
    hh=pd.DataFrame(read('harvey_harris_household_summary.json')['rows']).set_index('zipCode')
    areas=areas.join(hh,how='left')
    # Missing matches remain missing; absence is not treated as an observed zero.
    em=read('empower_zip.json')['response'];assert not em.get('exceededTransferLimit',False)
    medicare=pd.DataFrame([x['attributes'] for x in em['features']]);medicare['zipCode']=medicare.Zip_Code.astype(str)
    assert medicare.zipCode.is_unique
    cols=['Medicare_Benes','Power_Dependent_Devices_DME','Any_Healthcare_Srvc_Any_DME']
    areas=areas.join(medicare.set_index('zipCode')[cols])
    pred=pd.DataFrame(json.loads((ROOT/'people_model_predictions.json').read_text(encoding='utf-8'))['rows']).set_index('zipCode')
    areas=areas.join(pred[['model_estimated_flood_household_members_sum']])
    facilities=read('facilities_expanded.json');route=read('expanded_routing.json')
    areas=areas.loc[route['zip_codes']]
    sites=pd.DataFrame(facilities['candidate_sites']).set_index('name')
    checks=pd.DataFrame(facilities['flood_checks']).set_index('name')
    eligible=[n for n in route['site_names'] if not bool(checks.loc[n,'excluded'])]
    return {'areas':areas,'sites':sites,'checks':checks,'eligible':eligible,'facilities':facilities,'routes':route}
def optimize(matrix,weights,k,target=10):
    if not 1<=int(k)<=len(matrix):raise ValueError('There are not enough eligible sites for that selection.')
    if weights.sum()<=0:raise ValueError('There is no positive matched demand for this priority.')
    best=None;best_score=(-1,float('-inf'))
    for choice in combinations(range(len(matrix)),int(k)):
        nearest=np.min(matrix[list(choice)],axis=0)
        score=(float(weights[nearest<=target].sum()),-float(np.dot(nearest,weights)/weights.sum()))
        if score>best_score:best=choice;best_score=score
    return list(best),best_score

def build_plan(response_bases=2,hubs=3,slowdown=1.0,priority='ML: flood-household member estimate',closed='None',cooling_pct=30,community_pct=50,health_pct=10,days=3,stress=1.0,inspect_zip="All areas"):
    data=load_inputs();areas=data['areas'].copy();r=data['routes']
    if priority not in PRIORITIES:raise ValueError('Choose a listed priority.')
    if slowdown<1 or stress<0 or days<1:raise ValueError('Use slowdown at least 1, nonnegative scenario scale, and at least one day.')
    if any(not 0<=x<=100 for x in [cooling_pct,community_pct,health_pct]):raise ValueError('Participation percentages must be between 0 and 100.')
    names=[n for n in data['eligible'] if n!=closed];positions=[r['site_names'].index(n) for n in names]
    # Fill only the optimizer's unmatched weights with zero; keep missing values visible in the table.
    weights=areas[PRIORITIES[priority]].fillna(0).to_numpy(dtype=float)
    base=np.asarray(r['base_to_area_minutes'],dtype=float)[positions]*slowdown
    hub=np.asarray(r['area_to_hub_minutes'],dtype=float)[:,positions].T*slowdown
    bi,bs=optimize(base,weights,response_bases);hi,hs=optimize(hub,weights,hubs)
    bnames=[names[x] for x in bi];hnames=[names[x] for x in hi]
    b=base[bi];h=hub[hi];bt=b.min(axis=0);ht=h.min(axis=0)
    hospitals=np.asarray(r['area_to_hospital_minutes'],dtype=float)*slowdown
    target=areas.model_estimated_flood_household_members_sum*stress
    table=pd.DataFrame(index=areas.index)
    table['2020 population (context)']=areas.population_2020
    table['Historical summed household members']=areas.reported_household_members_sum
    table['ML flood-household members (scenario)']=target
    table['Cooling visitors (assumed)']=np.ceil(target*cooling_pct/100)
    table['Community visitors (assumed)']=np.ceil(target*community_pct/100)
    table['Health-service users (assumed)']=np.ceil(target*health_pct/100)
    table['Historical flood-damage records (cleanup indicator)']=areas.flood_damage_registration_records
    table['Published electricity-dependent Medicare count']=areas.Power_Dependent_Devices_DME
    table['Assigned response post']=[bnames[x] for x in b.argmin(axis=0)]
    table['Base to area drive (min)']=bt
    table['Within 10-minute drive']=bt<=10
    table['Assigned cooling/community hub']=[hnames[x] for x in h.argmin(axis=0)]
    table['Area to selected hub drive (min)']=ht
    table['Nearest of TWO example ERs']=[r['hospital_names'][x] for x in hospitals.argmin(axis=1)]
    table['Area to example ER drive (min)']=hospitals.min(axis=1)
    # Meals are a user planning assumption, not a nutrition recommendation.
    table['Community meals (3/person/day assumption)']=table['Community visitors (assumed)']*days*3
    table.index.name='ZIP'
    return {**data,'areas':areas,'table':table,'response_posts':bnames,'hub_sites':hnames,'response_coverage_pct':100*bs[0]/weights.sum(),'hub_coverage_pct':100*hs[0]/weights.sum(),'priority':priority,'weight_total':weights.sum(),'base_minutes':bt,'hub_minutes':ht,'matched_priority_areas':int(areas[PRIORITIES[priority]].notna().sum()),'matched_model_areas':int(target.notna().sum()),'assumptions':{'cooling_pct':cooling_pct,'community_pct':community_pct,'health_pct':health_pct,'days':days,'stress':stress,'slowdown':slowdown}}

def launch_planner():
    import folium
    import ipywidgets as widgets
    from IPython.display import HTML,display
    try:
        from google.colab import output
        output.enable_custom_widget_manager()
    except ImportError:pass
    key=''
    try:
        from google.colab import userdata
        key=userdata.get('CARTO_API_KEY').strip()
    except Exception:pass
    data=load_inputs();eligible=data['eligible'];state={}
    display(HTML('<h2>Houston Hurricane Resource Planner</h2><p>189 representative ZIP-area points â€¢ historical Harvey household impacts â€¢ separate response and hub choices</p><p><b>Model:</b> estimates occupants summed across flood-damage registrations using already-reported registration counts. Service-use percentages below are assumptions, not injury or ER-arrival predictions.</p>'))
    common={'style':{'description_width':'210px'},'layout':widgets.Layout(width='650px')}
    controls={
      'priority':widgets.Dropdown(options=list(PRIORITIES),description='Siting priority:',**common),
      'inspect_zip':widgets.Dropdown(options=['All areas']+list(data['areas'].index),description='Inspect your ZIP:',**common),
      'response_bases':widgets.IntSlider(value=2,min=1,max=min(5,len(eligible)),description='Response/medical posts:',continuous_update=False,**common),
      'hubs':widgets.IntSlider(value=3,min=1,max=min(5,len(eligible)),description='Cooling/community hubs:',continuous_update=False,**common),
      'slowdown':widgets.FloatSlider(value=1,min=1,max=2,step=.25,description='Travel slowdown (assumed):',continuous_update=False,**common),
      'closed':widgets.Dropdown(options=['None']+eligible,description='Unavailable candidate:',**common),
      'stress':widgets.FloatSlider(value=1,min=.25,max=2,step=.25,description='Harvey-case scale (assumed):',continuous_update=False,**common),
      'cooling_pct':widgets.IntSlider(value=30,min=0,max=100,step=5,description='Cooling participation (%):',continuous_update=False,**common),
      'community_pct':widgets.IntSlider(value=50,min=0,max=100,step=5,description='Community participation (%):',continuous_update=False,**common),
      'health_pct':widgets.IntSlider(value=10,min=0,max=100,step=5,description='Health participation (%):',continuous_update=False,**common),
      'days':widgets.IntSlider(value=3,min=1,max=14,description='Supply days (assumed):',continuous_update=False,**common),
    }
    download=widgets.Button(description='Download all ZIP results',button_style='info',layout=widgets.Layout(width='230px'))
    download_note=widgets.Output()
    def export(_):
        with download_note:
            download_note.clear_output(wait=True)
            if 'plan' not in state:print('Choose a valid scenario first.');return
            p=ROOT/'expanded_zip_results.csv';state['plan']['table'].round(2).to_csv(p)
            (ROOT/'scenario_assumptions.json').write_text(json.dumps({'priority':state['plan']['priority'],'response_posts':state['plan']['response_posts'],'hubs':state['plan']['hub_sites'],'assumptions':state['plan']['assumptions'],'notes':'Overlapping service groups. Assumed participation and stress, not trained service-use forecasts. Missing estimates are blank.','matched_model_areas':state['plan']['matched_model_areas']},indent=2))
            try:
                from google.colab import files
                import zipfile
                bundle=ROOT/'scenario_results.zip'
                with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as archive:
                    archive.write(p,p.name);archive.write(ROOT/'scenario_assumptions.json','scenario_assumptions.json')
                files.download(str(bundle))
            except ImportError:print('Saved',str(p))
    download.on_click(export)
    def render(**kw):
        try:plan=build_plan(**kw)
        except ValueError as e:state.pop('plan',None);print(e);return
        state['plan']=plan;t=plan['table'];areas=plan['areas'];sites=plan['sites']
        print('RESPONSE / TEMPORARY MEDICAL POSTS: '+', '.join(plan['response_posts']))
        print('COOLING / COMMUNITY HUBS: '+', '.join(plan['hub_sites']))
        print(f"Modeled 10-minute response-drive coverage: {plan['response_coverage_pct']:.1f}% of selected weight; hub-access coverage: {plan['hub_coverage_pct']:.1f}%.")
        print(f"Priority data matched {plan['matched_priority_areas']}/189 points. The people model matched {plan['matched_model_areas']}/189. Missing is not zero.")
        print('Coverage measures representative-point driving only; dispatch, rescue, closures, queues and building/road safety are not modeled.')
        totals=t[['ML flood-household members (scenario)','Cooling visitors (assumed)','Community visitors (assumed)','Health-service users (assumed)','Community meals (3/person/day assumption)']].sum(min_count=1)
        display(totals.round().to_frame('Partial-study scenario totals'))
        print('These service groups overlap. Do not add them to count unique people. Participation defaults are illustrative, not measured rates or confidence intervals.')
        if key:
            m=folium.Map(location=[29.8,-95.4],zoom_start=9,height=470,tiles='https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key='+key,attr='Â© OpenStreetMap contributors, Â© CARTO; routing OSRM/OpenStreetMap')
        else:
            print('Street background unavailable: enable the existing CARTO_API_KEY secret for this notebook. All planning results and markers still work; no key prompt is used.')
            m=folium.Map(location=[29.8,-95.4],zoom_start=9,height=470,tiles=None)
        af=folium.FeatureGroup(name='All 189 ZIP-area points',show=True).add_to(m)
        for code,a in areas.iterrows():
            minutes=t.loc[code,'Base to area drive (min)'];color='green' if minutes<=10 else 'red'
            est=a.model_estimated_flood_household_members_sum
            label='not matched' if pd.isna(est) else f'{est*kw["stress"]:,.0f}'
            folium.CircleMarker([a.latitude,a.longitude],radius=4,color=color,fill=True,fill_opacity=.65,tooltip=f'ZIP {code} | drive {minutes:.1f} min | flood-household member estimate {label}').add_to(af)
        sf=folium.FeatureGroup(name='Candidate posts and hubs',show=True).add_to(m)
        for name,s in sites.iterrows():
            status=[]
            if name in plan['response_posts']:status.append('selected response post')
            if name in plan['hub_sites']:status.append('selected hub')
            if name not in eligible or name==kw['closed']:status.append('excluded')
            color='black' if 'excluded' in status else 'purple' if len(status)==2 else 'blue' if 'selected response post' in status else 'orange' if 'selected hub' in status else 'gray'
            folium.Marker([s.latitude,s.longitude],tooltip=name,popup=name+'<br>'+(', '.join(status) or 'other candidate'),icon=folium.Icon(color=color)).add_to(sf)
        hf=folium.FeatureGroup(name='Two verified ER examples (partial inventory)',show=False).add_to(m)
        for h in plan['facilities']['hospital_examples']:folium.Marker([h['latitude'],h['longitude']],tooltip=h['name'],popup='Existing ER example. Activation, capacity, appropriate clinical destination and roads unverified.',icon=folium.Icon(color='red',icon='plus-sign')).add_to(hf)
        folium.LayerControl(collapsed=False).add_to(m);m.fit_bounds(areas[['latitude','longitude']].values.tolist());display(m)
        display(HTML('<p>Green/red: response-drive target met/missed. Blue: response post. Orange: hub. Purple: both. Black: excluded. Centers are hypothetical activated facilities; outside mapped SFHA does not establish safety.</p><p><b>ER column:</b> nearest by modeled drive among only two public ER examples, with no medical or capacity recommendation. Hospitals stay fixed; the optimizer chooses temporary posts.</p>'))
        print('Assumed demand assigned to each selected hub (no capacity limits):')
        display(t.groupby('Assigned cooling/community hub')[['Cooling visitors (assumed)','Community visitors (assumed)','Community meals (3/person/day assumption)']].sum(min_count=1).round())
        if kw['inspect_zip'] != 'All areas':
            print('Selected ZIP scenario and travel estimates:')
            display(t.loc[[kw['inspect_zip']]].T)
        display(t.sort_values('ML flood-household members (scenario)',ascending=False).head(25).round(1))
        print('Showing 25 rows. Download the complete 189-row table and assumptions below. Cleanup indicator counts registrations reporting flood damage, not people requesting cleanup.')
    result=widgets.interactive_output(render,controls)
    global _expanded_view
    _expanded_view=widgets.VBox(list(controls.values())+[result,download,download_note]);display(_expanded_view)
    details=widgets.Output()
    with details:
        display(data['checks'][['flood_zone','zone_description','excluded']])
        print('HHS public data uses 11 for small protected cells of 1â€“11; published counts are not exact unique local patients. Different health-service categories overlap; do not sum them.')
        print('Harvey outcomes (2017), Census context (2020), HHS snapshot and ordinary roads (2026) are separate layers, not one matched pre-storm training dataset.')
        print('NOAA Texas records for 2017, 2019 and 2024 are supplied separately as historical injury/weather context. County and forecast-zone records are not assigned to ZIP injury forecasts.')
    accordion=widgets.Accordion(children=[details],selected_index=None);accordion.set_title(0,'Source and flood-screen details');display(accordion)
if __name__=='__main__':launch_planner()
