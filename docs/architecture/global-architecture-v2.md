# Global Architecture Document v2

**1\. Purpose**

This document defines the global application architecture for KenTender so that module implementation happens within stable boundaries and does not drift into sprawl.

It exists to ensure:

- clear app responsibilities
- controlled dependency direction
- reusable shared services
- consistent implementation patterns
- safe module-by-module delivery

This architecture updates and tightens the earlier Wave 0 foundation approach and aligns with the product scope and lifecycle defined in the PRD .

**2\. Architectural goals**

The architecture must satisfy these goals:

1.  **Business-chain integrity**  
    Strategy, budget, procurement, contract, acceptance, stores, and assets must follow a controlled downstream chain.
2.  **Modular isolation without fragmentation**  
    Apps must be separate enough to prevent sprawl, but not split so aggressively that tightly coupled workflows become harder to maintain.
3.  **Cross-cutting governance**  
    Audit, exceptions, numbering, scope, permissions, file controls, and workflow guards must be centralized.
4.  **Workspace-first UX**  
    Modules must be implemented as guided workspaces and queues, not raw DocType forms.
5.  **Module-by-module delivery**  
    Each module must be independently implementable, testable, and freezeable before the next begins.

**3\. System backbone**

KenTender follows this controlled business chain:

Strategy → Budget → Requisition → Planning → Tender → Bid → Opening → Evaluation → Award → Contract → Inspection/Acceptance → Stores/Assets → Reporting/Audit

This chain must not be bypassed except through a formal exception path with approval and audit trace.

**4\. App landscape**

KenTender is implemented as a **multi-app Frappe platform**.

**4.1 App set**

- kentender_core
- kentender_strategy
- kentender_budget
- kentender_procurement
- kentender_governance
- kentender_compliance
- kentender_stores
- kentender_assets
- kentender_integrations

This is consistent with the earlier Wave 0 app foundation proposal .

**5\. App responsibilities**

**5.1 kentender_core**

The shared platform foundation.

Owns:

- Procuring Entity
- Department / Business Unit
- shared master data
- business ID / numbering service
- entity scope helpers
- assignment-based access helpers
- permission query helpers
- workflow guard framework
- controlled business action pattern
- audit event framework
- exception record
- typed attachment model
- sensitivity classification
- protected file access
- notification abstraction

Does not own:

- strategy hierarchy
- budget logic
- procurement business workflows

**5.2 kentender_strategy**

The strategic planning domain.

Owns:

- Strategic Plan
- Program
- Sub-program
- Output Indicator
- Performance Target

Exports:

- active strategy selector APIs
- strategy validation helpers

Does not own:

- budget control
- requisition workflows
- procurement planning logic

**5.3 kentender_budget**

The budget control domain.

Owns:

- Budget
- Budget Line
- Budget allocation
- reservation / commitment / release logic
- budget ledger and derived balances

Exports:

- budget availability checks
- reserve / commit / release services

Does not own:

- procurement approvals
- plan consolidation
- tender workflows

**5.4 kentender_procurement**

The transactional procurement lifecycle domain.

Owns:

- Purchase Requisition
- Procurement Plan
- Procurement Plan Item
- Procurement Templates / Template Sets
- Tender
- Bid Submission
- Bid Opening
- Evaluation
- Award
- Contract
- Inspection / Acceptance
- Complaints / disputes

This app is intentionally broad because these objects form one tightly coupled transactional chain.

Does not own:

- global audit primitives
- shared numbering framework
- entity scope framework

**5.5 kentender_governance**

Cross-cutting governance constructs that are business-facing rather than purely infrastructural.

Owns:

- committee/session governance views
- oversight views
- governance dashboards
- governed override processes that are broader than one module

Does not duplicate:

- audit infrastructure from core
- transactional domain records from business apps

**5.6 kentender_compliance**

Jurisdictional and policy overlays.

Owns:

- threshold rules
- procurement method enforcement overlays
- anti-fragmentation policies
- configurable regulatory rule packs
- compliance reporting support

This app should evaluate policy, not become the home of business transactions.

**5.7 kentender_stores**

Post-acceptance stores operations.

Owns:

- stores receipt
- inventory intake from accepted procurement
- store issue / movement
- stock-side handoff from acceptance

**5.8 kentender_assets**

Post-acceptance asset lifecycle.

Owns:

- asset creation from accepted items
- asset tagging
- assignment
- lifecycle controls
- disposal / retirement hooks

**5.9 kentender_integrations**

External interfaces.

Owns:

- finance/accounting interfaces
- external identity integrations
- publication / portal interfaces
- verification and external registry interfaces
- document gateway integrations if needed later

**6\. Dependency architecture**

**6.1 Allowed dependency direction**

kentender_core

↓

kentender_strategy

↓

kentender_budget

↓

kentender_procurement

↓

kentender_stores

↓

kentender_assets

Cross-cutting side apps:

- kentender_governance may depend on kentender_core and consume published interfaces from domain apps
- kentender_compliance may depend on kentender_core and evaluate policy for strategy/budget/procurement
- kentender_integrations may depend on kentender_core and published service interfaces from other apps

**6.2 Forbidden dependency rules**

These are hard rules.

- kentender_core must not depend on any business app
- kentender_strategy must not depend on budget or procurement
- kentender_budget must not depend on procurement
- kentender_procurement must not push dependencies upstream
- kentender_stores must not influence upstream planning logic
- kentender_assets must not influence procurement planning logic
- kentender_integrations must not own business rules

**7\. Internal app structure**

Every app must use the same layout:

doctype/

services/

api/

tests/

utils/

**Responsibility rules**

- doctype/ = persistence model + thin validation
- services/ = business actions and orchestration
- api/ = explicit API endpoints
- tests/ = unit/integration/smoke tests
- utils/ = lightweight helpers only

Business workflows must live in services/, not be buried in DocType controllers.

This is consistent with the service-structure direction from Wave 0 .

**8\. Cross-cutting architectural rules**

**8.1 Business IDs**

All major business records must use shared business ID generation from kentender_core.

**8.2 Entity scope**

Most business records must carry procuring_entity.

**8.3 Append-only audit**

Critical actions must generate structured audit events.

**8.4 Exception-based bypass**

Any lawful bypass path must use a formal exception record.

**8.5 Typed attachments**

Critical process documents must use typed attachment records, not only generic files.

**8.6 Workflow guards**

High-risk transitions must run through a workflow guard layer.

**8.7 Controlled business actions**

Critical actions such as submit, approve, publish, open, finalize must use explicit service-layer business actions.

**9\. Global UI architecture**

**9.1 Workspace-first rule**

Every module must have:

- one landing workspace
- one primary work queue or list
- one guided builder/editor where applicable

**9.2 Form-second rule**

Raw DocType forms must not be the default UX for complex business flows.

**9.3 Role-oriented navigation**

Navigation must be organized by role and workflow, not raw DocType exposure.

**9.4 Visible workflow rule**

The user must always be able to answer:

- where am I?
- what is next?
- what is missing?
- what can I act on?

This rule directly responds to the earlier UX failures you identified.

**10\. Global workflow architecture**

**10.1 Aggregate-level workflows**

Each major business aggregate gets one controlling workflow.

Examples:

- Strategic Plan
- Budget
- Purchase Requisition
- Procurement Plan
- Tender
- Award
- Contract

**10.2 No mega cross-app workflows**

Cross-app transitions should happen through:

- service calls
- explicit actions
- state propagation
- audit logging

Not through one giant workflow definition spanning multiple apps.

**11\. Global API architecture**

Each app must expose:

1.  **selector APIs** for downstream dropdowns and lookups
2.  **CRUD APIs** for its owned entities where needed
3.  **business action APIs** for critical controlled transitions

**Example pattern**

**Strategy**

- active programs
- active sub-programs
- active indicators
- active targets

**Budget**

- budget availability
- reserve funds
- commit funds
- release funds

**Procurement**

- create requisition
- submit requisition
- add PR to plan
- create tender from plan item
- submit tender
- finalize evaluation
- approve award

**API response standard**

All apps should use a consistent envelope:

Success:

{

"ok": true,

"data": {},

"message": "Success"

}

Error:

{

"ok": false,

"error_code": "ERROR_CODE",

"message": "Human-readable explanation"

}

**12\. Data governance architecture**

**12.1 Upstream ownership**

Each upstream domain owns its source-of-truth data:

- Strategy owns hierarchy
- Budget owns financial control state
- Procurement owns transactional execution

**12.2 Downstream consumption only**

Downstream apps consume upstream approved/active records via selectors and services. They do not recreate source data via free text.

**12.3 Versioning principle**

Where versions matter:

- new versions are created
- existing transactions remain linked to the version used at creation time

**13\. Security and access architecture**

**13.1 Role alone is not enough**

Use a combination of:

- role
- entity scope
- ownership
- assignment
- workflow state
- sensitivity classification

**13.2 Sensitive document access**

Sensitive files must go through protected access services with allow/deny audit hooks.

**13.3 Separation of duties**

Conflict-of-duty rules must be centrally stored and reusable across modules.

**14\. Delivery architecture**

KenTender will be delivered **module by module**, not breadth-first.

**Delivery rule**

A module is not complete until:

- its UX is usable
- its workflow is visible
- its validation is strict
- its save/reload path is stable
- its selector/API contract works
- its smoke tests pass

This aligns with the module-by-module MVP-gate approach you have now adopted.

**15\. Global implementation order**

**Foundation**

1.  kentender_core
2.  kentender_strategy

**Control layer**

1.  kentender_budget

**Transaction chain**

1.  Requisition
2.  Planning
3.  Templates
4.  Tender
5.  Bid Submission
6.  Opening
7.  Evaluation
8.  Award
9.  Contract
10. Inspection / Acceptance

**Downstream operations**

1.  Stores
2.  Assets

**Overlays and interfaces**

1.  Governance extensions
2.  Compliance overlays
3.  Integrations

**16\. Repository structure**

apps/

kentender_core/

kentender_strategy/

kentender_budget/

kentender_procurement/

kentender_governance/

kentender_compliance/

kentender_stores/

kentender_assets/

kentender_integrations/

docs/

architecture/

delivery/

prompts/

test-contracts/

module-prds/

This extends the earlier docs folder idea from Wave 0 .

**17\. Architecture anti-patterns to avoid**

**17.1 Monolith-by-accident**

Everything in one app because it feels faster.

**17.2 Hyper-fragmentation**

Too many small apps for tightly coupled procurement steps.

**17.3 UI-through-raw-forms**

Default ERPNext forms becoming the primary UX.

**17.4 Hidden coupling**

One app directly importing deep internals of another.

**17.5 Logic in controllers**

Critical business actions living only inside DocType methods.

**17.6 AI-generated architecture drift**

Implementation introducing new states, layers, or dependencies not in the architecture.

**18\. Architecture decision summary**

This architecture deliberately chooses:

- multi-app over monolith
- controlled boundaries over loose modularity
- one transactional procurement app over many fragmented procurement apps
- centralized cross-cutting infrastructure in core
- workspace-first UX
- module-gated delivery

That is the right tradeoff for your current failure mode.

**App Responsibility Matrix**

**1\. Matrix**

| **App** | **Owns** | **Exports** | **Must Not Own** |
| --- | --- | --- | --- |
| kentender_core | shared master data, scope, numbering, audit, exceptions, file controls, notification abstractions | shared services/utilities | strategy, budget, procurement business workflows |
| kentender_strategy | strategic plans, programs, sub-programs, indicators, targets | active hierarchy selectors, strategy validation helpers | budget or procurement logic |
| kentender_budget | budgets, lines, reservations, commitments, releases | budget availability and control services | procurement approvals, tender/planning logic |
| kentender_procurement | requisition through acceptance transaction chain | transactional business actions | shared audit/numbering infrastructure |
| kentender_governance | oversight-facing governance constructs | governance dashboards/rules views | duplicate core infrastructure or transaction ownership |
| kentender_compliance | threshold rules, policy overlays, anti-fragmentation checks | compliance rule evaluation | business transaction storage |
| kentender_stores | store receipt and inventory intake | downstream stores handoff | planning/tender logic |
| kentender_assets | asset registration and lifecycle | downstream asset handoff | procurement planning logic |
| kentender_integrations | external system connectors | interface services | core business rules |

**2\. Dependency matrix**

|     |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **From \\ To** | **core** | **strategy** | **budget** | **procurement** | **governance** | **compliance** | **stores** | **assets** | **integrations** |
| core | —   | No  | No  | No  | No  | No  | No  | No  | No  |
| strategy | Yes | —   | No  | No  | No  | No  | No  | No  | No  |
| budget | Yes | Yes | —   | No  | No  | No  | No  | No  | No  |
| procurement | Yes | Yes | Yes | —   | No direct deep coupling | No direct deep coupling | No  | No  | No  |
| governance | Yes | Interface only | Interface only | Interface only | —   | Optional | No  | No  | No  |
| compliance | Yes | Interface only | Interface only | Interface only | Optional | —   | No  | No  | No  |
| stores | Yes | No  | Via procurement/budget interface only | Yes | No  | Optional | —   | No  |     |
| assets | Yes | No  | Via procurement/budget interface only | Yes | No  | Optional | Optional | —   |     |
| integrations | Yes | Interface only | Interface only | Interface only | Interface only | Interface only | Interface only | Interface only | —   |

**3\. Developer use rules**

When implementing a module, developers and AI tools must ask:

1.  Which app owns this object?
2.  Is this business logic local to the app, or should it call a shared service?
3.  Am I importing across an app boundary illegally?
4.  Should this be a selector API, business action service, or DocType method?
5.  Am I pushing workflow or UX responsibility into the wrong layer?

**4\. Practical next step**

This should now be turned into two repo docs:

- docs/architecture/global-architecture-v2.md
- docs/architecture/app-responsibility-matrix.md

After that, the next strong step is to produce a **Global Delivery Order Matrix** aligned to this architecture and to your new module-by-module PRD method.

Global instruction

\+ Architecture rules

\+ UX rules

\+ Phase prompt