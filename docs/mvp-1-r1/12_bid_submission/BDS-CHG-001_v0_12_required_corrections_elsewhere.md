# BDS-CHG-001 v0.12 — requirement-to-line mapping: what the other documents say and what must change

Companion to `KenTender_BDS-CHG-001_Supplier_and_Electronic_Bid_Submission_v0_12.md` (proposed 10 October 2026). This note names corrections needed in the Tender Preparation and template documents. It does not edit them and it assumes nothing about versions of those documents that were updated outside this repository.

## 1. The question

The Requirements task of a two-line bid showed thirteen technical rows, but the design fixtures show eleven. The Project Owner asked whether the monitor requirements TECH-012 and TECH-013 are missing and whether “Technical requirements — Complete” can be trusted. The mapping was traced from the published Tender through the supplier form to the completion calculation.

## 2. What was traced (observations, not rules)

Source: the development site, Bid BID-MOH-2027-003-001 on Tender TND-MOH-2027-003, read through the same service the supplier screen uses. Read-only; nothing was changed.

**Goods lines in the Published Bid Definition**

| Line | Description | Quantity | Requirement identities listed on the line |
|---|---|---|---|
| 1 | Office laptops | 20 Each | TECH-001, TECH-002, TECH-003, TECH-004, TECH-005, TECH-006, TECH-007, TECH-008, TECH-009, TECH-010, TECH-011 |
| 2 | Monitors for office laptops | 20 Each | TECH-001, TECH-002, TECH-012, TECH-013 |

**Technical requirement rows in the same definition** (thirteen groups; each row's own “applies to” label and whether the line side agrees)

| Requirement | Label on the row | Applies to (row side) | Listed by line(s) |
|---|---|---|---|
| TECH-001 | Electrical compatibility | All items | Office laptops; Monitors for office laptops |
| TECH-002 | New and unused equipment | All items | Office laptops; Monitors for office laptops |
| TECH-003 | Memory | Office laptops | Office laptops |
| TECH-004 | Storage capacity | Office laptops | Office laptops |
| TECH-005 | Storage type | Office laptops | Office laptops |
| TECH-006 | Display size | Office laptops | Office laptops |
| TECH-007 | Battery runtime | Office laptops | Office laptops |
| TECH-008 | Processor requirement | Office laptops | Office laptops |
| TECH-009 | Operating-system compatibility | Office laptops | Office laptops |
| TECH-010 | Network connectivity | Office laptops | Office laptops |
| TECH-011 | Required ports | Office laptops | Office laptops |
| TECH-012 | Display resolution | Monitors for office laptops | Monitors for office laptops |
| TECH-013 | Panel size | Monitors for office laptops | Monitors for office laptops |

**Findings**

1. TECH-012 and TECH-013 are present. The published definition carries them, the supplier's Technical requirements table shows thirteen rows including Display resolution and Panel size, and each is Complete in that bid.
2. The completion calculation counts them. The Requirements task evaluated 52 technical field states across the thirteen rows, none with a Must fix issue. “Technical requirements — Complete” was therefore computed over all thirteen rows for that bid.
3. The “eleven rows” the concern rested on come from the design fixture (BDS-CHG-001 v0.11 §10.1 and §10.10 “Render all eleven fixture rows”) and from the front-end test fixture, which describe a one-line Tender. They are not the published data of the two-line Tender.
4. The line side and the requirement side agree for all thirteen rows in this bid.
5. The mapping rests on two places in the definition: the line's list of requirement identities, and the requirement row's applies-to label. The label is the line's description text. The exact item identifiers (`applies_to_item_ids`) are written to the row's lineage only when present; this trace did not inspect the lineage.
6. The Offered goods failure is separate and is the first-element lookup recorded in BDS-CHG-001 v0.12 header: only the first goods line's form was drawn while readiness counted both lines.

## 3. What the controlled documents say

| Document | Wording read | Does it state the requirement-to-line mapping? |
|---|---|---|
| REQ-CHG-001 v1.18 §5.7 and §5.12 | §5.7 `applies_to`: “`Item` (one Requisition Item), `Items` (a stated set of Requisition Items) or `All items`, with the exact item identifiers stored in `applies_to_item_ids` (§5.7A).” §5.12: “Every technical, service and acceptance row carries `applies_to_item_ids` (the exact items it covers) in addition to `applies_to` and `applies_to_id`”; handoff version 1.5. | Yes. This is the explicit mapping. |
| TPR-CHG-001 v0.18 §4.5.1 | “Each goods line | Read-only published quantity/unit; offered make/model; delivery commitment; linked evidence; permitted unit price and tax inputs; calculated total.” and “Each mandatory technical requirement | `Comply` or `Do not comply`; typed offered value where measurable…”. The only “Applies to” column found is the acceptance table. | No. It states per-line responses but not that a technical row carries the lines it covers, and does not mention handoff 1.5. |
| STD-TPL-001 v0.15 §7.1 | “Each supplier-facing goods line contains the stable schedule identity, description, quantity, unit, destination, latest delivery date, minimum warranty and source-item lineage. The supplier gives the offered make/model, offered delivery commitment, linked evidence and permitted prices.” §13.6 gives the response identity formula. A text search found no `applies_to_item_ids`, `technical_requirement_ids` or “handoff 1.5”. | No for the mapping fields. It does state per-line supplier responses. |
| STD-TPL-001 reference vector `07_tender_templates/it_equipment_open_v1/06_runtime/moh_published_bid_definition_expected.json` | A text search of the JSON found `technical_requirement_ids` and `applies_to`; it did not find `applies_to_item_ids`. | Partly: line side and label side, not the exact item identifiers. |
| BDS-CHG-001 v0.11 | A text search found no goods-line, per-line or applies-to wording. | No. v0.12 §4.4.9 adds it. |

The baseline register already records the gap for REQ v1.18 (entry for REQ-CHG-001): “TPR/STD-TPL wording for handoff 1.5 is a required correction in those documents.”

## 4. Required corrections (to be authored by the document owners; none made here)

### TPR-CHG-001 (current file in the repository: v0.18)

- **§4.5.1 Supplier response schema.** Add that each technical, service and acceptance requirement row carries the exact goods lines it covers (`applies_to_item_ids`, REQ-CHG-001 v1.18 §5.12 handoff 1.5), that a requirement covering several lines is stated and answered once, and that the supplier-facing definition carries the mapping from both the line and the requirement side.
- **§4.5.1 or the publication checks.** Say what publication does when the two sides disagree or a requirement covers no line. BDS-CHG-001 v0.12 proposes refusing, subject to owner decision BDS12-D2.
- **Version citation.** TPR-CHG-001 cites handoff versions only through REQ; confirm it accepts handoff 1.5 as REQ-CHG-001 v1.18 §5.12 says Tender Preparation does (“Tender Preparation accepts handoff versions 1.4 and 1.5”).

### STD-TPL-001 (current file in the repository: v0.15)

- **§7.1 Goods and delivery** (or the published-definition contract). Name the mapping fields: `technical_requirement_ids` on a goods line; `applies_to_scope`, `applies_to_id` and `applies_to_item_ids` on a requirement's lineage; and state the agreement check.
- **Reference vector** `moh_published_bid_definition_expected.json` and its release copies: reconcile so the expected definition carries `applies_to_item_ids` where the REQ handoff supplies it, or state why it does not.
- **Selector contract.** The release's goods-line selector lists `technical_requirement_ids` among the line's facts; confirm the document's selector table says so.

### Baseline register

- The BDS-CHG-001 entry now records v0.12 as proposed in `approval_history`; v0.11 stays the approved baseline until approval.
- Disagreement to report, not resolved: the register entry for TPR-CHG-001 says version 0.17 while `11_tenders/KenTender_TPR-CHG-001_Tenders_v0_18.md` exists in the repository. The register's own `approval_history` for TPR describes v0.17 as the proposed revision.

## 5. Not verified

- Whether the current externally maintained copies of TPR-CHG-001 or STD-TPL-001 differ from the repository files read here.
- Whether `applies_to_item_ids` is present in the lineage of the development bid's requirement rows.
- STD-TPL-001 v0.10 §13.6, which TPR-CHG-001 v0.18 §4.5 cites for the line grouping algorithm; v0.15 §13.6 was read and is a different subject (stable identity), so the grouping algorithm's current location is unconfirmed.
- Any seed document. Whether a two-line bid state exists in the canonical seed world is unknown.
