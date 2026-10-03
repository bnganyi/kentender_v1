# RES-IMP-001 — Reservation Correction Implementation Handoff

**Current approval record — 1 October 2026.** The Project Owner instructed: “Mark all the proposed documents as approved”. This approves RES-IMP-001 v1.0 in full, including its incorporated amendments. This record supersedes earlier pending/proposed approval wording and conditional predecessor-authority statements retained below as drafting history. Earlier versions remain historical. Approval does not establish implementation completion, test success, legal verification or production release; existing operating gates and substantive follow-ups remain in force.

| Control | Value |
|---|---|
| Document ID | RES-IMP-001 |
| Version | 1.0 |
| Date | 24 September 2026 |
| Status | **Approved requirement — Project Owner approved 1 October 2026** |
| Purpose | One focused functional-and-design correction scope for Claude Design and Claude Code |
| Approved governing baselines | LAW-REG-001 v1.2; BUD-CHG-001 v1.10; PLN-CHG-001 v1.25; CFG-CHG-002 v0.14 |
| Coordinated downstream drafts | REQ-CHG-001 v1.10; TPR-CHG-001 v0.9; STD-TPL-001 v0.7; BDS-CHG-001 v0.6 |
| Shared standards | KT-STD-001 v1.7; AUTH-ADR-001 v1.9 |

## 1. The correction in one page

### 1.1 Canonical decisions

1. The 30% planning denominator is the **eligible value of the exact current complete Annual Procurement Plan Version**. It is not the approved Budget ceiling and excludes unused Budget headroom.
2. The approved Budget remains a separate **funding ceiling and affordability control**.
3. Planning records an intended base reservation category: `None`, `Youth`, `Women` or `Persons with disabilities`.
4. County-residents treatment is a **separate independently applicable measure**, not a fifth base category. It requires a county Procuring Entity, a verified effective rule and explicit overlap treatment.
5. Every current Plan Item must be included in or excluded from each applicable measure under the exact rule, with an inspectable reason. Omission cannot be used to reduce the denominator.
6. A successor APP Version recalculates its own denominator, target, qualifying allocation and shortfall. It never rewrites the predecessor snapshot.
7. Planning designation is not supplier entitlement. Supplier entitlement is established only by the published declaration/evidence requirements and the governed evaluation result.
8. Actual achievement is a separate downstream calculation using authoritative actual procurement/award facts. It is never inferred from APP estimates.

### 1.2 Canonical fixture

| Fact | Required value |
|---|---:|
| Approved Budget ceiling | KES 160,000,000 |
| Eligible current complete APP value | KES 130,000,000 |
| Target | 30% |
| Required planned allocation | KES 39,000,000 |
| Qualifying planned allocation | KES 50,000,000 — Youth |
| Qualifying share | 38.46% |
| Remaining allocation | KES 0 |
| County-residents measure | Not applicable for the Ministry fixture |

The KES 30,000,000 unused Budget headroom must not appear in the denominator or change the result.

## 2. Ownership and information flow

| Layer | Owns | Receives downstream | Must never do |
|---|---|---|---|
| LAW / controlled interpretation | Legal source, verified interpretation and unresolved gates | Versioned rule requirements | Present the product formula as verbatim statutory wording |
| System Setup | Effective rule Versions, categories, applicability, counting, evidence, overlap treatment and verification status | Exact immutable rule snapshots | Hard-code legal rules in UI or let users waive them with notes |
| Budget & Funding | Ceiling, line eligibility, affordability, financial reservations and commitments | Exact funding evidence | Calculate or expose the 30% APP denominator |
| Procurement Planning | Complete-APP denominator, planned target, qualifying allocation, shortfall, item designation and calculation snapshot | Item designation, County treatment and exact rule snapshots | Decide bidder entitlement or actual achievement |
| Requisitions | Immutable carry-through of the authorised Plan treatment and source lineage | Exact inherited treatment in the authorised handoff | Recalculate the target or let the department change the designation |
| Tenders / template release | Compatibility, published wording, declarations, evidence rules, response identities and mappings | Exact Published Bid Definition | Fall back to `None`, invent a generic upload or treat Planning as eligibility proof |
| Supplier portal / Bid Submission | Typed bidder declarations and evidence against the Published Bid Definition | Signed responses and evidence by stable identity | Receive or display APP/Budget arithmetic, or infer eligibility from Account/address/file presence |
| Evaluation / Award | Pass/fail reservation eligibility against the exact published rule and evidence | Evaluated category/result for award and reporting | Add or rewrite criteria after publication |
| Contract | Awarded obligations and prices | Governed contract schedules | Turn reservation evidence into a contract obligation |
| Reporting | Planned allocation from PLN; actual achievement from authoritative downstream facts | Statutory outputs | Treat planned estimates as actual achievement |

## 3. Module-by-module correction matrix

| Module | Functional and data correction | Design correction | Verification / completion evidence |
|---|---|---|---|
| LAW register | Use LAW v1.2 as the only reservation interpretation baseline. Keep AGPO planning, County-residents, candidate eligibility and actual achievement distinct. Retain unresolved current-edition/category/overlap gates. | No operational screen. Any legal-evidence surface must distinguish source wording, controlled interpretation and product behavior. | Obsolete-law-reference scan; no claim that verification is complete. |
| Departmental Needs | **No reservation function.** Do not add reservation category, target, Budget or supplier-eligibility fields. Needs remains the plain requirement source. | No reservation UI. | Schema and screen negative assertions. |
| Strategy Alignment | **No reservation function.** Strategy may remain inherited Planning context only. | No reservation UI. | Schema and screen negative assertions. |
| Budget & Funding | Remove `AnnualProcurementBudgetBasis.v1`, `get_annual_procurement_budget_basis` and any equivalent compatibility alias. Return only ceiling/affordability evidence. Budget changes may stale affordability evidence but do not change the Planning denominator unless the APP/rule itself changes. Retain REQ financial reservations as a different concept. | Remove any 30% target, qualifying share or shortfall card from Budget screens. Keep Approved, Reserved, Committed and Available funding facts. Do not label financial holds as statutory reservation categories. | KES 160m Budget versus KES 130m APP separation test; API/schema negative tests; no obsolete denominator service or UI. |
| System Setup — Procurement rules | Store/resolve exact versioned measure definitions, effective dates, qualifying categories, denominator/counting basis, item inclusion/exclusion logic, county applicability, evidence and overlap treatment. Missing/ambiguous mandatory configuration blocks the affected positive action while drafting remains available. | On rule detail, show what the rule controls, when it applies, qualifying categories, measure basis, evidence/source verification and consequence. County-residents appears as a separate rule/measure. Use structured labelled sections; do not expose raw schema or a legal-validity checkbox. | Rule-resolution tests for date, PE type, category, inclusion/exclusion, missing rule, ambiguity and overlap; source-verification audit. |
| System Setup — Tender formats | Project `supported_reservation_categories = [None, Youth, Women, Persons with disabilities]` and separate `county_residents_support` from the exact installed release. Release 1.1 remains Unavailable until all reservation variants, mappings, fixtures and exact manifest approval pass. | Update CFG-DES-05A/B: show all four base treatments, conditional County residents, truthful blockers, Youth Passed and Women/PWD/County coverage Incomplete. Show reservation declaration/evidence mapping to eligibility and its non-contract/Award-reporting disposition. Read-only only. | CFG14-AC-001–006; no hard-coded **Unreserved only**; Available cannot appear from document rendering alone. |
| Procurement Planning | Replace every Budget-denominator formula with the exact complete-APP measure. Persist the Plan Version, rule Version, per-item inclusion/exclusion reason, eligible APP value, rate, required amount, qualifying amount, remaining amount, share and result as one immutable calculation snapshot. Recalculate open Drafts and every successor; preserve approved history. Keep base category, County measure, mandatory restrictions and lotting separate. Remove highest-advantage ranking and narrative override. | U07/U11: one compact Plan-level **Reservation allocation** block with the canonical values and a details disclosure for item applicability/rule evidence. U09 purchase editor: show **Planned designation** only when required or selected; omit `None`; show County or another restriction only when it changes the item decision. Never repeat target/qualifying/shortfall on each purchase. Governance views show the same frozen Plan-level snapshot read-only. | PLN25-AC-001–006; complete-coverage and amendment tests; missing-rule and shortfall blockers; predecessor snapshot unchanged; narrow/first-viewport usability check. |
| Procurement Requisitions | Inherit `reservation_category`, separate County-residents restriction and exact rule/overlap snapshots read-only from the Active Plan Item. Include them unchanged in the authorised handoff. Recheck installed-format compatibility before authorisation; do not calculate the Plan measure or evaluate a supplier. | Reuse the existing three-task journey. Show one concise inherited treatment in Request details/Review and supporting details; no selector, target, percentage, rule editor or new task. | None/Youth/Women/PWD and County handoff tests; mutation rejection; no Planning arithmetic in REQ. **REQ v1.10 must become controlling before claiming conformance.** |
| Tender template release | Complete code-owned document wording, response rules, declarations, evidence rules, `EVG-ELIGIBILITY` mapping, Award/reporting disposition and explicit non-contract treatment for every supported base category and County overlay. Add isolated Women, PWD and County fixtures; prove overlap handling. | No operational editor. Admin inspection is owned by CFG. Supplier compositions are rendered through the released BDS profile, not designed as raw metadata screens. | All STD-TPL §13 gates; exact bundle/response/downstream digests; release 1.1 remains Candidate/Unavailable until the exact manifest is approved. |
| Tenders — preparation/publication | Snapshot the inherited treatment and rules at Tender start. Recheck exact template/category/County compatibility at start, submit, HOPF approval and AO publication authorisation. Generate the published declaration/evidence rows and mappings from the released template. A material addendum cannot change reservation treatment. Missing/unsupported/unverified treatment blocks; never downgrade to unreserved. | Existing Tenders screens only: Start Tender explains the inherited treatment in **Why this requisition is supported**; preparation shows it read-only; HOPF/AO review includes the treatment in key facts; public Tender states plainly who the Tender is reserved for and the required evidence. No category editor or extra workflow step. | Four-boundary compatibility tests; unsupported category/overlap; addendum mutation rejection; publication package/PBD digest tests; isolated None/Youth/Women/PWD/County fixtures. |
| Supplier portal / Electronic Bid Submission | Materialise only the exact Tender-specific category, separate County treatment, declaration/evidence rules and stable mappings. Account status, organisation address, reusable evidence or upload success never establishes entitlement. Preserve the evaluated result for Award/reporting and exclude eligibility evidence from contract obligations. Keep all APP/Budget aggregate values out of schema, APIs, signed package and handoffs. | No new screen or task. In **Company, declarations and tender security**, render the category-specific declaration/evidence and a separate County section only when applicable. Tender overview/workspace may state the published reservation plainly. Review shows completion/issues, not internal Planning math. | BDS06-AC/IMP-001–005; negative schema/output scan; no-inference tests; existing Draft preservation when Start/revalidation fails; no silent `None` fallback. **BDS v0.6 must become controlling before claiming conformance.** |
| Evaluation / Award | Consume published stable identities. Record pass/fail for each applicable reservation declaration/evidence requirement under `EVG-ELIGIBILITY`; retain reason and evaluator identity. Preserve category, County treatment and result for award/reporting. Do not implement bidder ranking from the Planning designation. | When this module is designed, place reservation eligibility inside the ordinary eligibility review with the published requirement, submitted evidence, result and reason. Do not create a criterion builder or expose Planning percentages. | Published-criterion immutability, evidence/result audit, County/address non-inference and award-handoff tests. This is a downstream contract until the module is specified/implemented. |
| Contract Management | Consume only accepted contract destinations. Reservation declaration/evidence is explicitly not carried into contractual obligations. | No reservation-evidence contract clause/card. A governed audit link may show award classification outside contract obligations. | Projection test proving explicit N/A/non-contract treatment. |
| Statutory reporting | Keep planned allocation and actual achievement as separate measures. Count authoritative actual procurements/awards under verified category and overlap rules; calculate County separately. | Future reporting must label **Planned allocation** and **Actual achievement** distinctly, with period, denominator and source. | Reconciliation to Planning snapshots and actual Award facts; no estimate-as-actual fallback. |

## 4. Claude Design work package

Claude Design should receive KT-STD-001 v1.7 §2 plus the complete relevant static-design section and closed fixture data for each affected module. It must not be asked to infer behavior from this handoff.

### 4.1 Screens to change

1. **Planning — Annual Plan preparation and governance**
   - Replace the old Budget-based reservation summary with the canonical Plan-level block.
   - Keep it visually compact: result and remaining amount first; basis and rule evidence under structured details.
   - Keep the purchase editor simple; the user selects the planned designation, not a legal formula.
2. **System Setup — Procurement rules**
   - Make the effect of the rule understandable: what it controls, who/what it applies to, the calculation basis, source status and what is blocked.
   - Keep County-residents visibly separate from the base AGPO categories.
3. **System Setup — Tender formats**
   - Implement the approved CFG v0.14 list/detail correction and truthful Unavailable state.
4. **Requisition, Tenders and Bidder Workspace**
   - Amend existing screens only. Add concise inherited/published treatment and the exact supplier declaration/evidence composition; do not add another wizard, task, tab or dashboard.

### 4.2 Screens not to create or expand

- No reservation screen in Departmental Needs, Strategy or Budget.
- No generic preference/reservation workbench.
- No rule, template, schema or evaluation builder.
- No Plan arithmetic on purchase, Requisition, Tender or bidder screens.
- No candidate-entitlement decision in Planning.
- No automatic County eligibility from address.

### 4.3 Design acceptance

A representative Planner must be able to answer, without coaching:

1. What is the current Plan-level requirement?
2. Is it met; if not, what remains?
3. Which purchases count and why?
4. What one action can the Planner take?

A supplier must be able to answer:

1. Is this Tender reserved and for whom?
2. What declaration/evidence must I provide?
3. What remains incomplete?

No routine user should need to understand rule IDs, manifest digests, denominator services or overlap algorithms.

## 5. Claude Code work package

### 5.1 Recommended implementation order

| Sequence | Work | Exit condition |
|---:|---|---|
| 0 | Lock the baselines: approve or otherwise make controlling REQ v1.10, TPR v0.9, STD-TPL v0.7 and BDS v0.6; update their stale owner references to CFG v0.14, PLN v1.25, BUD v1.10 and LAW v1.2. | One non-conflicting dependency matrix. |
| 1 | Repository inventory: locate every old Budget-denominator formula, 30% field/service, **Unreserved only** literal, reservation enum, preference override, handoff field and affected UI/test fixture. | Reviewed impact list; no code change yet. |
| 2 | Shared rule/configuration and types: exact categories, separate County flag/rule snapshot, applicability/overlap results, installed-format projection. | Resolver and schema contract tests pass. |
| 3 | Budget cleanup and Planning owner implementation. | Formula/migration/unit/concurrency tests pass; canonical fixture reproduces exactly. |
| 4 | Requisition and Tender handoffs, template release pack and release gating. | End-to-end immutable treatment and compatibility tests pass. |
| 5 | Bidder runtime and downstream evaluation/Award interface. | No-inference, signed-package, mapping and non-contract tests pass. |
| 6 | UI corrections and visual verification using approved artboards. | Semantic component tests plus browser structural/interaction/visual tests pass at the module gate. |
| 7 | Migration, seed replacement and full affected-module regression. | No contradictory runtime path or fixture remains; release evidence signed. |

### 5.2 Migration and cutover rules

- Preserve every approved/Active historical Plan Version and its evidence. Do not rewrite signed or acted-upon facts.
- Recalculate open Draft/candidate Plans against the current complete item set and exact effective rule; mark stale calculations for explicit refresh rather than silently accepting them.
- A corrective successor Plan gets a new calculation snapshot. The predecessor remains readable.
- Demo/test fixtures may be rebuilt deterministically. Genuine evidence-bearing records require a governed migration/successor path.
- Remove obsolete APIs, fields and UI projections only after a repository reference scan. Do not retain a compatibility alias that can revive the Budget-denominator interpretation.
- Do not make template release 1.1 Available merely to unblock tests. Tests may use an unmistakable fixture release; production availability requires all release gates and exact manifest approval.

## 6. Minimum focused test matrix

| Area | Required cases |
|---|---|
| Planning arithmetic | 130m × 30% = 39m; 50m / 130m = 38.46%; Budget 160m does not affect result; exact decimal arithmetic only |
| Complete coverage | Every item included/excluded with reason; hidden/omitted item rejected; partial qualifying value uses separate item in this MVP |
| Plan succession | Draft recalculation; approved successor recalculation; predecessor unchanged; rule-Version change stales current calculation |
| Categories | `None`, Youth, Women, Persons with disabilities; unknown value rejected |
| County | Non-county N/A; applicable county with verified rule; missing rule; missing overlap treatment; address never proves eligibility |
| Blocking | Missing mandatory rule, incomplete basis and shortfall block the affected positive action; Draft save remains available |
| Budget boundary | No denominator service/field/UI; ceiling and affordability still enforced |
| Handoffs | PLN → REQ → TPR → Published Bid Definition preserves category, County treatment and exact snapshots without aggregate Planning values |
| Template | All category declarations/evidence/mappings; unknown renderer/rule blocked; Women/PWD/County isolated fixtures |
| Tender | Compatibility at start/submit/approve/publication; material addendum cannot change treatment; no downgrade to `None` |
| Bidder | Exact declaration/evidence; no Account/address/upload inference; no APP/Budget math; failed revalidation preserves existing Draft |
| Evaluation/contract | Reservation evidence maps to `EVG-ELIGIBILITY`; result preserved for Award/reporting; evidence is not a contract obligation |
| UI | Aggregate block appears only at Plan level; no **Unreserved only**; no duplicate tasks/screens; 390 px and desktop; keyboard/focus/contrast |

Use semantic component/UI-contract tests for each change. Use browser structural, interaction and visual-regression tests at module and release gates; do not assert literal DOM equality.

## 7. Definition of done

The reservation correction is complete only when:

1. all controlling documents and code use the same ownership and formula;
2. the obsolete Budget-denominator service, data and UI are absent;
3. the complete-APP calculation and history behavior pass the canonical fixture;
4. every downstream handoff preserves the exact treatment without carrying Plan arithmetic;
5. the template release proves every supported category and County path and receives exact-manifest approval;
6. the bidder supplies published evidence and Evaluation—not Planning or Account—decides eligibility;
7. Contract excludes reservation evidence while Award/reporting retain the governed result;
8. affected artboards pass the simplicity, directness, completeness and responsive-layout tests; and
9. focused cross-module tests and the release-gate browser suite pass with no contradictory legacy path.

## 8. Immediate blockers and non-blockers

| Item | Treatment |
|---|---|
| LAW v1.2, BUD v1.10, PLN v1.25, CFG v0.14 | Approved implementation baselines |
| REQ v1.10, TPR v0.9, STD-TPL v0.7, BDS v0.6 | Proposed; must be made controlling before final conformance is claimed |
| Template release 1.1 | Candidate/Unavailable; Youth fixture alone is insufficient |
| Women, PWD and County template fixtures | Required release blockers, not optional enhancements |
| Current-law/category/overlap verification | Production gate; requirements approval does not close it |
| Departmental Needs, Strategy, Budget workflow stages | No new reservation screens or approval stages required |
| Works/Services reservation rendering | Outside the current IT-equipment product; requires separately curated product releases |

