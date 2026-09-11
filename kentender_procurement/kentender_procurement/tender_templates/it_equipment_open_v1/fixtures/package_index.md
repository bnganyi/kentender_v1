# Package index — IT-EQUIPMENT-OPEN-V1, Version 1.1 (Ministry of Health fixture)

Per STD-TPL-001 v0.5 §11.3 and §14 Pass 5 step 6: the separate Invitation notice and the issued Tender package are listed distinctly. The notice may be released alongside the same approved Tender, but it is not a file within the issued Tender package. There is **no separate technical-specification file** in this release — Section V's Schedule of Requirements is generated directly from the structured technical requirement rows inherited from the authorised Requisition handoff (§8.4).

## Publication notice (not part of the issued Tender package)

| File | Purpose |
|---|---|
| `moh_invitation_expected.pdf` | The separate Invitation to Tender publication notice for `TND-MOH-2027-033`, rendered from `02_master/invitation_to_tender.html`. 1 page. |

## Issued Tender package

| File | Purpose |
|---|---|
| `moh_expected.pdf` | The complete issued Tender document (cover, contents, Sections I–VIII), rendered from `02_master/complete_tender.html`. 44 pages. Each page carries a footer with the Tender reference and page number (`TND-MOH-2027-033 — Page N of 44`), added at PDF-generation time via `wkhtmltopdf --footer-center`; not part of the Jinja template. |

## Section V structured-content confirmation (§8.4)

Section V.3 Technical Requirements renders the eleven rows `TECH-001` … `TECH-011` of `moh_input.json` exactly once each, with unchanged label, comparison, value, unit and scope; Section V.4 renders the package-level warranty and support values; Section V.6 renders the five acceptance rows `ACC-001` … `ACC-005`. Section V.1 renders the two authorised Requisition items `RQI-001` and `RQI-002` (100 + 150 Each, one shared specification) as one line of 250 Each with both item IDs shown, per §8.4(2) and SEED-001 v1.1 §5.2. Section IV's Technical Compliance Response carries one supplier response row per technical requirement ID. No PDF, cover sheet, publication filename or file digest stands for the technical specification.

No file outside the two listed above is part of this fixture package. `moh_input.json` and `render_fixture.py` are curation-only inputs/tooling, not package deliverables.
