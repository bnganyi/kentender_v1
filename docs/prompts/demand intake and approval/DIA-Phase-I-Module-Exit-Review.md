# DIA — Phase I module exit review (I1 / I2 / I3)

**Date:** 2026-04-23  
**Scope:** Demand Intake and Approval (`kentender_procurement` demand_intake) vs [8. DIA Master Checklist.md](./8.%20DIA%20Master%20Checklist.md), [7. Cursor Pack.md](./7.%20Cursor%20Pack.md) Phase I, [6. DIA Smoke Test Contract.md](./6.%20DIA%20Smoke%20Test.md) (reference).  
**Code changes:** None (review-only).

---

## I1 — Governance completeness review

| Cursor Pack question | Assessment |
|----------------------|------------|
| **1. All states implemented?** | **Complete.** Workflow states in `demand.json` / `demand.py` match PRD set: Draft, Pending HoD Approval, Pending Finance Approval, Approved, Planning Ready, Rejected, Cancelled. |
| **2. Invalid transitions blocked?** | **Complete.** `ALLOWED_STATUS_TRANSITIONS` + `validate` enforce transitions; lifecycle APIs are the supported mutation path. |
| **3. Reservations created/released correctly?** | **Complete** for designed paths: `approve_finance` creates reservation; reject/cancel paths release per `lifecycle.py` + budget services. Covered by BX5 / DIA integration tests. |
| **4. Approved / Planning Ready trustworthy and locked?** | **Complete.** B3 edit lock: only Draft/Rejected allow full header+items edit; Approved / Planning Ready locked from ad-hoc edits; `mark_planning_ready` is gated. |
| **5. Unplanned / Emergency governed?** | **Complete.** `validate_submission_gate` and type sync for `is_exception`; builder hides/shows impact and emergency justification; seeds include exception shapes. |
| **6. Work queues route each role?** | **Complete.** `queue_list.py` role + work_tab + queue_id filters; Desk pills aligned (incl. procurement rejected-tab fix). Row-level Demand permissions (`demand_permissions.py` + hooks) scope lists. |
| **7. Procurement Planning can trust output?** | **Complete with documentation debt.** Planning Ready carries reservation + strategy linkage on the record. **Risk:** landing KPI `frappe.db.count` may not apply the same row filter as list views — counts can diverge from visible rows under strict permissions; document or align if PP relies on KPI accuracy. |

### I1 summary

| Bucket | Items |
|--------|--------|
| **Complete** | States, transitions, budget gate + reservation, locks, exception types, queues + API protection, planning handoff. |
| **Missing** | Optional PRD **Auditor** read-only role (not present in `demand_intake` DocPerm grep); confirm against PRD §17 if still required. |
| **Risky** | KPI totals vs row-level permissions; Master checklist §8.6 wording vs implementation (**Pending HoD** stage is fully content-locked in v1 — stricter than the checklist line that only names “Pending Finance locked”; confirm this matches signed PRD / Cursor Pack B3). |
| **Must-fix before leaving DIA** | None identified for **core governance** if PRD accepts v1 HoD-stage lock and Auditor is explicitly out-of-scope. |

---

## I2 — UI/UX alignment review (vs DIA UI spec)

| UI spec theme | Assessment |
|---------------|------------|
| **1. Workbench vs generic list** | **Matches.** Injected shell: KPIs, work tabs, queue pills, filters, search, master–detail, role-aware copy. |
| **2. Minimal tabs, scalable queues** | **Matches.** Four work tabs + per-role queue sets; secondary queues scoped by tab (procurement rejected uses dedicated rejected queue). |
| **3. Detail panel decision-ready** | **Matches.** Sections A–F, badges, financial snapshot, actions from `dia_detail`; rejection/return/cancel context surfaced. |
| **4. Builder structured, not form-heavy** | **Mostly matches.** E2 field order + shell (back, title, badge, header actions); Frappe form underneath — acceptable for v1; further “cardification” is optional. |
| **5. Emergency / unplanned visible** | **Matches.** List accents + badges; detail exception flag; builder conditional fields. |
| **6. Action placement role/state aware** | **Matches.** Detail toolbar + form header RPCs aligned with D7; admin union where designed. |

### I2 summary

| Bucket | Items |
|--------|--------|
| **Matches** | Workbench pattern, queues, detail depth, exception signalling, actions. |
| **Missing** | Frappe standard **modals** for return/reject/cancel do not yet carry smoke-contract `dia-modal-*` test ids (Playwright uses roles/text where needed). |
| **Fix before signoff (nice-to-have)** | Extend Playwright from `test.fixme` to full flows for modal-heavy paths; optional UI polish from UI spec “quality bar” §13.3 if stakeholders want pixel-parity. |

---

## I3 — Module exit checklist (Master Checklist mapping)

Legend: **Pass** / **Partial** / **Fail** / **N/A**

### A. Domain and lifecycle

| Item | Result | Notes |
|------|--------|--------|
| Demand schema | **Pass** | Tracker A1–A4; PRD-aligned fields. |
| Item schema + totals | **Pass** | A2/A3; tests exist. |
| Transitions enforced | **Pass** | B1/B2; lifecycle whitelist. |
| Locks enforced | **Pass** | B3; HoD pending locked for edits (v1). |

### B. Integration

| Item | Result | Notes |
|------|--------|--------|
| Budget-line-first | **Pass** | C1 + builder E4. |
| Strategy linkage | **Pass** | Derived from budget line. |
| Finance budget check + reservation | **Pass** | C4/C5; BX tests. |
| Reservation release | **Pass** | C6 / lifecycle cancel & reject paths. |

### C. Workbench

| Item | Result | Notes |
|------|--------|--------|
| Landing | **Pass** | D1–D5 + Phase H testids. |
| Role queues | **Pass** | D3/D4; filter meta. |
| Filters + detail | **Pass** | D4/D6/D7. |

### D. Builder

| Item | Result | Notes |
|------|--------|--------|
| Create/edit draft | **Pass** | E1–E6; `demand_form.js`. |
| Exception fields | **Pass** | E5/E6. |
| Read-only when locked | **Pass** | E6 + B3. |

### E. Permissions

| Item | Result | Notes |
|------|--------|--------|
| Backend | **Pass** | F1 hooks + `demand_permissions.py`. |
| UI vs backend | **Pass** | F2 New Demand + hints. |
| Route/API protection | **Pass** | F3 `dia_access.py` on landing, queue, detail, lifecycle. |

### F. Seed and tests

| Item | Result | Notes |
|------|--------|--------|
| Seed packs | **Pass** | G1/G2; `test_dia_seed_phase_g`. |
| Automated tests (Python) | **Pass** | Broad coverage across phases in `demand_intake/tests`. |
| Smoke suite (Playwright) | **Partial** | Files exist per §16.1; **five** scenarios run green; **six** remain `test.fixme` — not full §16.2 coverage yet. |

### G. Downstream trust

| Item | Result | Notes |
|------|--------|--------|
| Planning Ready trustworthy | **Pass** | Status + `planning_status` + reservation metadata on record; no PP objects in DIA. |

### I3 summary

| Output | Content |
|--------|---------|
| **Pass/fail by section** | A–E **Pass**; F **Partial** (Playwright depth); G **Pass**. |
| **Blockers** | None for **code** exit if product accepts **Partial** smoke automation for v1. |
| **Recommended fixes before Procurement Planning** | (1) Implement remaining Playwright scenarios or accept manual UAT for those paths. (2) Resolve KPI vs permission-query consistency if PP consumes KPIs. (3) Confirm Auditor / HoD-lock wording vs PRD. |

---

## Sign-off recommendation

- **Ready to proceed to Procurement Planning (engineering):** **Yes**, subject to product sign-off on **Partial** Playwright coverage and the documented **risks** above.
- **Formal “module complete” per strict reading of Master Checklist §16.2:** Treat as **conditional** until `test.fixme` DIA specs are implemented or waived in writing.

---

## Tracker

Update [DIA-Implementation-Tracker.md](./DIA-Implementation-Tracker.md): **I1**, **I2**, **I3** → **Done**, linking this file.
