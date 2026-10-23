# HERP · Houston ER Placer
## Minimalist 6-Slide Executive & Technical Briefing
*AI-Powered Land Prediction & Emergency Staging Optimization for Greater Houston Disasters*

---

### Slide 1: Mission & The Core Problem
#### Where Can Emergency Infrastructure Be Built Before the Flood Arrives?

* **The Reality:** During catastrophic hurricanes (Harvey, Beryl, Derecho), downtown medical complexes and municipal dispatch yards are physically cut off by rising bayous and flooded underpasses.
* **The Siting Challenge:** Disaster planners cannot rely on already built, compromised municipal buildings. We must predict **open land parcels and staging aprons** where:
  * Ambulances can wait safely on elevated, dry terrain without drowning.
  * Rapid-deployment emergency response buildings can be erected.
  * Community relief and cooling/power hubs can be deployed to shelter displaced families.
* **The Goal:** An automated AI platform that analyzes open land across all 9 Greater Houston counties to predict the highest-survival locations to build and stage emergency infrastructure.

---

### Slide 2: AI & Data Science Methodology
#### Predicting Optimal Land via Multi-Objective Optimization

* **1. High-Hazard Land Exclusion:** Every land parcel intersecting FEMA Flood Zone AE (100-year floodway) is automatically disqualified to prevent vehicle and personnel entrapment.
* **2. Multi-Layer Demand Weighting:**
  * **Ambulance Staging:** HHS Medicare power-dependent patient density (oxygen, ventilators, dialysis).
  * **Emergency Response Outposts:** Multi-hazard 311 distress report clusters (fallen trees + downed powerlines + debris).
  * **Cooling & Power Hubs:** Historical county peak grid failure severity × low-mobility elderly populations.
  * **Community Relief Hubs:** Random Forest regression trained on FEMA Individual Assistance storm registrations.
* **3. Combinatorial Optimization:** Solves an NP-hard facility location problem to choose the exact land coordinates that maximize reach within a strict 15-minute response target under 2.0× flood slowdown.

---

### Slide 3: Outskirts & Distant Areas
#### Siting Land Across Greater Houston's Outer Perimeter

* **Beyond Downtown:** Greater Houston spans over 10,000 square miles. Focusing only on the central urban core leaves millions in outer suburbs stranded when major bayou bridges submerge.
* **Key Outskirts Land Anchors Identified:**
  * **West Houston & Katy Outskirts (Radack Corridor):** Open high ground commanding I-10 West and Grand Parkway TX-99, protecting communities west of Addicks and Barker reservoirs.
  * **Northwest Corridor (Acres Homes / Cypress Border):** Elevated dry land providing uninterrupted EMS transit north of swollen White Oak Bayou.
  * **South / Clear Lake / Pearland Outskirts (El Franco Lee Corridor):** Strategic open staging bays commanding Beltway 8 and Highway 35 near Galveston Bay.
  * **Southwest / Fort Bend Outskirts (Hiram Clarke / Fuqua Corridor):** Critical staging parcel protecting vulnerable Medicare patients across the Fort Bend threshold.
* **Regional Camera Navigation:** 8 sector presets let incident commanders immediately inspect land suitability across all 9 regional counties.

---

### Slide 4: Real-World Hurricane Conditions
#### 2.0× Road Slowdown & The 15-Minute Survival Target

| Planning Metric | Traditional City Assumption | HERP Disaster Simulation |
| :--- | :--- | :--- |
| **Road Conditions** | Clear, free-flowing dry traffic | **2.0× Hurricane Flood Slowdown** (Automated) |
| **Response Window** | 30–45 minute baseline | **Strict ≤ 15-Minute Target Isochrone** |
| **Elevation Standard** | General municipal boundaries | **FEMA Zone X Dry Ground Only** |
| **Resource Scaling** | Fixed arbitrary fleet cap | **Unlimited Dynamic Resource Scaling** |

* **Why 15 Minutes?** Cardiac, respiratory, and oxygen-depleted medical emergencies suffer exponential mortality beyond 15 minutes of transit latency.
* **Why 2.0× Slowdown?** Reflects real-world street flooding, fallen oak trees, downed power transformers, and bridge closures observed during Hurricane Beryl.

---

### Slide 5: Minimalist Command Terminal UI
#### High-Contrast Visual Intelligence & Decision Transparency

* **Tactical Green ✖ Placement Markers:** When the AI calculates optimal land staging locations, bold glowing **Green ✖** badges mark the exact coordinates across the region.
* **CartoDB Dark Matter Basemap:** High-performance, watermark-free dark cartography displaying all 9 Greater Houston counties, street names, bayous, highways, and suburban developments.
* **Explainable AI (XAI) Drawer:** Clicking any predicted site or green ✖ pin reveals:
  * *Why the AI Chose This Location:* Exact percentage of population covered in ≤15 minutes.
  * *Tactical Waiting Strategy:* Where ambulances stage and why they avoid bayou bridges.
  * *Decision Influence Factors:* Visual weights for flood safety, DME medical density, and road redundancy.
  * *Disqualification Audit:* Transparently details why floodway sites (e.g., Kashmere, Alief) were rejected.
* **Instant Directives & Printing:** One-click `🖨️ Print Directive` formats a printable Incident Command Directive for emergency field distribution.

---

### Slide 6: Summary & Operational Impact
#### Key Takeaways

1. **Predicting Where to Build, Not Just Where to Go:** Evaluates open, unbuilt land parcels to stage temporary emergency buildings, vehicle waiting lots, and relief shelters.
2. **Scientifically Defensible:** Trained on FEMA storm data, verified with NOAA damage narratives, and constrained by FEMA flood boundaries.
3. **100% Local & Edge-Native:** Runs locally on laptop CPU with zero cloud dependencies, zero external mapping tokens, and complete offline disaster resilience.

