# IT Tender Wizard — IT STD Coverage and Control Addendum v3

**Status:** Mandatory addendum. Supersedes earlier coverage addenda.

---

## 1. Control Decision

The wizard uses nine numbered configuration steps only.

Workflow gates may have views, but they are not configuration steps.

---

## 2. PPRA IT STD Coverage

| IT STD area | Wizard treatment |
|---|---|
| Tender identity / cover / invitation context | CFG-01 Tender Profile; downstream publication metadata handled by Tender Management where applicable |
| Section I — Instructions to Tenderers | Locked STD text rendered by STD Engine; parameterized through CFG-02 Tender Data Sheet only |
| Section II — Tender Data Sheet | CFG-02 Tender Data Sheet |
| Section III — Evaluation and Qualification Criteria | CFG-07 Evaluation Setup |
| Section IV — Tendering Forms | CFG-08 Forms & Evidence, excluding price schedule forms |
| Section IV — Price Schedule Forms | CFG-06 Price Schedule |
| Section V — Requirements of the Information System | CFG-03 IT Requirements |
| Section VI — Technical Requirements | CFG-03 IT Requirements |
| Section VII — Implementation Schedule | CFG-04 Implementation Schedule |
| Section VIII — System Inventory Tables | CFG-05 System Inventory & Bidder Background |
| Section IX — Background and Informational Materials | CFG-05 System Inventory & Bidder Background |
| General Conditions of Contract | Locked STD text rendered by STD Engine; parameterized through CFG-09 Contract Values only |
| Special Conditions of Contract | CFG-09 Contract Values |
| Contract Forms and appendices | CFG-09 Contract Values and generated package outputs |
| Securities, beneficial ownership, declarations, qualification evidence | CFG-08 Forms & Evidence or CFG-09 Contract Values depending on stage |
| Change-order forms and post-award administration forms | Downstream contract administration; not an IT Tender Configuration screen |

---

## 3. Required Refinements

1. `CFG-05` is **System Inventory & Bidder Background**, not merely System Inventory.
2. Background material must not create hidden obligations. Obligations belong in CFG-03 IT Requirements.
3. `CFG-08` covers all non-price Section IV forms/evidence, not only file uploads.
4. ITT and GCC are not edited by users.
5. Readiness, review, preview, and handoff are workflow gates, not configuration steps.

---

## 4. Coverage Verdict

The simplified model covers the full IT STD only when all of the following exist:

- UI-00, UI-M01, UI-01;
- CFG-01 through CFG-09;
- WF-01 through WF-04.

A pack that omits any of these is incomplete.
