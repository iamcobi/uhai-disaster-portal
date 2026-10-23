# UHAI Portal design direction

Purpose: a local Houston storm-planning workbench for one beginner presenting a hackathon prototype. The map is the primary workspace. Historical observations, modeling assumptions and unvalidated predictions remain visibly distinct.

Palette: bay navy #10273b, deep water #071724, sea glass #61d2bc, warm warning #efbd69, outage coral #ee796f, paper light #edf4f8. Translucent navy panels use blur with restrained rim highlights. Glass is user requested, not decoration layered over text.

Typography: locally bundled Manrope for interface, with tabular numerals for metrics. Sentence-case labels. One confident title and compact readable controls. No decorative uppercase labels or oversized statistic hero.

Layout:
Header: brand + storm selector + local-data status + source guide.
Main: [layer/resource controls | interactive map | area/site inspector].
Bottom: tabbed placements, source damage evidence, people/supplies, model evaluation.

Distinctive element: the storm map itself, with color-specific observed data overlays and optional 3D buildings when the online basemap is available. All panels frame that map rather than competing with it. Source dates and the historical label stay attached to the map. County outages never become ZIP probability tiles.

Accessibility: readable opaque-enough glass surfaces, visible focus, text/color dual legends, labeled range controls, reduced-motion support, keyboard tabs, mobile stacked panels. Tooltips never carry essential content alone. User actions update placement with clear busy and error states.

Brief review: retain the requested glass effect, but avoid repeated KPI-card decoration and neon sci-fi effects. Navy/water colors derive from storm-response geography. Building extrusions are geographic context only, not damaged-building predictions. Use a no-key basemap and provide a fully local data-only map when unavailable.
