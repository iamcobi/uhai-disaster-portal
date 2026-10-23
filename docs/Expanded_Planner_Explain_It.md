# Presenting your expanded planner

## Your two-minute explanation

My project is a hurricane resource-planning prototype for the Houston area. It asks: given limited temporary response posts and community hubs, where should we place them to reach more of the represented demand within a modeled ten-minute drive?

I use real public data: roughly 450,000 FEMA Harvey registration records summarized by ZIP, 2020 Census population, HHS counts of electricity-dependent Medicare beneficiaries, public community-center locations, FEMA flood-map checks and modeled road travel. The larger map represents 189 ZIP-area points. Two verified public ERs are shown as fixed destination examples.

I trained a random forest to estimate the summed household members in registrations marked with flood damage. It uses already-reported registration totals and location, so it is a post-event estimator. I trained on 113 ZIP areas and tested on 38. The simple pooled-rate baseline had mean absolute error about 1,151 reported members per ZIP; the forest had about 1,147. That is only a 0.35% reduction. I would not claim the new model is reliable or substantially better than the baseline. This evaluation tells us we need stronger predictors and independent-storm validation.

The planner compares every eligible combination of candidate sites. Response posts use base-to-area driving; hubs use area-to-hub driving. The user can adjust the site budget, travel slowdown, and one unavailable site. A point flood screen removes mapped Special Flood Hazard Area candidates and unknown results, but does not establish that other sites are safe.

For supplies and service demand, I expose the assumptions: a scale relative to the historical case, the share seeking cooling, community and health services, and the number of supply days. The interface assigns assumed demand to selected hubs and exports every ZIP result with the assumptions. These are scenario calculations, not trained attendance or injury forecasts. The groups overlap and cannot be added as unique people.

The prototype helps demonstrate data integration and resource tradeoffs. Next I would seek de-identified EMS/ER visit counts, cleanup work requests, actual hub capacity and additional storms to test whether service demand and placement improve on a meaningful baseline.

## A one-minute demo

1. Run the training cell and show the baseline alongside the forest. Say the new people model barely outperforms the baseline. MAE is an average count error, not percent accuracy.
2. Run the interface with two response posts, three hubs, slowdown 1.0 and no closure. The default ML-priority scenario selects Northeast and El Franco Lee for response posts; the hubs add Acres Homes. Expected modeled coverage is approximately 15.79% of selected response weight and 20.41% of hub weight.
3. Close Northeast or increase slowdown. Explain the reselected sites and remaining uncovered points. Different priority metrics have different denominators, so their percentages are not directly comparable.
4. Change assumed participation or supply days. Show the hub load table and download the ZIP results. Say those percentages are assumptions, not measured service-use rates.

## Questions you may get

**Why did coverage fall from the earlier notebook?** The old example used ten high-registration points and another priority definition. This one covers a wider study area and a new target. The percentages are not an apples-to-apples performance comparison. Two bases cannot cover all of this region in ten minutes; the map makes that gap visible.

**Did you fine-tune an AI model?** I trained a numerical random forest from labeled examples. The detailed Track 1 packet allows statistical/ML methods and asks for a built and trained model. NLP or language-model fine-tuning is not required for this detailed track. The notebook contains the actual training and evaluation code.

**Does the notebook count 450,000 injured people?** No. Those are source registration records. They aggregate into 151 matched ZIP-level training examples. Household composition is summed across records, not deduplicated to verified distinct residents. Flood damage is not injury or a cleanup request.

**Can you predict health users now?** The GUI calculates scenarios from an assumed participation percentage. A trained health-service model needs historical service-use labels. HHS adds a useful at-risk population layer, not a count of future injuries or hospital arrivals.

**Why not train the injury model on NOAA?** NOAA reports storm-related injuries at event, county or forecast-zone level. It does not tell us ZIP-level ER visits, healthcare demand, or people assigned to a particular facility. The supplied three selected years are context, not sufficient labels for those finer claims.

**Are all 189 ZIPs estimated?** The map has 189 points. FEMA outcomes and the people model match 151. The remaining 38 are shown with missing estimates, never converted to observed zero need. Most unmatched points are outside the FEMA county slice. The source aggregate includes 449,932 records; 449,878 are in matched model ZIPs and 54 are outside.

**Can you move or build an ER?** This demonstration chooses temporary response/medical posts from existing community-center candidates. Existing hospitals stay fixed. New hospital construction would require demand forecasts, suitable sites, costs, licensing, staffing and capacity data.

**Are those actual cooling centers?** They are hypothetical activated hubs in this scenario. Opening, capacity, permission and staffing are unverified. Response posts and hubs may co-locate; shared capacity is not modeled.

**Does it guarantee a rescue in ten minutes?** No. It compares ordinary modeled driving to representative ZIP points. Dispatch, weather, road closures, access, rescue time and queues are not modeled.

**Is the map safe because FEMA marks X?** No. Outside mapped SFHA does not mean a site or its access roads are safe. The point screen is an example rule, not official site approval.

## Before submitting

- Add your name and project name to the notebook.
- Run all cells and keep the actual model metrics visible.
- Demonstrate controls, the map, selected sites, assumed demand and export.
- Share the notebook/code link with access enabled and keep a live demo ready.
- Check the current organizer instructions. The supplied packet requests a live demo, and the supplied Kaggle text lists a 4:30 PM Central deadline.
- Explain the source units and limits plainly; do not claim future-storm, injury, outage or ER-arrival prediction.
