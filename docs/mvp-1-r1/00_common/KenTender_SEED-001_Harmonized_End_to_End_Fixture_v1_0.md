# SEED-001 — Harmonized End-to-End Fixture

| Control | Value |
|---|---|
| Document ID | SEED-001 |
| Version | 1.0 |
| Date | 4 September 2026 |
| Status | Proposed for approval |
| Purpose | One canonical, cross-module fixture — Need through Strategy, Budget, Plan, Requisition and Tender — sufficient to exercise the approved `IT-EQUIPMENT-OPEN-V1` template end to end. Every downstream module's own seed contract is corrected to match this document; this document invents nothing that those seed contracts do not now also state. |
| Standards | Governed by KT-STD-001 v1.2. |

**Controlling decision:** One site is one Procuring Entity — Ministry of Health, `PE-MOH` — already the shared entity behind every approved KenTender document's fixtures except three: REQ-CHG-001, TPR-CHG-001 and the two STD template-curation documents, which were built against a separate, non-existent second entity, `PE-KEBS`. Two entities cannot coexist under the one-site-one-PE model this whole system is built on. `PE-KEBS` is retired. Every fact it carried — the item quantities, the specification depth, the delivery and evaluation timeline — is preserved, reassigned to Ministry of Health, and connected to the real Need, Strategic Objective and Budget Line that already exist in the approved MOH fixture set.

---

## 1. Why this document exists

Four separate, mutually inconsistent attempts at the same underlying scenario were found sitting across the approved document set, none connected to the others:

| Where | What it was | Problem |
|---|---|---|
| PLN-CHG-001 §14.8 (before this correction) | A combined "laptops" Plan Item, explicitly marked isolated | Combined two sources on **two different** Procurement Budget Lines, violating PLN's own combine rule, and its total exceeded both candidate lines' headroom |
| PLN-CHG-001 §14.9 (before this correction) | A bare `PPI-KEBS-2026-ICT-001` fixture | No Need, department, Fiscal Year or Organisation Unit — floating, ungrounded, and keyed to an entity that cannot exist under one-site-one-PE |
| NDS-CHG-001 §14.6 (before this correction) | A parallel bare `SRC-KEBS-ICT-00X` profile | Same problem, independently — the same disconnection was found sitting in a second document, undetected by the first fix |
| REQ-CHG-001 §13.2, §16 | A full Requisition fixture for `PPI-KEBS-2026-ICT-001` | Correct in its own numbers, wrong entity |
| TPR-CHG-001 §13.2, §16 | A full Tender fixture for `TND-KEBS-2026-0001` | Same — correct numbers, wrong entity |

This document is the reconciliation. It does not invent a fifth scenario; it completes the one that was already half-built in the approved MOH fixtures — `NDS-MOH-2027-0003` and `NDS-MOH-2027-0004` were already seeded as two laptop-procurement Needs, sitting unaccepted, clearly meant to combine (their existence is why PLN-DES-09A already illustrated a combined laptop item before this document existed). Completing that thread, rather than starting a new one, is what makes this harmonization instead of one more parallel attempt.

### 1.1 What changed in already-approved documents to make this true

| Document | Correction |
|---|---|
| NDS-CHG-001 | `NDS-MOH-2027-0003` quantity 200→100; `NDS-MOH-2027-0004` quantity 300→150; both carried through to Accepted, not left in Draft/Returned |
| PLN-CHG-001 | §14.8's isolated combined item corrected to one shared Budget Line and integrated into the live Active Version as `PPI-MOH-2027-033`; §14.9's floating KEBS fixture retired; PLN-DES-09A's table corrected to match |
| NDS-CHG-001 | §14.6's parallel floating KEBS fixture retired, in favour of the properly-grounded `NDS-MOH-2027-0003`/`0004` already in §14.3 |
| BUD-CHG-001 | §15.4's stale per-Plan-Item reservation — which contradicted this same document's own corrected funding model — retired; the one reservation this scenario produces is now correctly shown as a Requisition-stage event, not a Planning-stage one; BUD-DES-06A retargeted from the retired reservation to the real one |

### 1.2 What still needs correction, not yet done here

**REQ-CHG-001 and TPR-CHG-001 still say `PE-KEBS` throughout.** This document gives both the exact target to correct to — every ID, date and amount below — but does not itself edit either document's text. Two reasons: first, both are already flagged, separately from this exercise, as needing a full realignment to AUTH-ADR-001 v1.6 and CFG-CHG-002 v0.9 — removing `pe_fy_context_id`, removing Frappe User Permission from their authorization model, adopting the registered permission hooks — and folding a seed-identity swap into that larger pass is cleaner than doing it twice. Second, the scale of what's already been reconciled to produce this document — three separate contradictions found and fixed across NDS, PLN and BUD — was enough for one pass to carry responsibly. This is named as a tracked dependency, not a silent gap: implementation of the Goods STD walkthrough cannot proceed until REQ-CHG-001 and TPR-CHG-001 are brought to the identifiers in §4 and §5 below.

**STD-TPL-001 and STD-TPL-IMP-001** reference the same KEBS fixture as illustrative curation material rather than live seed data. They need the same renaming for consistency but are lower priority — nothing in their own template-correctness depends on which entity the worked example names.

**Neither the Requisition-owning Head of User Department's date windows nor the Value-band statutory reference used elsewhere in PLN have been re-verified against every possible edge case** — this document treats the chain as sufficient to exercise the template, not as a substitute for the acceptance contracts already in each module.

---

## 2. The complete chain

```
NDS-MOH-2027-0003 ─┐                                  ┌─ TND-MOH-2027-033
(HRMD, 100 laptops) │                                  │  (IT-EQUIPMENT-OPEN-V1)
                    ├─ PPI-MOH-2027-033 ─ REQ-MOH-2027-033-001 ─┤
NDS-MOH-2027-0004 ──┘   (250 laptops,                  (Authorised)
(DHI, 150 laptops)       MOH-BL-HWD-2027,
                         OBJ-MOH-2023-001,
                         Open Tender)
```

Every node below cites the document and section where it is — or, for REQ/TPR, will be — the seed of record. This document does not duplicate the authority; it indexes it.

---

## 3. Upstream — Need through Plan Item (already corrected, live in the approved documents)

### 3.1 Site, actors, Organisation Units — no change

All from KT-STD-001 §8.3: Grace Wanjiku (Departmental Author, `OU-MOH-DHI`), Dr Peter Kimani (Head of User Department, `OU-MOH-HRMD` permanently, `OU-MOH-DHI` from 1 Dec 2026), Julia Njeri (Acting Head of User Department, `OU-MOH-DHI`, 1 Oct–30 Nov 2026), Mercy Kilonzo (Procurement Planner, site-wide), Josphat Mwangi (Budget Officer and Finance Confirmation Officer, site-wide), Charles Mutiso (Head of Procurement Function, site-wide — see §6 on this title), Naomi Chebet (Auditor, site-wide).

### 3.2 Needs — NDS-CHG-001 §14.3, §14.4

| Field | Need 1 | Need 2 |
|---|---|---|
| Reference | `NDS-MOH-2027-0003` | `NDS-MOH-2027-0004` |
| Department | HR Management and Development | Digital Health |
| Title | Clinical training laptops for digital health rollout | Clinical deployment laptops for digital health rollout |
| Quantity | 100 each | 150 each |
| Required by | 31 Dec 2027 | 31 Dec 2027 |
| Raised by | Grace Wanjiku | Grace Wanjiku |
| Accepted by | Dr Peter Kimani, 25 Nov 2026, 10:00 EAT | Julia Njeri, 25 Nov 2026, 09:30 EAT |

### 3.3 Departmental plans and entries — PLN-CHG-001 §14.4

| Field | Value |
|---|---|
| DPP 1 | `DPP-MOH-HRMD-2027-001` · Human Resources Management and Development · Version 1 |
| Entry 1 | `DPPE-MOH-HRMD-2027-001` |
| DPP 2 | `DPP-MOH-DHI-2027-001` · Version 1 — the same root as `NDS-MOH-2027-0001`'s entry |
| Entry 2 | `DPPE-MOH-DHI-2027-002` |
| Submission | Dr Peter Kimani certifies both DPPs, 25 Nov 2026, 10:00 EAT |
| Validation | Mercy Kilonzo accepts both, 27 Nov 2026, 14:00 EAT |

### 3.4 Strategy — STR-CHG-001 §14.3, no change

| Field | Value |
|---|---|
| Strategic Objective | `OBJ-MOH-2023-001` — Strengthen interoperable national digital health services |
| Ancestor path | Digital health systems › Health policy, standards and regulation › Digital health governance |

Reused as-is. A national digital-health-services objective is exactly the right justification for a field-equipment procurement; no new Objective was needed.

### 3.5 Budget — BUD-CHG-001 §15.3, §15.4, §15.4A

| Field | Value |
|---|---|
| Procurement Budget | `MOH-BUD-2027-001` · Version 1 · Active |
| Line used | `MOH-BL-HWD-2027` — Digital health workforce development |
| Approved amount | KES 60,000,000 |
| Planned against it (this item) | KES 50,000,000 |
| Funding source | Government of Kenya |

`MOH-BL-DHI-2027` was the first candidate line and is where the combined item's numbers originally, incorrectly, tried to sit. `MOH-BL-HWD-2027` is correct on two grounds: it is the one line with enough headroom (fully unused before this item), and "workforce development" is a defensible home for equipment that trains and equips staff, which is what both source Needs actually describe.

### 3.6 Plan Item — PLN-CHG-001 §14.5

| Field | Value |
|---|---|
| Plan Item | `PPI-MOH-2027-033` — Clinical training and deployment laptops for digital health rollout |
| Source allocations | `PSA-MOH-2027-033-001` (100 each, from `DPPE-MOH-HRMD-2027-001`) · `PSA-MOH-2027-033-002` (150 each, from `DPPE-MOH-DHI-2027-002`) |
| Requirement type / category | Goods |
| Quantity and value | 250 each · KES 50,000,000 |
| Procurement method | Open Tender — above the KES 3,000,000 goods threshold for request for quotations |
| Plan horizon / aggregation / lotting | Single year · Aggregated into this package · Single lot |
| Preference and reservation | None |
| Baseline invitation date | 15 May 2027 |
| Baseline delivery completion | 30 Sep 2027 |

Formed by Mercy Kilonzo, live in `PLN-MOH-2027-001-V1`, Active since 10 Dec 2026, 15:00 EAT — the same Annual Plan Version that already carries `PPI-MOH-2027-021`.

---

## 4. Downstream — the target for REQ-CHG-001

Not yet reflected in REQ-CHG-001's own text. This is what its seed contract must become.

### 4.1 Identity

| Field | Value |
|---|---|
| Requisition | `REQ-MOH-2027-033-001` · Version 1 |
| Plan Item consumed | `PPI-MOH-2027-033` |
| Procuring Entity | Ministry of Health (`PE-MOH`) — not Kenya Bureau of Standards |
| Delivery and inspection location | Ministry of Health Headquarters, Afya House, Nairobi — not KEBS Coast Region Office, Mombasa |

### 4.2 Drawdown lines and specification

| Field | Line 1 | Line 2 |
|---|---|---|
| Line ID | `PIL-MOH-033-001` | `PIL-MOH-033-002` |
| Source | `SRC-MOH-033-001` (from `PSA-MOH-2027-033-001`) | `SRC-MOH-033-002` (from `PSA-MOH-2027-033-002`) |
| Requirement | Business laptops | Business laptops |
| Quantity | 100 Each | 150 Each |
| Purpose | Secure clinical training equipment | Secure field deployment equipment |
| Required by | 30 Sep 2027 | 30 Sep 2027 |

One shared technical requirement, `TRQ-MOH-033-001` — a standard business laptop specification (mid-range processor, 16 GB memory, 512 GB solid-state storage, pre-loaded security configuration, three-year warranty and on-site support) — applies to both lines, since both draw the same item at the same specification; only the funding source and originating department differ.

### 4.3 Lifecycle

| Step | Actor | Date |
|---|---|---|
| Draft opened | Grace Wanjiku | 1 Mar 2027 |
| Submitted | Dr Peter Kimani, Head of User Department | 8 Mar 2027 |
| Authorised | Charles Mutiso, Head of Procurement Function | 15 Mar 2027 |

Authorisation is the event that creates `RSV-MOH-2027-033-001` on `MOH-BL-HWD-2027`, per BUD-CHG-001 §15.4A. Nothing before this step touches a Budget balance.

---

## 5. Downstream — the target for TPR-CHG-001

Not yet reflected in TPR-CHG-001's own text.

### 5.1 Identity

| Field | Value |
|---|---|
| Tender | `TND-MOH-2027-033` · Version 1 |
| Handoff consumed | The authorised `REQ-MOH-2027-033-001` handoff |
| Template | `IT-EQUIPMENT-OPEN-V1`, version 1.1 |
| Procuring Entity | Ministry of Health — not Kenya Bureau of Standards |

### 5.2 Schedule of requirements

Both `PIL-MOH-033-001` and `PIL-MOH-033-002` render as one consolidated line in the Schedule of Requirements — 250 Each, business laptop to `TRQ-MOH-033-001` — since Tender Preparation renders the requirement suppliers bid against, not the internal funding split. The funding split remains traceable through the immutable lineage back to both source allocations without appearing as two separate tender lines.

### 5.3 Milestones

These are the same dates already committed as `PPI-MOH-2027-033`'s baseline in PLN-CHG-001 §14.5 — this fixture deliberately shows the on-schedule case, with every actual date equal to its baseline. A second, isolated profile for the delayed case, exercising PLN's cascading-reforecast mechanism, is named as a useful future addition and is not built here.

| Milestone | Date |
|---|---|
| Invitation or advertisement | 15 May 2027 |
| Bid opening | 5 Jun 2027 |
| Evaluation completion | 5 Jul 2027 |
| Tender award approval | 10 Jul 2027 |
| Notification of award | 12 Jul 2027 |
| Contract signing | 26 Jul 2027 |
| Delivery or implementation completion | 30 Sep 2027 |

### 5.4 Lifecycle

| Step | Actor | Date |
|---|---|---|
| Tender preparation begins | Charles Mutiso | 20 Mar 2027 |
| Approved for publication | Charles Mutiso | 20 Apr 2027 |
| Published | System | 15 May 2027 |

---

## 6. One naming correction this harmonization surfaced

`TPR-CHG-001` correctly uses the Act's own term, **Head of Procurement Function** (sections 47–48), for the actor who prepares and approves a Tender. `DSP-CHG-001`, written after TPR-CHG-001 but before this document, independently introduced **Head of Procurement** — dropping "Function" — as what was meant to be the same statutory office, for the asset disposal plan.

These are one office, not two. Charles Mutiso, already seeded as Head of Procurement in DSP-CHG-001, is the same actor named as Head of Procurement Function in §4.3 and §5.4 above. **DSP-CHG-001's registry entry and every reference to "Head of Procurement" should be corrected to "Head of Procurement Function"** to match the statutory term and this Tender-side usage. This is a small, low-risk rename tracked here rather than actioned, since DSP-CHG-001 is otherwise stable and this touches only a label, not a mechanism.

---

## 7. Required corrections to KT-STD-001

Add one fixture-instant row to §8.5:

> **Requisition and Tender Preparation journeys — 1 Mar 2027 through 15 May 2027, EAT.**

No new actor is required. Every actor this scenario uses already exists in the shared register.

---

## 8. Acceptance

| ID | Required result |
|---|---|
| SEED-AC-001 | Exactly one Procuring Entity, `PE-MOH`, appears anywhere the harmonized chain is seeded, in every module from NDS through TPR. |
| SEED-AC-002 | `PPI-MOH-2027-033`'s two source allocations resolve to the one Procurement Budget Line `MOH-BL-HWD-2027`, and the combine rule's same-line requirement holds. |
| SEED-AC-003 | No Budget balance changes before `REQ-MOH-2027-033-001` is authorised; `RSV-MOH-2027-033-001` exists only after that event. |
| SEED-AC-004 | The Tender's Schedule of Requirements shows 250 Each against one specification, traceable through immutable lineage to both source allocations. |
| SEED-AC-005 | Every date in the chain is internally consistent: Requisition authorisation precedes Tender preparation, which precedes the baseline invitation date, which the published Tender matches exactly in this on-schedule fixture. |
| SEED-AC-006 | REQ-CHG-001 and TPR-CHG-001 contain no reference to `PE-KEBS`, `PPI-KEBS-2026-ICT-001` or `TND-KEBS-2026-0001` once corrected against this document. |
| SEED-AC-007 | `Head of Procurement Function` is the sole registry name for this office across TPR-CHG-001 and DSP-CHG-001. |
