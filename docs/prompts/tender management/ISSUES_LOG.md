# Tender Management v2 — ISSUES_LOG

**Canonical log** for **`TM2-*`** issues (defects, deferrals, sign-offs, smoke gaps) tied to [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md).

Cross-post to [`../planning-to-tender-handoff/ISSUES_LOG.md`](../planning-to-tender-handoff/ISSUES_LOG.md) only when an item is shared with planning → tender handoff (`STD-INT-*`) or STD POC governance (`STD-POC-*` / `STD-ADMIN-*`).

---

## Closed meta

| ID | Type | Summary | Status |
|----|------|---------|--------|
| TM2-SMOKE-001 | meta | Smoke Contract added as [`8. tender_module_v_2_smoke_contract.md`](8.%20tender_module_v_2_smoke_contract.md); tracker **A8** + **§O** reconciled. | **Closed** (2026-05-12) |
| TM2-ADR-R01 | architecture | **R01:** Canonical **`TM2 Tender`**; reject extend `Procurement Tender` + reject hybrid; **remove `Procurement Tender`** and legacy tender code (**R07**, **P11-04**, **P11-05**). Approved Product/System Owner 2026-05-12. Evidence: [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md) §R R01. | **Closed** (2026-05-12) |

---

## How to log

1. Add a row under a dated section or component (Domain / Lifecycle / UI / Seed / Smoke).
2. Use **`TM2-NNN`** or topical prefixes (`TM2-DT-*` DocTypes, `TM2-UI-*`, `TM2-SEED-*`) — keep ids unique within this file.
3. Reference the id from **Notes** / **Evidence** in `IMPLEMENTATION_TRACKER.md`.
