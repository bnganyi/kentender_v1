# PHASE 5 — Governance, Approval, and Atomic Publication

| Field | Value |
|---|---|
| Status | **Complete — Phase 5 governance + atomic publication** (not Phase 6 bidder cutover) |
| Site | `kentender.midas.com` |
| Date | 2026-07-24 |

## Goal

Implement the governed lifecycle from a finalized materialized Compile Artifact through review, approval/return, and **atomic publication** of an exact `BWMF Manifest Version`, binding tender publication version, immutable configuration/document package refs, approved artifact payload/digest, exact resources, approval decision, publication record, tender public state, and workspace **availability** — without creating bidder workspaces or cutting over the bidder UI (Phase 6).

## Documentation read gate

- Module pack: `apps/kentender_v1/docs/std-prod-impl/IT-STD-Wizard-v3/G1-IT-STD-Canonical-Config-Recovery/`
- Prior reports: Phase 0–4 (+ Phase 4 digest erratum / resource oracles)
- Precedence: Seed/Governance contracts in G1 directive §11 + Phase 5 prompt

## Phase 4 integrity preflight

1. **Structured composite keys** (`application/keys.py`):
   - `resource_version_key` = `sha256(JCS({algorithm_version, resource_id, resource_digest, schema_ref, schema_version}))` (bare hex)
   - Same pattern for `artifact_resource_key`, `manifest_resource_binding_key`
   - Controllers recalculate/verify; client mismatch → `BWMF_COMPOSITE_KEY`
2. **Phase 4 gates remain green** after key algorithm change (oracles + verifier + materialize).
3. **Phase 4 creates no Manifest Version / publication** (reconfirmed by Phase 4 + Phase 5 ineligible/NSSF tests).

---

## Exact files, DocTypes, migrations, indexes

### Application / persistence (new or materially extended)

| Path | Role |
|---|---|
| `.../application/keys.py` | JCS composite keys (Phase 4 preflight + Phase 5 bindings) |
| `.../application/roles.py` | Governance roles + SoD |
| `.../application/eligibility.py` | Server-derived review eligibility |
| `.../application/lifecycle_events.py` | Append-only lifecycle events |
| `.../application/review_service.py` | Prepare/submit review package; impact-plan approval |
| `.../application/approval_service.py` | Approve/return; immutable decisions; invalidation events |
| `.../application/publish_service.py` | Atomic publication + cancel + failure injection |
| `.../application/retrieval_service.py` | Exact verified published retrieval |
| `.../persistence/registry_doctypes.py` | New DT constants + CLEAR_ORDER + REQUIRED concepts |
| `.../persistence/guards.py` | Review/publication-request transitions; immutability |
| `.../fixtures/schema_coverage_ledger.json` | Phase 5 persistence concepts |
| `Makefile` | `bw-manifest-phase5-gate` |
| `.../tests/test_bwmf_governance_phase5.py` | Gate suite (12 tests) |

### DocTypes (migrated on `kentender.midas.com`)

| DocType | Purpose | Key uniqueness / indexes |
|---|---|---|
| `BWMF Review Package` | Immutable review package after submit | unique `package_id`, `review_package_digest`; state machine |
| `BWMF Approval Decision` | Immutable approve/return | unique `decision_id`; binds digests + warning acks |
| `BWMF Publication Request` | Publication attempt + idempotency metadata | unique `request_id`; state Requested→Succeeded\|Failed |
| `BWMF Manifest Resource Binding` | Published MV ↔ exact resource | unique `binding_id`, `binding_key` (= JCS key of MV+resource_id) |
| `BWMF Lifecycle Event` | Append-only governance/publication audit | unique `event_id`; indexed `event_type`, `organization` |
| `BWMF Tender Publication State` | Lineage lock + public/workspace availability | unique `lineage_key`; indexed `published_tender_ref` |
| `BWMF Manifest Publication` | Publication record | + `approval_decision`, `payload_digest`, `organization` (approval Link no longer required) |
| `BWMF Manifest Version` | Created **directly Published** at publication | unique `payload_digest`; uniqueness `(manifest_id, manifest_version)` enforced in service + lineage lock |

Migration: `bench --site kentender.midas.com migrate` (DocType sync; no production-data migration implemented).

---

## Governance state model

```
Prepared → SubmittedForApproval → Approved | Returned
```

Rules enforced in services + DocType guards:

- Compilation / validation do **not** submit or approve.
- Submit freezes package content (`immutable=1`); content fields cannot change.
- Returned packages cannot be resubmitted; correction requires a **new** finalized artifact + new review package.
- Approval does **not** publish.
- Decisions are immutable; stale usability is derived / recorded via lifecycle invalidation events (no rewrite to “invalid” on the decision row for publication failures — append-only `approval.invalidated_at_publication`).

---

## Role / permission / separation matrix

| Role | Prepare/preview | Submit | Final approve/return | Publish | Read history |
|---|---|---|---|---|---|
| `BWMF Tender Configurator` | yes | yes | no | no | limited |
| `BWMF Procurement Reviewer` | yes | yes (recommend/submit) | no | no | yes |
| `BWMF Tender Approver` | no edit | no | yes | no | yes |
| `BWMF Publication Service` | no | no | no | yes | yes |
| `BWMF Auditor` | no | no | no | no | yes (read) |

Server checks (`application/roles.py`):

- Authenticated actor required (`Guest` denied).
- Organization scope mismatch → `BWMF_ORG_SCOPE`.
- Unknown/missing role → `BWMF_ROLE_DENIED`.
- When separation enabled: submitter == approver → `BWMF_SOD_VIOLATION`.
- Administrator is treated as holding all governance roles in tests/dev only.

---

## Review-package and approval binding fields

### Review package (closed canonical JSON → `review_package_digest`)

Includes: package id/version, compile artifact + payload digest, target manifest id + proposed version, tender ref/version, configuration snapshot / document package / STD / catalogue / blueprint / submission-policy refs+digests, compiler/schema versions, validation report ref/digest, diagnostic digest, complete warning set, ordered resources (registry order) + descriptor-set digest, optional approved impact-plan ref/digest, submitting actor + server time.

### Approval decision binding

Binds at minimum: `review_package_digest`, artifact + payload digest, tender ref/version, config/doc/STD/catalogue/blueprint/policy digests, validation/diagnostic digests, warning acknowledgements, descriptor-set digest, approver + organization, decision, server time, comments/return reason.

Return requires non-empty `return_reason` and `correction_owner`.

---

## Warning-acknowledgement behavior

- Warnings appear in the review package with stable `code` + `fingerprint`.
- Approval requires an acknowledgement for **every** warning fingerprint.
- Unacknowledged → `BWMF_WARNING_UNACKED`.
- Acknowledgements store approver, `acknowledged_at`, optional comment.
- Warnings do not auto-block eligibility; they block **approval** until acked.

---

## Atomic transaction sequence and rollback evidence

Inside `publish_approved_package` → savepoint `bwmf_atomic_publish` + MySQL `GET_LOCK` on tender lineage:

1. Lock lineage (`BWMF Tender Publication State` `FOR UPDATE`)
2. Allocate next manifest version (first publication = 1; addendum = prior+1; previews consume none)
3. Insert `BWMF Manifest Version` directly in **Published** with **exact** approved payload bytes + digest
4. Insert immutable `BWMF Manifest Resource Binding` rows (unique per MV+resource_id)
5. Bind config/doc package digests via review package (no reinterpretation)
6. Create `BWMF Manifest Publication` + bind approval decision
7. Set tender `public_active` + `workspace_available` (flag only)
8. Emit `publication.succeeded` lifecycle/audit evidence
9. Commit / release savepoint

Envelope may add `publication.{approval_ref, published_at, ...}` **outside** the payload; payload digest unchanged.

**Rollback evidence** (`test_failed_publication_no_partial_and_no_version_consume`):

- Failure injection at `after_resource_bindings` → 0 MV rows for target, 0 resource bindings, 0 publications; retry allocates version **1**.
- Addendum failure at `after_manifest_version` leaves prior publication active and payload bytes unchanged.

---

## Exact published synthetic fixture (example gate run)

Resource digests are stable for the synthetic alpha fixture; `payload_digest` / `manifest_id` vary with `target_manifest_id`.

Example successful publication from this environment:

| Field | Value |
|---|---|
| `manifest_id` | `BWMF-SYN-P5-32b4bda0` |
| `manifest_version` | `1` |
| `payload_digest` | `sha256:109d8a4d8cc70b3a3b8662a8c0b1740998082c8601f6ff23ead09f59994b8bea` |
| `publication_id` | `PUB-REQ-RPT-32b4bda0` |
| `published_tender_ref` | `TENDER-P5-32b4bda0` |
| Descriptor-set (payload registry) | `sha256:2ddd6d47dff54a0136aea96cfae87f31fa5454ce5e4ebabd081098408a1be017` |

| order | resource_id | resource_digest |
|---:|---|---|
| 0 | `RESOURCE-SYN-REQUIREMENT_GROUPS` | `sha256:40f6ef257d1d9fd7a8a62d9c4dca558846e27ff85502921736f83a87c3564776` |
| 1 | `RESOURCE-SYN-REQUIREMENTS` | `sha256:4ad43b06350b080acaf608ddeeba26070b841f1df845f4a96d296c206e1c8f85` |
| 2 | `RESOURCE-SYN-PRELIMINARY_CRITERIA` | `sha256:9517feab94dc3153b4a3a638f8648e6777e81ccbdaea0e2039ad6df16e62156c` |
| 3 | `RESOURCE-SYN-QUALIFICATION_CRITERIA` | `sha256:beadc1143d8d675ac7d9be8610673feac0583dafb524806b59007fee835540a8` |
| 4 | `RESOURCE-SYN-TECHNICAL_SCORING` | `sha256:305cd16b591420f4fbb87835bacf58c58d5114844e7faf7e269d58426d28bda6` |
| 5 | `RESOURCE-SYN-SCHEDULE_ROWS` | `sha256:b867e1eeef9423d47d7d05a8cbab9f605bd8bc521ca694b2e5634158467546dc` |
| 6 | `RESOURCE-SYN-PRICE_LINES` | `sha256:72ef3a822e1f6d9cea97db526424c4811bd8fb12096ec6d0d1cd5edf3261c7cc` |
| 7 | `RESOURCE-SYN-CONTRACT_CONDITIONS` | `sha256:3c50bde02fbebd534746a8261377e847fe6377dfec630a5e91e5bcb05cbe0097` |
| 8 | `RESOURCE-SYN-DECISIONS` | `sha256:ac5b09ea903812450c4762b47882911f3db01754ca969eea6da2e88e63b3f5bf` |

Content refs are `bwmf-cas:v1:<hex>` matching the resource digest hex (logical == physical for these CAS JSON objects).

---

## Addendum and cancellation evidence

Covered by `test_addendum_and_cancellation`:

- Impact plan must be **Approved** before inclusion in review package.
- Failed addendum publish leaves prior MV `Published`, payload unchanged, lineage still active.
- Successful addendum → next version = prior+1; prior → `Superseded` without payload mutation.
- Cancellation → lifecycle `Cancelled` / `public_active=0`; payload digest and history retained.

NSSF calibration finalized artifacts are rejected (`BWMF_CALIBRATION_NOT_PUBLISHABLE`).

---

## Named tests, commands, non-zero counts

| Gate | Module(s) | Count | Result |
|---|---|---:|---|
| `bw-manifest-phase1-gate` | schema conformance + NSSF errata | **12** + **7** | OK |
| `bw-manifest-phase2-gate` | schema preflight + persistence suites | **7** + **19** + **15** + **6** | OK (after ledger update) |
| `bw-manifest-phase3-gate` | compiler + compile service | **29** + **5** | OK |
| `bw-manifest-phase4-gate` | oracle + verifier + materialize | **6** + **15** + **12** | OK |
| `bw-manifest-phase5-gate` | `test_bwmf_governance_phase5` | **12** | OK |
| `bw-a2-domain-gate` | checklist API + web | **10** + **2** | OK |
| `nssf-calibration-gate` | CAL-NSSF 001/002/003/012/013 | **1** each (non-zero) | OK |

Commands:

```bash
make -C apps/kentender_v1 bw-manifest-phase1-gate SITE=kentender.midas.com
make -C apps/kentender_v1 bw-manifest-phase2-gate SITE=kentender.midas.com
make -C apps/kentender_v1 bw-manifest-phase3-gate SITE=kentender.midas.com
make -C apps/kentender_v1 bw-manifest-phase4-gate SITE=kentender.midas.com
make -C apps/kentender_v1 bw-manifest-phase5-gate SITE=kentender.midas.com
make -C apps/kentender_v1 bw-a2-domain-gate SITE=kentender.midas.com
make -C apps/kentender_v1 nssf-calibration-gate SITE=kentender.midas.com
```

Phase 5 test names:

- `test_ineligible_preview_and_calibration_rejected`
- `test_package_immutable_on_submit_and_return_rules`
- `test_self_approval_and_unacked_warning_rejected`
- `test_approval_does_not_publish`
- `test_atomic_publication_success_and_bindings`
- `test_failed_publication_no_partial_and_no_version_consume`
- `test_idempotent_replay_and_fingerprint_mismatch`
- `test_stale_approval_and_corrupt_resource_rejected`
- `test_addendum_and_cancellation`
- `test_roles_matrix_unknown_denied`
- `test_no_manifest_before_publication_and_lifecycle_events`
- `test_active_retrieval_exposes_exact_version`

---

## Explicit non-scope confirmation (Phase 6+ unimplemented)

Not implemented in Phase 5:

- Live bidder checklist / section rendering
- Bidder workspace creation or workspace↔manifest runtime binding cutover
- Response / evidence / completion / issues runtime
- Confirmation, submission, sealing, or receipt
- Legacy migration / production-data preservation
- Applying addendum impact plans to bidder workspaces

`retrieve_published_manifest` returns `bidder_workspace_cutover: false`. Publication sets `workspace_available` only as a canonical availability flag.
