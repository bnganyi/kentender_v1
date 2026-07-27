# Digest Oracle Erratum — NSSF Calibration Resources (Phase 4 / 4A)

| Field | Value |
|---|---|
| Status | Controlled calibration integrity correction |
| Date | 2026-07-24 |
| Nature | **Not** a change to procurement requirements |
| Reason | Original §7 SHA-256 preimages / field-projection contract were not retained; orphaned constants are not independently reproducible |

## Canonicalization algorithm

Unicode NFC normalization → object keys sorted → compact JSON separators (`","`, `":"`) → SHA-256  
Implemented as `pack_equivalent_digest` / `logical_resource_digest` (Crosswalk §7.1).  
Full Compile Artifact payload digests remain RFC 8785 JCS via `jcs_sha256_digest`.

## Authoritative preimages

Frozen under:

`kentender_procurement/.../bidder_workspace_manifest/fixtures/nssf_calibration/resources/<RESOURCE-ID>.json`

Active fixture oracles (`resource_digest_meta.json`, `source_set.json`, `golden_projection.json`) contain **only recovered (new) digests**. Superseded constants appear **only in this erratum** (and historical Crosswalk / Phase 0–3 narrative docs).

---

## Resource records (complete)

### RESOURCE-NSSF-REQUIREMENT-GROUPS

| Field | Value |
|---|---|
| Authoritative frozen-array path | `fixtures/nssf_calibration/resources/RESOURCE-NSSF-REQUIREMENT-GROUPS.json` |
| Resource type | `requirement_group` |
| Item schema ref / version | `bwmf/item/requirement_group` / `1.0.0` |
| Item count | 23 |
| Ordering contract | `["order_weight", "group_key"]` |
| Canonicalization algorithm | NFC + sorted-key compact JSON + SHA-256 |
| Old (orphaned) logical digest | `sha256:76cd5d03583c4c4d042215b212a3b14925284cc6dbf57a5b8486cb0d7d441793` |
| New (authoritative) logical digest | `sha256:7c8725822187749999b76d04fb843038f1139e2ee249ead40cfffb175d11c78d` |

### RESOURCE-NSSF-REQUIREMENTS

| Field | Value |
|---|---|
| Authoritative frozen-array path | `fixtures/nssf_calibration/resources/RESOURCE-NSSF-REQUIREMENTS.json` |
| Resource type | `requirement` |
| Item schema ref / version | `bwmf/item/requirement` / `1.0.0` |
| Item count | 190 |
| Ordering contract | `["order_weight", "requirement_key"]` |
| Canonicalization algorithm | NFC + sorted-key compact JSON + SHA-256 |
| Old (orphaned) logical digest | `sha256:15b374c220891b52bf75c7390e7f3f7dc680760355997f18217492b6831bf912` |
| New (authoritative) logical digest | `sha256:12e64fd25709a935231213071a0e9d04c8aa3094a38a2fb11a44155b17f3d697` |

### RESOURCE-NSSF-PRELIMINARY-CRITERIA

| Field | Value |
|---|---|
| Authoritative frozen-array path | `fixtures/nssf_calibration/resources/RESOURCE-NSSF-PRELIMINARY-CRITERIA.json` |
| Resource type | `preliminary_criterion` |
| Item schema ref / version | `bwmf/item/preliminary_criterion` / `1.0.0` |
| Item count | 9 |
| Ordering contract | `["order_weight", "criterion_key"]` |
| Canonicalization algorithm | NFC + sorted-key compact JSON + SHA-256 |
| Old (orphaned) logical digest | `sha256:364dbde57e09558c11ebcc443710855698eace1a8d828b6bfc9aa0e488832287` |
| New (authoritative) logical digest | `sha256:0ab46d93f32e88876704b39526124a3c9b68f0e1d453e48ac3fa6d7b7e5edebb` |

### RESOURCE-NSSF-QUALIFICATION-CRITERIA

| Field | Value |
|---|---|
| Authoritative frozen-array path | `fixtures/nssf_calibration/resources/RESOURCE-NSSF-QUALIFICATION-CRITERIA.json` |
| Resource type | `qualification_criterion` |
| Item schema ref / version | `bwmf/item/qualification_criterion` / `1.0.0` |
| Item count | 9 |
| Ordering contract | `["order_weight", "criterion_key"]` |
| Canonicalization algorithm | NFC + sorted-key compact JSON + SHA-256 |
| Old (orphaned) logical digest | `sha256:8db3f47c5cd31e4ffd690a29e98647b87a8cd3b20f71a5e784c587270a534d54` |
| New (authoritative) logical digest | `sha256:54cf1d2458bde735721f7c3e23444df553efdae3c48d524a05bffef9131ff827` |

### RESOURCE-NSSF-TECHNICAL-SCORING

| Field | Value |
|---|---|
| Authoritative frozen-array path | `fixtures/nssf_calibration/resources/RESOURCE-NSSF-TECHNICAL-SCORING.json` |
| Resource type | `evaluation_criterion` |
| Item schema ref / version | `bwmf/item/evaluation_criterion` / `1.0.0` |
| Item count | 7 |
| Ordering contract | `["order_weight", "criterion_key"]` |
| Canonicalization algorithm | NFC + sorted-key compact JSON + SHA-256 |
| Old (orphaned) logical digest | `sha256:0ae31ac169b3ac5a1103390f338d962caf34deef117bf063012ac02b1e82bb76` |
| New (authoritative) logical digest | `sha256:2207ad23244b116cb97015c34c064234287d81fd3157e93dc7b896e14fb72030` |

### RESOURCE-NSSF-SCHEDULE

| Field | Value |
|---|---|
| Authoritative frozen-array path | `fixtures/nssf_calibration/resources/RESOURCE-NSSF-SCHEDULE.json` |
| Resource type | `implementation_schedule_row` |
| Item schema ref / version | `bwmf/item/implementation_schedule_row` / `1.0.0` |
| Item count | 6 |
| Ordering contract | `["order_weight", "row_key"]` |
| Canonicalization algorithm | NFC + sorted-key compact JSON + SHA-256 |
| Old (orphaned) logical digest | `sha256:2497f21da32a79f51a1261b47b1f4135a43de126a9204a46a51daa881dfa86f4` |
| New (authoritative) logical digest | `sha256:c33f7eb213e689e2b30ae89d329216373d5b24ac639fa46b926d4fd2a7d64ef8` |

### RESOURCE-NSSF-PRICE-LINES

| Field | Value |
|---|---|
| Authoritative frozen-array path | `fixtures/nssf_calibration/resources/RESOURCE-NSSF-PRICE-LINES.json` |
| Resource type | `price_line` |
| Item schema ref / version | `bwmf/item/price_line` / `1.0.0` |
| Item count | 22 |
| Ordering contract | `["order_weight", "line_key"]` |
| Canonicalization algorithm | NFC + sorted-key compact JSON + SHA-256 |
| Old (orphaned) logical digest | `sha256:8e34505c57a85b40088df4db29727932c9e27d0aa4b9c5f5db70f9d1673bc2c2` |
| New (authoritative) logical digest | `sha256:895d1c94c3446b07f8a5c4b72e68540e91e5e4a5d13a7126683b9547fff1db2e` |

### RESOURCE-NSSF-CONTRACT-CONDITIONS

| Field | Value |
|---|---|
| Authoritative frozen-array path | `fixtures/nssf_calibration/resources/RESOURCE-NSSF-CONTRACT-CONDITIONS.json` |
| Resource type | `contract_condition` |
| Item schema ref / version | `bwmf/item/contract_condition` / `1.0.0` |
| Item count | 8 |
| Ordering contract | `["order_weight", "condition_key"]` |
| Canonicalization algorithm | NFC + sorted-key compact JSON + SHA-256 |
| Old (orphaned) logical digest | `sha256:bd8f8ac784de60a448a23662f568009c95f88f2c4d01fe375550bdd0d8e93b8f` |
| New (authoritative) logical digest | `sha256:8b90a193c27ef0d6b5d740980630094064e9571fadd160c3bc2b9426f4f9ca94` |

### RESOURCE-NSSF-DECISIONS

| Field | Value |
|---|---|
| Authoritative frozen-array path | `fixtures/nssf_calibration/resources/RESOURCE-NSSF-DECISIONS.json` |
| Resource type | `controlled_decision` |
| Item schema ref / version | `bwmf/item/controlled_decision` / `1.0.0` |
| Item count | 8 |
| Ordering contract | `["order_weight", "decision_id"]` |
| Canonicalization algorithm | NFC + sorted-key compact JSON + SHA-256 |
| Old (orphaned) logical digest | `sha256:7712b4ed457d9be988d4f27ebbcba1dea61372ca998db0a9fefaf3158ac4bc17` |
| New (authoritative) logical digest | `sha256:fa677d4b40b1934c8c50a9817733a7c4183d641f1ff3d957ce1e190d5381c5ef` |

---

## Dependent digests (full 64-character values)

| Digest | Old (orphaned / historical) | New (authoritative) | Notes |
|---|---|---|---|
| Ordered descriptor-set | `sha256:9532a6c363914f10f94af53a832d49e5899e72821cae9361a9608e49bbbf047c` | `sha256:530792ace76ad691c168ab65c111f55a63a2e2d1929aa09ddf00d1d2e62bf6bd` | Ordered resource digests |
| Golden projection payload | `sha256:461ffc824759f767f01bdfa9be77b3280da8020267d4743cd5ca7f9fb03ffa22` | `sha256:9dac86f777ae8c89f5b02e29e82401e5f83e12966891f2337fc7cc98ee0f907d` | `pack_equivalent_digest` |
| Phase 3 preview payload (JCS) | `sha256:627ddfcdc1934af6dfa5207880b03117655bc853c34b98a54b4d3946e79f121a` | `sha256:60184f6b419d60866a418d5971d369fd634c7d3211a995f616122c75fc264a7e` | `unmaterialized_preview_payload` |
| Phase 4 materialized calibration (JCS) | — (not previously defined) | `sha256:5ed4eb04041f88e335d27acb20b1da8499ed8a46dfe23294ee57fbd27e22de4a` | `materialized_calibration_payload` |
| Diagnostic set | `sha256:b3bbc3f30456383236a9ea1b131fee9d6e62519a20e45484c987805260be84f7` | `sha256:b3bbc3f30456383236a9ea1b131fee9d6e62519a20e45484c987805260be84f7` | **Unchanged** |

---

## Unaffected

Official IT STD, obligation catalogue, section blueprint, and legal-source digests are **not** changed.

## Affected tests / documents

- `test_bwmf_compiler_phase3.py` / `test_bwmf_compile_service_phase3.py` projection oracles
- `test_bwmf_resource_oracle_phase4.py` (`test_superseded_digests_absent_from_active_fixture_oracles`)
- `fixtures/nssf_calibration/{source_set,golden_projection,resource_digest_meta,resources}/`
- Crosswalk `04` §7 — superseded by this erratum for resource digests
- Phase 3 / Phase 4 reports

## Reproducibility

Reload only frozen arrays under `fixtures/nssf_calibration/resources/` and recompute via `resources.canonical`; digests must match exactly (gate: `test_nssf_resource_digest_reproducibility`).
