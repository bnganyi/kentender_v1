# Budget & Funding — gap analysis against BUD-CHG-001 v1.3

**Authority:** `KenTender_BUD-CHG-001_Clean_Budget_and_Funding_v1_3.md` (approved 3 September 2026; supersedes v1.2 and all earlier versions in full).
**Companions:** `03_BUD_Rebuild_Implementation_Plan.md`, `IMPLEMENTATION_TRACKER.md`, `FOLLOW_UPS.md`.
**Analysis date:** 2026-09-04
**Implementation under review:** `kentender_budget/kentender_budget/` (doctypes, services, api, seeds, tests, public/js), plus `apps/erpnext/erpnext/accounts/doctype/budget/` (out-of-app, see §9).

## 1. Executive summary

Unlike Strategy Alignment, **this is a true correction pass against an untouched baseline** — no same-day commit has landed for v1.3. Every schema field, service signature, role, seed and route documented below is exactly where BUD-CHG-001 v1.2 left it. The one piece already partly aligned — `business_role_registry.py`'s `SCOPE_SITE` classification for Budget Officer/Approver/Finance Confirmation Officer — isn't wired into any live code path, so it has no effect today.

Three things make this rebuild materially harder than Strategy's fresh v1.6 precedent:

1. **A real DocType-name collision, not a hypothetical one.** `Budget`/`BudgetVersion`/`BudgetLine`/`BudgetLineVersion` must be renamed to the `Procurement Budget` family because ERPNext ships its own `Budget` DocType. This rename touches every layer — schema, services, API, routes, fixtures, tests — and has no precedent anywhere in this repo (no prior `frappe.rename_doc` migration exists to crib from).
2. **The ERPNext `Budget` DocType was not merely uninstalled, it was surgically deleted from the vendored `apps/erpnext` app** — the reason `/app/budget` is a colliding slug today. See §9.
3. **v1.3 explicitly requires `kentender_scope_map` registration** (§17.1) — a mechanism confirmed empty and unused across the entire live codebase, including by Strategy's own just-completed rebuild, which deliberately opted out of it. Budget will be the first production consumer of this integration path end to end.

Verdict: full correction pass required across schema, authorization, roles, seeds, service contracts, UI, and a genuinely out-of-repo dependency (`apps/erpnext`). Nothing here can be treated as "confirm and move on" the way most of Strategy's gap analysis could.

## 2. What is already correct (verified — narrow, confirm in Phase 1 rather than re-plan)

| # | Item | Evidence |
|---|---|---|
| 1 | Budget Officer / Budget Approver / Finance Confirmation Officer registered `SCOPE_SITE` in the business-role registry | `kentender_core/kentender_core/services/business_role_registry.py:138-142,167-173` — but not called by Budget's own service code, so inert today |
| 2 | Seeded Budget/Version/Line IDs already match §15.3's exact expected values | `kentender_core/kentender_core/seeds/kentender_mvp_v1/constants.py:87-93` — `MOH-BUD-2027-001`, `-V1`, `MOH-BL-DHI-2027`, `MOH-BL-HWD-2027` |
| 3 | Artboard set is essentially complete for §11 — no missing BUD-DES ID | `docs/mvp-1-r1/03_budget/design/*.dc.html` (22 of 30 files map cleanly to a live §11 ID; the other 8 model the two explicitly-retired screens, see §7 below) |
| 4 | `Cost Center` (unlike `Budget`) is genuinely untouched on this bench | ERPNext's real `cost_center.json` present and live; no KenTender doctype claims that name |
| 5 | Every one of the 15 documented service contracts already exists under its final name | `kentender_budget/kentender_budget/services/*.py`, `api/budget_api.py` — signatures need correcting (§5), not building from scratch |
| 6 | `kentender_procurement`'s sidebar link is already the modern `/desk/budget-funding` Page reference, not a stale Workspace pointer | `kentender_procurement/kentender_procurement/workspace_sidebar/procurement.json:53-58` |

## 3. §1.1 disposition register — row-by-row verdict against current code

| Spec disposition | Present in code? | Evidence | Verdict |
|---|---|---|---|
| DocType named `Budget` → **rename to `Procurement Budget`** family | **Yes — violated** | `doctype/budget/budget.json` `"name": "Budget"`; `budget_version`, `budget_line`, `budget_line_version` likewise unrenamed | Full rename, own phase |
| Relationship to ERPNext Cost Center → **none** | Compliant | No `cost_center` field found on any Budget doctype | Already compliant |
| `procuring_entity_id` on `Budget` → **remove** | **Yes — violated, live and required** | `budget.json:41-47` — field name is `procuring_entity` (no `_id` suffix, same field), `reqd: 1` | Delete field |
| `financial_year_id` → `fiscal_year` (ERPNext `Fiscal Year`) | **Yes — violated, both name and Link target wrong** | `budget.json:48-55` — field named `financial_year`, Link `options: "Financial Year"` (KenTender's own disposed doctype, not ERPNext's `Fiscal Year`) | Rename field, repoint Link |
| PE/FY/capability-scoped assignments → **remove PE, FY, capability entirely** | **Yes — violated, structurally** | `budget_authorization.py` imports `authorization_native.{evaluate_role_capability,require_role_capability}` and `authorization_policy.ResourceContext` (whose dataclass literally carries `procuring_entity_id`/`financial_year_id`/`pe_fy_context_id` fields); `require_budget_read_scope()` does a raw `User Permission` PE-scope read | Full authorization rewrite |
| "Capability" as the permission primitive → **remove** | **Yes — violated** | `CAP_LIST`/`CAP_VIEW`/`CAP_CREATE`/`CAP_EDIT`/`CAP_SUBMIT`/`CAP_RETURN`/`CAP_APPROVE`/`CAP_EXPORT` constants in `budget_authorization.py:25-32`; `require_budget_version_capability` still called from `budget_contracts.py:796` | Replace with registered business roles throughout |
| `Budget Viewer` workflow role → **remove** | **Yes — violated, extensively live** | DocPerm rows on 7 doctypes + the `budget_funding` Page; `business_role_registry.py:166`; `budget_permissions.py:11-29`; seed users; `authorization_role_registry.py:39,70-71`; **plus 3 additional stale roles in `kentender_procurement`'s own allowlist** (`Budget Reviewer`, `Budget Authority`, `Budget Activation Authority`) that v1.2 already claimed to have collapsed but never actually removed from Procurement's side | Remove everywhere, including the Procurement-side leftovers |
| `owner_org_unit_id` on the line version → **retain unchanged**, label becomes "Entity-wide" | Compliant field, label unverified | `budget_line_version.json:62-68` — field present, described as "Empty means PE-wide" (old label text) | Keep field/logic; correct only the display label to "Entity-wide" |
| County Government of Kisumu (`PE-CGK`) baseline, its actors, cross-PE isolation tests → **remove entirely** | **Yes — violated, live** | `kentender_mvp_v1_portfolio.py:236-239,267-285` still creates the full Kisumu baseline; a **shared, kentender_core-owned** cross-PE isolation test (`test_kentender_mvp_v1_seed_contract.py:146-164`) depends on Budget-owned fixture constants | Delete seed baseline; fix the shared test (lives outside `kentender_budget`) |
| Bespoke fixture cast → shared KT-STD-001 §8.3 register, extended by §14.1 | **Not yet added, and the extension point itself is malformed** | KT-STD-001 §8.3 has 6 rows, none of Budget's 2 required actors or the Naomi Chebet actor Budget's own spec assumes is already there from Strategy's work (it isn't — see §10) | Add 3 actors; resolve the §8.5 section-purpose collision (it's "Units of measure," not a fixture-timeline register) |
| PE row/selector in every artboard context strip and identity card → **remove** | **Yes — violated, on all 5 live screens** | See §7 | Remove; replace with FY-only local filter |
| "existing KenTender PE/FY selector" → **remove**, component no longer exists | **False — it still exists** | `WorkingContextPicker.vue` is a combined PE+FY selector, used on every screen with no explicit record ID, backed by `useWorkingContext.js` | Replace with a Budget-owned FY-only filter |

## 4. Domain model diff (§4)

### 4.1 DocType rename mapping

| Current name | v1.3 name | Notes |
|---|---|---|
| `Budget` | `Procurement Budget` | Collides with ERPNext's own `Budget` doctype today (see §9) |
| `Budget Version` | `Procurement Budget Version` | |
| `Budget Line` | `Procurement Budget Line` | |
| `Budget Line Version` | `Procurement Budget Line Version` | |
| `Funding Reservation` | (unchanged) | No collision, no rename required by v1.3 |
| `Procurement Commitment` | (unchanged) | |
| `Budget Audit Event` | (unchanged) | |

### 4.2 `Budget` (→ `Procurement Budget`) field-by-field

| Current field | Spec disposition | Gap |
|---|---|---|
| `generated_reference`, `title`, `currency` | Keep | None |
| `procuring_entity` | **Delete** | Live, required (§3) |
| `financial_year` | **Rename to `fiscal_year`, repoint Link to ERPNext `Fiscal Year`** | Both name and target wrong (§3) |

### 4.3 `Budget Line Version` (→ `Procurement Budget Line Version`) field-by-field

| Current field | Spec disposition | Gap |
|---|---|---|
| `title`, `funding_source`, `approved_amount` | Keep | None |
| `owner_org_unit` | **Keep unchanged**; correct the "Empty means PE-wide" label to "Empty means Entity-wide" | Field/logic compliant; label text stale |

### 4.4 Other doctypes

`Budget Version`, `Budget Line`, `Funding Reservation`, `Procurement Commitment`, `Budget Audit Event` match §4.2–§4.7's field shapes — the only gap on these is the rename cascade (§4.1) and, on `Budget Version`/`Budget Line`, the `budget` Link fieldname needing to track the renamed parent doctype. No missing or extra fields found beyond the DocType-name cascade.

### 4.5 Genuinely dead/empty doctype folders — already clean

`budget_line_supporting_target`, `budget_revision`, `budget_revision_line`, `expenditure_snapshot`, `funding_exception` — folders exist with no `.json`, only stale `__pycache__`. Not live DocTypes. No action required beyond confirming they stay that way.

## 5. Service and command contract gaps (§9)

### 5.1 Every contract takes a PE parameter that must be dropped

`resolve_budget_context(procuring_entity: str | None = None, financial_year: str | None = None)` (`budget_contracts.py:395`) takes both a PE and FY param; the correct §9.1 shape is Fiscal Year only. `check_funding`/`reserve_funding` have no explicit PE param in their own signature, but internally call `_require_finance_capability(procuring_entity)` (`budget_check_reserve_contracts.py:31-42`) which independently performs the same raw `User Permission` PE-scope read `budget_authorization.py` does — this is duplicated logic in two files, not a single choke point.

### 5.2 Authorization is on the wrong engine, structurally, not just parametrically

`budget_authorization.py`'s own header comment (lines 1-15) states it deliberately uses "AUTH-ADR-001's native Frappe Role + User Permission engine... not... the AUTH-ADR-001 v1.6... URA... engine" — i.e. it is self-aware v1.2-generation code, one full engine removed from the v1.6 target. Contrast with `kentender_strategy/kentender_strategy/services/strategy_authorization.py` (rewritten this week): calls `authorise_record(user=, business_role=, organisation_unit="", purpose=PURPOSE_COMMAND)`, no capability strings, no `ResourceContext`, no PE param, no `User Permission` read; no-self-approval read from the audit trail (`list_events()` filtered by action + actor), not a stored field. Budget's own `require_budget_read_scope()` (`budget_authorization.py:168-179`) is the exact anti-pattern AUTH-ADR-001 v1.6 §5.2/§18.1 prohibits: "domain apps never query the assignment DocType and never write module-local scope logic."

### 5.3 No Budget-owned FY-only read contract exists

Every FY-aware read today goes through the combined PE+FY `get_working_context`/`select_working_context` pair (`kentender_core.api.reference_data_api`). Strategy already solved the equivalent problem this week with a 3-line, narrowly-justified `list_available_fiscal_years()` (`strategy_ui_contracts.py:623-636`, `frappe.get_all("Fiscal Year", ..., ignore_permissions=True)`) — Budget needs its own copy of this pattern, not a shared dependency on Strategy's or a continued dependency on the combined PE+FY resolver.

### 5.4 The pinned cross-app contract test locks in the PE parameter

`kentender_procurement/.../tests/test_gateway_contracts.py:27` explicitly asserts `list_eligible_budget_lines`'s parameter set includes `"procuring_entity"` — this test will fail the moment the contract is corrected, by design ("pin the *published* signatures the gateways depend on, so a Budget or Strategy refactor fails here"). The same file already carries the done version of this exact fix for Strategy (line ~51-59: `assertNotIn("procuring_entity", params)`, CU-306 comment) — direct in-repo precedent for how to update it.

## 6. Permission gaps (§7)

| Spec requirement | Today |
|---|---|
| Exactly three Budget business responsibilities, all `Site-wide`: Budget Officer, Budget Approver, Finance Confirmation Officer | Registered correctly in `business_role_registry.py` (§2 item 1) — but not wired into any authorization call |
| "There is no Budget Viewer role" | **Violated, extensively.** See §3's row above — 7 doctype DocPerm rows, the registry entry, `budget_permissions.py`, seed users, dead capability mappings, and 3 *additional* stale roles in `kentender_procurement`'s allowlist |
| `Auditor` is a registered business role, confers no Budget mutation | Registered `SCOPE_SITE` in `business_role_registry.py:125-130`; Budget's own DocPerm rows already grant it read on all 7 doctypes — compliant, confirm in Phase 1 |
| The contract service principal (Contract Management calling `convert_reservation`/`adjust_commitment`) is an authenticated service account, not a business role | Not independently verified this pass — flagged for Phase 1 confirmation |
| `kentender_scope_map` registration required (§17.1, unlike Strategy) | **No entry exists anywhere in the live codebase** — not for Budget, not for any app. This mechanism has zero production consumers today. Confirmed (via direct trace of `scope_condition()`/`has_permission()` in `authorization.py`) that registering is **not** a no-op for a site-wide role: a DocType absent from the map falls through entirely to native DocPerm (a stale/unsynced Frappe Role grant would still work); a DocType present in the map with zero matching assignment rows returns a hard `1=0` — i.e. registering closes a real gap, it is not paperwork. Budget is the mechanism's first production consumer, with no in-repo precedent to crib from |

## 7. UI / route architecture (§10)

Current implementation is **one** Frappe Page (`budget-funding`), not the literal 5-route `/app/budget/...` table §10 specifies, and the slug itself is a documented workaround:

| §10 canonical route | Current | Gap |
|---|---|---|
| `/app/budget` (Workspace) | `/app/budget-funding` | Slug mismatch |
| `/app/budget/{budget_id}/version/{version_number}/edit` (Version editor) | `/app/budget-funding/{id}/version/{n}[/tab]` or `.../new/...` | Prefix mismatch, path shape otherwise close |
| `/app/budget/{budget_id}` (Budget workspace) | `/app/budget-funding/{id}[/tab]` | Prefix mismatch |
| `/app/budget/review/{budget_version_id}` (Approval task) | `/app/budget-funding/review/{id}[/tab]` | Prefix mismatch |
| `/app/budget/line/{budget_line_id}` (Line detail) | `/app/budget-funding/line/{id}` | Prefix mismatch |

`budget_funding_page.js:1-12` documents the reason directly: because a DocType named `Budget` already exists (KenTender's own), Frappe's client router auto-registers `/app/budget` as that DocType's native List View, "poisoning" the whole prefix — so `budget-funding` was chosen specifically to dodge it. **Once the DocType rename (§4.1) lands, this specific collision reason goes away** — but whether that alone is sufficient to safely adopt the literal `/app/budget` prefix depends on whether ERPNext's own (currently-shimmed, see §9) `Budget` doctype would also claim that slug once restored. This needs Phase 1's live route research before Phase-sizing, exactly as Strategy's own still-open route-architecture question does — Strategy's tracker lists its equivalent item as `Planned`, not a closed, provable precedent to copy blindly.

**PE/FY context selector is structural, not incidental**, and worse than Strategy's equivalent gap: every one of the 5 screens shows a Procuring Entity row/card (`workspace?.procuring_entity?.name` and equivalents in each screen component) and mounts the shared `PageRail.vue` with `showPeSwitcher: true`. `WorkingContextPicker.vue` is a *combined* PE+FY selector (not FY-only), used whenever a screen loads without an explicit record ID — i.e. exactly the workspace's initial-load state, the one place v1.3 wants a bare FY filter. Fixing this requires more than hiding UI: `useWorkingContext.js` threads a PE value through the underlying data calls even when not displayed, which would still violate BUD-AC-036 ("No `procuring_entity_id`... exists in Budget... services"). Budget needs its own FY-only resolution path end to end, not a display-layer patch on the shared component.

## 8. Seeds and tests

- `kentender_budget/kentender_budget/seeds/kentender_mvp_v1_portfolio.py` still creates the full Kisumu (`PE-CGKIS`) second-PE baseline (lines 236-239, 267-285) — Budget/Version/Line/actors, with its own approval document reference. v1.3 §1.1/§15.6 requires deleting this entirely.
- The cross-PE isolation test using Budget's own seed constants (`C.CGK_BL_COLDCHAIN` etc.) lives **outside `kentender_budget`**, in `kentender_core/kentender_core/tests/test_kentender_mvp_v1_seed_contract.py:146-164` — this will break the moment the Kisumu seed is removed and must be fixed in the same phase, even though it's not this app's own test file.
- `kentender_core/kentender_core/seeds/kentender_mvp_v1/users.py` still seeds `MOH Budget Viewer`/`Kisumu Budget Viewer` users. Some role tuples combine `("Strategy Viewer", "Budget Viewer")` — only the `Budget Viewer` half is this change unit's to remove; `Strategy Viewer` is Strategy's own still-open, separately-tracked violation (its tracker rows STR-401..404).
- 2 existing Budget test files (`test_bud_chg_001_phase3_lifecycle.py`, `test_bud_chg_001_phase3_check_reserve.py`) reference only `PE_MOH`, not `PE_CGKIS` — the module's own tests don't currently exercise cross-PE isolation at all; that assertion lives entirely in the shared `kentender_core` test above.
- No Budget design-fidelity gate exists (`tests/ui/smoke/design-fidelity/` has only `system-setup-fidelity.spec.ts`). **14 fully-dead legacy Makefile targets exist** (`ui-budget-funding-portfolio-gate` through `ui-budget-role-gate`, Makefile lines 264-393), referencing a 12-screen `BUD-UI-01..12` model and Playwright specs/Python tests/seeds that don't exist anywhere in the live tree — a full stale generation predating the v1.2 rebuild, never cleaned up. These need retiring, not migrating.
- FOLLOW_UPS.md's 4 open items (FU-01: dead `budget_workspace` import breaking fresh-site migrate; FU-02: two tests requiring a deleted `Budget Management` Workspace; FU-03: a Strategy-side workspace-shell issue riding the same test; FU-04: stale `budget-builder`/`budget-workbench` references, confirmed at **4** locations, one more than the file itself currently documents, including `kentender_budget/kentender_budget/patches/mvp1_teardown_drop_legacy_budget_doctypes.py:21`) are all still open and all intersect this rebuild's route/role phases.
- Artboard set: 8 of 30 `.dc.html` files (4x "Activation Task - *", 4x "Initial Baseline Activation - *") model the explicitly-retired BUD-DES-12/BUD-DES-13A second-decision-stage screens — confirmed by content, they contain literal "Awaiting Activation"/"Budget Reviewer" text. §17.1 (line 1285) already instructs "do not port" a retired artboard; these should be flagged/removed, not built against.

## 9. The ERPNext `Budget` DocType shim — a pre-existing, out-of-repo dependency

`apps/erpnext/erpnext/accounts/doctype/budget/budget.json` **does not exist** — deleted entirely, not merely uninstalled. Only a hand-written stub controller remains (`budget.py`, header comment: *"ERPNext Budget DocType was removed from this bench when KenTender MVP-1 claimed the 'Budget' DocType name"*), with a placeholder `Budget(Document): pass` and no-op `validate_expense_against_budget`/`get_accumulated_monthly_budget` functions — kept only so `general_ledger.py`/`buying_controller.py`/`budget_controller.py`'s import statements don't crash. Confirmed directly this session:

```
$ bench --site kentender.midas.com list-apps
frappe 16.12.0 UNVERSIONED
erpnext 16.10.1 UNVERSIONED
...
$ frappe.db.get_value('DocType', 'Budget', 'module')
'Kentender Budget'
```

ERPNext is genuinely installed on this site; "Budget" today resolves entirely to KenTender's own doctype. `apps/erpnext` itself has no usable git history to restore from (`git status` on that path shows the whole `budget/` directory as untracked; the checked-out branch has no commits). This predates BUD-CHG-001 v1.3 and was created by Budget's own earlier v1.0/v1.1-era land-grab of the "Budget" name, not by anything this change unit did.

**Decision (resolved with the module owner, recorded in the tracker): scope in restoring ERPNext's real `Budget` DocType** as prerequisite work, rather than treating BUD-AC-038 ("ERPNext accounting and its own Budget... remain fully functional") as a documented, permanent deviation. This can only happen after the KenTender rename (§4.1) frees the `Budget` name — the two DocTypes cannot coexist under the same name on one site. Sourcing the correct historical files for the installed version (16.10.1) is itself a research question with no guaranteed answer; see the implementation plan's Phase 3 and its documented fallback if the source can't be reliably found.

## 10. Documentation hygiene

- `business_role_registry.py:132-173`'s Budget entries all cite `"BUD-CHG-001 v1.2 §7"` — needs bumping to v1.3 in the same pass that touches this file for role cleanup.
- KT-STD-001 §8.3 does not yet carry Josphat Mwangi or Beatrice Kamau, and — contrary to v1.3 §15.1's own assumption ("Naomi Chebet (Auditor) is added by STR-CHG-001 v1.6 §14.1 and reused here") — **Naomi Chebet does not exist in any live seed code or the KT-STD-001 document either.** STR-CHG-001 v1.6 claimed this addition this week but never actually landed it; the real Strategy seed grants an unrelated existing user (Mercy Kilonzo) the Strategy Author role via an ad-hoc code comment instead. This is genuinely a three-way inconsistency (KT-STD-001 doc, STR-CHG-001's stated requirement, actual seed code), not a simple missing-row gap. **Decision (resolved with the module owner): Budget's plan adds only its own 3 required actors (Naomi Chebet + Josphat Mwangi + Beatrice Kamau); Strategy's separate Esther Muthoni/Alfred Ochieng gap is flagged as that module's own unfinished business, not absorbed here.**
- §8.5 as currently written is "Units of measure" (a UOM table), not a fixture-timeline/instants register — both STR-CHG-001 v1.6 and BUD-CHG-001 v1.3 assume it becomes/gains one. This section-purpose collision needs resolving (new subsection, or relocate to §8.4 "Fiscal years") before either module's fixture-instant addition can land cleanly.
- CFG-CHG-002 v0.6 has zero mentions of "funding" anywhere. The `Funding Source` DocType (`kentender_core/kentender_core/kentender_core/doctype/funding_source/funding_source.json`) already exists and works, created ad hoc by Budget's own v1.2 rebuild (commit `bc6464f9`) with no CFG-CHG-002 mandate. **Decision (resolved with the module owner): leave the DocType where it is, record the ownership gap as a cross-doc follow-up flagged to CFG-CHG-002's owner — do not edit CFG-CHG-002 within this change unit.**

## 11. Known decisions carried into the plan

All three resolved with the module owner on 2026-09-04; full rationale in the implementation plan's decision register and the tracker's decision log.

1. **ERPNext `Budget` DocType shim (§9)** — scope in restoration as prerequisite work, not a documented deviation.
2. **KT-STD-001 §8.3 scope** — add only Budget's 3 required actors; flag, don't fix, Strategy's separate Esther/Alfred gap.
3. **Funding-source catalogue ownership** — document as a CFG-CHG-002 follow-up; do not edit that document here.

Two items intentionally **not** resolved here, both gated on Phase 1 research: the UI route-slug migration's exact scope (§7), and the `kentender_scope_map` registration mechanics as Budget's first production use of that path (§6).
