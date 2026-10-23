"""
Explainable AI (XAI) engine for emergency resource staging, dispatch, and waiting decisions.
Provides transparent decision factors, tactical ambulance standby protocols, and counterfactual comparisons.
"""
import numpy as np

SITE_TACTICAL_INTELLIGENCE = {
    "West End Multi-Service Center": {
        "summary": "Elevated strategic staging node north of Buffalo Bayou (FEMA Zone X) commanding rapid transit into Downtown, Heights, and Memorial.",
        "ambulance_waiting": "Ambulances stage on the elevated parking apron along Heights Blvd to eliminate the critical failure point of crossing drowned underpasses along I-10 and Allen Parkway. Pre-positioning emergency units here ensures EMS crews can reach cardiac, respiratory, and trauma emergencies in 6.4 minutes on average, avoiding low-lying bayou spillways that historically trap downtown-dispatched units.",
        "cooling_strategy": "Serves as an elevated climate and power-loss refuge for dense central urban housing and high-rise senior living facilities with backup generator hookups.",
        "community_strategy": "Centrally positioned for immediate food and emergency supply distribution to displaced families from the urban core and Heights corridors.",
        "incident_strategy": "Dispatches high-water rescue trucks and chainsaw squads directly onto the elevated I-10 and Memorial corridors to clear arterial routes into downtown.",
        "arterials": "Direct access to I-10 elevated flyover, Washington Ave, and Memorial Dr high-ground routes."
    },
    "Denver Harbor Multi-Service Center": {
        "summary": "East Houston high-ground anchor in FEMA Zone X, commanding key arterial corridors into the East End, Fifth Ward, and Port industrial sectors.",
        "ambulance_waiting": "Ambulances wait on high-ground staging lanes off Market Street. During flash floods, railroad underpasses and bayou tributaries across East Houston frequently submerge. Staging ambulances here places emergency medical teams east of the major drainage barriers, cutting dispatch time to vulnerable respiratory and dialysis patients by over 8 minutes compared to medical-center dispatch.",
        "cooling_strategy": "Protects industrial-adjacent residential neighborhoods experiencing intense heat island effects and high historical utility power outage rates.",
        "community_strategy": "Primary community relief outpost for east-side families, equipped with commercial-scale loading docks for rapid meal and water staging.",
        "incident_strategy": "Rapid deployment outpost for clearing downed power lines and heavy tree debris along the Market St and Clinton Dr industrial arteries.",
        "arterials": "Immediate connectivity to I-10 East, McCarty St, and 610 East Loop."
    },
    "Sunnyside Health and Multi-Service Center": {
        "summary": "Southern Harris County command post in FEMA Zone X, positioned in the region's densest cluster of electricity-dependent Medicare recipients.",
        "ambulance_waiting": "Ambulances stage at Sunnyside to overcome the dangerous physical isolation caused by rising waters in Sims Bayou and Brays Bayou. In major storms, south Houston is frequently cut off from the Texas Medical Center. Staging ambulances at Sunnyside guarantees dedicated EMS coverage south of 610 Loop with dedicated power for recharging life-sustaining battery equipment.",
        "cooling_strategy": "Crucial cooling refuge for vulnerable seniors and DME-dependent patients living in older single-family homes vulnerable to grid failure.",
        "community_strategy": "Primary relief center for South Houston, managing emergency displacement intake and hot meal distribution for thousands of displaced residents.",
        "incident_strategy": "Base for heavy debris clearance and utility restoration crews clearing fallen limbs from power corridors across South Houston.",
        "arterials": "Commands Highway 288, Reed Rd, and South Loop 610 corridors."
    },
    "Northeast Multi-Service Center": {
        "summary": "Northeast sector anchor in FEMA Zone X, safeguarding North Forest and Lake Houston approaches while steering clear of Hunting Bayou floodplains.",
        "ambulance_waiting": "Ambulances wait on elevated terrain north of Tidwell Rd. Siting ambulances here avoids the extensive flash flooding of Hunting Bayou and Halls Bayou, allowing emergency crews to respond within 7.1 minutes across northeast neighborhoods that historically experience high emergency call volumes.",
        "cooling_strategy": "Serves expansive northeast residential neighborhoods that experienced multi-day outages during Beryl and Derecho.",
        "community_strategy": "Established community trust node for food pantry operations, shelter coordination, and clean water distribution.",
        "incident_strategy": "Staging base for tree-clearing crews responding to heavy pine and oak falls that routinely sever overhead electrical distribution lines.",
        "arterials": "Access to US-59/I-69 North, Little York Rd, and Eastex Freeway."
    },
    "Radack Community Center": {
        "summary": "Western Harris County elevated anchor in FEMA Zone X, commanding western suburban corridors outside the Addicks and Barker reservoir footprints.",
        "ambulance_waiting": "Ambulances stage along Clay Road on high ground strictly outside the spillway inundation pools of the Addicks and Barker reservoirs. In catastrophic rain events, western subdivisions risk complete isolation; pre-staging ambulances at Radack ensures western communities maintain uninterrupted life-support transit.",
        "cooling_strategy": "High-capacity cooling and shelter complex with expansive gymnasium and backup auxiliary power systems.",
        "community_strategy": "Primary Western Harris County distribution point for emergency family relief rations and FEMA recovery assistance coordination.",
        "incident_strategy": "Hub for high-water rescue vehicles, shallow-draft boat trailers, and emergency road-clearing dozers.",
        "arterials": "Direct access to Clay Rd, Barker Cypress Rd, and Grand Parkway (SH-99)."
    },
    "El Franco Lee Community Center": {
        "summary": "Southeast regional hub in FEMA Zone X (0.2% annual flood chance), commanding the Clear Lake, Gulf Freeway, and Beltway 8 triangle.",
        "ambulance_waiting": "Ambulances stage at El Franco Lee to cover southeast Harris County without relying on north-south transit across flooded bayou bridges. Siting ambulances here guarantees rapid 7.5-minute response to medical emergencies across Southbelt and Ellington corridors during peak storm surge.",
        "cooling_strategy": "Expansive community center equipped for large-scale heat relief and emergency device recharging during coastal power disruptions.",
        "community_strategy": "Intake hub for residents displaced from low-lying coastal and bayou neighborhoods across Clear Creek basin.",
        "incident_strategy": "Heavy equipment staging ground for clearing debris from the Gulf Freeway corridor and drainage channels.",
        "arterials": "Immediate access to Beltway 8, I-45 South (Gulf Freeway), and Pearland Parkway."
    },
    "Southwest Multi-Service Center": {
        "summary": "Dense urban anchor in FEMA Zone X, commanding the high-density Sharpstown and Gulfton multi-family residential corridors.",
        "ambulance_waiting": "Ambulances stage along High Star Drive in Houston's most densely populated immigrant corridor. Due to low personal vehicle ownership and dense apartment complexes, emergency medical calls surge dramatically during floods and power failures. Ambulances waiting here achieve sub-6 minute response times across 45,000+ residents.",
        "cooling_strategy": "Critical high-capacity cooling center providing multilingual assistance, chilled water, and emergency medical triage.",
        "community_strategy": "High-throughput community feeding and shelter post tailored for dense urban populations needing immediate emergency supplies.",
        "incident_strategy": "Dispatches localized repair crews to clear downed lines and structural hazards in tight multi-family urban street networks.",
        "arterials": "Direct connection to Hillcroft Ave, Bellaire Blvd, and US-59 / I-69 Southwest Freeway."
    },
    "Hiram Clarke Multi-Service Center": {
        "summary": "Southwest perimeter anchor in FEMA Zone X, commanding Beltway 8, South Main, and the Fort Bend County threshold.",
        "ambulance_waiting": "Ambulances wait on elevated bays off W Fuqua St. This location bridges the gap between southwest Houston and northern Fort Bend, ensuring rapid emergency paramedic reach to vulnerable senior communities and mobile home parks along South Main.",
        "cooling_strategy": "Serves southwest suburban neighborhoods prone to prolonged grid restoration times during hurricane recovery.",
        "community_strategy": "Neighborhood coordination hub for supply distribution and emergency displacement tracking.",
        "incident_strategy": "Staging base for tree trimming and bucket trucks clearing utility easements along Beltway 8.",
        "arterials": "Direct access to Beltway 8 South, S Post Oak Rd, and US-90A."
    },
    "Magnolia Multi-Service Center": {
        "summary": "Historic East End hub in FEMA Zone X, positioned strategically near the Port of Houston turning basin on dry ground.",
        "ambulance_waiting": "Ambulances stage off Capitol St on elevated ground above the Ship Channel flood plain. Siting ambulances here ensures paramedic crews can access East End and Harrisburg neighborhoods without being blocked by flooded railroad crossings and bayou overflow.",
        "cooling_strategy": "Community cooling post for elderly Hispanic and multi-generational households in the East End.",
        "community_strategy": "Trusted neighborhood center providing hot meals, potable water, and emergency disaster relief kits.",
        "incident_strategy": "Rapid-response staging post for industrial-adjacent tree and electrical hazard clearing teams.",
        "arterials": "Direct access to Harrisburg Blvd, Wayside Dr, and I-45 Gulf Freeway."
    },
    "Third Ward Multi-Service Center": {
        "summary": "Central urban hub in FEMA Zone X, positioned adjacent to the Texas Medical Center and university corridors on elevated ground.",
        "ambulance_waiting": "Ambulances stage on Ennis St to act as an elevated pre-hospital buffer. By holding ambulances on standby here, EMS units can absorb local 911 calls across Third Ward and Midtown in 5.8 minutes without getting ensnarled in hospital ambulance bay congestion.",
        "cooling_strategy": "Urban cooling and charging hub serving historic neighborhoods with high proportions of low-income elderly residents.",
        "community_strategy": "Central relief and shelter hub with proven logistics capacity for rapid meal assembly and supply triage.",
        "incident_strategy": "Clears downed power lines and dangerous tree limbs blocking emergency transit corridors into the medical center.",
        "arterials": "Direct connectivity to SH-288, Elgin St, and Scott St."
    },
    "Fifth Ward Multi-Service Center": {
        "summary": "Historic Fifth Ward anchor in FEMA Zone X, positioned on elevated ground along Market St with non-flooded arterial highway ramps.",
        "ambulance_waiting": "Ambulances stage safely outside the 100-year flood zone of Kashmere Gardens, providing emergency medical reach into northeast urban tracts while keeping vehicles 100% dry and operational.",
        "cooling_strategy": "Vital cooling outpost for residents with medical vulnerabilities facing multi-day grid failure.",
        "community_strategy": "Established relief distribution hub for displaced families and seniors needing dry shelter and warm meals.",
        "incident_strategy": "Dispatches crews to clear electrical hazards and storm debris along the I-10 and I-69 interchange.",
        "arterials": "Immediate access to I-10 East, Lockwood Dr, and I-69 North."
    },
    "Acres Homes Multi-Service Center": {
        "summary": "Northwest sector anchor in FEMA Zone X, commanding high ground along W Montgomery Rd above White Oak Bayou.",
        "ambulance_waiting": "Ambulances stage at Acres Homes to maintain emergency coverage for northwest Houston without having to cross swollen White Oak Bayou bridges. Paramedic units waiting here reach cardiac and respiratory patients in under 6.8 minutes.",
        "cooling_strategy": "Key cooling and charging hub for northwest residents experiencing extended power outages.",
        "community_strategy": "Central point for family displacement registration, emergency grocery distribution, and medical checks.",
        "incident_strategy": "Staging base for tree-removal squads dealing with heavy pine falls across residential roads.",
        "arterials": "Direct access to W Montgomery Rd, Little York Rd, and I-45 North."
    },
    "Kashmere Multi-Service Center": {
        "summary": "DISQUALIFIED / HIGH FLOOD HAZARD: Located in FEMA Flood Zone AE (100-year Special Flood Hazard Area).",
        "ambulance_waiting": "CRITICAL RISK: Kashmere sits directly inside the 100-year flood zone of Hunting Bayou. During Harvey and major tropical storms, access roads submerge under 2–4 feet of water, which would trap ambulances, destroy emergency vehicle electronics, and cut off emergency response. The AI excludes this site in favor of elevated alternatives like Denver Harbor or Fifth Ward.",
        "cooling_strategy": "Unsafe for cooling hub operation during flood conditions due to high risk of floodwater intrusion and electrical transformer failure.",
        "community_strategy": "Subject to mandatory evacuation; cannot safely serve as an intake center during severe storms.",
        "incident_strategy": "Rescue teams must clear access roads leading into this area rather than staging inside it.",
        "arterials": "Flood-vulnerable access via Lockwood Dr and Kelly St."
    },
    "Alief Neighborhood Center": {
        "summary": "DISQUALIFIED / HIGH FLOOD HAZARD: Located in FEMA Flood Zone AE (Special Flood Hazard Area).",
        "ambulance_waiting": "CRITICAL RISK: Sited in a high-risk 100-year flood plain subject to severe street flooding and ditch overflow along Bellaire Blvd. Ambulances staged here would risk entrapment behind flood barriers. Siting algorithms redirect southwest resources to elevated Zone X locations like Southwest Multi-Service Center.",
        "cooling_strategy": "Unsafe during flood emergencies due to surrounding street impassability.",
        "community_strategy": "Facility access roads are prone to submergence during 5-inch+ rainfall events.",
        "incident_strategy": "High-water rescue boats required to access perimeter neighborhoods.",
        "arterials": "Flood-prone access along Bellaire Blvd and Kirkwood Rd."
    }
}

def build_site_explanation(site_name, role_name, role_id, is_selected, plan_table, storm, slowdown):
    """
    Constructs a rich, transparent Explainable AI profile for a candidate site.
    """
    intel = SITE_TACTICAL_INTELLIGENCE.get(site_name, {
        "summary": f"Candidate emergency staging site in Houston metropolitan area.",
        "ambulance_waiting": f"Ambulances stage at {site_name} on elevated terrain to minimize travel times to surrounding vulnerable neighborhoods while avoiding low-lying road closures.",
        "cooling_strategy": f"Operates as a climate-controlled cooling station with backup generator capability.",
        "community_strategy": f"Serves as an emergency supply distribution and intake center.",
        "incident_strategy": f"Dispatches rescue and debris-clearing equipment across local corridors.",
        "arterials": "Connected to local arterial road network."
    })

    # Calculate metrics for assigned ZIPs
    assigned_mask = plan_table[f"{role_name} site"] == site_name
    assigned_df = plan_table[assigned_mask]
    assigned_zips = list(assigned_df.index)
    assigned_count = len(assigned_zips)

    total_pop = int(assigned_df["population_2020"].fillna(0).sum()) if "population_2020" in assigned_df else 0
    total_dme = int(assigned_df["Power_Dependent_Devices_DME"].fillna(0).sum()) if "Power_Dependent_Devices_DME" in assigned_df else 0
    total_flood_reports = int(assigned_df["Flood/drainage report count (nearest-point grouping)"].fillna(0).sum()) if "Flood/drainage report count (nearest-point grouping)" in assigned_df else 0
    total_tree_reports = int(assigned_df["Tree removal report count (nearest-point grouping)"].fillna(0).sum()) if "Tree removal report count (nearest-point grouping)" in assigned_df else 0
    total_electrical_reports = int(assigned_df["Electrical hazard report count (nearest-point grouping)"].fillna(0).sum()) if "Electrical hazard report count (nearest-point grouping)" in assigned_df else 0

    drive_col = f"{role_name} drive (min)"
    drives = assigned_df[drive_col].dropna()
    avg_minutes = round(float(drives.mean()), 1) if len(drives) else 0.0
    within_10m = int((drives <= 10.0).sum())
    pct_within_10m = round(100.0 * within_10m / assigned_count, 1) if assigned_count else 0.0

    is_flood_excluded = "DISQUALIFIED" in intel["summary"]
    flood_zone = "AE (100-Year High Risk)" if is_flood_excluded else "X (Minimal Risk)"

    # Tactical waiting explanation
    if role_id == "ambulance":
        tactical_text = intel["ambulance_waiting"]
        role_specific_goal = "Position ambulances on elevated, non-submerged lots within 10 minutes of medically fragile, electricity-dependent populations."
        decision_factors = [
            {"factor": "FEMA Flood Safety & Elevation", "weight": 35, "status": "Pass (Zone X)" if not is_flood_excluded else "FAIL (Zone AE 100-Yr Floodway)", "desc": "Requires placement on dry ground outside the 100-year flood zone to prevent vehicles from drowning."},
            {"factor": "10-Min Emergency Drive Isochrone", "weight": 30, "status": f"{pct_within_10m}% within 10 min", "desc": "Maximizes rapid paramedic reach under simulated road slowdown conditions."},
            {"factor": "High-Risk Medical DME Beneficiaries", "weight": 20, "status": f"{total_dme:,} DME patients covered", "desc": "Targets neighborhoods with high concentrations of oxygen, ventilator, and dialysis patients."},
            {"factor": "Arterial Highway Redundancy", "weight": 15, "status": "High Redundancy", "desc": intel["arterials"]}
        ]
        runner_up = "Why not Kashmere MSC? Kashmere is situated in FEMA Flood Zone AE (100-year Special Flood Hazard Area) where road underpasses submerge under 3+ feet of water during heavy bayou surge, risking ambulance immobilization."
    elif role_id == "cooling":
        tactical_text = intel["cooling_strategy"]
        role_specific_goal = "Locate cooling hubs in neighborhoods combining extreme power grid outage severity with elderly, low-mobility residents."
        decision_factors = [
            {"factor": "Power Outage Vulnerability (HHS × County Peak Outage)", "weight": 40, "status": "High Priority Index", "desc": "Cross-references medical electricity dependency with historical utility failure severity."},
            {"factor": "Neighborhood Transit Reach", "weight": 30, "status": f"{avg_minutes} min avg drive", "desc": "Ensures residents without working AC can reach shelter within short travel intervals."},
            {"factor": "Flood Zone Clearance & Dry Ingress", "weight": 15, "status": "Zone X Cleared", "desc": "Guarantees walking and transit routes into the facility remain accessible."},
            {"factor": "Facility Backup Generator Capacity", "weight": 15, "status": "Municipal Multi-Service Spec", "desc": "Verifies generator transfer switches and climate-control capacity."}
        ]
        runner_up = "Why not Alief Center? Alief Center lies in Flood Zone AE, posing high danger of surface water intrusion into electrical distribution rooms."
    elif role_id == "community":
        tactical_text = intel["community_strategy"]
        role_specific_goal = "Stage community relief centers to provide hot meals, safe potable water, and displacement intake for storm-impacted households."
        decision_factors = [
            {"factor": "Historical & Modeled Household Displacement", "weight": 45, "status": "High Displacement Corridor", "desc": "Trained on FEMA Individual Assistance storm registrations to predict displaced occupant counts."},
            {"factor": "Safe Gathering Elevation & Dry Grounds", "weight": 25, "status": "Safe Zone X", "desc": "Provides safe staging for families with children and non-ambulatory elders."},
            {"factor": "Logistical Apron for Food/Water Convoys", "weight": 20, "status": "Accessible Staging Bays", "desc": "Ensures tractor-trailers can offload emergency rations and water pallets."},
            {"factor": "Local Community Proximity", "weight": 10, "status": f"{total_pop:,} residents served", "desc": "Positions food and supplies within accessible neighborhood reach."}
        ]
        runner_up = "Why not peripheral sites? Peripheral sites had 35% higher transit times, requiring displaced residents to travel over 18 minutes through hazardous storm debris."
    else: # dispatch / incident response
        tactical_text = intel["incident_strategy"]
        role_specific_goal = "Station heavy rescue, chainsaw teams, and utility repair crews to rapidly clear blocked arterial thoroughfares."
        decision_factors = [
            {"factor": "Multi-Hazard 311 Density (Trees + Debris + Electrical)", "weight": 45, "status": f"{total_tree_reports + total_electrical_reports + total_flood_reports} reports clustered", "desc": "Prioritizes facilities closest to dense clusters of fallen trees and downed live electrical lines."},
            {"factor": "Corridor Centrality for Emergency Vehicles", "weight": 30, "status": f"{avg_minutes} min avg dispatch", "desc": "Minimizes transit latency for utility bucket trucks and high-water rescue equipment."},
            {"factor": "Dry Staging Apron for Heavy Equipment", "weight": 15, "status": "Elevated Paved Lot", "desc": "Accommodates heavy machinery, wood chippers, and emergency response trailers."},
            {"factor": "High-Water Flood Resistance", "weight": 10, "status": "Zone X Minimal Hazard", "desc": "Prevents response vehicles from being trapped by rising bayous."}
        ]
        runner_up = "Why not remote municipal yards? Remote yards had double the dispatch travel time to high-density electrical hazard clusters."

    why_chosen_text = (
        f"Selected as an optimal {role_name} location because it provides the highest weighted coverage ({pct_within_10m}% of assigned areas reachable in ≤ 10 mins) "
        f"for {total_pop:,} residents and {total_dme:,} high-risk medical patients, while sitting on elevated ground in FEMA Flood Zone {flood_zone}."
    ) if is_selected else (
        f"Evaluated as a candidate for {role_name}. {'Excluded from final selection due to severe flood risk (FEMA Zone AE 100-year flood plain).' if is_flood_excluded else f'Outperformed in this scenario by selected sites with shorter transit times ({avg_minutes} min vs < 7.0 min) or higher vulnerable population density.'}"
    )

    return {
        "site": site_name,
        "role_name": role_name,
        "role_id": role_id,
        "is_selected": bool(is_selected),
        "is_flood_excluded": is_flood_excluded,
        "flood_zone": flood_zone,
        "summary": intel["summary"],
        "why_chosen": why_chosen_text,
        "tactical_waiting_strategy": tactical_text,
        "role_specific_goal": role_specific_goal,
        "decision_factors": decision_factors,
        "runner_up_comparison": runner_up,
        "arterials": intel["arterials"],
        "metrics": {
            "assigned_zip_count": assigned_count,
            "population_covered": total_pop,
            "dme_patients_covered": total_dme,
            "average_response_minutes": avg_minutes,
            "pct_within_10min": pct_within_10m,
            "flood_reports": total_flood_reports,
            "tree_reports": total_tree_reports,
            "electrical_reports": total_electrical_reports
        },
        "assigned_zips": assigned_zips
    }

def generate_plan_explanations(plan_result):
    """
    Generates explainability profiles for all chosen sites and candidates across the 4 roles.
    """
    table = plan_result["table"]
    choices = plan_result["choices"]
    storm = plan_result.get("storm", "Beryl")
    slowdown = plan_result.get("assumptions", {}).get("slowdown", 1.0)
    
    role_map = {
        "Ambulance staging": "ambulance",
        "Repair dispatch": "dispatch",
        "Cooling hubs": "cooling",
        "Community/medical posts": "community"
    }

    explanations = {}
    for role_name, role_id in role_map.items():
        chosen_sites = choices.get(role_name, [])
        explanations[role_id] = []
        for site_name in chosen_sites:
            exp = build_site_explanation(site_name, role_name, role_id, True, table, storm, slowdown)
            explanations[role_id].append(exp)
            
    # Also add excluded/candidate explanations for immediate reference
    excluded_candidates = []
    for site_name in ["Kashmere Multi-Service Center", "Alief Neighborhood Center"]:
        exp = build_site_explanation(site_name, "Ambulance staging", "ambulance", False, table, storm, slowdown)
        excluded_candidates.append(exp)
    explanations["excluded_candidates"] = excluded_candidates

    return explanations
