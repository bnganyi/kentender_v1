# STD Engine — Import & API Wiring Plan

**Milestone:** 1 (read-only read model)  
**Tracker:** `BE_IMPLEMENTATION_TRACKER.md`  
**Decisions:** `docs/std-prod-impl/std backend answers.md`

## Goal

Define how the IT STD seed package, official source PDF, bench commands, HTTP import endpoints, and read APIs connect to the 22 static UI screens — without editing workflow or mutation.

## Import inputs

These are the only files Milestone 1 should treat as authoritative inputs. Older skeleton zips and NSSF fixture material may remain in the repository but must not be imported as the master STD.

| Input | Path | Role |
|---|---|---|
| Seed package (canonical) | `docs/std-prod-impl/data/KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip` | Structured JSON import |
| Official source PDF | `docs/std-prod-impl/data/DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.pdf` | **Must** register as `STD Source Document` with SHA-256, filename, page/anchor linkage |
| NSSF calibration PDF | `docs/std-prod-impl/data/NSSF SPS RFP ERP 2026.pdf` | Reference only — **not** imported as STD |

Zip-internal NSSF fixtures (`fixtures/nssf_erp/`) are skipped per `fixture_data_import_policy: DO_NOT_IMPORT_BY_DEFAULT`.

## Required package files for Milestone 1

| Classification | Files / folders | Import behavior |
|---|---|---|
| Required for any import | `manifest.json`, checksum manifest, package metadata | Dry-run fails if missing |
| Required for vertical slice | `source_documents*`, `source_trace*`, `sections*`, `clauses*` | Commit fails if missing or structurally invalid |
| Required for validation/audit visibility | validation metadata, smoke-test expectations where present | Missing items become validation findings, not silent defaults |
| Imported when present | parameters, rules, forms, form fields, requirements, price schedules, evaluation schema, render blocks | Needed for screens 07–16 after vertical slice |
| Skipped by default | `fixtures/nssf_erp/`, NSSF calibration PDF/data | Reference/calibration only; never master STD import |
| Deferred | second STD package for version diff | Screen 21 returns single-version stub until real second package exists |

## Import pipeline

```text
1. Read zip (manifest, checksums, nested JSON)
2. Resolve official PDF path (bench arg or default under data/)
3. Verify package structure + checksums
4. Dry-run: planned counts, missing files/anchors, blockers → Import Run record
5. Commit (DRAFT only): transactional persist + PDF registration + audit events
6. Post-import validation run → Validation Findings
```

**Rules:**

- Never silently invent missing legal content
- Commit target state is always **DRAFT** for v0.2
- Persist `activation_allowed=false` from the manifest and convert activation blockers into validation findings
- UI mode is `READ_ONLY_INSPECTION`; do not infer editability from `DRAFT`
- Idempotent only when `package_id + package_sha256` match
- Fail on same package ID with a different hash unless a future explicit replace-draft workflow exists
- Fail if any immutable `ACTIVE` version would be overwritten or mutated

## Import surfaces

### Bench / CLI (primary)

```bash
bench --site kentender.midas.com execute kentender_procurement.std_engine.import.dry_run \
  --kwargs "{'zip_path': '.../KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip', 'pdf_path': '.../DOC 10....pdf'}"

bench --site kentender.midas.com execute kentender_procurement.std_engine.import.commit \
  --kwargs "{'zip_path': '...', 'pdf_path': '...', 'package_id': 'KE-PPRA-IT-2022-04'}"
```

### HTTP (scaffold — Milestone 1)

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/std-engine/import/dry-run` | Non-destructive inspection + report |
| `POST` | `/std-engine/import/commit` | DRAFT commit import |
| `GET` | `/std-engine/import-runs/:id` | Retrieve dry-run or commit report |

Frappe implementation may map to `@frappe.whitelist` methods (e.g. `/api/method/kentender_procurement.std_engine.api.import_api.dry_run`) until dedicated route handlers exist. External contract above is the target shape for screen 20. Do not duplicate logic between CLI and HTTP; both must call the same importer services.

### Import Run record

Persist each dry-run and commit as an **STD Import Run** (or equivalent DocType) so screen 20 and `GET import-runs/:id` share one read model.

Report fields (minimum): `package_id`, `family_code`, `version_code`, `package_sha256`, `manifest_hash`, `source_document_hash`, `record_counts`, `missing_required_files`, `validation_blockers`, `validation_warnings`, `import_readiness`, `checksum_status`, `target_state` (always `DRAFT` on commit).

## Read API envelope

All read endpoints return:

```json
{
  "packageContext": {
    "familyCode": "KE-PPRA-IT",
    "versionCode": "KE-PPRA-IT-2022-04",
    "packageId": "KE-PPRA-IT-2022-04",
    "lifecycleState": "DRAFT",
    "activationAllowed": false,
    "packageQuality": "RECONCILED_DRAFT_NOT_ACTIVATABLE",
    "immutable": false,
    "uiMode": "READ_ONLY_INSPECTION",
    "canEdit": false,
    "canActivate": false
  },
  "data": {},
  "pagination": null,
  "validationSummary": { "blockers": 0, "warnings": 0, "info": 0 },
  "audit": { "snapshotHash": "...", "generatedAt": "..." }
}
```

## Screen ↔ API wiring

Static HTML in `public/std_prod_impl/` stays verbatim. **Desk page JS** (iframe shell) fetches APIs and injects data. Default package: `KE-PPRA-IT-2022-04`.

Data-bearing regions must be API-driven. Do not leave mock `2024-04` values in:

```text
breadcrumbs
screen headers
metadata strips
package/version columns
validation reports
audit logs
source traceability
usage bindings
import manifests
```

Harmless decorative text may wait for a later UI refresh, but legal/audit identity must always come from the API.

| # | Screen | Read API | M1 notes |
|---|---|---|---|
| 01 | STD Library | `get_std_families` | Real imported family |
| 02 | Family Detail | `get_std_family?family_code=KE-PPRA-IT` | Version list (DRAFT) |
| 03 | Version Detail | `get_std_version?package_id=KE-PPRA-IT-2022-04` | Integrity from validation summary |
| 04 | Source Traceability | `get_std_version_source_traceability` | PDF + anchors from import |
| 05 | Section / Clause Map | `get_std_version_sections` | Real tree |
| 06 | Clause Detail | `get_std_clause` | Real clause + trace |
| 07 | Parameter Dictionary | `get_std_version_parameters` | After vertical slice |
| 08 | Parameter Detail | `get_std_parameter` | |
| 09 | Rule Dictionary | `get_std_version_rules` | |
| 10 | Rule Detail | `get_std_rule` | |
| 11 | Form Schema Manager | `get_std_version_forms` | |
| 12 | Form Detail | `get_std_form` | |
| 13 | Requirement Schema | `get_std_version_requirements` | |
| 14 | Price Schedule | `get_std_version_price_schedules` | |
| 15 | Evaluation Schema | `get_std_version_evaluation_schema` | |
| 16 | Render Blocks | `get_std_version_render_blocks` | |
| 17 | Validation Report | `get_std_version_validation_report` | Persisted findings |
| 18 | Review & Approval | Composite: version + validation + audit | **No workflow actions** |
| 19 | Usage / Bindings | `get_std_version_usage_bindings` | Seeded; `fixture_source=SMOKE_TEST_EXPECTATION` |
| 20 | Import Package Review | `GET import-runs/:id` | Dry-run / commit reports |
| 21 | Version Diff | `get_std_version_diff` | **Stub:** `compareAvailable: false`, single-version message |
| 22 | Audit Log | `get_std_version_audit_log` | Import + validation events |

## Usage binding seed

Source: `KE-PPRA-IT-2022-04_seed_package_v0_2/tests/tender_binding_smoke_tests.json` (inside zip).

- Import **minimal** rows needed for screen 19 smoke/display
- Tag every seeded row: `fixture_source = "SMOKE_TEST_EXPECTATION"`
- Read-only; no tender enforcement

## Version diff (screen 21) — Milestone 1 stub

- Do **not** import skeleton or fabricate a second STD version
- API returns explicit payload, e.g. `compareAvailable: false`, `reason: "SINGLE_VERSION_ONLY"`, current version metadata only
- Real compare deferred until a second approved fixture package exists (future ticket)

## UI wiring order

1. **Vertical slice** (01–06, 17, 22) — see `MILESTONE_1_VERTICAL_SLICE.md`
2. Schema screens (07–16)
3. Placeholders (18–21) with rules above

## Module boundary

```
kentender_procurement/std_engine/     ← owns import, validation, audit, read APIs
kentender_procurement/tender_management/  ← consumes STD later; no import logic here
```

Desk iframe pages remain under existing `std_prod_*_page.js` hooks; they call `std_engine` APIs only.

## Empty-state and error behavior

- Missing optional schema data should render as an explicit empty state with the related validation finding where applicable.
- Missing required legal/source data must be a dry-run/commit failure.
- API responses must never fabricate clauses, source anchors, validation results, usage bindings, or version-diff rows.
- Screen 21 must return `compareAvailable=false` until a real second package is imported.
