<!--
  Evidence for Rectification Tracker §13 — R8-005 / LV-R8-BE-05
-->
## Goal

Automate **PLC-SMOKE-BE-005**: after the WORKS PLC load at **`TENDER_PUBLISHED`**, **`get_journey_evidence_timeline("JRN-MOH-2026-001")`** returns **base handoff-backed events in chronological order**, with **no fabricated closing/opening events** (those handoff cards are absent in the base checkpoint) and **no “Addendum Issued” rows** unless real **`Tender Addendum`** records exist — matching cursor pack §15.1 and **R3-015** (TL-004 / TL-005 / TL-006).

**Note:** The seed spec table **JRN-TEST-006** still says “8 events”; the implemented contract (**R3-015**, `evidence_timeline.py`) is **seven** events from the seven **`BASE_HANDOFF_CODES`** cards at base checkpoint. This smoke locks in the **implemented** seven-event spine; reconcile the spec separately if product still wants eight.

## What was verified

| Step | Check |
|------|--------|
| PLC | **`load_procurement_lifecycle_works_master(reset=True, checkpoint="TENDER_PUBLISHED")`** succeeds; **`OPENING_HANDOFF_CODES`** cards **not** in DB. |
| Order | **`occurred_at`** values are **strictly ascending** (sorted order). |
| Spine | Non-null **`handoff_code`** events match **`BASE_HANDOFF_CODES`** in order (**STRATREF** … **PUBCERT**). |
| Count | **`len(timeline) == 7`** and equals count of handoff-backed events (no extra addendum rows). |
| No fabrication | No **`CLOSECERT-` / `OPENREADY-`** handoff codes; **no** **`Addendum Issued`** events for base. |
| Shape | Each event has pack §9.5 keys (**TL-002**). |

## Evidence submitted (automated)

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_r8_005_plc_smoke_be_005_evidence_timeline_order
```

**Last run (2026-05-16, local bench):** `Ran 1 test … OK` — `test_plc_smoke_be_005_timeline_order_base_handoffs_only` in ~8.3s.

## Related references

- **PLC-SMOKE-BE-005** — cursor pack §15.1.
- **R3-015** — `evidence_timeline.py`, `test_r3_015_evidence_timeline.py`.
- **R7-001** — journey evidence timeline product stream (when UI lands).
