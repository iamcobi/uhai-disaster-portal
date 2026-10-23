# Houston Storm Impact & Resource Planner

Open Houston_Storm_Layers.ipynb in Google Colab with File → Upload notebook, then Runtime → Run all. All code and cached datasets are bundled inside the notebook. There is no separate dataset upload or code insertion. Enable the existing CARTO_API_KEY Secret for this notebook if you want street tiles; calculations and markers still work without it, and no key-entry prompt is used.

The first interactive GUI adds historical outage and tree/debris heatmaps, source damage descriptions, a date-checked utility-feed refresh, and independent ambulance, repair, cooling and community/medical placement controls. The original household/supply GUI remains available in a later cell. The optional source ZIP is an editable backup.

Read data/STORM_LAYER_SOURCES.md before presenting. Red records historical outage intensity, not a future probability. Green-yellow represents tree/debris report density, not predicted tree strikes. No future outage or tree-strike probability model is fitted or validated. Unknown causes and missing data remain unknown. The source feed is old at packaging time and is marked accordingly. Existing hospitals remain fixed examples; temporary posts are chosen among supplied centers.

The included numerical household model is trained and evaluated separately; its reference improvement over a simple baseline is only 0.35%, so it remains experimental. It does not predict outage or tree risk.
