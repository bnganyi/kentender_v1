# STD-CHG-001 v1.3 — Clean Manual STD Configuration and Runtime — Implementation Plan

**Authority:** `KenTender_STD-CHG-001_Clean_Manual_STD_Configuration_and_Runtime_v1.3.md` (the "spec" below), `KenTender_STD-OVW-001_Manual_IT_STD_Configuration_Worked_Example_v0.1.md`, `docs/mvp-1-r1/07_std_configuration/design/*.dc.html` (16 artboards), `AGENTS.md`.
**Companion:** `IMPLEMENTATION_TRACKER.md` (row-level work register, this plan's phases mirrored 1:1).
**Owning app:** `kentender_procurement` (new `std_configuration/` module), consumed by `kentender_core` (seed) and by `kentender_procurement`'s own `tender_configurations/` module.
**Status:** Plan authored and all open decisions (§6) confirmed by user 2026-08-25. Phase 1 may begin. No implementation phase started yet.

## 1. Why this plan exists, and the one fact that changes everything about it

The spec reads as a from-scratch build ("New DocTypes, services, pages, manifests, fixtures and tests are created from this specification... The old parsing engine, extracted-clause model, inferred schemas, runtime objects and routes are not migrated or wrapped"). Taken alone, that sentence undersells the situation: this is not an empty module. A prior-art audit (Explore-agent pass, 2026-08-25) found a **large, live, currently-in-production predecessor** that the spec's own language is describing when it says "the old parsing engine" and "the retired parsing runtime":

- **`kentender_procurement/kentender_procurement/std_engine/`** — ~10,800 lines, 19 real DocTypes (`STD Family`, `STD Version`, `STD Source Document`, `STD Source Anchor`, `STD Section`, `STD Clause`, `STD Parameter`, `STD Rule`, `STD Form Schema`, `STD Form Field`, `STD Requirement Schema`, `STD Price Schedule Schema`, `STD Evaluation Schema`, `STD Render Block`, `STD Validation Run`, `STD Validation Finding`, `STD Audit Event`, `STD Usage Binding`, `STD Import Run`), a working PDF-package importer, a validation engine, and a full read API — all built and proven against exactly one real dataset, `KE-PPRA-IT-2022-04` (94/94 clauses, 155/155 parameters extracted and verbatim-reconciled). Its own tracker (`docs/std-engine/BE_IMPLEMENTATION_TRACKER.md`) shows Milestone 1 (BE-00 through BE-15) **Done**.
- **22 live Desk routes** (`/app/std-library`, `/app/std-family-detail`, … `/app/std-version-diff-and-supersession`), static-HTML pages under `kentender_procurement/public/std_prod_impl/*.html`, hydrated by `public/js/std_prod_engine.js` and route-specific JS, all wired in `kentender_procurement/hooks.py`'s `page_js` dict and reachable today.
- **`kentender_procurement/kentender_procurement/tender_configurations/`** — ~67,400 lines, the live downstream Tender Preparation/Configuration module. It reads `STD Parameter`/`STD Version` **directly** (confirmed: `contract_parameter_readiness.py`'s `ensure_std_declared_contract_values` binds real codes like `IT-SCC-029` from `package_id="KE-PPRA-IT-2022-04"` into live `Tender Configuration` rows). This is production code with a passing test suite, not scaffolding.
- **`kentender_core/seeds/stable_platform_seed/std_it.py`** seeds the site today by calling `std_engine.package_import.commit_importer.CommitImporter` directly.
- **`scripts/std_extraction/`** — the dev-time tool that produced the verbatim `KE-PPRA-IT-2022-04` content `std_engine` imports (clause/parameter extraction + hash reconciliation). Runs outside the app; produces no DocType writes itself.
- Two **already-archived** predecessors (`archive/std-module-poc-retired-2026-07/`, a generic Works/BOQ-oriented STD POC; `archive/it-std-wizard-retired-2026-07/`, the full IT Tender Configuration Wizard v1–v3) are confirmed genuinely dead — zero live imports outside `archive/` — and are reference-only.

None of the spec's own DocType names (`STDPackage`, `STDDraft`, `STDVersion`, `STDContentBlock`, `STDAssistanceBatch`, `STDReviewTask`, `STDDecision`, `STDTenderConfigurationManifest`, etc.) exist anywhere in the live tree today, so **the DocType layer genuinely is a from-scratch build** — there is no schema to migrate. But `std_engine` is not the retired thing the spec is telling us to leave alone; it is the thing the spec's "no earlier implementation object becomes an authority merely because it already exists" (§2.1) and "preserve old runtime aliases, dual reads or compatibility adapters" prohibition (§2.3) are telling us to **replace**, deliberately and in the open, the same way the wizard and the POC were already replaced once each. The single largest risk in this whole build is not building the new DocTypes — it is safely re-pointing `tender_configurations`' live, tested, production dependency on `STD Parameter`/`STD Version` onto the new `STDTenderConfigurationManifest`/`GetRuntimeManifest` contract without a silent regression, and doing it without ever leaving two competing STD authorities live at once (a standing prohibition throughout AGENTS.md and this spec's own §2.3).

This plan treats that migration as its own phase (Phase 12) with the same weight Strategy's tracker gave `kentender_budget`/`kentender_procurement` re-wiring (STR-G06), and treats `std_engine`'s proven extraction output and validated domain shapes (`content_hash`/`source_anchor`/`validation_status`, its lifecycle enum, its envelope pattern) as **high-value input evidence** for the spec's own §17 one-time transformation utility — not as code to import, call, or wrap.

## 2. Scale relative to the last comparable rebuild

Strategy (`STR-CHG-001`, the immediately preceding clean-rebuild precedent, now Done) touched 5 DocTypes, 4 UI routes, and one real downstream consumer (`kentender_budget`). This module's spec defines:

- **20 new DocTypes** (§7.1–7.18, plus the manifest object in §7.18 and 9.2).
- **9 package-authoring areas** (PCFG-01 through PCFG-09, §8), each with its own domain schema, save command, and Vue page.
- **15 registered UI surfaces** (§14: 2 top-level pages, 2 modals, 9 config pages, 5 workflow/report/preview/comparison pages, 1 state-variant set) — versus Strategy's 4.
- **A 9-step, ~40+ item generated Tender Configuration Manifest contract** (§9) that is itself a second, downstream-facing product surface, not just an internal record.
- **A live, tested, 67k-line downstream consumer app** already depending on the module this replaces (§1 above) — Strategy's downstream blast radius was two call sites in one file each.
- **A named one-time reuse/transformation obligation** (§17, ~10 subsections) with its own register, procedure, rules, and acceptance gate — Strategy had no equivalent; this is new process weight, not just more DocTypes.
- **25 acceptance criteria** (§18) plus a 25-item automated-coverage checklist (§18.1) — roughly comparable density to Strategy's 30 `STR-AC-0xx`, but each criterion here spans a wider surface.

Treat this as **at least a 3x-larger build than Strategy** in every dimension except lifecycle-engine complexity (STD's lifecycle, §12, is simpler than Strategy's 8-state plan-version engine — 5 states, no approval-chain fan-out). Plan phases and checkpoints accordingly: land one PCFG area at a time behind its own focused tests, per AGENTS.md §7/§8, rather than attempting the full domain model in one pass.

## 3. Controlling decisions already made by the spec (do not re-litigate)

These are binding per spec §2 and are the equivalent of Strategy's "headline finding" — read before touching any doctype:

1. **Greenfield DocTypes; no runtime migration of `std_engine`.** §2.1. Confirmed above: no name collision exists, so this is achievable cleanly.
2. **`std_engine`'s extracted, verbatim-reconciled `KE-PPRA-IT-2022-04` content (94/94 clauses, 155/155 parameters) is legitimate reuse input**, not a forbidden shortcut — §17.3's "Configured STD content" and "Existing implementation exports" input classes describe exactly this data. It must go through the §17 disposition register and `STDAssistanceBatch` proposal review like any other reused content; it may not be copied directly into an Active package.
3. **`scripts/std_extraction/` is legitimate "one-time reuse utility" tooling** per §17.6/§19 ("development/controlled-deployment tooling... not called by package, Tender, bidder, evaluation or contract runtime paths"). It is not the prohibited "automated PDF parsing... as a production dependency" (§2.3) as long as its output only ever feeds the §17 transformation procedure and never a live runtime call path. Confirm this boundary explicitly in Phase 10 rather than assuming it.
4. **Four content treatments, exactly one per item** (§4) is the primary anti-gap control across every PCFG area — every domain-model phase must enforce "no undefined Other treatment" as a real validator, not a UI convention.
5. **Maker-checker is absolute**: the STD Configurator who submits can never be the STD Reviewer who activates the same Draft (§12, §16.4). No System Manager override (§12: "System Manager alone grants no STD business decision").
6. **`kt_industry_tokens.css` is the canonical design system** (AGENTS.md §6.6, a hard rule as of the Strategy rebuild) — every one of the 15 STD UI surfaces is built on it from the start. There is no equivalent of Strategy's forked-token detour to repeat here; Phase 11 starts on Industry, full stop.
7. **Tender Preparation (the §9 manifest's consumer) is out of scope** — §9.16 explicitly defers it to "a separate Tender Preparation canonical document." This plan's Phase 12 only covers re-pointing `tender_configurations`' *existing* STD reads at the new manifest contract, not building a new Tender Preparation UX.

## 4. Phase overview

Phases map 1:1 to the tracker's work registers. Each phase closes with focused tests for that phase's own scope (AGENTS.md §7/§8); no phase reruns the full suite except the Phase 14 release gate.

| Phase | Scope | Depends on |
|---|---|---|
| 0 | Plan, tracker, decisions (this document + companion tracker) | — |
| 1 | Domain model — backbone (`STDPackage`, `STDDraft`, `STDVersion`, `STDSourceDocument`, `STDSection`, `STDContentBlock`) + the four-content-treatment guard | 0 |
| 2 | Domain model — the 9 PCFG schema/definition DocTypes + cross-cutting objects (`STDOutputMapping`, `STDAssistanceBatch`, `STDValidationFinding`, `STDReviewTask`, `STDDecision`, `STDTenderConfigurationManifest`) | 1 |
| 3 | Lifecycle engine (§12) — Draft/In review/Returned/Active/Superseded/Retired, optimistic concurrency, atomic activate | 1, 2 |
| 4 | Roles and permissions — STD Configurator/STD Reviewer capability profiles, SoD, fail-closed | 3 |
| 5 | Service contracts (§13) — 11 read + 17 command endpoints, §13.3 error contract | 1, 2, 4 |
| 6 | Validation and coverage engine (§11) — 16-row coverage register, Blocking/Warning findings, `RunSTDCompleteCheck` | 2, 5 |
| 7 | Review and activation — submit/return/activate, atomic 7-manifest generation (§10), immutable submitted snapshot | 3, 4, 6 |
| 8 | Draft assistance (§16.2) — prior-configuration and AI-assisted proposal contract, selective accept/reject, staleness | 5, 6 |
| 9 | Seed contract — golden fixture `STD-IT-V1-GOLDEN` (§17.1) + worked Tender instance fixture (§9.15) | 6, 7 |
| 10 | One-time reuse/transformation utility (§17.2–17.9) — reuse bundle, disposition register, transformation run against real prior IT-STD content | 8, 9 |
| 11 | Vue UI — all 15 registered surfaces on `kt_industry` (§14/§15) | 5, 6, 7, 8 |
| 12 | Downstream consumer migration — retire `std_engine`'s 19 DocTypes/22 routes; re-point `tender_configurations`; migrate `kentender_core`'s seed | 7, 9 |
| 13 | Shell/registry + module menu wiring (`Configuration and Governance > Standard Tender Documents`) | 11 |
| 14 | Verification against §18 acceptance criteria, full suite, one complete browser journey | all |

Phases 1–2 (domain model) and 5–8 (services) are ordered by dependency, not by PCFG area, deliberately mirroring Strategy's own domain-model-then-lifecycle-then-services-then-UI layering (AGENTS.md §4.2) rather than building each PCFG area vertically end-to-end. Reasoning: nine near-identical "area save command + area validator + area page" slices sharing one coverage/readiness/manifest engine are more consistent, and more defensible against the spec's own "no undefined Other treatment" and "duplicate binding key" cross-area rules (§11.2), if the shared engine (Phase 6) is built once against a complete domain model, rather than evolved ad hoc nine times. Fine-grained per-PCFG-area tests still land inside each phase — see the tracker's row-level breakdown.

## 5. Key risks and how each phase is expected to handle them

1. **`tender_configurations` regression during Phase 12.** ~67k lines, 75 test files, live `STD Parameter`/`STD Version` reads. Do not delete `std_engine` DocTypes until every direct dependency is re-pointed and its *existing, currently-passing* test suite (not a rewritten one) is green against the new manifest contract — the same standard Strategy held `kentender_budget`'s `test_budget_line_strategy_validate.py` to (STR-606). Budget for this being the single largest phase; expect it to surface more direct-read call sites than the initial grep found.
2. **Two live STD authorities coexisting mid-migration.** Between Phase 7 (new activation works) and Phase 12 (old routes retired), both `std_engine`'s 22 Desk routes and the new PCFG-01..09 Vue pages will be reachable. This is expected and time-boxed, not a design flaw — Strategy's own Phase 6/8 split had the same shape (old and new both live until the retirement phase) — but the retirement must actually happen in Phase 12/13, not be left indefinitely, per §2.3's "preserve old runtime aliases" prohibition.
3. **§17 transformation utility scope creep.** §17.6's 12-step procedure plus the §17.4 disposition register is substantial process, not code, and is easy to under-scope. Do not fold it into Phase 9's seed work — it produces `STDAssistanceBatch` *proposals* a human then reviews (§17.9's acceptance gate), not seed records written directly; keep the seed fixture (deterministic, no human review loop) and the transformation utility (proposal-and-accept loop) architecturally and procedurally separate even though they share source content.
4. **Manifest generation atomicity (§10, §16.4).** "Activation generates Version and all seven manifests atomically. Any failure rolls back the entire activation." This needs one real Frappe transaction spanning `STDVersion` creation and all 7 manifest writes (`Requirement Composer`, `Tender Configuration`, `Bidder Response`, `Evaluation`, `Contract Formation`, `Contract Management`, `Render`) — verify this is tested with an induced failure on the *last* manifest, proving the first six are also rolled back, not just that a successful run produces seven.
5. **`kt_industry_tokens.css` gap for tree/hierarchy and multi-tab config-area chrome.** Strategy's Phase 1 already added a tree-row pattern to Industry (per its own §6.6 addendum); PCFG-02's section/coverage tree and PCFG-04/06/08's tabbed schema browsers are heavier UI than anything Industry has hosted yet. Audit Industry's current inventory at the start of Phase 11 before assuming every needed pattern exists — extend Industry centrally if a genuine gap is found (per the precedent set in Strategy's plan), never fork a page-local component.
6. **25 acceptance criteria spanning process, not just code** (§18 items 22–25 concern the reuse register and transformation report specifically). Phase 14's AC-mapping table must trace each of these to the Phase 10 deliverable, not to a code test, the same way Strategy's STR-AC mapping distinguished code evidence from live-verification evidence.

## 6. Decisions confirmed by the user, 2026-08-25

Unlike Strategy's STR-004 (architecture choices with a clean recommended default), this module's open decisions were mostly about **what happens to already-live production code and routes**, a higher-stakes category (AGENTS.md's "hard-to-reverse... affects shared systems" bar). All three were confirmed via `AskUserQuestion` before Phase 1 begins:

1. **`std_engine` retirement**: full retirement in Phase 12/13 — `std_engine`'s 22 Desk routes stop being reachable and `tender_configurations`' direct STD reads are re-pointed at the new manifest contract — but **archived with DB rows preserved and the archive recoverable**, matching the `std-module-poc-retired-2026-07` precedent exactly ("DB rows preserved, UI/API wiring removed"), not deleted outright. This is a middle path between the plan's original two options, and the one now binding for Phase 12 (tracker STD-1206).
2. **Reuse input**: `scripts/std_extraction`'s already-produced `KE-PPRA-IT-2022-04` verbatim content (94/94 clauses, 155/155 parameters) is the primary input to Phase 10's reuse bundle. Confirmed as recommended.
3. **Production IT package scope**: completing the full production IT package against the official PPRA document (spec §17.2) is a **separate follow-on**, not this build's exit criterion. Phase 10 ends at "transformation utility built and proven, vertical slice complete" — confirmed as recommended, matching the worked-example document's own "practical build boundary" (§7).

## 7. What is explicitly not in this plan

Per spec §9.16 and §20: Tender Preparation's own Procurement Officer workspace (the manifest's *consumer* UX) is a separate future canonical document and build. This plan builds and proves the manifest contract (Phase 7, Phase 9's worked fixture) and re-points the *existing* `tender_configurations` reads onto it (Phase 12) — it does not redesign `tender_configurations`' own UX.
