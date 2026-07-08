# KE-PPRA-WORKS-BLDG-2022-04-POC

This folder contains the developer-controlled template package for the PPRA Works Standard Tender Document POC.

This package represents the PPRA Standard Tender Document for Procurement of Works — Building and Associated Civil Engineering Works, April 2022 revision, as a minimal but complete proof-of-concept configuration package.

This package is not a full legal digitization of the entire PPRA STD. It is used to prove the template-package, safe-configuration, validation, bidder-form activation, BoQ hook, and tender-pack rendering architecture.

Ordinary procurement officers must not edit this package. Tender-specific values shall be entered through controlled Frappe tender configuration screens.

Package files:

- manifest.json
- sections.json
- fields.json
- rules.json
- forms.json
- render_map.json
- sample_tender.json

Changes to this package must be reviewed before import or deployment.

## Acceptance evidence

Formal POC acceptance checklist, matrices, and sign-off placeholders live under
[`evidence/acceptance_pack.md`](evidence/acceptance_pack.md), with
[`evidence/issue_log.md`](evidence/issue_log.md) and optional Desk captures under
[`evidence/screenshots/`](evidence/screenshots/) (see `screenshots/README.md`).
This location is stable for handoff; it follows the Tender Management slice path
(**STD-POC-003**), not the Step 17 spec’s literal `procurement/std_templates/...` string.
