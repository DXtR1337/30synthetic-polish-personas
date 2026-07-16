# Third-party materials

This package separates licensing by material type:

| Material | Author | License in this package |
|:---|:---|:---|
| Analysis and collection code (`*.py`) | M. Wiencek | MIT |
| Persona biographies (`synthetic/<persona>.md`), TCTM-22/57 vignettes, scored data, tables, manifests | M. Wiencek | CC BY 4.0 |
| Published psychometric instruments (DBZ-R, MentS-PL, KPP, TIPI-PL) | their respective authors | **not covered** by this package's licenses |

The scored CSV files contain only derived scores (item-level agreement flags,
scale means, z-scores) — no verbatim item content of the third-party
instruments. The collection scripts construct the battery from local
instrument files that are **not distributed** in this package; to re-run a
collection you must supply legally obtained copies of the instruments
locally.

The raw per-run artifacts (exact prompts and responses, deposited separately
per the Availability statement) contain verbatim instrument items; their
redistribution status is governed by the instruments' rights holders, and
access may be restricted accordingly rather than released under CC BY.

Instrument sources (see the manuscript's References for full citations):
- DBZ-R — Polish adaptation of the ECR-R (attachment dimensions)
- MentS-PL — Polish adaptation of the Mentalization Scale
- KPP — Polish Need for Cognition questionnaire
- TIPI-PL — Polish adaptation of the Ten-Item Personality Inventory
