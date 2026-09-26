# BDS-CHG-001 v0.8: definition-to-board reconciliation matrix

| Control | Value |
|---|---|
| Version | 0.8-phase0.1 |
| Status | Phase 0 working document (plan BDS-CHG-001 v0.8) |
| Purpose | Phase 0 input to plan Phase 3, the successor template release 1.2 (owner decision OD-E, 26 Sep 2026). |
| Owner instruction (OD-E, quoted) | "reconcile the template before completing the bid journey. Build the shared, definition-driven layout and unaffected journeys. Reconcile each difference against the approved template pack, source coverage, Published Tender and BDS contract. Correct the controlled template assets and rerun the definition, mapping and rendering checks. Do not hard-code the boards' rows or accept missing obligations as known departures. Hold completion of the affected Company, Requirements, Review and Submit journey until the corrected release passes. If release 1.1 has already been installed or bound to a Tender, preserve its immutable identity and issue a successor release for new bindings; do not silently change an existing Published Bid Definition." |
| Definition side | Release 1.1 expected MOH definition, `docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1/06_runtime/moh_published_bid_definition_expected.json`: 123 response rows, 2 price rows, 7 declaration texts, 21 evaluation and 21 contract mappings. Full inventory in Appendix A. It is v1 (no effective addenda) and was read by script on 26 Sep 2026. |
| Board side | BDS-CHG-001 v0.8 §10.1 fixture tables ("Company forms and declarations", "Tender security", "Offered goods and technical responses", "Warranty, support and experience", "Evidence set", "Price"), BDS-CHG-001 §10.8–10.13, and the v3 boards C and D. |
| Other authorities read | STD-TPL-001 v0.10 §§8–10 and STD-TPL-001 v0.10 §13.5–13.6 (read in full); BDS-CHG-001 v0.8 §4.4, BDS-CHG-001 v0.8 §4.8 and BDS-CHG-001 v0.8 §5.3 (read in full). **Not read:** the source coverage registers in `07_tender_templates/it_equipment_open_v1/03_registers/`. Phase 3 must read them before any classification is final. |
| Status | Every classification below is **preliminary**. Phase 3 confirms each one against source coverage and closes it. Nothing here changes a template asset. |

## Classification key

| Class | Meaning | Treatment in Phase 3 |
|---|---|---|
| **A: template gap** | A published obligation (in the Published Tender or in the group's own frozen `published_facts`) has no bidder response, validation or evidence rule that captures it. | Correct the release assets in 1.2 (response_rules / downstream_rules / product_profile) and rerun the checks. Never a known departure (OD-E). |
| **B: owned elsewhere** | The value is an Account, arrangement or assignment fact (BDS BDS-CHG-001 §4.4.8). | BDS pre-fills it read-only from the organisation snapshot, arrangement or assignment through the code-owned Goods composition. If the definition models it as free bidder input, 1.2 corrects the rule so it is not a second source of truth. |
| **C1: board omits template content** | The template (and its source) has an obligation the board does not draw. | Built from the definition. A design follow-up asks for a redraw. This is not a template change. |
| **C2: board content without source** | The board or BDS-CHG-001 §10.1 shows a value no source supports. | Not built. A spec/design follow-up is raised. |
| **OK** | Consistent. | Built as drawn, from the definition. |

## 1. Task 1: Tender documents, clarifications and addenda (DES-07)

| # | Definition (1.1) | Board / BDS-CHG-001 §10.1 | Class | Note |
|---|---|---|---|---|
| 1.1 | Section label **"Tender documents and addenda"** (`product_profile` TASK-DOCUMENTS; STD-TPL-001 v0.10 §8.1 table uses the same words) | **"Tender documents, clarifications and addenda"** (BDS BDS-CHG-001 §1 item 4.1, BDS-CHG-001 §5.3, BDS-CHG-001 §10.8) | **Decision needed (document conflict)** | Two approved documents disagree. Changing the release label changes wording that STD-TPL-001 v0.10 §8.1 states, so this needs the STD-TPL-001 document owner. Recommendation: raise to the owner; the build shows the release label until then. **Decided 26 Sep 2026 (Project Owner):** "2.1 Tender documents, clarifications and addenda" — the task label becomes **Tender documents, clarifications and addenda** in release 1.2; STD-TPL-001 §8.1 changes in STD-TPL-001 v0.12 (proposed); the STD-TPL-001 §11.5 release 1.1 design fixture keeps release 1.1's label. |
| 1.2 | `RR-DOC-ACK/DOCUMENT-PACKAGE` `acknowledged`, CTL-CONFIRMATION, `RQ-ALWAYS`: "I have read the current published Tender documents and every effective addendum." | Base: checkbox "I have reviewed ADD-MOH-2027-033-001 and understand that the delivery point and submission deadline changed." DES-07-NONE: "After David opens the current documents the task can be Complete; no empty acknowledgement control." | **Decision needed** | The definition always requires a confirmation; BDS BDS-CHG-001 §10.8 wants no control when there is no addendum and an addendum-specific sentence when there is one. Phase 3 checks the source; this may need STD-TPL-001 text. **Decided 26 Sep 2026 (Project Owner):** "2.2 When there's something specific to acknowledge" — an acknowledgement is asked only when there is something specific to acknowledge (an effective addendum), in wording that names it; with none, no acknowledgement control. Release 1.2 changes the rule; STD-TPL-001 §8.1's task purpose changes in STD-TPL-001 v0.12 (proposed). |

## 2. Task 2: Company, declarations and tender security (DES-08)

| # | Definition (1.1) | Board / BDS-CHG-001 §10.1 | Class | Note |
|---|---|---|---|---|
| 2.1 | `RR-SUPPLIER-DETAILS` `legal_name`, `country_of_registration`, `registered_address` (free bidder input) | "Bidding organisation … From your Account · copied to this bid" (legal name, registration number, KRA PIN, address) | **B** | BDS BDS-CHG-001 §4.4.8: pre-filled read-only from the organisation snapshot. 1.2 should mark these as snapshot-supplied. |
| 2.2 | `year_of_registration` (CTL-INTEGER, required) | Not drawn; not in the BDS-CHG-001 §4.1 Account fields | **C1** (board omits) | This is a Tenderer Information Form field, and Phase 3 must confirm that against the source. If confirmed, it is a bid-specific entry on DES-08. |
| 2.3 | `representative_name` / `_email` / `_telephone` | "Tender contact" David Ouma / email / phone | **B** | Bidder Arrangement Tender contact (BDS-CHG-001 §4.3), pre-filled and bid-specific. |
| 2.4 | `bidder_arrangement` (single choice) plus `joint_venture_members` (**CTL-LONG-TEXT**, required when Joint venture) | Arrangement "Single organisation"; DES-08-JV shows structured lead and members and forbids a "free-text member list" (BDS-CHG-001 §10.9) | **A/B** | The arrangement is owned by the Start bid transaction (BDS-CHG-001 §4.3). 1.2 should replace the free-text members field with the structured arrangement projection. |
| 2.5 | Declarations: FORM-OF-TENDER (4 responses), CITD (3), SD1 (1), SD2 (1), CODE-OF-ETHICS (1), **CBQ (17)**, RESERVATION text | Seven rows: **Tenderer information** (Complete), Form of Tender, Independent tender determination, SD not debarred, SD no corrupt practice, Code of ethics, Youth reservation declaration | **C1** (CBQ) / **OK** (rest) | CBQ is a PPRA Goods STD form with 17 responses; the board omits it. The board's "Tenderer information" row is the supplier-details composition shown as a form row. |
| 2.6 | FORM-OF-TENDER responses `discounts`, `state_owned_enterprise`, `commissions_gratuities_fees` | Only "Confirmed" drawn | **C1** | Built from the definition in the declaration view. The discount wording must be reconciled with BDS-CHG-001 §5.6 item 6 ("rejects … unrequested discount"); this is a Phase 3 check. |
| 2.7 | Reservation: `certificate_category`, `certificate_number`, `certificate_valid_until`, `certificate_evidence`, `confirmed`; published category Youth | "Youth reservation declaration Complete"; AGPO certificate AGPO-Y-2026-04172, expires 30 Jun 2027 | **OK** | — |
| 2.8 | Tender security: `security_form` (Demand Bank Guarantee / Insurance Guarantee), `issuer`, `guarantee_reference`, `security_evidence`. Published facts: amount 500,000.00 KES; `validity_date` 2027-10-03; `bank_guarantee_expiry_date` 2027-11-02; `insurance_guarantee_expiry_date` 2027-10-31 | Type **"Bank guarantee"**; Issuer; Reference; Amount; **Valid until 15 Nov 2027**; uploaded proof | **A** (`valid_until`) / **C2** (type wording) | BDS BDS-CHG-001 §4.8: `valid_until` is "Required when the published form states a validity date". The published facts carry expiry dates, but the definition has no bidder field, so 1.2 adds `valid_until` validated against the published expiry. The BDS-CHG-001 §10.1 type "Bank guarantee" should read the definition option "Demand Bank Guarantee" (spec/fixture follow-up). |
| 2.9 | — | Physical original recorded, receipt and time | **Owned elsewhere** | BDS-owned intake and match (OD-G/H), not a definition row. |
| 2.10 | — | Authorised Signatory Mary Wanjiku; authority evidence; certificate Ready | **B** | Assignment facts and the trust gateway certificate status. |

## 3. Task 3: Requirements and supporting evidence (DES-09)

| # | Definition (1.1) | Board / BDS-CHG-001 §10.1 | Class | Note |
|---|---|---|---|---|
| 3.1 | Goods offer: `offered_make_model`, `offered_delivery_date`, `evidence` (optional); published quantity 250 Each, destination, latest delivery 2027-09-30 | Offered model ApexBook Pro 14; quantity; delivery 15 Sep 2027; current delivery location | **OK** | — |
| 3.2 | 11 technical groups TECH-001…011, each `compliance` / `offered_value` (controls per characteristic, including multi-select TECH-010 and ports list TECH-011) / `comment` / `evidence` (mandatory 1–5). Published labels and required values match BDS-CHG-001 §10.1 | 11 rows with the same names and required values; offered responses; evidence | **OK** | The board draws the offered value and evidence; the compliance choice and optional comment are in the response drawer (BDS-CHG-001 §10.10). |
| 3.3 | Warranty/support: 4 rows: `confirmation` (yes/no), `offered_warranty_months`, `support_contact_details` (long text), `evidence` (optional). Published facts: `minimum_warranty_months` 36; `onsite_support_required` true; `maximum_support_response_hours` 8; `manufacturer_support_required` true; `service_location_constraint` "Within Kenya"; support description | 6 rows: minimum warranty → 36 months; on-site support → Yes; maximum response 8 h → 4 hours; manufacturer support → Yes; service location → Nairobi service centre; escalation and contacts → Supplied | **A** | Five published obligations share one blanket confirmation, and there is no offered value for response hours. STD-TPL-001 v0.10 §8.3 requires "Confirmation and the applicable offered value, contact or service detail" per warranty/support fact, and BDS01-AC-021 / BDS01-IMP-027 require all six rows. 1.2 adds per-obligation responses mapped to `EVG-TECHNICAL-COMPLIANCE`. |
| 3.4 | Experience: 2 entries × (`client_name`, `contract_reference`, `contract_value`, `completion_date` in the 5-year window, `scope`, `evidence` 1–3) | Customer, Supply, Completion date, Evidence (2 rows); "Add contract" | **C1** (contract reference, value) | Built from the definition. A design follow-up adds the columns. The "Add contract" action must respect the published required count of 2 (BDS-CHG-001 §11.4 "Add contract"). |
| 3.5 | Acceptance: 5 confirmations ACC-001…005 (quantity, physical condition, specification, functional test, documents) | **Not drawn** on DES-09 | **C1** | BDS01-AC-021 names "five acceptance obligations". Built from the definition; a design follow-up asks for the section. |
| 3.6 | Evidence list: 4 kinds (manufacturer authorisation, datasheets, after-sales support, eligibility and registration documents), plus per-row evidence on technical, experience, security, reservation and warranty rows | 10 items: incorporation, tax compliance, youth reservation, manufacturer authorisation, datasheet, warranty/support commitment, Kenya service-centre details, comparable contracts ×2, tender-security proof | **OK** except incorporation + tax | 8 of 10 map one-to-one to definition evidence slots. Incorporation and tax are **one** slot ("Tax compliance, registration and constitution documents") on the definition side and **two** items on the board. That slot accepts 1–10 files (Appendix A), so both certificates fit as two files under one requirement, and the board's two rows can render as two files of that slot. Phase 3 still checks the source form; 1.2 splits the slot only if the source lists them as separate requirements. **Decided 26 Sep 2026 (Project Owner):** "2.3 Keep one. In any case, these will be superseded in the next iteration when integration with the external authorities is established." — the definition keeps one evidence requirement; no 1.2 change. |

## 4. Task 4: Price (DES-10)

| # | Definition (1.1) | Board / BDS-CHG-001 §10.1 | Class | Note |
|---|---|---|---|---|
| 4.1 | Goods line 1: 250 Each, KES, inputs `unit_price` and `tax_amount`, `CALC-LINE-TOTAL` | One row: unit price excluding tax; line amount before tax | **OK** | BDS-CHG-001 §10.11: a bidder-entered tax control sits in the totals panel. |
| 4.2 | Tender total row `CALC-TENDER-TOTAL` | Subtotal excluding tax; Tax; **Bid total** | **OK** | Totals are server-calculated. The fixture (250 × 160,000 + 6,400,000 = 46,400,000) is recomputed in `test_price.py`. |

## 5. Task 5: Review and submit (DES-11, DES-12)

| # | Definition (1.1) | Board / BDS-CHG-001 §10.1 | Class | Note |
|---|---|---|---|---|
| 5.1 | `RR-SUBMISSION` `signatory_name`, `signatory_title` (free input), `confirmed` ("I confirm this is the complete Tender I am authorised to sign and submit.") | DES-12 signatory Mary Wanjiku / Managing Director (from the assignment); final confirmation "I confirm that the information, declarations and evidence in this bid are correct and that I am authorised to submit it for Afya Digital Supplies Limited." | **B** (name, title) / **Decision needed** (confirmation wording) | Name and title come from the active signatory assignment (BDS-CHG-001 §4.2). The two confirmation sentences differ: Phase 3 settles which is the published, signed statement. **Decided 26 Sep 2026 (Project Owner):** "2.4 Bid spec" — release 1.2 uses the BDS-CHG-001 §10.13 confirmation sentence, with the arrangement's name supplied at bid time. The sentence lives only in the release assets (`response_rules.json`), so no STD-TPL-001 text changes. |

## 6. Summary for Phase 3

| Class | Items |
|---|---|
| A: correct in 1.2 | 2.4 (structured JV), 2.8 (`valid_until`), 3.3 (per-obligation warranty and support responses) |
| B: pre-fill from snapshot, arrangement or assignment | 2.1, 2.3, 2.4, 2.10, 5.1 (name and title) |
| C1: build from definition; design follow-up | 2.2, 2.5 (CBQ), 2.6, 3.4, 3.5 |
| C2: spec/fixture follow-up | 2.8 (type wording) |
| Decisions needed | 1.1 (task label, STD-TPL-001 owner), 1.2 (document acknowledgement), 3.6 (split eligibility documents), 5.1 (confirmation wording) — all four decided by the Project Owner on 26 Sep 2026 (see each row). |

Class A and the decisions gate BDS-G03 and hold slices 11.8, 11.9, 11.11 and 11.12 (plan Phase 3).

## Appendix A: release 1.1 definition inventory (generated)

Generated by script on 26 Sep 2026 from `docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1/06_runtime/moh_published_bid_definition_expected.json`: 123 response rows, 2 price rows, 7 declaration texts, 21 evaluation mappings, 21 contract mappings. Response ids are omitted: they are opaque and never bidder-visible (BDS-CHG-001 §3). Group keys are the stable rule/source pairs.

### TASK-DOCUMENTS — Tender documents and addenda

| Group key | Field key | Label | Control | Required rule | Evidence rule | Evaluation / contract mapping |
|---|---|---|---|---|---|---|
| `RR-DOC-ACK/DOCUMENT-PACKAGE` | `acknowledged` | I have read the current published Tender documents and every effective addendum. | `CTL-CONFIRMATION` | `RQ-ALWAYS` | — | `DM-DOC-ACK` / `DM-DOC-ACK` |

### TASK-COMPANY — Company, declarations and tender security

| Group key | Field key | Label | Control | Required rule | Evidence rule | Evaluation / contract mapping |
|---|---|---|---|---|---|---|
| `RR-SUPPLIER-DETAILS/SUPPLIER` | `legal_name` | Tenderer's legal name | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-SUPPLIER-DETAILS` / `DM-SUPPLIER-DETAILS` |
| `RR-SUPPLIER-DETAILS/SUPPLIER` | `bidder_arrangement` | Tendering as | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-SUPPLIER-DETAILS` / `DM-SUPPLIER-DETAILS` |
| `RR-SUPPLIER-DETAILS/SUPPLIER` | `joint_venture_members` | Joint venture members (legal name, country and year of registration, address and authorised representative of each member) | `CTL-LONG-TEXT` | `RQ-WHEN-FIELD-EQUALS (bidder_arrangement = Joint venture)` | — | `DM-SUPPLIER-DETAILS` / `DM-SUPPLIER-DETAILS` |
| `RR-SUPPLIER-DETAILS/SUPPLIER` | `country_of_registration` | Actual or intended country of registration | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-SUPPLIER-DETAILS` / `DM-SUPPLIER-DETAILS` |
| `RR-SUPPLIER-DETAILS/SUPPLIER` | `year_of_registration` | Year of registration | `CTL-INTEGER` | `RQ-ALWAYS` | — | `DM-SUPPLIER-DETAILS` / `DM-SUPPLIER-DETAILS` |
| `RR-SUPPLIER-DETAILS/SUPPLIER` | `registered_address` | Address in the country of registration | `CTL-LONG-TEXT` | `RQ-ALWAYS` | — | `DM-SUPPLIER-DETAILS` / `DM-SUPPLIER-DETAILS` |
| `RR-SUPPLIER-DETAILS/SUPPLIER` | `representative_name` | Authorised representative's name | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-SUPPLIER-DETAILS` / `DM-SUPPLIER-DETAILS` |
| `RR-SUPPLIER-DETAILS/SUPPLIER` | `representative_email` | Authorised representative's email | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-SUPPLIER-DETAILS` / `DM-SUPPLIER-DETAILS` |
| `RR-SUPPLIER-DETAILS/SUPPLIER` | `representative_telephone` | Authorised representative's telephone | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-SUPPLIER-DETAILS` / `DM-SUPPLIER-DETAILS` |
| `RR-DECL-FORM-OF-TENDER/FORM-TENDER` | `discounts` | Discounts offered and the methodology for their application (or "none") | `CTL-LONG-TEXT` | `RQ-ALWAYS` | — | `DM-DECL-FORM-OF-TENDER` / `DM-DECL-FORM-OF-TENDER` |
| `RR-DECL-FORM-OF-TENDER/FORM-TENDER` | `state_owned_enterprise` | Is the Tenderer a state-owned enterprise or institution? | `CTL-YES-NO` | `RQ-ALWAYS` | — | `DM-DECL-FORM-OF-TENDER` / `DM-DECL-FORM-OF-TENDER` |
| `RR-DECL-FORM-OF-TENDER/FORM-TENDER` | `commissions_gratuities_fees` | Commissions, gratuities or fees paid or payable (or "none") | `CTL-LONG-TEXT` | `RQ-ALWAYS` | — | `DM-DECL-FORM-OF-TENDER` / `DM-DECL-FORM-OF-TENDER` |
| `RR-DECL-FORM-OF-TENDER/FORM-TENDER` | `confirmed` | I confirm the Form of Tender statements above on behalf of the Tenderer. | `CTL-CONFIRMATION` | `RQ-ALWAYS` | — | `DM-DECL-FORM-OF-TENDER` / `DM-DECL-FORM-OF-TENDER` |
| `RR-DECL-CITD/FORM-CITD` | `disclosure` | Paragraph 5 disclosure | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-DECL-CITD` / `DM-DECL-CITD` |
| `RR-DECL-CITD/FORM-CITD` | `consultation_details` | Names of the competitors and the nature of, and reasons for, the consultations | `CTL-LONG-TEXT` | `RQ-WHEN-FIELD-EQUALS (disclosure = Consulted with one or more competitors)` | — | `DM-DECL-CITD` / `DM-DECL-CITD` |
| `RR-DECL-CITD/FORM-CITD` | `confirmed` | I certify the Certificate of Independent Tender Determination on behalf of the Tenderer. | `CTL-CONFIRMATION` | `RQ-ALWAYS` | — | `DM-DECL-CITD` / `DM-DECL-CITD` |
| `RR-DECL-SD1/FORM-SD1` | `confirmed` | I make Self-Declaration SD1 on behalf of the Tenderer. | `CTL-CONFIRMATION` | `RQ-ALWAYS` | — | `DM-DECL-SD1` / `DM-DECL-SD1` |
| `RR-DECL-SD2/FORM-SD2` | `confirmed` | I make Self-Declaration SD2 on behalf of the Tenderer. | `CTL-CONFIRMATION` | `RQ-ALWAYS` | — | `DM-DECL-SD2` / `DM-DECL-SD2` |
| `RR-DECL-CODE-OF-ETHICS/FORM-COE` | `confirmed` | I make the Declaration and Commitment to the Code of Ethics on behalf of the Tenderer. | `CTL-CONFIRMATION` | `RQ-ALWAYS` | — | `DM-DECL-CODE-OF-ETHICS` / `DM-DECL-CODE-OF-ETHICS` |
| `RR-DECL-CBQ/FORM-CBQ` | `business_structure` | Business structure | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `ownership_details` | Owner, partner or director details (name, nationality, citizenship and percentage of shares owned) | `CTL-LONG-TEXT` | `RQ-ALWAYS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `trade_licence` | Current trade licence number and expiry date | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `maximum_business_value` | Maximum value of business the Tenderer handles | `CTL-MONEY` | `RQ-ALWAYS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `procuring_entity_interest` | Does any person in the Procuring Entity have an interest or relationship in this firm? | `CTL-YES-NO` | `RQ-ALWAYS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `procuring_entity_interest_details` | Names, designation in the Procuring Entity and the interest or relationship | `CTL-LONG-TEXT` | `RQ-WHEN-FIELD-EQUALS (procuring_entity_interest = Yes)` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `conflict_01` | Conflict of interest item 1 | `CTL-YES-NO` | `RQ-ALWAYS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `conflict_02` | Conflict of interest item 2 | `CTL-YES-NO` | `RQ-ALWAYS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `conflict_03` | Conflict of interest item 3 | `CTL-YES-NO` | `RQ-ALWAYS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `conflict_04` | Conflict of interest item 4 | `CTL-YES-NO` | `RQ-ALWAYS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `conflict_05` | Conflict of interest item 5 | `CTL-YES-NO` | `RQ-ALWAYS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `conflict_06` | Conflict of interest item 6 | `CTL-YES-NO` | `RQ-ALWAYS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `conflict_07` | Conflict of interest item 7 | `CTL-YES-NO` | `RQ-ALWAYS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `conflict_08` | Conflict of interest item 8 | `CTL-YES-NO` | `RQ-ALWAYS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `conflict_09` | Conflict of interest item 9 | `CTL-YES-NO` | `RQ-ALWAYS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `conflict_details` | Details of each conflict of interest answered Yes | `CTL-LONG-TEXT` | `RQ-WHEN-ANY-FIELD-EQUALS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-DECL-CBQ/FORM-CBQ` | `confirmed` | I certify that the information given in this questionnaire is correct. | `CTL-CONFIRMATION` | `RQ-ALWAYS` | — | `DM-DECL-CBQ` / `DM-DECL-CBQ` |
| `RR-RESERVATION/RESERVATION` | `certificate_category` | Registration category on the certificate | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-RESERVATION` / `DM-RESERVATION` |
| `RR-RESERVATION/RESERVATION` | `certificate_number` | Access to Government Procurement Opportunities registration certificate number | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-RESERVATION` / `DM-RESERVATION` |
| `RR-RESERVATION/RESERVATION` | `certificate_valid_until` | Certificate valid until | `CTL-DATE` | `RQ-ALWAYS` | — | `DM-RESERVATION` / `DM-RESERVATION` |
| `RR-RESERVATION/RESERVATION` | `certificate_evidence` | Registration certificate | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Access to Government Procurement Opportunities registration certificate (mandatory, 1–1) | `DM-RESERVATION` / `DM-RESERVATION` |
| `RR-RESERVATION/RESERVATION` | `confirmed` | I declare that the Tenderer holds the registration stated above in the published category. | `CTL-CONFIRMATION` | `RQ-ALWAYS` | — | `DM-RESERVATION` / `DM-RESERVATION` |
| `RR-TENDER-SECURITY/TENDER-SECURITY` | `security_form` | Form of Tender Security | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-TENDER-SECURITY` / `DM-TENDER-SECURITY` |
| `RR-TENDER-SECURITY/TENDER-SECURITY` | `issuer` | Issuing bank or insurer | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-TENDER-SECURITY` / `DM-TENDER-SECURITY` |
| `RR-TENDER-SECURITY/TENDER-SECURITY` | `guarantee_reference` | Guarantee number | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-TENDER-SECURITY` / `DM-TENDER-SECURITY` |
| `RR-TENDER-SECURITY/TENDER-SECURITY` | `security_evidence` | Tender Security instrument | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Tender Security instrument (mandatory, 1–1) | `DM-TENDER-SECURITY` / `DM-TENDER-SECURITY` |

### TASK-REQUIREMENTS — Requirements and supporting evidence

| Group key | Field key | Label | Control | Required rule | Evidence rule | Evaluation / contract mapping |
|---|---|---|---|---|---|---|
| `RR-GOODS-OFFER/GDS-be794a782966af680f892e94` | `offered_make_model` | Offered make and model | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-GOODS-OFFER` / `DM-GOODS-OFFER` |
| `RR-GOODS-OFFER/GDS-be794a782966af680f892e94` | `offered_delivery_date` | Offered delivery date | `CTL-DATE` | `RQ-ALWAYS` | — | `DM-GOODS-OFFER` / `DM-GOODS-OFFER` |
| `RR-GOODS-OFFER/GDS-be794a782966af680f892e94` | `evidence` | Supporting evidence for the offered goods | `CTL-EVIDENCE-REFERENCE` | `RQ-NEVER` | Datasheet, brochure or certificate (optional, 0–5) | `DM-GOODS-OFFER` / `DM-GOODS-OFFER` |
| `RR-TECHNICAL/TECH-001` | `compliance` | Compliance | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-001` | `offered_value` | Offered value | `CTL-YES-NO` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-001` | `comment` | Comment | `CTL-LONG-TEXT` | `RQ-NEVER` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-001` | `evidence` | Evidence reference | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Datasheet, brochure or certificate (mandatory, 1–5) | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-002` | `compliance` | Compliance | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-002` | `offered_value` | Offered value | `CTL-YES-NO` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-002` | `comment` | Comment | `CTL-LONG-TEXT` | `RQ-NEVER` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-002` | `evidence` | Evidence reference | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Datasheet, brochure or certificate (mandatory, 1–5) | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-003` | `compliance` | Compliance | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-003` | `offered_value` | Offered value | `CTL-INTEGER` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-003` | `comment` | Comment | `CTL-LONG-TEXT` | `RQ-NEVER` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-003` | `evidence` | Evidence reference | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Datasheet, brochure or certificate (mandatory, 1–5) | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-004` | `compliance` | Compliance | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-004` | `offered_value` | Offered value | `CTL-INTEGER` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-004` | `comment` | Comment | `CTL-LONG-TEXT` | `RQ-NEVER` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-004` | `evidence` | Evidence reference | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Datasheet, brochure or certificate (mandatory, 1–5) | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-005` | `compliance` | Compliance | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-005` | `offered_value` | Offered value | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-005` | `comment` | Comment | `CTL-LONG-TEXT` | `RQ-NEVER` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-005` | `evidence` | Evidence reference | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Datasheet, brochure or certificate (mandatory, 1–5) | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-006` | `compliance` | Compliance | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-006` | `offered_value` | Offered value | `CTL-DECIMAL` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-006` | `comment` | Comment | `CTL-LONG-TEXT` | `RQ-NEVER` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-006` | `evidence` | Evidence reference | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Datasheet, brochure or certificate (mandatory, 1–5) | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-007` | `compliance` | Compliance | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-007` | `offered_value` | Offered value | `CTL-DECIMAL` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-007` | `comment` | Comment | `CTL-LONG-TEXT` | `RQ-NEVER` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-007` | `evidence` | Evidence reference | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Datasheet, brochure or certificate (mandatory, 1–5) | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-008` | `compliance` | Compliance | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-008` | `offered_value` | Offered value | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-008` | `comment` | Comment | `CTL-LONG-TEXT` | `RQ-NEVER` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-008` | `evidence` | Evidence reference | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Datasheet, brochure or certificate (mandatory, 1–5) | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-009` | `compliance` | Compliance | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-009` | `offered_value` | Offered value | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-009` | `comment` | Comment | `CTL-LONG-TEXT` | `RQ-NEVER` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-009` | `evidence` | Evidence reference | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Datasheet, brochure or certificate (mandatory, 1–5) | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-010` | `compliance` | Compliance | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-010` | `offered_value` | Offered value | `CTL-MULTI-SELECT` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-010` | `comment` | Comment | `CTL-LONG-TEXT` | `RQ-NEVER` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-010` | `evidence` | Evidence reference | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Datasheet, brochure or certificate (mandatory, 1–5) | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-011` | `compliance` | Compliance | `CTL-SINGLE-CHOICE` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-011` | `offered_value` | Offered value | `CTL-PORTS-LIST` | `RQ-ALWAYS` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-011` | `comment` | Comment | `CTL-LONG-TEXT` | `RQ-NEVER` | — | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-TECHNICAL/TECH-011` | `evidence` | Evidence reference | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Datasheet, brochure or certificate (mandatory, 1–5) | `DM-TECHNICAL` / `DM-TECHNICAL` |
| `RR-WARRANTY-SUPPORT/WARRANTY-SUPPORT` | `confirmation` | We confirm the published minimum warranty and support obligations will be met. | `CTL-YES-NO` | `RQ-ALWAYS` | — | `DM-WARRANTY-SUPPORT` / `DM-WARRANTY-SUPPORT` |
| `RR-WARRANTY-SUPPORT/WARRANTY-SUPPORT` | `offered_warranty_months` | Offered warranty period (months) | `CTL-INTEGER` | `RQ-ALWAYS` | — | `DM-WARRANTY-SUPPORT` / `DM-WARRANTY-SUPPORT` |
| `RR-WARRANTY-SUPPORT/WARRANTY-SUPPORT` | `support_contact_details` | Warranty contact, escalation and service-centre details | `CTL-LONG-TEXT` | `RQ-ALWAYS` | — | `DM-WARRANTY-SUPPORT` / `DM-WARRANTY-SUPPORT` |
| `RR-WARRANTY-SUPPORT/WARRANTY-SUPPORT` | `evidence` | Warranty or support evidence | `CTL-EVIDENCE-REFERENCE` | `RQ-NEVER` | Warranty or support document (optional, 0–5) | `DM-WARRANTY-SUPPORT` / `DM-WARRANTY-SUPPORT` |
| `RR-EXPERIENCE/EXPERIENCE-01` | `client_name` | Client | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-EXPERIENCE` / `DM-EXPERIENCE` |
| `RR-EXPERIENCE/EXPERIENCE-01` | `contract_reference` | Contract name or reference | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-EXPERIENCE` / `DM-EXPERIENCE` |
| `RR-EXPERIENCE/EXPERIENCE-01` | `contract_value` | Contract value | `CTL-MONEY` | `RQ-ALWAYS` | — | `DM-EXPERIENCE` / `DM-EXPERIENCE` |
| `RR-EXPERIENCE/EXPERIENCE-01` | `completion_date` | Completion date | `CTL-DATE` | `RQ-ALWAYS` | — | `DM-EXPERIENCE` / `DM-EXPERIENCE` |
| `RR-EXPERIENCE/EXPERIENCE-01` | `scope` | Brief scope of the supply | `CTL-LONG-TEXT` | `RQ-ALWAYS` | — | `DM-EXPERIENCE` / `DM-EXPERIENCE` |
| `RR-EXPERIENCE/EXPERIENCE-01` | `evidence` | Completion evidence | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Completion certificate or client reference (mandatory, 1–3) | `DM-EXPERIENCE` / `DM-EXPERIENCE` |
| `RR-EXPERIENCE/EXPERIENCE-02` | `client_name` | Client | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-EXPERIENCE` / `DM-EXPERIENCE` |
| `RR-EXPERIENCE/EXPERIENCE-02` | `contract_reference` | Contract name or reference | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-EXPERIENCE` / `DM-EXPERIENCE` |
| `RR-EXPERIENCE/EXPERIENCE-02` | `contract_value` | Contract value | `CTL-MONEY` | `RQ-ALWAYS` | — | `DM-EXPERIENCE` / `DM-EXPERIENCE` |
| `RR-EXPERIENCE/EXPERIENCE-02` | `completion_date` | Completion date | `CTL-DATE` | `RQ-ALWAYS` | — | `DM-EXPERIENCE` / `DM-EXPERIENCE` |
| `RR-EXPERIENCE/EXPERIENCE-02` | `scope` | Brief scope of the supply | `CTL-LONG-TEXT` | `RQ-ALWAYS` | — | `DM-EXPERIENCE` / `DM-EXPERIENCE` |
| `RR-EXPERIENCE/EXPERIENCE-02` | `evidence` | Completion evidence | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Completion certificate or client reference (mandatory, 1–3) | `DM-EXPERIENCE` / `DM-EXPERIENCE` |
| `RR-ACCEPTANCE/ACC-001` | `confirmed` | We accept this acceptance requirement and will make the stated evidence available at inspection and acceptance. | `CTL-CONFIRMATION` | `RQ-ALWAYS` | — | `DM-ACCEPTANCE` / `DM-ACCEPTANCE` |
| `RR-ACCEPTANCE/ACC-002` | `confirmed` | We accept this acceptance requirement and will make the stated evidence available at inspection and acceptance. | `CTL-CONFIRMATION` | `RQ-ALWAYS` | — | `DM-ACCEPTANCE` / `DM-ACCEPTANCE` |
| `RR-ACCEPTANCE/ACC-003` | `confirmed` | We accept this acceptance requirement and will make the stated evidence available at inspection and acceptance. | `CTL-CONFIRMATION` | `RQ-ALWAYS` | — | `DM-ACCEPTANCE` / `DM-ACCEPTANCE` |
| `RR-ACCEPTANCE/ACC-004` | `confirmed` | We accept this acceptance requirement and will make the stated evidence available at inspection and acceptance. | `CTL-CONFIRMATION` | `RQ-ALWAYS` | — | `DM-ACCEPTANCE` / `DM-ACCEPTANCE` |
| `RR-ACCEPTANCE/ACC-005` | `confirmed` | We accept this acceptance requirement and will make the stated evidence available at inspection and acceptance. | `CTL-CONFIRMATION` | `RQ-ALWAYS` | — | `DM-ACCEPTANCE` / `DM-ACCEPTANCE` |
| `RR-EVIDENCE-MANUFACTURER-AUTHORISATION/EVIDENCE-MANUFACTURER-AUTHORISATION` | `evidence` | Manufacturer's Authorization Form | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Manufacturer's authorisation (mandatory, 1–5) | `DM-EVIDENCE-MANUFACTURER-AUTHORISATION` / `DM-EVIDENCE-MANUFACTURER-AUTHORISATION` |
| `RR-EVIDENCE-DATASHEET/EVIDENCE-DATASHEET` | `evidence` | Technical datasheets or brochures | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Datasheet or brochure (mandatory, 1–10) | `DM-EVIDENCE-DATASHEET` / `DM-EVIDENCE-DATASHEET` |
| `RR-EVIDENCE-AFTER-SALES/EVIDENCE-AFTER-SALES` | `evidence` | After-sales support evidence | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | After-sales support evidence (mandatory, 1–5) | `DM-EVIDENCE-AFTER-SALES` / `DM-EVIDENCE-AFTER-SALES` |
| `RR-EVIDENCE-ELIGIBILITY-DOCUMENTS/EVIDENCE-ELIGIBILITY-DOCUMENTS` | `evidence` | Tax compliance, registration and constitution documents | `CTL-EVIDENCE-REFERENCE` | `RQ-ALWAYS` | Eligibility and registration documents (mandatory, 1–10) | `DM-EVIDENCE-ELIGIBILITY-DOCUMENTS` / `DM-EVIDENCE-ELIGIBILITY-DOCUMENTS` |

### TASK-PRICE — Price

| Group key | Field key | Label | Control | Required rule | Evidence rule | Evaluation / contract mapping |
|---|---|---|---|---|---|---|
| `RR-PRICE-GOODS/GDS-be794a782966af680f892e94` | `unit_price` | Unit price | `CTL-MONEY` | `RQ-ALWAYS` | — | `DM-PRICE-GOODS` / `DM-PRICE-GOODS` |
| `RR-PRICE-GOODS/GDS-be794a782966af680f892e94` | `tax_amount` | Taxes payable on this line | `CTL-MONEY` | `RQ-ALWAYS` | — | `DM-PRICE-GOODS` / `DM-PRICE-GOODS` |

### TASK-REVIEW — Review and submit

| Group key | Field key | Label | Control | Required rule | Evidence rule | Evaluation / contract mapping |
|---|---|---|---|---|---|---|
| `RR-SUBMISSION/SUBMISSION` | `signatory_name` | Name of the person duly authorised to sign the Tender | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-SUBMISSION` / `DM-SUBMISSION` |
| `RR-SUBMISSION/SUBMISSION` | `signatory_title` | Title of the person signing the Tender | `CTL-SHORT-TEXT` | `RQ-ALWAYS` | — | `DM-SUBMISSION` / `DM-SUBMISSION` |
| `RR-SUBMISSION/SUBMISSION` | `confirmed` | I confirm this is the complete Tender I am authorised to sign and submit. | `CTL-CONFIRMATION` | `RQ-ALWAYS` | — | `DM-SUBMISSION` / `DM-SUBMISSION` |

### Price rows

| Line | Kind | Description | Quantity | Unit | Currency | Calculation | Bidder inputs |
|---|---|---|---|---|---|---|---|
| 1 | Goods | Business laptops | 250 | Each | KES | `CALC-LINE-TOTAL` | tax_amount, unit_price |
| Total | Tender total | Total Tender Price | 1 | tender | KES | `CALC-TENDER-TOTAL` | — |

### Declaration texts

| Text id | Rule | Version | Source locator |
|---|---|---|---|
| `TXT-RR-DECL-FORM-OF-TENDER` | `RR-DECL-FORM-OF-TENDER` | 1 | PPRA Goods STD Section IV, Form of Tender, items (a)–(s) (source pp. 40–42) |
| `TXT-RR-DECL-CITD` | `RR-DECL-CITD` | 1 | PPRA Goods STD Section IV, Certificate of Independent Tender Determination (source pp. 43–44) |
| `TXT-RR-DECL-SD1` | `RR-DECL-SD1` | 1 | PPRA Goods STD Section IV, Form SD1 (source p. 44) |
| `TXT-RR-DECL-SD2` | `RR-DECL-SD2` | 1 | PPRA Goods STD Section IV, Form SD2 (source pp. 44–45) |
| `TXT-RR-DECL-CODE-OF-ETHICS` | `RR-DECL-CODE-OF-ETHICS` | 1 | PPRA Goods STD Section IV, Declaration and Commitment to the Code of Ethics (source pp. 45–46) |
| `TXT-RR-DECL-CBQ` | `RR-DECL-CBQ` | 1 | PPRA Goods STD Section IV, Confidential Business Questionnaire, parts (e) and (f) (source pp. 50–52) |
| `TXT-RR-RESERVATION` | `RR-RESERVATION` | 1 | PPADA 2015 s.155 and PPADR 2020 reg. 149 reserved-procurement eligibility clause, Section III (KenTender generated clause, coverage COV-291) |

### Published facts per group (as frozen in the definition)

| Group key | Published facts |
|---|---|
| `RR-DOC-ACK/DOCUMENT-PACKAGE` | {"effective_addendum_ids": [], "publication_id": "TPUB-MOH-2027-033-001", "tender_reference": "TND-MOH-2027-033", "tender_title": "Supply and delivery of business laptops", "tender_version_id": "TNDV-MOH-2027-033-V2"} |
| `RR-SUPPLIER-DETAILS/SUPPLIER` | {"tender_reference": "TND-MOH-2027-033"} |
| `RR-DECL-FORM-OF-TENDER/FORM-TENDER` | {"form_id": "FORM-TENDER", "tender_reference": "TND-MOH-2027-033", "text_id": "TXT-RR-DECL-FORM-OF-TENDER", "text_version": "1"} |
| `RR-DECL-CITD/FORM-CITD` | {"form_id": "FORM-CITD", "tender_reference": "TND-MOH-2027-033", "text_id": "TXT-RR-DECL-CITD", "text_version": "1"} |
| `RR-DECL-SD1/FORM-SD1` | {"form_id": "FORM-SD1", "tender_reference": "TND-MOH-2027-033", "text_id": "TXT-RR-DECL-SD1", "text_version": "1"} |
| `RR-DECL-SD2/FORM-SD2` | {"form_id": "FORM-SD2", "tender_reference": "TND-MOH-2027-033", "text_id": "TXT-RR-DECL-SD2", "text_version": "1"} |
| `RR-DECL-CODE-OF-ETHICS/FORM-COE` | {"form_id": "FORM-COE", "tender_reference": "TND-MOH-2027-033", "text_id": "TXT-RR-DECL-CODE-OF-ETHICS", "text_version": "1"} |
| `RR-DECL-CBQ/FORM-CBQ` | {"form_id": "FORM-CBQ", "tender_reference": "TND-MOH-2027-033", "text_id": "TXT-RR-DECL-CBQ", "text_version": "1"} |
| `RR-RESERVATION/RESERVATION` | {"category": "Youth", "permitted_categories": ["Youth"], "rule_snapshot_ids": ["RULE-RES-YOUTH-V1"], "submission_deadline_date": "2027-06-05", "text_id": "TXT-RR-RESERVATION", "text_version": "1"} |
| `RR-TENDER-SECURITY/TENDER-SECURITY` | {"amount": "500000.00", "bank_guarantee_expiry_date": "2027-11-02", "currency": "KES", "insurance_guarantee_expiry_date": "2027-10-31", "permitted_forms": ["Demand Bank Guarantee", "Insurance Guarantee"], "validity_date": "2027-10-03"} |
| `RR-GOODS-OFFER/GDS-be794a782966af680f892e94` | {"currency": "KES", "description": "Business laptops", "destination": "Ministry of Health Headquarters, Afya House, Nairobi", "equipment_category": "Laptop", "latest_delivery_date": "2027-09-30", "line": "1", "minimum_warranty_months": 36, "quantity": "250", "technical_requirement_ids": ["TECH-001", "TECH-002", "TECH-003", "TECH-004", "TECH-005", "TECH-006", "TECH-007", "TECH-008", "TECH-009", "TECH-010", "TECH-011"], "unit": "Each"} |
| `RR-TECHNICAL/TECH-001` | {"applies_to": "All items", "characteristic_key": "electrical_compatibility", "comparison": "Required", "control": "YES_NO", "label": "Electrical compatibility", "options": ["Yes"], "port_options": [], "required_value": {"value": "Yes"}, "required_value_display": "Yes — suitable for Kenyan mains supply", "unit": ""} |
| `RR-TECHNICAL/TECH-002` | {"applies_to": "All items", "characteristic_key": "new_unused_equipment", "comparison": "Required", "control": "YES_NO", "label": "New and unused equipment", "options": ["Yes"], "port_options": [], "required_value": {"value": "Yes"}, "required_value_display": "Yes", "unit": ""} |
| `RR-TECHNICAL/TECH-003` | {"applies_to": "All items", "characteristic_key": "memory", "comparison": "Minimum", "control": "INTEGER", "label": "Memory", "options": [], "port_options": [], "required_value": {"value": 16}, "required_value_display": "16", "unit": "GB"} |
| `RR-TECHNICAL/TECH-004` | {"applies_to": "All items", "characteristic_key": "storage_capacity", "comparison": "Minimum", "control": "INTEGER", "label": "Storage capacity", "options": [], "port_options": [], "required_value": {"value": 512}, "required_value_display": "512", "unit": "GB"} |
| `RR-TECHNICAL/TECH-005` | {"applies_to": "All items", "characteristic_key": "storage_type", "comparison": "One of", "control": "SELECT", "label": "Storage type", "options": ["NVMe SSD", "SSD", "eMMC"], "port_options": [], "required_value": {"value": "NVMe SSD"}, "required_value_display": "NVMe SSD", "unit": ""} |
| `RR-TECHNICAL/TECH-006` | {"applies_to": "All items", "characteristic_key": "display_size", "comparison": "Minimum", "control": "DECIMAL", "label": "Display size", "options": [], "port_options": [], "required_value": {"value": "14.0"}, "required_value_display": "14.0", "unit": "inches"} |
| `RR-TECHNICAL/TECH-007` | {"applies_to": "All items", "characteristic_key": "battery_runtime", "comparison": "Minimum", "control": "DECIMAL", "label": "Battery runtime", "options": [], "port_options": [], "required_value": {"value": "8"}, "required_value_display": "8", "unit": "hours"} |
| `RR-TECHNICAL/TECH-008` | {"applies_to": "All items", "characteristic_key": "processor_requirement", "comparison": "Minimum", "control": "TEXT", "label": "Processor requirement", "options": [], "port_options": [], "required_value": {"value": "64-bit business-class processor, minimum 10 cores or equivalent benchmark"}, "required_value_display": "64-bit business-class processor, minimum 10 cores or equivalent benchmark", "unit": ""} |
| `RR-TECHNICAL/TECH-009` | {"applies_to": "All items", "characteristic_key": "operating_system_compatibility", "comparison": "Required", "control": "TEXT", "label": "Operating-system compatibility", "options": [], "port_options": [], "required_value": {"value": "Approved organisational Windows environment"}, "required_value_display": "Approved organisational Windows environment", "unit": ""} |
| `RR-TECHNICAL/TECH-010` | {"applies_to": "All items", "characteristic_key": "network_connectivity", "comparison": "Required", "control": "MULTI_SELECT", "label": "Network connectivity", "options": ["Ethernet", "Wi-Fi 5", "Wi-Fi 6", "Wi-Fi 6E", "4G", "5G", "Bluetooth 5 or later"], "port_options": [], "required_value": {"values": ["Wi-Fi 6", "Bluetooth 5 or later"]}, "required_value_display": "Wi-Fi 6 and Bluetooth 5 or later", "unit": ""} |
| `RR-TECHNICAL/TECH-011` | {"applies_to": "All items", "characteristic_key": "required_ports", "comparison": "Required", "control": "PORT_LIST", "label": "Required ports", "options": [], "port_options": ["USB-A", "USB-C", "HDMI", "DisplayPort", "Ethernet", "Audio", "Other stated port"], "required_value": {"ports": [{"minimum_count": 2, "port_type": "USB-C"}, {"minimum_count": 2, "port_type": "USB-A"}, {"minimum_count": 1, "port_type": "HDMI"}]}, "required_value_display": "USB-C ×2; USB-A ×2; HDMI ×1", "unit": ""} |
| `RR-WARRANTY-SUPPORT/WARRANTY-SUPPORT` | {"manufacturer_support_required": true, "maximum_support_response_hours": 8, "minimum_warranty_months": 36, "onsite_support_required": true, "service_location_constraint": "Within Kenya", "support_description": "Supplier to provide escalation and warranty-contact details."} |
| `RR-EXPERIENCE/EXPERIENCE-01` | {"entry_number": 1, "period_years": 5, "required_count": 2, "window_end": "2027-06-05", "window_start": "2022-06-05"} |
| `RR-EXPERIENCE/EXPERIENCE-02` | {"entry_number": 2, "period_years": 5, "required_count": 2, "window_end": "2027-06-05", "window_start": "2022-06-05"} |
| `RR-ACCEPTANCE/ACC-001` | {"applies_to": "All items", "check_type": "Quantity", "evidence_type": "Inspection record", "pass_condition": "Delivered quantities equal the authorised schedule"} |
| `RR-ACCEPTANCE/ACC-002` | {"applies_to": "All items", "check_type": "Physical condition", "evidence_type": "Inspection record", "pass_condition": "No visible damage and all listed accessories are present"} |
| `RR-ACCEPTANCE/ACC-003` | {"applies_to": "All items", "check_type": "Required specification", "evidence_type": "Inspection record", "pass_condition": "Every delivered unit complies with all mandatory technical rows"} |
| `RR-ACCEPTANCE/ACC-004` | {"applies_to": "All items", "check_type": "Functional test", "evidence_type": "Test result", "pass_condition": "Each device powers on and completes the agreed basic functional test"} |
| `RR-ACCEPTANCE/ACC-005` | {"applies_to": "All items", "check_type": "Documents received", "evidence_type": "Certificate", "pass_condition": "Warranty and delivery documents are received and verified"} |
| `RR-EVIDENCE-MANUFACTURER-AUTHORISATION/EVIDENCE-MANUFACTURER-AUTHORISATION` | {"evidence_kind": "MANUFACTURER-AUTHORISATION", "label": "Manufacturer's authorisation", "purpose": "Proves the Tenderer is duly authorised by the manufacturer or producer of the Goods offered.", "requirement_text": ""} |
| `RR-EVIDENCE-DATASHEET/EVIDENCE-DATASHEET` | {"evidence_kind": "DATASHEET", "label": "Technical datasheets or brochures", "purpose": "Proves the Goods offered conform to the published Technical Requirements.", "requirement_text": ""} |
| `RR-EVIDENCE-AFTER-SALES/EVIDENCE-AFTER-SALES` | {"evidence_kind": "AFTER-SALES", "label": "After-sales support evidence", "purpose": "Proves the Tenderer's capacity to provide after-sales support for the Goods offered.", "requirement_text": "Kenya service-centre details and escalation contacts"} |
| `RR-EVIDENCE-ELIGIBILITY-DOCUMENTS/EVIDENCE-ELIGIBILITY-DOCUMENTS` | {"evidence_kind": "ELIGIBILITY-DOCUMENTS", "label": "Eligibility and registration documents", "purpose": "Tax compliance, registration and constitution documents required by the Tenderer Information Form.", "requirement_text": ""} |
| `RR-PRICE-GOODS/GDS-be794a782966af680f892e94` | {"currency": "KES", "description": "Business laptops", "destination": "Ministry of Health Headquarters, Afya House, Nairobi", "equipment_category": "Laptop", "latest_delivery_date": "2027-09-30", "line": "1", "minimum_warranty_months": 36, "quantity": "250", "technical_requirement_ids": ["TECH-001", "TECH-002", "TECH-003", "TECH-004", "TECH-005", "TECH-006", "TECH-007", "TECH-008", "TECH-009", "TECH-010", "TECH-011"], "unit": "Each"} |
| `RR-SUBMISSION/SUBMISSION` | {"effective_addendum_ids": [], "tender_reference": "TND-MOH-2027-033", "tender_version_id": "TNDV-MOH-2027-033-V2"} |
