# G1 Phase 3 / 3A / 3B — Deterministic BWMF Compiler Report

| Field | Value |
|---|---|
| Status | **Complete — Phase 3B final compiler integrity corrections** (not Phase 4+) |
| Scope | Pure C01–C22 compiler + Compile Artifact persistence; failed-result integrity; C21 published baseline |
| Site | `kentender.midas.com` |
| Date | 2026-07-24 |

## Goal

Ship a deterministic, STD-family-generic Bidder Workspace Manifest compiler that:

- binds each compile attempt to an immutable run-scoped **Compile Artifact**;
- packages **logical resource candidates** on the artifact only (never as canonical `BWMF Manifest Resource`);
- treats display-label changes as digest-affecting presentation (stable IDs + stable response contracts);
- accepts only **Published** (or **Superseded** for historical replay) manifests as C21 addendum baselines;
- represents failed compiles as `failed_result` artifacts with **no** synthetic payload digest;
- keeps Phase 4 materialization and Phase 5 Manifest Version publication out of scope.

---

## Corrected label / digest semantics (Phase 3B)

| Change type | Stable object IDs | `response_contract_digest` | `display_contract_digest` | `payload_digest` | C21 class |
|---|---|---|---|---|---|
| Display label / instruction only | Unchanged | Unchanged | **Changes** | **Changes** | `display_only` |
| Response meaning change | Unchanged (unless identity fields change) | **Changes** | may change | **Changes** | `response_contract_change` |
| NFC-equivalent Unicode (NFC vs NFD) | — | identical after NFC | identical after NFC | identical after NFC | — |

Implementation:

- `compiler/contracts.py` — splits response vs display material; digests via NFC+JCS.
- `compiler/nfc.py` + `jcs_sha256_digest` — NFC normalize before RFC 8785 JCS.
- Payload carries `object_contracts.{response,display}_contract_digest`.
- Removed obsolete `test_label_only_change_stable_digest` (incorrect “label-stable digest” semantics).

---

## Exact C21 baseline authority

Addendum modes compare against an exact **prior published manifest**, not a compile artifact digest alone.

| Accepted | Rejected |
|---|---|
| `lifecycle_state=Published` + `baseline_authority=published_manifest` (current baseline) | Preview compile artifacts (`baseline_authority=compile_artifact` / `artifact_kind=preview`) |
| `lifecycle_state=Superseded` + superseded/published authority (**historical replay only**) | Failed compile artifacts (`artifact_kind=failed_result`) |
| Immutable `retained_payload` + matching `manifest_ref` / version / `payload_digest` | Draft / unpublished / Failed / Queued / Running |
| Verified resource descriptors when supplied | Mismatched version or digest; mutable / unresolved baselines |

C21 still does **not** apply the impact plan to workspaces (`workspace_application=not_applied`).

---

## Failed-result representation

A failed compile may persist:

- compile run + stage traces;
- deterministic diagnostics + `diagnostic_digest`;
- safe partial coverage / source refs on the run/report;
- failure state.

It must **not** contain:

- fabricated / synthetic `payload_digest`;
- a manifest envelope presented as valid;
- publication readiness capable of passing;
- resource candidates presented as a complete manifest;
- a publication command.

`BWMF Compile Artifact` for failures:

| Field | Value |
|---|---|
| `artifact_kind` | `failed_result` |
| `payload_json` | null / empty |
| `payload_digest` | null / empty |
| `digest_label` | `failed_result` |
| `final_runtime_manifest` | `false` |
| `diagnostic_digest` | present |
| `eligible_for_approval` / `eligible_for_publication` | `false` |

`assert_compile_artifact_eligible_for_publication` / `assert_failed_result_not_submittable` fail closed on failed results.

---

## Phase 4 versus Phase 5 ownership

| Phase | May create | Must not |
|---|---|---|
| **Phase 3** (this report) | Compile Artifact (preview / failed_result); logical candidates on artifact | Manifest Version; Manifest Resource; publication |
| **Phase 4** | Immutable materialized resources; **new** finalized compile artifact/package; new final payload digest; publication-readiness **evidence** | Mutate preview artifacts; create or publish `BWMF Manifest Version` |
| **Phase 5** | `BWMF Manifest Version` via **atomic publication** from an approved, materialized, digest-bound compile artifact | — |

---

## Compile-artifact versus manifest-version ownership

| Concern | Owner | Notes |
|---|---|---|
| Compile attempt | `BWMF Compile Artifact` | Immutable; many previews may share target `(manifest_id, version)` |
| Published runtime identity | `BWMF Manifest Version` | Unique `(manifest_id, manifest_version)` — **Phase 5 only** |
| Logical candidates | Artifact JSON | Not `BWMF Manifest Resource` until Phase 4 materialization |

---

## Revised persistence flow

```
Compile Request → Compile Run Queued→Running
  → pure pipeline C01–C22
  → Success → Compile Artifact (preview/candidate kinds; payload + digests + candidates)
  → Failure → Compile Artifact (artifact_kind=failed_result; no payload / no payload_digest)
  → never BWMF Manifest Version
  → never BWMF Manifest Resource rows
  → never publish / mutate workspace
```

---

## Digest labels (preview ≠ final runtime)

| Digest | Value | Meaning |
|---|---|---|
| Projection oracle | `sha256:461ffc824759f767f01bdfa9be77b3280da8020267d4743cd5ca7f9fb03ffa22` | Unchanged |
| Diagnostic oracle | `sha256:b3bbc3f30456383236a9ea1b131fee9d6e62519a20e45484c987805260be84f7` | Unchanged |
| Historical Phase 3 JCS | `sha256:10bb527daabb811d8a1c7d98a5d812a4d47ab9039b6f6b14e64d6a64071423d7` | Relabelled **unmaterialized preview-payload** (not final runtime) |
| Phase 3A preview JCS | `sha256:a8fa4c68c382e7c4be7c50fb4f0b808c948e1edacb1fcb70c6a8ef5382684a63` | Pre–object-contracts preview |
| **Current Phase 3B NSSF preview JCS** | `sha256:627ddfcdc1934af6dfa5207880b03117655bc853c34b98a54b4d3946e79f121a` | `digest_label=unmaterialized_preview_payload`; includes `object_contracts`; `final_runtime_manifest=false` |

Phase 4 must compute a **new** digest after verified resource descriptors and immutable content references are included.

---

## NSSF oracle (complete — still green)

| Check | Expected | Result |
|---|---:|---|
| Content sections | 10 | OK |
| Requirement groups | 23 | OK |
| Requirements | 190 | OK |
| Contract carry-forward | 117 | OK |
| Preliminary / qualification / technical scoring | 9 / 9 / 7 | OK |
| Maximum score / qualification threshold | `"100"` / `"75"` | OK |
| Schedule / price / SCC / decisions | 6 / 22 / 8 / 8 | OK |
| Workflow gates | 3 | OK |
| Evidence + Issues; `NSSF-DEC-SEC-001` | bound | OK |
| Readiness | `passed=false` (preview) | OK |

---

## Named tests and non-zero counts

### `test_bwmf_compiler_phase3` — **29** OK

Includes (Phase 3B highlights):

| Test | Covers |
|---|---|
| `test_label_change_preserves_identity_but_changes_payload_digest` | Stable IDs; response digest stable; display + payload digests change |
| `test_label_change_classified_display_only` | C21 `display_only` |
| `test_nfc_equivalent_text_identical_canonical_digest` | NFC equivalence |
| `test_addendum_baseline_must_be_published` | Draft rejected |
| `test_preview_artifact_rejected_as_addendum_baseline` | Preview artifact rejected |
| `test_failed_artifact_rejected_as_addendum_baseline` | Failed artifact rejected |
| `test_all_compile_modes_c21` | All modes + digest mismatch + addendum publication materialization fail |
| `test_historical_replay_against_superseded_published_manifest` | Superseded baseline |
| `test_failed_compile_has_no_payload_or_synthetic_digest` | Failed-result shape |
| `test_publication_mode_fails_unmaterialized` | Publication → failed_result |
| `test_nssf_oracles_complete` | Full NSSF counts |
| `test_synthetic_std_profile` | Second STD family |
| RFC 8785 / Unicode / integer boundary tests | JCS integrity |

### `test_bwmf_compile_service_phase3` — **5** OK

| Test | Covers |
|---|---|
| `test_successful_compile_persists_artifact_not_manifest_version` | No Manifest Version |
| `test_two_preview_compiles_same_manifest_version` | Dual preview; immutability |
| `test_failed_compile_not_publication_ready` | No synthetic digest; not submittable; no MV/Resource rows |
| `test_compile_does_not_mutate_workspace_or_tender` | Isolation |
| `test_candidates_not_stored_as_canonical_resources` | Candidates ≠ Manifest Resource; no Manifest Version |

---

## Gate evidence (2026-07-24)

| Gate | Counts | Result |
|---|---|---|
| `bw-manifest-phase1-gate` | 12 + 7 | OK |
| `bw-manifest-phase2-gate` | 7 + 19 + 15 + 6 | OK |
| `bw-manifest-phase3-gate` | **29** + **5** | OK |
| `bw-a2-domain-gate` | 10 + 2 | OK |
| `nssf-calibration-gate` | 5 targeted | OK |

```bash
make -C apps/kentender_v1 bw-manifest-phase1-gate SITE=kentender.midas.com
make -C apps/kentender_v1 bw-manifest-phase2-gate SITE=kentender.midas.com
make -C apps/kentender_v1 bw-manifest-phase3-gate SITE=kentender.midas.com
make -C apps/kentender_v1 bw-a2-domain-gate SITE=kentender.midas.com
make -C apps/kentender_v1 nssf-calibration-gate SITE=kentender.midas.com
```

---

## Stage ownership (unchanged from 3A)

| Stage | Owns |
|---|---|
| C09 | Dynamic collections + resource candidates |
| C17 | Projections only |
| C18 | Identity/ordering + object contract digests |
| C21 | Addendum impact / N/A (published baseline authority) |
| C22 | Envelope packaging; failed_result vs preview |

---

## Explicit non-scope confirmation

Phase 3B did **not** implement Phase 4+ functionality:

- Content-addressed resource repository / chunk materialization
- Creation of immutable canonical `BWMF Manifest Resource` records
- Final runtime-manifest digest after materialization
- Approval workflow or atomic publication (`BWMF Manifest Version` — Phase 5)
- Live checklist cutover or bidder runtime UI
- Response, evidence, confirmation, submission, seal, or receipt runtime
- Legacy migration

---

## Next (hints only — not started)

- **Phase 4:** materialize verified resources into a **new** finalized compile artifact; compute new final payload digest; produce publication-readiness evidence — without creating Manifest Versions.
- **Phase 5:** atomic publication transaction creates the unique published `BWMF Manifest Version` from an approved, materialized, digest-bound artifact.
