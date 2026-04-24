Here is the **master restructure prompt**. Use it once at the start of the restructuring session, then run the ticket pack one ticket at a time.

You are restructuring the KenTender codebase to align with the locked architecture v3.

This is a controlled architecture alignment task, not a redesign.

Your goals are:

1. preserve working Strategy and Budget modules
2. add missing first-class apps required by architecture v3
3. tighten internal boundaries inside kentender_procurement
4. update repo/docs/scripts so future module implementation does not drift
5. prepare a clean home for Demand Intake and Approval (DIA)

The final approved app set is:

* kentender_core
* kentender_strategy
* kentender_budget
* kentender_procurement
* kentender_suppliers
* kentender_governance
* kentender_compliance
* kentender_stores
* kentender_assets
* kentender_integrations
* kentender_transparency

Critical architecture rules:

* Do NOT rename existing working apps unless explicitly instructed
* Do NOT delete or break working Strategy/Budget code
* Do NOT split kentender_procurement into multiple apps
* Do NOT move business logic casually during app creation
* Do NOT invent any new apps beyond the approved list
* Do NOT introduce upstream dependency violations
* Business logic must live in services/, not DocType controllers or UI handlers
* Workspace-first UX remains the platform rule
* Governance-first module design remains mandatory
* Every future module must include:

  * pre-PRD
  * full PRD
  * strict domain model tables
  * governance/state model
  * tabular user/role/permission matrices
  * UI specification
  * seed data specification
  * smoke contracts

Architecture intent:

* kentender_core = shared platform controls
* kentender_strategy = strategic hierarchy
* kentender_budget = budget control and reservations
* kentender_procurement = transactional procurement chain, including:

  * Demand Intake and Approval
  * Procurement Planning
  * Tendering / Solicitation
  * Bid Submission & Opening
  * Evaluation & Award
  * Contract Management
  * Inspection & Acceptance
* kentender_suppliers = supplier lifecycle ownership
* kentender_transparency = public/read-only publication ownership

Dependency direction must remain controlled:

* core → strategy → budget → procurement → stores → assets
* suppliers, governance, compliance, integrations, transparency may consume published interfaces as appropriate but must not create upstream coupling or own the wrong business rules

Restructuring approach:

* scaffold first
* migrate later only where clearly required
* preserve working behavior
* prefer documentation and boundary clarification over risky logic movement
* if something is unclear, state the ambiguity instead of guessing

Expected deliverables from the restructuring effort:

1. missing apps scaffolded:

   * kentender_suppliers
   * kentender_transparency
2. repo scripts/install order/symlinks updated
3. architecture docs updated to v3
4. internal subdomain structure created inside kentender_procurement
5. supplier and transparency boundaries clarified
6. no regressions in Strategy/Budget
7. DIA internal implementation home prepared
8. final review confirming readiness for DIA implementation

For every restructure ticket I give you:

* execute only that ticket’s scope
* do not jump ahead
* do not redesign unrelated code
* after completing it, always return:

  * completed
  * not completed
  * assumptions made
  * files changed
  * risks remaining

Do not start implementing DIA business logic until explicitly instructed after the restructure is complete.


Use these **one at a time**.

---

# KenTender Architecture Restructure — Cursor Prompt Pack

## Global instruction for every restructuring ticket

Use the locked KenTender architecture v3 as the source of truth.

Goals:

* align the repo/app structure to the updated architecture
* preserve working Strategy and Budget modules
* avoid breaking existing bench/app installation
* keep dependency direction strict
* do not migrate business logic casually during app creation

Rules:

1. Do not delete or rename existing apps unless explicitly instructed.
2. Do not move working Strategy or Budget logic into new apps.
3. Do not invent new apps beyond the approved architecture.
4. Keep bench/install order and symlink strategy clean.
5. If a change is risky, prefer scaffolding first and migration later.
6. After each ticket, explicitly list:

   * completed
   * not completed
   * assumptions made
   * files changed
   * risks remaining

---

# Phase R0 — Architecture alignment review

## R0.1 — Review current repo against architecture v3

Review the current KenTender repo against architecture v3.

Tasks:

1. Inspect current apps and structure
2. Compare against required app set:

* kentender_core
* kentender_strategy
* kentender_budget
* kentender_procurement
* kentender_suppliers
* kentender_governance
* kentender_compliance
* kentender_stores
* kentender_assets
* kentender_integrations
* kentender_transparency

3. Identify:

* missing apps
* app naming mismatches
* dependency violations
* current working modules that must be preserved
* documentation that needs update

Do NOT change code yet.

Return:

1. current app inventory
2. gaps vs architecture v3
3. risks in restructuring
4. proposed safe order of change

---

# Phase R1 — Create missing apps only

## R1.1 — Scaffold new apps: suppliers and transparency

Create the missing apps required by architecture v3:

1. kentender_suppliers
2. kentender_transparency

Requirements:

* scaffold them as proper Frappe apps
* add them inside the monorepo structure consistent with the existing Kentender repo layout
* do not rename existing apps
* do not move logic into them yet
* do not add business DocTypes yet except minimal placeholder package structure if needed

Required internal structure for each app:

* doctype/
* services/
* api/
* tests/
* utils/

Acceptance criteria:

* both apps exist
* both apps are importable
* both apps fit the monorepo pattern
* no existing app broken

---

## R1.2 — Wire bench symlinks and install order

Update the monorepo/bench structure to include the new apps safely.

Tasks:

1. Add/update symlink commands for:

* kentender_suppliers
* kentender_transparency

2. Update install order documentation / scripts

Recommended install order:

* kentender_core
* kentender_strategy
* kentender_budget
* kentender_procurement
* kentender_suppliers
* kentender_governance
* kentender_compliance
* kentender_stores
* kentender_assets
* kentender_integrations
* kentender_transparency

3. Update:

* sites/apps.txt guidance
* Makefile targets
* helper scripts if present

Rules:

* do not break existing install order for current working apps
* keep transparency near the end since it is mostly downstream/read-only

Acceptance criteria:

* repo scripts/docs include the new apps
* install order is explicit and correct

---

# Phase R2 — Update architecture docs in repo

## R2.1 — Replace architecture docs with v3 versions

Update the repo architecture documentation to reflect architecture v3.

Update or create the authoritative docs for:

1. global architecture
2. architecture rules
3. monorepo structure

Must include:

* final app set including kentender_suppliers and kentender_transparency
* updated lifecycle:
  Strategy → Budget → Demand Intake and Approval → Procurement Planning → Supplier Management → Tendering / Solicitation → Bid Submission & Opening → Evaluation & Award → Contract Management → Contract Execution → Inspection & Acceptance → Stores / Assets → Reporting / Audit
* governance-first rule
* tabular role/permission matrix requirement for every module
* workspace-first UX rule
* strict service-layer rule

Do not leave conflicting older wording in place if this causes confusion.
If old docs are retained, clearly mark them superseded.

Acceptance criteria:

* repo docs reflect the new architecture clearly
* no ambiguity about app set or module order

---

# Phase R3 — Tighten procurement app internal structure

## R3.1 — Create internal subdomain structure inside kentender_procurement

Restructure kentender_procurement internally to reflect the approved subdomains, without moving business logic recklessly.

Create or normalize internal module folders for:

* demand_intake
* procurement_planning
* tendering
* bid_submission_opening (or split opening later if needed)
* evaluation_award
* contract_management
* inspection_acceptance

For each subdomain, establish a clear structure pattern such as:

* doctype/
* services/
* api/
* tests/
* utils/

Rules:

* do not break existing working Strategy/Budget integrations
* do not migrate large working code unless necessary
* create the structure so future implementation lands in the right place
* document current placeholders clearly

Acceptance criteria:

* kentender_procurement has clear internal subdomain boundaries
* future DIA implementation has a correct home

---

## R3.2 — Reserve supplier-owned boundaries

Update procurement app boundaries so supplier-related ownership is clearly reserved for kentender_suppliers.

Tasks:

1. Inspect existing procurement code/docs for supplier ownership leakage
2. Mark or refactor only the minimal boundaries needed so that:

* procurement references suppliers
* procurement does not own supplier lifecycle

Do NOT implement supplier module business logic yet.
Do NOT do large migrations yet.
This is primarily a boundary clarification pass.

Acceptance criteria:

* procurement app no longer implies it owns supplier registration/onboarding/performance/sanctions
* architecture and code comments align

---

## R3.3 — Reserve transparency-owned boundaries

Update architecture/code boundaries so publication and public transparency are clearly reserved for kentender_transparency.

Tasks:

1. Inspect existing code/docs for publication/transparency ownership leakage
2. Ensure:

* procurement owns transaction records
* transparency will own public-facing publication and read-only disclosure workflows

Do NOT implement transparency business logic yet.
Do NOT move real code unless necessary.

Acceptance criteria:

* no ambiguity about public publication ownership

---

# Phase R4 — Dependency and service boundary enforcement

## R4.1 — Validate dependency direction after restructure

Validate and document dependency direction after the architecture restructure.

Required allowed direction:

* core → strategy → budget → procurement → stores → assets

Side apps:

* suppliers depends on core and may be referenced by procurement via interfaces/services
* governance/compliance consume published interfaces
* integrations consume published interfaces
* transparency is downstream/read-only publishing

Tasks:

1. inspect imports and references where relevant
2. identify illegal deep imports
3. document any current violations
4. apply only low-risk corrections now; defer major refactors if needed, but document them clearly

Acceptance criteria:

* dependency map documented
* obvious illegal couplings identified or corrected

---

## R4.2 — Enforce service-layer architecture skeleton in new apps

Establish service-layer architecture skeletons for the newly added apps:

* kentender_suppliers
* kentender_transparency

Create minimal placeholder modules/files for:

* services/
* api/
* tests/
* utils/

Add app-level guidance/readme/comments if needed stating:

* business logic belongs in services
* API endpoints belong in api
* DocTypes remain thin

Do not implement full business flows yet.
This is a structural setup task.

Acceptance criteria:

* new apps follow the same architecture pattern as the rest of KenTender

---

# Phase R5 — Protect existing working modules

## R5.1 — Verify Strategy and Budget still work after restructure

After architecture restructure, verify that the existing working modules still function:

1. Strategy

* workspace loads
* landing page loads
* builder route loads

2. Budget

* workspace loads
* landing page loads
* builder route loads
* approval flow still reachable

Tasks:

* perform a code-level review and lightweight validation
* fix only restructure-induced breakage
* do not redesign Strategy or Budget

Acceptance criteria:

* no regressions introduced by app/repo restructure

---

## R5.2 — Update root docs and developer instructions

Update root developer guidance so future work follows the new architecture.

Update:

* AGENTS.md or equivalent
* scripts/README if present
* architecture references in docs
* any Windsurf/Cursor guidance files if present

Must explicitly state:

* final app set
* monorepo rules
* service-layer rules
* workspace-first UI rules
* governance-first module rule
* each module must include:

  * pre-PRD
  * PRD
  * strict domain model
  * governance/state model
  * tabular user/role/permission matrices
  * UI spec
  * seed data
  * smoke contracts

Acceptance criteria:

* future AI-assisted implementation is less likely to drift

---

# Phase R6 — DIA readiness prep

## R6.1 — Prepare kentender_procurement for DIA implementation

Prepare kentender_procurement specifically for Demand Intake and Approval implementation.

Tasks:

1. create the DIA internal home (for example within demand_intake/)
2. establish placeholder directories/files for:

* doctype/
* services/
* api/
* tests/
* seeds/ if your structure supports submodule seed grouping

3. add minimal comments/readme indicating this area owns:

* demand capture
* classification
* approval
* budget reservation handoff
* planning-ready output

Do NOT implement DIA logic yet.
This is structure-only preparation.

Acceptance criteria:

* DIA has a clear home in kentender_procurement
* there is no ambiguity where the next module will be built

---

# Phase R7 — Review and signoff

## R7.1 — Final restructure review

Review the architecture restructure before starting DIA implementation.

Do NOT change code yet.

Check:

1. Are all required apps present?
2. Are any app renames still necessary?
3. Are the new suppliers/transparency apps wired correctly?
4. Is kentender_procurement internally structured well enough for DIA and later modules?
5. Do the docs accurately reflect the final architecture?
6. Is there any remaining ambiguity that would cause Cursor to drift during DIA implementation?

Return:

* complete
* missing
* risky
* must-fix before starting DIA build

---

# Recommended execution order

Run these in order:

```text
R0.1
R1.1
R1.2
R2.1
R3.1
R3.2
R3.3
R4.1
R4.2
R5.1
R5.2
R6.1
R7.1
```

---

# Non-negotiable review gates

Do **not** start DIA implementation until all of these are true:

* [ ] `kentender_suppliers` exists
* [ ] `kentender_transparency` exists
* [ ] architecture docs updated to v3
* [ ] procurement internal subdomains established
* [ ] existing Strategy/Budget not broken
* [ ] developer guidance updated
* [ ] DIA internal home prepared
* [ ] final restructure review done

---

# Practical advice

Tell Cursor explicitly, each time:

* this is a **restructure**, not a redesign
* preserve working modules
* scaffold first, migrate later
* document ambiguity instead of guessing

If you want, I can next produce a **single-message “master restructure prompt”** for Cursor to use as the umbrella instruction before these tickets.
