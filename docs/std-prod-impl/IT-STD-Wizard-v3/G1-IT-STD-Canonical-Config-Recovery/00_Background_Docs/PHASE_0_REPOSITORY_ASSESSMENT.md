# G1 Phase 0 — Repository Assessment

| Item | Value |
|---|---|
| Phase | 0 — Repository audit (directive §12) |
| Status | **Complete — ready for Phase 1** (open legal-source digest gap; see §7.2) |
| Date | 2026-07-24 (revised same day) |
| Repo | `apps/kentender_v1` @ branch `master` |
| Site (runtime) | `kentender.midas.com` (**dev** — data may be torn down) |
| Calibration tender | NSSF SPS ERP `NSSFSPS/ICT/ERP/001/2025-2026` (fixture only) |
| Hard blockers (§25) for starting Phase 1 | None for schemas/fixture errata |
| Open non-blocking gap | Official IT STD + original NSSF tender archive digests unresolved (§7.2) |

---

## 1. Outcome

Phase 0 is complete. **Structured** G1/E1 binding inputs used by later compiler phases are present and match Cursor directive §13.1 digests. The current bidder checklist is confirmed to be driven by legacy `10_NSSF_Electronic_Bidder_Submission_Schema.json` via `schema_compiler.SECTION_KEYS`, not by the canonical PPRA IT STD blueprint.

**Legal source archives** cited in §13.1 (`sha256:2e57294f…` IT STD, `sha256:bb716e97…` NSSF tender) are **not present** at those digests anywhere under `docs/std-prod-impl/`. Closest on-disk PDFs hash differently. Consequence: do **not** claim “all binding inputs present”; Phase 1 can still encode closed schemas and fixture errata from the matched **structured** docs/fixtures, but later integrity stages that bind `std_source_digest` / tender `source_digest` must resolve or deliberately retarget those oracles before claiming golden legal provenance.

**No production code, DocTypes, seeds, or Website UI were modified in this phase.**

**Environment policy (standing):** this bench is in **development**. Site data on `kentender.midas.com` may be cleared/reseeded aggressively. Do not treat “preserve live published tenders” as a constraint for G1 test design.

**Next phase:** Phase 1 — Contract schemas and fixture errata (schemas + errata only; see §12 for corrected exit wording).

---

## 2. Stack inventory

| Concern | Finding |
|---|---|
| Monorepo | `apps/kentender_v1/` — multi-app KenTender set symlinked into Frappe bench |
| Apps (relevant) | `kentender_procurement` (bidder/tender CFG), `kentender_core` (Civic Ledger Desk — out of G1 UI scope) |
| Package managers | Python: each app `pyproject.toml` (flit); UI: root `package.json` + lockfile |
| Python | `kentender_procurement` requires `>=3.14`; ruff configured |
| Database | MariaDB via Frappe; migrations via `patches.txt` + `patches/*.py` (~41 patch modules) |
| Unit/integration tests | `bench --site kentender.midas.com run-tests --app kentender_procurement` (unittest modules) |
| UI tests | Playwright (`playwright.config.ts`); vitest for some frontend specs |
| Makefile gates (bidder / NSSF) | `bw-domain-gate`, `bw-a0/a2/a3/a4-domain-gate`, `ui-bidder-a0…a4-gate`, `e1-nssf-seed-gate`, `e1-nssf-poc-gate`, `nssf-calibration-gate` |
| Auth | Frappe session; bidder www routes redirect Guest to `/login` |
| Audit | `Electronic Bid Audit Event`; STD engine audit elsewhere |
| File / evidence | Frappe File + mock file payloads in A4 matrix / electronic bid |
| Hash / seal | Ad-hoc `_canonical_hash` (sort_keys JSON + SHA-256) in `schema_compiler.py` and `electronic_bid.py`; package/document hashes in `f1_publication_handoff.py`; richer STD helpers in `std_engine/package_import/hash_utils.py` (`compute_file_sha256`, `compute_manifest_hash` — **not** RFC 8785 JCS yet). See §11 for what `seal_hash` actually proves. |
| Decimal | Frappe / Python money paths in price schedule services |
| Frontend (bidder) | Website Jinja + `public/js` / `public/css` (not React Desk for A0–A4) |
| Frontend (officer) | Desk pages + Civic Ledger `kt_cl_*` — preserve; not G1 checklist rewrite surface |

---

## 3. Domain and service inventory

### 3.1 DocTypes (`tender_configurations/doctype/`)

| DocType | Role for G1 |
|---|---|
| `Tender Configuration` | CFG hub; field `bidder_submission_schema` (compiled JSON today) |
| `Confirmed Tender Document Package` | Confirmed package; `document_hash`, schema snapshots |
| `IT Tender Publication Record` | Publication / bidder-visible tender |
| `Electronic Bid Submission` | Bid draft/seal; `schema_hash`, `seal_hash`, `responses` |
| `Electronic Bid Audit Event` | Bid lifecycle audit |

### 3.2 Key services (`tender_configurations/services/`)

| Area | Modules |
|---|---|
| Schema compile / read | `schema_compiler.py`, `bidder_submission_schema.py`, `e1_nssf_fixture_mapper.py` |
| Bidder workspace | `available_tenders.py`, `published_tender_overview.py`, `submission_checklist.py`, `tender_documents_addenda.py`, `requirement_matrix.py`, `electronic_bid.py` |
| Publication handoff | `f1_publication_handoff.py`, `package_review.py`, `publication_setup.py` |
| CFG wizard blobs | `profile.py`, `tds.py`, `it_requirements.py`, `price_schedule.py`, `evaluation_setup.py`, `implementation_schedule.py`, `forms_and_evidence.py`, `contract_values.py`, … |
| Seed | `seed/e1_nssf_seed.py` (`TCFG-E1-NSSF*`) |

### 3.3 Website routes (`hooks.py` → `www/tenders/`)

| Route | Handler |
|---|---|
| `/tenders` | `index` |
| `/tenders/<publication_ref>` | `overview` |
| `/tenders/<publication_ref>/workspace` | `workspace` (A2 checklist) |
| `/tenders/<publication_ref>/documents` | `documents` (A3) |
| `/tenders/<publication_ref>/sections/<section_key>` | `section` (A4 matrix) |

---

## 4. Current vs canonical checklist / manifest pipeline

### 4.1 Current runtime pipeline (pre-recovery)

```text
E1 pack 10_NSSF schema (section templates)
  + Tender Configuration CFG blobs (190 reqs, 22 price lines, criteria)
  → schema_compiler.compile_schema_* / persist_compiled_schema
  → Tender Configuration.bidder_submission_schema
  → get_submission_checklist / get_requirement_matrix / electronic_bid
  → Website A2 / A4
```

Hard-coded order in `schema_compiler.SECTION_KEYS`:

1. `tender_document_acknowledgement`
2. `form_of_tender`
3. `confidential_business_questionnaire`
4. `preliminary_documents`
5. `technical_qualification`
6. `technical_compliance_matrix`
7. `implementation_plan`
8. `price_schedule`
9. `contract_terms_acknowledgement`
10. `final_declaration_and_submit`

Display override: `contract_terms_acknowledgement` → “Contract Conditions Acknowledgement” (`submission_checklist.SECTION_TITLE_OVERRIDES`).  
Final-section lock logic uses `FINAL_SECTION_KEYS` including `final_declaration_and_submit`.

### 4.2 Canonical target (directive §4.1 / Blueprint — not implemented)

Content sections (NSSF golden = 10, includes Tender Security; omits Lots):

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

Plus Evidence/Issues registers and workflow gates `review_and_validate` / `submit_and_seal` / `submission_receipt` (**not** content rows).

| Legacy key | Canonical disposition (from 04 crosswalk) |
|---|---|
| `tender_document_acknowledgement` | → `tender_documents_and_addenda` |
| `form_of_tender` | rebuild full PPRA FoT |
| `confidential_business_questionnaire` | rebuild full PPRA CBQ |
| `preliminary_documents` | → `preliminary_requirements_and_evidence` |
| `technical_qualification` | → `qualification_and_capability` |
| `technical_compliance_matrix` | → `requirements_compliance` |
| `implementation_plan` | → `technical_proposal_and_implementation_plan` |
| `price_schedule` | keep lines; canonical tables |
| `contract_terms_acknowledgement` | **remove** as content |
| `final_declaration_and_submit` | **split** → statutory decls + gates |
| *(missing)* | **add** `statutory_declarations`, `tender_security` |

---

## 5. Stitch / UI component map

| Surface | Design reference | Runtime |
|---|---|---|
| A0 landing | `docs/bidder-workspace/A0-bidder-landing-page/code.html` | `www/tenders/index.*`, `available_tenders.js` |
| A1 overview | `A1-published-tender-overview/code.html` | `www/tenders/overview.*` |
| A2 checklist | `A2-submission-checklist/code.html` | `www/tenders/workspace.*`, `submission_checklist_web.css` |
| A3 documents | `A3-documents-and-addenda/code.html` | `www/tenders/documents.*` |
| A4 Requirements Compliance (drawer) | `A4-requirements/code.html` | `www/tenders/section.*`, `requirement_matrix_web.js/.css` |
| Workspace sidebar | (shared) | `templates/includes/kt_bidder_workspace_sidebar.html` |
| Desk electronic PoC | — | `public/js/it_electronic_bidder_workspace_page.js` (defaults `TCFG-E1-NSSF-ERP`) |

**Phase 6+ rule:** preserve Stitch layout; Requirements Compliance keeps right-hand drawer; do not call the screen “Technical Requirements.”

---

## 6. Migrations and test gate map

### 6.1 Patches

- Registry: `kentender_procurement/patches.txt` (`pre_model_sync` / `post_model_sync`).
- Closest to G1: `ensure_tender_configurations_module`; no bidder-workspace-manifest patch yet.
- Pattern: ensure-module/page, retire/cleanup, backfill — forward-only.

### 6.2 Existing tests (no BWMF-T* / NSSF-GOLD-* yet)

| Gate / module | Covers |
|---|---|
| `test_schema_compiler` | Pack-10 compile + SECTION_KEYS |
| `test_e1_nssf_fixture_mapper` / `test_e1_nssf_seed` | E1 seed path |
| `test_submission_checklist_*` | A2 API + web |
| `test_requirement_matrix_*` | A4 API + web |
| `test_electronic_bid_submission` | Seal / responses |
| Playwright `a0…a4` | Website smoke |
| `e1-nssf-*` / `nssf-calibration-gate` | PoC / STD calibration |

Binding suites `BWMF-T001`–`054` and `NSSF-GOLD-001`–`048` are **not present** until later phases.

### 6.3 Isolated test / fixture strategy (dev)

Standing rules for G1 work on this bench:

1. **Site is disposable.** Prefer seed helpers with `clear=True` / dedicated clear+reload targets; delete electronic bids and CFG rows under test without hesitation.
2. **Isolate by known codes.** Use `TCFG-E1-NSSF*`, publication refs from E1 seed, and future `BWMF-*` / `NSSF-GOLD-*` fixtures — do not invent parallel master codes that collide with PP2 WORKS masters.
3. **Canonical clear before reload** when replacing a seed path (same spirit as PP2 legacy-removal); leave no orphan packages/bids for the config under test.
4. **Legacy pack 10** remains a **negative / compatibility** fixture until Phases 3 & 6 cut over; new tests must not treat it as the canonical contract.
5. **Makefile caveat:** `nssf-calibration-gate` passes fully-qualified `--test` names that currently match **zero** tests under this Frappe runner. Use **short** method names (e.g. `test_cal_nssf_001_…`) until the Makefile is fixed (out of Phase 0 scope unless requested).

Domain-model constraints from the directive (append-only versions, immutable sealed snapshots, idempotent submit) still apply to **code contracts and tests**; they are not a reason to avoid tearing down **dev** seed data between runs.

---

## 7. Binding-input path and digest table

Computed 2026-07-24 with `sha256sum` on repo files. Expected digests from Cursor directive §13.1 / golden crosswalk § where listed.

### 7.1 Structured pack inputs (matched)

| Artifact | Repo path | SHA-256 (computed) | Expected (§13.1) | Status |
|---|---|---|---|---|
| Obligation Catalogue | `G1-…/01. Canonical_PPRA_IT_STD_Bidder_Submission_Obligation_Catalogue_v1.md` | `eb045d1f33fe7c34d67ef18f004266bf3b25bd8eb11fa77ef4705f0691b369ba` | `eb045d1f…b369ba` | **Match** |
| Section Blueprint | `G1-…/02. Canonical_PPRA_IT_STD_Bidder_Submission_Section_Blueprint_v1.md` | `de3cf25fc4087d4d9f65407476b95d4e67a8701db31cd0246446807e30bc7c25` | `de3cf25f…bc7c25` | **Match** |
| Manifest Contract | `G1-…/03. Bidder_Workspace_Manifest_Contract_and_Compilation_Specification_v1.md` | `29c3a28fd80e67873a07e7ab10171b6a6ffd314b27bf66fd713af01d838f2eed` | `29c3a28f…8f2eed` | **Match** |
| NSSF Golden + Crosswalk | `G1-…/04. NSSF_Bidder_Workspace_Golden_Manifest_and_Migration_Crosswalk_v1.md` | `f14cb3c0bfbd6886296c0e8401c6491607db4d8be0b0db6d9cbed7185507a210` | *(not in §13.1 table)* | Recorded |
| Form of Tender spec | `G1-…/05. KenTender_Form_of_Tender_Electronic_Section_Specification_v1.md` | `92adadc808642cf034b3dc9cf0d6dcff092a955273e4a16b188a83a850488343` | `92adadc8…488343` | **Match** |
| Checklist correction note | `G1-…/00. Bidder-Checklist-Correction.md` | `3ca411508eff5bc1171a4c19f7488b9fa382740c2543d7186524b60ad66a5df1` | — | Recorded |
| Cursor directive | `G1-…/Cursor_Implementation_Directive_…_v1.md` | `96d9fbb971230aaefe761a6449ce3c774551e707684ffd4c6284aefae2c7f7e0` | — | Recorded |
| NSSF structured fixture 09 | `E1-…/09_NSSF_Full_Structured_Fixture.json` | `4db4747950e8831f9385ce52463c4365ae72e6de4b72b8e896deab5b4cd2bfe1` | `4db47479…d2bfe1` | **Match** |
| Requirement matrix CSV | `E1-…/04_Requirement_Matrix_Full_Row_Extraction.csv` | `188277306f78c62916b5136e58f225073e90a9344b8d1171567665f9513108ec` | *(resource digests differ — content-addressed later)* | 190 data rows OK |
| Price schedule CSV | `E1-…/05_Price_Schedule_Lines.csv` | `482be34f3fc5401a4b33e9a1ca67ce8a7e07cdcf0c50755644d1d35028762ef5` | *(resource digests later)* | 22 data rows OK |
| Legacy bidder schema 10 | `E1-…/10_NSSF_Electronic_Bidder_Submission_Schema.json` | `4d461f4901ef159578b441afd468125ce60b310d67575a81dc23d88ff4a6fa72` | `4d461f49…a6fa72` | **Match** |

### 7.2 Legal source archives (oracles unresolved)

| Oracle (directive / crosswalk) | Expected SHA-256 | On-disk candidates | Computed SHA-256 | Status |
|---|---|---|---|---|
| Official PPRA IT STD source archive | `2e57294f5cd49cfeca476347a3c81922f1efd834fdaa56430c3066efd1f6d251` | `docs/std-prod-impl/data/DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.pdf` | `7da1aeb2bb1af918e86ccdff0538ec87ec6dfa90e8433acbc84f6dbe6bb78a49` | **Mismatch** |
| Same PDF (duplicate) | (same) | `…/IT-STD-Wizard-v3/D1-WG3/DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.pdf` | `7da1aeb2…bb78a49` (identical twin) | **Mismatch** |
| Original NSSF tender source archive | `bb716e97a312548d8469c5513539f0679e83b3336c7d630c2d7d6c77773aeb38` | `docs/std-prod-impl/data/NSSF SPS RFP ERP 2026.pdf` | `622835296e2ec1721e3caee4b14d933d2c887568573ed83c12e843a41641a90a` | **Mismatch** |
| Same PDF (duplicate) | (same) | `…/IT-STD-Wizard-v3/D1-WG3/NSSF SPS RFP ERP 2026.pdf` | `62283529…41a90a` (identical twin) | **Mismatch** |

Repo-wide scan of `docs/std-prod-impl/**/*.{pdf,zip}`: **no file** hashes to `2e57294f…` or `bb716e97…`. Seed zips (including `Tender_Configurations_Full_Documentation_Pack_v6.zip` → `0a8373ee…`) also do not match those oracles.

**Consequence (accurate):**

- Structured catalogue / blueprint / manifest / FoT / fixture-09 / legacy-10 digests are usable as Phase 1+ contracts.
- Claims of “official IT STD archive digest” or “original NSSF tender archive digest” as **byte-verified** inputs are **not** supported by the current tree.
- Later compiler stages that require `std_source_digest` / tender `source_digest` equality against §13.1 must either obtain the matching archives, or the pack must be amended to retarget the digests of the PDFs above (product decision — not made in Phase 0).

### 7.3 Later-phase oracles (not verified by compile yet)

| Oracle | Digest |
|---|---|
| Projection | `sha256:461ffc824759f767f01bdfa9be77b3280da8020267d4743cd5ca7f9fb03ffa22` |
| Diagnostic-set | `sha256:b3bbc3f30456383236a9ea1b131fee9d6e62519a20e45484c987805260be84f7` |

Fixture counts confirmed from pack 10 / CSVs: **190** requirements, **22** price lines, **10** legacy sections.

---

## 8. Baseline gate evidence (2026-07-24)

All commands from bench root unless noted. Site: `kentender.midas.com`.

| Gate / command | Result | Tests | Approx. duration | Failures / notes |
|---|---|---|---:|---|
| `make -C apps/kentender_v1 bw-domain-gate` | **OK** | 9 | ~10–13s wall | — |
| `make -C apps/kentender_v1 bw-a0-domain-gate` | **OK** | 10 + 2 | ~domain wall | — |
| `make -C apps/kentender_v1 bw-a2-domain-gate` | **OK** | 10 + 2 | ~domain wall | — |
| `make -C apps/kentender_v1 bw-a3-domain-gate` | **OK** | 10 + 2 | ~domain wall | — |
| `make -C apps/kentender_v1 bw-a4-domain-gate` | **OK** | 17 + 2 | ~domain wall | — |
| `bench … --module …test_schema_compiler` | **OK** | 3 | ~few s | Pack-10 still canonical in runtime |
| `bench … --module …test_electronic_bid_submission` | **OK** | 2 | ~few s | Seal PoC path |
| `make -C apps/kentender_v1 e1-nssf-seed-gate` | **OK** | 15 + 11 | ~seed wall | — |
| `make -C apps/kentender_v1 ui-bidder-a0-gate` | **OK** | 3 passed | ~13s | Playwright |
| `make -C apps/kentender_v1 ui-bidder-a1-gate` | **OK** | 2 passed | ~36s | Playwright |
| `make -C apps/kentender_v1 ui-bidder-a2-gate` | **OK** | 1 passed | ~10s | Playwright |
| `make -C apps/kentender_v1 ui-bidder-a3-gate` | **OK** | 1 passed | ~10–12s | Playwright (clean rerun) |
| `make -C apps/kentender_v1 ui-bidder-a4-gate` | **OK** | 1 passed | ~12–14s | Playwright |
| NSSF CAL (short `--test` names; five methods) | **OK** | 5 × 1 | ~64s total | `001/002/003/012/013` all ✔ |
| `make -C apps/kentender_v1 nssf-calibration-gate` | **Misleading** | effectively **0** per FQ name | n/a | Makefile uses fully-qualified `--test` paths; runner matches nothing. Prefer short names until Makefile fixed. |
| `make -C apps/kentender_v1 e1-nssf-poc-gate` | **FAIL** (pre-existing) | domain subset OK; UI fails | ~175s wall | Playwright Desk PoC: `kt-eb-workspace` not found on `/desk/it-electronic-bidder-workspace/TCFG-E1-NSSF-ERP` |

**Baseline verdict for G1 Phase 0:** bidder Website A0–A4 + domain gates are green; E1 seed green; schema compiler + electronic bid unit tests green; NSSF calibration green when invoked correctly; Desk E1 PoC UI gate is **already red** and is not a Phase 0 exit blocker (PoC surface is superseding territory for G1, not the Website checklist recovery path).

---

## 9. NSSF boundary scan (production `.py` / `.js`)

Classification for later remediation. Phase 0 does not move these.

| Classification | Examples | Paths |
|---|---|---|
| **Allowed — seed / mapper / fixture loader** | `TCFG-E1-NSSF`, entity defaults, pack paths | `seed/e1_nssf_seed.py`, `e1_nssf_fixture_mapper.py`, `std_engine/fixtures/nssf_calibration_fixture_loader.py` |
| **Allowed — defensive “no NSSF in STD output”** | Forbidden markers, compressed-text guards | `preview_presentation.py`, `std_engine/services/render_service.py` |
| **Deferred — production runtime still NSSF-shaped** | Default schema name; pack-10 compile authority; hard-coded `technical_compliance_matrix` | `schema_compiler.py`, `electronic_bid.py`, `public/js/electronic_bid/bidder_workspace_renderer.js` |
| **Deferred — Desk PoC default** | Default config id `TCFG-E1-NSSF-ERP` | `public/js/it_electronic_bidder_workspace_page.js` |
| **Comments only** | Display-pattern comments | `requirement_matrix.py`, `document_preview.py` |
| **Not in production code** | `Microsoft Dynamics` / Azure product strings | Present in E1 JSON fixtures only (good) |

Canonical templates must not gain NSSF/Microsoft/KES/VAT constants in Phases 1+; fixture values stay in resources/migration/tests.

---

## 10. Unrelated WIP to preserve

`git status` on `apps/kentender_v1` at assessment time (do not fold into G1 commits unless required):

| Path | Note |
|---|---|
| `kentender_core/.../kt_cl_code_layout.css` | Civic Ledger — unrelated |
| `kentender_core/.../kt_cl_surface_registry.js` | Civic Ledger — unrelated |
| `kentender_core/.../test_kt_cl_surface_registry_contract.py` | Civic Ledger — unrelated |
| `kentender_procurement/.../workspace_sidebar/demand_intake.json` | DIA nav — unrelated |
| `kentender_procurement/.../workspace_sidebar/planning_module_navigation.json` | Planning nav — unrelated |
| `docs/std-prod-impl/IT-STD-Wizard-v3/D1-WG3/*.pdf` | Large untracked PDFs — do not auto-commit |
| `docs/std-prod-impl/IT-STD-Wizard-v3/Tender_Configurations_Full_Documentation_Pack_v6.zip` | Large untracked zip |
| `docs/std-prod-impl/IT-STD-Wizard-v3/G1-IT-STD-Canonical-Config-Recovery/` | Entire G1 pack currently **untracked** (including this assessment) — commit as a dedicated G1 docs/recovery commit when requested |

---

## 11. `seal_hash` — what it proves (and does not)

Implementation today (`electronic_bid._canonical_hash` / `submit_and_seal`):

```text
seal_hash = SHA-256( json.dumps(
  { responses, schema_hash, configuration_id, std_version },
  sort_keys=True, separators=(",", ":"), ensure_ascii=False
) )
```

| Claim | Verified? |
|---|---|
| Integrity fingerprint of the sealed payload fields above | **Yes** (content-addressed hash of sorted JSON) |
| RFC 8785 JCS / cross-language canonicalization | **No** |
| Encryption / confidentiality of bid contents before opening | **No** — hash does not hide `responses` in the DocType |
| Cryptographic “seal” in the legal/PKI sense | **No** — not a signature, not a confidentiality seal |
| Idempotent re-seal returning same receipt without re-hash edge cases | Partial — sealed path short-circuits to `get_receipt`; not a full G1 submit contract |

**Wording rule for later phases:** call `seal_hash` an **integrity fingerprint of the sealed snapshot**, not a “cryptographic confidentiality seal,” unless/until encryption + opening controls are implemented and verified.

---

## 12. Critical Capability Gap Register

Mapped against directive persistence / application services. Status is **as of Phase 0** (pre-recovery). Gaps are expected; they define later-phase work, not Phase 0 failure.

| Capability | Required (directive) | Current repo | Gap severity | Target phase |
|---|---|---|---|---|
| Legal authority binding | Authority ref/version; not role alone | Role/session checks; admin PoC gates on electronic bid | **High** | 5 / 8 |
| Confirmations ≠ save | Deliberate confirm with legal text + digest | Section save / matrix merge; no confirmation aggregate | **High** | 7 / 8 |
| Evidence content-addressed store | Digest uniqueness, version lineage | Frappe File + JSON response blobs | **High** | 4 / 7 |
| Validation snapshots | Immutable validation/diagnostic records | Ad-hoc validate APIs; not persisted snapshots | **High** | 1 schemas → 7 runtime |
| Dependency / invalidation graph | Acyclic deps; invalidation events on change | None in bidder workspace | **High** | 3 (C14) / 7 / 10 |
| Submit idempotency + atomicity | One authoritative sealed result; atomic persist | Soft idempotency if already sealed; no full transaction/idempotency key model | **High** | 2 / 8 |
| Receipt model | Stable receipt with snapshot digests | `receipt_code` + timestamps + `seal_hash` PoC DTO | **Medium** | 8 |
| Pre-opening confidentiality | Confidential until lawful opening | Bid JSON readable to privileged Desk users; no opening ceremony controls | **High** | 8+ |
| Approval ↔ manifest digest | Publication bound to approved digest | CFG / package hashes exist; no digest-bound approval→publish link for bidder manifest | **High** | 5 |
| Atomic tender + manifest publish | Tender version + matching manifest visible together | Publication record + compiled schema field; not atomic dual publish | **High** | 5 |
| Manifest compiler C01–C22 | Pure deterministic compiler | `schema_compiler` from pack 10 | **Critical** (wrong authority) | 3 |
| Canonical checklist projection | Blueprint §4.1 keys | Legacy `SECTION_KEYS` | **Critical** (user-visible) | 6 |
| Legal source archive digests | §13.1 IT STD + NSSF tender | On-disk PDFs mismatch (§7.2) | **Medium** (blocks provenance claims) | resolve before golden integrity claims |

---

## 13. Architecture mapping and Phase 1 entry recommendations

| Directive concept | Existing anchor | Gap / decision |
|---|---|---|
| Obligation catalogue | Docs `01` only | No runtime catalogue store |
| Section blueprint | Docs `02`; superseded by `SECTION_KEYS` | Replace hard-coded keys in later phases |
| Manifest compiler | `schema_compiler.py` | Wrong authority (pack 10); needs C01–C22 |
| Manifest digest | `_canonical_hash`; STD `hash_utils` | Prefer shared digest service; add RFC 8785 JCS in Phase 3 |
| Published tender + package | Publication + Confirmed Package | Atomic tender+manifest publish missing (Phase 5) |
| Checklist projection | `submission_checklist.py` + A2 UI | Must become manifest-driven (Phase 6) |
| Requirements Compliance | A4 `requirement_matrix_*` | Keep drawer; source from manifest |
| Seal / receipt | `electronic_bid.py` | Extend integrity + receipt model; do not overclaim crypto (§11) |
| NSSF resources | E1 JSON/CSV + mapper | Content-addressed resources (Phase 4) |
| Legacy migration | None | Adapter Phase 9; keep `10_NSSF` as negative fixture |

### Phase 1 schema encoding recommendation (not implemented in Phase 0)

Reuse repository patterns:

1. **JSON Schema documents** (closed objects, versioned) under a new tree such as  
   `kentender_procurement/kentender_procurement/tender_configurations/bidder_workspace_manifest/schemas/`  
   (or sibling `manifest_contract/`), mirroring STD package schema files under `std_engine`.
2. **Python validators** that reject unknown properties for v1 closed objects (stdlib `json` + explicit validation helpers; introduce `jsonschema` only if already accepted elsewhere — prefer minimal new deps).
3. **Fixture errata** only in calibration/test expectations: NSSF = **10** content sections including Tender Security; keep file `10_NSSF` for migration/negative tests.

---

## 14. Hard blockers

| Item | Blocks Phase 1? |
|---|---|
| Missing matched IT STD / NSSF **archive** digests (§7.2) | **No** for closed schemas + fixture errata; **Yes** for any claim that golden provenance digests are byte-verified |
| Red `e1-nssf-poc-gate` Desk UI | **No** — pre-existing PoC; Website A0–A4 green |
| Makefile FQ `--test` filter for NSSF CAL | **No** — workaround: short test names |

None of the above prevent starting Phase 1 schema work.

---

## 15. Explicit next phase (corrected exit)

**Phase 1 — Contract schemas and fixture errata**

Implement closed, versioned schemas and Section 4 fixture errata per directive § Phase 1 tasks.

**Corrected Phase 1 exit (binding for this recovery):**

1. Schemas compile; closed-object tests pass.
2. NSSF golden expectation is **10** content sections; Tender Security resolved in fixture/errata expectations.
3. **No new code** treats legacy `10_NSSF_Electronic_Bidder_Submission_Schema.json` as the canonical runtime contract.
4. **Legacy runtime may remain** (`schema_compiler.SECTION_KEYS`, Website A2/A4 still pack-10-shaped) behind an **explicit compatibility boundary** until Phases 3 (compiler) and 6 (checklist projection) cut over.
5. Phase 1 does **not** require deleting or rewriting live checklist UI in the same change set.

This corrects the stricter reading of directive wording (“no production code depends on the legacy schema”) so Phase 1 stays schema/errata-only without a forced big-bang cutover.

---

## 16. What you will see / What changed

### What changed

- **Revised:** this file —  
  `docs/std-prod-impl/IT-STD-Wizard-v3/G1-IT-STD-Canonical-Config-Recovery/PHASE_0_REPOSITORY_ASSESSMENT.md`
- **Added in revision:** legal-source digest table (§7.2), baseline gate evidence (§8), capability gap register (§12), seal_hash clarification (§11), corrected Phase 1 exit (§15), disposable-dev fixture strategy (§6.3).
- **Not changed:** production Python/JS, DocTypes, seeds, Website checklist/matrix UI, `schema_compiler.SECTION_KEYS`, E1 pack binaries, Civic Ledger / planning sidebar WIP.

### What you will see

1. G1 folder contains `PHASE_0_REPOSITORY_ASSESSMENT.md` beside 00–05 and the Cursor directive.
2. §7.1 structured digests match; §7.2 legal archives do **not**.
3. §4 contrasts legacy `SECTION_KEYS` with canonical §4.1 keys.
4. §8 gate table shows green Website/bidder domain baseline and red Desk E1 PoC.
5. Live UI `/tenders/<ref>/workspace` still shows the **old NSSF-shaped 10 rows** — intentional for Phase 0.
6. Dev teardown of seed/bid data is expected and allowed.

### What should NOT change

- Stitch HTML under `docs/bidder-workspace/A*/code.html`.
- A2/A4 runtime behavior and existing Playwright gates (unchanged by this phase).
- No new Makefile targets, DocTypes, or compiler modules from Phase 0.

### How to verify

```bash
# Assessment exists
test -f apps/kentender_v1/docs/std-prod-impl/IT-STD-Wizard-v3/G1-IT-STD-Canonical-Config-Recovery/PHASE_0_REPOSITORY_ASSESSMENT.md && echo OK

# Spot-check legacy schema digest
cd apps/kentender_v1
sha256sum docs/std-prod-impl/IT-STD-Wizard-v3/E1-NSSF_Tender_PoC_Mapping_Pack/10_NSSF_Electronic_Bidder_Submission_Schema.json
# Expect: 4d461f4901ef159578b441afd468125ce60b310d67575a81dc23d88ff4a6fa72

# Spot-check legal PDF digests (expect MISMATCH vs directive oracles)
sha256sum "docs/std-prod-impl/data/DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.pdf"
sha256sum "docs/std-prod-impl/data/NSSF SPS RFP ERP 2026.pdf"
# Expect: 7da1aeb2… and 62283529… respectively — NOT 2e57294f… / bb716e97…

# Phase 0 should not have touched production services
git status --short -- kentender_procurement/kentender_procurement/tender_configurations/services/
```

Optional (not required for Phase 0 exit): `make -C apps/kentender_v1 ui-bidder-a2-gate` — checklist still old shape.

### Cross-check against recovery intent

- Documents that today’s checklist is fixture-driven (`10_NSSF`), matching `00. Bidder-Checklist-Correction.md`.
- Records canonical 10-section + Tender Security target without implementing it.
- Inventories NSSF leakage so later phases can clear production code deliberately.
- Lists unrelated WIP so G1 commits stay isolated.
- Does **not** claim the bidder checklist is fixed (UI recovery starts at Phase 6).
- Does **not** claim legal source archives are byte-verified.

### Standing template for Phases 1–10 reports

Every later G1 phase report must repeat the five subsections above. Minimum verifier anchors:

| Phase | Verifier should eventually see |
|---|---|
| 1 | Closed schemas + fixture errata; tests expect **10** NSSF sections + Tender Security; **no new code** treats `10_NSSF` as canonical; legacy runtime may remain behind explicit compatibility boundary |
| 2 | Persistence; published-manifest mutation rejected (dev DB may still be wiped between suites) |
| 3 | Compiler C01–C22; deterministic digest replay |
| 4 | Content-addressed NSSF resources; count/digest gates |
| 5 | Atomic publish + digest-bound approval |
| 6 | `/workspace` checklist from published manifest (canonical keys); Stitch layout preserved |
| 7 | Versioned responses/evidence; derived status only |
| 8 | Confirm ≠ save; Submit & Seal + Receipt; integrity fingerprint wording accurate |
| 9 | Migration dry-run; reconfirmation flags; zero silent unmapped |
| 10 | Addendum impact by lineage/key/scope |

---

## 17. Phase 0 checklist (directive §12)

| # | Item | Evidence |
|---|---|---|
| 1 | Stack / PM / DB / tests / auth / audit / storage / seal / decimal / frontend | §2, §11 |
| 2 | Tender CFG, published tender, workspace, submission, evidence, evaluation models | §3 |
| 3 | Manifest/schema usage and renderer dispatch | §4, §5 |
| 4 | Hard-coded checklist and NSSF seed data | §4.1, §3.2 seed |
| 5 | Migrations and tests | §6, §8 |
| 6 | Approved Stitch files + Requirements Compliance drawer | §5 |
| 7 | NSSF-specific constants outside fixtures | §9 |
| 8 | Uncommitted / unrelated changes | §10 |
| 9 | Short repository assessment | This document |

**Phase 0 exit:** Ready for Phase 1 (schemas/errata), with open legal-source digest gap documented in §7.2.
