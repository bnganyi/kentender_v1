# Change request: a template walkthrough that shows how an STD release drives a Tender

| Control | Value |
|---|---|
| Document type | Change request. It is not a controlled version and changes no approved document. |
| Version | Not applicable: a change request, not a versioned document. If accepted, it is carried into successor versions of STD-TPL-001, TPR-CHG-001 and BDS-CHG-001. |
| Date | 2 October 2026 |
| Status | **Approved** (before approval read: **Proposal for Project Owner decision.** The scope decisions in §8 are recorded as the Project Owner stated them. The remaining decisions in §9 are not decided.) |
| Approved on | 2 October 2026 (before approval read: Not yet approved) |
| Approval record | Project Owner, 2 October 2026: "This is approved, together with your recommendations. Update the documents appropriately with care". The instruction approves this change request and the recommendations recorded against R1 to R5 in §9; see §13. (Before approval read: None.) |
| Concerns | The **STD Templates** read-only administrative surface (STD-TPL-001 §11), the Tender preparation, approval and publication record (TPR-CHG-001 §§9–11), the bid renderer (BDS-CHG-001 §§4.4.3–4.4.5) and the release validator (STD-TPL-001 §13.8) |
| Governing documents | STD-TPL-001 v0.13, Approved 27 September 2026. TPR-CHG-001 v0.15 and BDS-CHG-001 v0.10, both carrying the record "Current approval record — 1 October 2026. The Project Owner instructed: “Mark all the proposed documents as approved”." STD-ST-001 v0.5, Approved 11 September 2026. |
| Raised by | Project Owner, 2 October 2026, after the Confidential Business Questionnaire defects were found in QA during bid submission (change request "the structure of the Confidential Business Questionnaire", 2 October 2026) |
| Related change request | `KenTender_STD-TPL-001_Change_Request_Questionnaire_Structure_2026-10-02.md` (Approved; decisions D1, D2, D3 and D5 recorded; D4 open) |
| Drafted by | Claude, at the Project Owner's request |

## 1. Summary

An administrator or Procurement Officer cannot see how an installed template will behave before a real supplier meets it. The **STD Templates** surface describes a release; it does not show one working. The Confidential Business Questionnaire defects were therefore found only when QA exercised a published Tender in the supplier portal.

This request adds a **template walkthrough**: a read-only, full-screen run of a release through the stages it drives. Those stages are Tender preparation, the issued documents, the supplier bid, evaluation and contract carry-forward. The supplier bid is drawn by the real registered renderer, and each field can be inspected against its official source wording and its downstream use. The walkthrough is available in two places:

- from **STD Templates**, over the release's own shipped fixture, with no Tender needed; and
- from a Tender, over that Tender's own content: before publication from the saved Version, and after publication from the frozen Published Bid Definition.

It also adds one release-validator check. The check fails a release that publishes a supplier response without the wording of the official item it answers, or that collapses an official table into one text field.

The walkthrough is an inspection aid, not a gate. It creates no approval, commissioning or review step, consistent with owner decision OD5 (STD-TPL-001 §13.10).

## 2. What happened

These are observations. They are not rules.

- The questionnaire defects (nine Yes/No fields labelled "Conflict of interest item 1" to "Conflict of interest item 9", two official tables collapsed into single text boxes, and item 9 evaluated the wrong way round) are present in release 1.2's `response_rules.json` and `downstream_rules.json`. They were first seen on screen during a QA bid against `TND-MOH-2027-002` on 2 October 2026 (questionnaire change request, §2).
- Nothing in the product would have shown them earlier. **STD Templates** offers no view of the supplier screens. Tender preparation offers previews of the two human documents only.
- The Project Owner has asked for this capability more than once and states that the existing surface "just tells me section completeness and metadata" (Project Owner, 2 October 2026).

## 3. What the approved documents provide today

All quotations are from the version named in the control table.

### 3.1 STD Templates shows documents, not the bid

- The only preview is of the human documents. STD-TPL-001 §11.3, **Tender content**: "two output cards: **Invitation to Tender** and **Complete issued Tender**, each with section/form coverage summary and **Preview**".
- The bid is shown as summaries and counts. STD-TPL-001 §11.3, **Bid response and downstream use**: "supported controls and compositions as labelled chips/summaries, not raw schema" and "response-family counts and declaration/evidence/price treatment".
- The common actions are closed. STD-TPL-001 §11.4: "**View**, section links, Back, Preview, Download review pack, View coverage details, View change details, Report concern, filter and Clear filters are the only common actions."

### 3.2 The intended human check had no product surface and is no longer enforced

- STD-TPL-001 §13.7, Gate D: "Stop until the supplier-experience reviewer can complete the five tasks from the generated definition, and the procurement/legal reviewer confirms that every electronic obligation and declaration exists in the issued Tender."
- STD-TPL-001 §14.2, Usability gate: "Officer and supplier journeys pass representative-user review".
- Under OD5 both are evidence only. STD-TPL-001 §13: "A Pending, Incomplete or Failed review result, an open review item and a missing owner decision never block installation or use of a release." The release 1.1 fixture records "coordinated supplier-response/mapping upgrade Incomplete" (STD-TPL-001 §11.5).
- No route exists through which a reviewer could "complete the five tasks" without publishing a Tender.

### 3.3 Tender preparation previews documents only

- TPR-CHG-001 §10.6 (TPR-DES-05): "Actions **Preview Invitation** and **Preview complete Tender**, secondary and enabled."
- TPR-CHG-001 §11.3: "Generates a read-only preview from the current saved Version. Previewing does not freeze or submit it."
- The supplier response is already generated for every Version, before publication. TPR-CHG-001 §4.5: "For every Version, KenTender deterministically generates: … supplier response controls; fixed evaluation sequence and pass/fail mappings; contract-obligation projection". TPR-CHG-001 §5.4 says the review result verifies the "response schema; evaluation/contract mappings". The data needed for a Tender-level bid preview therefore already exists at review time; only a way to look at it is missing.

### 3.4 The approved documents already require what the walkthrough would let people check

- BDS-CHG-001 §4.4.2: a response row carries "Stable published identity, label, full requirement or question, response type, required/optional rule, applicability and source lineage". The nine conflict fields carry a label and no question.
- BDS-CHG-001 §4.4.2: "Every bidder-editable value must have a visible purpose".
- STD-ST-001 §13 pass condition: "every entered value has a visible tender, validation, supplier-response, evaluation or contract purpose".
- STD-ST-001 §8.3 records, as a defect seen in the Kenya eGP export, "default `YES` answers in bidder questionnaires". The walkthrough is where such a defect would be seen.

### 3.5 What STD-ST-001 §13 is, and is not

In the conversation of 2 October 2026 Claude said, before reading STD-ST-001, that its §13 might be "an approved requirement that already points at this capability". Having read it in full, that is only partly right. STD-ST-001 §13 requires "three static, no-code walkthroughs" by practising users before any implementation decision. It is a validation exercise, not a product feature. Its approval effect says: "The human walkthrough in section 13 and a separately approved narrow implementation pack remain required before implementation begins." It supports this request in principle but does not require the capability. Whether the §13 walkthroughs were held is not recorded in any document read for this request (§12).

### 3.6 Boundaries the walkthrough must respect

- BDS-CHG-001 §16: the implementation shall not "fall back to a raw-schema screen, partial workspace or Goods renderer when a definition/profile is unsupported".
- BDS-CHG-001 §12.3 item 7: "No routine **decrypt**, **preview submitted bid**, **download envelope** or **open now** control exists." BDS01-AC-080 says the same for technical and administrator views. The walkthrough never reads a supplier's Draft or submitted bid.
- TPR-CHG-001 §11.1 rule 2: "Opening a page, drawer, dialog, preview or history view never creates or changes a record." Rule 4: "The browser never calculates authority, compatibility, readiness, status, publication success, statutory dates or permitted actions."
- TPR-CHG-001 §4.5.4: the Published Bid Definition is materialised by publication authorisation, and "The definition identity and digest belong to `TenderPublication`". A pre-publication preview therefore cannot be a Published Bid Definition.
- STD-TPL-001 §11.1: "No raw JSON, database field name, digest or renderer key appears in the default reading path."
- STD-TPL-001 §11.6 grants **STD Templates** read access to Administrator, System Manager, Procurement Officer and Head of Procurement Function.

## 4. Proposal

### 4.1 What the walkthrough shows

The walkthrough follows the stages a release drives, in this order. Each stage is read-only.

| Stage | What the viewer sees | Source of what is shown |
|---|---|---|
| Tender preparation | Every fact the Tender holds, under three headings: **Inherited from the authorised Requisition**, **Entered during Tender preparation** and **Generated by KenTender**, each with its value | STD-TPL-001 §6; the fixture input or the Tender Version |
| Tender documents | The existing **Invitation to Tender** and **Complete issued Tender** previews | Unchanged from STD-TPL-001 §11.3 and TPR-CHG-001 §11.3 |
| Supplier bid | The five supplier tasks drawn exactly as a supplier will see them, by the registered renderer for the release's `renderer_profile_id` and `supported_renderer_version`, at supplier desktop width and at 390 px | The compiled bid content (§4.3) through the BDS renderer |
| Evaluation | Each evaluated response under its evaluation group, with its outcome rule and reason in plain language, as published | `downstream_rules.json` mappings in the compiled content |
| Contract | Each response's contract destination, or **Not carried forward** with its reason | The same mappings |

**Inspecting a field.** Selecting any field in the supplier bid opens a side panel with four labelled parts:

1. **Official source**: the anchored passage of the issued Tender that the field answers, with its source locator.
2. **When it applies**: requiredness and visibility in plain language, for example "Required when the answer to *Does any person in the Procuring Entity have an interest…* is Yes".
3. **How it is evaluated**: group, outcome rule and reason, or **Not evaluated** with its reason.
4. **Where it goes**: contract destination, or **Not carried forward** with its reason.

**Exercising the conditions.** The viewer may answer fields to see conditional fields appear, for example answering Yes to see a details field. Applicability is recalculated by the server with the same named rules the bid uses (BDS-CHG-001 §4.4.5), never by the browser. Nothing entered is saved, and leaving the walkthrough discards it.

**Supplied values.** Facts that the bid takes from the supplier Account, the bidder arrangement or the signatory assignment (STD-TPL-001 §8.3) are shown as clearly labelled supplied values that state their source, for example "From the bidder's Account". No supplier's real data is used. The viewer may switch between a single organisation and a joint venture so that the per-member composition can be seen.

**Field list.** A second view lists every supplier field of the release in one searchable table. Its columns are task, label, full question, control, when it applies, evaluation and contract. This is the systematic review view: nine rows reading "Conflict of interest item N" with no question are obvious in it.

### 4.2 Where it is opened

The Project Owner chose both places and a full-screen route (§8).

| Opened from | Content walked through | Who may open it |
|---|---|---|
| **STD Templates** release detail, from **Bid response and downstream use** | The release's own MoH fixture, compiled from its shipped assets | Administrator, System Manager, Procurement Officer and Head of Procurement Function, as STD-TPL-001 §11.6 already grants |
| A Tender before publication: Review and submit (TPR-DES-05), Head of Procurement Function approval (TPR-DES-06) and Accounting Officer publication authorisation (TPR-DES-07) | The current saved Version, as the existing document previews do | Those already permitted to read that Tender stage under TPR-CHG-001 §6 |
| A published Tender (TPR-DES-09) | The exact frozen Published Bid Definition, including the effective addenda | The same readers |

Each is a separate full-screen route; working routes are proposed in §6 as new content. The walkthrough opens beside the existing **Preview Invitation** and **Preview complete Tender** actions under the label **Walk through supplier bid** (new wording, §6).

### 4.3 How the content is produced

- **STD Templates.** The shared compiler `CompilePublishedBidDefinition` (STD-TPL-001 §13.7) is "deterministic, side-effect-free". At installation the template registry compiles the release's own fixture input and stores the result as part of the read-only release projection. The browser compiles nothing and parses no asset (STD-TPL-001 §11.1, TPL08-AC-019).
- **A Tender before publication.** The same compiler is applied to the saved Version to produce a preview of the bid content. It carries no `publication_id` and no `definition_digest`, is labelled as a preview of an unpublished Version, is not stored as a Published Bid Definition and is never visible to a supplier. It creates no Tender, Version, publication, task or audit business event (TPR-CHG-001 §11.1 rule 2).
- **A published Tender.** The walkthrough reads the frozen Published Bid Definition. It recompiles nothing.

### 4.4 What it never does

- It never falls back. If the renderer for the release's profile and version is not registered on the site, the supplier-bid stage shows that it cannot be drawn and why, and no other renderer or raw view is substituted (BDS-CHG-001 §16).
- It never reads a supplier's Draft, submitted bid, envelope or receipt (BDS-CHG-001 §12.3).
- It never edits, activates, switches, approves or blocks a release or a Tender. **Report concern** remains the only write action on **STD Templates** and can be opened from the walkthrough against the field being inspected.
- It shows no raw JSON, field key, rule key, digest or renderer key in the default reading path. They stay under **Technical details**.

### 4.5 One validator check

Add a check to `validate_release.py` (STD-TPL-001 §13.8):

1. **Item wording.** Every supplier-response field generated from an enumerated item or table row of an official form carries that item's official wording, as its label or its full question. The wording is digest-checked against the anchored issued-Tender text in the same way as locked declaration text (STD-TPL-001 §13.4). A label that only numbers the item fails.
2. **Table collapse.** A coverage row of `item_type` table, treated as `Supplier response`, that is answered by a single long-text field fails. (Severity when an open issue already records the collapse is decision R3, §9.)

Release 1.2 would fail both. Because the validator is a controlled asset of the release (STD-TPL-001 §4), the check takes effect in a new release.

### 4.6 Why this would have caught the questionnaire defects

| Defect | Where it shows in the walkthrough |
|---|---|
| Nine conflict fields with no wording | Supplier-bid stage, and the field list; the **Official source** panel shows the conflict wording the label lacks |
| Directors and persons-with-interest tables collapsed into text boxes | **Official source** shows a table with named columns beside a single text box |
| Item 9 evaluated the wrong way round | **How it is evaluated** shows "Yes: committee review" beside the question "Has the conflict … been resolved …?" |

The walkthrough makes these visible; a person must still look. The validator check (§4.5) catches the first two without anyone looking. Neither catches the third, which is an interpretation of the form.

### 4.7 Effect on releases already installed

The walkthrough changes no release asset. It works for releases 1.1 and 1.2 as installed, because each ships its MoH fixture input and its expected Published Bid Definition (STD-TPL-001 §4) and has a registered renderer. Release 1.2's walkthrough would show the questionnaire defects today.

## 5. Acceptance criteria proposed

No identifiers are proposed here; they are assigned in the successor versions.

1. From **STD Templates**, an authorised reader opens a full-screen walkthrough of any installed release with a registered renderer and sees the five stages in §4.1 without any Tender existing.
2. The supplier-bid stage is drawn by the exact registered renderer for the release's profile and version. Its fields, labels, questions, order, conditions and evidence rules equal what a supplier sees on a Tender published on that release from the same input.
3. Selecting a field shows its official source passage, applicability, evaluation treatment and contract destination in plain language.
4. Answering a controlling field changes applicability exactly as the bid would, by server-evaluated named rules. Nothing is saved, and no record, task or business event is created.
5. The field list shows every supplier field of the release with its task, label, full question, control, applicability, evaluation and contract treatment.
6. From a Tender before publication, the walkthrough reflects the current saved Version and is labelled as a preview of an unpublished Version. It is not stored as a Published Bid Definition and is never visible to a supplier.
7. From a published Tender, the walkthrough reflects the exact frozen Published Bid Definition and its effective addenda.
8. An unregistered renderer or unknown composition produces an explanation and no substitute view.
9. The walkthrough reads no supplier Draft, submitted bid, envelope or receipt.
10. The validator fails a release that publishes an enumerated official item without its official wording, or answers an official table with a single long-text field (subject to decision R3).
11. The walkthrough passes the KT-STD-001 v1.8 desktop, keyboard, 200% zoom and 390 px checks that STD-TPL-001 TPL08-AC-020 applies to **STD Templates**.

## 6. New content for review

None of the following comes from an approved source.

| Item | Proposed value | Note |
|---|---|---|
| Capability name | template walkthrough | Working name |
| Action label | **Walk through supplier bid** | Shown on **STD Templates** and the Tender stages in §4.2 |
| STD Templates route | `/app/std-templates/{release_id}/walkthrough` | Follows the STD-TPL-001 §11 route pattern |
| Tender route | `/app/tenders/{tender_id}/bid-walkthrough` | Follows the TPR-CHG-001 §9 route pattern |
| Stage names | Tender preparation; Tender documents; Supplier bid; Evaluation; Contract | §4.1 |
| Side-panel headings | Official source; When it applies; How it is evaluated; Where it goes | §4.1 |
| Supplied-value marker | "From the bidder's Account" and equivalents for the arrangement and signatory | §4.1 |
| Arrangement switch | Single organisation, or a joint venture of two unnamed members | No fixture names are proposed |
| Release projection extension | A compiled walkthrough projection stored at installation | Working name; no identifier is proposed |
| Validator checks | Item wording; table collapse | §4.5 |

## 7. Why this is a product change, not a fix in one module

The content belongs to the template release, the rendering to Bid Submission and the Tender-level entry points to Tenders. STD-TPL-001 §11 currently forbids any action beyond its closed list (§3.1), TPR-CHG-001 §11.1 limits optional disclosures to "View details, View source, View history and Preview document", and BDS-CHG-001 defines its renderer only for the supplier portal. Each therefore needs a successor version (§10).

## 8. Owner decisions recorded

Project Owner, 2 October 2026, answering the three questions put in the conversation of the same day: "1. Both 2. Full-screen route 3. Yes".

| # | Question as put | Decision recorded |
|---|---|---|
| S1 | Scope: template level only, or also a pre-publication preview in Tender Preparation? | **Both.** Applied in §4.2. Extending the Tender-level walkthrough to a published Tender is part of this proposal, not of the decision; see R4. |
| S2 | Placement: a sixth section of the **STD Templates** detail, or its own full-screen route? | **Full-screen route.** Applied in §4.2. |
| S3 | Add the validator check alongside the walkthrough? | **Yes.** Applied in §4.5. |

## 9. Decisions needed from the Project Owner

| # | Question | Recommendation |
|---|---|---|
| R1 | Which fixtures may the **STD Templates** walkthrough show: the MoH (Youth) fixture only, or also the isolated reservation variants? | MoH now, with the single/joint-venture switch. Add the `None`, Women, Persons-with-disabilities and County-residents variants when their fixtures are complete; STD-TPL-001 §11.5 records them as Incomplete. |
| R2 | Should the supplier-bid stage accept answers to exercise conditions, or be static? | Accept answers, evaluated by the server, never saved. Most of the questionnaire's behaviour is conditional and cannot be checked statically. |
| R3 | Validator severity when an official table is collapsed into text and `open_issues.md` already records it. | Item-wording failures always fail. A recorded table collapse is reported as a warning and shown in the walkthrough and in **Verification**; an unrecorded one fails. This keeps the existing route (STD-TPL-001 §13.1: new vocabulary "is first recorded in `open_issues.md`") without letting a collapse pass silently. |
| R4 | Should the Tender-level walkthrough also be offered on a published Tender (TPR-DES-09), over the frozen definition? | Yes. It costs no compilation and is the quickest way to answer a supplier clarification about what a field asks. |
| R5 | Which release carries the validator check? | The same release as Part A of the questionnaire change request, so that the check proves Part A on its first run. |

## 10. Corrections and follow-through in other documents

These are required if the proposal is accepted. None has been made.

- **STD-TPL-001.** A successor version. STD-TPL-001 §3 (the **STD Templates** row of the ownership table); STD-TPL-001 §3.1 (`InstalledSTDReleaseProjection v1` gains the compiled walkthrough content, or a new projection is named); STD-TPL-001 §11.1 and §11.3 (the walkthrough entry under **Bid response and downstream use**); a new static design subsection for the walkthrough route under STD-TPL-001 §11; STD-TPL-001 §11.4 (the closed list of common actions); STD-TPL-001 §11.5 (fixture facts for the walkthrough); STD-TPL-001 §11.6 (access, unchanged in substance); STD-TPL-001 §13.8 (the new check); STD-TPL-001 §14.2 (the Inspection gate names the walkthrough); STD-TPL-001 §15 (acceptance criteria); STD-TPL-001 §18 (change register). Version numbering must be coordinated with the successor versions for Parts A and B of the questionnaire change request, which are being prepared separately.
- **STD-TPL-IMP-001.** Compiling and storing the walkthrough content at installation; the walkthrough read service. Not read for this request.
- **BDS-CHG-001.** A read-only walkthrough mode of the registered renderer, usable inside the internal Desk shell, with saving and every supplier action inert, and server evaluation of named rules without a Draft (BDS-CHG-001 §§4.4.3, 4.4.5, 7.4, 9 and 16). BDS-CHG-001 §12.3 item 7 is unaffected because the walkthrough never reads submitted content; the successor should say so.
- **TPR-CHG-001.** The walkthrough action on TPR-DES-05, TPR-DES-06, TPR-DES-07 and, subject to R4, TPR-DES-09 (TPR-CHG-001 §§10.6–10.8 and 10.10); the route (TPR-CHG-001 §9); a read service beside `GetTenderReview` (TPR-CHG-001 §7.1); the interaction rules (TPR-CHG-001 §§11.1 rule 14 and 11.3); acceptance criteria (TPR-CHG-001 §14).
- **AUTH-ADR-001.** Confirm that the existing **STD Templates** and Tender read assignments cover the new routes. Not read for this request.
- **KT-DOC-CTRL-001.** Record this change request and, on acceptance, the successor versions. The register entry for STD-TPL-001 already lags at v0.10 (questionnaire change request, §9).
- **Existing stale references.** TPR-CHG-001 v0.15 and BDS-CHG-001 v0.10 both cite STD-TPL-001 v0.10 as an owner contract, for example TPR-CHG-001 control table "Owner contracts" and BDS-CHG-001 §17 ("STD-TPL-001 v0.10 for the `IT-EQUIPMENT-OPEN-V1` product profile…"), although STD-TPL-001 v0.13 was approved on 27 September 2026. Their successors should reconcile the citation. This finding is independent of this request.

## 11. Approval effect

This change request is a proposal. It approves nothing and changes no approved document, template asset or register entry. The Project Owner's decisions S1 to S3 (§8) are recorded as stated; decisions R1 to R5 (§9) remain open. Each accepted part is made in a successor version of the affected document and approved on its own, through the normal document-change process.

(Updated on approval, 2 October 2026.) This change request is approved by the Project Owner, together with the recommendations in §9 (instruction quoted in the control table; decisions recorded in §13). The approval changes no approved document, template asset or register entry by itself. The accepted proposal is carried into a successor version of STD-TPL-001 proposed for approval on its own, and into successor versions of TPR-CHG-001 and BDS-CHG-001 still to be drafted (§10). The paragraph above is retained as the before-approval reading.

## 12. Read list and not verified

- **Read in full:** STD-TPL-001 v0.13; STD-ST-001 v0.5; the questionnaire change request of 2 October 2026.
- **Read in part:** BDS-CHG-001 v0.10 (control table, §§1, 3, 4.4–4.4.8, 7.4, 9, 10 opening, 10.7, 10.9, 12.3 item 7, 14.8, 16, and the citations of STD-TPL-001); TPR-CHG-001 v0.15 (control table, §§4.5–4.5.4, 5.4, 5.5, 7.1, 9, 10.6–10.8, 10.10, 11.1–11.3, 16, and the citations of STD-TPL-001).
- **Not read:** STD-TPL-IMP-001, AUTH-ADR-001, KT-STD-001, EVL-CHG-001, KT-DOC-CTRL-001 and the release assets themselves.

Not verified:

- Whether the STD-ST-001 §13 walkthroughs were ever held.
- Whether STD-TPL-IMP-001 already stores a compiled fixture definition in the installed release, which would simplify §4.3.
- How the Evaluation module presents a field to the committee. The walkthrough's evaluation stage shows the release's published mapping, not EVL-CHG-001's screens.
- Whether the BDS renderer can run inside the Desk shell without change; BDS-CHG-001 §9 defines the supplier experience as "a Website portal, not Frappe Desk".
- Whether the approval records at the head of TPR-CHG-001 v0.15 and BDS-CHG-001 v0.10 agree with the register; both documents' internal text still describes parts of themselves as proposed (for example BDS-CHG-001 BDS06-AC-001: "this v0.10 BDS successor remains proposed").

## 13. Owner decisions recorded on approval

Project Owner, 2 October 2026: "This is approved, together with your recommendations. Update the documents appropriately with care". It is applied to each open decision in §9 as follows.

| # | Decision recorded | Basis |
|---|---|---|
| R1 | **Decided as recommended:** the **STD Templates** walkthrough shows the MoH (Youth) fixture now, with the single-organisation and joint-venture switch. The `None`, Women, Persons-with-disabilities and County-residents variants are added when their fixtures are complete. | §9 R1 recommendation |
| R2 | **Decided as recommended:** the supplier-bid stage accepts answers to exercise conditions. The server evaluates them with the bid's named rules and nothing is saved. | §9 R2 recommendation |
| R3 | **Decided as recommended:** missing item wording always fails validation. An official table collapsed into text fails unless `open_issues.md` records the collapse, in which case it is a warning shown in the walkthrough and in **Verification**. | §9 R3 recommendation |
| R4 | **Decided as recommended:** the Tender-level walkthrough is also offered on a published Tender (TPR-DES-09), over the frozen Published Bid Definition. | §9 R4 recommendation |
| R5 | **Decided as recommended:** the validator checks are carried by the same release as Part A of the questionnaire change request. | §9 R5 recommendation |

**What this does not do.** It does not change STD-TPL-001, TPR-CHG-001, BDS-CHG-001, any template asset or the register, and it does not approve the content of the successor versions. Each is approved on its own.
