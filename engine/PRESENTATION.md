# Explaining your storm planner

## Two-minute explanation

I built a Houston-area hurricane resource-planning prototype. It combines historical power outages, tree and debris service reports, source damage descriptions, medical-equipment vulnerability and modeled driving times.

The map has separate filters. A green-to-yellow layer shows tree-removal or storm-debris report density. A red county layer shows peak recorded electric customers without power during a selected storm/recovery window. County-level observations stay county-level. Gray means missing or flagged data, not safe. I also show NWS source descriptions of flooding, trees, roofs and electrical infrastructure, keeping source links and distinguishing text mentions from verified causes.

I used about 273,000 native outage observations in nine regional counties and more than 48,000 selected mapped service-request records. Reports are not unique injured people or verified utility faults. Historical utility coverage varies. I added source checks for duplicate timestamps, inconsistent customer denominators and stale live-feed event dates.

The placement tool independently searches for ambulance staging, repair dispatch, cooling hubs and community/medical posts. It exhaustively compares eligible combinations of supplied public facilities. Ambulances use a medical-vulnerability weight; repair dispatch uses historical tree/debris/electrical report weight; cooling combines medical vulnerability with historical county outage rank; community posts use a fixed Harvey household context layer. All are planning proxies. The ten-minute ambulance goal is base to affected area, using ordinary modeled driving. Actual closures, staffing, site permission, capacity and clinical assignment are not established.

I also trained a numerical random forest for post-event flood-household burden. Its held-out improvement over a pooled-rate baseline is only 0.35%, so I report that limitation. It is not a power-outage or injury predictor.

Future outage and tree-strike probabilities are an explicit remaining gap. I would need matched neighborhood/circuit outage and non-outage labels, pre-storm weather forecasts, tree exposure and condition, asset data, and validation on storms kept out of training. I do not call past hotspots high future probabilities or infer improper infrastructure from outage history alone.

## Demo steps

1. Keep Beryl selected. Select Tree removal reports, then Storm debris reports. Explain that green-yellow means report density and that requests can be duplicated or unrelated to the storm.
2. Select Recorded power outages. Explain that red represents county recorded peaks, customers are accounts rather than people, gray is unknown/flagged, and the map does not make ZIP-level outage claims.
3. Select Tree mentions or Power/pole mentions in the damage-evidence filter. Read a source record and open its link. Describe it as source evidence, not an automatic causal diagnosis.
4. Change ambulance or dispatch site budget, slowdown, or one unavailable candidate. Show the four role choices and separate objectives. Use layer checkboxes when roles share a site.
5. Inspect one planning ZIP point, then download placements and assumptions. Report counts are grouped to nearest representative points, not exact ZIP membership.
6. Optionally refresh the utility snapshot. Its newest event time matters more than retrieval time. The bundled feed is stale, and old markers stay gray. Do not claim these are confirmed current outages.

## Questions to answer clearly

**Does red mean my neighborhood will lose power?** No. The red historical layer shows county observations. The future probability filter explicitly says no validated model is available. We do not make numerical future outage claims.

**Does yellow mean a tree will hit a power line or person?** No. It shows historical service-report density. Actual strike prediction requires tree exposure/condition, weather, line locations and labeled strike events.

**Can you detect poor infrastructure?** Outage history can identify places needing investigation, but cannot establish design or maintenance failures. Engineering and asset records are required.

**What did you train?** A numerical household-burden random forest using already-reported FEMA registrations and location, with held-out ZIP evaluation. The code and baseline are included. The resource optimizer is a separate search algorithm; it is not a trained outage model.

**Are you building hospitals?** Existing ER examples stay fixed. The app selects hypothetical temporary medical/community and response posts among existing candidates. It does not model new hospital construction or complete regional hospital capacity.

**Why can ambulance placements remain the same across storms?** They use the fixed HHS medical-equipment layer. Community placements use fixed Harvey context. Repair and cooling priorities use the selected historical storm data. The source years are kept explicit.

**Can every area be reached in ten minutes?** No. The optimizer shows remaining gaps. Travel is ordinary modeled driving to representative points, excluding dispatch and rescue time. Four roles may share a site; actual staffing and capacities are not modeled.

## Submission

Add your name, run all cells, retain the actual model metrics and source notes, and prepare an accessible notebook/code link and live demo. The supplied detailed Track 1 accepts statistical/ML methods and asks for a trained model; NLP/LLM fine-tuning is not required for that detailed track. Check current organizer announcements and the stated submission deadline.
