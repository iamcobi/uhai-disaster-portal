# Your 90-second explanation

“After a Houston storm, response teams need to decide where to stage resources. UHAI Portal combines historical outages, tree and debris requests, damage descriptions, vulnerable-population context, and modeled driving times in one local planning dashboard.

I can compare Beryl, the May 2024 derecho, and Harvey. Red counties show recorded outage intensity; green-yellow heat shows tree or debris report density. These are historical observations, not future probabilities. Selecting a ZIP shows its nearest chosen resource sites and modeled travel times.

The planner chooses separate locations for ambulance staging, repair dispatch, cooling hubs and community/medical posts. It searches candidate combinations to maximize each role's priority weight within ten modeled drive minutes. I can change the number of sites, assume slower roads, or remove one candidate and compare the result.

There is also an experimental machine-learning component. I trained and evaluated a model of summed household members in Harvey flood-damage registration records, using already-reported registration counts and location. Its held-out mean absolute error is about 1,147 members per ZIP versus a baseline near 1,151. The improvement is only about 0.35%, so I label it exploratory. It does not predict injuries or future storms.

The supply calculator applies explicit participation assumptions to that historical model context. It helps compare food and service scenarios, without presenting assumptions as observed demand. The next steps are independent-storm validation, better service-use labels, capacity verification and storm-aware routing.”

# Demo order

1. Beryl outage counties → tree heat layer.
2. Place resources → reduce ambulance budget or increase slowdown → update.
3. Click a ZIP and explain outbound response versus inbound hub trips.
4. Damage evidence → search “roof” and show the original source.
5. People & supplies → change an assumption.
6. Model check → point to baseline and limitations.
7. 3D downtown is context only; export the scenario for review.

# Honest answers to likely questions

Does it use AI? Yes: the post-event household-member model is trained and evaluated locally. Resource placement uses explicit optimization, not a language model. This is training a small model; it is not fine-tuning a pretrained LLM.

Can it predict future outages or injuries? Not yet. There is no validated target dataset/model for those outputs in this prototype. Heatmap colors represent historical intensity or report density.

Is ten minutes guaranteed? No. It uses cached ordinary-road travel estimates and an optional slowdown multiplier. It does not account for real-time closures, access, response work, staffing or hospital capacity.

Can it place hospitals? It can compare temporary staging and community/medical posts. Existing ER examples remain fixed. Permanent hospital siting would require land, clinical demand, capacity, permitting and further analysis.

Can it estimate how much food is needed? It computes a scenario: assumed community participation × assumed days × 3 meals/day. This is not a nutrition recommendation or a validated demand forecast.

Does this satisfy the hackathon? Present the historical exploration, trained model, baseline evaluation and practical planner honestly. Consult the original hacker packet for required submission items and track-specific evaluation. This app does not claim to have implemented a validated future hurricane prediction system.
