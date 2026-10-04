# STD-TPL-IMP-001 v1.0 — STD Templates: installed release runtime — implementation plan

| Control | Value |
|---|---|
| Authority | `KenTender_STD-TPL-IMP-001_Installed_STD_Template_Runtime_v1_0.md` (implementation authority) and `KenTender_STD-TPL-001_IT_Equipment_Tender_Template_Curation_and_Release_Pack_v0_10.md` (requirements authority). Both are **Proposed — Project Owner review** in KT-DOC-CTRL-001 (`98_work_progress/KenTender_Baseline_Register.yaml`, as_of 2026-09-25). |
| Implementation start condition | Phase 0 (this plan and tracker) may proceed now. Phases A and B start only after the owner approves STD-TPL-001 v0.10 and STD-TPL-IMP-001 v1.0, or explicitly authorises building against the proposed text. STD-TPL-IMP-001 v1.0 §19: "Approval makes v1.0 the implementation authority". |
| Coordinated documents (read in full or in part for this plan) | TPR-CHG-001 v0.11, BDS-CHG-001 v0.7, AUTH-ADR-001 v1.10, CFG-CHG-002 v0.16 and G1-REG-001 v1.1 (all Proposed, in `98_work_progress/working_files/` or `09_unified_system_setup/`); KT-STD-001 v1.8 (Approved 2026-09-25) |
| Design | `design/STD Templates Artboards.dc.html` (12 boards: STD-DES-01, 01F, 01E, 01R, 02, 02C, 02A, 02F, 02S, 02W, 02R, plus notes), on the shared `_ds/kentender-industry-82d82607…` bundle |
| Companions | `STD-TPL-IMP-001_v1_0_IMPLEMENTATION_TRACKER.md` (evidence ledger) |
| Predecessor tracking | `STD-TPL-001_IMPLEMENTATION_TRACKER.md` (curation of release 1.0 and the 1.1 delta under v0.3–v0.6). Its TPL-G07 and TPL-G08 gates are superseded by gates STI-G01 and STI-G05 here |
| Owning app | `kentender_procurement`, new module **STD Templates** (package `std_templates/`) |
| Prepared | 25 September 2026 |
| Status | Proposed |

## 1. Governing approach

**Replace, don't layer.** A live minimal predecessor already registers, verifies, renders and binds the template, and marks it Available with no owner decision. This cycle replaces it with the controlled-release model and does not run the two side by side.

**Build the missing half of release 1.1 before the runtime consumes it.** STD-TPL-IMP-001 v1.0 §17 says: "Do not build the UI first against invented placeholder data. The projections and closed fixtures are the UI source." The runtime therefore consumes real pack assets built in Phase A. It never uses hand-typed projection values.

**Order of work** follows STD-TPL-IMP-001 v1.0 §17 and G1-REG-001 v1.1 §4:
1. pack assets;
2. schema;
3. installer;
4. compiler;
5. renderer adapters;
6. projections and permissions;
7. UI;
8. Tender binding;
9. lifecycle;
10. retirement and release evidence.

B1–B5 are horizontal: Python only, test-driven. B6 is vertical per screen: API, then screen, then browser.

**Done means** the following, all observed in a browser:
- release 1.1 is installed as a **Candidate** from the exact pack;
- `/app/std-templates` shows it as **Unavailable**, with its real blockers, to a Procurement Officer, a Head of Procurement Function and a System Manager;
- a denied role sees nothing;
- a concern round trip changes nothing about the release;
- Start Tender is refused with a link to the release.

After the owner approves the exact manifest, reinstalling makes it **Available** and a Tender can start.

## 2. Owner decisions recorded (25 September 2026)

Answers given through the planning questions, quoted:

| # | Question | Owner answer |
|---|---|---|
| OD1 | Build the missing release 1.1 runtime files as well as the runtime? | "Check /docs/mvp-1-r1/07_tender_templates". Checked: the folder holds `01_source`–`05_review` only, with no `06_runtime`, no reservation variants and no review JSON (see §3). Recorded as: build the pack from the existing candidate, per STD-TPL-001 v0.10 §12.1 "Do not discard or rebuild the candidate from scratch". **Owner to confirm this reading (Q1).** |
| OD2 | How is an unapproved release treated? | "Install as Candidate (Recommended)" |
| OD3 | When does Tenders switch to the new registry? | "In this cycle (Recommended)" |
| OD4 | Retire the STD Configuration module, stale roles and workspace? | "Retire and archive (Recommended)" |

## 3. Baseline facts (verified 25 September 2026)

### 3.1 The release pack

`docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1/`:
- **Contents:** only `01_source`, `02_master`, `03_registers`, `04_fixture` and `05_review`.
- **Missing** (whole-machine search and `git log --all` found none, ever): `06_runtime/` (`product_profile.json`, `response_rules.json`, `downstream_rules.json`, `addendum_identity_rules.json`, `moh_published_bid_definition_expected.json`, `release_manifest.json`, `validate_release.py`); `04_fixture/build_definition_fixture.py`; `04_fixture/reservation_variants/`; and `05_review/{release_gates,release_change_report,validation_report}.json`.
- **STD-TPL-001 v0.10 §12.1 is wrong** where it says "runtime product/response/downstream/addendum assets; a validator; review record; and a 127-file SHA-256 manifest … The packaged ZIP and current validator complete successfully". None of this exists.
- **The zip** `it_equipment_open_v1.zip` shows as deleted in the working tree (not by this session). Its 128 entries covered 01–05 only.

**Register counts match the 1.1 design fixture:**
- `coverage_register.csv` has 296 rows;
- `forms_register.csv` has 28 rows;
- `insertion_points.csv` has 80 rows.

**Register columns do not match STD-TPL-001 v0.10 §13.3:**
- coverage uses `render_location` rather than `human_render_location`, and has no `structured_rule_id`;
- forms has no `contract_fields` or `response_rule_ids`;
- insertion points has no `human_render_location` or `structured_use`.

**Coverage `treatment` values:**
- Locked 130, Not used by this released pattern 64, Generated 31, Officer value 23, Supplier response 19, Inherited 18, Award-derived 11;
- there are no `Contract-derived` rows;
- `status`: 290 Reviewed, 6 Draft checked.

The STD-TPL-001 v0.10 §11.5 fixture split (Rendered 214 / Structured input 39 / Conditional 24 / Excluded with reason 13 / Not applicable 6) **cannot be derived** from these values. For example, "Not used" is 64, against Excluded 13 + Not applicable 6 = 19. See ruling R7.

**Review record:** `05_review/review_record.md` still records the v0.3 decision "APPROVE FOR IMPLEMENTATION PACK" for **release 1.0**, with the 1.0 digests. It is the comparison base for `release_change_report.json`.

### 3.2 Live predecessor (`kentender_procurement`)

- **Package `tender_templates/`:**
  - `loader.py`: verifies against `MANIFEST.sha256`. Its `bundle_digest` is the SHA-256 of that file, which is not the STD-TPL-001 v0.10 §13.9 algorithm.
  - `registry.py`: `install()` runs on `after_migrate`, and `resolve()` returns `TND_TEMPLATE_UNAVAILABLE`.
  - `renderer.py`: Jinja with `StrictUndefined`; PDF via `frappe.utils.pdf.get_pdf`, i.e. wkhtmltopdf 0.12.6.1 patched Qt at `/usr/local/bin/wkhtmltopdf`.
  - `checks.py`: checks for unresolved content, the Invitation/issued-Tender boundary and internal-value leaks.
  - An in-app byte copy of the bundle (13 manifest entries), and the Make target `tender-templates-bundle-gate`.
- **DocType `Supported Tender Template`** (module Tenders): one row, `IT-EQUIPMENT-OPEN-V1-1.1`, "Available for new Tenders", `bundle_digest ce65430f…`. No owner decision exists behind that status.
- **Tenders binding:**
  - `tenders/services/template_binding.py` (`bind`, `verify`, `require_available`) and `draft_commands.py` (`PRODUCT_KEY`), used by `review.py`, `read.py`, `lifecycle.py` and `submission_close.py`;
  - `Tender` and `Tender Version` store `template_release_id` (the composite name), `official_source_digest` and `bundle_digest`;
  - one live Tender, `TDR-138016`.
- **Compatibility:** `tenders/services/compatibility.py` (eight hard-coded checks) and `procurement_requisitions/services/compatibility.py` (`template_support()`).
- **Definition-like projections:** `tenders/services/serializer.py` has `supplier_response_schema()`, `evaluation_contract()` (with fixed stages, not `EVG-*` groups) and `contract_obligations()`. Their digests are stored on `Tender Version`.
- **Canonical JSON:** `tenders/services/digest.py` uses `default=str`, so it does not meet the defined decimal/date format rule. `tender_configurations/bidder_workspace_manifest/compiler/jcs.py` is an RFC 8785 implementation that can be adapted.

### 3.3 Retirement inventory

- **`std_configuration/` (module "STD Configuration", in `modules.txt`):**
  - 27 `STD Cfg *` DocTypes, 6 Pages (`std-cfg-*`, `hooks.py:240-252`), technical-read hooks (`hooks.py:588`, `:596`) and about 7.2k Python lines;
  - no sidebar link; 0 `STD Cfg Package` and 0 `STD Cfg Version` rows.
  - It is editable template authoring, which STD-TPL-IMP-001 v1.0 §4.4 prohibits.
- **Stale roles (9):** STD Template Administrator, Importer, Reviewer, Approver, Activator and Auditor; STD Technical Inspector; STD Configurator; STD Reviewer. Also listed in `setup/procurement_home_page.py:94-105`.
- **Stale workspace fixture** `governance_and_configuration`: it links to DocTypes that no longer exist and to a page `std-module-retired` that is absent.
- **CFG leftovers:** the "Tender formats" link was deferred and never built (`ProcurementSettingsTab.vue:275`; its spec asserts there is no link). CFG FOLLOW_UPS FU-18 is still open, and the CFG boards still draw the link.

### 3.4 Route safety

- There is no Page or DocType named `std-templates`.
- The new DocType slugs `installed-std-release`, `installed-std-release-asset` and `std-template-concern` do not collide.
- Precedent: the page `std-cfg-package` lost to its DocType's list view, which is why it was renamed `std-cfg-package-home`.

## 4. Owner-rulings register

These do not block Phase 0. Each blocks only the phase named, and each carries a proposed default.

| # | Conflict or gap (source) | Proposed default | Blocks |
|---|---|---|---|
| R1 | STD-TPL-001 v0.10 §12.1 claims runtime assets, a validator and a manifest exist; they do not (§3.1) | Treat as new work in Phase A; correct §12.1 in the next STD-TPL-001 revision | — |
| R2 | STD-TPL-IMP-001 v1.0 STI10-AC-001: "Installation fails closed unless every asset, digest, gate, adapter and exact owner decision matches", while STD-TPL-001 v0.10 §11.5 shows installed release 1.1 as Unavailable | OD2: integrity failure installs nothing; incomplete gates or decision install **Candidate**, never selectable. Record in the next IMP revision | B2 |
| R3 | TPR-CHG-001 v0.11 §5.3 allows publication for a Superseded bound release; BDS-CHG-001 v0.7 §4.4.4 step 8 and BDS05-AC-001 require Available | TPR v0.11 and STD-TPL-IMP-001 v1.0 §9 prevail ("May proceed only while integrity/adapters pass") | B7 |
| R4 | BDS-CHG-001 v0.7 §7 and BDS06-AC-012 give STD Templates inspection to Administrator/System Manager only; AUTH-ADR-001 v1.10 §8.1, TPR v0.11 and STD-TPL-IMP-001 v1.0 §10 add Procurement Officer and HOPF | AUTH v1.10 prevails | B5 |
| R5 | No document names the "release owner" who resolves concerns and supersedes or withdraws a release (STD-TPL-IMP-001 v1.0 §10 "Controlled release owner only") | No Desk role. Deployment-only bench/Make commands record the named owner as a mandatory argument | B5, B8 |
| R6 | Artboards vs STD-TPL-001 v0.10 §11: Blockers lifted above the sections (§11.3 puts them in Verification); "First release" vs §11.5 "Compared with release 1.0 … Breaking"; every check Incomplete vs §11.5's Passed rows; eyebrow, rail, 390 px cards, open coverage/change panels and loading state not drawn | Board wins on layout and order. The projection (real data) wins on values. Undrawn states are built from §11 text and registered as fidelity departures | B6 |
| R7 | STD-TPL-001 v0.10 §11.2/§11.3 show five UI coverage buckets; §13.3 defines eight `treatment` values; no mapping exists, and the §11.5 counts do not reproduce from the register (§3.1) | The validator derives bucket counts from register data by a declared mapping stored in `document_summary`. The §11.5 figures are design-fixture values only, and the UI shows real counts | A4, B6 |
| R8 | CFG v0.14 labels `BDS-GOODS-IT-V1` the Bid Workspace renderer; no document-renderer profile identity exists | One `renderer_profile_id` with two adapter kinds: `document` (wkhtmltopdf 0.12.6.1 patched Qt) and `bid_workspace` (declared control/composition vocabulary and health check) | B4 |
| R9 | `TDR-138016` is bound to `ce65430f…` under the old digest rule; STD-TPL-IMP-001 v1.0 §14: "A migration must prove their exact template identity and digests or mark them legacy/read-only" | Mark legacy/read-only outside the new publication path; no guessed backfill | B7 |
| R10 | The register's CFG-CHG-002 entry says scope "STD Templates inspection" and action "implement … STD Templates settings"; CFG v0.16 §1/§9 and STD-TPL-001 v0.10 §11.6 say CFG owns no template inspection | Follow the document text; flag the register entry for correction | — |
| R11 | Stale references: BDS v0.7 cites STD-TPL v0.9, TPR v0.10 and AUTH v1.9; CFG v0.16 cites STD-TPL v0.9, KT-STD v1.7 and AUTH v1.9; G1-REG-001 v1.1 §5 requires current references | Report as required corrections in those documents; no effect on build | — |
| R12 | STD-TPL-IMP-001 v1.0 §9 / STI10-AC-012 block "Bid start" for unpublished Tenders, but Bid start only occurs on published Tenders. It is not stated whether a supplier may start a Bid on a published Tender whose release was later withdrawn | Out of this cycle's build (BDS owns Bid start). Record for BDS; proposed reading: published Tenders keep their exact release and Bid start continues | — |

## 5. Phases

### Phase 0 — Documents

- **Deliverables:** this plan and the tracker; a pointer banner on `STD-TPL-001_IMPLEMENTATION_TRACKER.md`.
- **Checks:** personas confirmed from `.env.ui`: a Procurement Officer, a HOPF, a System Manager and one denied user.
- **Gate STI-G00.**

### Phase A — Construct the release 1.1 pack

Working folder: `docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1/`. Follow STD-TPL-001 v0.10 §13. Curation only: this phase creates no DocType, route or permission.

| Step | Work | Spec |
|---|---|---|
| A1 | Update the review record preconditions (document versions, source URL, commit, participants). Fix one opaque `release_id` (format `stdr-` + lowercase UUID4, a new identifier for owner review) | §13.1, §13.5 |
| A2 | Bring the three registers to the exact §13.3 columns. Add `structured_rule_id` to every Supplier-response row. Close the 6 "Draft checked" rows or record them as blockers. Proposed register changes go to `open_issues.md` first | §13.3 |
| A3 | `06_runtime/product_profile.json`: supported and rejected use, 5 tasks, controls (including controlled multi-select and structured ports), compositions, named validations, `EVG-ELIGIBILITY`, `EVG-TECHNICAL-COMPLIANCE`, `EVG-FINANCIAL`, `EVG-AWARD`, contract destinations. `response_rules.json`, `downstream_rules.json` (exactly one mapping per rule) and `addendum_identity_rules.json` | §13.5.1–13.5.4 |
| A4 | The shared compiler is written in B3 first. Then add `04_fixture/build_definition_fixture.py` as a thin adapter, `06_runtime/moh_published_bid_definition_expected.json`, the 5 `reservation_variants/*` pairs, and the 4 addendum fixtures inside the validator. Re-render the MoH HTML/PDF through the registered document adapter | §13.7 |
| A5 | `06_runtime/validate_release.py`, covering all 21 §13.8 checks, the deterministic `validation_report.json` and `release_gates.json` (all 17 §14.2 gates; a missing gate counts as Pending). Also the generated `release_change_report.json` against release 1.0 | §13.8, §13.9 |
| A6 | `06_runtime/release_manifest.json` with the exact field list. `bundle_digest` is SHA-256 over sorted `path\0digest\n`, excluding the manifest. Record the manifest file digest in the review record | §13.9 |
| Stop | **Gate D** (supplier experience plus procurement/legal) and **Gate E** (`APPROVE EXACT MANIFEST`) are owner stops. Phase B continues against the Candidate | §13.7, §13.10 |

Inputs for A3:
- `STD-TPL-001_Bid_Response_Definition_Proposal_IT-EQUIPMENT-OPEN-V1.md`;
- the existing `serializer.py` projections (reference only, not authority);
- the coverage and forms registers.

Every identifier and wording in the runtime assets that no source supplies is listed as new content for owner review.

### Phase B — Runtime (`kentender_procurement/std_templates/`)

| Step | Work | Spec |
|---|---|---|
| B1 | DocTypes `Installed STD Release`, `Installed STD Release Asset` (child) and `STD Template Concern`. Controllers are immutable (install flag guard, as in `supported_tender_template.py`). Lifecycle changes append audit events. Test module with purge cleanup | IMP §4 |
| B2 | `services/installer.py`: staging; path-traversal, symlink, duplicate and undeclared-file rejection; digests; schema versions; adapter check; gates; owner decision; private Files (pattern from `tenders/services/documents.py`); one transaction; idempotent. The status decision follows R2. Package copy at `kentender_procurement/std_releases/it_equipment_open_v1/1.1/`, with a byte-match test. `make std-release-install SITE=`. Remove the `after_migrate` auto-install (`hooks.py:560-564`) | IMP §5 |
| B3 | `std_templates/compiler/`: pure Python with no `frappe` import (enforced by a test). Canonical JSON with defined decimal and date formats (adapted from `jcs.py`). Identity tuple and `goods_group_id`. Typed errors. Golden vectors. CLI-vs-production parity | IMP §7; STD-TPL-001 §13.6–13.7 |
| B4 | `std_templates/renderers/`: registry keyed by `renderer_profile_id + supported_renderer_version`. The document adapter wraps the existing renderer and checks, pins the engine version and adds a health check. The bid-workspace adapter declares its vocabulary. There is no fallback | IMP §8; R8 |
| B5 | Services: list, detail, coverage (paged and filtered), change report, preview, review-pack download, concern create/list, compatibility, error codes, audit. Resolve, supersede and withdraw are command-line only (R5). Thin whitelisted API with `parse_json` guards and not-found-as-data. Access through `kentender_core/services/authorization.py` | IMP §6, §10, §12, §13; AUTH v1.10 §8.1 |
| B6 | Vue page `std-templates` (list and detail), ported from the artboards class-for-class. Rail, sidebar row with a role condition for the four roles, `workspace_permissions.py` maps. Coverage and change details are server-paged. Concern dialog. Technical details. 390 px cards. Filters and section kept in the route | STD-TPL-001 §11; IMP §11 |
| B7 | Tenders cutover. `template_binding.py` goes through the registry; `StartTender` requires Available; later steps require Available or Superseded plus integrity and adapter checks; Withdrawn is blocked. Add fields `template_key`, `template_release`, `product_profile_id`, `renderer_profile_id` and `supported_renderer_version`. Both compatibility services use `CheckSTDReleaseCompatibility`. "View STD Template" link. Legacy patch for `TDR-138016`. The canonical `tenders` seed stage stops clearly while 1.1 is a Candidate | TPR v0.11 §4.1–4.2, §5.3, §7, §8; IMP §9 |
| B8 | Supersede/withdraw commands; affected-Tender projection; `ListTendersAffectedBySTDRelease` | IMP §9 |
| B9 | Retire and archive: `std_configuration/`, `Supported Tender Template`, old `tender_templates/`, the 9 stale roles and the stale workspace. Drop patches follow the `retire_std_engine_cleanup` precedent, preceded by a repo-wide search for DocType names and callers. Close CFG FU-18 | OD4 |
| B10 | Release evidence: AC map, runbook, full regression, persona pass | IMP §15–16 |

**Not in this cycle** (owner is TPR-CHG-001 v0.11):
- wiring `BuildPublishedBidDefinition` into `TenderPublication`;
- the addendum successor definition (TPR-IMP-057, TPR-IMP-071).

This cycle supplies the callable compiler and proves parity.

## 6. Verification

- **Python, test-driven per row:**

  ```bash
  bench --site kentender.midas.com run-tests \
    --app kentender_procurement --module kentender_procurement.std_templates.tests.<module>
  ```

  Every run is followed by a purge, because this bench has no test rollback.
- **Pack:**
  - `python 06_runtime/validate_release.py --root . --write-report 05_review/validation_report.json` must pass every check except the owner-gated ones, which report Pending;
  - the fixture CLI must reproduce the expected definition byte for byte.
- **Frontend:**
  - a vitest `std-templates` project and `*.fidelity.spec.js`, registered in `make ui-structure-gate`, with departures in `tests/ui/fidelity/departures/std-templates.js`;
  - Playwright specs under `tests/ui/smoke/std_templates/` and `tests/ui/smoke/design-fidelity/std-templates-fidelity.spec.ts`, run as real personas;
  - `make ui-queue-check` first. Never run Playwright and the Python suite at the same time.
- **Live check:**
  - install, then hard-refresh `/app/std-templates`;
  - confirm Unavailable with the real blockers;
  - confirm Start Tender is refused with the link;
  - confirm the bundle hash changed after the build.
- **Checkpoints:**
  - Tenders and Requisitions module tests after B7;
  - `make validate-links` and migrate after B9;
  - `make seed-canonical THROUGH=requisitions` plus validate.

## 7. Owner questions

| # | Question | Default until answered |
|---|---|---|
| Q1 | Confirm OD1: build the missing `06_runtime`, fixtures and review JSON from the existing 01–05 candidate | Build them (Phase A) |
| Q2 | Approve STD-TPL-001 v0.10 and STD-TPL-IMP-001 v1.0, or authorise building against the proposed text | Phase A/B wait |
| Q3 | Rulings R2–R9 | Proposed defaults in §4 |
| Q4 | Who acts as the named release owner in `make std-release-*` commands? | The Project Owner (bnganyi) |

**Answered 25 September 2026** (owner's words): Q1 "Confirmed"; Q2 "Authorised" (build against the proposed text; this is not document approval); Q3 "Accepted" (R1–R12 defaults are binding for this build); Q4 "Confirmed" (bnganyi is the named release owner).
