# G1 Phase 1 — Contract Schemas and Fixture Errata Report

| Item | Value |
|---|---|
| Phase | 1 — Contract schemas and fixture errata |
| Status | **Complete — ready for Phase 2** (entry conditions in §8) |
| Date | 2026-07-24 |
| Site | `kentender.midas.com` (dev; data disposable) |
| Manifest schema version | `1.0.0` |
| Compatibility boundary | `LEGACY_PACK10_BIDDER_SUBMISSION_SCHEMA_COMPATIBILITY_BOUNDARY` |

---

## 1. Outcome

Phase 1 delivered closed, versioned Bidder Workspace Manifest contract schemas with dual source-binding digests, NSSF fixture errata (10 content sections + `NSSF-DEC-SEC-001`), corrected BWMF-T049/T054 expectation tests, and a fixed `nssf-calibration-gate` that cannot false-green on zero matched tests.

Live checklist / `schema_compiler.SECTION_KEYS` were **not** switched. Pack-10 remains behind the named compatibility boundary until Phases 3 and 6.

---

## 2. Changed files

### Added — package

| Path |
|---|
| `kentender_procurement/.../tender_configurations/bidder_workspace_manifest/__init__.py` |
| `kentender_procurement/.../tender_configurations/bidder_workspace_manifest/compatibility.py` |
| `kentender_procurement/.../tender_configurations/bidder_workspace_manifest/digest.py` |
| `kentender_procurement/.../tender_configurations/bidder_workspace_manifest/registry.py` |
| `kentender_procurement/.../tender_configurations/bidder_workspace_manifest/validate.py` |
| `kentender_procurement/.../tender_configurations/bidder_workspace_manifest/nssf_fixture_errata.py` |
| `kentender_procurement/.../tender_configurations/bidder_workspace_manifest/schemas/v1/*.json` (20 files) |
| `kentender_procurement/.../tender_configurations/bidder_workspace_manifest/fixtures/examples/*.json` |
| `kentender_procurement/.../tender_configurations/bidder_workspace_manifest/fixtures/nssf_golden_section_expectation.json` |

### Added — tests / docs

| Path |
|---|
| `kentender_procurement/.../tender_configurations/tests/test_bwmf_schema_conformance_phase1.py` |
| `kentender_procurement/.../tender_configurations/tests/test_bwmf_nssf_fixture_errata_phase1.py` |
| `docs/std-prod-impl/IT-STD-Wizard-v3/G1-IT-STD-Canonical-Config-Recovery/PHASE_1_CONTRACT_SCHEMAS_AND_FIXTURE_ERRATA_REPORT.md` |

### Modified

| Path | Change |
|---|---|
| `apps/kentender_v1/Makefile` | `bw-manifest-phase1-gate`; `nssf-calibration-gate` short names + fail on zero matches |

### Not changed (intentional)

- `schema_compiler.py` / `SECTION_KEYS`
- Website A2/A4 checklist UI
- Electronic bid runtime / Desk PoC
- DocTypes / migrations
- E1 `10_NSSF_Electronic_Bidder_Submission_Schema.json` (negative fixture only)

---

## 3. Schema inventory

All under `bidder_workspace_manifest/schemas/v1/`; `schema_version` = `1.0.0`; closed (`additionalProperties: false`) unless noted.

| Schema id / file | Covers |
|---|---|
| `common_defs.json` | Identifier, Hash (`sha256:`), Datetime, SemanticVersion |
| `source_binding.json` | Binding + **`archive_provenance_digest`** + **`document_content_digest`** |
| `compile_request.json` | §35.1 compile request; nested closed input bindings with dual digests |
| `manifest_envelope.json` | Envelope: version, control, payload, integrity |
| `payload_core.json` | §12.1 payload top-level; `document_package` dual digests |
| `bindings.json` | §9.1 + `std_source_digest` (archive) |
| `section_group_task_field_collection.json` | Section / group / task / field / collection |
| `condition_calculation_ast.json` | Typed condition / calculation AST |
| `evidence.json` | Evidence + dual digests |
| `validation_diagnostic.json` | Validation / diagnostic records |
| `dependency_invalidation.json` | Dependencies + invalidation policies |
| `role_authority.json` | Role / permission / authority refs |
| `workflow_gates.json` | `review_and_validate` / `submit_and_seal` / `submission_receipt` |
| `resource_descriptor.json` | Resources + dual digests + `resource_digest` |
| `projections.json` | Opening / evaluation / contract |
| `addendum_diff_impact.json` | Addendum plan / impact |
| `response_instance.json` | Response instances |
| `confirmation.json` | Confirmations; **`accepted` required, no default** |
| `submission_receipt.json` | Submissions + receipts (`seal_integrity_digest`) |
| `migration_plan_run.json` | Migration plan/run/item/report (schema only) |

Validator: stdlib subset in `validate.py` (no `jsonschema` dependency).

---

## 4. Test commands, counts, durations

Recorded 2026-07-24 on `kentender.midas.com`.

| Command | Result | Tests | Duration |
|---|---|---:|---|
| `make -C apps/kentender_v1 bw-manifest-phase1-gate` | **OK** | 12 + 7 | ~6s wall |
| `… test_bwmf_schema_conformance_phase1` | **OK** | 12 | 0.004s |
| `… test_bwmf_nssf_fixture_errata_phase1` | **OK** | 7 | 0.011s |
| `make -C apps/kentender_v1 nssf-calibration-gate` | **OK** | 5 × 1 | ~47s wall |
| `make -C apps/kentender_v1 bw-a2-domain-gate` | **OK** | 10 + 2 | ~26s wall |

Zero-match proof: bogus `--test test_cal_nssf_DOES_NOT_EXIST` produces no `Ran N` / no `OK`; Makefile second check fails the gate.

---

## 5. Errata evidence

| Errata rule | Evidence |
|---|---|
| Exactly 10 content sections | `NSSF_CANONICAL_CONTENT_SECTION_KEYS`; `test_bwmf_t049_expects_ten_nssf_content_sections` |
| Tender Security via `NSSF-DEC-SEC-001` | Section key `tender_security`; `NSSF_SECURITY_DECISION_ID`; BWMF-T054 helper |
| Omit Lots & Alternatives | `NSSF_LOT_MODEL` single_scope / no selectable lots / no alternatives |
| Remove Contract Conditions Acknowledgement | Forbidden key `contract_terms_acknowledgement` |
| Remove Final Declaration as content | Forbidden key `final_declaration_and_submit` |
| Add Statutory Declarations | Key `statutory_declarations` in canonical list |
| BWMF-T049 corrected | Expects **ten**, rejects nine-without-security |
| BWMF-T054 corrected | Readiness passes only when `NSSF-DEC-SEC-001` bound |

Canonical keys (order):

1. `tender_documents_and_addenda`
2. `form_of_tender`
3. `confidential_business_questionnaire`
4. `statutory_declarations`
5. `tender_security`
6. `preliminary_requirements_and_evidence`
7. `qualification_and_capability`
8. `technical_proposal_and_implementation_plan`
9. `requirements_compliance`
10. `price_schedule`

---

## 6. Compatibility boundary

| Symbol | Value / meaning |
|---|---|
| Name | `LEGACY_PACK10_BIDDER_SUBMISSION_SCHEMA_COMPATIBILITY_BOUNDARY` |
| Module | `bidder_workspace_manifest/compatibility.py` |
| Pack-10 digest (negative) | `sha256:4d461f4901ef159578b441afd468125ce60b310d67575a81dc23d88ff4a6fa72` |
| Canonical? | `LEGACY_PACK10_IS_CANONICAL_RUNTIME_CONTRACT = False` |
| Still on pack-10 until P3/P6 | `schema_compiler.SECTION_KEYS`, Website A2/A4 checklist |

New G1 code must use schemas + `nssf_fixture_errata`, not pack-10 as contract.

---

## 7. What you will see / What changed

### What changed

- **Added:** `tender_configurations/bidder_workspace_manifest/` — closed v1 schemas, stdlib validator, dual-digest source bindings, `nssf_fixture_errata.py`, `LEGACY_PACK10_BIDDER_SUBMISSION_SCHEMA_COMPATIBILITY_BOUNDARY`.
- **Added:** Phase 1 conformance + errata tests and `make bw-manifest-phase1-gate`.
- **Fixed:** `make nssf-calibration-gate` — short `--test` names + fail when zero tests match.
- **Added:** this Phase 1 report beside Phase 0 / G1 pack docs.
- **Not changed:** `schema_compiler.SECTION_KEYS`, Website A2/A4 checklist UI, electronic bid runtime, DocTypes, migrations, compiler C01–C22.

### What you will see

1. New package tree under `tender_configurations/bidder_workspace_manifest/` with `schemas/v1/*.json` and validators.
2. Tests asserting **10** NSSF content sections including `tender_security` / `statutory_declarations`; forbidden legacy content keys absent; Lots omitted; `NSSF-DEC-SEC-001` readiness (BWMF-T049 / BWMF-T054 corrected).
3. Source-binding objects requiring both `archive_provenance_digest` and `document_content_digest`.
4. `nssf-calibration-gate` actually runs five CAL tests (not a silent 0-test pass).
5. Live `/tenders/<ref>/workspace` checklist **still** shows the old pack-10-shaped rows — intentional until Phase 6.

### What should NOT change

- Stitch HTML under `docs/bidder-workspace/A*/code.html`.
- Live `schema_compiler` / Website A2–A4 behavior and existing `ui-bidder-a*` / `bw-a*` gates (regression-only).
- No compiler stages, no persistence DocTypes, no legacy bid migration in this phase.
- Do not treat E1 `10_NSSF_Electronic_Bidder_Submission_Schema.json` as the canonical contract (negative fixture only).

### How to verify

```bash
make -C apps/kentender_v1 bw-manifest-phase1-gate SITE=kentender.midas.com
make -C apps/kentender_v1 nssf-calibration-gate SITE=kentender.midas.com
# Expect each CAL line: Ran 1 test … OK (five times); gate fails if no non-zero Ran
make -C apps/kentender_v1 bw-a2-domain-gate SITE=kentender.midas.com
test -f apps/kentender_v1/docs/std-prod-impl/IT-STD-Wizard-v3/G1-IT-STD-Canonical-Config-Recovery/PHASE_1_CONTRACT_SCHEMAS_AND_FIXTURE_ERRATA_REPORT.md && echo OK
```

### Cross-check against recovery intent

- Schemas encode the closed manifest contract without cutting over runtime authority.
- Fixture errata matches directive §4.3 (10 sections + SEC-001); BWMF-T049/T054 expectations corrected in code.
- Compatibility boundary explicitly names pack-10 as non-canonical until Phases 3 & 6.
- Calibration Makefile can no longer false-green on zero matches.
- Does **not** claim the bidder checklist UI is fixed or that legal archive digests are byte-verified.

---

## 8. Exact Phase 2 entry conditions

Phase 2 may start only when all are true:

1. Phase 1 schema + errata + BWMF-T049/T054 tests green via `bw-manifest-phase1-gate`. **Satisfied** (12+7 OK).
2. `nssf-calibration-gate` runs five tests (non-zero match) and is green. **Satisfied** (5×1 OK, ~47s).
3. No Phase 1 change altered live `schema_compiler.SECTION_KEYS` / Website checklist projection. **Satisfied** (`bw-a2-domain-gate` OK; compiler untouched).
4. Compatibility boundary module exists and documents pack-10 as non-canonical. **Satisfied**.
5. Legal archive digests may still mismatch on-disk PDFs (non-blocking for Phase 2 persistence); do not claim byte-verified archive provenance until resolved later. **Acknowledged** (Phase 0 §7.2).

Phase 2 scope (next): forward-only persistence/migrations for contract concepts (directive Phase 2), still without UI checklist cutover.
