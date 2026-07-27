# KenTender e-Procurement System

# Cursor Implementation Directive - Canonical Bidder Workspace Manifest Compiler, NSSF Golden Fixture, and Legacy Migration v1

| Item | Value |
|---|---|
| Project | KenTender e-Procurement System |
| Module family | Standard Tender Document Engine / Bidder Workspace |
| Artifact | Cursor implementation directive |
| Canonical STD family | PPRA Standard Tender Document for Procurement of Information Technology, DOC. 10 |
| Calibration fixture | NSSF SPS ERP Tender, Ref. `NSSFSPS/ICT/ERP/001/2025-2026` |
| Status | Implementation directive following the approved recovery baseline |
| Version | 1.0 |
| Primary implementation outcome | Deterministic manifest compiler, immutable NSSF fixture resources, canonical checklist projection, and controlled one-way legacy migration |
| Design boundary | Stitch controls approved visual design; Cursor implements system behavior and integration |
| Governing rule | Canonical code must be independent of NSSF. NSSF values may exist only in fixture inputs, migration mappings, and generated test output. |

---

## 1. How to Use This Directive

Give Cursor:

1. this directive;
2. every binding input listed in Section 3;
3. the existing KenTender repository;
4. the existing test and migration conventions; and
5. the approved Stitch HTML/screens already used by the repository.

Cursor must treat this document as an implementation instruction, not a request to redesign the product.

Cursor must:

- inspect the existing repository before choosing paths, frameworks, persistence mechanisms, or naming conventions;
- use the existing architecture and component system where sound;
- implement in the phase order defined here;
- preserve unrelated work;
- run the repository's existing checks after each material phase;
- produce the implementation evidence required in Section 24; and
- stop only for a hard blocker defined in Section 25.

Cursor must not ask routine design questions already resolved by the binding artifacts.

---

## 2. Objective

Implement the canonical bidder-workspace manifest pipeline and use the NSSF ERP tender only as a deterministic calibration fixture.

The completed implementation must support this chain:

```text
Approved STD Template Version
-> Approved Obligation Catalogue
-> Approved Section Blueprint
-> Approved Tender Configuration Snapshot
-> Deterministic Manifest Compilation
-> Validation and Approval Bound to Payload Digest
-> Atomic Tender and Manifest Publication
-> Manifest-Driven Bidder Workspace
-> Versioned Bidder Responses and Evidence
-> Review, Submit, Seal, and Receipt
-> Predetermined Opening, Evaluation, and Contract Projections
```

For the NSSF fixture, compilation must produce:

- 10 bidder-facing content sections;
- 2 cross-cutting views;
- 3 workflow gates;
- 9 preliminary criteria;
- 9 qualification criteria;
- 7 scored technical criteria;
- 190 requirements in 23 groups;
- 6 implementation-schedule rows;
- 22 price rows;
- 8 contract-condition records; and
- the corrected Tender Security section.

The legacy NSSF schema must remain a migration source and negative test fixture. It must not remain a production runtime contract.

---

## 3. Binding Inputs and Precedence

### 3.1 Required inputs

Cursor must locate or import the following files without paraphrasing them:

| Priority | Artifact | Required use |
|---:|---|---|
| 1 | `Canonical_PPRA_IT_STD_Bidder_Submission_Obligation_Catalogue_v1.md` | Canonical bidder-obligation ownership and source anchors |
| 2 | `Canonical_PPRA_IT_STD_Bidder_Submission_Section_Blueprint_v1.md` | Canonical section templates, ordering, dependencies, and routing |
| 3 | `Bidder_Workspace_Manifest_Contract_and_Compilation_Specification_v1.md` | Complete manifest, compiler, rule, evidence, workflow, integrity, and projection contract |
| 4 | `NSSF_Bidder_Workspace_Golden_Manifest_and_Migration_Crosswalk_v1.md` | Corrected NSSF fixture decisions, mappings, counts, diagnostics, and golden oracle |
| 5 | `KenTender_Form_of_Tender_Electronic_Section_Specification_v1.md` | Full electronic Form of Tender behavior and confirmation contract |
| 6 | `09_NSSF_Full_Structured_Fixture.json` | NSSF normalized source configuration |
| 7 | `04_Requirement_Matrix_Full_Row_Extraction.csv` | NSSF 190-row requirement source |
| 8 | `05_Price_Schedule_Lines.csv` | NSSF 22-row price source |
| 9 | `10_NSSF_Electronic_Bidder_Submission_Schema.json` | Legacy migration input and negative fixture only |
| 10 | Existing approved Stitch HTML and repository UI components | Visual implementation reference only |

If the repository contains versioned copies, Cursor must identify their exact paths and verify that their content matches the expected digests before implementation.

### 3.2 Precedence

When inputs conflict:

1. the official bound STD controls legal meaning;
2. the obligation catalogue controls canonical bidder obligations;
3. the section blueprint controls grouping and ownership;
4. the manifest contract controls runtime and compiler behavior;
5. the golden crosswalk controls the NSSF recovery decision;
6. the Form of Tender specification controls that section;
7. approved tender configuration controls NSSF instance data;
8. Stitch controls visual presentation only;
9. legacy code, schemas, screenshots, and old Cursor prompts are migration evidence only.

Cursor must not silently choose between conflicts. It must apply the explicit corrections in Section 4 or report a hard blocker.

---

## 4. Binding Corrections and Implementation Clarifications

### 4.1 NSSF section count

The NSSF fixture has **10 content sections**, not nine:

| Order | Section key | Title |
|---:|---|---|
| 1 | `tender_documents_and_addenda` | Tender Documents & Addenda |
| 2 | `form_of_tender` | Form of Tender |
| 3 | `confidential_business_questionnaire` | Confidential Business Questionnaire |
| 4 | `statutory_declarations` | Statutory Declarations |
| 5 | `tender_security` | Tender Security |
| 6 | `preliminary_requirements_and_evidence` | Preliminary Requirements & Evidence |
| 7 | `qualification_and_capability` | Qualification & Capability |
| 8 | `technical_proposal_and_implementation_plan` | Technical Proposal & Implementation Plan |
| 9 | `requirements_compliance` | Requirements Compliance |
| 10 | `price_schedule` | Price Schedule |

The prior nine-section working assumption is superseded for this fixture.

### 4.2 Tender Security

Apply `NSSF-DEC-SEC-001`.

The NSSF source label “Professional Indemnity” is provenance only. The operative instrument:

- is submitted with the tender;
- has a fixed KES 500,000 amount;
- is a bank guarantee or insurance bond;
- blocks responsiveness when missing;
- is forfeitable on withdrawal; and
- is forfeitable on failure to sign or furnish performance security.

It must therefore compile through the canonical `tender_security` section and ITT 22 rules.

Minimum fixture validity:

```text
Tender deadline:                2026-06-30T11:00:00+03:00
Tender validity end:            2026-12-01T11:00:00+03:00
Minimum security validity end:  2026-12-31T11:00:00+03:00
```

`PRELIM-05` must link to the Tender Security response and must not request a duplicate upload.

### 4.3 Required errata in retained conformance fixtures

Where the earlier documents or tests are represented in repository fixtures, update only their NSSF calibration expectations:

| Existing reference | Replace |
|---|---|
| Blueprint Section 34.2 NSSF expected checklist | Nine sections -> ten sections including Tender Security |
| Blueprint Section 34.3 working security classification | Replace unresolved working classification with `NSSF-DEC-SEC-001` |
| Manifest specification Section 43.1 | Nine NSSF sections -> ten |
| Manifest test `BWMF-T049` | Expect ten NSSF content sections |
| Manifest test `BWMF-T054` | Expect the approved security decision to be bound and readiness to pass |
| Any screenshot-based July deadline | Use `2026-06-30T11:00:00+03:00` |

Do not rewrite canonical conditional-security behavior. This is a fixture correction.

### 4.4 Golden projection digest versus full manifest digest

The golden crosswalk's Section 8 JSON is a controlled **projection oracle**. Its documented digest is:

```text
sha256:461ffc824759f767f01bdfa9be77b3280da8020267d4743cd5ca7f9fb03ffa22
```

Cursor must implement two checks:

1. project the full compiled NSSF manifest into the documented oracle shape and reproduce the projection digest above; and
2. canonicalize the complete closed runtime payload under RFC 8785 JCS and record its own full payload digest.

Do not ship the abbreviated projection as the complete runtime manifest. Do not force a full manifest containing all required nested contracts to have the projection digest.

The diagnostic-set digest must reproduce:

```text
sha256:b3bbc3f30456383236a9ea1b131fee9d6e62519a20e45484c987805260be84f7
```

---

## 5. Non-Negotiable Constraints

1. Do not make the NSSF tender the canonical STD.
2. Do not hard-code STD-family or NSSF section lists in UI or services.
3. Do not derive bidder tasks from PDF pages or document headings.
4. Do not build a PDF-filling or signed-form-upload workflow.
5. Do not paraphrase locked legal text.
6. Do not let runtime code invent a section, field, task, validation, evidence demand, price row, requirement, or downstream route.
7. Do not put executable code, SQL, callbacks, or arbitrary expressions in a manifest.
8. Do not use a generative model in publication compilation.
9. Do not use binary floating-point for money.
10. Do not infer `included_elsewhere` from a blank price.
11. Do not treat file presence as evidence satisfaction without a valid evidence link.
12. Do not let bidders or clients set task, section, or workspace status.
13. Do not let an application role alone prove legal authority.
14. Do not auto-confirm a legal form during migration.
15. Do not treat a legacy submission event as a canonical sealed submission.
16. Do not expose bidder responses to procuring-entity users before lawful opening.
17. Do not publish a tender without its exact matching immutable manifest.
18. Do not mutate a published manifest.
19. Do not permit a production override for readiness errors.
20. Do not delete historical response, evidence, confirmation, migration, or submission versions.

---

## 6. Scope

### 6.1 Implement

- immutable manifest input bindings;
- compiler request and run lifecycle;
- the 22 deterministic compiler stages;
- typed rule and calculation evaluation;
- canonical IDs and deterministic ordering;
- content-addressed resource loading and verification;
- publication-readiness diagnostics;
- preview, publication, addendum, and replay modes;
- approval bound to payload digest;
- atomic tender/manifest publication;
- manifest-driven checklist projection;
- renderer dispatch by declared `section_type`;
- runtime response instances and versioning;
- evidence records, versions, and links;
- validation, issues, status, and progress derivation;
- dependency and invalidation handling;
- legal confirmation and authority binding;
- Review, Submit & Seal, and Receipt gates;
- opening, evaluation, and contract projections;
- corrected NSSF resources and golden fixtures;
- one-way legacy NSSF migration with dry run;
- deterministic replay and reconstruction tests; and
- implementation/audit evidence.

### 6.2 Do not implement or redesign

- tender-page visual redesign;
- a new design system;
- evaluator scoring UX;
- award workflow;
- post-award contract administration;
- cryptographic-provider replacement when an approved repository service exists;
- document OCR or legal-text extraction;
- automatic classification of unresolved tender language;
- unrelated STD-family content; or
- unrelated repository refactoring.

If an approved Stitch screen exists, preserve its layout and implement the declared behavior through existing components.

For Requirements Compliance:

- use the manifest title `Requirements Compliance`;
- preserve the approved right-hand response drawer pattern;
- load the selected row into one drawer;
- save through the canonical response service;
- display derived row status and issues;
- support next/previous row actions without changing row identity; and
- do not redesign the screen or call it `Technical Requirements`.

---

## 7. Governance and Lifecycle

Governance is part of the implementation, not deferred documentation.

### 7.1 Artifact separation

Persist separate records for:

1. mutable tender configuration;
2. immutable configuration snapshot;
3. compile request;
4. compile run and trace;
5. preview manifest;
6. validation report;
7. approval bound to exact payload digest;
8. immutable published manifest;
9. publication event;
10. addendum diff and impact plan; and
11. superseded manifest history.

### 7.2 Manifest lifecycle

```text
draft_configuration
-> preview_generated
-> validation_failed | validated
-> submitted_for_approval
-> returned | approved
-> published
-> superseded | cancelled
```

Rules:

- compilation does not publish;
- validation does not approve;
- approval does not publish;
- publication re-verifies all bound digests;
- any post-approval digest change invalidates approval;
- publication of tender and manifest is atomic;
- published and superseded manifests are immutable;
- addenda create new versions and never edit the prior version.

### 7.3 Compile-run lifecycle

```text
requested
-> resolving_inputs
-> compiling
-> validating
-> succeeded | failed
```

A failed run:

- produces deterministic diagnostics;
- creates no publication command;
- performs no source mutation; and
- may retain safe partial coverage statistics.

### 7.4 Migration lifecycle

```text
planned
-> dry_run
-> dry_run_complete
-> approved_for_execution
-> executing
-> completed | failed
```

Rules:

- production migration requires an approved dry-run digest;
- the operator who executes cannot approve their own migration when separation is configured;
- each migrated source object receives a disposition;
- rerunning the same approved migration is idempotent;
- partial failure cannot silently mark the run complete;
- legacy data remains read-only and reconstructable.

### 7.5 Workspace lifecycle

```text
not_started
-> draft
-> in_progress | needs_attention
-> ready_to_submit
-> submitted
-> withdrawn | closed
```

Workspace state is derived except for controlled transaction transitions such as submission, withdrawal, replacement, and closure.

---

## 8. Roles, Permissions, and Separation of Duties

### 8.1 Procurement-side roles

| Capability | STD Administrator | Tender Configurator | Procurement Reviewer | Tender Approver | Publication Service | Migration Operator | Auditor |
|---|---:|---:|---:|---:|---:|---:|---:|
| Edit canonical draft | Yes | No | Review | Approve | No | No | View |
| Configure tender draft | No | Yes | Review | No | No | No | View |
| Generate preview | No | Yes | Yes | No | System | No | View |
| Edit compiled payload | No | No | No | No | No | No | No |
| Review diagnostics | Yes | Yes | Yes | Yes | View | Controlled | View |
| Submit for approval | No | Yes | Yes | No | No | No | View |
| Approve payload digest | No | No | Recommend | Yes | No | No | View |
| Publish approved package | No | No | No | Controlled request | Yes | No | View |
| Approve migration dry run | No | No | Yes | Yes | No | No | View |
| Execute migration | No | No | No | No | System/controlled | Yes | View |
| View reconstruction | Controlled | Controlled | Yes | Yes | Yes | Controlled | Yes |

### 8.2 Bidder-side roles

| Capability | Bidder Admin | Bid Preparer | Financial Preparer | Authorized Submitter | Bidder Viewer |
|---|---:|---:|---:|---:|---:|
| View non-financial workspace | Yes | Yes | Controlled | Yes | Yes |
| Edit general responses | Yes | Yes | Controlled | Controlled | No |
| Edit technical responses | Yes | Yes | No by default | Controlled | No |
| View financial section | Controlled | Controlled | Yes | Yes | Controlled |
| Edit Price Schedule | Controlled | No by default | Yes | Controlled | No |
| Upload/link evidence | Yes | Yes | Controlled | Controlled | No |
| Confirm legal declaration | Only with authority | No unless authorized | No unless authorized | Only with authority | No |
| Submit & Seal | Only with authority and permission | No | No | Only with current authority | No |
| View submitted receipt | Yes | Controlled | Controlled | Yes | Controlled |

### 8.3 Authority rule

`authorized_submitter` permits access to the action but does not prove legal authority.

Confirmation and submission require a current versioned authority record containing:

- represented bidder organization;
- represented entity or JV;
- representative identity;
- legal capacity;
- permitted actions;
- effective period;
- verification/evidence basis;
- authority version; and
- revocation state.

Unknown permission conditions deny. Unknown authority denies.

## 9. Logical Domain Model

Use repository naming conventions, but implement every concept and invariant below. Do not collapse immutable versions into mutable current-row blobs.

### 9.1 Compilation and publication

| Concept | Required data | Required invariants |
|---|---|---|
| Manifest compile request | Request ID; mode; target manifest ID/version; tender ref/version; exact input bindings; previous manifest ref; requester; request time; expected digests | Immutable after acceptance; idempotent request key; exact versions only |
| Manifest compile run | Run ID; request ref; compiler version; stage; state; start/end; input-set digest; output refs | One active execution per idempotency key; append-only stage trace |
| Manifest input binding | Binding ID; type; object ref; version; lifecycle state; digest; compatibility metadata | No mutable alias; digest verified before compile |
| Manifest envelope | Schema version; control; payload; integrity; lifecycle state | Payload immutable after compilation; published envelope immutable |
| Manifest payload | Complete closed runtime contract | RFC 8785 JCS digest; unknown top-level properties rejected for v1 |
| Manifest resource | Resource ID/type; schema/version; count; ordering; content ref; logical digest; source refs | Content-addressed; immutable; count/schema/digest verified |
| Compiler diagnostic | ID; code; severity; stage; message; source/object refs; correction owner/action; deterministic fingerprint | Same fault and inputs produce same fingerprint |
| Validation report | Report ID; run ref; exact diagnostics; coverage; readiness; diagnostic digest | Immutable; readiness cannot pass with errors |
| Manifest approval | Approval ID; tender/config/manifest refs and digests; validation ref; approver; decision/time; comments | Approval binds exact payload digest; digest change invalidates |
| Manifest publication | Publication ID; tender version; manifest version; approval ref; event time; transaction ref | Tender and matching manifest become visible atomically |
| Addendum impact plan | Old/new manifest refs/digests; object matches; change classes; carry/invalidation actions; notice and projection impacts; plan digest | Immutable and approved before applying to workspaces |

### 9.2 Bidder runtime

| Concept | Required data | Required invariants |
|---|---|---|
| Workspace | Workspace ID; bidder/JV scope; tender/manifest binding; state; created/updated refs; active submission ref | One active binding version; no client-set readiness |
| Workspace manifest binding | Workspace; manifest ID/version/digest; bound time; addendum impact ref | Exact immutable manifest; history retained |
| Response instance/version | Response ID; workspace; manifest; section/task/scope; version; contract digest; normalized values; derived refs; evidence links; state; response digest; actors/times | Material save creates version; optimistic concurrency; sealed version immutable |
| Evidence item | Evidence ID; owner/party; type; metadata; lifecycle state | Does not satisfy a task by existence alone |
| Evidence version | Evidence version ID; content digest; storage ref; file metadata; validation state; actors/times | Immutable bytes; replacement creates version |
| Evidence link | Evidence version; owning task/criterion/requirement; scope; link state | Party, lot, type, validity, and currentness validated |
| Confirmation | Confirmation ID; response/version/digest; legal text ref/digest; statement digest; actor/capacity; authority ref/version; time; state; invalidation ref | Deliberate authorized action; never created by save |
| Dependency snapshot | Consumer; provider; provider version/digest; dependency-contract digest; validation time | Used to detect staleness |
| Invalidation event | Trigger; prior/new versions; affected refs; impact/effects; reason; time; notice; resolution | Append-only; never deletes history |
| Validation snapshot | Snapshot ID; workspace/manifest; trigger; response/evidence version set; findings; result; digest; time | Submission requires a current successful snapshot |
| Validation finding | ID; rule; severity; owner/correction target; safe message; affected refs; state | Blocker reruns at submission; internal details not shown to bidder |
| Submission | Submission ID/version; exact snapshot; manifest/resource/response/evidence/legal/authority refs and digests; timestamp; seal state; snapshot digest | Atomic; immutable; confidential until lawful opening |
| Submission receipt | Receipt ID; submission ref; verification value; issued time; safe summary | Exists only after persisted sealed submission |

### 9.3 Legacy migration

| Concept | Required data | Required invariants |
|---|---|---|
| Migration plan | Plan ID; source schema digest; target manifest ref; mapping version; scope; created by/time | Exact source and target only |
| Migration run | Run ID; plan; mode; state; source snapshot digest; dry-run report digest; approval ref; idempotency key; counts | Dry run before execution; idempotent |
| Migration item disposition | Source path/ID/version/value digest; target ref; disposition; transform; result; finding; reconfirmation flag | Every source object has one disposition |
| Migration evidence link | Legacy file/version ref; canonical evidence version/link ref; content digest | Preserve exact legacy lineage |
| Migration report | Counts by disposition; errors; warnings; unmapped count; reconfirmation list; output digest | Execution cannot complete with silent unmapped objects |

### 9.4 Storage rules

- Use database-native exact decimal or an established arbitrary-precision decimal library for money.
- Use UTC for system event time and retain the tender's declared timezone/offset separately.
- Use optimistic-concurrency versions on mutable draft records.
- Use unique constraints for stable IDs, versions, idempotency keys, and active bindings.
- Use append-only history for responses, evidence versions, confirmations, invalidations, approvals, migrations, and submissions.
- Use restricted storage references rather than arbitrary URLs.
- Do not store credentials, tokens, private keys, or bidder values in the manifest.
- Index response lookup by workspace, section, task, and scope without using array position as identity.
- Ensure tenant/bidder isolation in every runtime query and mutation.

---

## 10. Architecture Boundaries

Adapt these boundaries to the repository's existing architecture. Do not create parallel infrastructure when an equivalent approved service exists.

| Boundary | Owns | Must not own |
|---|---|---|
| STD/Template Registry | Approved canonical versions and locked legal text | Tender values or bidder responses |
| Tender Configuration | Draft values and immutable approved snapshots | Compiled payload editing |
| Manifest Compiler | Deterministic expansion, validation, resources, projections, and digest | Publication mutation or bidder responses |
| Manifest Repository | Immutable envelopes/resources and exact retrieval | Runtime invention or source interpretation |
| Governance/Publication | Approval, separation of duties, and atomic publication | Payload editing |
| Bidder Workspace | Workspace binding, response/evidence orchestration, status, issues | Canonical template changes |
| Authority Service | Representative authority and revocation | Bidder role assignment alone |
| Evidence Service | Evidence versions, validation, and links | Obligation ownership |
| Validation Engine | Objective manifest-declared validation and findings | Evaluator judgment |
| Submission Service | Atomic snapshot, seal, timestamp, receipt, withdrawal/replacement | Evaluation or post-submission mutation |
| Projection Service | Predetermined sealed views for opening/evaluation/contract | New obligations or reinterpretation |
| Legacy Migration Adapter | One-way mapping and lineage | Canonical domain rules |

Dependency direction must follow the authority chain. Bidder Workspace may consume a published manifest; it may not call tender configuration to infer missing behavior.

---

## 11. Required Application-Service Contracts

Use existing transport conventions. The names below are logical capabilities, not mandatory route names.

### 11.1 Compiler and governance

| Capability | Required behavior |
|---|---|
| `requestManifestCompile` | Validate request identity, mode, exact bindings, versions, and expected digests |
| `runManifestCompile` | Execute deterministic stages; persist trace and success/failure outputs |
| `getCompileResult` | Return envelope/report/coverage/diagnostics or deterministic failure |
| `submitManifestForApproval` | Freeze review package and bind validation report |
| `approveManifestDigest` | Record authorized decision against exact digest |
| `publishTenderAndManifest` | Reverify bindings/approval and publish atomically |
| `compileAddendumPreview` | Produce new manifest, diff, and impact plan without publication |
| `publishAddendum` | Approve/publish new version and apply governed workspace impact |
| `replayManifest` | Reproduce a retained payload and digest without mutation |

### 11.2 Bidder runtime

| Capability | Required behavior |
|---|---|
| `startWorkspace` | Bind bidder/JV to exact published tender and manifest |
| `getWorkspaceManifest` | Return verified manifest and required resources |
| `getChecklistProjection` | Derive only applicable content sections, statuses, issue counts, and allowed action |
| `getSectionContract` | Return declared section/groups/tasks and resources; fail if renderer unsupported |
| `saveResponse` | Check permission/version; normalize; validate; version; invalidate dependents; return current issues |
| `createOrReplaceEvidence` | Version file and metadata; never rewrite sealed evidence |
| `linkEvidence` | Validate compatible owner, party, scope, type, and validity |
| `confirmResponse` | Verify response/current dependencies/legal text/authority; persist confirmation digest |
| `validateWorkspace` | Produce versioned whole-workspace validation snapshot |
| `submitAndSeal` | Revalidate, enforce server deadline/authority/idempotency, persist and seal atomically |
| `getSubmissionReceipt` | Return only the receipt for a successfully sealed submission |

### 11.3 Migration

| Capability | Required behavior |
|---|---|
| `planLegacyMigration` | Verify exact legacy schema/snapshot and target manifest |
| `dryRunLegacyMigration` | Produce per-object dispositions and no canonical writes |
| `approveMigrationRun` | Bind approval to dry-run report digest |
| `executeLegacyMigration` | Apply approved mappings idempotently and retain lineage |
| `getMigrationReport` | Return counts, findings, unmapped objects, and reconfirmations |

### 11.4 Mutation contract

Every material mutation must enforce:

- authenticated actor;
- tenant/organization scope;
- permission;
- legal authority where applicable;
- exact manifest binding;
- optimistic concurrency;
- idempotency where transaction-like;
- server-authoritative time;
- atomic persistence;
- audit event; and
- safe error output.

---

## 12. Implementation Sequence

Do not skip phases. Keep each phase buildable and testable.

### Phase 0 - Repository audit

Before editing:

1. identify the application stack, package manager, database, migration tool, test framework, authorization model, audit service, storage service, cryptographic/sealing abstraction, decimal library, and frontend component system;
2. locate current tender configuration, published tender, bidder workspace, submission, evidence, and evaluation models;
3. locate current manifest/schema usage and renderer dispatch;
4. locate the hard-coded checklist and NSSF seed data;
5. locate existing migrations and tests;
6. identify the approved Stitch implementation files, including the Requirements Compliance drawer;
7. search for NSSF-specific constants outside fixtures;
8. identify uncommitted or unrelated changes and preserve them; and
9. write a short repository assessment in the implementation report.

Do not introduce a new framework or package merely because it is convenient. Reuse established project abstractions unless they cannot satisfy a binding invariant.

### Phase 1 - Contract schemas and fixture errata

Implement versioned, closed schemas for:

- compile request;
- manifest envelope;
- complete payload;
- section/group/task/field/collection contracts;
- typed condition and calculation AST;
- evidence contracts;
- validation and diagnostic records;
- dependencies and invalidation policies;
- role/permission/authority references;
- workflow gates;
- resource descriptors;
- projections;
- addendum diff/impact;
- response instances;
- confirmations;
- submissions and receipts;
- migration plan/run/item/report.

Tasks:

1. encode schemas in the repository's established schema mechanism;
2. reject unknown properties where v1 declares closed objects;
3. make schema versions explicit;
4. add the Section 4 fixture errata;
5. replace legacy NSSF expectations only in calibration fixtures;
6. add schema conformance tests; and
7. ensure legal and commercial fields cannot be preaccepted by defaults.

Exit gate:

- schemas compile;
- closed-object tests pass;
- the NSSF expectation is 10 sections;
- Tender Security is resolved;
- no production code depends on the legacy schema.

### Phase 2 - Persistence and migrations

Add or adapt persistence for every concept in Section 9.

Requirements:

- forward-only, reviewable database migrations;
- unique and foreign-key constraints;
- append-only version relationships;
- immutable published/sealed protections;
- exact-decimal fields;
- idempotency constraints;
- approval and publication linkage;
- tenant/bidder isolation;
- evidence content-digest uniqueness where repository policy permits deduplication;
- safe indexes for 190-row and larger matrices;
- no destructive conversion of legacy data.

Write tests proving:

- published manifest mutation is rejected;
- sealed response/evidence mutation is rejected;
- duplicate stable IDs fail;
- concurrent response saves detect version conflict;
- concurrent submission idempotency permits one authoritative result;
- migration rerun does not duplicate canonical records.

### Phase 3 - Deterministic manifest compiler

Implement the compiler as a pure or side-effect-isolated domain/application service.

Execute these stages in order:

| Stage | Required output |
|---:|---|
| C01 Request validation | Valid compile request |
| C02 Source resolution | Exact immutable input objects |
| C03 Integrity verification | Verified digests |
| C04 Lifecycle and compatibility | Approved/compatible input set |
| C05 Source normalization | Deterministic normalized graph |
| C06 Obligation coverage | One disposition per catalogue obligation |
| C07 Blueprint expansion | Candidate section/group/task graph |
| C08 Tender applicability | Included/omitted conditional sections |
| C09 Dynamic expansion | Criteria, requirements, schedules, prices, parties, lots |
| C10 Deferred rules | Bidder-dependent declared branches |
| C11 Response contracts | Closed fields and response digests |
| C12 Evidence contracts | Types, requirements, and links |
| C13 Permissions and authority | Explicit role/action policies |
| C14 Dependencies/invalidation | Acyclic graph and policies |
| C15 Validation registry | Typed objective rules and messages |
| C16 Workflow gates | Review, submission, receipt, optional withdrawal/replacement |
| C17 Downstream projections | Opening, evaluation, and contract routes |
| C18 Ordering and identity | Stable IDs and deterministic arrays |
| C19 Schema/semantic readiness | Diagnostics and fail-closed result |
| C20 Canonicalization/digest | RFC 8785 JCS payload digest |
| C21 Addendum diff | Required only in addendum modes |
| C22 Output packaging | Envelope, reports, trace, resources, and impact plan |

Compiler rules:

- stages C01-C22 do not publish;
- static applicability must resolve at compile time;
- bidder-dependent applicability emits declared rules and never runtime-created tasks;
- every catalogue obligation has one disposition;
- every editable value has one owner;
- every output object retains source lineage and applied transform;
- array order uses declared stable ordering;
- identifiers do not depend on labels or array positions;
- money uses exact decimals with explicit scale and rounding;
- rules use the approved typed AST only;
- an unsupported renderer or unresolved route is an error;
- errors produce no publication-ready output;
- identical inputs and compiler version reproduce the same payload.

### Phase 4 - Content-addressed resources and NSSF materialization

Materialize immutable NSSF resources for:

- 23 requirement groups;
- 190 requirements;
- 9 preliminary criteria;
- 9 qualification criteria;
- 7 technical scoring criteria;
- 6 schedule rows;
- 22 price rows;
- 8 SCC/contract conditions; and
- 8 controlled decisions.

Each resource must declare:

- resource ID and type;
- schema ref and version;
- item count;
- ordering contract;
- logical digest;
- immutable repository ref;
- source refs; and
- optional chunk descriptors.

Hash the canonical ordered logical array, not CSV bytes or concatenated chunks.

Runtime must reject:

- missing resources;
- wrong count;
- wrong schema;
- wrong digest;
- duplicated item IDs;
- inconsistent order; or
- partial chunk availability.

### Phase 5 - Governance and atomic publication

Implement:

1. preview generation;
2. validation report review;
3. submission for approval;
4. approval/return decision;
5. approval binding to exact payload and source digests;
6. publication-time digest re-verification;
7. atomic publication of the tender version and matching manifest;
8. immutable published retrieval;
9. cancellation/supersession without mutation; and
10. addendum compilation and impact-plan approval.

Atomic publication must persist in one transaction:

- published tender version;
- document package version;
- configuration snapshot;
- manifest envelope;
- resources/bindings;
- payload digest;
- approval;
- tender public state; and
- workspace availability.

Fail the transaction if any element fails. Never expose a published tender without its manifest.

### Phase 6 - Manifest-driven Bidder Workspace

Replace the hard-coded checklist source with a projection from the bound published manifest.

Checklist behavior:

- show content sections only;
- order by manifest `order_weight`;
- use manifest titles and instructions;
- derive `not_started`, `in_progress`, `needs_attention`, `complete`, and `not_applicable`;
- calculate progress using applicable required content sections only;
- show blocker count and correction route;
- select primary action from current derived state;
- exclude Evidence Register and Issues from the checklist;
- exclude Review, Submit, and Receipt from the checklist; and
- never infer behavior from a label.

Renderer dispatch:

| Section type | Required renderer behavior |
|---|---|
| `document_acknowledgement` | Versioned package and addendum acknowledgement |
| `declaration_form` | Locked legal text, structured fields, derived values, authorized confirmation |
| `questionnaire` | Entity-scoped branches and certification |
| `declaration_bundle` | CITD, SD1, SD2, Ethics, and associated appendix status |
| `security_instrument` | Instrument metadata, party, issuer, validity, and evidence |
| `eligibility_checklist` | Criterion rows linked to authoritative forms/evidence |
| `qualification_response` | Structured projects, finances, personnel, capability, and evidence |
| `technical_response` | Structured technical topics, schedule, and governed attachments |
| `requirement_matrix` | Resource-backed grouped rows and response drawer |
| `price_schedule` | Canonical tables, exact calculations, and derived summaries |

Unsupported renderer behavior:

- fail the section closed;
- emit a blocker with a safe correction message;
- prevent submission;
- do not fall back to generic text or upload.

### Phase 7 - Responses, evidence, validation, status, and invalidation

#### Response saving

A material save must:

1. verify workspace/manifest binding;
2. verify actor and permission;
3. check optimistic-concurrency version;
4. normalize values;
5. validate the changed task;
6. create a new response version;
7. calculate its digest;
8. revalidate direct dependents;
9. create required invalidation events;
10. update derived issues/status; and
11. persist atomically.

#### Evidence

Implement:

- immutable evidence versions;
- file-safety validation;
- type and metadata validation;
- issuer, issue, expiry, and reference metadata where configured;
- party and scope ownership;
- reusable evidence links;
- replacement without history loss;
- dependent-task revalidation;
- sealed-version immutability; and
- optional page/section locators on evidence links.

A page locator cannot satisfy an obligation without a valid evidence record and link.

#### Completion

Derive task completion only when:

```text
applicable
and every required value exists
and every required evidence link is current
and every required confirmation is current
and every dependency is current
and every blocker passes
```

Derive section, group, workspace, and progress from task results. Never persist bidder-editable completion flags.

#### Invalidation

Implement policies for:

- display-only;
- revalidation;
- response-affecting;
- evidence-affecting;
- calculation-affecting;
- scope-affecting;
- legal-text-affecting;
- authority-affecting;
- deadline-affecting;
- routing-affecting; and
- submission-policy-affecting changes.

Any material price, legal text, bidder/JV identity, authority, lot/alternative, or declaration change must invalidate affected confirmations.

### Phase 8 - Confirmation, submission, receipt, and projections

#### Confirmation

Saving is not confirmation.

Confirmation requires:

- exact response/version/digest;
- exact legal-text ref/version/digest where applicable;
- exact confirmation statement digest;
- authenticated actor;
- verified current authority and authority version;
- deliberate confirmation action;
- current dependencies; and
- audit event.

#### Submit & Seal

Implement one atomic transaction:

1. lock workspace against conflicting material writes;
2. reload authoritative current state;
3. verify manifest and every resource digest;
4. use server time to verify deadline;
5. rerun all submission validations;
6. verify current confirmations and authority;
7. assemble exact snapshot;
8. calculate snapshot digest;
9. persist immutable snapshot;
10. apply approved confidentiality seal;
11. assign authoritative timestamp;
12. transition workspace;
13. persist receipt; and
14. release lock.

An idempotent replay returns the same authoritative submission. Failure before full completion creates no receipt.

#### Projections

Implement predetermined projections:

- opening: only declared opening fields;
- evaluation: only declared sealed response/evidence sources;
- contract: only accepted contract-routed values with provenance.

No downstream service may add a mandatory bidder obligation, edit bidder content, or reinterpret an absent route.

### Phase 9 - One-way legacy NSSF migration

Accept only the legacy schema digest:

```text
sha256:4d461f4901ef159578b441afd468125ce60b310d67575a81dc23d88ff4a6fa72
```

Implement `dry_run` before `execute`.

Supported dispositions:

- `carry_exact`;
- `transform_review`;
- `link_existing_evidence`;
- `recalculate`;
- `require_reconfirmation`;
- `audit_only`; and
- `reject`.

Mandatory migration behavior:

- preserve original object path, ID, value digest, timestamp, actor, and schema;
- map every source object;
- deduplicate evidence by content digest without losing versions;
- recalculate price totals;
- require current document acknowledgements;
- require full current Form of Tender confirmation;
- require full current statutory declarations;
- require corrected Tender Security completion;
- reject ambiguous values;
- surface unmapped count;
- produce reconfirmation list;
- support idempotent replay;
- never mark a legacy submission as sealed.

For non-production PoC workspaces, provide a clean regeneration option and prefer it over in-place migration unless response preservation is required for testing.

### Phase 10 - Addendum impact and reconstruction

Implement matching by:

1. source lineage;
2. stable logical key;
3. scope identity; and
4. parent lineage.

Do not match by array position or display label.

Support these change classes:

- unchanged;
- display-only;
- validation-compatible;
- dependency-changed;
- response-compatible extension;
- response-breaking;
- legal-text changed;
- calculation changed;
- scope added/removed;
- routing changed;
- deadline/submission policy changed.

Applying an approved addendum impact to an unsealed workspace must:

- preserve compatible response versions;
- retain removed history;
- create new active tasks;
- mark affected content stale;
- invalidate required confirmations;
- recalculate status/issues;
- bind the new manifest atomically; and
- notify the bidder of affected work.

Historical reconstruction must use exact retained versions, never current templates.

---

## 13. NSSF Golden Fixture Oracle

### 13.1 Source and control digests

| Artifact | Digest |
|---|---|
| Official IT STD source | `sha256:2e57294f5cd49cfeca476347a3c81922f1efd834fdaa56430c3066efd1f6d251` |
| NSSF source tender | `sha256:bb716e97a312548d8469c5513539f0679e83b3336c7d630c2d7d6c77773aeb38` |
| NSSF structured fixture | `sha256:4db4747950e8831f9385ce52463c4365ae72e6de4b72b8e896deab5b4cd2bfe1` |
| Legacy bidder schema | `sha256:4d461f4901ef159578b441afd468125ce60b310d67575a81dc23d88ff4a6fa72` |
| Canonical obligation catalogue | `sha256:eb045d1f33fe7c34d67ef18f004266bf3b25bd8eb11fa77ef4705f0691b369ba` |
| Canonical section blueprint | `sha256:de3cf25fc4087d4d9f65407476b95d4e67a8701db31cd0246446807e30bc7c25` |
| Manifest specification | `sha256:29c3a28fd80e67873a07e7ab10171b6a6ffd314b27bf66fd713af01d838f2eed` |
| Form of Tender specification | `sha256:92adadc808642cf034b3dc9cf0d6dcff092a955273e4a16b188a83a850488343` |

### 13.2 Logical resource digests

| Resource | Count | Digest |
|---|---:|---|
| Requirement groups | 23 | `sha256:76cd5d03583c4c4d042215b212a3b14925284cc6dbf57a5b8486cb0d7d441793` |
| Requirements | 190 | `sha256:15b374c220891b52bf75c7390e7f3f7dc680760355997f18217492b6831bf912` |
| Preliminary criteria | 9 | `sha256:364dbde57e09558c11ebcc443710855698eace1a8d828b6bfc9aa0e488832287` |
| Qualification criteria | 9 | `sha256:8db3f47c5cd31e4ffd690a29e98647b87a8cd3b20f71a5e784c587270a534d54` |
| Technical scoring | 7 | `sha256:0ae31ac169b3ac5a1103390f338d962caf34deef117bf063012ac02b1e82bb76` |
| Schedule | 6 | `sha256:2497f21da32a79f51a1261b47b1f4135a43de126a9204a46a51daa881dfa86f4` |
| Price lines | 22 | `sha256:8e34505c57a85b40088df4db29727932c9e27d0aa4b9c5f5db70f9d1673bc2c2` |
| Contract conditions | 8 | `sha256:bd8f8ac784de60a448a23662f568009c95f88f2c4d01fe375550bdd0d8e93b8f` |
| Controlled decisions | 8 | `sha256:7712b4ed457d9be988d4f27ebbcba1dea61372ca998db0a9fefaf3158ac4bc17` |
| Ordered descriptor set | 9 descriptors | `sha256:9532a6c363914f10f94af53a832d49e5899e72821cae9361a9608e49bbbf047c` |

### 13.3 Required compiler result

| Check | Expected |
|---|---|
| Content sections | 10 in Section 4.1 order |
| Conditional Tender Security | Included |
| Lots & Alternatives | Omitted |
| Cross-cutting views | Evidence Register and Issues |
| Workflow gates | Review & Validate; Submit & Seal; Submission Receipt |
| Preliminary criteria | 9 |
| Qualification criteria | 9 |
| Technical scoring criteria | 7, totaling 100, pass mark 75 |
| Requirements | 190 in 23 groups |
| Contract carry-forward requirements | 117 |
| Schedule rows | 6 |
| Price rows | 22 |
| SCC conditions | 8 |
| Calibration diagnostics | 0 errors, 2 warnings, 6 information |
| Projection oracle digest | `sha256:461ffc824759f767f01bdfa9be77b3280da8020267d4743cd5ca7f9fb03ffa22` |
| Diagnostic-set digest | `sha256:b3bbc3f30456383236a9ea1b131fee9d6e62519a20e45484c987805260be84f7` |

### 13.4 NSSF values that must remain fixture data

- procuring entity and tender identity;
- contract title;
- June 2026 deadline;
- KES currency;
- configured 16% VAT;
- KES 500,000 Tender Security;
- maximum three JV members;
- prohibition on alternatives;
- 154-day validity;
- Microsoft Dynamics 365 and Azure scope;
- two implementation phases;
- every requirement/criterion/schedule/price row;
- 75-point technical pass mark; and
- every SCC value.

A repository test must fail if these values occur in canonical template/compiler/renderer code outside fixture or migration namespaces.

---

## 14. Required Legacy Crosswalk Behavior

### 14.1 Section dispositions

| Legacy section | Canonical disposition |
|---|---|
| Tender Document Acknowledgement | Versioned Tender Documents & Addenda |
| Abbreviated Form of Tender | Full canonical Form of Tender; require reconfirmation |
| Short CBQ | Full canonical CBQ; move misplaced fields |
| Mandatory Preliminary Documents | Nine derived criteria with owner/evidence links |
| Technical Qualification | Qualification & Capability |
| Technical Compliance Matrix | Requirements Compliance |
| Implementation Plan | Technical Proposal & Implementation Plan |
| Price Schedule | Canonical price tables |
| Contract Conditions Acknowledgement | Audit only; remove section |
| Final Declaration and Submission | Statutory Declarations plus workflow gates |

Add:

- Statutory Declarations; and
- Tender Security.

### 14.2 Critical field mappings

| Legacy value | Canonical behavior |
|---|---|
| Generic acknowledgement Boolean | Do not carry; create unacknowledged current-version records |
| Three Form of Tender totals | Recalculate from canonical Price Schedule |
| Free-text signatory | Resolve authenticated person and current authority |
| Form confirmation checkbox | Require full current authorized confirmation |
| Microsoft designation in CBQ | Move to qualification/product authorization |
| Pending litigation in CBQ | Move to canonical qualification litigation records |
| Signed Form of Tender upload | No target; link current electronic form status |
| CITD/SD upload | No target; link current electronic declaration status |
| Requirement Yes/No | Map to `complies` / `does_not_comply` |
| Requirement statement | Carry only for unchanged source requirement |
| Reference pages | Optional evidence locator |
| Evidence uploads | Versioned evidence records and links |
| Deviation note | Reject when non-blank; alternatives are prohibited |
| Implementation upload | Evidence only; does not complete structured tasks |
| Legacy subtotal/VAT/grand total | Discard and recalculate |
| Blank price | Incomplete |
| Implicit inclusion | Require explicit `included_elsewhere` link |
| Contract checkbox | Audit only |
| Legacy submit event | Audit only; never sealed |

---

## 15. Functional UI Integration Requirements

Cursor implements functionality against the approved design. Cursor must not issue new Stitch prompts or redesign screens.

### 15.1 Workspace checklist

- render section rows from manifest data;
- display manifest title, requiredness, derived status, issue count, last activity, and allowed action;
- use the exact 10-section NSSF output only because the NSSF manifest contains those sections;
- allow another tender or STD family to produce a different list without code changes;
- derive progress from applicable required content sections;
- route correction actions to the owning section/task;
- show workflow gates separately.

### 15.2 Requirements Compliance screen

- title comes from `section.title`;
- group navigation comes from the 23-group resource;
- rows come from the 190-row resource;
- row status is derived;
- selecting a row opens the approved right-hand response drawer;
- drawer fields come from the row response contract;
- evidence is selected/linked through the Evidence Register;
- page/section locator is optional metadata;
- Save creates a response version;
- Save & Next saves, closes or advances according to the approved interaction without losing group/filter state;
- close with unsaved changes uses the repository's established dirty-state guard;
- a stale or changed requirement displays the current issue and requires a current response;
- no bidder score or evaluator-only field appears.

### 15.3 Tender Security

- show the source alias as provenance only where useful;
- label the section `Tender Security`;
- collect instrument type, issuer, reference, amount, currency, issue/expiry dates, bidder/JV parties, and evidence;
- display calculated minimum expiry;
- block completion for wrong amount/currency/party/form/validity;
- link `PRELIM-05` to its derived status.

### 15.4 Form of Tender

- use the complete canonical form;
- render tender and bidder identity as derived;
- derive price summary from the Price Schedule;
- show current associated-form statuses;
- require structured disclosures;
- confirm through verified authority;
- invalidate confirmation after material changes;
- do not accept a signed-form upload.

### 15.5 Evidence and Issues

- provide one Evidence Register across sections;
- permit compatible reuse by link;
- show evidence validity/currentness;
- provide one Issue Register;
- give every bidder-visible blocker an owning correction action;
- do not expose stack traces, schema paths, secrets, or evaluator notes.

### 15.6 Review and submission

- Review & Validate presents section completion, blockers, warnings, confirmations, and permitted financial summary;
- Submit & Seal is unavailable until entry rules pass;
- server-side submission validation is authoritative;
- Receipt is available only after successful sealing and persistence;
- physical PDF is reference material only.

## 16. Test and Verification Requirements

### 16.1 Test layers

Implement:

- schema tests;
- compiler unit tests;
- typed-rule tests;
- exact-decimal calculation tests;
- identifier and ordering property tests;
- resource-integrity tests;
- repository/persistence tests;
- permission and authority tests;
- migration unit and integration tests;
- API/application-service contract tests;
- renderer contract tests;
- workflow transaction tests;
- pre-opening confidentiality tests;
- deterministic replay tests;
- historical reconstruction tests; and
- end-to-end NSSF calibration tests.

### 16.2 Binding conformance suites

Implement every test from:

- `BWMF-T001` through `BWMF-T054`, with the corrected NSSF expectations in Section 4.3; and
- `NSSF-GOLD-001` through `NSSF-GOLD-048`.

Minimum combined binding-test count:

```text
54 manifest-contract tests
+ 48 NSSF golden tests
= 102 binding tests
```

Repository-specific unit, integration, migration, UI, security, and end-to-end tests are additional.

### 16.3 Determinism

Tests must prove:

- identical logical inputs and compiler version produce equivalent complete payloads;
- canonical bytes and full payload digest reproduce;
- generation timestamps outside the payload do not change its digest;
- shuffled input file order does not change declared logical ordering;
- inline and content-addressed logical resources hash equivalently;
- changed source values change affected output/digest;
- diagnostic fingerprints reproduce;
- projection oracle digest reproduces; and
- replay performs no mutation.

### 16.4 Money

Tests must prove:

- decimal precision and rounding are explicit;
- binary floating-point does not enter commercial calculations;
- blank, zero, priced, included elsewhere, and allowed not-applicable are distinct;
- invalid inclusion links fail;
- all 22 NSSF lines reconcile;
- the configured VAT is calculated once;
- derived summaries equal the Form of Tender;
- amount in words matches numeric amount/currency; and
- a price change invalidates Form of Tender confirmation.

### 16.5 Authority and submission

Tests must prove:

- preparer cannot confirm without authority;
- role access does not substitute for authority;
- revoked/expired authority fails;
- confirmation binds exact response/legal/authority digests;
- submission reruns blockers;
- server time controls deadline;
- two concurrent submissions create one authoritative result;
- idempotent replay returns the same result;
- failed persistence or sealing creates no receipt;
- submitted versions are immutable; and
- procuring-entity access remains denied before lawful opening.

### 16.6 Migration

Test:

- exact source-schema digest acceptance;
- wrong digest rejection;
- complete per-object disposition;
- evidence deduplication with lineage;
- legal reconfirmation;
- price recalculation;
- non-blank deviation rejection;
- ambiguous inclusion rejection;
- legacy submission audit-only handling;
- dry-run no-write behavior;
- approval binding;
- idempotent execution;
- partial failure reporting; and
- zero silent unmapped items.

### 16.7 UI integration

Test:

- checklist rows derive from manifest;
- section count is not hard-coded;
- cross-cutting views and gates are outside the checklist;
- unsupported renderer fails closed;
- NSSF Requirements Compliance renders 23 groups and 190 rows;
- the right-hand drawer loads and saves the selected stable row;
- filter/group state survives drawer progression;
- issue correction routes target the owning task;
- financial permissions are enforced server-side;
- status cannot be altered by client payload;
- PDF remains reference only; and
- a different fixture can produce a different section/count structure without component changes.

### 16.8 Clock handling

The NSSF source deadline precedes this recovery implementation date. Do not alter it.

Use an injected/fake authoritative clock:

- before `2026-06-30T11:00:00+03:00` for successful submission tests;
- exactly at the boundary according to the approved deadline policy; and
- after the deadline for late-submission rejection.

Production code must not accept a client-supplied clock.

---

## 17. Diagnostics and Error Handling

Implement the complete diagnostic registry in the manifest specification.

At minimum, preserve error categories:

- governance/approval;
- binding and digest;
- source normalization;
- obligation coverage;
- identity;
- rules;
- sections/renderers;
- fields/collections;
- evidence;
- validation;
- dependencies;
- price calculations;
- downstream routes;
- submission;
- resources/integrity; and
- addendum migration.

Rules:

- a digest mismatch is an error, never a warning;
- every error identifies stage and source;
- every bidder-visible finding has a safe message and correction route;
- the same source problem produces the same code/fingerprint;
- warnings cannot hide unresolved legal, security, coverage, or integrity problems;
- internal exceptions, SQL, stack traces, secret values, and storage references are never bidder-visible;
- failed compilation may report multiple independent errors but cannot auto-correct sources.

The NSSF calibration diagnostic set must remain exactly:

- 0 errors;
- 2 warnings; and
- 6 information records.

---

## 18. Security and Confidentiality

Implement or verify:

- tenant and bidder-organization isolation;
- least-privilege authorization;
- separate financial permissions;
- legal-authority verification;
- server-side validation of every mutation;
- content-type, size, malware/safety, and integrity checks for evidence;
- non-executable rendering of configured text;
- protection against active HTML/script injection;
- restricted immutable content references;
- safe logs without bidder payloads or secrets;
- rate/idempotency controls for submission;
- transaction locking for submission;
- approved cryptographic sealing abstraction;
- immutable seal and receipt references;
- pre-opening confidentiality;
- audited lawful-opening transition;
- no manifest credentials, tokens, private keys, or internal network locations.

Do not replace a repository's approved security or sealing provider. Integrate with it through its existing boundary.

---

## 19. Scalability and Performance

The implementation must not assume:

- exactly 10 sections;
- exactly 23 groups;
- exactly 190 requirements;
- exactly 22 price rows;
- one bidder entity;
- one evidence item per task;
- one STD family;
- one lot;
- one language; or
- an unchunked manifest resource.

Requirements:

- paginate or virtualize large row resources while preserving logical order;
- cache immutable resources by ID and digest;
- verify cached resource digests;
- avoid N+1 response, evidence, and issue queries;
- fetch only authorized financial data;
- retain deterministic order across pagination/chunking;
- keep compiler behavior logically identical whether resources are inline or external;
- report compiler-stage timing without logging confidential values;
- ensure partial resource loading cannot make a section appear complete; and
- keep submission validation authoritative even if the client holds stale cached state.

Do not add arbitrary performance thresholds without repository requirements. Record benchmark results for the NSSF fixture and identify material bottlenecks.

---

## 20. Seed and Fixture Data

Add seed/test data only through fixture namespaces.

Required fixtures:

1. canonical IT STD binding metadata;
2. NSSF tender snapshot;
3. eight NSSF controlled decisions;
4. nine content-addressed resource files/descriptors;
5. corrected 10-section golden projection;
6. exact diagnostic set;
7. legacy NSSF schema;
8. representative legacy draft workspace;
9. expected migration dry-run report;
10. representative bidder organization and users;
11. current and revoked authority records;
12. evidence versions and reusable links;
13. pre-deadline and post-deadline clock scenarios;
14. successful sealed submission and receipt reconstruction fixture.

Never load NSSF fixtures automatically into production environments.

---

## 21. Required Code and Artifact Outputs

Follow repository conventions, but produce all applicable outputs:

### 21.1 Schemas and domain

- versioned manifest schemas;
- rule/calculation AST schemas;
- response/evidence/confirmation/submission schemas;
- migration schemas;
- domain models/value objects;
- migrations and constraints;
- repositories and immutable-resource adapters.

### 21.2 Services

- compiler and stages;
- canonicalization/digest service;
- resource verifier;
- validation/readiness service;
- governance/approval/publication service;
- checklist/status projection;
- response/evidence services;
- confirmation/authority integration;
- submission/seal/receipt service;
- addendum diff/impact service;
- downstream projection service;
- legacy migration adapter.

### 21.3 Fixtures

- normalized NSSF resource objects;
- descriptor registry;
- golden projection oracle;
- exact diagnostics;
- legacy source fixture;
- migration expected outputs.

### 21.4 Frontend integration

- manifest client/types;
- section renderer registry;
- checklist projection integration;
- Requirements Compliance resource loading;
- right-hand response drawer integration;
- Evidence and Issue views;
- Review/Submit/Receipt integrations;
- server-authoritative error handling.

### 21.5 Tests and reports

- all binding tests;
- repository-specific tests;
- migration dry-run report;
- resource digest report;
- full manifest digest report;
- golden projection comparison;
- canonical-code NSSF-constant audit;
- implementation report.

Do not create duplicate documentation files when the repository already has an established location. Update the appropriate implementation index.

---

## 22. Cursor Execution Protocol

Cursor must work in this order:

1. inspect;
2. map existing components to this directive;
3. identify gaps;
4. implement the smallest coherent phase;
5. run focused tests;
6. run existing affected test suites;
7. review diffs for unrelated changes;
8. continue to the next phase;
9. run the complete suite;
10. produce implementation evidence.

Cursor must not:

- return only a plan;
- stop after generating types;
- replace implementation with mock data;
- skip migrations;
- skip governance;
- skip authority;
- skip negative tests;
- claim a test passed without running it;
- weaken a failing test to make it pass;
- delete legacy evidence;
- modify unrelated code;
- leave material unfinished markers, placeholder text, or stub behavior;
- hide a blocked requirement behind a feature flag unless the repository already governs that capability and the blocker is reported.

If the complete directive cannot be implemented in one context window, Cursor must finish the current atomic phase, leave the repository passing, and return the exact next phase and remaining acceptance tests. It must not mix incomplete changes from multiple phases.

---

## 23. Required Cursor Completion Response

Cursor's final response must contain:

1. outcome;
2. repository assessment;
3. architecture mapping;
4. files created/modified;
5. database migrations;
6. compiler stages implemented;
7. governance/state transitions implemented;
8. permissions and authority controls implemented;
9. fixture/resource results;
10. migration dry-run results;
11. test commands and exact pass/fail counts;
12. full manifest payload digest;
13. golden projection digest comparison;
14. diagnostic digest comparison;
15. NSSF-constant boundary scan result;
16. security/concurrency verification;
17. any hard blocker or explicitly deferred out-of-scope item.

Do not summarize a failed or unrun test as successful.

---

## 24. Required Implementation Evidence

Preserve and report:

| Evidence | Required content |
|---|---|
| Repository assessment | Stack, relevant modules, existing models/services, approved UI components, migration/test conventions |
| Source verification | Actual paths and verified input digests |
| Compiler trace | All 22 stages and deterministic outputs |
| Coverage report | Disposition of every applicable canonical obligation |
| Resource report | IDs, schemas, counts, logical digests, storage refs |
| Readiness report | Errors, warnings, information, coverage, renderers, rules, projections |
| Governance evidence | State transitions, approval digest binding, atomic publication test |
| NSSF golden comparison | 10 sections and all declared counts |
| Full manifest integrity | RFC 8785 JCS payload digest |
| Projection integrity | Expected and actual `461ffc...ffa22` digest |
| Diagnostic integrity | Expected and actual `b3bbc...e84f7` digest |
| Migration dry run | Counts by disposition, unmapped count, blockers, reconfirmations |
| Deterministic replay | First and second payload/digest comparison |
| Test report | Commands, suites, pass/fail/skip counts |
| Boundary scan | NSSF constants outside allowed fixture/migration paths |
| Reconstruction proof | Exact manifest/resource/response/evidence/confirmation/submission refs for a sample sealed bid |

---

## 25. Hard Blockers

Cursor may stop and request direction only when:

1. a required canonical input is absent or its digest cannot be reconciled;
2. the repository lacks a required authority, transaction, or sealing boundary and implementing one would require a material architecture decision beyond this directive;
3. an existing production migration would destructively overwrite or delete bidder data;
4. two binding legal sources remain genuinely inconsistent after applying Section 4;
5. production execution is requested without an approved snapshot, approval, or migration authorization;
6. repository permissions prevent safe implementation or verification; or
7. unrelated user changes directly conflict with required edits and cannot be preserved.

A hard-blocker report must state:

- exact blocker;
- affected phase/files;
- evidence;
- safe work completed;
- alternatives and trade-offs;
- the smallest user decision required.

Ordinary naming, file placement, component reuse, and implementation details are not hard blockers; resolve them from repository conventions.

---

## 26. Smoke Contract

The implementation fails if any of the following is possible:

1. NSSF data changes a canonical template.
2. A hard-coded checklist replaces manifest projection.
3. The NSSF fixture compiles nine rather than ten content sections.
4. Tender Security is missing.
5. “Professional Indemnity” is handled as generic insurance evidence.
6. Lots & Alternatives appears for NSSF.
7. Statutory Declarations is missing.
8. Contract Terms Acknowledgement remains a content section.
9. Final Declaration and Submission remains a content section.
10. Microsoft authorization remains in CBQ.
11. Pending litigation remains in CBQ.
12. A signed Form of Tender upload replaces the electronic form.
13. Saving creates a legal confirmation.
14. A free-text signatory proves authority.
15. A bidder score exists in bidder response data.
16. A requirement page reference is the primary response.
17. A prohibited deviation can be submitted.
18. Any required NSSF resource count or digest differs without failure.
19. A blank price becomes zero or included.
20. Price totals can diverge from the Form of Tender.
21. A price change leaves Form of Tender confirmation current.
22. Evidence must be uploaded repeatedly instead of linked.
23. File presence alone satisfies evidence.
24. A bidder/client can set completion status.
25. An unsupported renderer falls back to an unvalidated control.
26. A blocker has no correction owner.
27. A submission blocker does not rerun at submission.
28. Client time determines deadline eligibility.
29. Concurrent submission creates duplicate authoritative bids.
30. Failed sealing creates a receipt.
31. A legacy confirmation becomes a canonical confirmation automatically.
32. A legacy submission becomes sealed.
33. Migration loses source lineage.
34. Migration leaves a source object without a disposition.
35. Published manifest content can be edited.
36. Tender and manifest publication is non-atomic.
37. Approval survives a payload-digest change.
38. A digest mismatch is downgraded to a warning.
39. A resource can load partially and still complete a section.
40. Opening exposes an undeclared field.
41. Evaluation edits bidder content.
42. Contract carry-forward loses sealed provenance.
43. Historical reconstruction uses current templates.
44. Identical compile inputs yield different payloads.
45. The projection oracle is shipped as the complete closed runtime manifest.
46. NSSF constants appear in canonical production code.
47. The historical source is represented as an actual electronic republication.
48. Production NSSF fixtures load automatically.

---

## 27. Final Acceptance Gate

Implementation is complete only when:

- every phase exit gate passes;
- existing repository tests remain passing;
- all 102 binding tests pass;
- repository-specific new tests pass;
- every required schema and domain invariant is implemented;
- governance and state transitions are enforced;
- roles and authority are separate;
- the complete manifest schema is generated;
- full runtime payload digest is recorded;
- projection and diagnostic digests match;
- all NSSF counts match;
- legacy migration dry run has zero silent unmapped objects;
- all required legal confirmations are marked for reconfirmation;
- deterministic replay succeeds;
- atomic publication and submission tests succeed;
- pre-opening confidentiality tests succeed;
- no prohibited NSSF constant exists in canonical code;
- no material stub or placeholder remains;
- implementation evidence is preserved.

---

## 28. Direct Cursor Instruction

```text
Implement this directive in the existing KenTender repository.

First inspect the repository and map its current architecture to the required
boundaries. Then execute Phases 1 through 10 in order. Preserve existing
conventions and unrelated work.

Use the official canonical PPRA IT artifacts as authority. Treat NSSF only as
fixture data and a migration source. Apply the resolved ten-section NSSF model,
including Tender Security under NSSF-DEC-SEC-001.

Implement the complete closed manifest contract, deterministic compiler,
content-addressed resources, governance and atomic publication, manifest-driven
Bidder Workspace, versioned responses and evidence, validation and invalidation,
authorized confirmations, Submit & Seal, projections, and one-way legacy
migration.

Do not redesign approved Stitch screens. Implement their behavior using the
existing component system. Preserve the right-hand response drawer for
Requirements Compliance.

Run all existing tests, BWMF-T001 through BWMF-T054 with corrected NSSF
expectations, NSSF-GOLD-001 through NSSF-GOLD-048, and all new tests required
by this directive.

Do not stop at a plan or partial scaffold. Stop only for a hard blocker in
Section 25. On completion, return the exact evidence listed in Sections 23 and
24.
```

---

## 29. Final Control Statement

```text
Cursor implements; it does not redesign.
The official STD controls legal meaning.
The catalogue and blueprint control bidder obligations and ownership.
The compiler is deterministic, declarative, version-bound, and fail-closed.
Publication is governed, approved, atomic, and immutable.
The Bidder Workspace renders only the published manifest.
NSSF is a corrected ten-section calibration fixture, not a canonical model.
Legacy data migrates through explicit dispositions and reconfirmation.
Submission is authorized, validated, sealed, immutable, and reconstructable.
```
