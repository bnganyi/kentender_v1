# G1 Phase 4 / 4A — Content-Addressed Resources and NSSF Materialization

| Field | Value |
|---|---|
| Status | **Complete — Phase 4 + 4A hardening** (not Phase 5 publication) |
| Scope | Oracle recovery; CAS; immutable Manifest Resources; finalize new Compile Artifact; ownership/uniqueness/atomic package/verifier/CAS protection |
| Site | `kentender.midas.com` |
| Date | 2026-07-24 |

## Goal

Materialize Phase 3 logical resource candidates into immutable content-addressed `BWMF Manifest Resource` rows, bind them to a **new** finalized Compile Artifact with verified descriptors and a newly calculated payload digest, and recover NSSF resource digests via controlled oracle correction from frozen canonical item arrays — without creating or publishing `BWMF Manifest Version` (Phase 5).

Phase 4A hardens ownership, uniqueness, atomic finalize packaging, CAS protection, verifier negatives, chunk contract, clean-reseed determinism, and idempotency.

---

## Revised ownership model

| Concern | Owner | Notes |
|---|---|---|
| Physical canonical bytes | `BWMF Content Object` | Unique `content_ref` + unique `physical_digest`; private File internal only |
| Logical resource descriptor/content | `BWMF Manifest Resource` | **No** `manifest_version` field (removed completely) |
| Finalized Compile Artifact ↔ exact resource version | `BWMF Artifact Resource Binding` | Unique `(compile_artifact, resource_id)` |
| Published Manifest Version ↔ exact resource version | Phase 5 `BWMF Manifest Resource Binding` | **Not created** |
| Materialization audit | `BWMF Materialization Report` | References **preview** artifact + exact preview payload digest; success links finalized artifact |

```
Preview Compile Artifact (immutable input)
  → validate all candidates
  → CAS put + Manifest Resource create/reuse (idempotent)
  → re-verify all resources
  → pure finalize recompile
  → savepoint transaction:
        Finalized Compile Artifact
      + Artifact Resource Bindings (finalized only)
      + Succeeded Materialization Report
```

Preview artifacts never receive resource bindings.

---

## Exact uniqueness / indexes

| DocType | Unique | Non-unique indexes |
|---|---|---|
| `BWMF Content Object` | `content_ref`; `physical_digest` | — |
| `BWMF Manifest Resource` | `resource_version_key` = SHA-256(`resource_id‖digest‖schema_ref‖schema_version`) | `resource_id`, `resource_digest`, `resource_type`, `schema_ref`, `schema_version`, `content_ref` |
| `BWMF Artifact Resource Binding` | `binding_id`; `artifact_resource_key` = `compile_artifact‖resource_id` | `compile_artifact`, `resource_id`, `resource_digest` |

Permitted:

- same Content Object reused by multiple Manifest Resources;
- same `resource_id` with a new immutable digest in a later artifact;
- different resource IDs referencing identical content bytes.

---

## Transaction and partial-failure behavior

1. **Validate all candidates** before creating the finalized package.
2. CAS + Manifest Resources may be written before the package (idempotent; unreferenced CAS is removable via `clear_bwmf_phase4_materialization` / `clear_bwmf_canonical_fixture`).
3. **Re-verify** every resource before finalized-artifact creation.
4. Finalized artifact + all bindings + Succeeded report are created under MariaDB savepoint `bwmf_finalize_package`; any failure rolls the package back.

Injected failure during the **fifth** NSSF resource (`set_fail_during_resource_n(5)`) proves:

- no `finalized_materialized` Compile Artifact;
- no Artifact Resource Bindings;
- no Succeeded Materialization Report;
- no readiness-passing result;
- preview artifact unchanged;
- residual CAS cleaned by development reset.

---

## `content_ref` and CAS protection

| Contract | Value |
|---|---|
| Format | `bwmf-cas:v1:<sha256-hex-of-canonical-utf8-bytes>` |
| Path derivation | `private/files/bwmf-cas-<hex>.json` from digest only |
| Opacity | Rejects `http(s):`, `file:`, `/`, `\` paths as `content_ref` |
| Adapter-only resolution | `get_verified` / `put_canonical_json` / `delete_content_via_repository` |
| Replace | Forbidden while referenced (`BWMF_CAS_REFERENCED` / immutability) |
| Delete | Content Object `on_trash` + File `doc_events.on_trash` → `assert_content_not_deletable` |
| Missing / changed bytes | `BWMF_CAS_MISSING` / `BWMF_CAS_CORRUPT` |

NSSF resources use ordinary `content_addressed`. Chunking (`bwmf-chunk-v1`) is synthetic-only.

---

## Verifier diagnostic / test matrix

| Diagnostic code | Named test |
|---|---|
| `BWMF_RESOURCE_COUNT` | `test_wrong_item_count` |
| `BWMF_RESOURCE_SCHEMA` (unknown schema) | `test_unknown_schema` |
| `BWMF_RESOURCE_SCHEMA` (wrong version) | `test_wrong_schema_version` |
| `BWMF_RESOURCE_SCHEMA` (unknown property) | `test_unknown_item_property` |
| `BWMF_RESOURCE_SCHEMA` (missing property) | `test_missing_required_item_property` |
| `BWMF_RESOURCE_DUP_ID` | `test_duplicate_logical_item_id` |
| `BWMF_RESOURCE_ORDER` (reordered) | `test_reordered_logical_items` |
| `BWMF_RESOURCE_ORDER` (unreconstructable) | `test_unreconstructable_ordering_contract` |
| `BWMF_RESOURCE_DIGEST` | `test_logical_resource_digest_mismatch` |
| `BWMF_CAS_CORRUPT` (physical) | `test_physical_object_digest_mismatch` |
| `BWMF_CAS_REF` / missing ref | `test_incorrect_deterministic_content_ref` |
| `BWMF_RESOURCE_LINEAGE` | `test_missing_source_lineage` |
| `BWMF_DESCRIPTOR_SET` | `test_descriptor_set_digest_mismatch` |
| `BWMF_SECTION_RESOURCE` | `test_section_referencing_absent_resource` |
| `BWMF_CANDIDATE_ABSENT` | `test_resource_candidate_absent_from_preview` |
| `BWMF_MATERIALIZE_INPUT` (failed_result) | `test_failed_result_rejected` |

Chunk negatives (synthetic): missing / duplicate / reordered / overlapping ranges / corrupt bytes / incorrect `byte_size` / aggregate digest independent of concatenation — `test_chunking_synthetic_full_contract`.

---

## End-to-end clean-reseed proof

`test_clean_reseed_determinism`:

1. Compile a fixed preview artifact.
2. Materialize → snapshot digests/bytes.
3. `clear_bwmf_phase4_materialization(keep_preview_artifacts=True)` (Phase 4 rows + CAS files).
4. Materialize the **same** preview again.

Both runs produce identical:

- frozen resource bytes;
- logical resource digests;
- physical object digests;
- `content_ref`s;
- ordered descriptor-set digest;
- finalized payload canonical bytes;
- finalized payload digest.

DB names, File names, timestamps, and insertion order may differ and do not enter the payload.

---

## Idempotency

| Case | Result |
|---|---|
| Same key + same fingerprint | Same finalized artifact / report |
| Same key + different fingerprint | `BWMF_IDEMPOTENCY_FINGERPRINT_MISMATCH` |
| Different key + same inputs | New finalized artifact; reuses immutable resources/content objects |
| Contended same key | One Succeeded report (`GET_LOCK` in `resolve_idempotency`) |

---

## Complete NSSF resource registry (expected = actual)

Verification result for all nine after successful materialization: **pass**.  
Finalized-artifact binding ref pattern: `BIND-ART-FINAL-<preview_artifact_id>-<RESOURCE-ID>`.

| resource_id | resource_type | schema_ref / version | ordering_contract | expected count | actual count | expected logical digest | actual logical digest | physical object digest | content_ref | verification | binding ref pattern |
|---|---|---|---|---:|---:|---|---|---|---|---|---|
| RESOURCE-NSSF-REQUIREMENT-GROUPS | requirement_group | bwmf/item/requirement_group / 1.0.0 | ["order_weight","group_key"] | 23 | 23 | sha256:7c8725822187749999b76d04fb843038f1139e2ee249ead40cfffb175d11c78d | sha256:7c8725822187749999b76d04fb843038f1139e2ee249ead40cfffb175d11c78d | sha256:7c8725822187749999b76d04fb843038f1139e2ee249ead40cfffb175d11c78d | bwmf-cas:v1:7c8725822187749999b76d04fb843038f1139e2ee249ead40cfffb175d11c78d | pass | BIND-ART-FINAL-…-RESOURCE-NSSF-REQUIREMENT-GROUPS |
| RESOURCE-NSSF-REQUIREMENTS | requirement | bwmf/item/requirement / 1.0.0 | ["order_weight","requirement_key"] | 190 | 190 | sha256:12e64fd25709a935231213071a0e9d04c8aa3094a38a2fb11a44155b17f3d697 | sha256:12e64fd25709a935231213071a0e9d04c8aa3094a38a2fb11a44155b17f3d697 | sha256:12e64fd25709a935231213071a0e9d04c8aa3094a38a2fb11a44155b17f3d697 | bwmf-cas:v1:12e64fd25709a935231213071a0e9d04c8aa3094a38a2fb11a44155b17f3d697 | pass | BIND-ART-FINAL-…-RESOURCE-NSSF-REQUIREMENTS |
| RESOURCE-NSSF-PRELIMINARY-CRITERIA | preliminary_criterion | bwmf/item/preliminary_criterion / 1.0.0 | ["order_weight","criterion_key"] | 9 | 9 | sha256:0ab46d93f32e88876704b39526124a3c9b68f0e1d453e48ac3fa6d7b7e5edebb | sha256:0ab46d93f32e88876704b39526124a3c9b68f0e1d453e48ac3fa6d7b7e5edebb | sha256:0ab46d93f32e88876704b39526124a3c9b68f0e1d453e48ac3fa6d7b7e5edebb | bwmf-cas:v1:0ab46d93f32e88876704b39526124a3c9b68f0e1d453e48ac3fa6d7b7e5edebb | pass | BIND-ART-FINAL-…-RESOURCE-NSSF-PRELIMINARY-CRITERIA |
| RESOURCE-NSSF-QUALIFICATION-CRITERIA | qualification_criterion | bwmf/item/qualification_criterion / 1.0.0 | ["order_weight","criterion_key"] | 9 | 9 | sha256:54cf1d2458bde735721f7c3e23444df553efdae3c48d524a05bffef9131ff827 | sha256:54cf1d2458bde735721f7c3e23444df553efdae3c48d524a05bffef9131ff827 | sha256:54cf1d2458bde735721f7c3e23444df553efdae3c48d524a05bffef9131ff827 | bwmf-cas:v1:54cf1d2458bde735721f7c3e23444df553efdae3c48d524a05bffef9131ff827 | pass | BIND-ART-FINAL-…-RESOURCE-NSSF-QUALIFICATION-CRITERIA |
| RESOURCE-NSSF-TECHNICAL-SCORING | evaluation_criterion | bwmf/item/evaluation_criterion / 1.0.0 | ["order_weight","criterion_key"] | 7 | 7 | sha256:2207ad23244b116cb97015c34c064234287d81fd3157e93dc7b896e14fb72030 | sha256:2207ad23244b116cb97015c34c064234287d81fd3157e93dc7b896e14fb72030 | sha256:2207ad23244b116cb97015c34c064234287d81fd3157e93dc7b896e14fb72030 | bwmf-cas:v1:2207ad23244b116cb97015c34c064234287d81fd3157e93dc7b896e14fb72030 | pass | BIND-ART-FINAL-…-RESOURCE-NSSF-TECHNICAL-SCORING |
| RESOURCE-NSSF-SCHEDULE | implementation_schedule_row | bwmf/item/implementation_schedule_row / 1.0.0 | ["order_weight","row_key"] | 6 | 6 | sha256:c33f7eb213e689e2b30ae89d329216373d5b24ac639fa46b926d4fd2a7d64ef8 | sha256:c33f7eb213e689e2b30ae89d329216373d5b24ac639fa46b926d4fd2a7d64ef8 | sha256:c33f7eb213e689e2b30ae89d329216373d5b24ac639fa46b926d4fd2a7d64ef8 | bwmf-cas:v1:c33f7eb213e689e2b30ae89d329216373d5b24ac639fa46b926d4fd2a7d64ef8 | pass | BIND-ART-FINAL-…-RESOURCE-NSSF-SCHEDULE |
| RESOURCE-NSSF-PRICE-LINES | price_line | bwmf/item/price_line / 1.0.0 | ["order_weight","line_key"] | 22 | 22 | sha256:895d1c94c3446b07f8a5c4b72e68540e91e5e4a5d13a7126683b9547fff1db2e | sha256:895d1c94c3446b07f8a5c4b72e68540e91e5e4a5d13a7126683b9547fff1db2e | sha256:895d1c94c3446b07f8a5c4b72e68540e91e5e4a5d13a7126683b9547fff1db2e | bwmf-cas:v1:895d1c94c3446b07f8a5c4b72e68540e91e5e4a5d13a7126683b9547fff1db2e | pass | BIND-ART-FINAL-…-RESOURCE-NSSF-PRICE-LINES |
| RESOURCE-NSSF-CONTRACT-CONDITIONS | contract_condition | bwmf/item/contract_condition / 1.0.0 | ["order_weight","condition_key"] | 8 | 8 | sha256:8b90a193c27ef0d6b5d740980630094064e9571fadd160c3bc2b9426f4f9ca94 | sha256:8b90a193c27ef0d6b5d740980630094064e9571fadd160c3bc2b9426f4f9ca94 | sha256:8b90a193c27ef0d6b5d740980630094064e9571fadd160c3bc2b9426f4f9ca94 | bwmf-cas:v1:8b90a193c27ef0d6b5d740980630094064e9571fadd160c3bc2b9426f4f9ca94 | pass | BIND-ART-FINAL-…-RESOURCE-NSSF-CONTRACT-CONDITIONS |
| RESOURCE-NSSF-DECISIONS | controlled_decision | bwmf/item/controlled_decision / 1.0.0 | ["order_weight","decision_id"] | 8 | 8 | sha256:fa677d4b40b1934c8c50a9817733a7c4183d641f1ff3d957ce1e190d5381c5ef | sha256:fa677d4b40b1934c8c50a9817733a7c4183d641f1ff3d957ce1e190d5381c5ef | sha256:fa677d4b40b1934c8c50a9817733a7c4183d641f1ff3d957ce1e190d5381c5ef | bwmf-cas:v1:fa677d4b40b1934c8c50a9817733a7c4183d641f1ff3d957ce1e190d5381c5ef | pass | BIND-ART-FINAL-…-RESOURCE-NSSF-DECISIONS |

### Aggregate digests

| Digest | Value |
|---|---|
| Descriptor-set | `sha256:530792ace76ad691c168ab65c111f55a63a2e2d1929aa09ddf00d1d2e62bf6bd` |
| Projection | `sha256:9dac86f777ae8c89f5b02e29e82401e5f83e12966891f2337fc7cc98ee0f907d` |
| Preview payload (JCS) | `sha256:60184f6b419d60866a418d5971d369fd634c7d3211a995f616122c75fc264a7e` |
| Materialized calibration payload (JCS) | `sha256:5ed4eb04041f88e335d27acb20b1da8499ed8a46dfe23294ee57fbd27e22de4a` |
| Diagnostic (**unchanged**) | `sha256:b3bbc3f30456383236a9ea1b131fee9d6e62519a20e45484c987805260be84f7` |

Carry-forward / scoring: **117** contract carry-forward; max score **100** / qualification threshold **75**.

---

## Publication readiness (retained)

| Profile | `resource_readiness.passed` | `publication_readiness.passed` | Notes |
|---|---|---|---|
| NSSF calibration finalize | `true` | `false` | `calibration_only_not_publishable`; `final_runtime_manifest=false` |
| Approved synthetic publication finalize | `true` | `true` | Still **no** Manifest Version / publication record; `final_runtime_manifest=false` |

---

## Digest-oracle erratum

Full old→new 64-character values, per-resource schema/ordering/paths, and dependent digests:  
[`DIGEST_ORACLE_ERRATUM_NSSF_RESOURCES.md`](DIGEST_ORACLE_ERRATUM_NSSF_RESOURCES.md).

Active fixture oracles contain only recovered digests (`test_superseded_digests_absent_from_active_fixture_oracles`).

---

## Named tests and non-zero counts

| Module | Count | Result |
|---|---:|---|
| `test_bwmf_resource_oracle_phase4` | **6** | OK |
| `test_bwmf_resource_verifier_phase4a` | **15** | OK |
| `test_bwmf_materialize_phase4` | **12** | OK |

Materialize highlights: nine-resource NSSF materialization; dual-key reuse; fingerprint mismatch; concurrent/same-key single success; fifth-resource atomic failure; CAS protection suite; clean-reseed determinism; synthetic publication readiness; full chunk contract; immutability; same-bytes/different-identity.

---

## Gate evidence (2026-07-24)

| Gate | Counts | Result |
|---|---|---|
| `bw-manifest-phase1-gate` | 12 + 7 | OK |
| `bw-manifest-phase2-gate` | 7 + 19 + 15 + 6 | OK |
| `bw-manifest-phase3-gate` | 29 + 5 | OK |
| `bw-manifest-phase4-gate` | **6** + **15** + **12** | OK |
| `bw-a2-domain-gate` | 10 + 2 | OK |
| `nssf-calibration-gate` | 5 targeted | OK |

```bash
make -C apps/kentender_v1 bw-manifest-phase1-gate SITE=kentender.midas.com
make -C apps/kentender_v1 bw-manifest-phase2-gate SITE=kentender.midas.com
make -C apps/kentender_v1 bw-manifest-phase3-gate SITE=kentender.midas.com
make -C apps/kentender_v1 bw-manifest-phase4-gate SITE=kentender.midas.com
make -C apps/kentender_v1 bw-a2-domain-gate SITE=kentender.midas.com
make -C apps/kentender_v1 nssf-calibration-gate SITE=kentender.midas.com
```

---

## Explicit non-scope confirmation (Phase 5+ unimplemented)

Phase 4 / 4A did **not** implement:

- Approval / return workflow
- Atomic tender / manifest publication
- `BWMF Manifest Version` creation
- Phase 5 `BWMF Manifest Resource Binding`
- Checklist / bidder cutover / UI
- Response, evidence, confirmation, submission, seal, or receipt runtime
- Legacy migration or production-data preservation
