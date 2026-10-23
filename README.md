# UHAI: Disaster Staging AI & Explainable Emergency Siting Engine

> **One-Line Summary**: An explainable AI command portal that predicts optimal high-ground staging locations for ambulances, cooling hubs, community shelters, and rescue outposts during severe floods, power grid collapses, and mass displacements.

[![Local Edge Ready](https://img.shields.io/badge/Architecture-Local%20Edge%20(No%20API%20Keys)-00f5c4?style=flat-square)](#)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-38bdf8?style=flat-square)](#)
[![MapLibre GL 3D](https://img.shields.io/badge/Geospatial-MapLibre%20GL%203D-fbbf24?style=flat-square)](#)
[![Tests Passing](https://img.shields.io/badge/Tests-10%2F10%20Green-34d399?style=flat-square)](#)

---

## 🎯 What We Are Building

When major hurricanes and flash floods strike Houston (such as **Hurricane Beryl**, **Hurricane Harvey**, or the **May 2024 Derecho**), rising bayous and flooded highway underpasses quickly cut off surface travel. If ambulances and rescue equipment remain at central hospital depots, they become trapped behind flood barriers, inflating emergency response latency from 8 minutes to over 25 minutes.

**UHAI** is an explainable geospatial AI system that:
1. **Predicts Optimal Staging Locations**: Solves a Maximal Covering Location Problem (MCLP) combined with $k$-median travel minimization to place:
   * 🚑 **Ambulance Staging & Standby Bases** (elevated waiting posts to bypass submerged bayous)
   * ❄️ **Cooling Hubs** (heat & power-loss refuge for vulnerable elders)
   * 🏛️ **Community Hubs** (displacement intake & feeding centers modeled for 3 hot rations/person/day)
   * 🚨 **Incident Response Outposts** (heavy debris, chainsaw squads, and flood-rescue equipment)
2. **Explainable AI (XAI)**: When clicking any placed asset or candidate, the AI transparently explains:
   * **Why it chose this location** (mathematical coverage and demographic priority).
   * **Tactical Standby & Waiting Protocol** (when and why ambulances should wait on high-ground aprons).
   * **Decision Factor Influence Breakdown** (FEMA Flood Safety 35%, 10-Min Travel Isochrone 30%, Medical DME Beneficiaries 20%, Arterial Redundancy 15%).
   * **Counterfactual Comparison** (why flood-prone sites like Kashmere MSC in Zone AE were disqualified).
3. **Dual-Tab Minimalist Architecture**:
   * **🎯 Staging Engine**: Full-screen interactive map, compact controls, 3D extruded skyscrapers, and instant explainability cards.
   * **📊 Regional Analytics Hub**: Dedicated tab for 189-ZIP placement ledgers, 311 damage evidence logs, disaster supply models, and machine learning holdout checks.

---

## 🔬 How the AI Works Under the Hood

### 1. Mathematical Formulation
$$\max_{S \subseteq C, |S|=k} \sum_{i \in \text{Areas}} w_i \cdot \mathbb{I}\left(\min_{j \in S} T_{ij} \le \tau\right) - \epsilon \sum_{i \in \text{Areas}} w_i \cdot \min_{j \in S} T_{ij}$$

* Maximizes coverage of weighted demand $w_i$ within $\tau = 10$ modeled drive minutes under storm slowdown conditions $s \in [1.0\times, 2.0\times]$.
* Siting weights derived from authoritative public datasets:
  * **Ambulances**: HHS emPOWER electricity-dependent Medicare beneficiaries (`Power_Dependent_Devices_DME`).
  * **Cooling**: Medical fragility scaled by CenterPoint historical peak outage customer rank.
  * **Community**: Historical FEMA Individual Assistance household displacement sums.
  * **Incident Response**: 48,000+ City of Houston 311 emergency work orders (fallen trees, downed live wires, drainage/flood calls).

### 2. Flood Hazard Constraint (FEMA NFHL)
* All candidates undergo FEMA Digital Flood Insurance Rate Map (DFIRM) screening.
* Sites in **Zone AE (100-Year Special Flood Hazard Area)**—e.g., *Kashmere MSC* and *Alief Center*—are disqualified ($excluded = \text{True}$) to prevent vehicles from drowning.
* Only sites in **Zone X (0.2% annual chance / minimal flood hazard)** are permitted.

### 3. Machine Learning Holdout Validation
* Scikit-Learn Random Forest Regressor trained on FEMA storm data to forecast displacement demand.
* Evaluated against holdout test areas (113 train / 38 test ZIPs) benchmarked against a baseline pooled rate.

---

## 🚀 Quickstart (Runs 100% Locally on Laptop)

No Google account, Colab, Mapbox token, or external API keys required. All models, cached geometry, and routing matrices execute locally.

1. **Start the Portal**:
   ```cmd
   START_PORTAL.cmd
   ```
   Or run directly with Python:
   ```bash
   .venv\Scripts\python.exe app.py
   ```
2. Open your browser at:
   ```
   http://127.0.0.1:8765/
   ```
3. **Run Automated Verification Tests**:
   ```bash
   .venv\Scripts\python.exe tests\test_portal.py
   ```

---

## 🏛️ Code Architecture

* `app.py`: High-performance HTTP backend with `/api/plan`, `/api/explain`, `/api/supplies`, and `/api/storm`.
* `engine/explainability.py`: Explainable AI engine computing tactical standby protocols, factor weights, and runner-up comparisons.
* `engine/storm_layers.py`: Siting optimization engine and multi-hazard layer processing.
* `engine/expanded_planner.py`: Combinatorial MCLP optimizer and supply demand arithmetic.
* `web/index.html`: Modern, minimal dual-view portal interface.
* `web/app.css`: Streamlined dark command-center design system.
* `web/app.js`: Reactive controller, MapLibre GL 3D extruded skyscraper rendering, and XAI inspector.

---

## 📜 Authors & Hackathon Track
* **CodeCoogs AI Hackathon Track 1**: Resource Optimization & Disaster Response for Houston Storms.
* Built by **I_amcobi** (`cobi9260@gmail.com`).
