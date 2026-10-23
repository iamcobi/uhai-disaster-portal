# Presentation and demo notes

## Two minute explanation

Houston needs to position limited response resources near areas affected by hurricanes while considering access and staging-site exposure. I built a historical planning prototype using Hurricane Harvey homeowner assistance records, public facility locations, FEMA flood-map checks and modeled road driving times.

The trained component estimates recorded homeowner cases with inspected damage above $30,000, given already-reported registration counts and location. I aggregated records by ZIP, so each ZIP appears once. I held out 42 ZIP areas and trained on 125. A pooled-rate baseline had mean absolute error of 57.95 cases per ZIP; the random forest had 50.45, a 12.94% reduction on this split. That is within-Harvey validation, not a forecast of a future hurricane. Damage amounts and payments were not used as input features.

The planning component compares every eligible combination of staging sites. It maximizes the selected priority weight within a modeled ten-minute base-to-area drive. The GUI can prioritize historical registration counts or cross-fitted estimates of high-damage cases. Those represent different quantities, so their coverage percentages should be reported separately.

For the historical-registration example, expanding the candidate pool from five to seven improved coverage from 23.98% to 41.54% of the weight in the same ten-area sample, using two staging bases. An example FEMA point screen removes mapped Special Flood Hazard Area sites and unknowns. The selected default pair is Northeast Multi-Service Center and Radack Community Center.

Users can change the number of bases, assume slower travel, or make one site unavailable. The cooling-hub table separately calculates area-to-hub driving, treating eligible community centers as assumed-open heat-relief hubs. Actual activation and capacity are not verified.

This is a decision-support case study. It does not guarantee ten-minute rescues, predict power outages, cover all Houston residents, or establish facility safety. Next improvements would use more storms, current outage and road-closure data, verified building entrances and hub capacities.

## Three demo actions

1. Select Historical registrations, 2 bases, slowdown 1.0, and no manual exclusion. Explain the 41.54% sample-weight coverage and green/red representative points.
2. Exclude Northeast Multi-Service Center. Under historical-registration priority, the program should reselect Radack and El Franco Lee, with about 38.87% sample-weight coverage. The number of bases remains two.
3. Reset the exclusion, switch to model-estimated high-damage cases, and explain that the trained model changes the priority weights. Show the separate training evaluation and the cooling-hub travel table.

## Questions to be ready for

**What did you train?** A random forest regressor: an ensemble of decision trees learning a numeric caseload estimate from labeled examples. This is ordinary numerical model training, not language-model fine-tuning.

**What is the label?** The number of registered homeowner cases with FEMA-inspected damage greater than $30,000. This is a chosen monetary threshold, not an official structural damage-severity class.

**What did the model see?** Registration counts, latitude and longitude. Registration counts are post-storm inputs; the model is for post-event estimation rather than pre-storm forecasting.

**How did you test it?** A fixed 75/25 split of unique study ZIPs. No ZIP is duplicated between those subsets. Nearby ZIPs can occur in both subsets; this does not test another hurricane or another geographic region. Planning estimates additionally use three-fold cross-fitting, leaving each ZIP's target out of its own prediction fit.

**What is MAE?** Mean absolute error: the average absolute difference between predicted and recorded high-damage case counts, measured in cases per ZIP. Lower is better. MAE is not percentage accuracy.

**What does the optimizer do?** It enumerates candidate-site combinations, counts the priority weight covered within ten modeled driving minutes without double counting an area, then breaks ties by weighted average driving time.

**Does 41.54% mean 41.54% of Houston people?** No. It is the share of registration weight at the ten representative points in this case study. Program registrations are not people, all affected households, outages or rescue calls.

**Are the bases safe?** Not established. The screen checks current FEMA mapped SFHA status at approximate address points. Sites outside SFHA can still flood; building condition, access routes, wind, power and permission require separate assessment.

**Are these actual open cooling centers?** They are hypothetical heat-relief hubs assumed open in the scenario. Actual activation, capacity, eligibility and medical transport requirements are not modeled.

**Does the slowdown predict flood closures?** No. It multiplies all modeled drive times by a user-selected assumption. No specific blocked roads are inferred.

**Why no separate website?** The notebook already provides a GUI through controls, a map and tables. The supplied detailed competition description accepts notebooks and prototypes. Prepare an accessible notebook/code link and live demo, and check any organizer updates.

## Submission checklist

- Add your project name and your own name to the notebook.
- Run setup, training and GUI cells successfully.
- Keep the model evaluation outputs and explain their limits.
- Include the project source ZIP or a repository link along with the notebook link.
- Check sharing permissions from another browser/account if possible.
- Keep a live demo ready as requested by the packet. The supplied Kaggle description calls for submission by 4:30 PM Central.

## Technical references

- FEMA source catalog: https://catalog.data.gov/dataset/housing-assistance-program-data-owners
- Census ZCTA geography: https://www.census.gov/programs-surveys/geography/guidance/geo-areas/zctas.html
- FEMA flood-map layer: https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28
- OSRM routing: https://project-osrm.org/docs/v26.4.0/http
- Random forest documentation: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html
- Data snapshots and source-specific qualifications: data/SOURCES.md
