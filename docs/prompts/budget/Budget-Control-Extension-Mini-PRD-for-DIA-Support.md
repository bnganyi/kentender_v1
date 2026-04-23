Budget Control Extension — Mini-PRD for DIA Support

**1\. Purpose**

This extension makes the Budget module capable of serving as the **financial control authority** for Demand Intake and Approval.

It must support:

-   budget-line-based strategy derivation
-   budget sufficiency checks
-   reservation creation
-   reservation release
-   clean service-layer APIs for DIA

It must **not** yet become:

-   full commitment accounting
-   GL integration
-   payment control
-   multi-period forecasting
-   reporting overhaul

**2\. Why this is needed**

DIA assumes:

-   a user selects a **Budget Line**
-   strategy linkage can be derived from it
-   finance approval can validate available funds
-   approval can create a reservation
-   rejection/cancellation can release it

If Budget cannot do those things natively, then DIA will either:

-   duplicate Budget logic, or
-   fake financial control

Both are unacceptable.

**3\. Scope**

**In scope**

-   strengthen Budget Line
-   add Budget Reservation
-   add Budget service APIs
-   define reservation lifecycle
-   define availability calculation

**Out of scope**

-   budget revisions
-   approval redesign for Budget
-   encumbrance accounting
-   purchase order commitment logic
-   invoice/payment logic
-   variance reports
-   accounting integration

**4\. Core design decision**

**Budget Line becomes the operational anchor**

For DIA, the user should select:

Budget Line

From that, the system should derive:

-   Budget
-   Entity
-   Funding source
-   Strategic Plan
-   Program
-   Sub-program
-   Output Indicator
-   Performance Target

That keeps DIA usable and traceable.

**5\. Minimal entities**

You need only **two things**:

**A. Extend Budget Line**

**B. Add Budget Reservation**

That is enough.

**6\. Budget Line — Required extension**

**6.1 Purpose**

Represents the smallest budget-controlled unit against which demand can be validated and reserved.

**6.2 Required fields**

| **Field Name** | **Type** | **Required** | **Purpose** |
| --- | --- | --- | --- |
| name | ID / autoname | ✓ | internal key |
| budget\_line\_code | Data | ✓ | business-readable code |
| budget\_line\_name | Data | ✓ | label |
| budget | Link → Budget | ✓ | parent budget |
| procuring\_entity | Link | ✓ | scope control |
| fiscal\_year | Int | ✓ | control period |
| amount\_allocated | Currency | ✓ | approved amount |
| amount\_reserved | Currency | ✓ | running reserved total |
| amount\_consumed | Currency | ✗ | future downstream use |
| amount\_available | Currency / derived | ✓ | derived available balance |
| currency | Link → Currency | ✓ | financial unit |
| funding\_source | Link / Data | ✗ | source traceability |
| strategic\_plan | Link | ✓ | derived or explicit |
| program | Link | ✓ | derived or explicit |
| sub\_program | Link | ✗ | if model supports |
| output\_indicator | Link | ✗ | if model supports |
| performance\_target | Link | ✗ | if model supports |
| is\_active | Check | ✓ | only active lines selectable |

**6.3 Derived rule**

amount\_available = amount\_allocated - amount\_reserved - amount\_consumed

For the current phase, if amount\_consumed is not yet in active use, treat it as 0.

**7\. Budget Line — Validation rules**

| **Rule ID** | **Rule** |
| --- | --- |
| BL-001 | amount\_allocated >= 0 |
| BL-002 | amount\_reserved >= 0 |
| BL-003 | amount\_consumed >= 0 |
| BL-004 | amount\_reserved + amount\_consumed <= amount\_allocated |
| BL-005 | only is\_active = 1 lines may be exposed to DIA |
| BL-006 | strategic linkage fields must be internally consistent |
| BL-007 | budget line must belong to same entity as parent budget |

**8\. Budget Reservation — New entity**

**8.1 Purpose**

Represents a formal budget hold created when DIA is finance-approved.

This is the missing control record.

**8.2 Required fields**

| **Field Name** | **Type** | **Required** | **Purpose** |
| --- | --- | --- | --- |
| name | ID / autoname | ✓ | internal key |
| reservation\_id | Data | ✓ | business-readable ref |
| budget\_line | Link → Budget Line | ✓ | controlled unit |
| budget | Link → Budget | ✓ | parent budget |
| procuring\_entity | Link | ✓ | scope |
| source\_doctype | Data | ✓ | e.g. Demand |
| source\_docname | Data | ✓ | DIA record ID |
| amount | Currency | ✓ | reserved amount |
| currency | Link → Currency | ✓ | financial unit |
| status | Select | ✓ | Active / Released / Cancelled |
| created\_at | Datetime | ✓ | audit |
| created\_by | Link → User | ✓ | audit |
| released\_at | Datetime | ✗ | audit |
| released\_by | Link → User | ✗ | audit |
| release\_reason | Text | ✗ | audit |
| notes | Text | ✗ | optional |

**8.3 Status values**

Active

Released

Cancelled

For DIA support, Active and Released are the important ones.

**9\. Budget Reservation — Validation rules**

| **Rule ID** | **Rule** |
| --- | --- |
| BR-001 | amount > 0 |
| BR-002 | budget\_line required |
| BR-003 | source\_doctype required |
| BR-004 | source\_docname required |
| BR-005 | active reservation must not exceed current available amount at creation time |
| BR-006 | only one active reservation per (source\_doctype, source\_docname) unless deliberate split-reservation policy exists |
| BR-007 | releasing a reservation must preserve audit metadata |

**10\. Reservation lifecycle**

**10.1 Create reservation**

Triggered by:

DIA Finance Approval

Effects:

-   create Budget Reservation
-   increment Budget Line.amount\_reserved
-   update available amount
-   return reservation reference to DIA

**10.2 Release reservation**

Triggered by:

-   DIA rejected after reservation
-   DIA cancelled after reservation

Effects:

-   set reservation status to Released
-   decrement Budget Line.amount\_reserved
-   update available amount
-   preserve audit trail

**10.3 Not yet in scope**

Do not yet implement:

-   conversion from reservation to committed spend
-   partial consumption
-   split release logic

**11\. Required Budget service APIs**

These are the real reason for this extension.

**11.1 get\_budget\_line\_context(budget\_line\_id)**

Returns:

-   budget line identity
-   active status
-   budget
-   entity
-   currency
-   funding source
-   strategy linkage
-   available amount

Used by DIA for:

-   budget-line selection context
-   strategy derivation

**11.2 check\_available\_budget(budget\_line\_id, amount)**

Returns:

-   ok / not ok
-   available amount
-   requested amount
-   shortfall if any

Used by DIA Finance approval.

**11.3 create\_reservation(budget\_line\_id, source\_doctype, source\_docname, amount, actor)**

Behavior:

-   validate active line
-   validate sufficient funds
-   create reservation
-   increment reserved amount
-   return reservation reference

Used by DIA Finance approval.

**11.4 release\_reservation(reservation\_id, reason, actor)**

Behavior:

-   validate reservation active
-   mark released
-   decrement reserved amount
-   persist release metadata

Used by DIA rejection/cancellation flows.

**11.5 get\_available\_budget(budget\_line\_id)**

Returns:

-   allocated
-   reserved
-   consumed
-   available

Useful for UI and detail panels.

**12\. Service-layer rules**

These are non-negotiable.

**Rule 1**

DIA must **not** compute availability itself.

**Rule 2**

DIA must **not** directly update amount\_reserved.

**Rule 3**

All reservation operations go through Budget services.

**Rule 4**

Reservation creation/release must be atomic and auditable.

**13\. Minimal UX implications**

This is not a Budget landing redesign, but there are a few necessary implications.

**In Budget UI / detail surfaces**

Budget line summaries should be able to show:

-   allocated
-   reserved
-   available

**In selector APIs**

Only active budget lines should be exposed to DIA.

**In future Budget Builder**

Budget lines should become visible operational objects, not hidden implementation details.

**14\. Seed data requirements for this extension**

Before DIA can be seeded properly, Budget must seed at least these lines:

| **Code** | **Name** | **Budget** | **Allocated** | **Strategic Link** |
| --- | --- | --- | --- | --- |
| BL-MOH-2026-001 | Medical Equipment Capex | FY2026 Budget | 5000000 | Healthcare Access |
| BL-MOH-2026-002 | Clinical Workforce Training | FY2026 Budget | 3000000 | Workforce Development |
| BL-MOH-2027-001 | Rural Facility Expansion | FY2027 Budget | 9000000 | Healthcare Access |

Initial values:

-   amount\_reserved = 0
-   amount\_consumed = 0
-   is\_active = 1

**15\. Acceptance criteria**

This extension is complete when:

**Budget Line**

-   can be selected by DIA
-   derives strategy correctly
-   exposes available amount correctly

**Reservation**

-   can be created on finance approval
-   can be released on rejection/cancellation
-   updates budget line balances correctly

**Services**

-   DIA can call Budget services without duplicating logic
-   insufficient funds are blocked reliably
-   reservation reference is returned deterministically

**Integrity**

-   no negative availability
-   no silent reservation drift
-   no direct DIA write to Budget balances

**16\. Recommended implementation sequence**

Do this **before resuming DIA Phase C**:

1.  Extend Budget Line
2.  Create Budget Reservation
3.  Implement Budget service APIs
4.  Add seed support for budget lines
5.  Validate with a simple reservation smoke test
6.  Resume DIA integration

**17\. Cursor-ready prompt pack**

Use these as insert tickets before DIA Phase C.

**BX1 — Extend Budget Line for DIA support**

Implement the minimal Budget Line extension required to support Demand Intake and Approval (DIA).

Do NOT redesign the whole Budget module.  
Do NOT add accounting/GL logic.  
Do NOT add procurement planning logic.

Extend Budget Line to include:

-   budget\_line\_code
-   budget\_line\_name
-   budget
-   procuring\_entity
-   fiscal\_year
-   amount\_allocated
-   amount\_reserved
-   amount\_consumed
-   amount\_available (derived or computed consistently)
-   currency
-   funding\_source
-   strategic\_plan
-   program
-   sub\_program
-   output\_indicator
-   performance\_target
-   is\_active

Validation rules:

-   amount\_allocated >= 0
-   amount\_reserved >= 0
-   amount\_consumed >= 0
-   amount\_reserved + amount\_consumed <= amount\_allocated
-   strategic linkage fields must be internally consistent
-   only active lines should be exposed downstream

Acceptance criteria:

-   Budget Line can act as DIA’s operational anchor
-   strategy linkage can be derived from it
-   available balance can be computed reliably

**BX2 — Create Budget Reservation DocType**

Create a new DocType: Budget Reservation.

Purpose:  
Represent a formal reservation/hold created when a DIA record is finance-approved.

Fields:

-   reservation\_id
-   budget\_line
-   budget
-   procuring\_entity
-   source\_doctype
-   source\_docname
-   amount
-   currency
-   status
-   created\_at
-   created\_by
-   released\_at
-   released\_by
-   release\_reason
-   notes

Status values:

-   Active
-   Released
-   Cancelled

Validation:

-   amount > 0
-   budget\_line required
-   source\_doctype/source\_docname required
-   only one active reservation per source record unless explicitly supported later

Acceptance criteria:

-   reservations can be created and released
-   audit metadata preserved

**BX3 — Implement Budget service APIs for DIA**

Implement the minimal Budget service-layer APIs required by DIA.

Required service methods:

1.  get\_budget\_line\_context(budget\_line\_id)
2.  check\_available\_budget(budget\_line\_id, amount)
3.  create\_reservation(budget\_line\_id, source\_doctype, source\_docname, amount, actor)
4.  release\_reservation(reservation\_id, reason, actor)
5.  get\_available\_budget(budget\_line\_id)

Rules:

-   DIA must not compute availability itself
-   DIA must not directly update reserved amounts
-   create/release must be atomic and auditable
-   create\_reservation must fail if insufficient budget

Acceptance criteria:

-   services are callable from DIA
-   balances remain correct
-   reservation references are returned consistently

**BX4 — Add Budget Line seed support**

Add the minimum Budget Line seed data needed for DIA.

Create these exact budget lines:

-   BL-MOH-2026-001 — Medical Equipment Capex
-   BL-MOH-2026-002 — Clinical Workforce Training
-   BL-MOH-2027-001 — Rural Facility Expansion

Requirements:

-   link to existing budgets
-   set allocated amounts appropriately
-   set reserved/consumed to zero initially
-   set correct strategic linkage
-   set is\_active = 1

Acceptance criteria:

-   DIA seed specs can reference these lines directly
-   budget-line selector can use them

**BX5 — Add minimal reservation smoke tests**

Implement minimal smoke tests for the Budget control extension used by DIA.

Cover:

1.  get\_budget\_line\_context returns correct linkage
2.  check\_available\_budget succeeds/fails correctly
3.  create\_reservation reduces available balance
4.  release\_reservation restores available balance
5.  cannot reserve beyond allocated amount

Do not build full Budget reporting tests.  
This is only the control-layer support required for DIA.

Acceptance criteria:

-   Budget is now authoritative enough for DIA integration