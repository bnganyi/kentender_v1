# Change request: the structure of the Confidential Business Questionnaire in the IT Equipment Open Tender template

| Control | Value |
|---|---|
| Document type | Change request. It is not a controlled version and changes no approved document. |
| Version | Not applicable: a change request, not a versioned document. If accepted, it is carried into successor versions of STD-TPL-001. |
| Date | 2 October 2026 |
| Status | **Approved** (before approval read: **Proposal for Project Owner decision.** Nothing here is decided.) |
| Approved on | 2 October 2026 |
| Approval record | Project Owner, 2 October 2026: "Mark it as approved". The instruction approves this change request as a document. It does not state an answer to any of the decisions D1 to D5 in §8; see §11. Later the same day the Project Owner stated: "I approve the recommendations". That instruction is recorded against D1 to D5 in §12. |
| Concerns | Template `IT-EQUIPMENT-OPEN-V1`, release 1.2 (`release_manifest.json`: `"template_release": "1.2"`, status `Candidate`), form `FORM-CBQ` (the Tenderer's Eligibility Confidential Business Questionnaire) and the response rule `RR-DECL-CBQ` |
| Governing document | STD-TPL-001 v0.13, Approved 27 September 2026 (control table, `Approved on`). Note: the baseline register KT-DOC-CTRL-001 still lists STD-TPL-001 as v0.10 (`KenTender_Baseline_Register.yaml`, entry `STD-TPL-001`). The register lags the approved document and needs correcting; see §9. |
| Raised by | QA test of the supplier bid screens on 2 October 2026 (screenshots supplied in the working session; they are not stored in the repository) |
| Drafted by | Claude Code, at the Project Owner's request |

## 1. Summary

A supplier filling in the questionnaire meets two problems that come from how the template publishes the form, not from the portal that shows it.

1. **Nine conflict-of-interest questions have no wording.** The template publishes each as a Yes/No field labelled only "Conflict of interest item 1" to "Conflict of interest item 9". The words of each conflict are in the long locked form text above the fields. The supplier has to scroll up and match numbers. The evaluation rule for the same fields ends "otherwise fail with the item named", so an evaluator reading "item 3" meets the same problem.
2. **Tables on the official form are collapsed into one text box.** The official form has a table of directors (name, nationality, citizenship, % shares) and a table of persons with an interest (name, designation, interest). The template publishes each as a single long-text field.

A related defect in the same form is also recorded here (§5.3): item 9 on the official form is worded the opposite way round to items 1 to 8, and the template treats it the same way as the others.

We ask for a decision on two separable parts (§6):

- **Part A**: give each conflict item its own wording and its own "details if Yes". It needs no new control and stays inside the existing vocabulary.
- **Part B**: replace the collapsed tables with repeating rows. It needs a new composition, so it is a vocabulary change.

Neither part can be made in Bid Submission. Bid Submission draws the form exactly as published (§7).

## 2. What was observed

These are observations from a QA session on 2 October 2026 against Tender `TND-MOH-2027-002`. They are not rules.

- The questionnaire drawer shows nine Yes/No questions headed "Conflict of interest item 1" to "Conflict of interest item 9", each with the help line "Disclosure of Interest item (ii) N." and no conflict wording.
- Ownership is one text box labelled "Owner, partner or director details (name, nationality, citizenship and percentage of shares owned)".
- The QA tester described the ownership box as compound questions collapsed into one, and the item labels as making no sense.

## 3. What the official form requires

The template is built from the PPRA standard tender document held at `docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1/01_source/ppra_goods_std_official.txt` (Tenderer's Eligibility Confidential Business Questionnaire Form, source pages 50 to 52; `forms_register.csv`, row `FORM-CBQ`). Wording below is quoted from that text.

**Sole proprietor (section (b)):** "Sole Proprietor, provide the following details. Name in full; Age; Nationality; Country of Origin; Citizenship".

**Partners (section (c)):**

> c) Partnership, provide the following details.
> Names of Partners   Nationality   Citizenship   % Shares owned
> 1  2  3

**Directors of a registered company (section (d), item iii):**

> iii) Give details of Directors as follows.
> Names of Director   Nationality   Citizenship   % Shares owned
> 1  2  3

**Persons with an interest in the firm (section (e), item i):**

> (i) Are there any person/persons in …………… (Name of Procuring Entity) who has an interest or relationship in this firm? Yes/No………………………
> If yes, provide details as follows.
> Names of Person   Designation in the Procuring Entity   Interest or Relationship with Tenderer
> 1  2  3

**Conflict of interest disclosure (section (e), item ii):** a table with the columns "Type of Conflict", "Disclosure YES OR NO" and "If YES provide details of the relationship with Tenderer", and nine rows. The nine types, as the source words them, are listed in Appendix A.

## 4. What the approved documents say

All quotations are from STD-TPL-001 v0.13 unless another file is named.

- **The controls are a closed set.** STD-TPL-001 §8.2: "The renderer accepts only released controls: confirmation, yes/no, controlled single choice, controlled multi-select, short text, long text, integer, decimal, money, date, evidence reference and structured ports list." It adds that the ports list is "not an arbitrary nested-form facility".
- **Unknown vocabulary blocks publication.** STD-TPL-001 §8.2: "Unknown controls, compositions, validations or renderer versions block publication and Bid start. There is no generic fallback." And the repetition clause: "An unknown repetition, source, fact or parameter is Blocking."
- **Repetition is a closed set too, and has been extended before.** "A composition's repetition rule is `one` or `per_source`. From release 1.2 (v0.13) it may also be `per_arrangement_member`, which repeats the composition once for each member of the bidder's joint-venture arrangement." The change entry TPL13-CHG-003 records why: "Joint-venture members were one free-text field". This is a precedent for the same kind of change, made by an owner decision (OD-E, 26 September 2026).
- **New vocabulary is recorded first.** "A proposed additional file, response type, evaluation group, contract destination, control or composition is first recorded in `open_issues.md`; it is not silently introduced."
- **Declaration wording is digest-checked.** "The response-definition assets may repeat locked declaration text only where the electronic supplier must affirm it. Such a rule records the official source locator and a normalized source-text digest. The validator must prove that the electronic text and the corresponding human-readable anchored text are identical."
- **The collapse is a known open issue.** `05_review/open_issues.md`, item 71: "Joint-venture members and Confidential Business Questionnaire ownership tables are captured as bounded long text | **For review — Gate D** | The released control vocabulary (STD-TPL-001 §8.2) has no nested repeating form other than the structured ports list, so these official tables cannot be itemised electronically in this release." (Joint-venture members were since made structured by v0.13; the questionnaire tables were not.) Item 43 of the same file already asks: "needs a product decision on whether to restore a repeatable table (and how many rows) rather than a text substitution."
- **The questionnaire's coverage entries** treat the conflict table as a table: `coverage_register.csv`, `COV-215`: "Confidential Business Questionnaire - (e) Disclosure of Interest / Conflict of interest table (items 1-9)", type `table`, treatment `Supplier response`. `forms_register.csv`, `FORM-CBQ`, lists the supplier fields as "Business structure detail blocks; Disclosure of Interest / Conflict of interest table (items 1-9); certification name/title/signature/date".

## 5. What the template publishes today

Source: `06_runtime/response_rules.json` (release 1.2), rule `RR-DECL-CBQ`; `06_runtime/downstream_rules.json` and `evaluation_rules/IT-EQUIPMENT-OPEN-V1.json` for the mappings.

### 5.1 The fields

| Field key | Control | Label as published | Rule |
|---|---|---|---|
| `business_structure` | single choice | Business structure | required; Sole proprietor, Partnership or Registered company |
| `ownership_details` | long text | Owner, partner or director details (name, nationality, citizenship and percentage of shares owned) | required; 10 to 4000 characters |
| `trade_licence` | short text | Current trade licence number and expiry date | required |
| `maximum_business_value` | money | Maximum value of business the Tenderer handles | required |
| `procuring_entity_interest` | yes/no | Does any person in the Procuring Entity have an interest or relationship in this firm? | required |
| `procuring_entity_interest_details` | long text | Names, designation in the Procuring Entity and the interest or relationship | required when the answer above is Yes; 10 to 2000 characters |
| `conflict_01` to `conflict_09` | yes/no | "Conflict of interest item 1" to "Conflict of interest item 9"; help "Disclosure of Interest item (ii) 1." to "(ii) 9." | required |
| `conflict_details` | long text | Details of each conflict of interest answered Yes | required when any of the nine is Yes (`RQ-WHEN-ANY-FIELD-EQUALS`); 10 to 4000 characters |
| `confirmed` | confirmation | I certify that the information given in this questionnaire is correct. | required |

### 5.2 How the answers are used

- `DM-DECL-CBQ` (evaluation): "Pass when the questionnaire is certified and no unresolved conflict of interest is disclosed; otherwise fail with the item named." Treatment: Evaluated, group `EVG-ELIGIBILITY`; contract treatment "Not carried forward".
- Each of `conflict_01` to `conflict_09` has the evaluation rule kind `review-if-yes`, with the reason "A disclosed interest or conflict must be assessed by the committee."
- `business_structure`, `ownership_details`, `trade_licence` and `maximum_business_value` have the kind `recorded`: kept, not evaluated.

### 5.3 A related defect: item 9 reads the other way round

Items 1 to 8 on the official form describe a conflict, so Yes is the disclosure. Item 9 is a question about resolution:

> Has the conflict stemming from such relationship stated in item 7 and 8 above been resolved in a manner acceptable to the Procuring Entity throughout the tendering process and execution of the Contract?

For item 9, Yes is the reassuring answer. The template gives `conflict_09` the same rule as the others (`review-if-yes`, and Yes counts towards "any conflict answered Yes" for `conflict_details`). A tenderer with no conflict, for whom item 9 does not arise, has no truthful answer; a tenderer who truthfully says Yes (resolved) sends their bid to committee review as if they had disclosed a conflict. This has not been confirmed against how the evaluation presents it on screen; it is read from the rules above.

## 6. Proposal

### Part A: wording and detail for the nine conflict items (existing vocabulary)

| What changes | Basis |
|---|---|
| The label of each `conflict_NN` becomes the wording of that conflict type from the official form (Appendix A), kept as the help line "Disclosure of Interest item (ii) N." | Official form, section (e) item ii; §4 on digest-checked declaration wording |
| The single `conflict_details` box is replaced by one "If YES, provide details of the relationship with Tenderer" long-text field per item, shown and required only when that item is Yes | Official form column "If YES provide details of the relationship with Tenderer". Existing rule kinds are enough: `RQ-WHEN-FIELD-EQUALS` and `VS-WHEN-FIELD-EQUALS` are already used for `procuring_entity_interest_details` |
| `DM-DECL-CBQ` keeps its outcome rule; its "fail with the item named" now names an item with words | `downstream_rules.json` |

No new control, composition or renderer version is needed. It is a new template release with the validator, fixtures and digests re-run. Tenders already published keep the release they were published with (STD-TPL-IMP-001 is, per the register, the "Immutable installed-release runtime"; the Tenders specification, read in the TPR-CHG-001 v0.16 working copy (status not checked), states "The response schema cannot add a criterion that is absent from the published Tender").

### Part B: repeating rows for the tables (new vocabulary)

| What changes | Basis |
|---|---|
| A **repeating row group** (working name; no identifier is proposed here) with fixed, named columns and a bounded row count, as a released composition and a new renderer version | STD-TPL-001 §8.2 and its repetition clause need extending, as TPL13-CHG-003 did for joint-venture members |
| Partners table (section (c)) and directors table (section (d) item iii), each: name, nationality, citizenship, % shares owned, replacing the `ownership_details` text box. The official form has separate Sole Proprietor, Partnership and Registered Company blocks; whether the blocks are shown according to `business_structure` is for the owner | Official form sections (b) to (d); open issue 43 |
| Persons-with-interest table: name, designation in the Procuring Entity, interest or relationship, replacing `procuring_entity_interest_details` | Official form section (e) item i |
| The recorded (not evaluated) treatment of ownership stays; the evaluation rule for `procuring_entity_interest` stays `review-if-yes` | `evaluation_rules/IT-EQUIPMENT-OPEN-V1.json` |

Per the one-concern-per-version discipline, Part B should be its own version of STD-TPL-001, separate from Part A.

### Part C: item 9

Decide how item 9 is treated so its answer is read the right way round (§5.3). This is an interpretation of the form, so it is the owner's decision (§8, D2).

## 7. Why this cannot be fixed in the portal

Bid Submission builds each bid from the exact published bid definition and draws what it contains. The labels, the field list and the rules are fixed by the published release, and the definition carries a digest. Wording or fields that are not in the definition cannot be supplied by the portal without breaking that integrity. The portal can only change how the published fields are drawn.

## 8. Decisions needed from the Project Owner

| # | Question | Recommendation |
|---|---|---|
| D1 | Approve Part A (official wording and per-item details for the nine conflict items) as a new template release? | Yes. It needs no new vocabulary and fixes what both the supplier and the evaluator read. |
| D2 | How should item 9 be read? Options: (a) keep the official wording, show it only when item 7 or 8 is Yes (the `VS-WHEN-ANY-FIELD-EQUALS` rule exists), and treat No (unresolved) as the answer that needs committee assessment; (b) keep it as today. | (a), subject to the owner's reading of the form. This is a legal and procurement interpretation that no approved document states. |
| D3 | Approve Part B (a bounded repeating row group, as a new composition and renderer version), as a separate version after Part A? | Yes, separately scoped. It answers open issues 43 and 71. |
| D4 | How many rows? The official form prints three. | The owner decides. Options are three as printed, or a larger bounded number so a firm with more than three directors can list them all. No figure beyond the printed three is proposed here. |
| D5 | Tenders already published (including the QA test Tender) keep release 1.2. Accept that, or re-issue them? | Accept for published Tenders; the change applies to Tenders published on the new release. |

## 9. Corrections and follow-through in other documents

These are required if the proposal is accepted. None has been made.

- **KT-DOC-CTRL-001 (baseline register):** correct the `STD-TPL-001` entry from v0.10 to the approved v0.13. This is independent of the proposal.
- **STD-TPL-001:** a successor version for each part: STD-TPL-001 §8.2 (controls and compositions), STD-TPL-001 §8.3 (response generation), the repetition clause, the STD-TPL-001 §18 change register, `forms_register.csv` (`FORM-CBQ` supplier fields), `coverage_register.csv` (`COV-214`, `COV-215`), `open_issues.md` (items 43 and 71 closed, and the new vocabulary first recorded there, as the document requires), and `response_rules.json`, the human-readable anchors and the normalized text digests.
- **STD-TPL-IMP-001:** the compiler and renderer registry for a new renderer version (Part B only).
- **BDS-CHG-001:** the definition model and the response drawer would need a repeating-row control (Part B only); Part A needs no portal change.
- **EVL-CHG-001 and the evaluation rules:** the mapping for any new fields (`review-if-yes` per item, item 9 handling), and the reasons shown to the committee.
- **Seeds, fixtures and tests:** the canonical seed answers the questionnaire; its answers would change with the new fields.

## 10. Not verified

- The legal status of adapting the PPRA form's wording into electronic fields: no primary source on this was read. The proposal keeps the official wording verbatim for that reason.
- STD-TPL-001 v0.13 was read in part (the passages quoted above, its control table and change register entries). It was not read in full. STD-TPL-IMP-001, BDS-CHG-001 and EVL-CHG-001 were not read for this request.
- Whether the nominal and issued capital items of the official form (section (d), item ii) are captured anywhere in the template.
- How the evaluation screen presents a Yes on `conflict_09` to the committee (§5.3 is read from the rules).
- How `complete_tender.html` (the human-readable Tender) shows the nine conflict wordings. `open_issues.md` records, in its Gate D remediation table, that the partner and director detail "restored as repeatable static tables (3 rows each)" in that document; that is the printed form, not the electronic response.
- The effect of Part B on the template validator and the release digest was not assessed.

## 11. Approval effect

This change request is approved by the Project Owner (instruction quoted in the control table). The instruction does not state an answer to decisions D1 to D5 (§8); they remain the recommendations recorded there until the Project Owner states them. This approval changes no approved document, template asset or register entry, and creates no successor version or template release. STD-TPL-001 v0.13 stays the governing approved version, and template release 1.2 is unchanged. (Updated later on 2 October 2026: the Project Owner's instruction "I approve the recommendations" is recorded against D1 to D5 in §12; D4 remains open.) (Before approval read: This change request approves nothing and changes no approved document, template asset or register entry. STD-TPL-001 v0.13 stays the governing approved version, and template release 1.2 is unchanged. A decision on D1 to D5 is recorded by the Project Owner; each accepted part is then made in a successor version of STD-TPL-001 and a new template release, through the normal document-change process.)

## 12. Owner decisions recorded

Project Owner, 2 October 2026, after the document was approved (§11): "I approve the recommendations". It is applied to each decision in §8 as follows. Where §8 gave no recommendation, nothing is recorded as decided.

| # | Decision recorded | Basis |
|---|---|---|
| D1 | **Decided as recommended:** Part A (official wording and per-item details for the nine conflict items) is to be made as a new template release. | §8 D1 recommendation: "Yes." |
| D2 | **Decided as recommended:** option (a). Keep the official wording of item 9, show it only when item 7 or item 8 is Yes, and treat No (unresolved) as the answer that needs committee assessment. | §8 D2 recommendation: "(a), subject to the owner's reading of the form." The owner's approval is taken as that reading. The legal reading is still not verified against a primary source (§10). |
| D3 | **Decided as recommended:** Part B (a bounded repeating row group, as a new composition and renderer version) is to be made, as a separate version after Part A. | §8 D3 recommendation: "Yes, separately scoped." |
| D4 | **Decided, 2 October 2026, working session: 10 rows; the first row is required and the rest are optional.** The Project Owner chose "10 rows, optional (Recommended)". (Earlier on 2 October this read: **Not decided.** The number of rows remains open.) | §8 D4 gave no recommendation, only the owner's choice between three as printed and a larger bounded number, so the instruction gives nothing to apply. A figure is needed before Part B is drafted. |
| D5 | **Decided as recommended:** Tenders already published keep release 1.2; the change applies to Tenders published on the new release. | §8 D5 recommendation: "Accept for published Tenders". |
| D6 | **Decided, 2 October 2026, working session:** in a partners table and in a directors table the percentages of shares owned must total 100. | Project Owner: "Should shares be checked? Yes, must total 100". |
| D7 | **Decided, 2 October 2026, working session:** the same person appearing in more than one table, or in the same table of another party, is not a problem and is not cross-checked. | Project Owner: "Ownership across the whole Tender: No issue". |
| D8 | **Decided, 2 October 2026, working session:** the amount and the currency of a commission, gratuity or fee are two cells, not one. | Project Owner: "Money cell in commissions: two cells". |
| D9 | **Decided, 2 October 2026, working session; the reading below is to be confirmed:** a table asks for rows only when the question that governs it is answered Yes. | Project Owner: "Which tables are required: Only if yes". Read here as: persons with an interest needs rows only when that question is answered Yes; partners only for the Partnership structure and directors only for the Registered company structure (both already conditional in release 1.3). The commissions table has no Yes/No question in the official form, which says "none"; applying this decision needs a new Yes/No question for it, which has not been decided. |

**What this does not do.** It does not change STD-TPL-001, any template asset or the register, and it does not approve the content of the new release. Part A and Part B are each drafted as a successor version of STD-TPL-001 and approved on their own, through the normal document-change process (§9). STD-TPL-001 v0.13 stays the governing approved version until then.

## Appendix A. The nine conflict types as the official form words them

Source: `ppra_goods_std_official.txt`, section (e) item (ii), "Conflict of interest disclosure". Quoted without change; line breaks joined.

| # | Type of conflict |
|---|---|
| 1 | Tenderer is directly or indirectly controlled by or is under common control with another tenderer. |
| 2 | Tenderer receives or has received any direct or indirect subsidy from another tenderer. |
| 3 | Tenderer has the same legal representative as another tenderer |
| 4 | Tender has a relationship with another tenderer, directly or through common third parties that puts it in a position to influence the tender of another tenderer, or influence the decisions of the Procuring Entity regarding this tendering process. |
| 5 | Any of the Tenderer's affiliates participated as a consultant in the preparation of the design or technical specifications of the works that are the subject of the tender. |
| 6 | Tenderer would be providing goods, works, non-consulting services or consulting services during implementation of the contract specified in this Tender Document. |
| 7 | Tenderer has a close business or family relationship with a professional staff of the Procuring Entity who are directly or indirectly involved in the preparation of the Tender document or specifications of the Contract, and/or the Tender evaluation process of such contract. |
| 8 | Tenderer has a close business or family relationship with a professional staff of the Procuring Entity who would be involved in the implementation or supervision of the Contract. |
| 9 | Has the conflict stemming from such relationship stated in item 7 and 8 above been resolved in a manner acceptable to the Procuring Entity throughout the tendering process and execution of the Contract? |

Two points in the source are flagged for the owner, not corrected here: item 3 ends without a full stop, and item 4 begins "Tender has" where "Tenderer has" appears to be meant. The wording above is kept exactly as the source gives it.
