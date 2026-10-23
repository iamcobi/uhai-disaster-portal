# Expanded planner: source and interpretation guide

All source snapshots were retrieved on October 23, 2026. Data collection needs no paid subscriptions or API keys. CARTO's street background uses the user's existing key; the GUI works with markers and tables without it. Source publishers may change downloads in the future.

## Sources actually included

| Source | Included data | Use | Important limit |
| --- | --- | --- | --- |
| OpenFEMA IndividualAssistanceHousingRegistrantsLargeDisasters v1 | All 449,932 records returned for Harvey and geocoded Harris County block prefix, aggregated by ZIP | Household-member counts and observed flood-damage record counts | Not distinct affected residents, confirmed assistance eligibility, cleanup requests, injuries, or service users |
| Census 2020 TIGERweb ZCTAs | 282 ZIP-area records in 77000–77599; 189 populated internal representative points in the study rectangle | Population context and broader geographic coverage | 2020 population, not today's population or a storm impact forecast; ZCTAs approximate ZIP geography |
| HHS emPOWER public service | 1,850 Texas ZIP records, October 2026 source-layer snapshot | Electricity-dependent Medicare beneficiary priority | Medicare subset only; small protected 1–11 cells published as 11; counts and service groups are not additive |
| NOAA Storm Events details | 13,657 Texas event records for 2017, 2019, 2024 | Injury and weather-history context | Three selected years, not continuous history or hurricane-only records; county and forecast-zone geography; no ZIP ER-arrival labels |
| Houston Health and Harris County public facility directories | 14 existing community-center candidates | Hypothetical response posts and cooling/community hubs | Not verified activated, safe, permitted or capacity-sufficient sites |
| Harris Health emergency-care directory | Ben Taub and LBJ ER examples | Fixed destinations and modeled travel examples | Only two examples, not a complete regional ER inventory or a clinical destination recommendation |
| Census Geocoder | Approximate address points | Facility location | Street interpolation, not verified emergency vehicle entrances |
| FEMA NFHL | 14 point flood-zone queries; 12 pass the prototype rule | Exclude SFHA and unknown candidate points | Outside mapped SFHA does not establish safety; no road or building assessment |
| OSRM/OpenStreetMap | Both driving directions, 189 points, 14 centers, two ER examples | Separate response and hub access calculations | Ordinary modeled driving, not ambulance speeds, flood closures, queues, dispatch or service time |

Source links:
- https://www.fema.gov/api/open/v1/IndividualAssistanceHousingRegistrantsLargeDisasters
- https://www.fema.gov/openfema-data-page/individual-assistance-housing-registrants-large-disasters-v1
- https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/tigerWMS_Census2020/MapServer/84
- https://www.census.gov/programs-surveys/geography/guidance/geo-areas/zctas.html
- https://empowerprogram.hhs.gov/about-empowermap.html
- https://empowerprogram.hhs.gov/empowermap.html
- https://services2.arcgis.com/ZQ4jTQn6k7VPXEwO/arcgis/rest/services/HHS_emPOWER_REST_Service_Public/FeatureServer/1
- https://www.ncei.noaa.gov/access/storm-events-database/
- https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/
- https://www.houstonhealth.org/services/multi-service-centers
- https://www.hcp1.net/EFLCommunityCenter
- https://ssc.harriscountytx.gov/Events/EventID/5300/Precinct-4-Townhall-Meeting-at-Radack-Community-Center
- https://www.harrishealth.org/locations/emergency-care
- https://geocoding.geo.census.gov/geocoder/
- https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28
- https://project-osrm.org/docs/v26.4.0/api/
- https://www.openstreetmap.org/copyright

## What the GitHub search supplied

The requested awesome-public-datasets repository is a directory of links, not one downloadable disaster dataset. Its Government section points to Houston's portal and the US Census; Climate+Weather points to NOAA climate datasets; GIS points to OpenStreetMap; SocialSciences points to WorldPop and the Humanitarian Data Exchange. The implementation follows authoritative sources for the actual Houston-area data. WorldPop and HDX were investigated as discovery options but are not included in the fitted model. No synthetic data or duplicate records were added to inflate the sample.

Repository: https://github.com/awesomedata/awesome-public-datasets/blob/master/README.rst

## County, geography and aggregation

The FEMA query is `disasterNumber eq 4332 and censusBlockId ge '482010000000000' and censusBlockId lt '482020000000000'`. It selects geocoded Harris County blocks by county FIPS prefix, not every Harris County applicant. Missing and erroneous census-block locations can exclude records. Pages were ordered by ID, all source counts checked, and duplicate IDs rejected. The delivery contains only ZIP aggregates, not household-level records. `source_records` counts registrations, not training examples or people. Records are not filtered by verified eligibility or deduplicated at person/address level.

Household composition is summed only when numeric and between 1 and 50 inclusive; other values are counted as missing/invalid and are not filled with an average. The source distribution and excluded-count fields remain in the summary JSON. The target sums household members for records with `floodDamage == true`. This is a labeled historical proxy for flood-affected household burden, not actual cooling-center attendance, injury counts or cleanup requests. `specialNeeds` describes applicant accommodation needs for FEMA assistance and is not a count of injured household members.

The map uses the 189 populated Census 2020 ZCTA representative points in latitude 29.4–30.4, longitude -96.1–-94.8, and codes 77000–77599. This is a study rectangle, not the Harris County boundary or all Greater Houston. FEMA postal ZIP codes are joined by code to Census ZCTAs, with unmatched areas left missing. Current layer dates and geographic vintages differ: 2017 FEMA, 2020 Census context, 2026 HHS/roads/maps. Context layers are not treated as pre-Harvey predictors.

## Machine learning and scenarios

A random forest learns a rate of reported flood-household members per registration. It uses only already-reported total registration count and location. The target ZIP's flood outcomes, household-member total, loss dollars, and assistance payments are not input features. The rate is multiplied by known registrations to estimate a count. Train/test splitting is fixed at 75/25 of unique matched ZIPs; separate three-fold cross-fitted estimates supply map weights. Nearby ZIPs can occur on both sides. This does not test another storm, a future time period, or unseen spatial regions.

The baseline uses the pooled training-set members-per-registration rate. `people_model_report.json` contains both held-out MAEs. The report uses MAE in reported member-count units per ZIP, not percent accuracy. There are far fewer ZIP-level training examples than raw household registrations.

Service quantities are scenario calculations: model estimated members × Harvey-case scale × assumed service participation. Cooling, community and health participation defaults are illustrative; the data do not estimate them. Groups overlap, so their totals must not be added as unique people. Low/high settings are sensitivity scenarios, not statistical confidence intervals. Meals assume three per community visitor per day and are an inventory calculation, not a nutrition recommendation. Actual food selection, medical acuity, attendance duration and special diets are not modeled.

Cleanup priority uses the observed number of registrations marked with flood damage; it is not a prediction of cleanup jobs, debris volume, crew hours or unique cleanup clients. The NOAA injury history is supplied for analysis, but there is no fitted ZIP-level injury, ER-arrival or hospitalization model. Predicting those needs historical local labels with comparable event and geographic definitions, such as de-identified EMS/ER service counts, clinic visits or cleanup work requests. Request counts also need deduplication before treating them as people.

## Optimization

The response-post search exhaustively compares eligible combinations, maximizes selected demand weight within a modeled ten-minute base-to-area drive, and breaks ties by weighted average driving time. A separate search uses area-to-selected-hub times. The ten-minute hub target is an additional illustrative access objective; the user's required ten-minute goal is base to affected area. Neither includes service time or guarantees real-world arrival. Every area is counted once per objective. The solution is best among the supplied candidates and assumptions, not a proven best site anywhere in Houston.

An illustrative point-screen excludes SFHA and unknowns. Sites outside SFHA can flood. Road closures, facility capacity, staffing, generator fuel, site permission, opening hours and building safety require additional inputs. Posts and hubs may share a candidate under an assumed co-location option; shared capacity is not modeled. Two existing hospitals remain fixed examples; the optimizer does not plan construction or relocation of hospitals.

## Reuse and provenance

Publicly accessible is not the same as open-source licensing. Review individual publishers' terms. US federal source data are public; use the publishers' caveats. OSRM route data uses the OpenStreetMap network under ODbL with required OpenStreetMap attribution. CARTO tiles use CARTO attribution and key terms. Source URLs, queries and retrieval dates are stored with the cached data. No medical-equipment subgroup counts are combined to infer suppressed cells.
