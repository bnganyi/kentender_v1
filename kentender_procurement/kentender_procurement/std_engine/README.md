# STD Engine (`kentender_procurement.std_engine`)

**Milestone 1:** IT STD read model — import-first, immutable-first, read-only inspection.

## Boundary

This module owns:

- STD package import (dry-run + commit)
- Persistent validation findings and audit events
- Read-only STD Engine APIs for Desk iframe wiring

**Tender Management must not** host STD import logic or canonical STD DocTypes.  
`tender_management` may consume STD Engine outputs later (e.g. tender STD binding).

Legacy STD POC code under `tender_management/services/std_template_loader.py` remains a retired stub.

## Layout

```text
std_engine/
  api/          @frappe.whitelist read + import HTTP scaffold (BE-04a, BE-06+)
  package_import/       package reader, dry-run, commit (BE-02–BE-04)
  validation/   persistent validators (BE-05)
  audit/        audit event writers (BE-04+)
  services/     shared read-model helpers
  doctype/      Frappe DocTypes (BE-01)
  tests/        unit + integration gates
```

## Seed artifacts

- Zip: `apps/kentender_v1/docs/std-prod-impl/data/KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip`
- PDF: `apps/kentender_v1/docs/std-prod-impl/data/DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.pdf`

## Tracker

`apps/kentender_v1/docs/std-engine/BE_IMPLEMENTATION_TRACKER.md`
