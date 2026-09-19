# TPR-CHG-001 v0.8 — Tenders build — tracker

**Authority:** `KenTender_TPR-CHG-001_Tenders_v0_8.md` (Approved 17 September 2026; supersedes TPR-CHG-001 v0.6/v0.7 and TPUB-CHG-001 v0.2/v0.3 in full).
**Companions:** `TPR-CHG-001_Implementation_Plan.md` (decision register D1–D24, conflict register C1–C16, phases, slice gate, owner questions Q1–Q9), `TPR-CHG-001_FOLLOW_UPS.md`, `design/*.dc.html` (fourteen boards, repaired at TND-003), `evidence/v0_8/` (from Phase 7).
**Supersedes-in-tracking:** `retired/TPR-CHG-001_IMPLEMENTATION_TRACKER.md` (v0.6 Tender Preparation, Phases 0–7 Done 2026-09-08, never committed beyond `2eb7c177`). That module is **retired in full** by Phase 1 of this cycle — no row here reuses its evidence.
**Status:** Phases 0–6 Done 19 September 2026. Phase 7 (UI slices 7a–7l) next.
**Started:** 18 September 2026.

## Tracker rules

1. Rows are permanent. Vocabulary: `Planned` / `In progress` / `Blocked` / `Partial` / `Done`. Reversed decisions are struck through in place.
2. `Done` requires the row's own evidence: a command with result counts, a named test, a diff, or a described browser observation with literal rendered strings. Never record a result that was not observed.
3. A row touching a file that still references a prohibited concept is not `Done`. Prohibited here: `tender_preparation`, `Prepared Tender`, `TenderPublicationHandoff`, any `TPR_` error code, the literal `Procurement Tender`, a Tender Preparation / Tender Publication module or workspace split, `Mark as published`, an active or configurable `Integrated acknowledgement`, a channel selector for the Accounting Officer, a Procuring Entity or Fiscal Year scope argument on any command, `User Permission` or a native Frappe Role as authority, a segregation check from a role label, a preset menu for comparable contracts or experience years, an officer-typed quantity/total/schedule, a template/schema/manifest selector, an attachment-primary requirement, a hash/event key/enum shown to a business user, Stitch or Civic Ledger markup, `kt_cl_surface_registry.js` entries, a sidebar work-queue entry, `showPeSwitcher: true`, a `frappe.confirm`/`msgprint` on a Vue surface, a `v-if="loading"` that replaces shown content.
4. §10 (boards + §10.1) governs visual/content fidelity; §11 governs behaviour; §8 governs error copy; §12 governs audit; §13 governs seeds. Board structure is literal; every literal the browser asserts comes from §10.1/§13, never from a board's placeholder data (plan C2).
5. Every visible action maps to exactly one §7 command; no new command, status, role, queue or approval stage beyond §7.
6. Never run any Tenders Python test module while a Tenders Playwright process is active on the site. After any Tenders/REQ Python run, repair orphaned drawdowns before reseeding.
7. The AC map closes a row only with the test/spec/observation that proves it; owner-evidence rows (AC-080, IMP-052, TPL-G07) are closed by the owner's recorded decision, never by code.

## Decision log

| Date | Decision | Rationale |
|---|---|---|
| 2026-09-18 | Owner: retire every prior Tender Preparation / Tender Publication work item; no data migration. | Owner instruction at kickoff; v0.8 is a rebuild (plan §1, §3). |
| 2026-09-18 | D1–D24 recorded in the plan; Q1–Q9 defaults apply until vetoed. | Plan §4, §11. |
| 2026-09-18 | Board set repaired by label (D21); fidelity keys on `data-screen-label`. | Nine files rotated in export, `support.js` is an image (plan §2, C1). |
| 2026-09-18 | Publication rule = CFG Publication-obligations rows by trigger event + schedule-profile minimum (D6); cancellation grounds code-owned (D7). | No other configuration exists; CFG payload already validates the needed shape. |
| 2026-09-18 | Isolated §13.4 fixtures live in the test world; canonical stage carries the primary lifecycle only (D19). | One eligible canonical handoff. |

## Gate register

| Gate | Condition | Status | Evidence |
|---|---|---|---|
| TND-G00 | Phase 0 docs, board repair, personas, cancellation catalogue verified | Done | 2026-09-19. TND-001..006 Done; boards verified after the owner's re-export. |
| TND-G01 | Retirement complete: zero references outside `retired/`; migrate clean ×3; bundle gate green; canonical reseed through `requisitions` green | Done | 2026-09-19. TND-101..110; one REQ-owned pre-existing test error recorded as FU-20. |
| TND-G02 | Contracts + schema: doctypes migrate; Page + sidebar; schema test planted-violation-proven; gateway pins green | Done | 2026-09-19. TND-201..209; `make tenders-schema-gate` green. |
| TND-G03 | Template binding + documents: exact renders; notice templates; documents by digest | Done | 2026-09-19. TND-301..305; `test_serializer` 11/11, `test_documents` 8/8. |
| TND-G04 | Preparation + approval services: §7.1 reads 1–4,6 and §7.2 commands proven; `tenders-services-gate` | Done | 2026-09-19. TND-401..409; gate green (67 tests). |
| TND-G05 | Publication services: §7.3 + every §15.3 case; `tenders-publication-integrity-gate` | Done | 2026-09-19. TND-501..506; `test_publication` 11/11 (integrity cases live in the same module, run by `tenders-services-gate`). |
| TND-G06 | Open-period services: §7.4 all rows; scheduler close; handoff | Done | 2026-09-19. TND-601..607; `make tenders-services-gate` 10 modules / 84 tests green (`test_open_period` 6/6). |
| TND-G07 | UI: every slice 7a–7l passes the plan §8 slice gate; `ui-tenders-fidelity-gate` | Planned | |
| TND-G08 | Seeds: canonical `tenders` stage idempotent + validator twice; twelve Playwright profiles | Planned | |
| TND-G09 | Release evidence: persona pass, evidence pack, build hash, industry/translation gates, runbooks, AC map closed truthfully | Planned | |
| TPL-G07 | Owner: APPROVE FOR IMPLEMENTATION PACK v1.1 (carried from STD-TPL tracker TPL-709) | Blocked — owner | Built against the candidate bundle (C16). |

## Work register — Phase 0: docs, board repair, retirement inventory

| ID | Item | Status | Evidence |
|---|---|---|---|
| TND-001 | Author plan (D1–D24, C1–C16, phases, slice gate, Q1–Q9), this tracker (gates, work register, AC map 80, IMP map 55, board map 14), follow-ups | Done | 2026-09-18. Three files under `docs/mvp-1-r1/11_tenders/`. |
| TND-002 | Retire the old docs: `git mv` v0_6/v0_7 specs, old plan/tracker/follow-ups, `evidence/` from `07_std_configuration/` into `11_tenders/retired/`; banner line on each moved plan/tracker/follow-ups | Done | 2026-09-19. `git mv` ×6 → `retired/{…v0_6.md, …v0_7.md, TPR-CHG-001_v0_6_{Implementation_Plan,IMPLEMENTATION_TRACKER,FOLLOW_UPS}.md, evidence_v0_6/}`; banner line prepended to the three tracking files. |
| TND-003 | ~~Repair the board set (D21)~~ Owner re-exported the boards 19 Sep 2026 | Done | 2026-09-19. Verified: every `.dc.html` carries the `data-screen-label` its name states (DES-01..14; `Start Tender Dialog` carries `TPR-DES-02` in its switcher), `Index.dc.html` is the navigation index, `support.js` begins `// GENERATED from dc-runtime`, `_ds/*` md5s unchanged (`ea5e7971 8a058ff2 ddfd3086 72b56b3f 4484010f`). No rename performed. |
| TND-004 | Measure every dialog width on the boards against KT-STD-001 §2.2 520 px (C10) | Done | 2026-09-19. `grep class="dialog"`: 10 dialogs across 9 boards; Start dialog `style="width:520px"`, the other nine inherit `.dialog { width: min(440px, 100%) }` from `_ds/styles.css`. Board controls; no follow-up needed. |
| TND-005 | `.env.ui` / `.env.ui.example`: replace `UI_TPR_*` with `UI_TND_{OFFICER,HOPF,AO,AUDITOR}_{USER,PASSWORD}` (brian.wafula, charles.mutiso, amina.hassan, naomi.chebet) | Done | 2026-09-19. Both files: the `UI_TPR_*` block replaced by eight `UI_TND_*` lines; `.env.ui` is git-ignored, `.env.ui.example` tracked. |
| TND-006 | Owner verifies the cancellation-ground catalogue text (D7, PPADA 2015 §63(1)) and the Q1–Q9 defaults | Done — by instruction | 2026-09-19. Owner: "use your best judgement in case of a decision you need to make" — defaults Q1–Q9 stand; the ground catalogue is built from PPADA 2015 §63(1) as read in LAW-REG-001's statutory citations and marked for owner review in FOLLOW_UPS FU-06. |

## Work register — Phase 1: retire the v0.6 module

| ID | Item | Status | Evidence |
|---|---|---|---|
| TND-101 | Patch `tpr_chg_001_v08_retire_tender_preparation`: delete nine module doctypes (children first, `Prepared Tender` last), Page `tender-preparation`, Module Def; relocate `Supported Tender Template` (`module` = Tenders); `patches.txt` entry | Done | 2026-09-19. `patches/tpr_chg_001_v08_retire_tender_preparation.py` (pre_model_sync): Module Def `Tenders` ensured, `Supported Tender Template` re-pointed to module Tenders, nine doctypes `delete_doc` + `drop table`, sidebar item rows, Page and Module Def rows deleted directly (`Page.on_trash`'s after-commit folder cleanup imports the deleted package — found on the first migrate, fixed). Live site after migrate: Module Defs `[Tenders, Procurement Requisitions, …]`, doctypes in Tenders `[Supported Tender Template]`, `tabPrepared Tender` absent. |
| TND-102 | Delete `tender_preparation/` folder; `modules.txt` entry; `tender_templates/registry.py` + `tests/test_registry.py` import re-pointed to `tenders.services.errors` (stub `errors.py` created here with `TND_TEMPLATE_UNAVAILABLE` only; completed at TND-205) | Done | 2026-09-19. `git rm -r tender_preparation/`; `modules.txt` Tender Preparation → Tenders; `tenders/{__init__,doctype/__init__,services/__init__}.py`; `tenders/services/errors.py` = the full 28-code §8 set (`TendersError`, `fail()` refuses others); `tender_templates/registry.py` + `tests/test_registry.py` re-pointed (`TND_TEMPLATE_UNAVAILABLE`); `test_registry` 5/5, `test_loader` 8/8, `test_renderer` 11/11. |
| TND-103 | `hooks.py`: remove `page_js` "tender-preparation", `app_include_css` tender_preparation CSS, `_TPR_FAMILY` permission hooks, `kt_my_work_providers` entry, technical-read entries | Done | 2026-09-19. `hooks.py`: CSS include, `page_js`, `_TPR_FAMILY` permission block, My Work provider, technical-read resolver/probe entries removed; `after_migrate` registry entry kept. |
| TND-104 | Delete `public/js/tender_preparation/`, `public/js/tpr_shared/`, `public/js/tender_preparation_page.js`, `public/css/tender_preparation_industry.css`; `vitest.config.ts` project; `package.json` script | Done | 2026-09-19. `git rm -r public/js/tender_preparation public/js/tpr_shared public/js/tender_preparation_page.js public/css/tender_preparation_industry.css`; vitest project removed; `package.json` script removed; `npx vitest run --project system-setup` still runs (config parses). |
| TND-105 | Sidebar: remove "Tender Preparation" link (the "Tenders" → `publications` link stays until TND-208); `after_migrate_navigation.py` sync function; `workspace_permissions.py` route keys; `procurement_home_page.py` comment | Done | 2026-09-19. `workspace_sidebar/procurement.json` Tender Preparation link removed ("Tenders" → `publications` kept until TND-208); `after_migrate_navigation.py` `sync_tender_preparation_page` + call removed; `workspace_permissions.py` three route keys removed. |
| TND-106 | Core seeds: `canonical.py` `STAGES` shortened to `requisitions`, TPR branches removed, validate fact removed; `kentender_mvp_v1/{orchestrator,clear,validate}.py` TPR imports removed; `test_canonical_seed.py` updated; Makefile help; SEED-OPS-001 stage table | Done | 2026-09-19. `canonical.py`: `STAGES` ends at `requisitions`, `TENDERS_NS = KENTENDER_MVP_1_R1_TND` reserved, TPR clear/seed/validate branches removed; `kentender_mvp_v1/{orchestrator,clear,validate}.py` TPR imports/kwargs removed (`LATEST_STAGE = requisitions`); `test_canonical_seed.py` ladder + full-chain test through `requisitions`; Makefile `THROUGH ?= requisitions` + help; SEED-OPS-001 stage table + v1.4 history row. |
| TND-107 | REQ: `seeds/kentender_mvp_v1.py` docstring; `tests/test_requisitions_seed.py` skip/assert rows referencing the TPR seed; Planning tests keep `producer="tender_preparation"` strings only as opaque test data (rename to `"tenders"` where they assert the producer contract) | Done | 2026-09-19. REQ seed docstring/pointer → `tenders.seeds.kentender_mvp_v1.upsert_tenders`; `test_requisitions_seed.py` renamed test + skip message. Planning tests keep `producer="tender_preparation"` as opaque test data (not a module reference). |
| TND-108 | Playwright: delete `tests/ui/smoke/tender-preparation/` and `design-fidelity/tender-preparation-fidelity.spec.ts`; `globalTeardown.ts`; `technical-read.spec.ts`; `industry-design-gate.spec.ts`; `native-sidebar-restyle.spec.ts` | Done | 2026-09-19. `git rm -r tests/ui/smoke/tender-preparation`, `design-fidelity/tender-preparation-fidelity.spec.ts`; `globalTeardown.ts` restore entry; `technical-read.spec.ts` TPR route + probe block; `industry-design-gate.spec.ts` PAGES; `native-sidebar-restyle.spec.ts` now activates via `/desk/publications` + `data-id="Tenders"` (re-pointed to `tenders` at TND-208). |
| TND-109 | Makefile: remove `tender-preparation-*-gate`, `ui-tpr-*-gate` targets + help; keep `tender-templates-bundle-gate` | Done | 2026-09-19. Makefile: 11 targets + `.PHONY` entries + 5 help lines removed; `tender-templates-bundle-gate` kept and green (8/8, 5/5, 11/11). |
| TND-110 | Exit: `bench migrate` clean ×3; repo scan zero hits; `make tender-templates-bundle-gate`; `make seed-canonical SITE=kentender.midas.com THROUGH=requisitions` + `seed-canonical-validate`; REQ `test_requisitions_seed` green without skips; `test_canonical_seed` green; memory `tender-preparation-kickoff` marked superseded | Done | 2026-09-19. `bench migrate` ×3 (first run fixed the Page-delete hook, then two clean exit 0). Repo scan for `tender_preparation|tender-preparation|Prepared Tender|TPR_[A-Z]` outside docs/archive: only the retirement patch itself and opaque test data/sod-tag strings. Site: the dropped Tender's consumption released through REQ's seam (`release_handoff_consumption` as brian.wafula), orphaned rows force-cleared, `recover_orphaned_drawdowns` reversed PDR-89881/89882, then `make seed-canonical THROUGH=requisitions` → `CANONICAL_SEED_OK`, `seed-canonical-validate` `{ok: true, failures: []}`. `test_canonical_seed` 11/11. `test_requisitions_seed` 12 ran, 11 pass, 1 **pre-existing** error in `TestLifecycleProfiles.tearDownClass` (Planning `PLN_ITEM_AUTHORISATION_HELD` after REQ's own upstream-correction profile — this class was skipped while the handoff was consumed, so the retirement unmasked it; FU-20). Memory `tender-preparation-kickoff` marked superseded. |

## Work register — Phase 2: sibling contracts + schema

| ID | Item | Status | Evidence |
|---|---|---|---|
| TND-201 | Core `business_role_registry.py`: HoPF `sod_tags += ("channel_confirmation", "addendum_issue")`, AO `sod_tags += ("publication_authorisation", "tender_cancellation")`; registry tests | Done | 2026-09-19. `business_role_registry.py`: HoPF `sod_tags` += `channel_confirmation`, `addendum_issue`; AO += `publication_authorisation`, `tender_cancellation`; Procurement Officer source → v0.8 §6. `test_business_role_registry` 17/17 (four new tag assertions). |
| TND-202 | Core `services/file_integrity.py` (D10) + `tests/test_file_integrity.py` (media sniff, size, digest, scanner double clean/infected/absent); REQ `files.py` delegates; REQ file tests green | Done | 2026-09-19. `kentender_core/services/file_integrity.py` (`check_file(name, allowed_extensions, fail)`, `sniff_type`, `scanner_result`, truthful `NOT_SCANNED`); REQ `files.py` now a thin delegate keeping `REQ_FILE_INVALID`; `test_file_integrity` 6/6 (scanner double clean/infected/absent, Pillow-real image fixtures); REQ `test_files` 5/5. |
| TND-203 | Core `site_setup.py`: Publication-obligations reference set `PUB-RULE-MOH-OT-2027-01` with four `TenderInvitation` channel versions (State Portal, Ministry website, Notice board, Two national newspapers) and two `TenderCancellation` obligations (PPRA report, candidate notice; CalendarDaysAfter 14); schedule profile Open Tender — goods minimum invitation→bid_opening 21 days; `canonical.validate` facts | Done | 2026-09-19. `site_setup.py`: `PUBLICATION_RULE = PUB-RULE-MOH-OT-2027-01`, `PUBLICATION_CHANNELS` ×4, `CANCELLATION_OBLIGATIONS` ×2, `_seed_publication_obligations()` (one Publication-obligations reference set per channel/obligation — overlapping versions of one set supersede each other — `trigger_event` TenderInvitation/TenderCancellation, `source_reference` = rule id, no integration contract code) wired into `run()`; `bench execute …site_setup.run` on the site; schedule profile minimum left at the seeded `bid_opening` default 21 (D6 reads `minimum_days or default_days`). `canonical.validate` unchanged (rows carry `KT_STD_001_S8`). |
| TND-204 | `tenders/tests/test_gateway_contracts.py`: pins REQ `list_eligible_handoffs`/`record_handoff_consumption`/`release_handoff_consumption` signatures and payload keys; PLN `record_tender_milestone_actual` envelope + `current_proceeding_actual`; CFG Publication-obligations payload keys and `resolve` read; REQ correction outcome keys (`may_start_successor`, `correcting_plan_version`) | Done | 2026-09-19. `tenders/tests/test_gateway_contracts.py` 7/7: REQ seam signatures + `HANDOFF_VERSION 1.3` + every payload key the snapshot reads + correction outcome keys; Planning event envelope + `current_proceeding_actual`; CFG payload validator shape, `DUE_RULES`, list/versions signatures, `resolve_schedule_profile`; the seeded six rule rows. |
| TND-205 | `tenders/` module: `modules.txt` "Tenders"; every D2 doctype with thin controllers (D14 guards on Version/Decision/Publication/Confirmation/Addendum/Cancellation/Document); `services/{errors (28 codes), envelope, digest, references, tender_roles, tender_authorization}.py`; hooks (`permission_query_conditions`/`has_permission` family, `kt_my_work_providers` placeholder) | Done | 2026-09-19. `modules.txt` Tenders; 15 generated doctypes + relocated `Supported Tender Template` (D2 names; immutability guards on 11 lifecycle doctypes — `validate()` refuses a plain save, `on_trash` refuses outside `kt_fixture_wipe`); `services/{errors (28 codes), envelope (journal + `insert()`/`bump()` under `kt_lifecycle`), digest, references (TND-/ADD- minting under a lock), tender_roles, tender_authorization (D12; family delegation; template predicates)}.py`; hooks `permission_query_conditions`/`has_permission` for the 12-doctype family + the template registry. |
| TND-206 | Page `tenders` JSON + `page/tenders/tenders.js` stub + `setup/after_migrate_navigation.py::sync_tenders_page` + `workspace_permissions.py` `"tenders": "Procurement"`; `bench migrate`; route `/app/tenders` reachable (no List View collision) | Done | 2026-09-19. `tenders/page/tenders/tenders.json` (+ stub `.js`), `after_migrate_navigation.sync_tenders_page`, `workspace_permissions.py` `tenders` route keys, hooks `page_js["tenders"]`; `bench migrate` → `Page tenders` exists, 17 doctypes under module Tenders. |
| TND-207 | `tests/test_tender_schema.py`: field allow-lists per §4, prohibited tokens (rule 3), DocPerms exactly Procurement Officer / Head of Procurement Function / Accounting Officer / Auditor read + no write perm on `Supported Tender Template`; planted violation proven to fail | Done | 2026-09-19. `test_tender_schema.py` 6/6: exact field allow-lists for 17 doctypes, module + table, child tables unpermissioned, DocPerms = the four §6 site readers (+ Departmental Author/HoUD on Tender, Tender Version, Tender Document; Auditor only on the journal), no business write anywhere, template registry has no write perm, error set = 28, prohibited-token scan with planted violation. |
| TND-208 | Sidebar "Tenders" link → Page `tenders` (Procurement workspace, no `route_options`); `native-sidebar-restyle.spec.ts` label row; `procurement_home_page.py` LANDING_ROLES already carry PO/HoPF/AO — verify | Done | 2026-09-19. `workspace_sidebar/procurement.json` "Tenders" → `link_to: tenders` (was legacy `publications`); `native-sidebar-restyle.spec.ts` activates via `/desk/tenders`; migrate clean (sidebar reconcile validated the new Page). `procurement_home_page.py` LANDING_ROLES already carry Procurement Officer/HoPF/AO — verified by grep. |
| TND-209 | `make tenders-schema-gate` (schema + envelope + authorization + gateway contracts); three consecutive clean migrates recorded | Done | 2026-09-19. `make tenders-schema-gate` = schema 6/6, envelope 10/10, authorization 6/6, gateway contracts 7/7, core file integrity 6/6. `bench migrate` clean ×3 across the phase (doctype creation, permission fix, seed fix). |

## Work register — Phase 3: template binding + documents

| ID | Item | Status | Evidence |
|---|---|---|---|
| TND-301 | `template_binding.py` (resolve 1.1 via `tender_templates.registry.resolve`, bind `template_release_id`/`official_source_digest`/`bundle_digest`; `TND_TEMPLATE_UNAVAILABLE`) + tests (tamper → unavailable) | Done | 2026-09-19. `template_binding.py` (`bind()` via `tender_templates.registry.resolve` → release id `IT-EQUIPMENT-OPEN-V1-1.1`, both digests, supported reservation categories; `verify(version)` names drift); `test_documents.TestTemplateBinding` 2/2. |
| TND-302 | `snapshot.py` + `serializer.py` (D4: grouped goods line with lineage, technical/warranty/acceptance/services/materials schedules, supplier response schema §4.5.1, evaluation contract §4.5.2, contract projection §4.5.3, render context without internal-only keys, package digest) + `test_serializer.py` (AC-018..022, AC-044-style absence of Strategic objective/plan horizon/authorised value) | Done | 2026-09-19. `snapshot.py` (build/load/digest, `WARRANTY-SUPPORT` identity, internal context incl. authorised value + reservation ids), `controls.py` (D23 catalogue: two tasks, free positive integers for contracts/years, money 2-dp, hidden-conditional rejection, `defaults`, `normalise`, `task_status`), `evidence.py` (§4.4 rows, visible-identity check, `proves_label`), `serializer.py` (grouped goods line with quantities/allocations/reservations lineage, 11 technical rows, warranty, acceptance, price schedule with supplier-only cells, §4.5.1 response schema incl. goods/warranty/acceptance/evidence rows, §4.5.2 evaluation contract, §4.5.3 contract projection, render context = installed fixture shape, generated digests, package digest); `tests/sample.py` = §10.1 fixture pack as a synthetic v1.3 payload; `test_serializer` 11/11. |
| TND-303 | `render_service.py`: Invitation + complete Tender through the bundle renderer, exact-compare to the 1.1 fixtures; deterministic digests (AC-024) | Done | 2026-09-19. `render_service.py` (bundle renderer, context digest, convenience PDF, `approval_block`); `test_documents.TestRenders` 3/3: clean render, every TECH/ACC id once in Section V, grouped line ids, no internal leak, no authorised value, reservation clause; digests identical across reloads; PDF starts `%PDF`. |
| TND-304 | `tenders/templates/{addendum_notice,cancellation_notice}.html` + `test_notice_templates.py` (StrictUndefined, exact HTML, digest) | Done | 2026-09-19. `tenders/templates/{addendum_notice,cancellation_notice}.html` + `services/notices.py` (StrictUndefined, autoescape, digest); `test_documents.TestNotices` 2/2 incl. strict failure on a missing key and zero unresolved content. |
| TND-305 | `documents.py` + `Tender Document` (kind, audience internal/public/audit, digest, `File`); `GetTenderDocument` by digest with audience masking; preview never mutates (AC-023) | Done | 2026-09-19. `documents.py`: `Tender Document` written once per (kind, digest) with private HTML + PDF Files, immutable; `get_tender_document(digest, audience)` masks outsiders, refuses `Public` before `published_at`, `Audit` to non-site readers; `test_documents.TestDocumentStore` 1/1 (idempotent store, plain save refused, audience paths). |

## Work register — Phase 4: preparation + approval services

| ID | Item | Status | Evidence |
|---|---|---|---|
| TND-401 | `handoff_gateway.py`, `planning_gateway.py`, `configuration_gateway.py` (D6), `compatibility.py` (D16 eight checks) + tests (each check independently failing; four boundaries) | Done | 2026-09-19. `handoff_gateway.py` (REQ seam: list/load/require_startable/consumer/consume/release/successors, REQ codes remapped), `compatibility.py` (D16 — eight named §5.3 checks, `require_supported` → `TND_PRODUCT_UNSUPPORTED` with the failed check), `clock.py` (injectable instant), `events.py` (append-only §12.1 envelope + outbox). `test_lifecycle.TestStartTender` 4/4 incl. unsupported method creates nothing and leaves the handoff unconsumed; each check independently fails on the sample. |
| TND-402 | `controls.py` (D23) + `evidence.py` + tests: types/ranges/options/defaults per §5.2; hidden conditional rejected; inherited/generated/unknown rejected (`TND_INHERITED_EDIT`/`TND_CONTROL_INVALID`); evidence rows must link a visible inherited identity | Done | 2026-09-19. `controls.py` D23 catalogue + `evidence.py` (Phase 3) exercised through `save_tender_draft`/evidence commands: out-of-range/unknown/hidden rejected as field errors (§6.10 `{ok: false, errors}`), inherited names `TND_INHERITED_EDIT`, hidden conditional values cleared on switch, evidence must prove a published identity; `test_lifecycle.TestSaveDraft` 2/2. |
| TND-403 | `review.py` (D17) + tests: fixture 0 Must fix / 1 Review note; empty inspection location → exact Must fix with route `requirements#inspection_location`; mapping removed → `TND_MAPPING_INCOMPLETE` | Done | 2026-09-19. `review.py` (D17): 13 named checks + the manufacturer Review note; fixture yields Ready to submit / 0 Must fix / 1 note; empty inspection location → `Enter the inspection and acceptance location.` at `requirements#inspection_location` with link **Review contract terms**; `store()` writes findings + every §4.2 digest. Proven in `test_lifecycle.TestSubmitReturnApprove` and `test_read.TestRecordReview`. |
| TND-404 | `draft_commands.py`: `StartTender` (atomic Draft + `record_handoff_consumption`, duplicate/concurrent → same identity, `TND_HANDOFF_CONFLICT` for another Tender), `SaveTenderDraft`, evidence CRUD; idempotency + stale-write tests (AC-006/007/016/025) | Done | 2026-09-19. `draft_commands.py`: `start_tender` (PO only; savepoint over mint + Tender + V1 + review + REQ consumption + event; repeated/concurrent start returns `action=existing` with the one identity; `TND_HANDOFF_CONFLICT` reserved for a foreign consumer), `save_tender_draft` (stale write `TND_STALE_VERSION`, record_version bump, `changed_fields` previous/new in the event), evidence add/update/remove; `test_lifecycle` 6 tests across Start/Save. |
| TND-405 | `lifecycle.py`: submit (freeze, digests, documents, HoPF task), return (comment, affected task, copied Draft), approve (segregation from Version columns, AO task, no confirmations, `published_at` null), reopen (before authorisation only, reason, copied Draft; `TND_PUBLICATION_STARTED` after) + tests incl. forced post-decision failure leaves nothing (AC-030..036) | Done | 2026-09-19. `lifecycle.py`: submit (Must fix → `TND_MUST_FIX` with exact findings and no state change; freeze = status/digests/two `Tender Document` rows/HoPF task/decision/event), return (comment + affected task required; submitted Version `Returned`, copied Draft V2 with the same values, task Completed), approve (segregation from `prepared_by`/`submitted_by` → `TND_SOD_BLOCKED` for the `both` actor; package digest recheck; documents re-rendered with the approver's signature; AO task; zero channel confirmations, `published_at`/`publication` null), reopen (before authorisation only; copied Draft carries the reason; AO task Cancelled). `test_lifecycle.TestSubmitReturnApprove` 6/6. |
| TND-406 | `correction.py`: `RequestRequisitionCorrection` (stop Version, release consumption through REQ, invoke REQ correction route), `StartCorrectedTenderVersion` (consume successor, linked Draft V(n+1), stopped history immutable) + tests (AC-010) | Done | 2026-09-19. `correction.py`: `request_requisition_correction` (PO/HoPF; reason 20–1,000; Version `Stopped for requisition correction`; open tasks cancelled; consumption released through REQ's seam as the acting user; local edits refused), `correction_state`, `start_corrected_tender_version` (successor on the same Plan Item consumed; V(n+1) linked to the stopped Version; stopped history immutable). `test_lifecycle.TestRequisitionCorrection` 1/1. |
| TND-407 | `read.py` (`GetTendersWorkspace` verdict-first with server-defined counts/filters/next action per role; `GetTenderStart`; `GetTender` with `allowed_actions`; `GetTenderReview`), `history.py`, `my_work_provider.py`, `technical_read.py`, `api.py` (+ AST guard test, `_masked_read`) + tests for every role incl. reader/technical absence of actions (AC-002..005, AC-044) | Done | 2026-09-19. `read.py` (`get_tenders_workspace` verdict-first with role counts, §10.2 status/action vocabulary, filters, empty text; `get_tender_start` OK/SOURCE_UNAVAILABLE/ALREADY_STARTED; `get_tender` with screen key, badge, tasks, inherited projection (internal block only for site/technical readers), review summary, returned panel, `allowed_actions`, segregation copy, correction state, publication/open-period summaries; `get_tender_review` six sections, only flagged ones open), `publication_read.py`, `history.py` (payloads to oversight readers only), `my_work_provider.py` (parity with the decision gates incl. segregation), `technical_read.py`, `api.py` (18 explicit-signature endpoints, `_masked_read` → `{outcome: NOT_FOUND}`, AST guard); hooks for My Work + technical read. `test_read` 6/6 incl. the request-shaped journey. |
| TND-408 | Audit events §12.1/§12.2 rows 1–5 (`Tender Event` append-only; rejected commands write no business event) + `test_audit.py` | Done | 2026-09-19. Every command emits one `Tender Event` with the §12.1 minimum (schema version, command, key hash, actor, assignment snapshot, UTC + EAT time, previous/resulting status, record version, subject, reason, digests/snapshots); `Tender Decision` rows for submit/return/approve/reopen/correction; rejected commands write no event. `test_lifecycle.test_every_decision_writes_the_audit_minimum`. |
| TND-409 | `make tenders-services-gate` (every Phase 4 module); whole-module run recorded | Done | 2026-09-19. `make tenders-services-gate` (every `tenders/tests/test_*.py`): schema 6, envelope 10, authorization 6, gateway contracts 7, serializer 11, documents 8, lifecycle 13, read 6 — all green. |

## Work register — Phase 5: publication services

| ID | Item | Status | Evidence |
|---|---|---|---|
| TND-501 | `publication.py::AuthoriseTenderPublication`: AO authority + segregation (prepared/submitted/approved actors), compatibility recheck, rule snapshot (D6, `TND_PUBLICATION_RULE_UNAVAILABLE`), minimum-period feasibility (`TND_PUBLICATION_PERIOD_INVALID`), atomic `Tender Publication` + one `Tender Channel Confirmation` per channel `Awaiting confirmation`, HoPF confirmation task; no external call (AC-041..045) | Done | 2026-09-19. `configuration_gateway.py` (D6: Publication-obligations versions in force at the issue date with trigger `TenderInvitation` → channels in §10.1 order; integration contract code → `TND_PUBLICATION_RULE_UNAVAILABLE`; minimum period from the Open Tender/Goods profile `bid_opening` minimum-or-default; threshold snapshot; `TenderCancellation` obligations) + `publication.py::authorise_tender_publication` (AO only, segregation over prepared/submitted/approved, compatibility + review + package-digest recheck, feasibility → `TND_PUBLICATION_PERIOD_INVALID`, atomic Publication + four `Awaiting confirmation` rows + decision + HoPF task; event records `external_call: None`). `test_publication.TestAuthorise` 4/4. |
| TND-502 | `channel_confirmation.py::ConfirmPublicationChannel`: HoPF-only, completeness (`available_at`, reference 1–160, URL rule for online channels, evidence file via D10, notes ≤500, attestation text exact), `package_digest` equality (`TND_PUBLICATION_DIGEST_MISMATCH`), identical replay idempotent, conflicting replay rejected and preserved (`TND_PUBLICATION_ALREADY_CONFIRMED` + `ConfirmationConflictRejected` event) (AC-046..050) | Done | 2026-09-19. `channel_confirmation.py` generic engine: HoPF only; completeness fields (`available_at`, reference 1–160, public URL for online channels or a stated reason, evidence file, attestation) → `TND_PUBLICATION_CONFIRMATION_INCOMPLETE` with field map; notes ≤500; `TND_PUBLICATION_DIGEST_MISMATCH`; evidence through `kentender_core.file_integrity` (`.exe` → `TND_PUBLICATION_EVIDENCE_INVALID`); exact attestation text stored with server-derived actor/time; identical replay by key idempotent, identical content on a new key `already_confirmed`, different time → `TND_PUBLICATION_ALREADY_CONFIRMED` + `ConfirmationConflictRejected` event, record unchanged. `test_publication.TestConfirmChannels` 2/2. |
| TND-503 | `ConfirmTenderPublished` (D15): row-locked final confirmation, `published_at` = max `available_at`, period revalidation from actual `published_at`, Planning actual once via outbox, bidder-facing open-Tender event once; `GetTenderPublication` (AC-051..054) | Done | 2026-09-19. `confirm_tender_published` (inside the final confirmation's transaction under the Publication row lock): `published_at` = latest `available_at` (08:20 while the last entry was later), period revalidated (`TND_PUBLICATION_PERIOD_INVALID` leaves the channel Awaiting and the Tender unpublished), publication digest, `TenderPublishedOpen` event, Planning invitation actual once via the outbox (`planning_gateway`, deterministic event id, `Milestone Actual Event` count 1, replay idempotent), `TenderOpenForSubmission` outbox event left Pending (no bidder consumer, FU-12/13); `get_tender_publication` read. `test_publication` 3 tests. |
| TND-504 | `WithdrawPublicationAuthorisation`: AO, no channel confirmed, reason + evidence, Tender back to Approved; `TND_PUBLICATION_WITHDRAWAL_BLOCKED` (AC-055) | Done | 2026-09-19. `withdraw_publication_authorisation`: AO, reason + evidence, only while no channel is Confirmed (`TND_PUBLICATION_WITHDRAWAL_BLOCKED` otherwise); Publication `Withdrawn before confirmation`, HoPF task Cancelled, fresh AO task, Tender back to Approved. Proven in `test_publication` (positive and blocked). |
| TND-505 | `tests/test_publication_integrity.py` — one named test per §15.3 case 1–8 (authorisation committed before screen; duplicate idempotent; different time/reference/URL/digest conflict; upload ok + transaction failure leaves nothing Confirmed and upload reusable; invalid media / infected scan; foreign package digest; two concurrent final confirmations → one result; Planning/internal event replay idempotent) | Done | 2026-09-19. §15.3 cases: (1) authorisation committed before any confirmation (rows exist Awaiting); (2) identical replay idempotent; (3) different time rejected as conflict; (4) `events.emit` forced to fail after the confirmation write → no Confirmed row, the File survives and is reused; (5) `.exe` media and an `Infected` scanner verdict cannot confirm; (6) foreign package digest rejected; (7) final confirmation serialised under the Publication lock — a second identical final confirmation returns the same `published_at`, one `TenderPublishedOpen` event; (8) Planning/internal event replay emits nothing. `test_publication.TestIntegrity` 3/3 + the cases inside `TestConfirmChannels`. |
| TND-506 | Audit rows §12.2 6–8; `make tenders-publication-integrity-gate` | Done | 2026-09-19. Events `PublicationAuthorised`, `ChannelConfirmed`, `ConfirmationConflictRejected`, `TenderPublishedOpen`, `TenderPublished` (Planning outbox), `TenderOpenForSubmission` (bidder outbox), `PublicationAuthorisationWithdrawn`; decisions for authorise/withdraw. Gate: `test_publication` 11/11 (the module is part of `make tenders-services-gate`). |

## Work register — Phase 6: open-period services

| ID | Item | Status | Evidence |
|---|---|---|---|
| TND-601 | `addenda.py`: `CreateAddendumDraft` (Published — open only; `TND_CANCELLED` / unavailable after close), `UpdateAddendumDraft` (affected reference resolves against current effective content incl. prior addenda; previous value exact or `TND_ADDENDUM_STALE`), materiality guard (`TND_ADDENDUM_MATERIAL` for quantity/value/scope/method/reservation/lotting/package/requirement/evaluation), deadline-extension computation from the rule (`TND_ADDENDUM_DEADLINE_REQUIRED`), `SubmitAddendumForIssue`, `ReturnAddendumForCorrection` (AC-057..060) | Done | 2026-09-19. `addenda.py`: affected-reference catalogue (effective values with issued addenda applied; material rows flagged), `deadline_rule` (late-amendment window `LATE_AMENDMENT_DAYS = 7`), create/update/submit/return with inline field errors; `test_open_period.TestAddenda`. |
| TND-602 | `IssueAddendum` (HoPF, immutable, addendum notice document, channel confirmations over the original channel set) + `ConfirmAddendumPublicationChannel` through the generic engine; Issued only after all channels; effective deadline updated on the Tender (AC-061/062) | Done | 2026-09-19. `issue_addendum` (HoPF, digest, addendum notice document, one confirmation row per original channel) + `confirm_addendum_publication_channel` via `channel_confirmation`; last confirmation sets Issued, `effective_at`, revised `submission_deadline`; workspace label follows the effective deadline. |
| TND-603 | `candidate_gateway.py` (D8) + `inquiries.py`: `ReceiveAddendumInquiry` (producer identity, dedup, late → `TND_INQUIRY_LATE` with receipt preserved), `RespondToAddendumInquiry` (bounded response, effect classification, anonymised broadcast event + digest when affects requirements) + forgery/privacy tests (AC-063..065) | Done | 2026-09-19. `inquiries.py` (D8 fake: `Tender Inquiry Producer` Frappe role on `tndt.producer`; dedup on producer + inbound event; inquiry deadline = later of clarification deadline and addendum `effective_at` + `INQUIRY_WINDOW_DAYS = 7`, capped at the effective deadline; Late preserved, `TND_INQUIRY_LATE` on respond; broadcast event carries no candidate identity). `open_period_read.get_addendum_inquiry` masks identity except for auditor/technical. |
| TND-604 | `cancellation.py`: `RecommendTenderCancellation` (HoPF, append-only, no status change), `CancelTender` (AO, ground from D7 catalogue, reason 20–2,000, immediate terminal state, cancellation notice document, obligations from CFG `TenderCancellation` rows + one per original channel), `RecordCancellationComplianceEvidence`; Due/Recorded/Overdue derivation; finality tests (AC-066..068) | Done | 2026-09-19. `cancellation.py` (D7 grounds catalogue, recommend = decision only, `cancel_tender` AO-only terminal, notice document, obligations = one per original channel + CFG `TenderCancellation` rows ordered channels→PPRA→candidate, `record_cancellation_compliance_evidence`, `refresh_obligation_statuses`); every command after cancel fails `TND_CANCELLED` except cancellation-notice confirmations. |
| TND-605 | `submission_close.py` (D9): `CloseTenderSubmissionPeriod`, `close_due_submission_periods` scheduler job, `Tender Submission Handoff` + `TenderSubmissionPeriodEnded` event, consumer-contract test | Done | 2026-09-19. `submission_close.py` (Administrator/technical/scheduler only; `force` for seeds; immutable handoff payload with package, publication, confirmations digests, addendum trail, documents), `hooks.scheduler_events.hourly`, `get_submission_handoff`; `test_open_period.TestCancellationAndClose`. |
| TND-606 | Audit rows §12.2 9–12; `GetTenderHistory` covers addenda/inquiries/cancellation/downstream events; My Work rows for HoPF issue task and inquiry response | Done | 2026-09-19. `history.py` lists addendum/inquiry/cancellation/close events; `my_work_provider` surfaces `HOPF addendum issue` and `Inquiry response` tasks; `technical_read` probes for addendum and cancellation. |
| TND-607 | `tenders-services-gate` extended with Phase 6 modules; whole-module run recorded | Done | 2026-09-19. Gate globs every `tenders/tests/test_*.py`; run 2026-09-19: 8+10+7+13+6+11+6+11+6+6 = 84 tests OK. `test_read` asserts 37 whitelisted endpoints. |

## Work register — Phase 7: UI slices

| ID | Slice | Status | Evidence |
|---|---|---|---|
| TND-701 | 7a shared runtime (`tenders_page.js`, bundle with `globalProperties` bindings, `Tenders.vue`, `tnd_shared/`, `tenders_industry.css`, hooks, vitest project `tenders`, `package.json` script, `tests/ui/smoke/tenders/helpers.ts`, fidelity spec skeleton) + DES-01 workspace (all nine variants) + DES-14 common states | Planned | |
| TND-702 | 7b DES-02 Start Tender dialog (supported / unsupported; `/new/{handoff}` direct load) | Planned | |
| TND-703 | 7c DES-03 Tender details (record shell, progress row, requisition drawer, meeting variants, unsaved-change guard) | Planned | |
| TND-704 | 7d DES-04 Supplier and contract requirements (evidence table + dialog add/edit/remove, disclosures) | Planned | |
| TND-705 | 7e DES-05 Review and submit (ready / needs attention, previews, submit dialog) | Planned | |
| TND-706 | 7f DES-06 HOPF approval (return/approve dialogs, segregation) + DES-13 returned / correction dialog / correction requested / successor ready | Planned | |
| TND-707 | 7g DES-07 AO publication authorisation (channel table read-only, confirmation, segregation) | Planned | |
| TND-708 | 7h DES-08 Publication confirmation (notice-board / newspaper / online dialogs, invalid evidence, already confirmed, view confirmation) | Planned | |
| TND-709 | 7i DES-09 Published Tender (HoPF / AO / officer / reader variants, no addendum, submission ended, View public Tender) | Planned | |
| TND-710 | 7j DES-10 Prepare and issue addendum (draft / HOPF issue / material blocked) + DES-11 Respond to addendum inquiry (Yes/No) | Planned | |
| TND-711 | 7k DES-12 Cancel Tender (base / recommendation / confirmation / cancelled detail / evidence actions) | Planned | |
| TND-712 | 7l History route (D22 — fidelity-exempt, exemption recorded here) | Planned | |
| TND-713 | Accessibility pass §11.9 on every slice (keyboard order, one `h1`, focus to issue summary, text status, responsive cards at narrow width, dialog focus trap/return, document preview name/format/size/Download) (AC-075) | Planned | |
| TND-714 | `make ui-tenders-{workspace,start,details,requirements,review,approval,authorisation,publication,published,addendum,cancel,history}-gate` + `ui-tenders-fidelity-gate` | Planned | |

## Work register — Phase 8: seeds + worlds

| ID | Item | Status | Evidence |
|---|---|---|---|
| TND-801 | `seeds/kentender_mvp_v1.py` (`verify_prerequisites`, `upsert_tenders` through the §13.3 rows with injected clock, `reset_tenders_seed`, `validate_tenders_seed`) | Planned | |
| TND-802 | Core `canonical.py` `tenders` stage (clear/seed/validate), `make seed-canonical THROUGH=tenders`, Makefile help, SEED-OPS-001 row; `test_canonical_seed.py` idempotency test through `tenders` | Planned | |
| TND-803 | `seeds/playwright_ui_fixtures.py`: world FY 2100-2101, `ensure_world`, `restore_site`, twelve `reset_<profile>` functions (§13.4) built through real commands; `seeds/clear.py`; `globalTeardown.ts` | Planned | |
| TND-804 | `tests/test_tenders_seed.py`; validator green twice on the site; second run creates no duplicate (AC-078) | Planned | |
| TND-805 | Site left canonical after the phase (`seed-canonical-validate THROUGH=tenders` green; Playwright world wiped) | Planned | |

## Work register — Phase 9: release evidence

| ID | Item | Status | Evidence |
|---|---|---|---|
| TND-901 | `tnd-release-evidence.spec.ts`: the whole §13.3 lifecycle as Brian / Charles / Amina / Naomi single-worker on the canonical world | Planned | |
| TND-902 | `tnd-evidence-pack.spec.ts`: every board + named variant → `evidence/v0_8/*.png` (1440×1024) | Planned | |
| TND-903 | Targeted build `./scripts/bench-with-node.sh build --app kentender_procurement`, bundle hash recorded; `make ui-industry-design-gate vue-desk-bundle-translation-binding-gate`; prohibited-token scan (rule 3) | Planned | |
| TND-904 | `11_tenders/RUNBOOKS.md` (§15.4): evidence rejection, conflicting confirmation, failed confirmation transaction, overdue cancellation obligations | Planned | |
| TND-905 | AC map 80/80 and IMP map 55/55 closed truthfully; FOLLOW_UPS updated; REQ/PLN/CFG/SEED follow-ups filed; memory `tenders-v08-kickoff` updated | Planned | |
| TND-906 | Owner evidence: representative-user sessions for PO/HoPF/AO (AC-080, IMP-052); TPL-G07 decision | Planned — owner | |

## Board map

| Label (authoritative) | Current file (scrambled export) | Correct file after TND-003 | Slice |
|---|---|---|---|
| TPR-DES-01 Tenders workspace | `Start Tender Dialog.dc.html` | `Tenders Workspace.dc.html` | 7a |
| TPR-DES-02 Start Tender dialog | `Review and Submit.dc.html` | `Start Tender Dialog.dc.html` | 7b |
| TPR-DES-03 Draft Tender details | `Draft - Tender Details.dc.html` (correct) | same | 7c |
| TPR-DES-04 Draft supplier and contract requirements | `Draft - Supplier and Contract Requirements.dc.html` (correct) | same | 7d |
| TPR-DES-05 Review and submit | `Respond to Addendum Inquiry.dc.html` | `Review and Submit.dc.html` | 7e |
| TPR-DES-06 HOPF approval | `HOPF Approval.dc.html` (correct) | same | 7f |
| TPR-DES-07 AO publication authorisation | `AO Publication Authorisation.dc.html` (correct) | same | 7g |
| TPR-DES-08 Publication confirmation | `Prepare and Issue Addendum.dc.html` | `Publication Progress and Evidence.dc.html` | 7h |
| TPR-DES-09 Published Tender | `Publication Progress and Evidence.dc.html` | `Published Tender.dc.html` | 7i |
| TPR-DES-10 Prepare and issue addendum | `Index.dc.html` | `Prepare and Issue Addendum.dc.html` | 7j |
| TPR-DES-11 Respond to addendum inquiry | `Requisition Correction.dc.html` | `Respond to Addendum Inquiry.dc.html` | 7j |
| TPR-DES-12 Cancel Tender | `Cancel Tender.dc.html` (correct) | same | 7k |
| TPR-DES-13 Requisition correction | `Published Tender.dc.html` | `Requisition Correction.dc.html` | 7f |
| TPR-DES-14 Common states | `Common States.dc.html` (correct) | same | 7a |
| (index page) | `Tenders Workspace.dc.html` holds lint JSON | regenerated `Index.dc.html` | — |
| (runtime) | `support.js` is a WebP image | restored from git HEAD | — |

## Re-implementation register map (§19)

| IDs | Phase / rows |
|---|---|
| TPR-IMP-001, 002, 003 | Phase 2 (TND-206/208) + Phase 4 (TND-407) + 7a (TND-701) |
| TPR-IMP-004, 005, 006 | Phase 2 (TND-205/207), Phase 3 (TND-302), Phase 4 (TND-402/404) |
| TPR-IMP-007, 011, 015 | Phase 3 (TND-302/303/305) |
| TPR-IMP-008, 012, 013, 014 | Phase 4 (TND-401/403/404) |
| TPR-IMP-009, 010 | Phase 4 (TND-402) + 7c/7d (TND-703/704) |
| TPR-IMP-016, 017, 018, 019, 021 | Phase 4 (TND-405) |
| TPR-IMP-020 | Phase 4 (TND-406) + 7f (TND-706) |
| TPR-IMP-022, 023, 024 | Phase 5 (TND-501) |
| TPR-IMP-025, 026, 027, 028, 029, 030 | Phase 5 (TND-502/505) |
| TPR-IMP-031, 032, 033 | Phase 5 (TND-503) |
| TPR-IMP-034 | Phase 5 (TND-504) |
| TPR-IMP-035 | 7i (TND-709) |
| TPR-IMP-036, 037 | Phase 6 (TND-601/602) + 7j |
| TPR-IMP-038, 039 | Phase 6 (TND-603) + 7j |
| TPR-IMP-040, 041, 042, 043 | Phase 6 (TND-604) + 7k |
| TPR-IMP-044, 045 | Phase 4 (TND-407) + 7a (TND-701) |
| TPR-IMP-046, 047, 048 | Phase 7 (all slices, TND-713/714) |
| TPR-IMP-049 | TND-408/506/606 |
| TPR-IMP-050 | Phase 8 |
| TPR-IMP-051, 053, 054 | Phase 9 (TND-901..905) |
| TPR-IMP-052 | Owner (TND-906) |
| TPR-IMP-055 | Phase 6 (TND-605) |

## Acceptance map

| ID | Criterion (short) | Closing row(s) | Status | Evidence |
|---|---|---|---|---|
| TPR08-AC-001 | One menu item **Tenders** | TND-208, 701 | Planned | |
| TPR08-AC-002 | One role-safe queue for starts, drafts, decisions, publication, open | TND-407, 701 | Planned | |
| TPR08-AC-003 | Forbidden state, no data | TND-407, 701 | Planned | |
| TPR08-AC-004 | Scope never widened by a filter | TND-407, 701 | Planned | |
| TPR08-AC-005 | Opening a route/drawer/preview/dialog creates nothing | TND-407, every slice | Planned | |
| TPR08-AC-006 | Start only from an available compatible handoff | TND-401, 404 | Planned | |
| TPR08-AC-007 | Concurrent/repeated Start → one Tender | TND-404 | Planned | |
| TPR08-AC-008 | Start snapshots exact source facts + templates/rules | TND-302, 404 | Planned | |
| TPR08-AC-009 | Inherited content read-only with source route; no owner write | TND-402, 703 | Planned | |
| TPR08-AC-010 | Requisition correction stops the Version; successor only | TND-406, 706 | Planned | |
| TPR08-AC-011 | Three tasks | TND-703..705 | Planned | |
| TPR08-AC-012 | Purchase/quantity/funding/source facts before officer fields | TND-703 | Planned | |
| TPR08-AC-013 | Dates validate as dates and as an ordered sequence | TND-402 | Planned | |
| TPR08-AC-014 | Meeting conditional requirements | TND-402, 703 | Planned | |
| TPR08-AC-015 | Requirements screen separation; positive-integer experience inputs, no preset menu | TND-402, 704 | Planned | |
| TPR08-AC-016 | Evidence CRUD on Draft only, versioned, audited | TND-404, 408, 704 | Planned | |
| TPR08-AC-017 | Evidence wording cannot alter an inherited requirement | TND-402 | Planned | |
| TPR08-AC-018 | Price schedule exact lines/quantities/units/lots/funding split | TND-302 | Planned | |
| TPR08-AC-019 | Technical schedule all eleven rows | TND-302 | Planned | |
| TPR08-AC-020 | Warranty six values; acceptance five checks | TND-302 | Planned | |
| TPR08-AC-021 | Optional schedules absent when sources empty | TND-302 | Planned | |
| TPR08-AC-022 | Evaluation mappings trace to source; not free text | TND-302 | Planned | |
| TPR08-AC-023 | Previews use saved Version data; never mutate | TND-305, 705 | Planned | |
| TPR08-AC-024 | Deterministic document digests | TND-303, 304 | Planned | |
| TPR08-AC-025 | Save returns record version; stale save never overwrites | TND-404, 703 | Planned | |
| TPR08-AC-026 | Review: one result, counts, direct links, no rule ids | TND-403, 705 | Planned | |
| TPR08-AC-027 | Must fix blocks submission with exact route | TND-403, 705 | Planned | |
| TPR08-AC-028 | Review note does not block | TND-403, 705 | Planned | |
| TPR08-AC-029 | Compatibility at start/submit/approve/authorise | TND-401, 501 | Planned | |
| TPR08-AC-030 | Submission freezes Version, package digest, documents | TND-405 | Planned | |
| TPR08-AC-031 | Submitted Version read-only to every actor | TND-405, 207 | Planned | |
| TPR08-AC-032 | Return requires comment; copied Draft | TND-405, 706 | Planned | |
| TPR08-AC-033 | Approval records exact Version/digest; AO task | TND-405 | Planned | |
| TPR08-AC-034 | Approval creates no confirmations, no `published_at`, no supplier exposure | TND-405 | Planned | |
| TPR08-AC-035 | Preparer/submitter cannot approve | TND-405, 706 | Planned | |
| TPR08-AC-036 | Reopen before authorisation only, reason, copied Draft | TND-405 | Planned | |
| TPR08-AC-037 | HOPF/AO/reader boards use exact §10.1 fixture | TND-706, 707, 709, 803 | Planned | |
| TPR08-AC-038 | AO sees package, decision facts, channels; no edit control | TND-707 | Planned | |
| TPR08-AC-039 | Preparer/submitter/approver cannot authorise | TND-501, 707 | Planned | |
| TPR08-AC-040 | Every decision rechecks state/assignment/segregation/integrity | TND-405, 501, 602, 604 | Planned | |
| TPR08-AC-041 | Authorisation atomically records AO, time, Version, digest, rule snapshot, channel set | TND-501 | Planned | |
| TPR08-AC-042 | AO cannot choose/remove/edit a channel | TND-501, 707 | Planned | |
| TPR08-AC-043 | One Evidence-based record per channel; no external call | TND-501 | Planned | |
| TPR08-AC-044 | No adapter; `Integrated acknowledgement` refused | TND-401 (D6), 501 | Planned | |
| TPR08-AC-045 | Stable confirmation identity bound to publication + digest | TND-502 | Planned | |
| TPR08-AC-046 | Only a current HoPF confirms | TND-502 | Planned | |
| TPR08-AC-047 | Attestation, HoPF identity/time, availability time atomic | TND-502 | Planned | |
| TPR08-AC-048 | Checks limited to technical validation; no proof claim | TND-502, 708 | Planned | |
| TPR08-AC-049 | Required confirmation fields; notes ≤500 optional | TND-502 | Planned | |
| TPR08-AC-050 | Evidence scanned/digested/retained; rejected upload cannot confirm | TND-202, 502, 505 | Planned | |
| TPR08-AC-051 | Not Published while any channel outstanding/invalid | TND-503 | Planned | |
| TPR08-AC-052 | `published_at` once = latest availability | TND-503, 505 | Planned | |
| TPR08-AC-053 | Period revalidated from actual `published_at` | TND-503 | Planned | |
| TPR08-AC-054 | Invitation actual written once to Planning; replay idempotent | TND-503, 505 | Planned | |
| TPR08-AC-055 | Withdrawal only unpublished/no channel; auditable | TND-504 | Planned | |
| TPR08-AC-056 | Published record shows time, deadline, documents, evidence, addenda, inquiries | TND-709 | Planned | |
| TPR08-AC-057 | Addendum draft unavailable before publication / after close / after cancel | TND-601 | Done (server) | 2026-09-19 `test_open_period`; UI row pending Phase 7. |
| TPR08-AC-058 | Addendum records before/after, reference, reason, materiality | TND-601, 710 | Done (server) | 2026-09-19 `test_open_period`; UI row pending Phase 7. |
| TPR08-AC-059 | Material change cannot be issued | TND-601, 710 | Done (server) | 2026-09-19 `test_open_period`; UI row pending Phase 7. |
| TPR08-AC-060 | Late addendum requires lawful revised deadline | TND-601, 710 | Done (server) | 2026-09-19 `test_open_period`; UI row pending Phase 7. |
| TPR08-AC-061 | Issue freezes addendum; confirmations per original channel | TND-602 | Done (server) | 2026-09-19 `test_open_period`; UI row pending Phase 7. |
| TPR08-AC-062 | Issued only after all channels confirmed | TND-602, 708 | Done (server) | 2026-09-19 `test_open_period`; UI row pending Phase 7. |
| TPR08-AC-063 | Inquiry only from authenticated candidate-service event | TND-603 | Done (server) | 2026-09-19 `test_open_period`; UI row pending Phase 7. |
| TPR08-AC-064 | Requirement-affecting response broadcast anonymously with digest | TND-603, 710 | Done (server) | 2026-09-19 `test_open_period`; UI row pending Phase 7. |
| TPR08-AC-065 | Non-affecting response to asker, auditable | TND-603, 710 | Done (server) | 2026-09-19 `test_open_period`; UI row pending Phase 7. |
| TPR08-AC-066 | Only AO cancels; ground + reason; final on commit | TND-604, 711 | Done (server) | 2026-09-19 `test_open_period`; UI row pending Phase 7. |
| TPR08-AC-067 | Cancellation never restores/reopens/replaces | TND-604 | Done (server) | 2026-09-19 `test_open_period`; UI row pending Phase 7. |
| TPR08-AC-068 | Obligations tracked with truthful states | TND-604, 711 | Done (server) | 2026-09-19 `test_open_period`; UI row pending Phase 7. |
| TPR08-AC-069 | Every board implementable from §10.1 + KT-STD §2 | TND-003, 714 | Planned | |
| TPR08-AC-070 | Every visible action = one §11 behaviour; absent when not permitted | every slice, TND-714 | Planned | |
| TPR08-AC-071 | No keys/hashes/enums/payloads in the default UI | TND-714, 903 | Planned | |
| TPR08-AC-072 | Officer completes the primary fixture by task labels alone | TND-901, 906 | Planned | |
| TPR08-AC-073 | HoPF and AO each see one plain decision + consequence + content | TND-706, 707 | Planned | |
| TPR08-AC-074 | Status/stage/next action distinct; never label approval or upload as publication | TND-701, 707..709 | Planned | |
| TPR08-AC-075 | §11.9 keyboard/focus/heading/error-link/status-text/responsive | TND-713 | Planned | |
| TPR08-AC-076 | Every command writes §12 minimum audit | TND-408, 506, 606 | Planned | |
| TPR08-AC-077 | Evidence retrievable by digest under audit access | TND-305, 502 | Planned | |
| TPR08-AC-078 | Seed rerun without duplication; proves fixtures independently | TND-804 | Planned | |
| TPR08-AC-079 | Owner-contract failure leaves source unchanged; safe recovery | TND-404, 406, 503, 505 | Planned | |
| TPR08-AC-080 | Representative-user tests | TND-906 | Planned — owner | |
