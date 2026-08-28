# Package index — IT-EQUIPMENT-OPEN-V1, Version 1.0 (KEBS fixture)

Per STD-TPL-001 v0.3 §11.3 and §14 Pass 5 step 6: the separate Invitation notice, the issued Tender package, and the controlled technical specification are listed distinctly. The notice may be released alongside the same approved Tender, but it is not a file within the issued Tender package.

## Publication notice (not part of the issued Tender package)

| File | Purpose |
|---|---|
| `kebs_invitation_expected.pdf` | The separate Invitation to Tender publication notice for `TND-KEBS-2026-0001`, rendered from `02_master/invitation_to_tender.html`. |

## Issued Tender package

| File | Purpose |
|---|---|
| `kebs_expected.pdf` | The complete issued Tender document (cover, contents, Sections I–VIII), rendered from `02_master/complete_tender.html`. 44 pages. Each page carries a footer with the Tender reference and page number (`TND-KEBS-2026-0001 — Page N of 44`), added at PDF-generation time via `wkhtmltopdf --footer-center`; not part of the Jinja template. |
| `kebs_technical_specification.pdf` | The approved, controlled technical-specification document for this Tender (Section V cover sheet references it by title, version, approval date and digest — see below). It is published in the same Tender package, not embedded in `kebs_expected.pdf`. |

## Technical specification metadata (as recorded in `kebs_input.json`)

| Field | Value |
|---|---|
| Title | ICT Equipment Technical Specification |
| Version | 1.0 |
| Approval date | 15 September 2026 |
| Publication filename | `kebs_technical_specification.pdf` |
| File digest (SHA-256) | `f3556acf6d3809a981bc625082fd12eb63b13a06d541f6a231db66918b8d5326` |

No file outside the three listed above is part of this fixture package. `kebs_input.json` and `render_fixture.py` are curation-only inputs/tooling, not package deliverables.
