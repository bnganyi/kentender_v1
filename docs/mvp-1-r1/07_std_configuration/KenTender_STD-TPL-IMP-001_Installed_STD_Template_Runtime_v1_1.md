# STD-TPL-IMP-001 — Installed STD Template Runtime

| Control | Value |
|---|---|
| Document ID | STD-TPL-IMP-001 |
| Version | 1.1 |
| Date | 26 September 2026 |
| Status | **Proposed for approval** — v1.0 was proposed on 25 September 2026 and never approved; Project Owner approval of v1.1 is required |
| Approved on | Not yet approved |
| Approval record | None for v1.1. None for v1.0, which was never approved. On 25 September 2026 the Project Owner answered "Authorised" to "Approve the two documents, or authorise building against them as proposed."; that authorised building against v1.0 as proposed and is not an approval. |
| Owner decision applied | OD5, Project Owner, 26 September 2026: "I don't want this complicated admin overhead regarding approvals and commissioning of templates. It is unnecessary, adds no value and is vexing. Allow development work to contine without this friction. Template release is purely an on and off switch on an affected site. Update this decision as a follow up to reflect in affected documents if necessary" |
| Owner instruction for this revision | Project Owner, 26 September 2026: "Close the open issues" |
| Requirements authority | STD-TPL-001 v0.10 proposed. Owner decision OD5 overrides its exact-manifest approval, `Candidate` and availability provisions; §21 lists the corrections STD-TPL-001 needs |
| Coordinated consumers | TPR-CHG-001 v0.11 proposed; BDS-CHG-001 v0.7 proposed |
| Responsibility authority | AUTH-ADR-001 v1.10 proposed |
| Design standard | KT-STD-001 v1.8 |
| Supersedes | STD-TPL-IMP-001 v1.0 (proposed 25 September 2026, never approved); STD-TPL-IMP-001 v0.2, which is historical and not implementation authority |
| Change type | Owner-directed revision for owner decision OD5 only: a template release is an On/Off switch on a site. Installation needs no owner approval and creates no `Candidate`; an intact release installs `Available` and switched On; switched Off blocks new Tender binding only. Integrity checks, fail-closed installation on any integrity failure, Superseded and Withdrawn are unchanged; recorded gate results become evidence (§5.2). Full changes: §20. |
| Purpose | Implement exact controlled STD releases, their inspection, deterministic compilation and lifecycle without creating a runtime template editor |

## 1. Outcome

KenTender shall install an intact (v1.0 read: owner-approved) STD release as immutable assets, verify the exact manifest transactionally, give each site an On/Off switch for the installed release (owner decision OD5), expose a clear read-only **STD Templates** module, and supply the same deterministic compiler and renderer contracts to Tender Preparation and Bid Submission.

This document does not author the `IT-EQUIPMENT-OPEN-V1` content. STD-TPL-001 v0.10 and the exact release pack (v1.0 read: the exact approved release pack) own that content. This document defines how code stores, verifies, exposes and consumes it.

## 2. Scope and non-goals

### 2.1 In scope

- exact-manifest installation and upgrade;
- immutable private asset storage;
- installed-release records and projections;
- release coverage and change inspection;
- bounded concern reporting;
- the shared Published Bid Definition compiler;
- renderer-adapter registration and compatibility checks;
- binding, supersession and withdrawal enforcement, and the per-site On/Off switch (owner decision OD5);
- affected-Tender projections;
- audit, migration, deployment and automated tests.

### 2.2 Not in scope

- site-authored clauses, forms, fields, criteria or mappings;
- browser upload of a template bundle;
- generic JSON editing or schema building;
- a second site-adoption approval;
- an owner approval or commissioning step as a condition of installing or using a release (owner decision OD5);
- a Desk or browser control for the site switch, which is a deployment command (§10);
- legal-content authoring in Frappe;
- silent repair of a failed release;
- automatic Tender rebinding;
- candidate registration, clarifications, notices, Bid custody or evaluation execution.

## 3. Architecture

Use four bounded components:

| Component | Responsibility | Prohibited responsibility |
|---|---|---|
| Release installer | Verify and atomically install an exact manifest (v1.0 read: an exact approved manifest) and immutable assets, switched On unless the deployment asks for Off | Approve, rewrite or partially install a release |
| Release registry | Persist lifecycle, site switch, evidence, compatibility, summaries and asset identities | Store editable template content |
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
| `lifecycle_status` | `Available`, `Superseded`, `Withdrawn`. There is no `Candidate` state: an intact release installs as `Available`, whatever the constructed manifest `status` value in STD-TPL-001 v0.10 §13.9 says (owner decision OD5) (v1.0 read: `Candidate`, `Available`, `Superseded`, `Withdrawn`) |
| `site_switch`, `switched_by`, `switched_at` | Site switch `On` or `Off`, who last set it and when (owner decision OD5). Installation sets `On`, or `Off` when the deployment asks, and records the installer as `switched_by`. Changed only by `SwitchSTDRelease` while `lifecycle_status` is `Available`; not editable through Desk |
| `product_profile_id`, `renderer_profile_id`, `supported_renderer_version` | Exact compatibility identities |
| `official_source_title`, `official_source_digest`, `source_retrieved_at` | Exact source identity |
| `source_checked_by`, `source_checked_at`, `source_check_outcome` | Named verification evidence |
| `bundle_digest`, `manifest_digest`, `validation_report_digest`, `release_gates_digest`, `release_change_report_digest` | Lowercase SHA-256 values |
| `owner_decision`, `owner_approved_by`, `owner_approved_at` | Exact-manifest decision, recorded as evidence only when the package carries one; not required for Available or for use (owner decision OD5) (v1.0 read: Exact-manifest decision; required for Available) |
| `installed_by`, `installed_at`, `repository_commit` | Deployment evidence |
| `supported_use_summary`, `rejected_use_summary`, `document_summary`, `response_summary`, `evaluation_summary`, `contract_summary`, `reservation_support` | Versioned read projections from the manifest |
| `verification_results`, `blockers` | Structured evidence; not editable through Desk |
| `superseded_by_release_id`, `superseded_at` | Optional non-safety successor facts |
| `withdrawal_reason`, `withdrawn_by`, `withdrawn_at`, `withdrawal_successor_release_id` | Required withdrawal facts except optional successor |

Content and digest fields are immutable after successful installation. Lifecycle changes append audit evidence; they do not rewrite the installed manifest. The site switch (owner decision OD5) is not a lifecycle change: switching appends audit evidence and changes no content, digest or lifecycle field.

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

The deployable package contains the exact release pack (v1.0 read: the exact approved release pack) plus:

- manifest-file digest;
- optionally, an owner decision binding `release_id`, `template_release`, `bundle_digest` and `manifest_digest`; when present it must name exactly this release, bundle and manifest, and it is recorded as evidence only (owner decision OD5; v1.0 required it);
- package signature or repository release provenance accepted by the deployment process; and
- the runtime adapter versions declared by the manifest.

### 5.2 Transaction

`InstallApprovedSTDRelease` shall:

1. unpack into an isolated staging directory;
2. reject paths outside the package root, links, duplicates and undeclared files;
3. calculate every asset digest, bundle digest and manifest digest;
4. validate schema versions and, when the package carries an owner decision, that it names this exact release, bundle and manifest (v1.0 read: validate schema versions and exact owner decision);
5. check the registered compiler and renderer adapter versions;
6. verify that the release-gate record lists every mandatory gate and that the release validator reports no Blocking failure; each gate result is stored as evidence, and a `Pending` or `Failed` gate result does not by itself prevent installation or use (owner decision OD5) (v1.0 read: verify every mandatory release gate is `Passed` with evidence);
7. store private immutable assets and registry rows in one transaction;
8. expose the release as `Available`, with its site switch `On` or, when the deployment asks, `Off`, only after the transaction commits (v1.0 read: expose `Available` only after the transaction commits); and
9. remove staging data after success or rollback.

The installer is idempotent for the same exact release and digests. A different byte under an existing identity fails. A failed install leaves no selectable partial release. An intact release installs directly as `Available`; nothing is installed as a `Candidate`, and any integrity failure installs nothing (owner decision OD5). Reinstalling the same exact release leaves its site switch as it is.

The service keeps the name `InstallApprovedSTDRelease` for continuity; under owner decision OD5 it requires no approval.

### 5.3 Deployment authority

Installation requires no approval (owner decision OD5); it verifies integrity and records any owner decision the package carries as evidence (v1.0 read: Installation verifies the template-owner approval); it does not request another approval from a site administrator. The production deployment pipeline may restrict who invokes installation or the site switch, but that access control is not a substantive release decision. Whether new Tenders may start on an installed release is decided by its site switch, subject to the integrity and renderer checks in §§8–9.

## 6. Services

| Service | Result and guard |
|---|---|
| `InstallApprovedSTDRelease` | Exact verified registry and assets, installed `Available` and switched `On` unless the deployment asks for `Off`; no approval required (owner decision OD5); deployment-only |
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
| `SwitchSTDRelease` | Site switch `On` or `Off` with the named actor and time, only while `lifecycle_status` is `Available` (otherwise `STD_RELEASE_NOT_AVAILABLE`; a Superseded or Withdrawn release stays as it is); audited; deployment-only (owner decision OD5) |
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
| Candidate — removed by owner decision OD5: no installed release is ever a Candidate; row retained as v1.0 history | Prohibited | Not possible | Not applicable |
| Available, switched On (v1.0 row read: Available) | Permitted after compatibility check; only the one switched-on Available release of the template key | May proceed while integrity/adapters pass | Exact release retained |
| Available, switched Off (owner decision OD5) | Prohibited | May proceed while integrity/adapters pass; switching Off never strands a started Tender | Exact release retained |
| Superseded | Prohibited | May proceed only while integrity/adapters pass; show successor notice | Exact release retained and readable |
| Withdrawn | Prohibited | Publication and Bid start blocked; cancel/start new or follow an explicit TPR correction route | Exact historical release remains immutable/readable with withdrawal notice |

No transition rewrites a `TenderVersion`, document, publication or Published Bid Definition. No automatic successor binding is allowed.

Withdrawal requires reason, actor and time; successor is optional. The operation atomically creates the affected-Tender projection and audit event. It does not delete assets or published evidence.

**Site switch (owner decision OD5).** The switch decides only whether a new Tender may bind the release; it is not a lifecycle state. A new Tender binds the one switched-on `Available` release of its template key. While more than one release of that key is switched On, new binding is refused with `STD_RELEASE_NOT_AVAILABLE` until one is switched Off or superseded. Every later action on a Tender that is already bound uses the release it bound, whether that release is switched On or Off, subject to the Superseded and Withdrawn rows above; switching Off never strands a started Tender. Switching rewrites no Tender record, asset or published evidence and never rebinds a Tender.

**Availability projection (owner decision OD5).** **STD Templates** projects a release as `Available` only while its lifecycle is `Available`, its site switch is On, its integrity verifies and its renderer adapter is registered; otherwise it projects `Unavailable`. `Superseded` and `Withdrawn` project as themselves. The blockers that stop use are derived live from the switch, integrity and renderer. Recorded gate results, review items and any owner decision are evidence shown under **Verification** or **Technical details**, never blockers.

## 10. Permissions

| Capability | Administrator / System Manager | Procurement Officer | HOPF | Other roles |
|---|---:|---:|---:|---:|
| List/detail/coverage/change/preview | Yes | Yes | Yes | No, unless a consuming module explicitly grants scoped evidence access |
| Report concern | Yes | Yes | Yes | No |
| View own concern status | Yes | Yes | Yes | No |
| Resolve concern | Controlled release owner only | No | No | No |
| Install/supersede/withdraw | Deployment/release-owner service only | No | No | No |
| Switch a release On or Off on this site | Deployment command only, audited; no Desk action | No | No | No |
| Edit release content | No | No | No | No |

Permission checks run server-side. Possessing Administrator or System Manager does not create a release-owner approval or content-edit privilege. Nor does it provide a Desk action that switches a release.

Deployment commands (owner decision OD5), run from the repository root:

- install: `make std-release-install SITE=<site> [SWITCH=Off]` installs the exact release pack switched On, or switched Off when `SWITCH=Off` is given;
- switch: `make std-release-switch SITE=<site> STATE=On|Off [RELEASE_ID=<release>] [RELEASE_OWNER=<name>]` runs `SwitchSTDRelease`; `RELEASE_OWNER` names the actor recorded as `switched_by`.

Each switch writes a **Switched On** or **Switched Off** audit event with the actor, the time and the previous position. Switching a release to the position it already has changes nothing and writes no event.

## 11. UI and routes

Implement STD-TPL-001 v0.10 §11 exactly:

- `/app/std-templates`;
- `/app/std-templates/{release_id}`;
- detail sections **Overview**, **Tender content**, **Bid response and downstream use**, **Coverage and changes**, **Verification**;
- collapsed **Technical details**;
- bounded **Report concern** dialog.

The browser consumes owner projections. It does not read ZIPs, parse PDF, calculate digests, compare releases or reconstruct coverage. Large coverage/change results use server paging and preserve filters. Raw JSON may be downloaded only inside the authorised review pack, never used as the ordinary detail UI.

Owner decision OD5 changes the projection that STD-TPL-001 v0.10 §§11.3–11.4 describe, until STD-TPL-001 is revised (§21): **Verification** shows the release's site switch, with who switched it and when, in place of the **Owner approval** row; a recorded owner decision appears only under **Technical details**; and no screen offers a switch, activation or approval action.

## 12. Errors

| Code | Meaning | User treatment |
|---|---|---|
| `STD_RELEASE_NOT_FOUND` | Unknown or unauthorised identity | Not found without leaking existence |
| `STD_RELEASE_NOT_AVAILABLE` | New binding attempted against a release that is not both `Available` and switched On, or while more than one release of the template key is switched On; or a switch attempted on a release that is not `Available` (owner decision OD5) (v1.0 read: New binding attempted against a non-Available release) | Choose a currently available compatible format |
| `STD_RELEASE_WITHDRAWN` | Operation requires an unpublished Tender bound to a Withdrawn release | Publication cannot continue; show governed next steps |
| `STD_RELEASE_INTEGRITY_FAILED` | Manifest or asset digest differs | Block use and direct to release owner |
| `STD_RELEASE_GATE_INCOMPLETE` | The release-gate record omits a mandatory gate (v1.0 read: Gate missing, Pending or Failed); under owner decision OD5 a recorded `Pending` or `Failed` result is evidence, not this error | Block installation and name the missing gate (v1.0 read: Block installation/availability and name gate) |
| `STD_RENDERER_UNSUPPORTED` | Exact adapter is missing or incompatible | Block render/publication/Bid start |
| `STD_INPUT_UNSUPPORTED` | Tender input is outside release boundary | Name unsupported fact and stop |
| `STD_DEFINITION_INVALID` | Compiler finds an unknown/orphaned rule or mapping | Block publication and name stable identity |
| `STD_CONCERN_INVALID` | Concern fails bounded validation | Preserve entered values and identify correction |

Do not expose filesystem paths, stack traces or private asset URLs.

## 13. Audit and observability

Audit successful and failed installation, lifecycle transition, site switch (**Switched On** or **Switched Off**), preview/download, concern creation/resolution, compatibility decision, compilation and rendering. Record actor/service identity, time, release, Tender/publication where applicable, result and correlation ID. Never log supplier secrets or full Bid responses.

Operational metrics include installation failures, integrity failures, unavailable adapter, compiler failure by code, concern ageing and affected unpublished Tenders after withdrawal.

## 14. Migration and deployment

1. create registry, asset and concern schema;
2. register compiler and renderer adapters;
3. package the exact 1.1 release pack once its validator run is clean, carrying its gate results and any owner decision as evidence (owner decision OD5) (v1.0 read: package the exact approved 1.1 release only after its gates and owner decision pass);
4. run install in staging and reproduce canonical documents/definition;
5. deploy records and assets transactionally;
6. enable **STD Templates** navigation and permissions;
7. enable Tender binding only after registry health checks pass; and
8. preserve the older `/07_tender_templates` artefacts as curation evidence, not mutable runtime configuration.

Existing Tender records cannot be backfilled with a guessed release. A migration must prove their exact template identity and digests or mark them legacy/read-only outside the new publication path.

## 15. Acceptance contract

| ID | Acceptance criterion |
|---|---|
| STI10-AC-001 | Installation fails closed unless every asset, digest, gate record, adapter and, when the package carries one, owner decision matches; an intact release installs as `Available`, switched On or, when the deployment asks, Off, and never as a `Candidate` (owner decision OD5) (v1.0 read: every asset, digest, gate, adapter and exact owner decision matches). |
| STI10-AC-002 | A failed installation exposes no partial/selectable release: it installs nothing, so no `Candidate`, switched-off or partial record remains (owner decision OD5). |
| STI10-AC-003 | Installed assets and content identities are immutable and private. |
| STI10-AC-004 | No editable clause, field, response, evaluation or contract-mapping DocType is introduced. |
| STI10-AC-005 | List/detail/coverage/change projections satisfy STD-TPL-001 v0.10 §11 without browser reconstruction. |
| STI10-AC-006 | Administrator, System Manager, Procurement Officer and HOPF have the prescribed read/concern access and no template-edit privilege. |
| STI10-AC-007 | Concern creation has no automatic lifecycle or Tender effect. |
| STI10-AC-008 | Fixture and production adapters return identical canonical Published Bid Definition output for every approved vector. |
| STI10-AC-009 | An unknown control, mapping, input or adapter produces a typed failure and no fallback. |
| STI10-AC-010 | New binding uses only Available releases that are switched On (owner decision OD5), after compatibility checks. |
| STI10-AC-011 | Superseded allows only integrity-checked continuation of already-bound unpublished Tenders. |
| STI10-AC-012 | Withdrawn blocks new binding and publication/Bid start for already-bound unpublished Tenders without changing published records. |
| STI10-AC-013 | No lifecycle event automatically rebinds a Tender. |
| STI10-AC-014 | Installation requires no owner approval and creates no site-adoption approval; an owner decision carried by the package must name the exact release, bundle and manifest and is recorded as evidence only (owner decision OD5) (v1.0 read: Installation verifies the one exact-manifest approval and creates no duplicate site-adoption approval). |
| STI10-AC-015 | Renderer engine/version changes require a new adapter identity and complete regression evidence. |
| STI10-AC-016 | The implementation passes desktop, keyboard, 200% zoom and 390 px requirements in KT-STD-001 v1.8. |
| STI11-AC-001 | The site switch changes only through the audited deployment command, only while the release is `Available`, and records who switched it and when; no Desk or browser route switches a release. |
| STI11-AC-002 | Switching a release Off blocks new Tender binding only; a Tender already bound to it continues while integrity and renderer checks pass, and no switch rebinds a Tender. |
| STI11-AC-003 | New binding is refused while more than one release of the same template key is switched On. |
| STI11-AC-004 | **STD Templates** projects `Available` only for a release that is `Available`, switched On, integrity-verified and renderer-registered; recorded gate results and any owner decision are shown as evidence and never block use. |

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
- Available (switched On and switched Off), Superseded and Withdrawn binding/publication matrices;
- affected-Tender projection and historical published readability;
- install without an owner decision (`Available`, switched On), install with `Off` requested, and a reinstall that leaves the switch unchanged;
- an owner decision naming a different release, bundle or manifest fails closed;
- the site switch through the deployment command only, only while `Available`, with its audit event;
- new binding refused while more than one release of a template key is switched On;
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

The site switch (owner decision OD5) belongs to step 2 (installation sets it) and step 8 (`SwitchSTDRelease`).

Do not build the UI first against invented placeholder data. The projections and closed fixtures are the UI source.

## 18. Traceability

| Requirement owner | This implementation supplies |
|---|---|
| STD-TPL-001 v0.10 | Installation, inspection, compiler, renderer and lifecycle implementation |
| TPR-CHG-001 v0.11 | Available-only new binding; bound-release checks; Withdrawn failure; immutable exact identity |
| BDS-CHG-001 v0.7 | Exact Published Bid Definition and renderer compatibility; no PDF parsing |
| AUTH-ADR-001 v1.10 | Module-specific inspection/concern permissions without responsibility mutation |
| KT-STD-001 v1.8 | Artboard, accessibility and verification quality |
| Owner decision OD5 (Project Owner, 26 September 2026) | Per-site On/Off switch; installation with no `Candidate` state and no required owner approval; switched-on-only new binding |

## 19. Approval effect

### 19.1 v1.1 approval effect

Approval makes v1.1 the implementation authority for the installed STD template runtime and retires v1.0, which was never approved, and v0.2 from active use. It applies owner decision OD5: an intact installed release is `Available` and switched On unless a deployment switches it Off, and neither installation nor use requires an exact-manifest owner decision. It does not approve release 1.1 content. STD-TPL-001 v0.10 and the other documents named in §21 still need the corrections listed there.

### 19.2 v1.0 approval effect (retained)

Approval makes v1.0 the implementation authority for the installed STD template runtime and retires v0.2 from active use. It does not approve release 1.1 content or make that candidate Available. The exact bundle must still pass STD-TPL-001 v0.10 and receive its exact-manifest owner decision.

v1.0 was never approved, so this effect never applied. Owner decision OD5 (§19.1) removed the exact-manifest owner decision it describes.

## 20. v1.1 change register

All v1.1 changes apply owner decision OD5. No other concern is changed.

| ID | v1.0 position | v1.1 correction | Verification |
|---|---|---|---|
| STI11-CHG-001 | §1 and §5.1 required an owner-approved release pack; §5.2 step 4, §5.3 and STI10-AC-014 verified an exact-manifest owner approval; §4.1 made the owner decision required for Available. | Installation needs no approval. An owner decision the package carries must still name the exact release, bundle and manifest, and is recorded as evidence only. | STI10-AC-001; STI10-AC-014 |
| STI11-CHG-002 | §4.1 and §9 defined a `Candidate` lifecycle state. | No `Candidate` state: an intact release installs as `Available` and any integrity failure installs nothing. The §9 Candidate row is retained as history. | STI10-AC-001; STI10-AC-002 |
| STI11-CHG-003 | No per-site control over an installed release. | Add `site_switch`, `switched_by` and `switched_at`, `SwitchSTDRelease`, the §10 switch permission row and the `make std-release-switch` deployment command, audited as **Switched On** or **Switched Off**. | STI11-AC-001 |
| STI11-CHG-004 | §9 had one Available row. | Split it into Available switched On (new binding permitted for the one switched-on release of the template key) and Available switched Off (new binding prohibited; already-bound Tenders continue). | STI10-AC-010; STI11-AC-002; STI11-AC-003 |
| STI11-CHG-005 | §5.2 step 6 and `STD_RELEASE_GATE_INCOMPLETE` blocked installation on a `Pending` or `Failed` gate. | The gate record must list every mandatory gate and the validator must report no Blocking failure; gate results are evidence. | STI10-AC-001; STI11-AC-004 |
| STI11-CHG-006 | **STD Templates** availability rested on STD-TPL-001 v0.10 §14.1, where a `Candidate` or a missing owner decision projects `Unavailable`. | Derive the availability projection from lifecycle, site switch, integrity and renderer; show the site switch in **Verification** instead of **Owner approval**. | STI11-AC-004 |

## 21. Required corrections in other documents

Each correction below is required so that the named document states owner decision OD5. The sections of TPR-CHG-001, REQ-CHG-001, BDS-CHG-001 and G1-REG-001 are those named by follow-up FU-01 in `STD-TPL-IMP-001_v1_0_FOLLOW_UPS.md`; their text was not reread for this revision.

| Document and section | Required correction |
|---|---|
| STD-TPL-001 v0.10 §3 | The **STD Templates** layer's "Must not do" includes "activate". State that the per-site switch is a deployment command outside the read-only surface. |
| STD-TPL-001 v0.10 §§11.2–11.4 | Replace the **Owner approval** verification row with the site switch (On or Off, who switched it and when); show any recorded owner decision only under **Technical details**; restate the installed-empty text, the Unavailable consequence and the "Unavailable / Candidate" variant without approval or `Candidate`. |
| STD-TPL-001 v0.10 §11.5 | Restate the closed fixture's status, verification, blockers and change-report classification without owner approval. |
| STD-TPL-001 v0.10 §11.6 | Restate how a release becomes Available: installed intact and switched On, with no exact-manifest owner decision. |
| STD-TPL-001 v0.10 §13.9 | State that the constructed manifest `status` value `Candidate` is evidence only (the build still writes it), or drop or rename the field in a later format change. |
| STD-TPL-001 v0.10 §13.9 | Replace the change-report result `Breaking — new release approval required` with the built wording `Breaking — not interchangeable with the preceding release`. |
| STD-TPL-001 v0.10 §§13.10–13.11 | Keep the reviews and any owner decision as recorded evidence; remove Gate E's exact-manifest approval as a condition of installation or use. |
| STD-TPL-001 v0.10 §14.1 | Remove `Candidate` from the lifecycle; derive the availability projection from lifecycle, site switch, integrity and renderer; describe Available switched On and switched Off. |
| STD-TPL-001 v0.10 §14.2 | State that gate results are recorded evidence and do not decide use; the validator's Blocking failures still stop installation. |
| STD-TPL-001 v0.10 §15 | Restate TPL07-AC-015, TPL08-AC-013, TPL08-AC-022, TPL10-AC-003 and TPL10-AC-009 for owner decision OD5. |
| STD-TPL-001 v0.10 §16 | Restate prohibitions 8 and 15 so that the per-site switch and installation without an owner decision are permitted. |
| STD-TPL-001 v0.10 §19 | Restate the approval effect: release 1.1 is usable on a site when installed intact and switched On. |
| TPR-CHG-001 v0.11 §§5.1, 5.3, 7 and 15.4 | Make new binding require the switched-On Available release instead of any Available release; state that switching Off never stops a Tender already bound. |
| REQ-CHG-001 v1.12 §5A | In the designation row, replace "exact Available release" with the installed, intact, switched-on release. |
| BDS-CHG-001 v0.7 §4.4.4 | Restate the release condition in step 8 for owner decision OD5. |
| BDS-CHG-001 v0.7 BDS05-AC-001 | Restate the release condition for owner decision OD5. |
| G1-REG-001 v1.1 §4 | Remove exact-manifest approval from step 2. |
| G1-REG-001 v1.1 §5 | Remove exact-manifest approval from the checklist. |
