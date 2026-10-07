# KenTender audit remediation — implementation tracker

Created 6 October 2026 from `audit/FINDINGS.md` (237 findings: 3 Critical · 36 High · 114 Medium · 84 Low). This file is the single place to see progress. Update the **Status** cell of a row when its state changes; update the dashboard counts at the end of each working session.

## How to read and update this tracker

**Status values** (move strictly left to right):

| Status | Meaning |
|---|---|
| Todo | Not started |
| Red | A focused test that reproduces the finding exists and fails for the right reason |
| Green | Smallest fix made; the focused test and its module tests pass |
| Verified | Passed on the test site (`kentender-test.local`), seen working in a real browser/API call where the finding is user-visible, and counted clean by the wave’s regression sweep |
| Blocked | Waiting on an owner decision or another finding (say which in Notes) |
| Won’t fix | Owner accepted the risk — record who, when, and why in Notes |

**Working rules (from CLAUDE.md / AGENTS.md):** test first (red → green → refactor); run Python tests on the test site only, never the dev site; one commit per finding or tight group, message ends `Refs AUD-<id>`; after a server-side change check first paint and one interactive re-render for any screen it touches; report exactly what was and was not run. Any change that adds a migrate, patch or seed is flagged before it lands because code is live on the dev site at once.

**Wave exit gate:** a wave is closed only when every row is Verified (or Won’t fix with a reason) **and** the wave’s regression sweep (named in each wave) has been re-run read-only with none of the wave’s findings left open.

## Owner decisions recorded (6 October 2026)

| # | Decision | Effect on the findings |
|---|---|---|
| D1 | **Tender Management v2 is permanently retired — "no reference to it".** | AUD-XC-003 is closed by deletion, not patching (WP1.3). XC-011 and XC-126 may close with it. Needs an inventory first so nothing live depends on it. |
| D2 | **Award chain:** only the HOPF prepares and signs the professional opinion and handles supplier correspondence and restrictions; only the AO records the award decision — Award, No award or Return. No other roles. | AUD-AWD-001 was a SPEC GAP; it becomes a **CODE DEFECT** against this rule (WP4.1). The approved Award document must be amended (Wave 7, D-1). |
| D3 | **Budget callers:** Requisitions service principal releases the exact reservations its requisition created (governed revocation before Tender Preparation consumes the handoff; release and reversal of the Planning drawdown together). Contract service principal converts reservations into commitments, releases an unused reservation amount (authenticated owner event), and adjusts a commitment with `adjust_commitment`. Planning, Tenders, Evaluation and Award cannot release or convert funds. No general "Release funds" permission for business users. "Release" means freeing a reserved budget amount, not cash. | Defines the acceptance rule for AUD-XC-002 and XC-012 and settles the spec gap BUD-012 (WP1.2). |
| D4 | **Annual Plan publication is manual.** | AUD-XC-106 is no longer "nothing dispatches it" but "no human, role-gated way to publish it". It is also a **SPEC DEFECT**: PLN v1.29 lines 454 and 989 require a post-commit worker (WP5.1, document D-2). |

## Open questions (none blocks starting Wave 1)

| # | Question | Default I will use until answered | Blocks |
|---|---|---|---|
| Q1 | Who may call `revalidate_reservations`? It is not in the owner’s caller table. | Budget itself only (internal), no web endpoint | WP1.2 |
| Q2 | Who may call `check_funding` / `reserve_funding`? | Requisitions service principal only | WP1.2 (XC-012) |
| Q3 | May one person hold both HOPF and AO assignments, and so both prepare and decide? D2 names the roles but not whether one person may hold both. | Refuse the decision if the same user signed the opinion for that case | WP4.1 |
| Q4 | Which role presses **Publish** for an approved Annual Plan? | The Head of Procurement Function (HOPF) | WP5.1 |
| Q5 | Keep public supplier self-registration (`ktsm_register`)? No approved document justifies it. | Keep it, but remove `ignore_permissions`, add rate limiting and create the User only after email verification | WP1.4 |
| Q6 | Governed exit for a Tender stranded by a late final channel confirmation (AUD-TND-002): revise the deadline in the same publication package, or allow withdraw/cancel? | Revise the deadline in the same package (what the document says) | WP4.4 |

## Progress dashboard

All counts are findings, excluding duplicates. Update when statuses change.

| Wave | Title | Findings | Todo | Red | Green | Verified | Blocked/Won’t fix |
|---|---|---|---|---|---|---|---|
| 1 | Close the doors anyone can open | 25 | 0 | 6 | 4 | 14 | 1 |
| 2 | Stop REST from bypassing the approval rules | 11 | 0 | 3 | 0 | 8 | 0 |
| 3 | Money correctness | 28 | 0 | 6 | 1 | 20 | 1 |
| 4 | Segregation of duties and approval integrity | 39 | 0 | 2 | 9 | 24 | 4 |
| 4R | Regression findings from the Waves 1-4 sweeps | 42 | 42 | 0 | 0 | 0 | 0 |
| 5 | Flows that dead-end or lose data | 37 | 37 | 0 | 0 | 0 | 0 |
| 6 | Audit trail and Frappe hazards | 14 | 13 | 0 | 0 | 1 | 0 |
| 7 | Remaining Medium/Low and document corrections | 83 | 83 | 0 | 0 | 0 | 0 |
| **All** | | **279** | **175** | **17** | **14** | **67** | **6** |

By severity (all rows, including Wave 4R): Critical 3 (2 Verified · 0 Green · 1 Red · 0 Blocked · 0 Todo) · High 38 (23 Verified · 2 Green · 3 Red · 1 Blocked · 9 Todo) · Medium 129 (35 Verified · 10 Green · 8 Red · 3 Blocked · 73 Todo) · Low 109 (7 Verified · 2 Green · 5 Red · 2 Blocked · 93 Todo)
Of which Wave 4R (new regression findings, all Todo): High 2 · Medium 15 · Low 25 · total 42

Wave 1-4 rows are Verified only when the regression sweeps judged them CLOSED and the integration gate reported none of their covering tests failing; Red rows were reopened by the sweeps (see Wave 4R); rows not judged by any sweep stay Green. Wave 5-7 rows and the document workstream are untouched by this reconciliation.

## Integration gate result (7 October 2026)

Full Python suites of the product apps on `kentender-test.local` only, every run under `flock /tmp/kt-test-site.lock`, one module per call. Detail: `audit/progress/INT-A.md` (core, budget, strategy, suppliers) and `audit/progress/INT-B.md` (kentender_procurement). Apps with no tests (governance, compliance, stores, assets, integrations, transparency) were skipped.

**No pre-wave baseline was run.** Nothing was swapped back to the commit before the Wave work and no before/after comparison was made. Every failure below is classed R (regression), E (environmental or pre-existing) or D (decision) from evidence in the code: root-cause reads, rolled-back probes, and `git log`/blame showing the involved files were not touched by the Wave commits. That is evidence of cause, not a measured baseline.

| App | Modules run | Tests | Failing on first run | Failing at the end |
|---|---|---|---|---|
| kentender_core | 102 | 925 | 42 in 22 modules | 39 in 22 modules (all E) |
| kentender_budget | 22 | 236 | 0 | 0 |
| kentender_strategy | 17 | 187 | 103 in 9 modules | 0 |
| kentender_suppliers | 14 | 92 | 0 | 0 |
| kentender_procurement | 283 of 302 | 2,976 | 48 (21 F + 27 E) in 25 modules | 44 (20 F + 24 E) in 24 modules (all E) |
| **Total** | **438** | **4,416** | **193** | **83** |

Not run in kentender_procurement: 19 modules (3 doctype stubs with no tests; 16 `tender_configurations` modules that die at load on an ERPNext Fiscal Year overlap). One further module, `bid_evaluation.tests.test_evl_canonical_seed`, errored once and passed on rerun (transient, not reproduced). **Regressions open: 0.**

**Regressions found and fixed (two root causes, not one):**

- INT-A, commit `a1747084`: the Strategy audit fix (AUD-STR-008) made the structure command refuse fields outside its allow-list, but the canonical Strategy seed still passed `fixture_namespace` in a target row, so every lower-stage reseed or REBUILD died (3 `test_canonical_seed` ladder tests). The seed now stamps the namespace after the command.
- INT-B, commit `759685f6`: the command-write guard (AUD-XC-010) refuses maintenance writes while `frappe.local.request` is set; a portal-page test left a request behind, so later fixture wipes in the same process were refused (3 errors + 1 failure in `test_available_tenders`). Test-only fix: the request is restored in a cleanup. No guard weakened.

**Failures accepted as E, with the evidence:**

- Strategy, 103 tests in 9 modules: ERPNext `_Test Fiscal Year 2040`..`2050` rows (created 11:01 that day by an ERPNext test-record load) overlap the fixture year. After deleting those 11 throw-away rows from the test site, all 9 modules passed (103 tests).
- Core canonical world residue (3 `test_canonical_seed` tests, `test_procurement_settings` one test): `canonical.validate()` fails on rows other modules' tests left on the shared site (extra Organisation Units, users, Budgets, stray Funding Reservations, a plan item pinned to a deleted schedule profile). A rolled-back probe reproduced the schedule-profile case.
- Core, 7 modules create a Procuring Entity without `reporting_currency` (required since 15 Aug 2026, commit 9f1f5cf8); the rest are legacy seeds and gates for retired surfaces (Demand tables, Civic Ledger/Stitch, module registry, `seed_v1`, multi-PE reference seed) and the Supplier Website template. Files untouched by the Wave commits.
- Procurement: tests that assume an empty site and fail against the two-year canonical world (Evaluation intake, three Requisitions reads, Tenders workspace counts); expired seed assignment for an acting Head; legacy Journey rows and Strategy tables that no longer exist; stray HOPF "Head of User Department" grant left by a Requisitions fixture; a projection left dated in the future by a Needs test; ERPNext `_Test Fiscal Year 2028` and `2040` overlaps; removed doctype and www file in `tender_configurations`; documented sidebar drift (`procurement-sidebar-g0012`).

**Follow-ups (none blocks; all D class):**

- D-1: 7 core tests create a Procuring Entity without `reporting_currency`; add it to the fixtures (separate `test(core)` commit).
- D-2: a Requisitions test leaves a plan item pointing at a deleted schedule profile, and profile names are reused after deletion; delete plan items with the profile, consider monotonic version names.
- D-3: `get_tender_publication.can_configure` is true for Administrator in the technical-read conformance probe, and the Bid Opening technical-read resolver declares `route` as a string; owner of Tenders and Bid Opening to decide and fix.
- D-4: the test-site canonical world no longer validates after the full run; `make test-site-rebuild` before any canonical-dependent run.
- D-5: retire or repair the legacy test files listed in INT-A (they fail for reasons unrelated to the Waves and hide signal).
- Strategy tests: `ensure_fiscal_year` should pick a window that cannot overlap ERPNext test years.
- INT-B 1: Requisitions fixture `restore_site` should revoke the HOPF grant; `test_departmental_needs_contracts` should restore the usage projection it leaves dated in the future.
- INT-B 2: several tests assume an empty site; decide whether tests scope to their own records or run on a site without the canonical world.
- INT-B 3: `set_request` users should restore `frappe.local.request` (pattern in `759685f6`): `tender_configurations/tests/test_published_tender_overview_web.py` and `kentender_core/tests/test_portal_runtime.py`.
- INT-B 4: 16 `tender_configurations` modules never load, so the Tender Configuration guards are not exercised by the suite (relevant to RG-04 and RG-05); owner decision on those retired-feature tests.
- INT-B 5: three doctype folders contain no tests (harmless). INT-B 6: an uncommitted change to `kentender_procurement/workspace_sidebar/procurement.json` belongs to someone else (relates to the E-10 sidebar tests).
- INT-B unclassified: re-run `test_evl_canonical_seed` once in the lead's final sweep.

Wave exit status: no wave is closed. Wave 1 to 4 rows are Verified, Red (reopened) or Green (not judged by any sweep); see the dashboard and Wave 4R.



## Wave 0 — Preparation (no product code)

| ID | Task | Output | Status | Notes |
|---|---|---|---|---|
| WP0.1 | Record the four owner decisions | This file + memory note | Verified | Done 6 Oct 2026 |
| WP0.2 | **TM2 inventory:** every importer of `tender_management`, every `tm2_*` doctype and whether this site holds rows, hooks/workspace/menu/patch/seed/test references, and whether the Tender Configuration doctypes in XC-011 and the legacy Tender Configurations endpoints (XC-143) belong to TM2 | `audit/tm2-inventory.md`: delete list, keep list, risks | Todo | Gate for WP1.3. Check the site for TM2 Tender rows before deletion |
| WP0.3 | **Budget caller inventory:** every Python and JS caller of release / convert / adjust / revalidate / check / reserve | Caller table in WP1.2 notes | Todo | Confirms nothing browser-side calls them |
| WP0.4 | **Test-site baseline:** `make test-site-rebuild`, then record which tests already fail so regressions are distinguishable (an earlier sweep left 168 failing, mostly environmental) | `audit/test-baseline.md` | Todo | Never run these tests on the dev site |
| WP0.5 | Confirm assumptions Q1–Q6 | Answers in this file | Todo | Defaults above apply meanwhile |
| WP0.6 | Choose the shared test helpers: a wrong-user caller fixture, a two-process race harness, a REST-bypass probe | Helpers in `kentender_core/tests` | Todo | Used by Waves 1–3 |

## Wave 1 — Close the doors anyone can open

**Goal:** Small, local fixes. Anyone signed in (or not signed in) can currently impersonate, move funds, change suppliers, or read what they should not. No design dependencies except the owner decisions already recorded.

**Exit gate:** Re-run sweep-authorization and sweep-sod read-only; AST test shows no whitelisted function takes an actor/user parameter; module tests for Needs, Budget, Strategy, Suppliers on the test site.

### WP1.1 — Needs identity: never take the acting user from the request

*Internal callers (Planning intake/validation/publication) move to an internal function with an explicit principal.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-001 | C | Every Departmental Needs endpoint takes the acting user from the request (`user=`); any signed-in account acts | Drop `user` from every whitelisted Needs function; pass `frappe.session.user` only. Test: signed in as A, call accept_need_revision with user=<HoD> → refused/ignored; AST test: no whitelisted function in any app has a `user`/`actor` parameter that names the acting principal. | Verified | departmental_needs/tests/test_departmental_needs_principal.py::TestEndpointsActAsTheSessionUser (6 tests); kentender_core/tests/test_whitelisted_principal_param | 8bc76479 | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site; AST test narrower than the scanned patterns (REG-SOD-09, RG-41). Endpoints now act as `frappe.session.user` only. |
| XC-016 | M | Planning projection endpoints are callable by a human Planner with caller-chosen actor and ordering time | See finding in `audit/FINDINGS.md`. | Verified | test_departmental_needs_principal.py::TestPlanningProjectionsAreNotWebEndpoints::test_no_projection_command_is_reachable_over_http | 8bc76479 | 7 Oct 2026 | regression sweep authorization, state-machine + test site; In-process technical principal in usage.py is a spec decision, not an endpoint. The three projection commands are no longer web endpoints. |
| NDS-011 | M | check_accepted_need_withdrawal_dependency has no permission check | See finding in `audit/FINDINGS.md`. | Verified | test_departmental_needs_principal.py::TestWithdrawalDependencyRead::test_a_person_who_cannot_read_the_need_is_refused | 8bc76479 | 7 Oct 2026 | regression sweep authorization + test site. New reader service `lifecycle.read_withdrawal_dependency` (view-scope check); internal command callers keep `check_withdrawal_dependency`. |
| XC-140 | L | `**kwargs` Needs endpoints and journey/search endpoints turn unknown or malformed input into HTTP 500 | See finding in `audit/FINDINGS.md`. | Green | test_departmental_needs_principal.py::TestUnknownFieldsAreRefused (2 red tests) | 8bc76479 | test site | Unknown field -> typed `DepartmentalNeedError` (HTTP 417), not TypeError/500. Only the Needs part; see Follow-ups for the journey/search `limit` part. |

### WP1.2 — Budget service-principal authority (owner decision, screenshot)

*Release/convert/adjust become in-process services, not web endpoints. Requisitions principal: release only the exact reservations its requisition created, before the handoff is consumed, together with Planning drawdown reversal. Contract principal: convert, release unused amount, adjust commitment — each needs an owner event, exact allocation and an idempotency key used for dedupe. Planning, Tenders, Evaluation, Award refused. No business-user "Release funds" permission.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-002 | C | Budget release / convert / adjust / revalidate endpoints are open to every non-Guest account; `idempotency_key | See WP1.2. Test matrix caller × action (Requisitions: release own reservations only; Contract: convert / release unused / adjust; Planning, Tenders, Evaluation, Award, any browser user: refused). Idempotency key replays return the first result. | Red | kentender_budget/tests/test_budget_service_principal.py::TestPrincipalMatrix, ::TestNoWebSurface, ::TestRequisitionsRelease, ::TestContractPrincipal | 94f1c9ba (dia_budget_control.py deletion landed in 9c7c9a6d, a concurrent session's commit swept my staged `git rm`) | reopened 7 Oct 2026 | Reopened 7 Oct: idempotent-by-key half not met, a concurrent same-key release applies twice and governance replay is user-blind (REG-MONEY-01, REG-STATE-07: RG-16); mint/lineage lows REG-AUTHORIZATION-12/-16: RG-26. Whitelist removed from the 4 wrappers (+ check/reserve); dia_budget_control module deleted (no caller). Allow-list matrix + idempotency journal implemented. |
| XC-012 | H | `check_funding` / `reserve_funding` accept Finance Confirmation Officer, trust a self-declared caller, and val | Restrict check_funding/reserve_funding to the Requisitions service principal using the same mechanism as XC-002; remove the Finance Confirmation Officer path and the self-declared caller. (Assumption A2.) | Verified | same file::TestCheckReserveCaller | 94f1c9ba | 7 Oct 2026 | regression sweep authorization, state-machine, money-concurrency + test site. FCO/HOPF session path removed; calling_module comes from the principal; caller_reference must equal the principal's requisition. Inverted the old `test_finance_confirmation_officer_still_permitted`. |
| BUD-012 | M | SPEC GAP: how an in-process caller proves it is the REQ / Contract Management service principal | See finding in `audit/FINDINGS.md`. | Verified | same file (TestPrincipalMatrix::test_a_caller_cannot_be_forged, ::test_only_the_owning_gateways_and_seeds_mint_principals) | 94f1c9ba | 7 Oct 2026 | regression sweep authorization, money-concurrency + test site; Mint enforcement is a regex scan (RG-26). Mechanism: `kentender_budget/services/budget_service_principal.py` — a `ServiceCaller` object only `service_caller()` can mint (not constructible from a web request), checked against an allow-list of (principal, action); error `BUDGET_DOWNSTREAM_FORBIDDEN`. Repo test fails if any non-seed, non-test file other than |
| BUD-013 | L | Check token not bound to actor or Budget revisions | See finding in `audit/FINDINGS.md`. | Verified | same file::TestCheckReserveCaller::test_the_token_is_bound_to_the_actor_who_checked, ::test_the_token_is_bound_to_the_requisition_that_checked, ::test_a_budget_ | 94f1c9ba | 7 Oct 2026 | regression sweep authorization, money-concurrency + test site. Token now carries actor, requisition and per-line Budget Version; a real governed revision (successor, submit, approve) between check and reserve gives BUDGET_CHECK_STALE. |

### WP1.3 — Retire Tender Management v2 permanently (owner decision: no reference to it)

*Inventory first (WP0.2). Delete code, doctypes, endpoints, workspace/menu links, hooks, seeds, tests and current docs. One idempotent drop patch is the only permitted reference. XC-011 and XC-126 close here if the inventory shows those doctypes/paths belong to TM2; otherwise they are fixed in place.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-003 | C | Tender Management v2 publication API trusts a client `actor`; `actor=Administrator` skips every role check | See WP1.3. Gate: repo-wide grep for tm2 / tender_management / "Tender Management v2" returns nothing outside the single drop patch and the archive; bench migrate on the test copy is clean. | Verified | `kentender_procurement/tests/test_retired_surface_gone.py::TestRetiredSurfaceGone` (4 tests, red before deletion) | 7aa419cc (+ file deletions swept into 9c7c9a6d via shared index) | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site; Code clean; docs/ and archive/ still name TM2 (REG-AUTHORIZATION-14, RG-35). Package, 23 doctypes + 5 companion doctypes, Desk page, assets, hooks, Makefile targets, scripts, UI specs, lifecycle/home/core references removed. Endpoints no longer routable. |
| XC-011 | H | Role `All` has create/write on Confirmed Tender Document Package and IT Tender Publication Record | If the two doctypes belong to retired TM2/legacy → removed with WP1.3; otherwise drop the `All` DocPerm and add the command guard. | Red | `kentender_procurement/tender_configurations/tests/test_publication_record_permissions.py` (4 tests, red before) | 2d630604 | reopened 7 Oct 2026 | Reopened 7 Oct: a publication record can still be created already Published and the configuration publication lock lifts with one save (REG-STATE-05: RG-05; legacy module RG-04). Both doctypes belong to Tender Configurations. `All` DocPerm removed (officer roles Tender Manager / Planning Authority instead); direct `status` / `package_status` change refused unless the service flag is set (all service call sites alread |
| XC-126 | M | Dropped-doctype crash class still present: post-sync patches and a whitelisted TM2 export touch dropped tables | See finding in `audit/FINDINGS.md`. | Green | `kentender_procurement/tests/test_patches_tolerate_dropped_tables.py::test_each_patch_is_a_no_op_when_its_tables_are_gone_and_safe_twice` (TableMissingError bef | 4e8995f2 | test site | TM2 export half closed by deletion; the three post-sync Planning patches now guard with `table_exists`. |

### WP1.4 — Supplier registry: role gates and registration

*XC-020 (guest self-registration) needs a decision — see open question Q5.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-004 | H | Supplier-registry state changes (suspend, reinstate, expire, qualify/reject category) have no role gate and wr | Named supplier-registry capability on every ktsm_* state-change endpoint; remove ignore_permissions. Test as plain internal user and as supplier account → refused. | Verified | kentender_suppliers/tests/test_ktsm_authorization.py::test_state_changes_refuse_plain_internal_and_supplier_accounts | b283453b | 7 Oct 2026 | regression sweep authorization + test site; Residual technical-role paths are tracked under XC-019 (RG-10, RG-11, RG-30). One `registry_access` module names each capability; API entry points gated. `governance._save` still uses ignore_permissions (see Follow-ups F1) |
| XC-018 | M | Supplier-registry reads and eligibility results are open to every logged-in account | See finding in `audit/FINDINGS.md`. | Verified | ...::test_registry_reads_refuse_plain_internal_and_supplier_accounts | b283453b | 7 Oct 2026 | regression sweep authorization + test site. whitelisted eligibility checks gated; suppliers read own status through ungated `compute_eligibility` after their own-supplier check |
| XC-019 | M | Supplier approval/return/reject are authorised by bare Frappe Roles (System Manager, "Approving Authority") | See finding in `audit/FINDINGS.md`. | Red | ...::test_system_manager_cannot_approve_return_reject_or_verify | b283453b | reopened 7 Oct 2026 | Reopened 7 Oct: Administrator passes every registry mutation capability, builder write endpoints use the read capability, System Manager/Administrator act for any supplier (REG-AUTHORIZATION-03/-04/-07: RG-10, RG-11, RG-30). technical roles removed from every mutation capability |
| XC-020 | M | Unauthenticated `ktsm_register` creates User, Supplier, profile and API-access rows with `ignore_permissions` | See finding in `audit/FINDINGS.md`. | Red | ...::test_ktsm_register_never_binds_an_existing_login / ..._creates_new_login_disabled_until_verified / ..._is_rate_limited | b283453b | reopened 7 Oct 2026 | Reopened 7 Oct: ktsm_register still writes unauthenticated with ignore_permissions and its disabled login can never be enabled (REG-AUTHORIZATION-06: RG-12). POST-only, 5/hour/IP, existing login never bound, new login disabled. Guest writes still need ignore_permissions (F2) |

### WP1.5 — Open reads: audit trail, catalogues, strategy consumers, drafts

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-009 | H | Audit-event read endpoints return any object's audit trail to any logged-in account | Gate sec_api_audit_events / sec_api_audit_tender_events by an oversight capability plus object-level read permission. | Verified | n/a | n/a | grep, 7 Oct | [No change needed (closed by deletion)] `tender_management/` no longer exists and `grep -rn sec_api_audit` over *.py/*.js is empty; no other whitelisted functio |
| XC-017 | M | Reference-data API lets a bare Frappe Role create further Procuring Entities and PE/FY contexts | See finding in `audit/FINDINGS.md`. | Red | kentender_core/tests/test_reference_data_single_entity.py::test_a_role_holder_cannot_create_a_second_procuring_entity | 63a06c57 | reopened 7 Oct 2026 | Reopened 7 Oct: a Reference Data Manager can still create a second Procuring Entity through /api/resource; the rule lives only in the API (REG-AUTHORIZATION-02: RG-07). Guard is at the API layer (`require_single_entity`); services stay callable for seeds/legacy tests (F3) |
| XC-021 | M | Frappe User Permission is read in a production path reachable from whitelisted endpoints | See finding in `audit/FINDINGS.md`. | Red | kentender_core/tests/test_pe_scope_without_user_permission.py::test_user_permission_alone_offers_no_entity | 2e62762b | reopened 7 Oct 2026 | Reopened 7 Oct: journey list still reads tabUser Permission and User Scope Assignment still feeds the entity offer (REG-AUTHORIZATION-10/-11: RG-32, RG-33). A user with a responsibility in force works in the site PE; seeds that only grant User Permission now yield no context (see Needs browser check) |
| XC-022 | M | A department reader can fetch unpublished Internal Tender documents by digest | See finding in `audit/FINDINGS.md`. | Verified | kentender_procurement/tenders/tests/test_documents.py::test_a_department_reader_cannot_fetch_an_unpublished_document_or_the_digests_that_address_it (red proven  | d3f95e38 | 7 Oct 2026 | regression sweep authorization + test site. test_read has 3 failures on workspace counts (lines 71/156/219, `ws["counts"]`), unrelated to department mode; likely test-site residue (not investigated) |
| STR-005 | M | Strategy consumer endpoints open to every signed-in account; lineage ignores version status | See finding in `audit/FINDINGS.md`. | Verified | kentender_strategy/tests/test_ovs_strategy_reads.py::test_a_portal_account_is_refused_every_consumer_endpoint, ::test_lineage_of_a_version_awaiting_approval_is_ | b07f04e3 | 7 Oct 2026 | regression sweep authorization + test site; create_strategy_snapshot write behind the read gate is RG-34. `create_strategy_snapshot` API still writes audit/journal rows for any internal user (F4) |
| NDS-003 | M | AO, HOPF and Planner receive an author's unsent Draft successor through get_departmental_need | See finding in `audit/FINDINGS.md`. | Verified | departmental_needs/tests/test_departmental_needs_unsent_draft.py::test_the_planner_and_the_oversight_offices_do_not_receive_the_draft | 9a28582c | 7 Oct 2026 | regression sweep authorization + test site. `get_departmental_need` and the register list show the accepted revision, not the author's Draft successor, to Planner / AO / HOPF. |
| REQ-007 | M | Draft and in-review requisitions are readable by every site-wide role | See finding in `audit/FINDINGS.md`. | Blocked | n/a |  |  | [Blocked (Follow-up only, per lead)] SPEC GAP, owner decision needed (F5); nothing implemented |
| XC-029 | L | `list_organisation_units` serves the unit catalogue to portal accounts the doctype itself refuses | See finding in `audit/FINDINGS.md`. | Verified | kentender_core/tests/test_reference_data_single_entity.py::TestOrganisationUnitCatalogueIsInternal | 63a06c57 | 7 Oct 2026 | regression sweep authorization + test site. |

### WP1.6 — Destructive patches and fresh-site safety

*A patch must never delete DocType records the app still ships.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-125 | M | A post-model-sync patch deletes the DocType records of two doctypes the app still ships, and the next patch wi | See finding in `audit/FINDINGS.md`. | Green | kentender_strategy/tests/test_str_patch_guards.py (mocked db; red = HEAD patches list "Strategy Node"/"Strategic Plan" and run an unconditional DELETE, shown by | 9451a490 | test site: 4 OK | Strategy doctype folders unchanged from HEAD (git diff --stat empty) |
| XC-127 | M | One-shot destructive patches have no environment or non-empty guard | See finding in `audit/FINDINGS.md`. | Green | kentender_procurement/tests/test_destructive_patch_guards.py (mocked db) | 46337d10 | test site: 5 OK | Five patches guarded via `kentender_core.utils.patch_guards.require_empty_or_authorised`; p6 table_exists bug fixed. Note `Tender Evidence Requirement` is shipp |

## Wave 2 — Stop REST from bypassing the approval rules

**Goal:** Build one shared "command-only write" guard (Award and Evaluation already use the pattern) and apply it to every state-bearing doctype; remove business-role write on lifecycle/approval fields; make approved records and the audit log immutable to everyone including System Manager.

**Exit gate:** Re-run sweep-state-machine and sweep-authorization; a REST PUT/DELETE test per doctype family is refused; every module’s own test suite still passes on the test site (seeds/tests that wrote directly are moved to services).

### WP2.1 — Build the shared command-only write guard (no finding; infrastructure)

*Reuse the Award/Evaluation command-flag pattern as one helper in kentender_core. Acceptance: REST PUT/DELETE/set_value on a guarded doctype is refused; the owning service succeeds.*

| Task | Status | Notes |
|---|---|---|
| Build and document the helper; unit-test it | Todo | |
| Dry-run on one doctype in the test site before rolling out | Todo | |

### WP2.2 — Strategy doctypes

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-005 | H | Strategy Author can set a plan version Active (or edit an Active version) over REST; approval, readiness and s | Command-only write guard on Strategic Plan Version / Plan / Node / Indicator / Target; remove write DocPerm on status and approval fields. REST PUT status=Active → refused. | Verified | kentender_strategy/tests/test_str_aud_remediation.py::TestCommandOnlyWrites (6 tests: user save/delete of all 5 doctypes refused with COMMAND_ONLY_WRITE/DELETE  | 2bbbfdc8 | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site; Strategy Command Journal still unguarded (RG-40). Strategic Plan, Strategic Plan Version, Strategy Node, Performance Indicator, Performance Target use `CommandWriteGuardMixin`, family "Strategy", no user-editable fields, no user insert. Every service write (draft save/create, successor, discard, structure save, Approve/activate/supersede, Submit/Return)  |

### WP2.3 — Budget doctypes

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-006 | H | Budget Officer / Budget Approver can write version status and approved amounts over REST | Same guard on Budget Version / Line Version / Budget; approved amounts and status only via services. | Verified | kentender_budget/tests/test_budget_command_only_writes.py::TestBudgetRecordsAreCommandOnly (9 tests: save refused for Officer/Approver/dual/Administrator on all | 0250ccf6 | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site. Controllers of all 10 Budget doctypes use `CommandWriteGuardMixin`, family `Budget` (`services/budget_write_family.py`, `budget_write()`); every service insert/save/delete runs inside `with budget_write():`. DocPerm: write/create/delete/submit/share removed from every role incl. System Manager (Administrator is stopped by the guard, not the DocPerm). Red |

### WP2.4 — Planning doctypes and projections

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-007 | H | Procurement Planner and Departmental Author / HoD can write Annual Plan and Departmental Plan lifecycle fields | Same guard on Annual Plan, Annual Plan Version, Plan Item, Plan Source Allocation, Departmental Plan Entry. | Verified | procurement_planning/tests/test_rest_bypass_guard.py (5 tests: client set_value as Planner/Author/HoD/Administrator on all 7 doctypes refused, `save()` refused  | 07450f0c | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site; Closed for the 7 doctypes it names; the other Planning doctypes are RG-02. Family `Procurement Planning`: Annual Plan, Annual Plan Version, Annual Plan Item, Plan Source Allocation, Departmental Plan, Departmental Plan Version, Departmental Plan Entry. `envelope.bump` and every service command that inserts/saves/deletes them open the window (`planning_co |
| XC-014 | M | Need Planning Intake Projection is writable and deletable by six roles including Auditor | See finding in `audit/FINDINGS.md`. | Verified | departmental_needs/tests/test_rest_bypass_guard.py::TestPlanningIntakeProjectionIsReadOnly | f34b2c3b | 7 Oct 2026 | regression sweep authorization, state-machine + test site. Intake projection is in the Needs family; only `project_planning_intake` writes it; no role (Auditor, Planner, Author, HoD, System Manager, Administrator) can write, create or delete. The two sibling projections are in the same family. |

### WP2.5 — Needs doctypes

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-008 | H | Departmental Author / HoD can write Need, Revision, Review Task and Withdrawal Request lifecycle fields over R | Same guard on Need, Revision, Review Task, Withdrawal Request; accepted revisions cannot be flipped to Draft by REST. | Verified | departmental_needs/tests/test_rest_bypass_guard.py::TestNeedRecordsAreCommandOnly (incl. the audit's Accepted-revision `revision_status="Draft"` + title rewrite | f34b2c3b | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site; Need Event/Decision are outside the family (RG-08, RG-09). Family `Departmental Needs`: Need, Revision, Review Task, Withdrawal Request and the three projections. The nine lifecycle commands and three `project_planning_*` commands are `@needs_command`. Decision and Event doctypes left as they were (Decision already read-only; Event: Follow-ups 5). |
| XC-015 | M | Need Revision / Withdrawal Request have no scope hook; Planner and Author reads are wider than NDS section 6 | See finding in `audit/FINDINGS.md`. | Red | departmental_needs/tests/test_rest_bypass_guard.py::TestNeedReadScope (list and direct route agree for every Need and role for Author, HoD, Planner; Planner rea | f34b2c3b | reopened 7 Oct 2026 | Reopened 7 Oct: Departmental Need Decision has business-role read and no scope hook (REG-AUTHORIZATION-05: RG-09). `departmental_needs/services/need_authorization.py` registered as has_permission and permission_query_conditions for the 7 Needs doctypes in `hooks.py` (replacing the generic core predicate for Need and Review Task). One SQL predicate and one record test over the same inputs. Revision and Withdrawal Requ |

### WP2.6 — Requisition and other approved records

*System Manager/Administrator lose write/delete on decisions, evidence, handoffs, reservations and assignments.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-013 | M | System Manager / Administrator hold write/delete on decision, evidence, handoff, reservation and assignment re | See finding in `audit/FINDINGS.md`. | Red | kentender_core/tests/test_assignment_command_only.py::TestAssignmentRecordIsCommandOnly (DocPerm test observed failing on the first run, before the DocPerm chan | a1d9d92a (helpers), a250b0ce (assignment), 0bd6dd19 (Requisitions + Tenders), ac1aa3b8 (legacy assignment doctypes) | reopened 7 Oct 2026 | Reopened 7 Oct: about 35 Planning decision/evidence/journal doctypes, Departmental Need Event and Strategy Command Journal still writable by System Manager/Administrator; child-table rows unguarded (REG-AUTHORIZATION-01, REG-SOD-02, REG-STATE-02/-04: RG-02, RG-06, RG-08, RG-40). Requisition (10 top-level doctypes), Tender (15) and User Responsibility Assignment: write/create/delete DocPerm removed for System Manager, |
| XC-025 | L | Requisition package, event, journal and outcome doctypes have business-role read DocPerm and no registered hoo | See finding in `audit/FINDINGS.md`. | Verified | kentender_procurement/procurement_requisitions/tests/test_requisition_authorization.py::TestFamilyRecordsReadThroughTheirRequisition (4 tests) | 1c1b1cd | 7 Oct 2026 | regression sweep authorization + test site. Package, Package Version, Requisition Event, Correction Outcome, Command Journal join the existing Requisition `permission_query_conditions` / `has_permission` delegation (`_CHILD_LINK`; the journal reads through the record it names). Registered through the Requisition module's own predicate, not `kentender_scope_map`, because a Requisition has no single organisation_unit c |

### WP2.7 — Audit Event immutability

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-010 | H | `Audit Event` is writable and deletable by System Manager, and Strategy's no-self-approval check reads it | Audit Event controller refuses update/delete; remove write/delete from System Manager and Administrator. | Verified | kentender_core/tests/test_audit_event.py::TestAuditEventIsAppendOnly (update, delete, insert refused for System Manager and Administrator; confirmed failing wit | 701a2edf | 7 Oct 2026 | regression sweep authorization, state-machine + test site. Helper `kentender_core/services/command_write_guard.py`. Audit Event controller = `CommandWriteGuardMixin`, family "Audit Event", no editable fields. DocPerm: System Manager and Administrator read/report/export/print/email only (write/create/delete/share removed); track_changes 0. Only writer: `log_audit_event` (opens `command_write("Audit Event")`). Only del |

### WP2.8 — Legacy authorization engine and role self-grant

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-026 | L | Legacy AUTH-G04 engine (Operational Scope Assignment, Capability Profile) is still writable and still authoris | See finding in `audit/FINDINGS.md`. | Verified | kentender_core/tests/test_legacy_authorization_retired.py (4 tests) | ac1aa3b8 | 7 Oct 2026 | regression sweep authorization + test site; Code only, dev data not cleaned; User/Strategy Scope Assignment are RG-32. `evaluate_capability` is a stable denial (`LEGACY_AUTHORIZATION_RETIRED`); removed `add_assignment`, `revise_routing_rule`, `claim_my_work_task`, `workflow_tasks.py`, `workflow_routing.py`, the administration writers, and the gate01-04 tests of the retired behaviour; Operational Scope Assignment, Cap |
| XC-136 | L | Nothing stops an assignment administrator granting business roles to themselves or Administrator; registry `so | See finding in `audit/FINDINGS.md`. | Red | kentender_core/tests/test_assignment_command_only.py::TestGrantRules (6 tests) | a250b0ce | reopened 7 Oct 2026 | Reopened 7 Oct: refusal is grant-time only; a later System Manager grant to a holder, technical principal denied for READ only, sod_tags unconsumed (REG-SOD-07: RG-39). `grant` and `update_scheduled` refuse granting to yourself (`AUTH_SEGREGATION_BLOCKED`) and granting to a technical account (`AUTH_CONFIGURATION_INVALID`); `preview_assignment` returns the same refusals as a `user` problem. Exception found by running  |

## Wave 3 — Money correctness

**Goal:** Lock-then-read-under-lock for every Budget check-and-write, one shared lock set, exact decimals end to end, stale-write protection mandatory, Award/Evaluation re-read Budget.

**Exit gate:** Re-run sweep-money-concurrency; two-process race tests on the test site pass; Decimal property tests at the ceiling/limit boundaries.

### WP3.1 — Budget locking under REPEATABLE READ (confirmed)

*One ordered lock set shared by reserve, adjust, approve, close and the Finance decision; re-read under a locking read.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-101 | H | `reserve_funding` can oversubscribe a Budget Line: lock is taken, availability is then read from a pre-lock sn | Take line locks, then re-read sums with a locking read. Two-process test: two 80m reservations on a 100m line → second refused. | Verified | tests/test_budget_locking_races.py::test_two_80m_reservations_on_a_100m_line_cannot_both_succeed (+ ::test_a_reservation_waiting_on_a_reservation_decides_on_the | dfb23492 | 7 Oct 2026 | regression sweep money-concurrency + test site. Real two-connection test (threads, own frappe.init/connect, REPEATABLE-READ). All 9 race tests FAILED on the pre-fix services (HEAD copies swapped in temporarily) and pass now. |
| XC-102 | H | `adjust_commitment` increase is not serialised against the Budget Line or against reservations | adjust_commitment locks the Budget Line with the same lock key as reserve and re-reads under lock. | Verified | ::test_two_commitment_increases_of_20m_cannot_both_succeed, ::test_a_commitment_increase_waits_for_a_reservation_on_the_same_line | dfb23492 | 7 Oct 2026 | regression sweep money-concurrency + test site. |
| XC-103 | H | Budget approval/closure and reservation take disjoint lock sets, so successor approval or closure can race a r | Approve/close lock the version’s lines in the same ordered lock set as reserve. | Verified | ::test_approval_waits_for_a_racing_reservation_and_rechecks_the_floor, ::test_a_reservation_waits_for_an_approval_and_uses_the_new_basis, ::test_closure_waits_f | dfb23492 | 7 Oct 2026 | regression sweep money-concurrency + test site. Both orderings of approve-vs-reserve and close-vs-reserve. |
| XC-104 | H | Finance decision "serialised basis" is validated with stale reads after the lock | Finance decision re-reads Version status and line versions with locking reads after the lock. | Verified | ::test_decision_basis_waits_for_an_approval_and_fails_stale | dfb23492 | 7 Oct 2026 | regression sweep money-concurrency + test site. Raises BUD_BASIS_STALE after waiting behind an approval. |
| BUD-003 | M | A Closed Budget can be re-activated by an already-open successor | See finding in `audit/FINDINGS.md`. | Verified | tests/test_budget_approval_integrity.py::TestClosedBudgetStaysClosed | dfb23492 | 7 Oct 2026 | regression sweep state-machine, money-concurrency + test site. Approving an open successor of a Closed Budget returns BUDGET_CLOSED; successor creation is lock-serialised (no DB constraint, see follow-ups). |
| BUD-004 | M | `Procurement Commitment.contract` is unique table-wide | See finding in `audit/FINDINGS.md`. | Verified | ::TestOneContractOnSeveralReservations (three tests incl. patch double-run) | 6a88d4fc | 7 Oct 2026 | regression sweep money-concurrency + test site; Index exists only through a patch, a fresh install lacks it (REG-MONEY-07, RG-20). Key is now (contract, reservation). |

### WP3.2 — Other check-then-act races

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-107 | M | Requisition drawdown rechecks (correction hold, Plan Item state, record version) read a pre-lock snapshot | See finding in `audit/FINDINGS.md`. | Red | procurement_planning/tests/test_drawdown_races.py::TestDrawdownSnapshotRaces (3 real two-connection snapshot races: hold, record version, item state) | aca30f93 | reopened 7 Oct 2026 | Reopened 7 Oct: funding_state and drawn totals still read from the snapshot after the Plan Item lock (REG-MONEY-10: RG-23). `envelope.locked()` in Planning and Requisitions now loads with `for_update=True` (locking read, children included) after the row lock. All three races bypassed the check before the fix (drawdown succeeded). |
| XC-108 | M | Award cancellation guard reads `notification_status` from a stale snapshot after taking the Award Case lock | See finding in `audit/FINDINGS.md`. | Verified | award/tests/test_awd_authority.py::test_a_cancellation_that_waited_on_the_case_lock_sees_the_notices_issued_meanwhile | b6181d2d | 7 Oct 2026 | regression sweep state-machine, money-concurrency + test site. `cancellation_guard` reads `notification_status` with `for_update=True`. `award/services/records.lock` was already a locking read (fixed under AUD-XC-130). |
| XC-109 | M | Requisition revocation and handoff consumption take row locks in opposite order (AB-BA) | See finding in `audit/FINDINGS.md`. | Verified | procurement_requisitions/tests/test_authorise.py::test_consumption_queues_on_the_requisition_root_without_holding_the_handoff | b7d36e35 | 7 Oct 2026 | regression sweep money-concurrency + test site. One published lock order: Requisition root, then Authorised Requisition Handoff (authorise and revoke already did; consumption now does). The test holds the root in one connection and proves consumption, while waiting, does not hold the handoff row. Red confirmed by temporarily restoring the old order (lock-wait timeout on the handoff). |

### WP3.3 — Budget approval integrity

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-105 | H | Budget no-self-approval reads the FIRST submission event, and fails open when the event was never written | Read the current submission attempt’s event, fail closed when none exists, and make the audit write non-swallowing. | Verified | ::TestNoSelfApprovalOfTheCurrentAttempt (4 tests) | dfb23492 | 7 Oct 2026 | regression sweep sod, state-machine, money-concurrency + test site. Latest submit event; fail closed while Submitted for approval; submit audit write not swallowed (savepoint); locked row's submitted_by rechecked after the lock. |
| BUD-001 | H | Owner-scope and source-OU eligibility not enforced where money moves | Enforce owner-scope and funding-source eligibility at check and reserve; reject a missing source OU. | Verified | ::TestOwnerScopeAndSourceUnit (3 tests) | dfb23492 | 7 Oct 2026 | regression sweep authorization, money-concurrency + test site. BUDGET_SOURCE_OU_REQUIRED / BUDGET_LINE_NOT_ELIGIBLE in check and reserve. Funding-source half only when the caller supplies one (follow-up 1). |
| BUD-002 | H | Return/resubmit keeps no immutable submission-attempt snapshot | Persist an immutable snapshot per submission attempt; return/resubmit never overwrites it. | Verified | ::TestSubmissionAttemptSnapshot (2 tests) | dfb23492 | 7 Oct 2026 | regression sweep state-machine, money-concurrency + test site. New doctype Budget Submission Attempt; exposed as `attempts` in get_budget_version_history. |
| BUD-010 | M | Disabled or inactive Organisation Unit / Funding Source never rechecked on line save or approval | See finding in `audit/FINDINGS.md`. | Verified | ::TestCatalogueStateOfNewLines (2 tests) | dfb23492 | 7 Oct 2026 | regression sweep money-concurrency + test site. New lines only (see follow-up 3). |

### WP3.4 — Funding re-read at Award and Evaluation (fail closed)

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| AWD-002 | H | Funding is never re-read from Budget and an unavailable funding (or validity) read permits a positive award | Award re-reads Budget through its published read at decision time; unavailable or unknown = refuse (fail closed). | Verified | `award/tests/test_awd_funding.py::TestFundingAtDecision::{test_budget_unavailable_refuses_a_positive_award, test_an_absent_funding_block_in_the_report_is_not_tr | c70ceaf9 | 7 Oct 2026 | regression sweep money-concurrency + test site. Red observed: 3 tests failed ("AwardError not raised") on the first run. Before that, the fix was wrong because an empty `Guards` is falsy, so `g or Guards()` threw the collector away. The tests exposed it. |
| EVL-014 | M | Evaluation's funding read runs as the session user and swallows every failure | See finding in `audit/FINDINGS.md`. | Verified | evl/test_evl_funding.py (4 tests) + kentender_budget/tests/test_budget_funding_read.py | b07e043a | 7 Oct 2026 | regression sweep state-machine, money-concurrency + test site. New Budget published read `kentender_budget/services/budget_funding_read.read_reservation_funding` (in-process, not whitelisted, no session-role dependency); Evaluation uses it; a failed or incomplete read is a typed `Unavailable` funding fact that qualifies the report. |

### WP3.5 — Exact decimals end to end

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-115 | M | Plan affordability and method-limit tests compare float sums with a 1e-9 epsilon | See finding in `audit/FINDINGS.md`. | Verified | procurement_planning/tests/test_plan_exact_money.py::TestExactPlanningSums (red observed against the old code: `line_totals` returned `{'BL-1': 184132482.070000 | 07450f0c | 7 Oct 2026 | regression sweep money-concurrency + test site. Decimal sums via `money.sum_money`; `money.exceeds`/`same_amount` replace the 1e-9 / 0.005 tolerances in readiness, profiles, budget_revision, departmental_update, plan_read; totals reach Budget as decimal strings. Budget-side epsilon is WP3.x's. |
| XC-116 | M | Budget position, floor and `Needs Attention` tests use float arithmetic | See finding in `audit/FINDINGS.md`. | Verified | kentender_budget/tests/test_budget_exact_money.py::TestExactPositions (fully subscribed line = exactly 0.00 and not Needs Attention; floor admits exactly reserv | 0250ccf6 | 7 Oct 2026 | regression sweep money-concurrency + test site. `_line_position_exact` (Decimal, sums read as exact text) is used by every decision: revalidate (Needs Attention), floor in readiness/omit, adjust increase, reserve availability, both affordability checks. `_line_position` stays as the float display view of the exact result. |
| XC-117 | M | Money inputs are not validated as exact decimals: NaN/Inf, excess scale, 0.01 and 0.0001 tolerances | See finding in `audit/FINDINGS.md`. | Red | test_budget_exact_money.py::TestExactInputs (parse rules, line save, allocation, reconcile, release/convert/adjust, no tolerance) | 0250ccf6 | reopened 7 Oct 2026 | Reopened 7 Oct: Planning DPP amount/quantity not exact-validated (NaN passes, excess scale rounded) and huge integers raise untyped InvalidOperation (REG-MONEY-05/-06: RG-03, RG-29). `services/budget_money.py` (`parse_money`/`check_money`): NaN/Inf, exponent, excess scale, overflow, bool/blank refused with `BUDGET_MONEY_PRECISION_INVALID`, nothing rounded. 0.01 (reconcile, transfer balance, summary sentences) and 0.0 |
| XC-118 | M | Need quantity is a 3-decimal Float with no unit-of-measure precision or whole-number rule | See finding in `audit/FINDINGS.md`. | Verified | departmental_needs/tests/test_departmental_needs_lifecycle.py::TestDraftContentBounds (whole-number unit, exact scale, non-decimal/overflow, submit recheck). Re | f34b2c3b | 7 Oct 2026 | regression sweep state-machine, money-concurrency + test site; Needs lifecycle module has one unrelated environmental error on the gate (INT-B E-4). New code `NDS_QUANTITY_PRECISION_INVALID` (in NDS v1_16 §9). Validated at draft save (service and controller) and at submit; the unit's rule is the native ERPNext UOM `must_be_whole_number`; the Needs seed declares Each whole-number. The old pinned test (`NDS_FIELD_REQUI |
| XC-129 | L | Frappe `Currency` storage (decimal 21,9) cannot hold the 18 integral digits the documents require | See finding in `audit/FINDINGS.md`. | Red | test_budget_exact_money.py::TestExactInputs::test_parse_money_accepts_exact_amounts_and_refuses_the_rest (12-digit limit) | 0250ccf6 | reopened 7 Oct 2026 | Reopened 7 Oct: refusal is typed but limited to 12 integral digits, 18 required, storage decision open (money-concurrency sweep PARTIAL, no REG id: RG-28). Not practical to fix by patch: see Follow-up 2. An amount the column cannot hold (more than 12 integral digits) now fails typed before any write instead of as a database error. Needs the owner's storage decision. |
| XC-132 | L | Reservation "required" amount is rounded half-up to the cent | See finding in `audit/FINDINGS.md`. | Blocked |  |  |  | [Blocked (unchanged, owner decision)] Left as WP3.5 recorded it. |
| XC-133 | L | Currency and precision are hard-coded in Planning and Budget reads | See finding in `audit/FINDINGS.md`. | Red | procurement_planning/tests/test_plan_exact_money.py::TestCurrencyBasisIsNotDefaulted | 07450f0c | reopened 7 Oct 2026 | Reopened 7 Oct: check/reserve fixed at scale 2, Requisitions CURRENCY constant KES, Tenders snapshot constants (money-concurrency sweep PARTIAL, no REG id: RG-28). Snapshot, requisition hand-off and financial basis take the currency from `resolve_budget_context` and the precision from the Budget statement or the captured basis; missing value blocks (`PLN_REFERENCE_UNAVAILABLE` / `PLN_MONEY_PRECISION_INVALID`). `finan |

### WP3.6 — Stale-write protection and idempotency

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-119 | M | Budget optimistic-lock stamp is optional on every command, and a line save never moves it | See finding in `audit/FINDINGS.md`. | Verified | kentender_budget/tests/test_budget_optimistic_lock.py::TestTheStampIsMandatory, ::TestALineSaveMovesTheStamp | 0250ccf6 | 7 Oct 2026 | regression sweep state-machine, money-concurrency + test site. `expected_modified` is mandatory on draft save, line save, submit, return, approve and close (missing or different = `BUDGET_STALE_WRITE`); decided again on the locked row for draft save, line save, return, approve, close. A line save now saves the Version, so the stamp advances. Red proven by mutation (stamp optional again: the new tests fail). Strategy  |
| XC-120 | M | Strategy idempotency journal is keyed without payload, replays before authorisation, and its race leaves dupli | See finding in `audit/FINDINGS.md`. | Verified | kentender_strategy/tests/test_str_idempotency_envelope.py::test_same_key_with_another_payload_is_a_typed_conflict, ::test_same_key_for_another_command_is_a_type | 8753be14 | 7 Oct 2026 | regression sweep state-machine, money-concurrency + test site. Journal row now carries actor + payload hash; unique-insert claim inside the command transaction; typed STRATEGY_IDEMPOTENCY_CONFLICT / _REQUIRED / STRATEGY_VERSION_REQUIRED. Existing code also caught the wrong exception (a unique-index violation is `UniqueValidationError`, not `DuplicateEntryError`), so the old race branch never ran. |
| BUD-006 | M | `save_budget_lines_draft` is not one validated change set | See finding in `audit/FINDINGS.md`. | Verified | test_budget_optimistic_lock.py::TestALineSaveIsOneChangeSet (3 tests) | 0250ccf6 | 7 Oct 2026 | regression sweep money-concurrency + test site; Server side; the Vue editor half is BUD-007. Line save validates every row, writes inside a savepoint and rolls the whole set back if any row is refused (or an exception is raised); the stamp does not move on a refused set. |
| BUD-007 | M | Editor lost-on-save race and line-scope stamp that never changes | See finding in `audit/FINDINGS.md`. | Green | server: test_budget_optimistic_lock.py::TestALineSaveMovesTheStamp::test_a_second_line_save_with_the_pre_first_stamp_is_refused | 0250ccf6 | test site; bundle rebuilt | [Green (server); UI Todo browser check] `BudgetVersionEditorScreen.vue`: the dirty signature is the one of the values SENT (taken before the request), and every |
| XC-130 | L | Typed stale-version / idempotency errors are unreachable under real concurrency; reference generators read sta | See finding in `audit/FINDINGS.md`. | Red | award/tests/test_awd_command_envelope.py::test_two_requests_with_one_key_execute_once_and_both_get_the_result and ::test_a_stale_revision_is_the_typed_refusal_n | a394d872 (Award), 2e1721eb (Evaluation), 641b6cc6 (reference allocators) | reopened 7 Oct 2026 | Reopened 7 Oct: Bid Opening and Proceedings still lock then read a snapshot; Bid Submission and per-case sequences use count()+1 (REG-MONEY-02/-03/-04, REG-STATE-06: RG-17, RG-18, RG-19). Planning, Needs, Requisition, Tenders, Opening and Proceedings lock helpers and reference generators: see Follow-ups. |
| XC-131 | L | Idempotent replay is answered before authorisation and from a user-blind key lookup | See finding in `audit/FINDINGS.md`. | Red | Strategy: ::test_a_caller_without_the_responsibility_gets_no_replay; Award: award/tests/test_awd_command_envelope.py::test_a_replay_is_refused_when_the_actor_no | 8753be14 (Strategy), a394d872 (Award), 2e1721eb (Evaluation) | reopened 7 Oct 2026 | Reopened 7 Oct: Budget, Bid Opening, Proceedings and Bid Submission journals still key-first, user-blind or optional (REG-MONEY-01/-02/-03, REG-STATE-07: RG-16, RG-17, RG-18). Needs, Planning, Requisition, Tenders envelopes left to the later pass: see Follow-ups. |

## Wave 4 — Segregation of duties and approval integrity

**Goal:** Award chain per the owner rule, evaluator/conflict rules, Requisition maker-checker on every path, Tender late-change gates, Strategy structure edits confined to their own Draft version.

**Exit gate:** Re-run sweep-sod; role×command refusal matrices pass; module suites pass.

### WP4.1 — Award chain roles (owner decision)

*Only HOPF prepares/signs the professional opinion, handles supplier correspondence and restrictions; only AO records the decision (Award / No award / Return); no other role, enforced server-side on every command and on effective dates.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| AWD-001 | H | No segregation of duties anywhere in the evaluation → opinion → award-decision chain | See WP4.1. Role × command refusal matrix; HOPF-only opinion, correspondence and restrictions; AO-only decision; no other role. | Red | `award/tests/test_awd_role_matrix.py::TestAwardRoleMatrix::{test_every_command_refuses_every_non_permitted_role, test_the_person_who_signed_the_opinion_cannot_r | c70ceaf9 | reopened 7 Oct 2026 | Reopened 7 Oct: Award side closed; evaluation side open, AO/HOP can sit on the committee and sign reports, owner decision needed (REG-SOD-04: RG-15). The tests were written together with the fix, so a separate red run was not observed. The role x command matrix existed nowhere before. The authority gate itself (`authorise_record`, which honours effective dates) already refused non-HOP and non-AO users on every comman |
| AWD-003 | M | Heads of Procurement can end an authoritative order or a funding restriction with free-text "evidence" | See finding in `audit/FINDINGS.md`. | Verified | `test_awd_restrictions.py::test_a_tenders_order_cannot_be_ended_by_free_text`, `test_awd_funding.py::TestFundingRestrictionEvidence::test_free_text_does_not_cle | c70ceaf9 | 7 Oct 2026 | regression sweep sod + test site; Manual external orders still accept free text by design (D2). Red not separately observed. A Tenders-sent order now ends only on the stored Tenders release event, with that event's reference as the evidence. A Funding issue clears only when Budget's live read confirms (a system sync), and reopens on a later shortfall (the source-event key now includes a counter). A manually recorded  |
| AWD-011 | M | Return to Evaluation dead-ends when the Head of Procurement who received the report is replaced | See finding in `audit/FINDINGS.md`. | Verified | `test_awd_role_matrix.py::TestReplacedHeadOfProcurement::test_the_current_hop_can_return_a_report_the_replaced_hop_received` | c70ceaf9 | 7 Oct 2026 | regression sweep sod + test site. Red not separately observed. The synthetic source now mimics Evaluation's "recipient only" rule (raises Not found). Award passes the recorded recipient to the seam and names the current HOP in the comment and in Award's audit. Evaluation was not edited (see follow-up 2). |
| AWD-015 | L | `retry_operation` authority ignores effective dates | See finding in `audit/FINDINGS.md`. | Verified | `test_awd_role_matrix.py::TestAwardRoleMatrix::test_retry_operation_rechecks_the_technical_operator_effective_dates` | c70ceaf9 | 7 Oct 2026 | regression sweep authorization, sod + test site. Red not separately observed. `people.is_technical_operator` runs `authorise_record`, which honours the effective period. `technical_operators()` and `retry_operation` now use it. |

### WP4.2 — Evaluation integrity

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| EVL-001 | H | A conflicted evaluator can clear their own declared conflict and regain bid access | A re-declaration cannot supersede a declared conflict; only the Accounting Officer’s resolve action can. | Verified | evl/test_evl_committee.py::TestDeclarationAndReplacement::test_a_conflicted_member_cannot_clear_their_own_conflict | 5efa26ac | 7 Oct 2026 | regression sweep authorization, sod + test site. A conflicted member re-declaring "No conflict to declare" is refused (EVL_MEMBER_INELIGIBLE, reason declared_conflict); only the AO's replacement ends it. |
| EVL-002 | H | A committee-recorded qualified report on an unresolved requirement or price discrepancy can never be frozen fo | Allow freezing a qualified report with unresolved items recorded as such, as the document specifies. | Green | evl/test_evl_discussion.py::TestQualifiedReport::test_a_qualified_unresolved_requirement_can_be_frozen_for_signing | bdb29777 | test site, module tests | A bid whose every unresolved requirement carries a committee "Qualified report" conclusion is not pending: comparison outcome "Qualified report", no recommendat |
| EVL-003 | H | One member's evidence finding resolves a price-arithmetic discrepancy (or a missing rule) and the bid is ranke | A price-arithmetic discrepancy or missing rule cannot be cleared by a member’s "Meets" finding. | Green | evl/test_evl_discussion.py::TestPriceDiscrepancy::{test_a_member_finding_cannot_resolve_the_discrepancy, test_even_a_committee_conclusion_cannot_resolve_it_but_ | bdb29777 | test site, module tests | A price-arithmetic discrepancy or a missing/unavailable rule cannot be resolved by a member finding or committee conclusion (refused at record time and ignored  |
| EVL-004 | M | `retry_delivery` completes and hands over a report with no suspension, roster or validity recheck | See finding in `audit/FINDINGS.md`. | Green | evl/test_evl_report.py::TestSendAndSign::{test_a_retry_does_not_deliver_through_a_suspension, test_a_retry_after_validity_expired_returns_a_positive_recommendat | a3533154 | test site, module tests | `retry_delivery` now rechecks (suspension/cancellation/roster/source impact) and the validity withdrawal, and completes the Proceedings record once. Also: `with |
| EVL-005 | M | A pending opening-supplement impact does not block freezing, and a "material" impact triggers no recalculation | See finding in `audit/FINDINGS.md`. | Green | evl/test_evl_report.py::TestSendAndSign::{test_a_pending_opening_update_blocks_freezing_until_assessed, test_a_material_opening_update_recalculates_and_withdraw | a3533154 | test site, module tests | Unassessed opening supplements block freezing and delivery; "Findings need review" withdraws signing and reruns the checks (new run, reason "Opening supplement" |
| EVL-006 | M | A participant who is no longer an eligible member can still sign the verification report | See finding in `audit/FINDINGS.md`. | Verified | evl/test_evl_diligence.py::TestReport::{test_a_participant_who_is_no_longer_eligible_cannot_freeze_or_sign, test_a_participant_who_became_conflicted_after_freez | 5efa26ac | 7 Oct 2026 | regression sweep sod + test site. `diligence.sign` and the lead's `send_for_signing` require current eligibility. |
| EVL-007 | M | `return_report` has no check that the delivery is the current, unreturned one | See finding in `audit/FINDINGS.md`. | Verified | evl/test_evl_report.py::TestAfterDelivery::test_a_return_applies_only_to_the_current_unreturned_delivery | a3533154 | 7 Oct 2026 | regression sweep state-machine + test site. Both return routes require case state "Report sent" and a not-yet-returned delivery. |
| EVL-010 | M | A conflicted or unavailable member who is also the secretary keeps bid access | See finding in `audit/FINDINGS.md`. | Verified | evl/test_evl_reads.py::TestMemberSecretary::{test_a_conflicted_member_secretary_loses_bid_access, test_an_unavailable_member_secretary_loses_bid_access} | 5efa26ac | 7 Oct 2026 | regression sweep authorization, sod + test site. A secretary who is also an appointed member reads as that member: not eligible = no bid/evidence/report access. Secretary write commands are not restricted (see Follow-ups). |
| EVL-013 | M | Independent-opening-member exclusion from evaluation works in one order only | See finding in `audit/FINDINGS.md`. | Verified | evl/test_evl_committee.py::TestAppointment::test_a_person_already_on_the_evaluation_committee_cannot_be_the_independent_opening_member | 5efa26ac | 7 Oct 2026 | regression sweep sod + test site. Symmetric, as instructed by the lead. Bid Opening's `appointment.validate` (and candidate list) now ask Evaluation's new published read `bid_evaluation/services/opening_seam.committee_members`. |
| EVL-016 | M | The secretary reads every bid with no declaration or confidentiality acceptance | See finding in `audit/FINDINGS.md`. | Blocked |  |  |  | SPEC GAP: EVL is silent on whether the secretary declares. Logged as a follow-up with a recommended default; no code change. |

### WP4.3 — Requisition integrity

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| REQ-001 | H | `record_handoff_consumption` endpoint lets a Procurement Officer or HOPF mark any authorised handoff consumed | Handoff consumption becomes part of Tenders’ start command; verify the Tender exists and belongs to the handoff; not a free-form endpoint. | Verified | tenders/tests/test_handoff_consumption.py (4 refusal cases + start still consumes); requisitions test_requisitions_api_requests no longer consumes over HTTP and | b7d36e35 (Requisitions side: endpoint removed, service docstring), acdc6d7d (Tenders side, separate commit: `handoff_gateway.consume` verification) | 7 Oct 2026 | regression sweep authorization, state-machine + test site. Endpoint `api.record_handoff_consumption` deleted (no JS/Vue/seed caller; grep of whole repo). Consumption is now only the in-process call inside Tenders' Start tender and Start corrected version. `handoff_gateway.consume` first checks: the Tender exists and carries this handoff, the Tender Version belongs to that Tender and handoff, and no other Tender holds |
| REQ-002 | H | HoD maker-checker is enforced only on the Awaiting branch; a Draft can be certified by an Author who later bec | Apply the HoD self-certification refusal on the Draft-certify path; record who sent for approval. | Red | procurement_requisitions/tests/test_maker_checker.py::TestHeadOfDepartmentCannotCertifyWhatTheyPreparedOrSent | 11d3a7ac | reopened 7 Oct 2026 | Reopened 7 Oct: a different lead Head can certify an Author Draft directly and only the creator counts as preparer (REG-SOD-03: RG-14). One rule, `records.certifier_conflict`, used by the Draft path, the approval-task path and the offers (editor action, Home work list): an actor who prepared or sent the Version cannot certify it unless they prepared it directly as Head. Send for approval now records `sent_for_approva |
| REQ-003 | M | Preparer can also be the Procurement authoriser (no "self-authorisation" check beyond `submitted_by`) | See finding in `audit/FINDINGS.md`. | Verified | test_maker_checker.py::TestPreparerCannotAuthorise | 11d3a7ac | 7 Oct 2026 | regression sweep sod + test site; Preparer is the creator only (REG-SOD-03, RG-14). `records.authoriser_conflict`: the authoriser may be neither the submitting Head nor the preparer. Used by `authorise_requisition`, the Authorise offer on the task view and the Home work list. The sender is recorded but deliberately not yet part of the authoriser rule, see Follow-ups F2. |
| REQ-004 | M | HoD submission from "Awaiting Department Approval" skips the section 7.2 rechecks | See finding in `audit/FINDINGS.md`. | Verified | test_maker_checker.py::TestSubmissionRechecksOnTheApprovalPath (balance changed; product unsupported) | 11d3a7ac | 7 Oct 2026 | regression sweep sod, state-machine + test site. `lifecycle.recheck` (eligibility, compatibility, zero Blocking findings) is the one recheck used by `lock()` and by the approval-task branch, plus the canonical digest comparison on the locked Version. Parity with the Draft path, see Follow-ups F3 for the correction hold. |
| REQ-005 | M | Category applicability of technical characteristics is not enforced server-side | See finding in `audit/FINDINGS.md`. | Green | procurement_requisitions/tests/test_validation.py::TestCategoryApplicability (pure) + test_maker_checker.py::TestCategoryApplicabilityIsEnforcedByTheCommands | d6a2796b (tests for the commands sit in test_maker_checker.py, committed in 11d3a7ac) | test site | Two layers: commands refuse an inapplicable characteristic (`add`/`update` technical requirement, `apply selected package`, `save proposal draft`) with REQ_CONT |
| REQ-006 | M | Brand/restrictive-term Blocking finding is applied only to technical TEXT rows | See finding in `audit/FINDINGS.md`. | Green | procurement_requisitions/tests/test_validation.py::TestRestrictiveWordingEverywhereItReachesTheTender (pure, 9 tests) | d6a2796b | test site | Brand / restrictive wording is now a Blocking RESTRICTIVE_TERM finding in: requirement title, item name and intended use, support description, acceptance pass c |

### WP4.4 — Tender integrity

*TND-002 needs an owner decision (spec gap).*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| TND-001 | H | An addendum can become effective (deadline rewritten, definition activated) after the submission period has cl | Refuse addendum issue after submission close; revised deadlines go through the governed reopen route. | Verified | tenders/tests/test_open_period.py::TestAddendumEffects::test_an_addendum_cannot_become_effective_after_the_submission_period_closed (+ ::test_an_addendum_cannot | d966ee5a | 7 Oct 2026 | regression sweep state-machine + test site. Issue and the final channel confirmation now refuse (TND_STALE_VERSION, message states the period has ended) once the Tender is not Published - open or its deadline is reached. The confirm check is a `precondition` run under the Tender row lock inside `channel_confirmation.confirm_channel`. Read parity: the addendum screen no longer offers issue / confirm once the period is |
| TND-002 | H | A late final channel confirmation strands the Tender with no governed exit | Needs a governed exit — owner decision (spec gap): revise the deadline inside the same publication package, or withdraw/cancel. | Blocked |  |  |  | Document does not name a command or the digest consequence; see Follow-ups F-1. No code changed. |
| XC-023 | M | Tender list predicate (lead unit only) differs from the direct-access predicate (lead plus contributors) | See finding in `audit/FINDINGS.md`. | Verified | tenders/tests/test_tender_authorization.py::TestFrameworkHooks::test_a_contributing_unit_lists_the_tender_it_may_open | 92572108 | 7 Oct 2026 | regression sweep authorization + test site. One predicate: `tender_authorization.unit_scope_condition` = lead unit in reader's units OR any contributing unit (json_contains on `contributing_org_unit_ids`), the list form of what `has_permission` / `reader_mode` already test. Child doctypes inherit it through the Tender sub-select. |
| TND-003 | M | Accounting Officer can still authorise publication after returning the package; the return item is orphaned | See finding in `audit/FINDINGS.md`. | Verified | tenders/tests/test_publication.py::TestAuthorise::test_the_accounting_officer_cannot_authorise_while_their_return_is_open | e83c4033 | 7 Oct 2026 | regression sweep sod, state-machine + test site. `authorise_tender_publication` refuses with TND_STALE_VERSION while an open RETURNED_BY_AO hand-off exists (also when a stale task id is passed). Reopen already clears the hand-off. |
| TND-004 | M | Non-material addendum rows for clarification deadline and others have no effect on the Tender or definition | See finding in `audit/FINDINGS.md`. | Green | tenders/tests/test_open_period.py::TestAddendumEffects::{test_a_clarification_deadline_row_moves_the_tenders_clarification_deadline_and_the_definition, test_a_s | d966ee5a | test site, test_open_period + the modules above | Clarification-deadline row: revised value validated as a date before the submission deadline, kept as the label the notice shows ("29 May 2027, 17:00 EAT"), par |
| TND-005 | M | The conflicting-confirmation audit event is written and then rolled back with the refusal | See finding in `audit/FINDINGS.md`. | Green | tenders/tests/test_publication.py::TestConfirmChannels::test_a_conflicting_confirmation_audit_record_survives_the_refusal_the_request_rolls_back | d41f4f25 | test site, test_publication (20 tests) | `fail(..., audit_preserved=True)` marks the refusal; the three confirmation endpoints (`confirm_publication_channel`, `confirm_addendum_publication_channel`, `r |
| TND-008 | M | "Prepared by" for segregation is only the person who started the Tender | See finding in `audit/FINDINGS.md`. | Verified | tenders/tests/test_lifecycle.py::TestSubmitReturnApprove::test_an_officer_who_edited_the_draft_cannot_approve_it_as_head_of_procurement | 6857cfb4 | 7 Oct 2026 | regression sweep sod + test site; Opening processing-actors rule is XC-135 (open). "Prepared" = Version.prepared_by plus every actor of TenderDraftSaved / evidence add-update-remove events on any Version of the Tender (`draft_commands.draft_editors`, one query on the event log). Applied once in `lifecycle.require_segregation` so approve, authorise, return, the read offers, guidance and My Work all agree. |
| TND-013 | L | A true concurrent StartTender returns a conflict error, not the first Tender's identity | See finding in `audit/FINDINGS.md`. | Green | tenders/tests/test_lifecycle.py::TestStartTender::test_a_losing_concurrent_start_returns_the_first_tenders_identity | 6857cfb4 | test site, test_lifecycle | `start_tender` catches the loser's TND_HANDOFF_CONFLICT (or a duplicate-key error) after the savepoint rollback, re-reads the committed Tender with a locking re |

### WP4.5 — Strategy integrity

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| STR-001 | H | `save_strategy_structure_draft` deletes any record of any DocType (permissions bypassed) | Confine `deletes` to this version’s own Node/Indicator/Target rows; no ignore_permissions; refuse any other doctype. | Verified | ...::TestChangeSetConfinement::test_deletes_refuse_any_other_doctype | 2bbbfdc8 | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site. `deletes` accepts only Strategy Node / Performance Indicator / Performance Target rows that belong to this Draft version; anything else (ToDo, Audit Event) is refused with STRATEGY_INVALID_STATE and nothing is deleted. `ignore_permissions` now applies only to those rows, inside the command window. Whole change set validated before the first write. |
| STR-002 | H | Structure change set accepts record names from other versions: Active content can be deleted or moved | Every node/indicator/target name in a change set must belong to this Draft version. | Verified | ...::test_delete_of_a_row_in_an_active_version_is_refused, ::test_update_of_a_row_from_another_version_is_refused | 2bbbfdc8 | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site. Named node/indicator/target must belong to this version; parent / measured node / target indicator pointing at another version refused; `plan_version_id` never taken from the request; version must be Draft. |
| STR-003 | H | `save_strategy_plan_draft` edits any version and any plan identity regardless of status | save_strategy_plan_draft requires a Draft version that belongs to the plan. | Verified | ...::TestPlanDraftSave (4 tests) | 2bbbfdc8 | 7 Oct 2026 | regression sweep authorization, state-machine + test site. `save_strategy_plan_draft` requires a Draft version of the named plan (STRATEGY_INVALID_STATE otherwise). Title/role/parent/period cannot change once the plan has more than one version (matches the UI's `identity_editable`); a successor Draft can still change its own use-from/until. Unchanged identity values sent back by the UI are accepted. |
| STR-004 | H | Open-ended (null `effective_to`) version never resolves and escapes the overlap guard | Null effective_to treated as open-ended in the overlap guard and context resolution. | Verified | ...::TestOpenEndedApplicability (4 tests) | 2bbbfdc8 | 7 Oct 2026 | regression sweep state-machine + test site. Blank `effective_to` is open-ended in `_overlaps` (domain guard) and `_overlaps_range` / `_covers_date` (resolver), for both as_of_date and fiscal_year. Approving a successor with blank "Use until" keeps the context resolvable (predecessor is closed to the day before, as before). |
| STR-006 | M | "Author cannot approve" is implemented as "submitter cannot approve" | See finding in `audit/FINDINGS.md`. | Blocked | none | none |  | Policy decision, see Follow-ups 1. Code unchanged (submitter cannot approve/return, as before). |
| STR-008 | M | Generated Strategy identifiers can be supplied by the caller and are not unique | See finding in `audit/FINDINGS.md`. | Verified | ...::TestGeneratedReferences (2 tests) | 2bbbfdc8 | 7 Oct 2026 | regression sweep state-machine + test site; INT-A: canonical seed regression fixed in a1747084. A caller cannot set any generated reference (the change set accepts content fields only); the record itself refuses a duplicate reference (`validate_reference_field`). Supplied references on in-process inserts (canonical seed remaps) are still honoured, now unique-checked. |
| STR-011 | M | Approval does not refuse expired applicability | See finding in `audit/FINDINGS.md`. | Verified | ...::TestExpiredApplicability | 2bbbfdc8 | 7 Oct 2026 | regression sweep state-machine + test site. New approval blocker `EFFECTIVE_DATE_EXPIRED` when `effective_to` is before the site date; approval refused with STRATEGY_NOT_READY, version stays Submitted for approval. Red evidence: the first run, before any implementation, had 15 failures and 19 errors across the 22 tests (errors were mostly cleanup of rows left by failed assertions); I did not re-prove each red individ |

### WP4.6 — Planning and Needs approval rules

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| NDS-007 | M | Acceptance does not recheck the unit or the content hash | See finding in `audit/FINDINGS.md`. | Verified | departmental_needs/tests/test_departmental_needs_lifecycle.py::TestAcceptanceRechecks (unit disabled: red observed, `DepartmentalNeedError not raised`; the whol | cf8813d1 | 7 Oct 2026 | regression sweep sod, state-machine + test site; Needs lifecycle module has one unrelated environmental error on the gate (INT-B E-4). `_recheck_for_acceptance` runs on `accept` only, before the task is consumed: unit still enabled (`NDS_UNIT_INELIGIBLE`), quantity still valid for the unit (`NDS_QUANTITY_PRECISION_INVALID`), stored `content_hash` equals the recomputed digest (`NDS_STATE_CONFLICT`). Return and decline |
| PLN-010 | M | Segregation chain omits SavePlanVersionDetails and the funding-reuse request | See finding in `audit/FINDINGS.md`. | Verified | procurement_planning/tests/test_plan_finance.py::TestPlannerChainCoverage (both tests; red observed for each: `is_segregated` was False for an actor who only sa | 9e7c2073 | 7 Oct 2026 | regression sweep sod, state-machine + test site. `SavePlanVersionDetails` added to `PLANNER_CHAIN_COMMANDS`; the chain now also reads the journal against `Plan Finance Basis Reuse` records of the chain's versions. |
| XC-134 | L | Planner segregation chain omits `SavePlanVersionDetails` and other Planner commands | See finding in `audit/FINDINGS.md`. | Verified | same tests | 9e7c2073 | 7 Oct 2026 | regression sweep sod + test site. Fixed once with PLN-010. `CancelPlanUpdate` deliberately not added: PLN §6.4 names authoring content, forming/dissolving, requesting Finance and signing; cancelling a successor is not an authoring act and leaves no content to decide on. Every other Planner command the finding implies was already in the list (nine commands) or is not a content/Finance/signature act (Follow-ups 2). |
| PLN-021 | L | Statutory withdrawal for correction skips the segregation check (spec gap) | See finding in `audit/FINDINGS.md`. | Blocked |  |  |  | [Blocked (document ambiguous; owner decision)] See Follow-ups 1. Code unchanged. |

## Wave 4R — regression findings from the Waves 1-4 sweeps

**Source:** the four read-only regression sweeps of 7 October 2026 (`audit/regress-authorization.md`, `audit/regress-sod.md`, `audit/regress-state-machine.md`, `audit/regress-money-concurrency.md`), 49 REG-* defects de-duplicated by root cause into the rows below (RG-01 to RG-42). Each row names its REG ids and source file in Notes. Severity is the highest any sweep gave; every row starts at Todo. Rows reopen Wave 1-4 findings (set Red in the waves above); a reopened row returns to Green only when its RG rows are Green. Work packages are ordered by severity and each is one worker's lane; the Low items are one batch.

**Progress files:** a worker records status in `audit/progress/WP4R.<n>.md` using `| AUD-RG-nn | Green | ... |` rows (merged after `REGRESS.md`).

**Exit gate:** every row Verified (or Won't fix with a reason), then re-run the four regression sweeps read-only.

### WP4R.1 — Planning: publication and approval evidence

*Annual Plan cannot be published by any role; the approval evidence the segregation chain reads is tamperable; DPP amounts are not exact. Owner: kentender_procurement/procurement_planning. Do RG-01 together with Wave 5 AUD-XC-106.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| RG-01 | H | Annual Plan publication is neither a post-commit worker nor a human role-gated command (owner decision D4 unmet): after ApproveAnnualPlan the version waits at "Approved - publication pending" and only a System Manager calling the REST endpoint by hand can publish it; `publish_annual_plan` and the pipeline acknowledge/retry are technical-only. | Add a role-gated Publish command (default HOPF, open question Q4) offered in the Planning allowed actions, authorised by registered responsibility and not by a technical role; keep acknowledgement/retry internal. Tests: HOPF sees and runs Publish and the version leaves "publication pending"; Planner, AO and System Manager are refused. Amend PLN through document item D-2. | Todo | | | | CODE DEFECT + SPEC DEFECT. Same root as Wave 5 AUD-XC-106 (Todo): fix together. Source: regress-state-machine.md REG-STATE-01. |
| RG-02 | M | Planning approval-evidence doctypes are still writable and deletable by System Manager and Administrator with empty controllers (about 35): Plan Governance Decision/Task, Approved Plan Snapshot, Plan Finance Decision/Task/Basis Reuse, Plan Preparation Signature, Treasury Submission Evidence, Plan Drawdown Reference (`drawdown_state`), Plan Publication family, Departmental Plan Submission/Validation, Plan Item Correction Request/Disposition, Late Activation Explanation, Planning Command Journal. The Planner segregation chain is computed from these rows. | Put each in the Planning write family (`CommandWriteGuardMixin`), remove write/create/delete DocPerm, open the window only in the owning Planning commands. Tests: System Manager and Administrator `set_value`/save/delete refused on every listed doctype, commands still write, DocPerm walk covers all Planning doctypes (see RG-36). Needs `bench migrate` (dev action). | Todo | | | | CODE DEFECT. De-duplicated from three sweeps. Reopens AUD-XC-013. Source: regress-authorization.md REG-AUTHORIZATION-01; regress-sod.md REG-SOD-02; regress-state-machine.md REG-STATE-02 (Planning part). |
| RG-03 | M | Planning DPP funding amount and direct-requirement quantity are not exact-validated: `dpp_lifecycle.py:377,461,536` use `flt()`, so NaN/Infinity pass the positivity check, `1000000.005` is stored and later silently rounded by `sum_money`. | Parse with `money.parse_money` and the exact quantity rule in `save_need_funding` and `save_direct_requirement`; typed `PLN_MONEY_PRECISION_INVALID` before any effect. Tests: NaN, excess scale, overflow, exact amount accepted. | Todo | | | | CODE DEFECT. Reopens AUD-XC-117 (Planning half). Source: regress-money-concurrency.md REG-MONEY-05. |

### WP4R.2 — Legacy Tender Configurations module

*A parallel publication path with no Accounting Officer gate. Owner decision first: retire (recommended) or gate. Owner: kentender_procurement/tender_configurations.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| RG-04 | H | Legacy Tender Configurations still approves and PUBLISHES a tender with no maker-checker and no Accounting Officer: `approve_for_preview`, `publish_tender` and `return_publication_for_correction` authorise on write permission only (Frappe roles Tender Manager / Planning Authority); the submitter is recorded and never compared; the dashboard page and the whitelisted endpoints are still live. | Owner decision: retire the module as with Tender Management v2 (inventory, delete, guarded drop patch) or put the Accounting Officer and segregation gate on every publish path. Test either way: one user holding only Tender Manager cannot submit, approve, confirm and publish alone. | Todo | | | | CODE DEFECT (legacy surface). OWNER DECISION needed. Related: AUD-XC-143 (open). Source: regress-sod.md REG-SOD-01. |
| RG-05 | M | Legacy Tender Configurations: an IT Tender Publication Record can be created already Published (`is_new()` returns before the status guard) and the configuration publication lock lifts with one save (`confirmed_document_package` and `status` are not locked fields). | Apply the status and locked-field guards on insert; add `confirmed_document_package` and `status` to the locked set. Tests: POST as Published refused; PUT clearing the package refused. Moot if RG-04 retires the module. | Todo | | | | CODE DEFECT. Reopens AUD-XC-011. Source: regress-state-machine.md REG-STATE-05. Note: 16 tender_configurations test modules do not load on the test site (gate follow-up INT-B 4), so these guards are not exercised by the suite today. |

### WP4R.3 — Core and cross-app guards

*Guard coverage the family tests missed. Owner: kentender_core (guard) with the Requisitions/Tenders child doctypes and Procuring Entity.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| RG-06 | M | The command-write guard does not cover child-table rows of guarded parents: Administrator can insert or delete Requisition Item / Technical Requirement / Related Service / Acceptance Requirement / Supporting Material / Contributing Unit / Drawdown Line, Tender Evidence Requirement / Review Finding, Tender Cancellation Obligation and Tender Candidate Notice Attempt directly (the REST create inserts a child row alone). | Give the child controllers a guard that refuses insert/update/delete unless the parent family window is open. Tests: POST and DELETE of each listed child row as Administrator refused; the commands still write. | Todo | | | | CODE DEFECT. Reopens AUD-XC-013. Source: regress-state-machine.md REG-STATE-04. |
| RG-07 | M | A second Procuring Entity can still be created by a Reference Data Manager through `/api/resource`: the single-entity rule lives only in `reference_data_api` and the DocPerm grants create. | Move `require_single_entity` into the Procuring Entity controller and/or drop create from the DocPerm. Test: POST `/api/resource/Procuring Entity` as the role holder refused (the existing test only drives the API and skips on an empty site). | Todo | | | | CODE DEFECT. Reopens AUD-XC-017. Source: regress-authorization.md REG-AUTHORIZATION-02. |

### WP4R.4 — Needs: outbox and decision rows

*Doctypes outside the Needs write family and read-scope hook. Owner: kentender_procurement/departmental_needs.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| RG-08 | M | Departmental Need Event (the Needs outbox) is writable by System Manager and its insert starts a departmental plan (`dpp_autostart.on_need_event` on `after_insert`); the controller guards payload fields on update only. | Add Departmental Need Event (and Decision) to the Needs write family, drop DocPerm write/create, refuse insert outside the command window. Test: POST an accepted-Need event as System Manager is refused and no plan starts. | Todo | | | | CODE DEFECT. Severity Low in REG-AUTHORIZATION-08, Medium in REG-STATE-02: stricter taken. Source: regress-authorization.md REG-AUTHORIZATION-08; regress-sod.md REG-SOD-02 (Needs part); regress-state-machine.md REG-STATE-02. |
| RG-09 | M | Departmental Need Decision has business-role read DocPerm (Author, Head of User Department, Planner, Auditor) and no scope hook: decision rows (reason, actor, assignment, source IP, session id) are readable across departments. | Register `permission_query_conditions` and `has_permission` for Departmental Need Decision through `need_authorization` (same predicate as the list and the direct route). Test: an Author of department A cannot list or open department B decisions. | Todo | | | | CODE DEFECT. Reopens AUD-XC-015. Source: regress-authorization.md REG-AUTHORIZATION-05. |

### WP4R.5 — Suppliers: registry authority and registration

*Owner: kentender_suppliers.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| RG-10 | M | The literal Administrator user passes every supplier-registry mutation capability (Frappe returns every Role for Administrator), so Administrator can approve, blacklist, suspend and reinstate. | Make `has_capability` refuse Administrator and technical principals explicitly for mutation capabilities; review other bare-role gates that exclude System Manager but not Administrator. Test with the user Administrator, not only a System Manager test user. | Todo | | | | CODE DEFECT. Reopens AUD-XC-019. Source: regress-authorization.md REG-AUTHORIZATION-03. |
| RG-11 | M | Supplier-builder write endpoints (`create_supplier_builder_profile`, `update_builder_identity`) are gated by the read capability and write with `ignore_permissions=True`: a Procurement Planner can rename a registered supplier. | Gate on a write capability, refuse rename once past Draft, drop `ignore_permissions` or wrap in a governed service. Tests: planner, auditor and System Manager refused. | Todo | | | | CODE DEFECT. Reopens AUD-XC-004/-019. Source: regress-authorization.md REG-AUTHORIZATION-04. |
| RG-12 | M | `ktsm_register` still performs unauthenticated writes with `ignore_permissions`; its "disabled until verified" login can never be enabled, so a caller can squat any e-mail address; each call also creates a Supplier, a profile and an API-access row; the rate-limit test only checks the decorator. | Per owner default Q5: create the User only after e-mail verification, remove `ignore_permissions` from the User path, assert rate limit and POST-only in a test. Whether to keep guest registration at all stays an owner question. | Todo | | | | CODE DEFECT against the Q5 default + SPEC GAP. Reopens AUD-XC-020. Source: regress-authorization.md REG-AUTHORIZATION-06. |
| RG-13 | M | Supplier-registry status is writable by System Manager over REST: the KTSM Supplier Profile controller tests the NEW status (Approved to Draft passes, insert is unchecked); KTSM Category Assignment `qualification_status`, API Access and Document are System Manager rwcd. | Command-only guard on the four doctypes with the window opened in `services/governance.py`; compare the OLD status; remove DocPerm write. Tests: POST an Approved profile and PUT Approved to Draft as System Manager refused. | Todo | | | | CODE DEFECT (same shape as original sweep F2). Commands were fixed, the doctypes were not. Source: regress-state-machine.md REG-STATE-03. |

### WP4R.6 — Segregation of duties: Requisitions, Evaluation, Award

*Owner: kentender_procurement (procurement_requisitions; bid_evaluation + award). RG-15 needs an owner decision first.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| RG-14 | M | Requisition HoD certification: a different lead Head of User Department can certify an Author Draft directly (skipping the approval task) and only the creator counts as "prepared" - an editor in any contributing unit, or a HOPF who edited as Author, is not blocked. `test_a_different_head_still_certifies_an_authors_draft` asserts the wrong behaviour. | Follow the Tender precedent (AUD-TND-008): derive the prepared/edited set from the immutable Version audit, block every editor in `certifier_conflict` and `authoriser_conflict`, limit direct certification to the preparing Head per REQ table row 551; replace the contradicting test. | Todo | | | | CODE DEFECT (direct-certify row) + SPEC GAP (prepared = every editor). Reopens AUD-REQ-002 / REQ-003. Source: regress-sod.md REG-SOD-03. |
| RG-15 | M | Evaluation members, report signers and the deciding AO/HOP are not segregated: an AO or HOP can be appointed to the committee, chair it, sign the verification report and record the Award; registry `sod_tags` are unconsumed. | OWNER DECISION first (D2 is silent on evaluation membership): exclude AO/HOP from committee roles or add evaluator-to-decider checks in appointment and in the award decision; then a red test per the decision. | Todo | | | | SPEC GAP. Reopens AUD-AWD-001 (second half; tracker follow-up WP4.1 item 7). Source: regress-sod.md REG-SOD-04. |

### WP4R.7 — Budget: idempotency journal

*Owner: kentender_budget.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| RG-16 | M | Budget idempotency journal is optional, read-then-effect-then-insert with the insert failure swallowed (a concurrent same-key release applies twice), user-blind and answers before authorisation (governance replay returns user A result to user B); the digest excludes command and actor. | Port the `services/command_journal.py` pattern to `run_idempotent`: authorise, claim by unique insert in a savepoint, bind key to actor + command + payload; do not write the journal row with `safe_record_event`. Tests: two-connection same-key release applies once; replay refused to another actor. | Todo | | | | CODE DEFECT. Reopens AUD-XC-002 (idempotent by key) and AUD-XC-131. Source: regress-money-concurrency.md REG-MONEY-01; regress-state-machine.md REG-STATE-07 (Low, merged, stricter taken). Latent for releases until Contract Management exists; governance replay is reachable now. |

### WP4R.8 — Bid Submission: reference numbers

*Owner: kentender_procurement/bid_submission.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| RG-17 | M | Bid Submission reference numbers (`correlation_id`, support and receipt references) are `count()+1` read from the snapshot after a Tender lock, so concurrent bidders at the deadline collide (a receipt collision happens after the deposit); a same-key retry is not replayed; the journal is key-first and not actor-bound. | Use the atomic `kentender_core` series for the references, locking reads for the attempt lookup, and the authorise-claim-replay envelope. Test: two bidders on one Tender through two connections get distinct ids. | Todo | | | | CODE DEFECT. Reopens AUD-XC-130 / AUD-XC-131. Source: regress-money-concurrency.md REG-MONEY-03. |

### WP4R.9 — Low batch

*All Low items, one lane (or split by app at the lead discretion). Each is small; none blocks a wave on its own except where the Notes name a reopened row.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| RG-18 | L | Bid Opening and Proceedings still use the pre-audit lock helper (`select ... for update` then a plain `get_doc`) and read the journal before claiming it: a stale revision surfaces as a raw timestamp error and a racing duplicate as a raw duplicate-key error. | Copy `award/services/records.py` (locking `get_doc`, authorise-claim-replay); test per `award/tests/test_awd_command_envelope.py` stale-revision pattern. | Todo | | | | CODE DEFECT. Reopens AUD-XC-130/-131. Source: regress-money-concurrency.md REG-MONEY-02; regress-state-machine.md REG-STATE-06. |
| RG-19 | L | Per-case child sequence numbers are `count()+1` / `max()+1` from a snapshot after the case lock (about 55 sites in Award, Evaluation, Opening, Proceedings). | One shared helper that reads under `for_update` after the lock (or uses the atomic series); sweep test. | Todo | | | | CODE DEFECT. Reopens AUD-XC-130. Source: regress-money-concurrency.md REG-MONEY-04. |
| RG-20 | L | The database-level concurrency guards (unique active Budget Version, unique (contract, reservation) commitment key) exist only as patches; a fresh install marks patches complete and creates neither index. | Move both constraints into the DocType JSON or an `after_install`/`after_migrate` ensure step; test against a fresh schema. Dev/test: migrate. | Todo | | | | CODE DEFECT (install path). Behind AUD-BUD-004. Source: regress-money-concurrency.md REG-MONEY-07. |
| RG-21 | L | Reference candidates are probed with `SELECT ... FOR UPDATE` on absent keys (`kentender_core/utils/series.py:50`): gap locks may deadlock creators with different prefixes. Medium confidence, not confirmed by execution. | Confirm with a two-connection two-prefix run; if it deadlocks, probe with a plain read inside the prefix lock. | Todo | | | | CODE DEFECT (unconfirmed). Source: regress-money-concurrency.md REG-MONEY-08. |
| RG-22 | L | `validate_plan_affordability_for_decision` is a whitelisted endpoint that takes whole-Budget row locks behind a read-scope gate: any Budget reader can stall reserve, approve and close. | Remove `@frappe.whitelist` (Planning calls it in-process) or require the Finance-decision capability. Test: not in `frappe.whitelisted`. | Todo | | | | CODE DEFECT (availability). Source: regress-money-concurrency.md REG-MONEY-09. |
| RG-23 | L | Requisition drawdown still reads `funding_state` and the drawn totals from the snapshot after the Plan Item lock. | Locking reads of both; two-connection tests in the style of `test_drawdown_races`. | Todo | | | | CODE DEFECT. Reopens AUD-XC-107. Source: regress-money-concurrency.md REG-MONEY-10. |
| RG-24 | L | Float arithmetic and epsilons remain outside the decisions: `plan_read.py:948` (1e-9 on float sums), `tenders/services/review.py:164-165` (1e-6, a blocking SCHEDULE_MISMATCH), `tenders/services/snapshot.py:108-113`. | Decimal sums and exact comparison; tests with 1e-8 noise at ministry scale. | Todo | | | | CODE DEFECT. Source: regress-money-concurrency.md REG-MONEY-11. |
| RG-25 | L | Requisitions release scope is decided from a pre-lock snapshot (`_require_release_scope` before the `_release` lock): a conversion committed between the two is not seen; `revalidate_reservations` reads unlocked. | Repeat the converted/own-requisition test after the lock in `_release`; lock in revalidate; two-connection test. | Todo | | | | CODE DEFECT (latent: no Contract Management yet). Reopens AUD-XC-002. Source: regress-money-concurrency.md REG-MONEY-12; regress-state-machine.md REG-STATE-08. |
| RG-26 | L | A Budget service principal can be minted by any module (`service_caller` is public; the guard test is a regex over literal names and exempts seeds), and the Contract principal converts any reservation for a contract it names (no lineage test). | Restrict minting to the owning gateways and replace the regex with an import/AST check; state the lineage rule in BUD before a real Contract Management caller exists. | Todo | | | | CODE DEFECT (weak control) + SPEC GAP (lineage). Source: regress-authorization.md REG-AUTHORIZATION-12, -16; regress-money-concurrency.md REG-MONEY-13. |
| RG-27 | L | Reserve replay does not enforce "same key, changed payload" once the 300 s check token has expired. | Persist the payload digest with the idempotency row and compare on replay. Test after token expiry. | Todo | | | | CODE DEFECT. Source: regress-money-concurrency.md REG-MONEY-14. |
| RG-28 | L | Money boundary residuals with no defect id of their own: Budget accepts a JSON float of at most 15 digits although BUD18-AC-051 says float JSON fails (deliberate, undocumented deviation); the 12-integral-digit limit versus 18 required (AUD-XC-129, storage-type decision open); fixed scale 2 in check/reserve, a `CURRENCY = "KES"` constant in Requisitions and constants in the Tenders snapshot (AUD-XC-133). | Owner decisions: record the float deviation in BUD; choose the storage type for 18 digits. Then take scale and currency from Budget `scale_for(currency)` in check/reserve, Requisitions precision and the Tenders snapshot. | Todo | | | | SPEC GAP + CODE DEFECT. Reopens AUD-XC-129 and AUD-XC-133. Source: regress-money-concurrency.md REG-MONEY-15 and the PARTIAL rows XC-129, XC-133. |
| RG-29 | L | An integer amount of about 27 or more digits raises an uncaught `decimal.InvalidOperation` (`budget_money.py:111` sits outside the try) instead of `BUDGET_MONEY_PRECISION_INVALID`. | Move the quantize inside the try. Test with `"9" * 30` (the existing test stops at 13 digits). | Todo | | | | CODE DEFECT. Reopens AUD-XC-117. Source: regress-money-concurrency.md REG-MONEY-06. |
| RG-30 | L | System Manager and Administrator can act for any supplier through the external API gate (`_assert_may_access_supplier`): update profile, upload a document, submit for review. | Remove technical roles from the gate; require the supplier own account or a registry write capability. | Todo | | | | CODE DEFECT. Reopens AUD-XC-019. Source: regress-authorization.md REG-AUTHORIZATION-07. |
| RG-31 | L | Plan Item Correction Request is readable over REST by any Head of User Department with no scope hook. | Register the two permission hooks delegating to the plan item department scope (can ride with RG-02). Test as RG-09. | Todo | | | | CODE DEFECT (pre-existing). Source: regress-authorization.md REG-AUTHORIZATION-09. |
| RG-32 | L | User Scope Assignment and Strategy Scope Assignment remain writable by System Manager/Administrator, and User Scope Assignment still feeds the working-context entity offer. | Guard or retire them (AUTH section 19) and remove `user_scope_rows` from `permitted_procuring_entities`. Tests accordingly. | Todo | | | | CODE DEFECT. Reopens AUD-XC-021 / XC-026 residue. Source: regress-authorization.md REG-AUTHORIZATION-10. |
| RG-33 | L | The legacy Procurement Journey list (`journey_api.list_journeys`) reads `tabUser Permission` and applies no responsibility scope; it shows every journey when the user has none. | Replace with responsibility scope or retire the surface (deferred legacy, OD-F). | Todo | | | | CODE DEFECT. Reopens AUD-XC-021. Source: regress-authorization.md REG-AUTHORIZATION-11. |
| RG-34 | L | `create_strategy_snapshot` writes an audit event and an idempotency row for any enabled internal user (a read gate authorises a write). | Require a snapshot/write capability, or make the snapshot read-only. Test with a plain internal user. | Todo | | | | CODE DEFECT. Residue of AUD-STR-005. Source: regress-authorization.md REG-AUTHORIZATION-13. |
| RG-35 | L | Owner decision D1 "no reference to Tender Management v2" holds for code, but `docs/` (65 files) and `archive/` (237 files) still name it; the live sidebar label "Tender Management" is the Tenders module name. | Owner to say whether history in docs/archive and the sidebar label count; if yes, edit the documents through the document-change protocol. | Todo | | | | SPEC GAP. Source: regress-authorization.md REG-AUTHORIZATION-14. |
| RG-36 | L | No repository-wide test ties write-capable doctypes to the command-write guard; each family test hard-codes its own list, which is how RG-02, RG-08 and RG-09 slipped through. | A core test walking every non-child doctype of the five core apps: any write/create/delete DocPerm without a command-write family must be on a named allow-list. Do first or with RG-02. | Todo | | | | CODE DEFECT (missing coverage). Source: regress-authorization.md REG-AUTHORIZATION-15. |
| RG-37 | L | A Technical Operator can deliver award notices and the Contracting package (`retry_operation`), against a literal reading of D2 "only the HOPF handles supplier correspondence". | Owner to confirm whether redelivery counts as correspondence; adjust the matrix test if not. | Todo | | | | SPEC GAP. Source: regress-sod.md REG-SOD-05. |
| RG-38 | L | Addendum issue has no maker-checker: a Procurement Officer or HOPF submits and the HOPF issues, so one person can draft, submit and issue. | Owner to confirm the rule in TPR; then compare drafted/submitted by with the issuer. | Todo | | | | SPEC GAP. Source: regress-sod.md REG-SOD-06. |
| RG-39 | L | Assignment-grant residuals: a person granted a business role who later receives System Manager keeps it; `authorise_record` denies a technical principal only for the READ purpose (Award alone adds its own exclusion); registry `sod_tags` still have no consumer. | Owner decision (tracker follow-up 5); deny technical principals on commands in `authorise_record`; consume `sod_tags`. STR-006 and PLN-021 are already tracked Blocked rows. | Todo | | | | CODE DEFECT + owner decision. Reopens AUD-XC-136. Source: regress-sod.md REG-SOD-07 (third bullet). |
| RG-40 | L | Strategy Command Journal is System Manager rwcd and unguarded: a technical user can delete a key row, weakening the replay protection. | Add it to the Strategy write family; drop DocPerm write/delete. | Todo | | | | CODE DEFECT. Part of the XC-013 residue. Source: regress-sod.md REG-SOD-08; regress-authorization.md REG-AUTHORIZATION-01 (tail); regress-state-machine.md REG-STATE-02. |
| RG-41 | L | The principal-parameter AST test (`test_whitelisted_principal_param.py`) does not scan `**kwargs` whitelisted functions and its name list is narrower than the scanned patterns. | Extend the scan to `**kwargs` and names such as `made_by`/`requested_by` with a reviewed allow-list. | Todo | | | | CODE DEFECT (test gap). Source: regress-sod.md REG-SOD-09. |
| RG-42 | L | Eight retired authorisation doctypes keep `allow_rename: 1`; a rename bypasses the guard (Administrator only; the engine is retired). | Set `allow_rename` to 0 or drop the doctypes with the retired engine. | Todo | | | | CODE DEFECT (retired engine, impact nil unless rows exist). Source: regress-state-machine.md REG-STATE-09. |


## Wave 5 — Flows that dead-end or lose data

**Goal:** Manual Annual Plan publication, Need ↔ Planning loop for successor revisions, hold/withdraw, classification correction, hand-off contract mismatches.

**Exit gate:** Re-run sweep-handoffs; end-to-end test per flow (producer → consumer, not hand-written payloads); canonical seed validates.

### WP5.1 — Annual Plan publication — manual (owner decision)

*Add a human, role-gated Publish command and screen with unknown-outcome handling (role: question Q4). Amend the spec wording that requires a post-commit worker.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-106 | H | An approved Annual Plan is never dispatched for publication: nothing transmits it, so it never becomes Active | See WP5.1: human Publish command + UI; unknown-outcome handling; spec wording amended. | Todo | | | | |
| XC-121 | M | `PublishAnnualPlan` re-sends after an Indeterminate result; `PLN_PUBLICATION_FAILED`/`UNKNOWN` are never produ | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| PLN-020 | L | Technical-operator "Your turn" contradicts PLN27-AC-009 (spec defect) | See finding in `audit/FINDINGS.md`. | Todo | | | | |

### WP5.2 — Needs ↔ Planning loop

*Calibration regression: the late-accepted-Need dead end for successor revisions.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| HND-002 | H | Need withdrawal checks only the named revision's local usage card; Active Plan dependency of an older revision | Withdrawal checks every accepted revision and the Active-plan dependency via a Planning validator; Planning activation revalidates the Need. | Todo | | | | |
| NDS-001 | H | A Need whose accepted revision is a successor drops out of Planning's source list; Planning then deletes its D | current_accepted_events includes successor-accepted Needs; publish "Update required" on successor acceptance; refresh_draft_entries keeps their Draft entry; end-to-end test. | Todo | | | | |
| HND-003 | M | `NeedPlanningDispositionChanged` deviates from the approved wire contract (enum, schema_version, producer_sequ | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| NDS-005 | M | "Awaiting planning clearance" is unreachable from the UI; approve-while-included raises instead of recording t | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| NDS-009 | M | Disposition event uses a different enum and sequence than the approved wire contract | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| NDS-010 | M | The Planning-event consumer lacks the versioning, conflict, ownership and ordering rules of §7.4–7.5 | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| XC-141 | L | Departmental-plan autostart failure is swallowed and never retried | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| PLN-013 | L | Late-activation read labels ordinary successors as late and offers an action that then fails | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| PLN-015 | L | A withdrawn initial departmental plan leaves a stale Need position at NDS | See finding in `audit/FINDINGS.md`. | Todo | | | | |

### WP5.3 — Planning flows

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| PLN-002 | H | Hold-then-withdraw-for-correction sequence dead-ends | request_plan_withdrawal and withdraw-for-correction agree on hold kind so hold-then-withdraw works; test the whole sequence. | Todo | | | | |
| PLN-003 | H | A classification correction does not mark or block an affected Draft Plan Item | Classification correction marks affected Draft items "Source correction required" and blocks Finance/signature/approval until cleared. | Todo | | | | |
| PLN-004 | H | An absent reservation rule is reported as "Required allocation met" and does not block submission | An absent reservation rule is "cannot determine" and blocks submission, not success. | Todo | | | | |
| PLN-001 | M | Active-plan funding is never marked stale when the Budget changes; Requisition authorisation keeps passing | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| PLN-006 | M | Successor submission and activation recheck neither scope lock nor consumed value; removal takes no reason | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| PLN-007 | M | Approved removals re-queue the source; removed items stay in the reviewed totals but not in the published plan | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| PLN-008 | M | A correction request can be "Resolved" against the unchanged Active Version | See finding in `audit/FINDINGS.md`. | Todo | | | | |

### WP5.4 — Requisition → Tender hand-off

*HND-001 and HND-009 also need document corrections (Wave 7).*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| HND-001 | H | Tender "requisition correction" route has no producer; a consumed handoff can never be re-authorised and the t | Implement the Tender requisition-correction producer (release/successor handoff route in REQ); remove the test shortcut that clears consumed_at. | Todo | | | | |
| HND-004 | M | Tenders' proceeding-coverage rows never reach Planning (allocation id tested as a document name, silent skip) | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| HND-006 | M | Tenders maps the wrong REQ error code, so a concurrent second Tender start gets `TND_HANDOFF_INVALID` instead  | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| HND-007 | M | Tender stores the Annual Plan Version id in `plan_item_version_id`; exact item-content identity is lost | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| HND-009 | M | Handoff and outbox event are v1.4 in code; approved REQ v1.14 and TPR v0.17 still specify v1.3, and unconsumed | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| REQ-008 | M | "Purchase ready for requisition" does not clear for an occupied item and the start surfaces carry no hold word | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| REQ-009 | M | `funding_source` is not sent to Budget and is not in the handoff | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| TND-006 | M | A Planning refusal of the invitation actual is recorded and never retried | See finding in `audit/FINDINGS.md`. | Todo | | | | |

### WP5.5 — Planning → Budget hand-off

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| HND-005 | M | Planning's budget-revision request omits `expected_line_revision`, so Budget's stale-line check is dead and Bu | See finding in `audit/FINDINGS.md`. | Todo | | | | |

### WP5.6 — Evaluation → Award → Contracting hand-offs

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| HND-008 | M | `TenderPublishedForEvaluation v1` and `ReadEvaluationPreparationSource` do not exist; Evaluation polls on a on | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| EVL-008 | M | Opening exceptions, including "Comment for Evaluation", are handed over but never read by Evaluation | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| EVL-015 | M | Tenders publishes only cancellation: suspension, resumption, validity-extension, award-decision and dated-rule | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| AWD-004 | M | Later restrictions and cancellation-after-notice do not reliably reach an already-delivered Contracting case | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| AWD-005 | M | Case `outcome` is never set to "Award", so the HoD decision summary shows no outcome | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| AWD-006 | M | The real Evaluation producer hard-codes every annex as available | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| AWD-009 | M | The "No award" follow-up task can never be completed | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| AWD-010 | M | An open debrief request or missing debrief rule never blocks Contracting delivery | See finding in `audit/FINDINGS.md`. | Todo | | | | |

### WP5.7 — Tender package digest drift

*Calibration: a new catalogue control must not invalidate approved-but-unauthorised Versions.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| TND-007 | M | Package-digest recomputation makes every unauthorised Tender Version fragile to any new CATALOGUE control | See finding in `audit/FINDINGS.md`. | Todo | | | | |

## Wave 6 — Audit trail and Frappe hazards

**Goal:** Durable, complete, append-only audit; denial events; sensitive reads logged; safe patches and scheduler jobs.

**Exit gate:** Re-run sweep-audit-trail and sweep-frappe-hazards; patch double-run test on the test site.

### WP6.1 — Durable and complete audit records

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-110 | M | Budget funding-ledger events (20 sites) and Award audit are best-effort: a failed audit write is swallowed aft | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| XC-111 | M | Funding-ledger events omit before/after positions, business role, assignment ID and fiscal year | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| XC-112 | M | Denial events required by STR §13 / BUD §14 are never written, or are written and rolled back | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| XC-122 | M | Strategy §13 audit list is incomplete (consumer reads, context resolution) and two events omit attribution | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| XC-123 | M | Planning and Requisition command journals do not record the exercised authority, role or request id | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| XC-124 | M | Departmental Need Decision stores a bare assignment ID, not the snapshot NDS §4.5 requires | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| STR-007 | M | §13 audit obligations for downstream contract calls and snapshots are not met | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| XC-128 | L | Organisation Unit commands and Award Settings changes write no audit event | See finding in `audit/FINDINGS.md`. | Todo | | | | |

### WP6.2 — Sensitive reads and exports are logged

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-113 | M | Reads of sealed/confidential bid pages and opening exports create no audit event | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| XC-114 | M | Opening-register download delivery record and audit event are written inside a GET and rolled back | See finding in `audit/FINDINGS.md`. | Todo | | | | |

### WP6.3 — Patch and scheduler hazards

*XC-143 may be removed by the TM2 retirement if the inventory shows it belongs there.*

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-138 | L | A patch records success although its unique indexes may not exist | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| XC-139 | L | Patches that rewrite data by heuristic | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| XC-142 | L | Scheduler sweeps without per-item isolation | See finding in `audit/FINDINGS.md`. | Todo | | | | |
| XC-143 | L | Legacy Tender Configuration services commit mid-request and a "get" writes and commits | See finding in `audit/FINDINGS.md`. | Verified |  |  |  | [No change needed here (stays open)] Tender Configurations / Tenders, not TM2; does not close with the retirement. See Follow-ups. |

## Wave 7 — Remaining Medium/Low and document corrections

**Goal:** Module batches for everything not covered above, plus the controlled document updates (owner decisions and spec defects).

**Exit gate:** Re-run the eight module traces for the rows touched; documents approved through the document-change protocol.

### WP7.XC — Cross-cutting — remaining Medium/Low

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| XC-024 | M | Evaluation and Proceedings register nothing with the technical-read hooks | See finding. | Todo | | | | |
| XC-027 | L | Bid working-copy doctypes are denied by hook, but Administrator reads them by name; Bid Receipt technical rout | See finding. | Todo | | | | |
| XC-028 | L | BOP v0_11 and OVS v0_6 section 4.2 disagree on what Administrator/System Manager read in Bid Opening | See finding. | Todo | | | | |
| XC-135 | L | "Independent of direct processing" for the opening committee covers only Tender Version actors and the publish | See finding. | Todo | | | | |
| XC-137 | L | Open segregation questions in approved documents (Finance vs Budget Officer, BDS signatory, Contract) | See finding. | Todo | | | | |

### WP7.HND — Hand-offs — remaining Medium/Low

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| HND-010 | L | NDS accepted-Need contract has two key shapes under one `.v2` tag; quantity is a JSON float | See finding. | Todo | | | | |
| HND-011 | L | REQ v1.14 is internally inconsistent about its own version status and conflicts with E2E-REQ-001 v0.2 | See finding. | Todo | | | | |

### WP7.STR — Strategy — remaining Medium/Low

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| STR-009 | M | Snapshot and lineage payloads carry Frappe docnames, not the generated references, and omit §8 fields | See finding. | Todo | | | | |
| STR-010 | M | Planning and Requisitions read Strategy tables directly; objective reference column does not exist | See finding. | Todo | | | | |
| STR-012 | L | Submitter blocked from Return, contrary to §12.4 | See finding. | Todo | | | | |
| STR-013 | L | `effective_to` not bounded by the plan period on the server | See finding. | Todo | | | | |
| STR-014 | L | Plan type cannot be changed in the first Draft although §11.3A shows the control | See finding. | Todo | | | | |
| STR-015 | L | Existence of a plan is distinguishable from refusal | See finding. | Todo | | | | |
| STR-016 | L | Hierarchy and target validation raise untyped errors where §9 requires typed codes | See finding. | Todo | | | | |
| STR-017 | L | §9 error vocabulary contradicts the AUTH-ADR-001 §10 closed vocabulary Strategy is bound to | See finding. | Todo | | | | |
| STR-018 | L | Predecessor closure can lengthen the predecessor's applicability | See finding. | Todo | | | | |
| STR-019 | L | Seed plan title lacks "(Demo)"; §14.3 identifiers cannot be produced under STR-BR-016 | See finding. | Todo | | | | |
| STR-020 | L | Extra `fixture_namespace` field on every Strategy DocType | See finding. | Todo | | | | |
| STR-021 | L | Workspace shortcut still labelled "Strategy Portfolio" | See finding. | Todo | | | | |

### WP7.BUD — Budget — remaining Medium/Low

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| BUD-005 | M | `check_funding` writes a ledger-table event on every call | See finding. | Todo | | | | |
| BUD-008 | M | Approval document removed from the evidence gate against approved BUD-BR-004 | See finding. | Todo | | | | |
| BUD-009 | M | No historical funding position, no CurrencyBasis, no `get_budget_currency_contract` | See finding. | Todo | | | | |
| BUD-011 | M | Procurement lifecycle and Requisitions read Budget tables directly; Budget reads Planning tables | See finding. | Todo | | | | |
| BUD-014 | L | Mixed release/convert hold ends as `Released`; Close blocked for the version's submitter | See finding. | Todo | | | | |
| BUD-015 | L | Seed diverges from §15.3/§15.5/§15.6 (generated line references, BUD-SC-FIN-* names, relative dates) | See finding. | Todo | | | | |
| BUD-016 | L | SPEC DEFECT: canonical route `/app/budget` cannot be served (collides with ERPNext Budget) | See finding. | Todo | | | | |
| BUD-017 | L | SPEC DEFECT: BUD-BR-027 "no ledger event" vs §14 request events in the same ledger | See finding. | Todo | | | | |

### WP7.NDS — Needs — remaining Medium/Low

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| NDS-004 | M | A superseded accepted revision cannot be read at its own route; the page shows the current revision | See finding. | Todo | | | | |
| NDS-006 | M | A Returned correction can be resubmitted after intake closes; the next-step answer says it cannot | See finding. | Todo | | | | |
| NDS-008 | M | Unknown save/submit outcome is not resolved; a refresh mints a new key and can create a second root | See finding. | Todo | | | | |
| NDS-012 | L | Successor / withdrawal mutual exclusion is enforced late, with the wrong code, and without a stale-source chec | See finding. | Todo | | | | |
| NDS-013 | L | Intake and usage ordering compares timestamps as strings | See finding. | Todo | | | | |
| NDS-014 | L | Usage projection keeps a third value "Not proceeding" | See finding. | Todo | | | | |
| NDS-015 | L | The Procurement Planner is given a full Needs workspace | See finding. | Todo | | | | |
| NDS-016 | L | The Vue app reads error meaning from message text | See finding. | Todo | | | | |
| NDS-017 | L | §7.1 lists a PE id in the accepted payload; §3/§4.2/§1.1 say the PE is implicit | See finding. | Todo | | | | |
| NDS-018 | L | Withdrawn Needs cannot be found from the register (owner decision open) | See finding. | Todo | | | | |
| NDS-019 | L | NDS §14 seed fixture differs from the executable two-year seed world | See finding. | Todo | | | | |

### WP7.PLN — Planning — remaining Medium/Low

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| PLN-005 | M | Strategy snapshot is taken at Plan Item save, not at final approval, and ignores the plan's fiscal year | See finding. | Todo | | | | |
| PLN-009 | M | ReturnPlanVersion records no collective resolution and caps the reason at 500 | See finding. | Todo | | | | |
| PLN-011 | M | Splitting confirmation is free text with no related-item set, rule Version or stale-finding check | See finding. | Todo | | | | |
| PLN-012 | M | "Fixture-verified — not production law" passes every verification gate (spec gap) | See finding. | Todo | | | | |
| PLN-014 | L | Planning raises a Finance notification where the spec says Planning sends none | See finding. | Todo | | | | |
| PLN-016 | L | Return issue entry ids are not validated | See finding. | Todo | | | | |
| PLN-017 | L | PLN_BASELINE_LOCKED is raised for only two edit shapes | See finding. | Todo | | | | |
| PLN-018 | L | WithdrawDepartmentalSubmission cannot withdraw a Submitted plan; spec is ambiguous (spec gap) | See finding. | Todo | | | | |
| PLN-019 | L | Combination rule: PLN §5.6.2 and PLN18-AC-055 disagree; code adds an undocumented origin restriction | See finding. | Todo | | | | |
| PLN-022 | L | Departmental plan is auto-created on Need acceptance (spec gap) | See finding. | Todo | | | | |

### WP7.REQ — Requisition — remaining Medium/Low

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| REQ-010 | M | Supporting files: no private/ownership check, "Not scanned" accepted, no download predicate | See finding. | Todo | | | | |
| REQ-011 | L | Item/service dates are validated at write time only | See finding. | Todo | | | | |
| REQ-012 | L | `GetRequisitionHistory` omits drawdown/reservation/reversal/consumption evidence; outbox is never relayed | See finding. | Todo | | | | |
| REQ-013 | L | Closed error codes with no raise site; "internally contradictory" Blocking finding unimplemented | See finding. | Todo | | | | |
| REQ-014 | L | Planning outcome sequence gaps are not detected | See finding. | Todo | | | | |
| REQ-015 | L | HOPF lead directive survives only the immediate successor Draft | See finding. | Todo | | | | |
| REQ-016 | L | Direct read of Budget's Funding Reservation table and import of a private Planning helper | See finding. | Todo | | | | |

### WP7.TND — Tenders — remaining Medium/Low

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| TND-009 | M | Cancellation grounds are a code-owned, unverified list | See finding. | Todo | | | | |
| TND-010 | M | Publication/addendum evidence is accepted with "Not scanned" | See finding. | Todo | | | | |
| TND-011 | L | Reopen of an approved Tender skips the compatibility recheck | See finding. | Todo | | | | |
| TND-012 | L | Doc says one publication authorisation per approved Version; code allows several after withdrawal | See finding. | Todo | | | | |
| TND-014 | L | Back saves a dirty Draft silently; no "Leave without saving?" | See finding. | Todo | | | | |
| TND-015 | L | "Contact administrator" control is absent | See finding. | Todo | | | | |
| TND-016 | L | Late-amendment window is a hard-coded 7 days, not a configured/verified rule | See finding. | Todo | | | | |
| TND-017 | L | Two TPR section 5.2 / AC rules have no field or server rule behind them | See finding. | Todo | | | | |
| TND-018 | L | Certified lead and contributing OU identifiers are not on `GetTender` | See finding. | Todo | | | | |
| TND-019 | L | "Authorise publication" is offered when no publication rule exists | See finding. | Todo | | | | |

### WP7.EVL — Evaluation — remaining Medium/Low

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| EVL-009 | M | Clarification-reply attachments bypass the shared upload integrity check | See finding. | Todo | | | | |
| EVL-011 | M | Accounting Officer / Head of Procurement see committee free text and a submission version before delivery | See finding. | Todo | | | | |
| EVL-012 | M | `ExportEvaluationRecord` / "Download report" is not a server operation | See finding. | Todo | | | | |
| EVL-017 | M | No authoritative statutory evaluation deadline exists, so overdue highlighting is dead in production | See finding. | Todo | | | | |
| EVL-018 | L | Published rounding mode (`ROUND_HALF_UP`) is ignored by the price calculation | See finding. | Todo | | | | |
| EVL-019 | L | "Test attestation — not an electronic signature" label absent from Evaluation signing views | See finding. | Todo | | | | |
| EVL-020 | L | A verification plan never clears the chair's discussion item | See finding. | Todo | | | | |
| EVL-021 | L | A failed second package read after intake rolls everything back without recording an issue | See finding. | Todo | | | | |
| EVL-022 | L | EVL v0_5 says the Head's item clears on "return" but `ReturnEvaluationReport` carries no source event | See finding. | Todo | | | | |
| EVL-023 | L | EVL v0_5 control table, history and task-title claims are inconsistent | See finding. | Todo | | | | |

### WP7.AWD — Award — remaining Medium/Low

| ID | Sev | Finding | Approach / acceptance | Status | Red test | Commit | Verified on | Notes |
|---|---|---|---|---|---|---|---|---|
| AWD-007 | M | Contracting package "contract terms" are constant strings, not mapped tender data | See finding. | Todo | | | | |
| AWD-008 | M | §88 validity extension and the notice's contracting window are not modelled | See finding. | Todo | | | | |
| AWD-012 | L | `RecordAwardDecision` does not read live tender status before committing | See finding. | Todo | | | | |
| AWD-013 | L | "Issue in progress" is not durable before the first outward effect and an interrupted issue has no recovery | See finding. | Todo | | | | |
| AWD-014 | L | Authority-status contract answers "no decision / not issued" from absence of a case | See finding. | Todo | | | | |
| AWD-016 | L | Award never checks the product profile or the published award method | See finding. | Todo | | | | |
| AWD-017 | L | AWD v0_5 still carries "proposed"/"would establish" wording after approval | See finding. | Todo | | | | |
| AWD-018 | L | AWD v0_5 §15 says "Persist timestamps in UTC"; the project rule and the code store site time | See finding. | Todo | | | | |

## Documentation workstream (controlled document changes)

Requirements documents are changed only through the document-change protocol (full rewrite at the next version, nothing marked approved without the owner). Each item below is raised with the owner after the code it describes is verified.

| ID | Document | Change | Triggered by | Status |
|---|---|---|---|---|
| D-1 | AWD-CHG-001 → v0.6 | Record the HOPF/AO rule; remove leftover "proposed" wording; state timestamps are site time, not UTC | D2; AWD-001, AWD-017, AWD-018 | Todo |
| D-2 | PLN-CHG-001 → v1.30 | Manual Annual Plan publication replaces the post-commit worker; add who publishes; departmental correction route wording | D4; XC-106, XC-121; PLN-020; RG-01 | Todo |
| D-3 | TPR-CHG-001 → v0.18 | TM2 retired; handoff v1.4; fix the REQ cross-reference (§10.14, not §10.4); late-confirmation exit | D1; HND-001, HND-009, TND-002, TND-012 | Todo |
| D-4 | REQ-CHG-001 → v1.15 | Handoff v1.4; §7.4 cross-reference; reconcile with E2E-REQ-001; Budget caller wording | HND-009, HND-011 | Todo |
| D-5 | BUD-CHG-001 → v1.13 | Caller table already in place; resolve `/app/budget` route collision; ledger vs request-event wording | BUD-016, BUD-017 | Todo |
| D-6 | EVL-CHG-001 → v0.6 | Control-table version; "return clears the Head’s item"; supersede wording | EVL-022, EVL-023 | Todo |
| D-7 | NDS-CHG-001 → v1.17 | PE id in the accepted payload; disposition enum and sequence; seed fixture | NDS-017, NDS-009, NDS-019 | Todo |
| D-8 | STR-CHG-001 → v1.10 | Error vocabulary vs AUTH §10; seed title; define "author" for no-self-approval | STR-006, STR-016, STR-017, STR-019 | Todo |
| D-9 | AUTH-ADR-001 | Whether Administrator/System Manager may hold write on business doctypes; OVS 4.2 vs BOP | XC-013, XC-028 | Todo |

## Won’t-fix and risk-accepted register

| ID | Finding | Accepted by | Date | Reason |
|---|---|---|---|---|
| — | none yet | | | |

## Change log

| Date | Change |
|---|---|
| 6 Oct 2026 | Tracker created; all findings Todo; owner decisions D1–D4 recorded. |
| 7 Oct 2026 | Four regression sweeps and the integration gate (INT-A, INT-B) reconciled: rows the sweeps closed set Verified, partial rows set Red, Wave 4R (RG-01 to RG-42) added; verdicts live in `audit/progress/REGRESS.md`; `merge_progress.py` gained the REGRESS overlay and the Wave 4R dashboard row. |
