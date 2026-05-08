# STD production readiness — programme implementation tracker

**Purpose:** Single cross–workstream view: health, last update, and pointers to per–workstream trackers and issue logs.

**Detailed execution** lives in each workstream’s `IMPLEMENTATION_TRACKER.md` (tickets, evidence, design sign-off).

---

## Workstream index

| Workstream | Scope (summary) | Tracker | Status (rollup) |
|------------|-----------------|---------|-----------------|
| **1** — STD Template Governance and Lifecycle | Import → validate → approve → activate; versioning; immutability; usage lock; audit/snapshot; admin UX | [`workstream-1/IMPLEMENTATION_TRACKER.md`](workstream-1/IMPLEMENTATION_TRACKER.md) | **Done (implementation + doc 8 §C gate)** — STD-GOV-001–014 + [evidence](workstream-1/STD-GOV-doc8_smoke_environment_and_results.md) + [review](workstream-1/STD-GOV-014_implementation_review_report.md). **§A** product/architecture sign-off in that tracker is separate. |
| **2** — Official Library UI (admin revamp) | Library landing; package import wizard; validation/bundle preview; usage/supersession; advanced hidden; audit | [`admin-revamp/IMPLEMENTATION_TRACKER.md`](admin-revamp/IMPLEMENTATION_TRACKER.md) | **Implementation complete (tracker)** — §B tickets Done; §C/D evidenced; **§E** [0700 review](admin-revamp/STD-LIB-0700_implementation_review_report.md) + [REST mapping](admin-revamp/STD-LIB-REST-mapping.md) (2026-05-08). [Smoke results](admin-revamp/STD-LIB-section-C_smoke_environment_and_results.md). |

Rollup **Status** is informational only; the workstream tracker rows are authoritative.

**Agent rules (links from `docs/prompts/std-production-readiness/`):** [TDD / Playwright](../../../../../.cursor/rules/kentender-tdd-playwright-quality-gate.mdc) · [bench + Node](../../../../../scripts/bench-with-node.sh) · [frappe-bench-node](../../../../../.cursor/rules/frappe-bench-node.mdc)

---

## Programme health

| Field | Value |
|-------|--------|
| Primary template (first production path) | `KE-PPRA-WORKS-BLDG-2022-04-POC` (WORKS) |
| Canonical governance specs | [`workstream-1/`](workstream-1/) documents 1–8 |
| Implementation pack (tickets STD-GOV-001 … STD-GOV-014) | [`workstream-1/7. std_template_governance_lifecycle_complete_cursor_implementation_pack.md`](workstream-1/7.%20std_template_governance_lifecycle_complete_cursor_implementation_pack.md) |
| Last programme tracker update | 2026-05-08 — Workstream 2 **§E** [STD-LIB-0700](admin-revamp/STD-LIB-0700_implementation_review_report.md) + [REST mapping](admin-revamp/STD-LIB-REST-mapping.md); §C/D; [admin-revamp tracker](admin-revamp/IMPLEMENTATION_TRACKER.md) |

---

## Cross-workstream dependencies (watch)

| Topic | Notes |
|-------|--------|
| `STD Template` DocType | Extended by Workstream 1; POC loader/engine assume current fields — migrations and regressions must run `test_std_works_poc_*` as applicable. |
| Handoff / seed (`STD-INT-*`) | `allowed_for_tender_creation` and lifecycle semantics may replace POC shortcuts; align `std_template_handoff_resolution` and seeds after STD-GOV-008. |
| Playwright | New governance Desk flows need specs under `apps/kentender_v1/tests/ui/` when UI ships (Workstream 1 doc 5 / pack §20). |
| Official Library UI (WS2) | Must not bypass Workstream 1 lifecycle/hash; pack’s `/api/std-engine/...` maps to Frappe whitelist/services; default Desk not SPA unless §A sign-off ([`admin-revamp/IMPLEMENTATION_TRACKER.md`](admin-revamp/IMPLEMENTATION_TRACKER.md)). |

---

## How to use

1. Open the **workstream tracker** for the active stream; execute tickets in order unless dependencies allow parallel prep.
2. Log blockers, deviations, and policy decisions in the workstream **`ISSUES_LOG.md`** (`STD-GOV-*` for Workstream 1; `STD-LIBU-*` for Workstream 2).
3. Update **Last tracker update** in this file when the programme rollup changes materially.
