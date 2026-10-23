"""Train a post-event estimator of summed reported occupants in flood-damage registrations."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import KFold,train_test_split
import sklearn
ROOT=Path(__file__).resolve().parent
FEATURES=['registration_records','latitude','longitude']
TARGET='members_in_flood_damage_records_sum'
def new_model():return RandomForestRegressor(n_estimators=300,min_samples_leaf=3,random_state=42,n_jobs=1)
def fit_predict(train,validation):
    # Learn occupants-per-registration rate, then scale by the known registration count.
    # The target ZIP's flood outcomes and household-member totals are not input features.
    m=new_model();m.fit(train[FEATURES],train[TARGET]/train.registration_records,sample_weight=train.registration_records)
    return np.maximum(0,m.predict(validation[FEATURES])*validation.registration_records.to_numpy())
def train_and_evaluate():
    source=json.loads((ROOT/'data'/'harvey_harris_household_summary.json').read_text(encoding='utf-8'))
    hh=pd.DataFrame(source['rows']);areas=pd.DataFrame(json.loads((ROOT/'data'/'study_areas.json').read_text(encoding='utf-8'))['rows'])
    frame=hh.merge(areas,on='zipCode',how='inner',validate='one_to_one');frame=frame[frame.registration_records>0].reset_index(drop=True)
    assert frame.zipCode.is_unique and frame[FEATURES+[TARGET]].notna().all().all()
    train,test=train_test_split(frame,test_size=.25,random_state=42)
    rate=float(train[TARGET].sum()/train.registration_records.sum());baseline=test.registration_records.to_numpy()*rate
    prediction=fit_predict(train,test);base_mae=float(mean_absolute_error(test[TARGET],baseline));mae=float(mean_absolute_error(test[TARGET],prediction))
    estimates=np.full(len(frame),np.nan)
    for a,b in KFold(n_splits=3,shuffle=True,random_state=42).split(frame):estimates[b]=fit_predict(frame.iloc[a],frame.iloc[b])
    assert np.isfinite(estimates).all()
    planning=frame[['zipCode','registration_records',TARGET]].copy();planning['model_estimated_flood_household_members_sum']=estimates
    held=test[['zipCode','registration_records',TARGET]].copy();held['baseline_estimate']=baseline;held['model_estimate']=prediction
    report={'task':'Post-event estimate of summed reported household members in FEMA flood-damage registration records','target':TARGET,'source_records':source['source_records'],'source_records_in_matched_model_zips':int(frame.registration_records.sum()),'source_records_outside_matched_model_zips':int(source['source_records']-frame.registration_records.sum()),'study_zip_codes':len(frame),'train_zip_codes':len(train),'test_zip_codes':len(test),'features':FEATURES,'model':'Random forest of rates scaled by already-reported registration counts','sklearn_version':sklearn.__version__,'baseline_mae_reported_members_per_zip':base_mae,'model_mae_reported_members_per_zip':mae,'mae_reduction_percent':100*(base_mae-mae)/base_mae,'pooled_training_rate':rate,'validation':'Fixed random 75/25 split of ZIP areas within Harvey; three-fold cross-fitting for map estimates','limitations':['Post-event registrations are required; this does not predict a future storm.','The target is summed household members in registration records, not verified distinct affected people or users of any service.','Households without registrations, unmatched geocodes and missing household sizes are incompletely represented.','Flood damage is an observed proxy for cleanup priority, not a cleanup request or injury label.','Nearby ZIPs may be in both train and test; this is not independent-storm or spatial holdout validation.','Cooling, community and health service participation percentages in the GUI are user assumptions, not learned labels.']}
    (ROOT/'people_model_report.json').write_text(json.dumps(report,indent=2));(ROOT/'people_model_predictions.json').write_text(json.dumps({'rows':planning.to_dict('records')},indent=2));(ROOT/'people_model_heldout.json').write_text(json.dumps({'rows':held.to_dict('records')},indent=2));print(json.dumps(report,indent=2));return report
if __name__=='__main__':train_and_evaluate()
