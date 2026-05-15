# G0-004 — TM2 legal control confirmation

**Parent gate:** [G0-004](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md) (§5 row).  
**Atomic ticket:** LV-G0-004-01  
**Controlling product rule:** Rectification tracker preamble — TM2 legal behaviour remains canonical; rectification must not weaken TM2 controls.

---

## Evidence summary (§3.2 template)

```text
Implementation Evidence:
- TM2-surface guard (no legacy Procurement Tender document API on curated paths):
  kentender_procurement/kentender_procurement/tender_management/audit/p11_04_tm2_surface_procurement_tender_scan.py
  (includes services/planning_tender_handoff_*.py on the package→TM2 release chain; G0-004 scope extension).
- TM2-surface quoted literal ban (Python paths above + TM2 v2 desk JS):
  kentender_procurement/kentender_procurement/tender_management/audit/p11_05_tm2_surface_procurement_tender_literal_scan.py

Test Evidence:
- bench --site kentender.midas.com run-tests --app kentender_procurement \
    --module kentender_procurement.tender_management.tests.test_p11_04_tm2_surface_no_procurement_tender
  Result: OK (1 test, ~0.02s) — 2026-05-15 agent run.
- bench --site kentender.midas.com run-tests --app kentender_procurement \
    --module kentender_procurement.tender_management.tests.test_p11_05_tm2_surface_no_procurement_tender_literal
  Result: OK (1 test, ~0.02s) — 2026-05-15 agent run.

Result:
- G0-004 and LV-G0-004-01 **Accepted** in [implementation tracker](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md) §5 / §18.1.

Review Notes:
- Decision: **Accepted** (TM2 legal control / no legacy Procurement Tender on TM2 surface paths).
```

---

## Scope (what this gate proves)

1. **In scope:** TM2-first Python entrypoints and desk JS listed by **P11-04 / P11-05** (including **`services/planning_tender_handoff_*.py`**) must not call `frappe.get_doc` / `frappe.new_doc` on **`Procurement Tender`** and must not contain a quoted **`"Procurement Tender"`** / `'Procurement Tender'` literal (P11-05), so the **planning → release → TM2** path cannot silently reintroduce the legacy DocType API on that surface.

2. **Out of scope (explicit):** Other modules may still mention `Procurement Tender` in comments, legacy officer mapping, or DocType controllers until full DocType removal (see P11-04 module docstring). That does **not** satisfy “TM2-only flows” in the sense of this gate; those areas are outside the expanded scan set.

---

## Tracker cross-walk

| Ticket | Evidence |
|--------|----------|
| LV-G0-004-01 | This file §3.2 + audit modules + test modules named above |
