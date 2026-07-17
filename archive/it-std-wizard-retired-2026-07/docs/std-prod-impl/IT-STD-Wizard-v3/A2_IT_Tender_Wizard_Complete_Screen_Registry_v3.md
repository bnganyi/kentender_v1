# IT Tender Wizard Complete Screen Registry v3

**Purpose:** Prevent missing screens, naming drift, and confusion between application surfaces, configuration steps, and workflow gates.

---

## 1. Registry Status

This registry is mandatory. A screen/view/modal is not valid unless listed here.

---

## 2. Application Surfaces

| ID | Exact user-facing name | Surface type | Required? | Current spec status |
|---|---|---|---:|---|
| UI-00 | IT Tender Configurations Dashboard | Application screen | Yes | Must be audited against v3 |
| UI-M01 | Create IT Tender Configuration | Modal | Yes | Missing detailed spec |
| UI-01 | Tender Configuration Home | Application screen | Yes | Must be rewritten against v3 |

---

## 3. Numbered Configuration Steps

| ID | Exact user-facing name | Required? | Current spec status | Notes |
|---|---|---:|---|---|
| CFG-01 | Tender Profile | Yes | Draft exists; must be audited against v3 | First configuration step |
| CFG-02 | Tender Data Sheet | Yes | Draft exists; must be audited against v3 | TDS values only |
| CFG-03 | IT Requirements | Yes | Draft exists; must be audited against v3 | Must not include scoring/pricing/contract administration |
| CFG-04 | Implementation Schedule | Yes | Draft exists; must be audited against v3 | Delivery plan only; no project execution |
| CFG-05 | System Inventory & Bidder Background | Yes | Missing detailed spec | Must cover Sections VIII and IX |
| CFG-06 | Price Schedule | Yes | Missing detailed spec | Price forms and pricing structure only |
| CFG-07 | Evaluation Setup | Yes | Missing detailed spec | Criteria/scoring only, not actual evaluation |
| CFG-08 | Forms & Evidence | Yes | Missing detailed spec | All non-price Section IV forms/evidence |
| CFG-09 | Contract Values | Yes | Missing detailed spec | SCC and contract-facing values |

---

## 4. Workflow Gates / Views

These are required, but they are not configuration steps.

| ID | Exact user-facing name | Surface type | Required? | Current spec status | Notes |
|---|---|---|---:|---|---|
| WF-01 | Readiness Report | Workflow report/view | Yes | Missing detailed spec | Opened after Run Readiness Check |
| WF-02 | Review Workspace | Workflow task/view | Yes | Missing detailed spec | Reviewer-focused; not a configuration form |
| WF-03 | Tender Document Preview | Preview view | Yes | Missing detailed spec | Read-only generated package preview |
| WF-04 | Publication Handoff | Handoff confirmation/view | Yes | Missing detailed spec | Marks package ready for Tender Management; does not publish |

---

## 5. Canonical Display in Tender Configuration Home

### Configuration Steps

1. Tender Profile
2. Tender Data Sheet
3. IT Requirements
4. Implementation Schedule
5. System Inventory & Bidder Background
6. Price Schedule
7. Evaluation Setup
8. Forms & Evidence
9. Contract Values

### Completion & Handoff

- Readiness Check
- Review Status
- Tender Document Preview
- Publication Handoff

Do not show Validation, Review & Approval, Final Preview, or Publication Readiness as configuration cards.

---

## 6. Explicit Corrections to Earlier Packs

Earlier packs are superseded where they:

1. Omit Tender Profile;
2. Omit Tender Data Sheet;
3. Treat Validation, Review & Approval, Final Preview, or Publication Readiness as CFG steps;
4. Use `Screen 01`, `Screen 02`, etc. without distinguishing application surfaces from configuration steps;
5. Use `System Inventory` instead of `System Inventory & Bidder Background`;
6. Use `Final Preview` instead of `Tender Document Preview`;
7. Use `Publication Readiness` instead of `Publication Handoff` for the workflow gate;
8. Use `Tender Shell`, `Tender to Configure`, `Ready`, or `Locked` in default procurement UI.

---

## 7. Next Required Work Order

Do not proceed to CFG-05 until these are corrected in order:

1. UI-M01 — Create IT Tender Configuration detailed spec;
2. UI-01 — Tender Configuration Home rewrite against this registry;
3. CFG-01 — Tender Profile audit/rewrite;
4. CFG-02 — Tender Data Sheet audit/rewrite;
5. CFG-03 — IT Requirements audit/rewrite;
6. CFG-04 — Implementation Schedule audit/rewrite.

Then proceed to:

7. CFG-05 — System Inventory & Bidder Background.
