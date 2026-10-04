# STD-TPL-IMP-001 — Installed STD Template Runtime

| Control | Value |
|---|---|
| Document ID | STD-TPL-IMP-001 |
| Version | 1.0 |
| Date | 25 September 2026 |
| Status | **Proposed for approval** |
| Requirements authority | STD-TPL-001 v0.10 proposed |
| Coordinated consumers | TPR-CHG-001 v0.11 proposed; BDS-CHG-001 v0.7 proposed |
| Responsibility authority | AUTH-ADR-001 v1.10 proposed |
| Design standard | KT-STD-001 v1.8 |
| Supersedes | STD-TPL-IMP-001 v0.2, which is historical and not implementation authority |
| Purpose | Implement exact controlled STD releases, their inspection, deterministic compilation and lifecycle without creating a runtime template editor |

## 1. Outcome

KenTender shall install an owner-approved STD release as immutable assets, verify the exact manifest transactionally, expose a clear read-only **STD Templates** module, and supply the same deterministic compiler and renderer contracts to Tender Preparation and Bid Submission.

This document does not author the `IT-EQUIPMENT-OPEN-V1` content. STD-TPL-001 v0.10 and the exact approved release pack own that content. This document defines how code stores, verifies, exposes and consumes it.

## 2. Scope and non-goals

### 2.1 In scope

- exact-manifest installation and upgrade;
- immutable private asset storage;
- installed-release records and projections;
- release coverage and change inspection;
- bounded concern reporting;
- the shared Published Bid Definition compiler;
- renderer-adapter registration and compatibility checks;
- binding, supersession and withdrawal enforcement;
- affected-Tender projections;
- audit, migration, deployment and automated tests.

### 2.2 Not in scope

- site-authored clauses, forms, fields, criteria or mappings;
- browser upload of a template bundle;
- generic JSON editing or schema building;
- a second site-adoption approval;
- legal-content authoring in Frappe;
- silent repair of a failed release;
- automatic Tender rebinding;
- candidate registration, clarifications, notices, Bid custody or evaluation execution.

## 3. Architecture

Use four bounded components:

| Component | Responsibility | Prohibited responsibility |
|---|---|---|
| Release installer | Verify and atomically install an exact approved manifest and immutable assets | Approve, rewrite or partially install a release |
| Release registry | Persist lifecycle, evidence, compatibility, summaries and asset identities | Store editable template content |
| Template runtime | Compile published Bid definitions and call registered renderer adapters | Query users, infer policy or fall back to arbitrary controls |
| Inspection surface | Return authorised read projections and accept bounded concerns | Expose raw storage as the normal UI or mutate a release |

The curation CLI and production service call one shared `CompilePublishedBidDefinition` implementation. A fixture-specific compiler is not permitted.

## 4. Data model

### 4.1 `InstalledSTDRelease`

One immutable content identity plus controlled lifecycle facts:

| Field | Contract |
|---|---|
| `release_id` | Opaque immutable primary identity |
| `template_key`, `template_release`, `display_name` | Exact manifest values; unique pair `template_key + template_release` |
| `lifecycle_status` | `Candidate`, `Available`, `Superseded`, `Withdrawn` |
| `product_profile_id`, `renderer_profile_id`, `supported_renderer_version` | Exact compatibility identities |
| `official_source_title`, `official_source_digest`, `source_retrieved_at` | Exact source identity |
| `source_checked_by`, `source_checked_at`, `source_check_outcome` | Named verification evidence |
| `bundle_digest`, `manifest_digest`, `validation_report_digest`, `release_gates_digest`, `release_change_report_digest` | Lowercase SHA-256 values |
| `owner_decision`, `owner_approved_by`, `owner_approved_at` | Exact-manifest decision; required for Available |
| `installed_by`, `installed_at`, `repository_commit` | Deployment evidence |
| `supported_use_summary`, `rejected_use_summary`, `document_summary`, `response_summary`, `evaluation_summary`, `contract_summary`, `reservation_support` | Versioned read projections from the manifest |
| `verification_results`, `blockers` | Structured evidence; not editable through Desk |
| `superseded_by_release_id`, `superseded_at` | Optional non-safety successor facts |
| `withdrawal_reason`, `withdrawn_by`, `withdrawn_at`, `withdrawal_successor_release_id` | Required withdrawal facts except optional successor |

Content and digest fields are immutable after successful installation. Lifecycle changes append audit evidence; they do not rewrite the installed manifest.

### 4.2 `InstalledSTDReleaseAsset`

Child rows are immutable and unique by `release_id + relative_path`:

`relative_path`, `asset_role`, `mime_type`, `byte_size`, `sha256_digest`, `private_file_id`.

Every controlled manifest asset has one row and every row has one asset. Files remain private. Download and preview use authorised services, never predictable public paths.

### 4.3 `STDTemplateConcern`

This is deliberately smaller than an incident-management system:

| Field | Contract |
|---|---|
| `concern_id`, `release_id` | Immutable identity and exact installed release |
| `category` | `Source treatment`, `Tender document`, `Supplier response`, `Evaluation mapping`, `Contract mapping`, `Renderer`, `Other` |
| `source_locator` | Optional source row, document anchor or visible section |
| `summary`, `description` | Required concise text; bounded lengths |
| `evidence_file_id` | Optional private attachment |
| `status` | `Open`, `Acknowledged`, `Resolved`, `Rejected` |
| `reported_by`, `reported_at` | System-derived actor and time |
| `resolved_by`, `resolved_at`, `resolution_note`, `successor_release_id` | Controlled owner resolution |

Creating a concern does not change lifecycle, block a Tender or alter release content. A release owner decides whether it requires a corrected successor or withdrawal.

### 4.4 No additional content DocTypes

Do not create editable DocTypes for template sections, clauses, response rows, evaluation mappings or contract mappings. They remain signed release assets projected for inspection.

## 5. Installation and upgrade

### 5.1 Input

The deployable package contains the exact approved release pack plus:

- manifest-file digest;
- owner decision binding `release_id`, `template_release`, `bundle_digest` and `manifest_digest`;
- package signature or repository release provenance accepted by the deployment process; and
- the runtime adapter versions declared by the manifest.

### 5.2 Transaction

`InstallApprovedSTDRelease` shall:

1. unpack into an isolated staging directory;
2. reject paths outside the package root, links, duplicates and undeclared files;
3. calculate every asset digest, bundle digest and manifest digest;
4. validate schema versions and exact owner decision;
5. check the registered compiler and renderer adapter versions;
6. verify every mandatory release gate is `Passed` with evidence;
7. store private immutable assets and registry rows in one transaction;
8. expose `Available` only after the transaction commits; and
9. remove staging data after success or rollback.

The installer is idempotent for the same exact release and digests. A different byte under an existing identity fails. A failed install leaves no selectable partial release.

### 5.3 Deployment authority

Installation verifies the template-owner approval; it does not request another approval from a site administrator. The production deployment pipeline may restrict who invokes installation, but that access control is not a substantive release decision.

## 6. Services

| Service | Result and guard |
|---|---|
| `InstallApprovedSTDRelease` | Exact verified registry and assets; deployment-only |
| `ListInstalledSTDReleases` | Compact `InstalledSTDReleaseProjection v1` list |
| `GetInstalledSTDRelease` | Complete authorised detail projection |
| `ListSTDReleaseCoverage` | Paged/filterable source-treatment rows |
| `GetSTDReleaseChangeReport` | Generated preceding-release comparison |
| `PreviewSTDReleaseDocument` | Authorised immutable HTML/PDF preview |
| `DownloadSTDReleaseReviewPack` | Authorised exact review pack |
| `CreateSTDTemplateConcern` | Bounded concern only |
| `ListSTDTemplateConcerns` | Release-owner queue and authorised release detail summary |
| `ResolveSTDTemplateConcern` | Resolution facts; no content mutation |
| `CheckSTDReleaseCompatibility` | Deterministic supported/rejected result for an authorised Requisition/Tender input |
| `CompilePublishedBidDefinition` | Pure canonical definition result or typed failure |
| `RenderSTDDocument` | Output from a registered adapter for exact profile/version |
| `SupersedeSTDRelease` | Lifecycle transition and optional successor |
| `WithdrawSTDRelease` | Reasoned lifecycle transition and affected-Tender projection |
| `ListTendersAffectedBySTDRelease` | Bound unpublished/published Tender counts and identities subject to caller scope |

No service accepts arbitrary clause, field, mapping or executable expression input.

## 7. Shared compiler

`CompilePublishedBidDefinition` accepts only:

- exact installed release identity and verified assets;
- immutable `TenderVersion v1`;
- `publication_id`;
- ordered effective addenda; and
- the release-declared compilation context.

It returns the complete `PublishedBidDefinition v1` or a typed error. It is deterministic, side-effect-free and free of Frappe queries. Canonical JSON uses UTF-8, sorted object keys, defined decimal/date formats and no insignificant whitespace before digesting.

The curation fixture adapter loads files and calls this compiler. The production service loads authorised projections and calls the same compiler. CI runs the approved fixture vectors through both adapters and requires byte-identical canonical output and digest.

## 8. Renderer adapters

Implement a registry keyed by `renderer_profile_id + supported_renderer_version`. An adapter declares:

- supported controls and compositions;
- document engine and exact version;
- sanitisation and local-resource policy;
- page, font and print-CSS support;
- deterministic text-extraction and visual-regression procedure; and
- runtime health check.

The release manifest binds the adapter identity, not an unversioned executable name. The current engine may reproduce the approved fixture, but changing engine or version requires a new adapter version and complete release evidence. Missing or unhealthy adapters block new binding, publication and Bid start; there is no generic fallback.

## 9. Release lifecycle and bound Tenders

| Release state | New Tender binding | Already-bound unpublished Tender | Published Tender |
|---|---|---|---|
| Candidate | Prohibited | Not possible | Not applicable |
| Available | Permitted after compatibility check | May proceed while integrity/adapters pass | Exact release retained |
| Superseded | Prohibited | May proceed only while integrity/adapters pass; show successor notice | Exact release retained and readable |
| Withdrawn | Prohibited | Publication and Bid start blocked; cancel/start new or follow an explicit TPR correction route | Exact historical release remains immutable/readable with withdrawal notice |

No transition rewrites a `TenderVersion`, document, publication or Published Bid Definition. No automatic successor binding is allowed.

Withdrawal requires reason, actor and time; successor is optional. The operation atomically creates the affected-Tender projection and audit event. It does not delete assets or published evidence.

## 10. Permissions

| Capability | Administrator / System Manager | Procurement Officer | HOPF | Other roles |
|---|---:|---:|---:|---:|
| List/detail/coverage/change/preview | Yes | Yes | Yes | No, unless a consuming module explicitly grants scoped evidence access |
| Report concern | Yes | Yes | Yes | No |
| View own concern status | Yes | Yes | Yes | No |
| Resolve concern | Controlled release owner only | No | No | No |
| Install/supersede/withdraw | Deployment/release-owner service only | No | No | No |
| Edit release content | No | No | No | No |

Permission checks run server-side. Possessing Administrator or System Manager does not create a release-owner approval or content-edit privilege.

## 11. UI and routes

Implement STD-TPL-001 v0.10 §11 exactly:

- `/app/std-templates`;
- `/app/std-templates/{release_id}`;
- detail sections **Overview**, **Tender content**, **Bid response and downstream use**, **Coverage and changes**, **Verification**;
- collapsed **Technical details**;
- bounded **Report concern** dialog.

The browser consumes owner projections. It does not read ZIPs, parse PDF, calculate digests, compare releases or reconstruct coverage. Large coverage/change results use server paging and preserve filters. Raw JSON may be downloaded only inside the authorised review pack, never used as the ordinary detail UI.

## 12. Errors

| Code | Meaning | User treatment |
|---|---|---|
| `STD_RELEASE_NOT_FOUND` | Unknown or unauthorised identity | Not found without leaking existence |
| `STD_RELEASE_NOT_AVAILABLE` | New binding attempted against a non-Available release | Choose a currently available compatible format |
| `STD_RELEASE_WITHDRAWN` | Operation requires an unpublished Tender bound to a Withdrawn release | Publication cannot continue; show governed next steps |
| `STD_RELEASE_INTEGRITY_FAILED` | Manifest or asset digest differs | Block use and direct to release owner |
| `STD_RELEASE_GATE_INCOMPLETE` | Gate missing, Pending or Failed | Block installation/availability and name gate |
| `STD_RENDERER_UNSUPPORTED` | Exact adapter is missing or incompatible | Block render/publication/Bid start |
| `STD_INPUT_UNSUPPORTED` | Tender input is outside release boundary | Name unsupported fact and stop |
| `STD_DEFINITION_INVALID` | Compiler finds an unknown/orphaned rule or mapping | Block publication and name stable identity |
| `STD_CONCERN_INVALID` | Concern fails bounded validation | Preserve entered values and identify correction |

Do not expose filesystem paths, stack traces or private asset URLs.

## 13. Audit and observability

Audit successful and failed installation, lifecycle transition, preview/download, concern creation/resolution, compatibility decision, compilation and rendering. Record actor/service identity, time, release, Tender/publication where applicable, result and correlation ID. Never log supplier secrets or full Bid responses.

Operational metrics include installation failures, integrity failures, unavailable adapter, compiler failure by code, concern ageing and affected unpublished Tenders after withdrawal.

## 14. Migration and deployment

1. create registry, asset and concern schema;
2. register compiler and renderer adapters;
3. package the exact approved 1.1 release only after its gates and owner decision pass;
4. run install in staging and reproduce canonical documents/definition;
5. deploy records and assets transactionally;
6. enable **STD Templates** navigation and permissions;
7. enable Tender binding only after registry health checks pass; and
8. preserve the older `/07_tender_templates` artefacts as curation evidence, not mutable runtime configuration.

Existing Tender records cannot be backfilled with a guessed release. A migration must prove their exact template identity and digests or mark them legacy/read-only outside the new publication path.

## 15. Acceptance contract

| ID | Acceptance criterion |
|---|---|
| STI10-AC-001 | Installation fails closed unless every asset, digest, gate, adapter and exact owner decision matches. |
| STI10-AC-002 | A failed installation exposes no partial/selectable release. |
| STI10-AC-003 | Installed assets and content identities are immutable and private. |
| STI10-AC-004 | No editable clause, field, response, evaluation or contract-mapping DocType is introduced. |
| STI10-AC-005 | List/detail/coverage/change projections satisfy STD-TPL-001 v0.10 §11 without browser reconstruction. |
| STI10-AC-006 | Administrator, System Manager, Procurement Officer and HOPF have the prescribed read/concern access and no template-edit privilege. |
| STI10-AC-007 | Concern creation has no automatic lifecycle or Tender effect. |
| STI10-AC-008 | Fixture and production adapters return identical canonical Published Bid Definition output for every approved vector. |
| STI10-AC-009 | An unknown control, mapping, input or adapter produces a typed failure and no fallback. |
| STI10-AC-010 | New binding uses only Available releases after compatibility checks. |
| STI10-AC-011 | Superseded allows only integrity-checked continuation of already-bound unpublished Tenders. |
| STI10-AC-012 | Withdrawn blocks new binding and publication/Bid start for already-bound unpublished Tenders without changing published records. |
| STI10-AC-013 | No lifecycle event automatically rebinds a Tender. |
| STI10-AC-014 | Installation verifies the one exact-manifest approval and creates no duplicate site-adoption approval. |
| STI10-AC-015 | Renderer engine/version changes require a new adapter identity and complete regression evidence. |
| STI10-AC-016 | The implementation passes desktop, keyboard, 200% zoom and 390 px requirements in KT-STD-001 v1.8. |

## 16. Required tests

At minimum automate:

- path traversal, symlink, duplicate and undeclared-asset rejection;
- corrupt asset, bundle, manifest, gate and owner-decision digests;
- idempotent identical install and conflicting-identity rejection;
- transaction rollback at each installation stage;
- access matrix and server-side denial;
- complete projection/fixture values, paging and filter persistence;
- concern validation, private evidence and no lifecycle side effect;
- compiler golden vectors, property determinism and CLI/production parity;
- renderer missing, wrong version, unhealthy and regression mismatch;
- Available, Superseded and Withdrawn binding/publication matrices;
- affected-Tender projection and historical published readability;
- audit redaction and stable error codes; and
- prohibited editor/upload/activate routes returning denial or not existing.

## 17. Implementation order

1. schema and immutable asset repository;
2. fail-closed installer and manifest/gate verification;
3. shared compiler and canonical vectors;
4. renderer-adapter registry;
5. read projections and permission checks;
6. STD Templates UI and concern capture;
7. Tender compatibility/binding hooks;
8. supersession/withdrawal enforcement and affected-Tender projection;
9. deployment migration, audit and full regression.

Do not build the UI first against invented placeholder data. The projections and closed fixtures are the UI source.

## 18. Traceability

| Requirement owner | This implementation supplies |
|---|---|
| STD-TPL-001 v0.10 | Installation, inspection, compiler, renderer and lifecycle implementation |
| TPR-CHG-001 v0.11 | Available-only new binding; bound-release checks; Withdrawn failure; immutable exact identity |
| BDS-CHG-001 v0.7 | Exact Published Bid Definition and renderer compatibility; no PDF parsing |
| AUTH-ADR-001 v1.10 | Module-specific inspection/concern permissions without responsibility mutation |
| KT-STD-001 v1.8 | Artboard, accessibility and verification quality |

## 19. Approval effect

Approval makes v1.0 the implementation authority for the installed STD template runtime and retires v0.2 from active use. It does not approve release 1.1 content or make that candidate Available. The exact bundle must still pass STD-TPL-001 v0.10 and receive its exact-manifest owner decision.
