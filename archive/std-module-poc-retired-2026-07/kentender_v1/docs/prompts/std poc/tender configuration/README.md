# Procurement Officer Tender Configuration POC — folder index

**Workstream:** Procurement Officer Tender Configuration POC (officer-facing guided tender setup on top of STD-WORKS-POC + Admin Console foundation).

**Template code (POC):** `KE-PPRA-WORKS-BLDG-2022-04-POC`

## Artefacts in this folder

| Artefact | Purpose |
|----------|---------|
| [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md) | Step status, evidence, acceptance pointers for officer POC (specs 1–9 + implementation sequence). |
| [`ISSUES_LOG.md`](ISSUES_LOG.md) | Decisions, deviations, blockers — ids **`STD-OFFICER-NNN`**. |
| [`1. procurement_officer_tender_configuration_poc_scope_document.md`](1.%20procurement_officer_tender_configuration_poc_scope_document.md) … [`9. …smoke_test_specification.md`](9.%20procurement_officer_tender_configuration_poc_smoke_test_specification.md) | Authoritative specifications (read before coding). |

## Parent / sibling trackers

- **STD-WORKS-POC:** [`../IMPLEMENTATION_TRACKER.md`](../IMPLEMENTATION_TRACKER.md) · [`../ISSUES_LOG.md`](../ISSUES_LOG.md) (`STD-POC-*`)
- **STD Administration Console POC:** [`../admin console/IMPLEMENTATION_TRACKER.md`](../admin%20console/IMPLEMENTATION_TRACKER.md) (`STD-ADMIN-*`)

## Code (expected slice)

Primary implementation is expected under `kentender_procurement/.../tender_management/` (same slice as STD POC engine), with optional module name `officer_tender_config.py` per doc 8 — record path deviations as **`STD-OFFICER-NNN`** in [`ISSUES_LOG.md`](ISSUES_LOG.md).
