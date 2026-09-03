# STD-TPL-IMP-001 — IT Equipment Tender Implementation Pack

| Control | Value |
|---|---|
| Document ID | STD-TPL-IMP-001 |
| Version | 0.2 |
| Date | 28 August 2026 |
| Status | Proposed for approval |
| Product | `IT-EQUIPMENT-OPEN-V1` Version 1.0 |
| Application | `kentender_procurement` |
| Starts from | One authorised Procurement Requisition |
| Ends at | One approved, immutable publication handoff |
| Implementation authority | None until this pack is approved |

## 1. Outcome

Implement one working Tender Preparation journey for straightforward IT equipment:

```text
Authorised Requisition
        ↓
IT Equipment — Open Tender
        ↓
Five Procurement Officer tasks
        ↓
Readiness and complete preview
        ↓
Author submits
        ↓
Approver returns or approves
        ↓
Immutable publication package
```

The implementation must reproduce the approved KEBS golden fixture.

There is no STD Configuration module. The template is code-owned and installed with the application.

## 2. Controlling material

Claude must read these before changing code:

1. `STD-ST-001 v0.3 — Approved`;
2. `STD-TPL-001 v0.3` and its final `05_review/review_record.md`;
3. the complete approved folder:
   `docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1`;
4. `TPR-CHG-001 v0.3`; and
5. this implementation pack.

The approved template masters, registers, fixture and recorded digests control the Tender content. Do not reconstruct the template from this document.

If the final review record does not say **APPROVE FOR IMPLEMENTATION PACK**, stop.

## 3. Hard boundaries

Implement only:

- the `IT-EQUIPMENT-OPEN-V1` template;
- one authorised Requisition per Tender;
- the five fixed Tender Preparation tasks;
- Author and Approver actions;
- readiness, preview and return;
- approval and immutable publication handoff; and
- the KEBS fixture and focused tests.

Do not add:

- an STD Library or STD Configuration screen;
- editable clauses, schemas, mappings or steps;
- manifests or generic template records;
- Configurator, Reviewer or capability-profile roles;
- a second permission system;
- AI, PDF parsing or OCR in production;
- multiple Requisitions, lots or multiple currencies;
- weighted evaluation or a criterion builder;
- complex IT, WORKS or consulting controls;
- bidder submission, evaluation, award, contract management or publication; or
- compatibility code for the retired STD Engine.

Do not replace a control defined by `TPR-CHG-001 v0.3` with a generic text input. Do not accept a value merely because it can be stored in a Frappe Data field.

Task 3 must never contain Procurement Officer-entered unit prices, taxes, line totals or Tender totals. Those are supplier-response values and remain blank in Tender Preparation.

Do not delete the retired implementation during this work. The new journey must not call it or expose it in new routes. Removal is a separate change after this slice passes.

## 4. Repository placement

Work from:

```bash
cd /home/midasuser/kentender/apps/kentender_v1
```

Use the existing Tender Preparation module inside `kentender_procurement` if it exists. If it does not exist, create:

```text
kentender_procurement/kentender_procurement/tender_preparation/
```

Place the released bundle at:

```text
kentender_procurement/kentender_procurement/tender_templates/
└── it_equipment_open_v1/
    ├── metadata.json
    ├── source_record.json
    ├── coverage_register.csv
    ├── insertion_points.csv
    ├── forms_register.csv
    ├── templates/
    │   ├── invitation_to_tender.html
    │   ├── complete_tender.html
    │   └── print.css
    └── tests/
        └── fixtures/
            ├── kebs_input.json
            ├── kebs_expected.html
            ├── kebs_invitation_expected.html
            ├── kebs_technical_specification.pdf
            └── package_index.md
```

Copy these files from the approved curation folder. Do not retype or regenerate their legal content during implementation.

Do not install the curation-only `render_fixture.py` as runtime code.

## 5. Minimal records

Before creating a DocType, inspect the repository for an existing record with the same purpose. Reuse it only if it supports the fields and rules below without a compatibility layer. Do not create parallel legacy and new models.

### 5.1 Supported Tender Template

One read-only registry row installed from the bundle:

| Field | Required value |
|---|---|
| Template key | `IT-EQUIPMENT-OPEN-V1` |
| Template version | `1.0` |
| Display name | `IT Equipment — Open Tender` |
| Supported category | `Goods — IT equipment` |
| Supported method | `Open Tender` |
| Official source title | From the approved source record |
| Official source digest | From the approved source record |
| Bundle digest | Calculated from the released bundle |
| Availability | `Available for new Tenders` or `Historical only` |

No user may edit this record. The registry points to the code bundle; it does not contain an editable copy of the template.

### 5.2 Procurement Tender

The stable root record contains only:

- Tender reference;
- source Requisition handoff;
- Procuring Entity, financial year and Plan Item;
- template key, version, source digest and bundle digest;
- current state;
- current Version number;
- approved Version;
- publication-handoff reference;
- record version; and
- created-by and created-at audit fields.

Allowed states are only:

- `Draft`;
- `Submitted for Approval`; and
- `Approved for Publication`.

Return and reopen are recorded actions that create a Draft successor. They are not additional standing states.

### 5.3 Procurement Tender Version

One Version holds the exact values for the five tasks and:

- Version number and parent Tender;
- source Requisition snapshot digest;
- author;
- locked status and Version digest;
- submission actor and time;
- return actor, time and correction, where returned;
- approval actor and time, where approved;
- readiness digest, time and counts; and
- rendered-preview file references and digests.

A submitted, returned or approved Version is immutable. A return or permitted reopen creates a copied Draft successor.

### 5.4 Fixed child tables

Use only these child tables on the Tender Version:

1. **Tender Goods Item**
   - row number;
   - description;
   - quantity;
   - unit;
   - delivery location;
   - latest delivery date; and
   - minimum warranty months.

2. **Tender Related Service**
   - description;
   - place of performance;
   - completion date;
   - quantity; and
   - unit.

3. **Tender Evidence Requirement**
   - evidence label;
   - evidence type;
   - published requirement reference; and
   - mandatory flag.

4. **Tender Readiness Finding**
   - code;
   - severity: `Blocking` or `Warning`;
   - task number;
   - field or row reference; and
   - plain-language message.

Do not create a Price Schedule DocType. Generate it from goods and related-service rows.

### 5.5 Tender Publication Package

Approval creates one immutable package containing:

- Tender and approved Version;
- template identity and bundle digest;
- Invitation PDF and digest;
- complete Tender PDF and digest;
- controlled technical-specification PDF and verified digest;
- package index or manifest and digest;
- approval actor, time and reference;
- overall package digest; and
- handoff status: `Ready` or `Consumed`.

Actual generated file digests are recorded after the files are created. An idempotent retry returns the same stored package; it does not render another copy.

## 6. Roles and permissions

Use ordinary Frappe Roles and User Permissions.

| Role | Permission |
|---|---|
| Procurement Officer | Prepare, edit Draft, run readiness, preview and submit |
| Head of Procurement Function | Review, return, approve and reopen before handoff consumption |
| Internal Auditor | Read Versions, findings, decisions and package evidence |
| Requesting department user | Read inherited Requisition information and neutral Tender status only where already authorised |
| System Manager | Technical administration only; no Tender business decision merely from this role |

Rules:

- the preparing officer cannot approve the same Tender;
- native User Permissions limit Procuring Entity access;
- direct URL and API access apply the same checks;
- DocType write permission alone never bypasses lifecycle rules; and
- no Capability Profile or Operational Scope Assignment is used.

## 7. Server commands

Expose exactly these whitelisted business commands. UI components must call them rather than writing lifecycle fields directly.

### 7.1 `prepare_tender`

Input:

- Requisition handoff ID;
- idempotency key.

Effect:

1. lock and recheck the handoff;
2. confirm it is authorised, unconsumed and supported;
3. resolve the one available `IT-EQUIPMENT-OPEN-V1` bundle;
4. create the Tender and Draft Version 1;
5. copy the approved Requisition facts and technical-document metadata;
6. bind the template key, version and digests; and
7. mark the handoff consumed by this Tender.

A retry returns the same Tender.

### 7.2 `save_tender_draft`

Input:

- Tender and Version;
- expected record version;
- values for one or more of the five fixed tasks; and
- idempotency key.

Effect:

- reject a non-Draft Version;
- accept only authorised fields and tables;
- reject stale writes;
- derive repeated and calculated values server-side; and
- return the updated task and record version.

Incomplete Drafts may be saved.

### 7.3 `run_tender_readiness`

Effect:

- validate the exact Draft Version;
- replace its readiness findings;
- build both resolved HTML previews with strict missing-value failure;
- verify the controlled technical-specification digest;
- store the readiness digest and preview references; and
- return Blocking and Warning findings grouped by task.

Readiness is not a lifecycle state.

### 7.4 `submit_tender_for_approval`

Effect:

- rerun readiness;
- require zero Blocking findings;
- lock the Version and calculate its digest;
- move the Tender to `Submitted for Approval`; and
- create one native assignment for the Head of Procurement Function.

### 7.5 `return_tender_for_correction`

Input includes one required, actionable correction.

Effect:

- preserve the submitted Version unchanged;
- record the return actor, time and correction;
- create a copied Draft successor;
- move the Tender to `Draft`; and
- assign it to the original Procurement Officer.

### 7.6 `approve_tender_for_publication`

Effect:

1. recheck role, PE scope and segregation of duties;
2. rerun readiness against the locked Version;
3. render the final Invitation and complete Tender once;
4. verify and include the approved technical specification;
5. create private immutable Files, their digests and package index;
6. create the approval record, publication package and ready handoff; and
7. move the Tender to `Approved for Publication`.

The operation must produce all required records or none.

### 7.7 `reopen_approved_tender`

Allowed only when the publication handoff remains `Ready` and unconsumed.

It requires a reason, preserves the approved Version and package, creates a copied Draft successor and returns the Tender to `Draft`.

## 8. Five tasks

Implement the fields, controls, allowed values, defaults, source labels, editability, conditional visibility and validation in `TPR-CHG-001 v0.3` section 8 exactly.

| Task | Main responsibility |
|---|---|
| 1. Tender details | Dates, validity, security and meeting decision |
| 2. Goods and delivery | Goods rows, related services and protected technical document |
| 3. Price schedule | Read-only released currency/price/tax treatment and generated blank supplier schedule |
| 4. Submission and evaluation | Fixed evaluation sequence and finite evidence decisions |
| 5. Contract terms | Payment, acceptance, performance security and delay damages |

Do not display internal template keys, source classifications or STD terminology to the officer.

Inherited, template-fixed and generated values must use read-only display, not enabled text boxes. Boolean decisions use Yes/No controls. Finite decisions use closed selects or radio groups. Dates, numbers and governed references use the exact controls in v0.3. Unknown options and free-text substitutes are rejected by the server.

## 9. Readiness checks

Implement these server-side Blocking checks:

- the Requisition remains authorised and belongs to this Tender;
- template, source and bundle digests match the installed release;
- every required Task field is complete;
- date order is valid;
- quantities equal the authorised Requisition quantity;
- delivery dates do not exceed the authorised date;
- the generated price rows exactly match Task 2;
- security values and generated expiry dates are consistent;
- evidence rows point to visible published requirements;
- the technical specification exists, is approved, readable and digest-matched;
- no unsupported brand restriction or unresolved drafting text remains;
- contract values agree everywhere they render;
- Invitation and Tender shared values match;
- the Invitation is absent from the issued Tender document; and
- both outputs render with no missing value or section.

Also block submission when:

- a value does not match its defined control type or allowed options;
- an inherited, fixed, generated or supplier-response value was sent as an officer edit;
- a hidden conditional field contains a value;
- an inactive or cross-PE governed reference was used; or
- a Task 3 supplier price or total was supplied by the Procurement Officer.

Warnings remain visible but do not require dismissal.

## 10. Rendering

Implement one server-side renderer for this bundle.

Rules:

- load masters only from the installed code bundle;
- use Jinja with auto-escaping and `StrictUndefined`;
- build one typed render context from the Requisition snapshot and Tender Version;
- calculate dates, totals and repeated values once;
- render the Invitation separately from the issued Tender;
- include the controlled technical specification as a separate package file;
- produce a package index naming every published file and digest;
- store files privately until the downstream publication service consumes the handoff; and
- never execute templates or rules stored in user-editable database fields.

Use two digests:

1. a deterministic render-context digest from canonical input plus bundle digest; and
2. the actual SHA-256 of each generated file.

Tests compare resolved HTML exactly and inspect PDF content, sections and page rendering. Do not require byte-identical PDFs across clean runs where the PDF tool writes timestamps. Approval retries must reuse the first stored files and therefore return the same file digests.

## 11. Screens

Use the existing Vue 3/Frappe Desk shell and existing KenTender components.

Implement only:

1. **Tender Preparation** — eligible handoffs and existing Tenders;
2. **Start IT-equipment Tender** — shows the one compatible template and inherited summary;
3. **Tender workspace** — five tasks, save status and task completion;
4. **Review and readiness** — grouped findings plus Invitation, Tender and technical-document previews;
5. **Tender approval** — submitted values, findings, full preview, Return and Approve; and
6. **Approved Tender** — immutable package, approval and handoff status.

Use the exact screen text, control presentation and KEBS fixture in `TPR-CHG-001 v0.3` section 12. Do not redesign the screens during implementation.

## 12. Installation

Add one idempotent install/migration function that:

1. reads the code-owned metadata and source record;
2. validates that every required bundle file exists;
3. recalculates and verifies the source and bundle digests;
4. validates the coverage register has no unresolved row;
5. creates or updates the one read-only registry row; and
6. marks it available only after all checks pass.

Running the installer twice must create no duplicate and no semantic change.

A missing file, invalid register or digest mismatch makes the template unavailable and fails the release check. There is no fallback to a partial bundle.

## 13. Build sequence and stop gates

### Gate 1 — Install and reproduce the bundle

Implement the bundle loader, registry and renderer tests first.

Required proof:

- one registry row after two installs;
- exact KEBS resolved HTML;
- correct Invitation/Tender separation;
- technical-document digest match; and
- no unresolved authoring content.

Stop and show the results before building transaction screens.

### Gate 2 — Complete the server journey

Implement the minimal records, commands, permissions, lifecycle and tests.

Required proof:

- prepare the KEBS Draft idempotently;
- save all five tasks;
- demonstrate quantity and delivery blockers;
- submit, return and create Draft Version 2;
- deny self-approval; and
- approve once without duplicate package records.

Stop and show the results before completing the UI.

### Gate 3 — Complete the officer and approver screens

Implement the six screens using the approved design contract.

Required proof:

- complete the five tasks without using STD concepts;
- show readiness findings at the correct task and field;
- preview the three package files; and
- complete return and approval through the UI.

Stop for a practical Procurement Officer walkthrough.

### Gate 4 — Accept the vertical slice

Run the full smoke contract and record:

- elapsed preparation time;
- unclear or duplicate entry;
- missing or unnecessary fields;
- exact generated package and digests;
- permission and segregation results; and
- any correction made.

The result is **ACCEPT**, **CORRECT AND RE-TEST** or **REJECT**.

## 14. Required tests

At minimum, automate:

1. clean and repeated bundle installation;
2. bundle tamper and missing-file failure;
3. compatible and unsupported Requisition decisions;
4. idempotent Tender preparation;
5. native PE scoping and direct-route denial;
6. Draft partial save and stale-write rejection;
7. quantity and delivery reconciliation;
8. generated price schedule consistency;
9. technical-document status and digest checks;
10. strict render failure on a missing value;
11. Invitation/Tender shared-value consistency;
12. Invitation absence from the issued Tender;
13. generated security-expiry calculation;
14. submission with zero Blocking findings only;
15. immutable submitted and approved Versions;
16. return creates a Draft successor;
17. self-approval denial;
18. atomic approval and idempotent retry;
19. reopen before handoff consumption only;
20. Version 1.1 does not alter an existing Version 1.0 Tender;
21. no endpoint or Desk route edits the installed template;
22. every five-task field uses its defined control, source and editability;
23. free text is rejected for Boolean and closed-choice values;
24. inactive, cross-PE and wrong-reference-type Links are rejected;
25. hidden conditional values are rejected; and
26. Task 3 rejects officer-entered prices and shows blank supplier-response placeholders.

Run the existing application tests before and after this suite. Preserve unrelated work and fix only regressions caused by this change.

## 15. Completion definition

The implementation is complete only when:

- the KEBS journey works from authorised Requisition to ready publication handoff;
- the generated package matches the approved template release;
- the officer uses only the five tasks;
- Author and Approver permissions work through UI and direct API calls;
- no STD configuration or legacy runtime dependency exists in the journey;
- all required tests pass; and
- the Gate 4 result is **ACCEPT**.

Do not begin Goods-generalisation, WORKS or complex IT after completion. Present the result and obtain a separate decision.

## Appendix A — Instruction to give Claude

> Implement STD-TPL-IMP-001 v0.2 from `/home/midasuser/kentender/apps/kentender_v1`. First read TPR-CHG-001 v0.3, the other controlling documents and the approved `docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1/05_review/review_record.md`. Stop if the review record does not say `APPROVE FOR IMPLEMENTATION PACK`. Preserve unrelated work. Implement only `IT-EQUIPMENT-OPEN-V1`, the five-task Tender Preparation journey, Author/Approver lifecycle, readiness, rendering and immutable publication handoff. Implement every field using the exact control, source, editability, allowed values and validation in TPR-CHG-001 v0.3. Task 3 contains no officer-entered prices or totals. Use ordinary Frappe Roles and User Permissions. Do not create an STD Configuration module, generic engine, manifests, schema editors, new capability system, complex IT, WORKS or downstream procurement modules. Follow the four gates in this pack and stop after each gate with the required evidence. Do not silently resolve a missing source value, policy choice or conflict; record it and stop.
