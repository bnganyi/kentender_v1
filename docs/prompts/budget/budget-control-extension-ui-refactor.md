Budget Control Extension UI Refactor

# Refactor Architecture

**🚨 What changed conceptually**

**BEFORE (current UI)**

-   Budget is allocated to **Programs**
-   Programs are the main operational unit
-   No explicit financial control object below program

**AFTER (new design)**

-   Budget is controlled at **Budget Line level**
-   Budget Line = **atomic financial + strategy + control unit**
-   Programs become **grouping/visual structure**, not control

**🔥 Core problem in your current UI**

Your current builder:

-   allocates money to **Programs**
-   does NOT expose **Budget Lines**
-   therefore:
    -   no place to attach reservations
    -   no place to attach strategy linkage cleanly
    -   no place to enforce financial control

👉 This will break DIA immediately if not fixed.

**✅ What must change (high-level)**

**1\. Programs → Budget Lines (critical shift)**

**Replace this mental model:**

Budget → Programs → Amount

**With:**

Budget → Budget Lines → Amount → (derived Program)

**🧱 Impact on your CURRENT UI**

Let’s go screen by screen.

**1️⃣ Budget Landing Page**

Your current landing is actually **mostly fine**.

**What stays**

-   KPI cards ✅
-   Budget list ✅
-   Summary panel ✅

**What changes**

**Add budget-line awareness**

In **Allocation overview / Structure**, change:

Programs: 2

Allocated programs: 1

👉 to:

Budget Lines: 3

Allocated lines: 2

Unallocated lines: 1

**Add (optional but strong improvement)**

Top Budget Lines:

\- Medical Equipment Capex → 5,000,000

\- Workforce Training → 3,000,000

👉 This prepares users mentally for DIA.

**2️⃣ Budget Builder — THIS is where the real change is**

Your current builder:

LEFT: Programs

RIGHT: Program Allocation Form

This must change.

**❌ Current (problematic)**

Programs

\- Healthcare Access → 6,000,000

\- Workforce Development → Not allocated

👉 This is no longer your control layer.

**✅ New Builder Structure**

**LEFT PANEL → Budget Lines**

Budget Lines

Medical Equipment Capex

KES 5,000,000

\[Allocated\]

Clinical Workforce Training

KES 3,000,000

\[Allocated\]

Rural Facility Expansion

KES 0

\[Unallocated\]

**RIGHT PANEL → Budget Line Editor**

Instead of:

Program: Healthcare Access

Allocation Amount: 6000000

You now show:

Budget Line: Medical Equipment Capex

Allocated Amount: 5,000,000

Program: Healthcare Access

Sub-program: Infrastructure

Target: Rural coverage expansion

Funding Source: Treasury

Notes: Capital equipment investment

**🧠 Important shift**

👉 Program is now **read-only / derived**, not the thing you allocate to.

**3️⃣ Summary cards in Builder**

Your current:

TOTAL / ALLOCATED / REMAINING

✅ Keep this exactly

**Add one more (optional but powerful)**

Reserved: 0

Available: 9,000,000

👉 This prepares for DIA integration.

**4️⃣ New required behaviors**

**A. Budget Line creation**

You now need a way to:

-   create/edit budget lines
-   assign:
    -   program
    -   strategy linkage
    -   funding source

👉 This can be:

-   inline  
    OR
-   modal  
    OR
-   separate config step

**B. Validation**

Instead of:

Program allocations ≤ total budget

You now enforce:

Sum(Budget Line allocations) ≤ Total Budget

**C. Locking**

When budget is approved:

Budget Lines become immutable

NOT just program allocations.

**5️⃣ What you should NOT do**

Do NOT:

-   keep both program allocation AND budget line allocation (duplication)
-   try to “map later”
-   allow DIA to select Programs instead of Budget Lines
-   hide budget lines behind the scenes

That creates:

-   inconsistent totals
-   broken reservations
-   bad audit trail

**🧭 Migration approach (very important)**

Do NOT delete your current model abruptly.

**Step 1 — Introduce Budget Lines**

-   create budget lines behind the scenes
-   map each program allocation → 1 budget line

Example:

Healthcare Access → Medical Equipment Capex

**Step 2 — Switch UI**

-   replace program list with budget lines

**Step 3 — Deprecate program allocation**

-   keep programs as grouping only

**🧪 Quick sanity test**

After refactor, you should be able to answer:

“Which exact budget unit funds this demand?”

With:

Budget Line: BL-MOH-2026-001

NOT:

Program: Healthcare Access ❌

**🧱 Final structure**

**BEFORE**

Budget

→ Program allocations ❌

**AFTER**

Budget

→ Budget Lines ✅

→ Strategy linkage

→ Amount

→ Reservation target

**⚡ Bottom line**

**Your current UI is:**

✔ clean  
❌ conceptually outdated

**Required change:**

Replace **Program Allocation Builder** with **Budget Line Builder**

# Budget Line domain model specification

**Budget Line — Strict Domain Model Specification**

**1\. Purpose**

Budget Line is the **atomic financial control unit** within a Budget.

It exists to:

-   hold an allocatable amount
-   carry stable strategy linkage
-   serve as the selectable control anchor for DIA
-   support availability checks
-   support reservation lifecycle

It is **not**:

-   a program
-   a generic accounting GL line
-   a procurement transaction
-   a reporting-only artifact

**2\. Ownership**

**Owning app**

kentender\_budget

**Owned by**

-   Budget module only

**Consumed by**

-   DIA (read/select/check/reserve)
-   later Procurement Planning (read only / controlled consumption)

No downstream app may directly mutate Budget Line balances.

**3\. Record identity**

**Business role**

A Budget Line is the smallest controlled budget subdivision that can fund demand.

**Identity rules**

Each Budget Line must have:

-   internal primary key (name)
-   stable business code (budget\_line\_code)
-   business-readable name (budget\_line\_name)

The business code is what users and downstream modules should rely on operationally.

**4\. Canonical fields**

**4.1 Core identity and ownership**

| **Field Name** | **Label** | **Type** | **Required** | **Read-only** | **Default** | **Description** |
| --- | --- | --- | --- | --- | --- | --- |
| name | System ID | Data / autoname | ✓ | ✓ | generated | Internal Frappe primary key |
| budget\_line\_code | Budget Line Code | Data | ✓ | No | — | Stable business-readable unique code within scope |
| budget\_line\_name | Budget Line Name | Data | ✓ | No | — | Human-readable line title |
| budget | Budget | Link → Budget | ✓ | No | — | Parent Budget record |
| procuring\_entity | Procuring Entity | Link | ✓ | No / derived | derived if possible | Entity that owns the line |
| fiscal\_year | Fiscal Year | Int | ✓ | No / derived | derived from Budget if possible | Control year for the line |
| currency | Currency | Link / Data | ✓ | No / derived | derived from Budget | Currency for amounts |
| is\_active | Active | Check | ✓ | No | 1 | Only active lines are selectable downstream |

**4.2 Strategic linkage**

These are required because Budget Line is now the operational bridge from Budget to DIA.

| **Field Name** | **Label** | **Type** | **Required** | **Read-only** | **Default** | **Description** |
| --- | --- | --- | --- | --- | --- | --- |
| strategic\_plan | Strategic Plan | Link → Strategic Plan | ✓ | No | — | Plan context |
| program | Program | Link → Program | ✓ | No | — | Main strategic grouping |
| sub\_program | Sub-program | Link → Sub-program | ✗ / preferred | No | — | More specific strategy grouping if model supports |
| output\_indicator | Output Indicator | Link → Output Indicator | ✗ / preferred | No | — | Indicator linkage if model supports |
| performance\_target | Performance Target | Link → Performance Target | ✗ / preferred | No | — | Deepest target linkage if model supports |

**Required linkage rule**

At minimum, every Budget Line must link to:

-   strategic\_plan
-   program

If your strategy model already has stable lower-level objects, you should also store:

-   sub\_program
-   output\_indicator
-   performance\_target

The system should enforce consistency across these fields.

**4.3 Financial control fields**

| **Field Name** | **Label** | **Type** | **Required** | **Read-only** | **Default** | **Description** |
| --- | --- | --- | --- | --- | --- | --- |
| amount\_allocated | Allocated Amount | Currency | ✓ | No | 0 | Amount assigned to this line from parent budget |
| amount\_reserved | Reserved Amount | Currency | ✓ | ✓ to ordinary users | 0 | Running total reserved by approved DIA records |
| amount\_consumed | Consumed Amount | Currency | ✓ | ✓ to ordinary users | 0 | Downstream committed/consumed amount; currently may stay 0 |
| amount\_available | Available Amount | Currency / derived | ✓ | ✓ | derived | Computed available amount |
| funding\_source | Funding Source | Link / Data | ✗ | No | — | Treasury / Donor / Grant / etc. |
| notes | Notes | Text | ✗ | No | — | Explanatory notes |

**Derived formula**

amount\_available = amount\_allocated - amount\_reserved - amount\_consumed

For the current stage:

-   amount\_consumed may remain 0
-   but the field must exist to avoid redesign later

**4.4 Metadata / audit support**

| **Field Name** | **Label** | **Type** | **Required** | **Read-only** | **Default** | **Description** |
| --- | --- | --- | --- | --- | --- | --- |
| created\_by | Created By | Link → User | ✓ | ✓ | session user / system | Audit convenience |
| creation | Created At | Datetime | ✓ | ✓ | system | Standard audit |
| modified\_by | Modified By | Link → User | ✓ | ✓ | system | Standard audit |
| modified | Modified At | Datetime | ✓ | ✓ | system | Standard audit |

No custom duplication beyond what is actually useful.

**5\. Uniqueness constraints**

**5.1 Mandatory uniqueness**

The following combination must be unique:

(budget, budget\_line\_code)

This prevents duplicate line codes within the same budget.

**5.2 Recommended uniqueness**

If operationally appropriate, also avoid duplicate names within a budget:

(budget, budget\_line\_name)

You may enforce this softly at UI level or strictly if your users will benefit from the constraint.

**6\. Validation rules**

**6.1 Core identity validation**

| **Rule ID** | **Rule** |
| --- | --- |
| BL-001 | budget\_line\_code required |
| BL-002 | budget\_line\_name required |
| BL-003 | budget required |
| BL-004 | procuring\_entity required |
| BL-005 | fiscal\_year required |
| BL-006 | currency required |

**6.2 Financial validation**

| **Rule ID** | **Rule** |
| --- | --- |
| BL-010 | amount\_allocated >= 0 |
| BL-011 | amount\_reserved >= 0 |
| BL-012 | amount\_consumed >= 0 |
| BL-013 | amount\_reserved + amount\_consumed <= amount\_allocated |
| BL-014 | amount\_available = amount\_allocated - amount\_reserved - amount\_consumed |
| BL-015 | inactive budget lines must not be selectable in DIA |

**6.3 Strategic validation**

| **Rule ID** | **Rule** |
| --- | --- |
| BL-020 | strategic\_plan required |
| BL-021 | program required |
| BL-022 | if sub\_program exists, it must belong to program |
| BL-023 | if output\_indicator exists, it must belong to the selected hierarchy |
| BL-024 | if performance\_target exists, it must belong to the selected hierarchy |
| BL-025 | all strategic linkage fields must be internally consistent |

**6.4 Parent-budget consistency validation**

| **Rule ID** | **Rule** |
| --- | --- |
| BL-030 | budget and procuring\_entity must belong to the same entity |
| BL-031 | fiscal\_year must match parent Budget unless deliberate cross-year logic exists |
| BL-032 | currency should match parent Budget currency |

**7\. Editability rules**

**Editable in Budget Draft / Rejected**

Users with proper rights may edit:

-   budget\_line\_code
-   budget\_line\_name
-   amount\_allocated
-   strategic linkage fields
-   funding\_source
-   notes
-   is\_active

**Non-editable by normal users**

-   amount\_reserved
-   amount\_consumed
-   amount\_available

These must be updated by controlled services only.

**Locked states**

When parent Budget is:

-   Submitted
-   Approved

then Budget Line records must be effectively read-only except for highly controlled admin actions.

That lock is critical because DIA will later trust active lines as stable control units.

**8\. Selector behavior**

Budget Lines exposed to DIA must satisfy all of:

-   is\_active = 1
-   parent Budget in valid state for downstream use
-   internally consistent strategy mapping
-   valid financial fields

Recommended selector payload for DIA:

| **Field** | **Include** |
| --- | --- |
| budget\_line\_code | ✓ |
| budget\_line\_name | ✓ |
| budget | ✓ |
| procuring\_entity | ✓ |
| fiscal\_year | ✓ |
| currency | ✓ |
| funding\_source | ✓ |
| strategic\_plan | ✓ |
| program | ✓ |
| sub\_program | if present |
| output\_indicator | if present |
| performance\_target | if present |
| amount\_allocated | ✓ |
| amount\_reserved | ✓ |
| amount\_available | ✓ |

Do not expose irrelevant internals.

**9\. Relationship to reservation model**

A Budget Line may have zero or more Budget Reservation records.

**Aggregate control rule**

The line does **not** store reservation details directly beyond rolled-up balances.

Detailed reservation history belongs in:

Budget Reservation

The Budget Line only stores:

-   amount\_reserved
-   derived amount\_available

That keeps the control model clean.

**10\. Relationship to Budget Builder v2**

Budget Builder v2 must treat Budget Line as the primary editable object.

**Left panel**

List of Budget Lines

**Right panel**

Selected Budget Line detail/editor

**Summary strip**

Derived from all active Budget Lines:

-   Total Budget
-   Allocated
-   Remaining

Optional later:

-   Reserved
-   Available

**11\. Migration implications from current program-allocation model**

If your current budget records are program-based, migrate them carefully.

**Minimal transition rule**

For each current program allocation, create at least one corresponding Budget Line.

Example:

| **Old Program Allocation** | **New Budget Line** |
| --- | --- |
| Healthcare Access → 6,000,000 | BL-MOH-2026-001 Medical Equipment Capex → 5,000,000 and/or another line as needed |
| Workforce Development → 0 | BL-MOH-2026-002 Clinical Workforce Training → 0 |

Do not keep both as competing control models.

Programs should become:

-   grouping context
-   derived strategic context

not the allocatable object.

**12\. Acceptance criteria**

Budget Line implementation is correct only if:

-   every active line has a stable code and name
-   every active line links to a Budget
-   every active line has valid financial fields
-   strategy linkage is present and internally consistent
-   amount\_available derives correctly
-   amount\_reserved cannot be manually changed through ordinary UI edits
-   only active lines are exposed to DIA
-   parent Budget locks line editing in submitted/approved states
-   Builder v2 can use Budget Lines without ambiguity

**13\. Cursor-ready implementation prompt**

Implement the Budget Line domain model exactly as specified.

This is the authoritative financial control unit for Budget and the selection/control anchor for DIA.

Requirements:

1.  Create or refactor Budget Line so it includes:

-   budget\_line\_code
-   budget\_line\_name
-   budget
-   procuring\_entity
-   fiscal\_year
-   currency
-   is\_active
-   strategic\_plan
-   program
-   sub\_program
-   output\_indicator
-   performance\_target
-   amount\_allocated
-   amount\_reserved
-   amount\_consumed
-   amount\_available
-   funding\_source
-   notes

1.  Enforce validation rules:

-   required identity fields
-   financial constraints
-   internal strategy consistency
-   parent budget consistency
-   unique (budget, budget\_line\_code)

1.  Implement amount\_available consistently as:

-   amount\_allocated - amount\_reserved - amount\_consumed

1.  Protect these fields from ordinary manual edits:

-   amount\_reserved
-   amount\_consumed
-   amount\_available

1.  Ensure submitted/approved parent budgets lock Budget Line editing.
2.  Do not implement GL/accounting logic.
3.  Do not implement procurement transaction logic here.
4.  Do not keep program allocation as a competing control model.

At the end report:

-   files changed
-   migration assumptions from current program-allocation data
-   any unresolved gaps before Budget Builder v2 refactor

**Recommendation**

Do **this** before the Budget Builder UI refactor if the field model is not already locked in code.

That sequence should be:

Budget Line domain model

→ Budget Reservation model/services

→ Budget Builder v2 refactor

→ Resume DIA Phase C

If you want, the next useful artifact is the **strict Budget Reservation domain model table** so the reservation control object is just as tightly defined.

# Budget Reservation — Strict Domain Model Specification

**Budget Reservation — Strict Domain Model Specification**

**1\. Purpose**

Budget Reservation is the **formal, auditable financial hold** placed against a Budget Line when a downstream demand record is finance-approved.

It exists to:

-   reserve part of a Budget Line’s available amount
-   provide a traceable financial control reference back to the source demand
-   support release on rejection or cancellation
-   let downstream modules trust that funds were actually held, not just “checked”

It is **not**:

-   a payment
-   a ledger posting
-   a commitment voucher
-   a purchase order
-   a generic note or audit log entry

**2\. Ownership**

**Owning app**

kentender\_budget

**Owned by**

-   Budget module only

**Created by**

-   Budget service layer only

**Consumed by**

-   DIA
-   later Procurement Planning / downstream financial control flows as read/reference

No downstream module may create or mutate reservation state directly except through Budget services.

**3\. Business role**

A Budget Reservation answers the question:

**Which exact amount was reserved, against which Budget Line, for which source demand, by whom, and what is its current state?**

That is the core control question DIA needs answered.

**4\. Record identity**

Each reservation must have:

-   internal primary key: name
-   stable business-readable identifier: reservation\_id

**Reservation ID pattern**

Recommended pattern:

RSV-<ENTITY>-<YEAR>-####

Example:

RSV-MOH-2026-0001

This should be generated through the shared business ID service in kentender\_core.

**5\. Canonical fields**

**5.1 Identity and ownership**

| **Field Name** | **Label** | **Type** | **Required** | **Read-only** | **Default** | **Description** |
| --- | --- | --- | --- | --- | --- | --- |
| name | System ID | Data / autoname | ✓ | ✓ | generated | Internal primary key |
| reservation\_id | Reservation ID | Data | ✓ | ✓ | generated | Stable business-readable ID |
| budget\_line | Budget Line | Link → Budget Line | ✓ | ✓ after create | — | Budget control unit being reserved |
| budget | Budget | Link → Budget | ✓ | ✓ | derived | Parent Budget of the line |
| procuring\_entity | Procuring Entity | Link | ✓ | ✓ | derived | Entity scope for the reservation |
| fiscal\_year | Fiscal Year | Int | ✓ | ✓ | derived | Derived from Budget Line / Budget |
| currency | Currency | Link / Data | ✓ | ✓ | derived | Currency of the Budget Line |

**5.2 Source linkage**

These fields make the reservation traceable to the originating transaction.

| **Field Name** | **Label** | **Type** | **Required** | **Read-only** | **Default** | **Description** |
| --- | --- | --- | --- | --- | --- | --- |
| source\_doctype | Source DocType | Data | ✓ | ✓ | — | Originating record type, e.g. Demand |
| source\_docname | Source Record ID | Data | ✓ | ✓ | — | Originating record primary key |
| source\_business\_id | Source Business ID | Data | ✗ / preferred | ✓ | derived if available | Human-readable source reference, e.g. DIA-MOH-2026-0004 |

**Rule**

For current DIA support:

-   source\_doctype = Demand
-   source\_docname must point to the exact DIA record

**5.3 Financial fields**

| **Field Name** | **Label** | **Type** | **Required** | **Read-only** | **Default** | **Description** |
| --- | --- | --- | --- | --- | --- | --- |
| amount | Reserved Amount | Currency | ✓ | ✓ after create | — | Exact amount reserved |
| status | Reservation Status | Select | ✓ | controlled by service | Active | Current reservation state |
| available\_before\_reservation | Available Before | Currency | ✓ | ✓ | system | Snapshot before create |
| available\_after\_reservation | Available After | Currency | ✓ | ✓ | system | Snapshot after create |

**Status values**

Active

Released

Cancelled

For the current phase:

-   Active = valid hold in force
-   Released = previously valid hold has been released
-   Cancelled = optional administrative terminal status if needed later

You may keep operational logic centered on Active and Released for now.

**5.4 Lifecycle metadata**

| **Field Name** | **Label** | **Type** | **Required** | **Read-only** | **Default** | **Description** |
| --- | --- | --- | --- | --- | --- | --- |
| created\_at | Created At | Datetime | ✓ | ✓ | system | Creation timestamp |
| created\_by | Created By | Link → User | ✓ | ✓ | actor | Who created the reservation |
| released\_at | Released At | Datetime | ✗ | ✓ | — | Time reservation released |
| released\_by | Released By | Link → User | ✗ | ✓ | — | Who released it |
| release\_reason | Release Reason | Text | ✗ / required on release | ✓ after release | — | Why reservation was released |

**5.5 Optional operational fields**

Keep these only if useful now.

| **Field Name** | **Label** | **Type** | **Required** | **Read-only** | **Default** | **Description** |
| --- | --- | --- | --- | --- | --- | --- |
| notes | Notes | Text | ✗ | No | — | Additional remarks |
| is\_active | Active Flag | Check | ✓ | controlled by service | 1 | Convenience mirror of status if your conventions use it |

If status is authoritative, is\_active is optional and may be omitted to avoid duplication.

**6\. Authoritative status model**

**Allowed values**

-   Active
-   Released
-   Cancelled

**Current recommended lifecycle**

Active → Released

For v1, this is enough.

Avoid introducing more states unless clearly needed.

**7\. Required constraints**

**7.1 Core validation**

| **Rule ID** | **Rule** |
| --- | --- |
| BR-001 | budget\_line required |
| BR-002 | budget required |
| BR-003 | procuring\_entity required |
| BR-004 | source\_doctype required |
| BR-005 | source\_docname required |
| BR-006 | amount > 0 |
| BR-007 | currency required |
| BR-008 | created\_at required |
| BR-009 | created\_by required |

**7.2 Source integrity**

| **Rule ID** | **Rule** |
| --- | --- |
| BR-020 | source record must exist |
| BR-021 | source record must belong to same entity if entity-scoped |
| BR-022 | source record must be valid for reservation creation |
| BR-023 | reservation must not be created against an already terminal/invalid source state |

For current DIA support, the main source validity rule is:

-   reservation may only be created during valid finance approval flow

**7.3 Budget integrity**

| **Rule ID** | **Rule** |
| --- | --- |
| BR-030 | budget\_line must exist and be active |
| BR-031 | budget must match the selected budget\_line |
| BR-032 | procuring\_entity must match the selected budget\_line |
| BR-033 | fiscal\_year must match the selected budget\_line / budget |

**7.4 Financial control integrity**

| **Rule ID** | **Rule** |
| --- | --- |
| BR-040 | amount <= available\_before\_reservation at creation time |
| BR-041 | available\_after\_reservation = available\_before\_reservation - amount |
| BR-042 | reservation creation must atomically update Budget Line reserved balance |
| BR-043 | release must atomically reduce Budget Line reserved balance |
| BR-044 | released reservation must not remain counted in active reserved total |

**7.5 Uniqueness / anti-duplication**

**Mandatory uniqueness policy**

For current phase, enforce at most **one active reservation per source record**.

Recommended constraint logic:

(source\_doctype, source\_docname, status = Active) must be unique

This prevents accidental double-reservation for the same DIA record.

If later you deliberately support split reservations, relax this only with explicit design.

**8\. Editability rules**

**Ordinary users**

Must **never** directly edit:

-   amount
-   status
-   budget\_line
-   source fields
-   snapshot values
-   release metadata

**Service-layer only fields**

The following are updated only via Budget services:

-   status
-   released\_at
-   released\_by
-   release\_reason
-   available\_before\_reservation
-   available\_after\_reservation

**UI rule**

This is not a casual data-entry record. It is a controlled financial artifact.

So:

-   it should be visible in summaries/reports if needed
-   but not exposed as a free-edit form to ordinary users

**9\. Relationship to Budget Line**

**One Budget Line → many reservations**

A Budget Line may have many reservations over time.

**Budget Line roll-up fields**

Budget Line stores only rolled-up values:

-   amount\_reserved
-   amount\_available

Detailed reservation history belongs in Budget Reservation.

That separation must remain clean.

**10\. Relationship to DIA**

For current scope:

-   DIA Finance approval calls create\_reservation(...)
-   DIA rejection/cancellation calls release\_reservation(...)
-   DIA stores:
    -   reservation\_reference
    -   reservation\_status
    -   budget snapshot if needed

But DIA does **not** own reservation truth.

Budget Reservation remains the authoritative record.

**11\. Required service operations**

These operations are the only supported lifecycle entry points.

**11.1 Create reservation**

**Method**

create\_reservation(budget\_line\_id, source\_doctype, source\_docname, amount, actor)

**Responsibilities**

-   validate budget line
-   compute available amount
-   ensure sufficient balance
-   ensure no duplicate active reservation for source
-   create Budget Reservation
-   increase Budget Line amount\_reserved
-   return reservation reference and financial snapshots

**11.2 Release reservation**

**Method**

release\_reservation(reservation\_id, reason, actor)

**Responsibilities**

-   validate reservation exists and is Active
-   mark reservation Released
-   record release metadata
-   decrease Budget Line amount\_reserved
-   preserve audit trail

**11.3 Read reservation**

**Methods**

get\_reservation(reservation\_id)

get\_active\_reservation\_for\_source(source\_doctype, source\_docname)

list\_reservations\_for\_budget\_line(budget\_line\_id)

These can be added incrementally, but at minimum the active-source lookup is useful for DIA integrity.

**12\. Recommended API exposure**

If you expose APIs, keep them controlled.

**Recommended API types**

-   business action API:
    -   create reservation
    -   release reservation
-   selector / lookup API:
    -   get reservation by source
    -   get reservation by id

Do not expose open CRUD casually.

**13\. Minimal UI implications**

You do not need a full Budget Reservation workspace yet.

But the following should be possible:

**In Budget Line detail**

Show:

-   reserved amount
-   available amount

**In DIA detail**

Show:

-   reservation status
-   reservation reference

**Optional admin/finance inspection**

A lightweight lookup/report is enough for now.

**14\. Seed requirements**

For current phase, reservation seed should come from upstream scenario creation, not arbitrary standalone reservation demos.

At minimum, the following scenarios should result in reservations:

-   Approved DIA demand
-   Planning Ready DIA demand

Examples already aligned in your seed plan:

-   DIA-MOH-2026-0004
-   DIA-MOH-2026-0005

These should create matching reservations such as:

-   RSV-MOH-2026-0004
-   RSV-MOH-2026-0005

**15\. Audit and compliance expectations**

Every reservation must be reconstructable for audit:

-   who created it
-   when
-   against what source
-   against which Budget Line
-   for what amount
-   whether it is still active
-   if released, who released it and why

That is the entire reason this object exists separately from just a numeric field on Budget Line.

**16\. Acceptance criteria**

Budget Reservation is correctly implemented only if:

-   reservation has a stable business ID
-   every reservation links to one Budget Line
-   every reservation links to one source record
-   amount is positive and validated
-   duplicate active reservation for same source is blocked
-   create operation updates Budget Line reserved balance
-   release operation updates Budget Line reserved balance
-   release preserves audit metadata
-   ordinary UI cannot mutate reservation internals
-   DIA can consume reservation reference without owning reservation truth

**17\. Cursor-ready implementation prompt**

Implement the Budget Reservation domain model exactly as specified.

This is a controlled financial artifact inside kentender\_budget.

Requirements:

1.  Create Budget Reservation with fields:

-   reservation\_id
-   budget\_line
-   budget
-   procuring\_entity
-   fiscal\_year
-   currency
-   source\_doctype
-   source\_docname
-   source\_business\_id
-   amount
-   status
-   available\_before\_reservation
-   available\_after\_reservation
-   created\_at
-   created\_by
-   released\_at
-   released\_by
-   release\_reason
-   notes

1.  Status values:

-   Active
-   Released
-   Cancelled

1.  Enforce validation:

-   amount > 0
-   budget\_line required
-   source\_doctype/source\_docname required
-   one active reservation per source record
-   amount cannot exceed available budget at create time

1.  Protect reservation internals from ordinary manual edits.
2.  Keep reservation lifecycle controlled through service methods, not free-form CRUD.
3.  Do not implement GL/accounting posting.
4.  Do not implement procurement logic here.
5.  Do not expose broad editable UI for reservations.

At the end report:

-   files changed
-   how uniqueness was enforced
-   how Budget Line balances will stay in sync
-   any unresolved gap before DIA resumes integration

**Recommended sequence now**

The clean sequence remains:

Budget Line domain model

→ Budget Reservation domain model

→ Budget service-layer methods

→ Budget Line seed support

→ reservation smoke tests

→ Budget Builder v2 refactor

→ resume DIA Phase C

If you want, the next most useful artifact is the **strict Budget service contract** so Cursor has exact request/response behavior for:

-   get\_budget\_line\_context
-   check\_available\_budget
-   create\_reservation
-   release\_reservation
-   get\_available\_budget

# Budget Control Services — Strict Service Contract

**1\. Purpose**

These services provide the only valid way to:

-   read Budget Line operational context
-   check available budget
-   create a reservation
-   release a reservation
-   read reservation/availability state

They exist to ensure:

-   DIA does not compute budget availability itself
-   DIA does not mutate Budget balances directly
-   reservation lifecycle remains auditable and centralized
-   Budget remains the authoritative financial control layer

**2\. Ownership**

**Owning app**

kentender\_budget

**Implementation location**

Recommended:

kentender\_budget/services/budget\_control.py

or split cleanly if needed:

kentender\_budget/services/budget\_lines.py

kentender\_budget/services/reservations.py

But keep a coherent service entry surface.

**3\. Non-negotiable service rules**

**Rule 1**

All write operations must be service-mediated.

**Rule 2**

No downstream app may directly update:

-   Budget Line.amount\_reserved
-   Budget Line.amount\_consumed
-   Budget Line.amount\_available
-   Budget Reservation.status

**Rule 3**

All critical service operations must:

-   validate inputs
-   enforce business rules
-   be atomic
-   write audit-safe metadata

**Rule 4**

Service responses must follow the standard envelope already defined in your architecture:

**Success**

{

"ok": true,

"data": {},

"message": "Success"

}

**Error**

{

"ok": false,

"error\_code": "ERROR\_CODE",

"message": "Human-readable explanation"

}

**4\. Service list**

For the current phase, the required services are:

1.  get\_budget\_line\_context
2.  check\_available\_budget
3.  create\_reservation
4.  release\_reservation
5.  get\_available\_budget
6.  get\_active\_reservation\_for\_source (recommended)
7.  list\_reservations\_for\_budget\_line (recommended, lightweight)

The first five are mandatory.

**5\. Service contract details**

**5.1 get\_budget\_line\_context(budget\_line\_id)**

**Purpose**

Return the operational context of a Budget Line for downstream consumers such as DIA and Budget Builder.

**Signature**

get\_budget\_line\_context(budget\_line\_id: str) -> dict

**Input**

| **Parameter** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| budget\_line\_id | str | ✓ | Internal Budget Line identifier |

**Behavior**

The service must:

1.  load the Budget Line
2.  validate it exists
3.  validate it is active if being exposed for downstream transactional use
4.  return the full operational context needed by DIA

**Required returned data**

{

"budget\_line\_id": "BL\_INTERNAL\_ID",

"budget\_line\_code": "BL-MOH-2026-001",

"budget\_line\_name": "Medical Equipment Capex",

"budget": "FY2026 Budget",

"budget\_id": "BUDGET\_INTERNAL\_ID",

"procuring\_entity": "MOH",

"fiscal\_year": 2026,

"currency": "KES",

"funding\_source": "Treasury",

"strategic\_plan": "MOH Strategic Plan 2026–2030",

"program": "Healthcare Access",

"sub\_program": "Infrastructure",

"output\_indicator": "Rural diagnostic coverage",

"performance\_target": "Target 2026-2030",

"amount\_allocated": 5000000,

"amount\_reserved": 0,

"amount\_consumed": 0,

"amount\_available": 5000000,

"is\_active": true

}

**Success response**

{

"ok": true,

"data": {

"...": "..."

},

"message": "Budget line context loaded"

}

**Error cases**

| **Error Code** | **When** |
| --- | --- |
| BUDGET\_LINE\_NOT\_FOUND | no such line |
| BUDGET\_LINE\_INACTIVE | line inactive and not valid for downstream use |
| BUDGET\_LINE\_INVALID | line exists but missing required control fields |

**Notes**

This is the service DIA should use to:

-   derive strategy context
-   show budget details
-   confirm operational validity

**5.2 get\_available\_budget(budget\_line\_id)**

**Purpose**

Return the authoritative financial availability snapshot for a Budget Line.

**Signature**

get\_available\_budget(budget\_line\_id: str) -> dict

**Input**

| **Parameter** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| budget\_line\_id | str | ✓ | Internal Budget Line identifier |

**Behavior**

The service must:

1.  load the Budget Line
2.  validate it exists
3.  compute or retrieve:
    -   allocated
    -   reserved
    -   consumed
    -   available

**Required returned data**

{

"budget\_line\_id": "BL\_INTERNAL\_ID",

"amount\_allocated": 5000000,

"amount\_reserved": 1200000,

"amount\_consumed": 0,

"amount\_available": 3800000,

"currency": "KES"

}

**Success response**

{

"ok": true,

"data": {

"budget\_line\_id": "BL\_INTERNAL\_ID",

"amount\_allocated": 5000000,

"amount\_reserved": 1200000,

"amount\_consumed": 0,

"amount\_available": 3800000,

"currency": "KES"

},

"message": "Available budget loaded"

}

**Error cases**

| **Error Code** | **When** |
| --- | --- |
| BUDGET\_LINE\_NOT\_FOUND | line missing |
| BUDGET\_LINE\_INVALID | financial fields invalid or inconsistent |

**Notes**

This is a read-only service. It must not mutate anything.

**5.3 check\_available\_budget(budget\_line\_id, amount)**

**Purpose**

Validate whether a Budget Line can support a requested amount.

**Signature**

check\_available\_budget(budget\_line\_id: str, amount: Decimal | float | int) -> dict

**Input**

| **Parameter** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| budget\_line\_id | str | ✓ | Internal Budget Line identifier |
| amount | numeric | ✓ | Requested amount to validate |

**Behavior**

The service must:

1.  validate amount > 0
2.  load Budget Line
3.  compute current available amount
4.  compare requested amount to available amount
5.  return result without mutating anything

**Required returned data**

{

"budget\_line\_id": "BL\_INTERNAL\_ID",

"requested\_amount": 800000,

"amount\_available": 1200000,

"currency": "KES",

"is\_sufficient": true,

"shortfall": 0

}

If insufficient:

{

"budget\_line\_id": "BL\_INTERNAL\_ID",

"requested\_amount": 1800000,

"amount\_available": 1200000,

"currency": "KES",

"is\_sufficient": false,

"shortfall": 600000

}

**Success response**

{

"ok": true,

"data": {

"budget\_line\_id": "BL\_INTERNAL\_ID",

"requested\_amount": 1800000,

"amount\_available": 1200000,

"currency": "KES",

"is\_sufficient": false,

"shortfall": 600000

},

"message": "Budget availability checked"

}

**Error cases**

| **Error Code** | **When** |
| --- | --- |
| INVALID\_AMOUNT | amount <= 0 |
| BUDGET\_LINE\_NOT\_FOUND | line missing |
| BUDGET\_LINE\_INVALID | invalid financial state |

**Notes**

DIA Finance approval must call this before reservation creation, even if create\_reservation also re-validates.

**5.4 create\_reservation(budget\_line\_id, source\_doctype, source\_docname, amount, actor, source\_business\_id=None)**

**Purpose**

Create an authoritative budget reservation against a Budget Line for a source transaction such as DIA.

**Signature**

create\_reservation(

budget\_line\_id: str,

source\_doctype: str,

source\_docname: str,

amount: Decimal | float | int,

actor: str,

source\_business\_id: str | None = None

) -> dict

**Input**

| **Parameter** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| budget\_line\_id | str | ✓ | Target Budget Line |
| source\_doctype | str | ✓ | Source record type, e.g. Demand |
| source\_docname | str | ✓ | Source internal record id |
| amount | numeric | ✓ | Amount to reserve |
| actor | str | ✓ | User creating reservation |
| source\_business\_id | str | ✗ | Human-readable source ref, e.g. DIA-MOH-2026-0004 |

**Preconditions**

1.  Budget Line exists
2.  Budget Line is active
3.  amount > 0
4.  available amount is sufficient
5.  no active reservation already exists for the same (source\_doctype, source\_docname) unless later explicitly supported

**Behavior**

The service must:

1.  lock or safely read the Budget Line for update
2.  compute availability
3.  validate sufficiency
4.  validate uniqueness for active source reservation
5.  create Budget Reservation with:
    -   status = Active
    -   snapshots before and after
    -   source metadata
6.  increment Budget Line.amount\_reserved
7.  update Budget Line.amount\_available
8.  return reservation details

**Atomicity rule**

This must be a single atomic operation.  
If any step fails:

-   no reservation is created
-   Budget Line balances remain unchanged

**Required returned data**

{

"reservation\_id": "RSV-MOH-2026-0004",

"reservation\_name": "RESERVATION\_INTERNAL\_ID",

"budget\_line\_id": "BL\_INTERNAL\_ID",

"budget\_line\_code": "BL-MOH-2026-001",

"source\_doctype": "Demand",

"source\_docname": "DIA\_INTERNAL\_ID",

"source\_business\_id": "DIA-MOH-2026-0004",

"amount": 3000000,

"status": "Active",

"available\_before\_reservation": 5000000,

"available\_after\_reservation": 2000000,

"currency": "KES"

}

**Success response**

{

"ok": true,

"data": {

"reservation\_id": "RSV-MOH-2026-0004",

"reservation\_name": "RESERVATION\_INTERNAL\_ID",

"budget\_line\_id": "BL\_INTERNAL\_ID",

"budget\_line\_code": "BL-MOH-2026-001",

"source\_doctype": "Demand",

"source\_docname": "DIA\_INTERNAL\_ID",

"source\_business\_id": "DIA-MOH-2026-0004",

"amount": 3000000,

"status": "Active",

"available\_before\_reservation": 5000000,

"available\_after\_reservation": 2000000,

"currency": "KES"

},

"message": "Reservation created successfully"

}

**Error cases**

| **Error Code** | **When** |
| --- | --- |
| INVALID\_AMOUNT | amount <= 0 |
| BUDGET\_LINE\_NOT\_FOUND | line missing |
| BUDGET\_LINE\_INACTIVE | line inactive |
| INSUFFICIENT\_BUDGET | not enough available amount |
| DUPLICATE\_ACTIVE\_RESERVATION | active reservation already exists for source |
| SOURCE\_REFERENCE\_INVALID | source record invalid |
| RESERVATION\_CREATE\_FAILED | write/update failed |

**Notes**

This is the critical control service for DIA Finance approval.

**5.5 release\_reservation(reservation\_id, reason, actor)**

**Purpose**

Release an active reservation and restore available balance.

**Signature**

release\_reservation(

reservation\_id: str,

reason: str,

actor: str

) -> dict

**Input**

| **Parameter** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| reservation\_id | str | ✓ | Reservation business ID or internal ID, choose one convention and document it |
| reason | str | ✓ | Reason for release |
| actor | str | ✓ | User performing release |

**Preconditions**

1.  reservation exists
2.  reservation status = Active
3.  reason is not empty

**Behavior**

The service must:

1.  load reservation and linked Budget Line
2.  validate reservation is active
3.  mark reservation Released
4.  set:
    -   released\_at
    -   released\_by
    -   release\_reason
5.  decrement Budget Line.amount\_reserved by reservation amount
6.  update Budget Line.amount\_available
7.  preserve reservation record for audit

**Atomicity rule**

Release must be atomic with balance update.

**Required returned data**

{

"reservation\_id": "RSV-MOH-2026-0004",

"status": "Released",

"budget\_line\_id": "BL\_INTERNAL\_ID",

"budget\_line\_code": "BL-MOH-2026-001",

"released\_amount": 3000000,

"available\_after\_release": 5000000,

"released\_at": "2026-03-04T15:20:00",

"released\_by": "finance.reviewer@moh.test"

}

**Success response**

{

"ok": true,

"data": {

"reservation\_id": "RSV-MOH-2026-0004",

"status": "Released",

"budget\_line\_id": "BL\_INTERNAL\_ID",

"budget\_line\_code": "BL-MOH-2026-001",

"released\_amount": 3000000,

"available\_after\_release": 5000000,

"released\_at": "2026-03-04T15:20:00",

"released\_by": "finance.reviewer@moh.test"

},

"message": "Reservation released successfully"

}

**Error cases**

| **Error Code** | **When** |
| --- | --- |
| RESERVATION\_NOT\_FOUND | reservation missing |
| RESERVATION\_NOT\_ACTIVE | already released/cancelled |
| RELEASE\_REASON\_REQUIRED | no reason |
| RESERVATION\_RELEASE\_FAILED | release/update failed |

**Notes**

DIA should call this on:

-   rejection after reservation
-   cancellation after reservation

**5.6 get\_active\_reservation\_for\_source(source\_doctype, source\_docname)**

**Purpose**

Return the active reservation for a given source transaction, if one exists.

**Signature**

get\_active\_reservation\_for\_source(

source\_doctype: str,

source\_docname: str

) -> dict

**Input**

| **Parameter** | **Type** | **Required** |
| --- | --- | --- |
| source\_doctype | str | ✓ |
| source\_docname | str | ✓ |

**Behavior**

Look up active reservation by source.

**Returned data**

If found:

{

"reservation\_id": "RSV-MOH-2026-0004",

"status": "Active",

"amount": 3000000,

"budget\_line\_id": "BL\_INTERNAL\_ID",

"budget\_line\_code": "BL-MOH-2026-001"

}

If not found:

{

"reservation\_id": null,

"status": null

}

**Success response**

{

"ok": true,

"data": {

"reservation\_id": "RSV-MOH-2026-0004",

"status": "Active",

"amount": 3000000,

"budget\_line\_id": "BL\_INTERNAL\_ID",

"budget\_line\_code": "BL-MOH-2026-001"

},

"message": "Active reservation lookup complete"

}

**Error cases**

Usually minimal unless inputs invalid.

**5.7 list\_reservations\_for\_budget\_line(budget\_line\_id)**

**Purpose**

Provide a lightweight reservation history view for a Budget Line.

**Signature**

list\_reservations\_for\_budget\_line(budget\_line\_id: str) -> dict

**Input**

| **Parameter** | **Type** | **Required** |
| --- | --- | --- |
| budget\_line\_id | str | ✓ |

**Behavior**

Return reservations for that line, newest first.

**Returned data**

{

"budget\_line\_id": "BL\_INTERNAL\_ID",

"reservations": \[

{

"reservation\_id": "RSV-MOH-2026-0005",

"source\_doctype": "Demand",

"source\_docname": "DIA\_INTERNAL\_ID\_5",

"source\_business\_id": "DIA-MOH-2026-0005",

"amount": 1500000,

"status": "Active",

"created\_at": "2026-01-23T14:30:00"

},

{

"reservation\_id": "RSV-MOH-2026-0004",

"source\_doctype": "Demand",

"source\_docname": "DIA\_INTERNAL\_ID\_4",

"source\_business\_id": "DIA-MOH-2026-0004",

"amount": 3000000,

"status": "Released",

"created\_at": "2026-02-11T14:00:00"

}

\]

}

This is useful but not strictly required for the first DIA pass.

**6\. Internal invariants**

These must hold after every successful service operation.

**Budget Line invariants**

amount\_allocated >= 0

amount\_reserved >= 0

amount\_consumed >= 0

amount\_available = amount\_allocated - amount\_reserved - amount\_consumed

amount\_reserved + amount\_consumed <= amount\_allocated

**Reservation invariants**

-   only one active reservation per source record
-   released reservation is never counted in active reserved total
-   reservation amount never changes after creation
-   release preserves audit history

**7\. Transaction and concurrency expectations**

Because reservations affect balances, this layer must be safe under concurrent access.

**Required behavior**

When creating a reservation:

-   use transactional integrity
-   lock the Budget Line row or equivalent update path safely
-   prevent double reservation races

When releasing:

-   update reservation and Budget Line in one transaction

If your current stack does not make row-level locking elegant, document the exact approach and ensure it still prevents balance drift.

**8\. Error code set**

Use these exact or very close codes consistently.

| **Error Code** | **Meaning** |
| --- | --- |
| BUDGET\_LINE\_NOT\_FOUND | Budget Line missing |
| BUDGET\_LINE\_INACTIVE | Budget Line inactive |
| BUDGET\_LINE\_INVALID | Invalid financial/strategy state |
| INVALID\_AMOUNT | Invalid requested amount |
| INSUFFICIENT\_BUDGET | Requested amount exceeds available |
| DUPLICATE\_ACTIVE\_RESERVATION | Active reservation already exists for source |
| SOURCE\_REFERENCE\_INVALID | Bad source linkage |
| RESERVATION\_NOT\_FOUND | Reservation missing |
| RESERVATION\_NOT\_ACTIVE | Release attempted on non-active reservation |
| RELEASE\_REASON\_REQUIRED | Missing release reason |
| RESERVATION\_CREATE\_FAILED | Reservation creation failed |
| RESERVATION\_RELEASE\_FAILED | Reservation release failed |

**9\. API wrapper expectations**

If you expose these through api/, keep wrappers thin.

Recommended pattern:

@frappe.whitelist()

def api\_check\_available\_budget(budget\_line\_id, amount):

return check\_available\_budget(budget\_line\_id, amount)

Do not reimplement logic in API wrappers.

**10\. Acceptance criteria**

The service layer is correct only if:

-   get\_budget\_line\_context returns all required operational fields
-   get\_available\_budget returns correct balances
-   check\_available\_budget returns correct sufficiency result
-   create\_reservation creates one active reservation and updates balances
-   duplicate active reservation for same source is blocked
-   release\_reservation releases and restores balances correctly
-   all write operations are atomic
-   all responses follow the standard envelope
-   DIA can use these services without any direct balance mutation

**11\. Cursor-ready implementation prompt**

Implement the Budget control service layer exactly as specified.

Required service methods:

1.  get\_budget\_line\_context(budget\_line\_id)
2.  get\_available\_budget(budget\_line\_id)
3.  check\_available\_budget(budget\_line\_id, amount)
4.  create\_reservation(budget\_line\_id, source\_doctype, source\_docname, amount, actor, source\_business\_id=None)
5.  release\_reservation(reservation\_id, reason, actor)
6.  get\_active\_reservation\_for\_source(source\_doctype, source\_docname)
7.  list\_reservations\_for\_budget\_line(budget\_line\_id) \[lightweight, recommended\]

Rules:

-   use kentender\_budget as the service owner
-   enforce all validation and invariants server-side
-   use the standard response envelope:  
    success: { ok: true, data: {}, message: "..." }  
    error: { ok: false, error\_code: "...", message: "..." }
-   all write operations must be atomic
-   no downstream module may directly mutate Budget Line balances
-   API wrappers, if added, must be thin

Do not:

-   implement GL posting
-   implement procurement business logic here
-   expose broad CRUD for reservations
-   duplicate logic between service and API layers

At the end report:

1.  files changed
2.  transaction/concurrency approach used
3.  how duplicate active reservations were prevented
4.  whether DIA can now safely resume Phase C

**Recommended next sequence**

You now have the minimum Budget control package fully specified:

1.  Budget Line domain model
2.  Budget Reservation domain model
3.  Budget control service contract

So the clean next order is:

Implement Budget Line

→ Implement Budget Reservation

→ Implement Budget Services

→ Seed Budget Lines

→ Reservation smoke tests

→ Refactor Budget Builder v2

→ Resume DIA Phase C

If you want, the next useful artifact is a **Budget control smoke contract** so Cursor has a strict test target before you resume DIA.

# Budget Builder v2 spec

Here is the **Budget Builder v2 spec** aligned to the new **Budget Line control model**.

This is a **targeted refactor**, not a redesign from scratch. The goal is to preserve what is already good in your current Budget UX while correcting the underlying control unit.

**Budget Builder v2 — UI Specification**

**1\. Purpose**

Budget Builder v2 exists to let users:

-   define and review **Budget Lines**
-   allocate budget at the **Budget Line** level
-   see the strategic context derived from each line
-   prepare the Budget module to support DIA cleanly

It replaces the old model of:

Budget → Program allocation

with:

Budget → Budget Lines → derived strategic linkage

**2\. Core design rule**

**Control unit**

The primary editable object in the builder is now:

Budget Line

Not:

-   Program
-   Strategic Plan
-   Target

Programs remain visible, but they are **derived / grouping context**, not the allocation unit.

**3\. Route and header**

**Route**

Keep the same builder route pattern if already implemented.

Example:

/desk/budget-builder/<budget\_id>

**Header layout**

Left:

-   Breadcrumb: Budget Management / Budget Builder
-   Title: Budget Builder
-   Subtitle: selected budget name, e.g. FY2027 Budget
-   Status badge: Draft / Submitted / Approved / Rejected

Right:

-   Back to Budgets

**Status banner**

Directly below the header, show a state-aware banner when applicable.

Examples:

-   Draft: no banner required
-   Submitted: This budget is submitted and awaiting approval.
-   Approved: This budget is approved and locked.
-   Rejected: This budget was rejected and requires revision.

**4\. Top summary strip**

Keep the summary cards. They are good and should remain.

**Required cards**

-   Total Budget
-   Allocated
-   Remaining

**Optional but recommended cards**

-   Reserved
-   Available for Reservation

If reservation is not yet actively surfaced in UI, keep it out for now rather than showing fake zeroes everywhere.

**Formatting rules**

-   use proper currency formatting
-   no truncation
-   large numeric values
-   small labels

Example:

TOTAL BUDGET KES 9,000,000

ALLOCATED KES 6,000,000

REMAINING KES 3,000,000

**5\. Main layout**

Use a stable two-panel layout.

**Left panel**

**Budget Lines list**

**Right panel**

**Budget Line detail/editor**

Recommended width split:

-   Left: 35–40%
-   Right: 60–65%

This matches what is already working in your Budget and Strategy UIs.

**6\. Left panel — Budget Lines list**

**Panel title**

Use:

Budget Lines

Not:

-   Programs
-   Allocations

**Secondary controls**

At the top of the left panel, include:

-   \+ Add Budget Line (only in editable states)
-   optional filter/search if needed later

For now, keep it simple unless line counts become large.

**List row structure**

Each row must show:

**Required**

-   Budget Line Name
-   Budget Line Code
-   Allocated Amount
-   Allocation state badge

**Optional but recommended**

-   Program name as muted secondary text

**Example**

Medical Equipment Capex

BL-MOH-2026-001

Healthcare Access

KES 5,000,000 \[Allocated\]

Another:

Rural Facility Expansion

BL-MOH-2027-001

Healthcare Access

KES 0 \[Unallocated\]

**Visual states**

-   selected row has clear highlight and border
-   unallocated lines visually distinguishable but not alarming
-   if approved budget is read-only, rows are still selectable

**Empty state**

If no budget lines exist yet:

-   show message:  
    No budget lines yet. Add a budget line to begin.
-   show Add Budget Line CTA if editable

**7\. Right panel — Budget Line editor/detail**

This replaces the old Program Allocation editor.

**Panel title**

Use the selected line name as title.

Example:

Medical Equipment Capex

**Section structure**

The right panel should be divided into clean sections.

**Section A — Budget Line Definition**

Fields:

-   Budget Line Name
-   Budget Line Code
-   Allocated Amount
-   Notes

**Section B — Strategic Context**

Read-only or derived fields:

-   Strategic Plan
-   Program
-   Sub-program
-   Output Indicator
-   Performance Target

**Section C — Financial Context**

Fields:

-   Parent Budget
-   Currency
-   Funding Source
-   Reserved Amount
-   Available Amount

**Section D — Status / Metadata**

Fields:

-   Active / Inactive
-   Created / Updated metadata if useful

Do not overload this section.

**8\. Field behavior**

**Editable fields in Draft / Rejected**

-   Budget Line Name
-   Budget Line Code
-   Allocated Amount
-   Notes
-   Funding Source
-   Active/Inactive if appropriate
-   Strategic linkage fields only if your design requires manual mapping during line creation

**Derived or read-only**

-   Parent Budget
-   Currency
-   Strategic Plan
-   Program
-   Sub-program
-   Indicator
-   Target
-   Reserved Amount
-   Available Amount

**Locked states**

In Submitted / Approved:

-   all editing disabled
-   no save button
-   Add Budget Line hidden
-   list remains navigable
-   detail remains readable

**9\. Add Budget Line interaction**

**Recommended pattern**

Use a **modal** for initial line creation, then show full details in the right panel after creation.

That keeps the main builder clean.

**Modal fields**

Required:

-   Budget Line Name
-   Budget Line Code
-   Allocated Amount
-   Funding Source
-   Strategic linkage anchor

**Strategic linkage entry**

Because this is still the budget side, you have two acceptable options:

**Option A — Manual strategy selection at creation**

-   Program
-   Sub-program
-   Output Indicator
-   Performance Target

**Option B — Select target or controlled strategic node and derive upwards**

Given your earlier concerns about deep target selection for broad operational users, **Option A with progressive hierarchy** is better here too.

**Modal actions**

-   Create Budget Line
-   Cancel

After creation:

-   select the new line in the left panel
-   show it in the right panel

**10\. Save behavior**

**Draft / Rejected**

Show:

-   Save Budget Line
-   Delete Budget Line if allowed and safe

**Submitted / Approved**

Hide save/delete actions entirely

**Validation**

Inline validation required for:

-   missing code
-   missing name
-   allocated amount < 0
-   duplicate budget line code within budget
-   invalid strategy mapping

**11\. Totals and allocation logic**

**Builder-level calculations**

The builder must compute:

Allocated = sum(amount\_allocated across active budget lines)

Remaining = Total Budget - Allocated

**Rules**

-   allocated total must not exceed total budget
-   if user edits a line such that total exceeds budget, block save and show clear error
-   if total budget is fully allocated, remaining = 0
-   unallocated lines with 0 remain valid if your model allows defining lines before assigning full amounts

**12\. Program visibility after refactor**

Programs do not disappear entirely.

They remain useful in two places:

**A. As secondary context in left list**

Each line can show its Program beneath the line name/code.

**B. As derived read-only strategic context in right panel**

But **Programs are no longer the thing the user edits or allocates against**.

That is the critical shift.

**13\. Landing page impact**

Your Budget landing page should also reflect this shift.

**Update Structure section**

Replace:

-   Programs
-   Allocated programs
-   Unallocated programs

With:

-   Budget Lines
-   Allocated lines
-   Unallocated lines

**Optional detail panel addition**

Add a small “Top Budget Lines” summary:

-   top 3–5 lines by amount

This helps users understand the budget composition before entering the builder.

**14\. Approval flow impact**

The budget approval flow still stands, but its lock target changes.

**Before**

Approval locked program allocations.

**Now**

Approval locks:

-   Budget Lines
-   line amounts
-   line definitions

That means:

-   no edits to allocated amounts after submission/approval
-   DIA can trust budget lines as stable control units

**15\. Relationship to DIA**

This refactor is specifically what enables DIA to work properly.

**DIA will now select**

Budget Line

and derive:

-   Budget
-   Strategy context
-   available amount

**Therefore the builder must ensure**

every active line has:

-   unique code
-   stable name
-   amount
-   strategy linkage
-   funding context if applicable

Without that, DIA will become messy and ambiguous.

**16\. What should be removed from current UI**

Remove or replace these patterns from the current builder:

**Remove**

-   Programs as primary left panel title
-   Program as primary editable field
-   program allocation editing as the main workflow

**Replace with**

-   Budget Lines
-   Budget Line definition/editor
-   program shown only as derived context

**17\. Minimal migration strategy**

Do not destroy the current UI in one shot.

**Step 1**

Introduce Budget Line model and map existing program allocations to seeded/default lines.

**Step 2**

Change builder left list from Programs → Budget Lines

**Step 3**

Change right editor from Program Allocation → Budget Line Detail

**Step 4**

Update landing page summaries from program counts → budget line counts

**Step 5**

Retire old program-allocation editing logic

**18\. Acceptance criteria**

Budget Builder v2 is correct only if:

-   left panel is Budget Lines, not Programs
-   right panel edits Budget Line, not Program allocation
-   strategic context is visible per line
-   totals derive from Budget Lines
-   total allocated cannot exceed budget total
-   approval locks Budget Lines
-   landing page reflects line-based structure
-   DIA can later consume Budget Lines without ambiguity

**19\. Cursor-ready prompt**

Refactor the current Budget Builder to align with the Budget Line control model.

This is a targeted refactor, not a full redesign.

Current problem:

-   the builder is program-allocation-centric
-   DIA now requires Budget Lines as the atomic control unit

Required changes:

1.  Replace the left panel title and list from:

-   Programs  
    to:
-   Budget Lines

1.  Replace the primary editable object from:

-   Program allocation  
    to:
-   Budget Line

1.  Left panel rows must show:

-   Budget Line Name
-   Budget Line Code
-   Allocated Amount
-   Allocation state
-   Program as secondary read-only context

1.  Right panel must be restructured into sections:

-   Budget Line Definition
-   Strategic Context
-   Financial Context
-   Status / Metadata

1.  Keep summary cards:

-   Total Budget
-   Allocated
-   Remaining

1.  Update all builder calculations so:

-   allocated total = sum of budget line amounts
-   remaining = total budget - allocated
-   saving is blocked if allocated total exceeds total budget

1.  In submitted/approved states:

-   hide edit/add/save actions
-   keep list/detail readable
-   show lock banner

1.  Update Budget landing page structure summary from:

-   Programs / Allocated programs / Unallocated programs  
    to:
-   Budget Lines / Allocated lines / Unallocated lines

1.  Do not keep both program allocation editing and budget line editing.  
    Programs must become grouping/derived context only.
2.  Preserve the existing ERP-grade look and feel:

-   clean cards
-   master-detail layout
-   no grey slab overload
-   clear back navigation

At the end, report:

-   files changed
-   migrated UI elements
-   assumptions made about existing program allocation data
-   any leftover legacy program-allocation behavior that still needs removal

# Budget Control Smoke Contract v1

**Budget Control Smoke Contract v1**

**1\. Purpose**

This smoke contract verifies that the Budget extension layer correctly supports:

-   Budget Line as the operational control unit
-   strategy derivation from Budget Line
-   budget sufficiency checks
-   reservation creation
-   reservation release
-   balance integrity

It exists to answer one question:

Can DIA safely rely on Budget without duplicating financial control logic?

If this contract fails, DIA Phase C must not proceed.

**2\. Scope**

**Included**

-   Budget Line data integrity
-   Budget Line selector/context behavior
-   balance calculations
-   budget sufficiency checks
-   reservation creation
-   duplicate reservation protection
-   reservation release
-   lock/restriction behavior relevant to control integrity

**Excluded**

-   full Budget landing page
-   full Budget approval flow
-   Procurement Planning
-   GL/accounting
-   payment or commitment accounting
-   downstream procurement consumption beyond DIA support

**3\. Required dependencies**

These tests assume the following are present:

-   Budget module installed and working
-   Budget Line domain model implemented
-   Budget Reservation domain model implemented
-   Budget control service layer implemented
-   Budget line seed support implemented

Recommended upstream seeds:

-   seed\_core\_minimal
-   seed\_strategy\_basic
-   seed\_budget\_basic
-   seed\_budget\_extended
-   budget-line extension seed

**4\. Required seeded Budget Lines**

At minimum, these lines must exist:

| **Budget Line Code** | **Name** | **Budget** | **Allocated** | **Reserved** | **Consumed** | **Available** |
| --- | --- | --- | --- | --- | --- | --- |
| BL-MOH-2026-001 | Medical Equipment Capex | FY2026 Budget | 5000000 | 0 | 0 | 5000000 |
| BL-MOH-2026-002 | Clinical Workforce Training | FY2026 Budget | 3000000 | 0 | 0 | 3000000 |
| BL-MOH-2027-001 | Rural Facility Expansion | FY2027 Budget | 9000000 | 0 | 0 | 9000000 |

Each seeded line must also include valid strategic linkage.

**5\. Core invariants to prove**

The smoke contract must prove all of these:

**Budget Line invariants**

-   amount\_allocated >= 0
-   amount\_reserved >= 0
-   amount\_consumed >= 0
-   amount\_available = amount\_allocated - amount\_reserved - amount\_consumed
-   amount\_reserved + amount\_consumed <= amount\_allocated

**Reservation invariants**

-   reservation amount > 0
-   one active reservation per source record
-   released reservations are not counted in active reserved total
-   Budget Line balances stay in sync with reservation lifecycle

**6\. Recommended test structure**

tests/budget\_control/

test\_budget\_line\_context.py

test\_budget\_availability.py

test\_budget\_reservations.py

test\_budget\_control\_permissions.py

If you prefer UI-plus-service coverage later, keep this contract backend-first for now.

**7\. Core smoke scenarios**

**BC1 — Budget Line context loads correctly**

**Purpose**

Verify Budget Line can act as DIA’s operational anchor.

**Preconditions**

-   seeded Budget Line exists

**Action**

Call:

get\_budget\_line\_context("BL-MOH-2026-001")

**Expected**

Response includes:

-   budget\_line\_code
-   budget\_line\_name
-   budget
-   procuring\_entity
-   fiscal\_year
-   currency
-   funding\_source if present
-   strategic\_plan
-   program
-   sub\_program if supported
-   output\_indicator if supported
-   performance\_target if supported
-   amount\_allocated
-   amount\_reserved
-   amount\_consumed
-   amount\_available
-   is\_active

**Pass condition**

Returned data is complete and consistent.

**BC2 — Inactive Budget Line cannot be exposed downstream**

**Purpose**

Verify DIA cannot consume inactive lines.

**Preconditions**

-   one inactive Budget Line exists or temporarily mark one inactive in test setup

**Action**

Call:

get\_budget\_line\_context(inactive\_line\_id)

**Expected**

-   service returns error
-   error code:
    -   BUDGET\_LINE\_INACTIVE

**Pass condition**

Inactive lines are blocked for downstream use.

**BC3 — Available budget calculation is correct**

**Purpose**

Verify authoritative balance calculation.

**Preconditions**

-   seeded Budget Line with known values

**Action**

Call:

get\_available\_budget("BL-MOH-2026-001")

**Expected**

If allocated = 5000000, reserved = 0, consumed = 0:

-   available = 5000000

**Pass condition**

Returned values reconcile exactly.

**BC4 — Budget sufficiency check succeeds when funds are enough**

**Purpose**

Verify positive budget check path.

**Preconditions**

-   available amount = 5000000

**Action**

Call:

check\_available\_budget("BL-MOH-2026-001", 3000000)

**Expected**

-   ok = true
-   is\_sufficient = true
-   shortfall = 0

**Pass condition**

Sufficiency is correctly reported.

**BC5 — Budget sufficiency check fails when funds are insufficient**

**Purpose**

Verify negative budget check path.

**Preconditions**

-   available amount = 3000000

**Action**

Call:

check\_available\_budget("BL-MOH-2026-002", 3500000)

**Expected**

-   ok = true
-   is\_sufficient = false
-   shortfall = 500000

**Pass condition**

Shortfall is computed correctly.

**BC6 — Cannot check invalid amount**

**Purpose**

Verify defensive validation.

**Action**

Call:

check\_available\_budget("BL-MOH-2026-001", 0)

and

check\_available\_budget("BL-MOH-2026-001", -100)

**Expected**

-   error response
-   error\_code = INVALID\_AMOUNT

**Pass condition**

Non-positive amounts are rejected.

**BC7 — Create reservation successfully**

**Purpose**

Verify full reservation creation flow.

**Preconditions**

-   BL-MOH-2026-001 available = 5000000
-   no active reservation exists for source:
    -   source\_doctype = Demand
    -   source\_docname = DIA\_TEST\_0001

**Action**

Call:

create\_reservation(

budget\_line\_id="BL-MOH-2026-001",

source\_doctype="Demand",

source\_docname="DIA\_TEST\_0001",

source\_business\_id="DIA-MOH-2026-TEST1",

amount=3000000,

actor="finance.reviewer@moh.test"

)

**Expected**

-   reservation created
-   status = Active
-   reservation\_id returned
-   available\_before\_reservation = 5000000
-   available\_after\_reservation = 2000000
-   Budget Line:
    -   amount\_reserved = 3000000
    -   amount\_available = 2000000

**Pass condition**

Reservation and Budget Line balances both update correctly.

**BC8 — Reservation creation is blocked if insufficient funds**

**Purpose**

Verify reservation service re-checks sufficiency itself.

**Preconditions**

-   available amount < requested amount

**Action**

Call:

create\_reservation(... amount=6000000 ...)

**Expected**

-   error response
-   error\_code = INSUFFICIENT\_BUDGET
-   no reservation created
-   Budget Line balances unchanged

**Pass condition**

Reservation cannot be created beyond availability.

**BC9 — Duplicate active reservation for same source is blocked**

**Purpose**

Prevent double-reservation drift.

**Preconditions**

-   active reservation already exists for:
    -   source\_doctype = Demand
    -   source\_docname = DIA\_TEST\_0001

**Action**

Call create\_reservation(...) again for same source.

**Expected**

-   error response
-   error\_code = DUPLICATE\_ACTIVE\_RESERVATION
-   Budget Line balances unchanged

**Pass condition**

Only one active reservation per source record exists.

**BC10 — Release reservation successfully**

**Purpose**

Verify reservation release lifecycle.

**Preconditions**

-   active reservation exists for DIA\_TEST\_0001
-   amount = 3000000
-   Budget Line reserved = 3000000
-   Budget Line available = 2000000

**Action**

Call:

release\_reservation(

reservation\_id="RSV-MOH-2026-0001",

reason="DIA demand cancelled",

actor="finance.reviewer@moh.test"

)

**Expected**

-   reservation status = Released
-   released\_at set
-   released\_by set
-   release\_reason stored
-   Budget Line:
    -   amount\_reserved = 0
    -   amount\_available = 5000000

**Pass condition**

Release updates both reservation and line balances correctly.

**BC11 — Cannot release non-active reservation**

**Purpose**

Prevent double-release corruption.

**Preconditions**

-   reservation already released

**Action**

Call release\_reservation(...) again.

**Expected**

-   error response
-   error\_code = RESERVATION\_NOT\_ACTIVE
-   balances unchanged

**Pass condition**

Released reservations cannot be released twice.

**BC12 — Release requires reason**

**Purpose**

Verify audit-quality release behavior.

**Preconditions**

-   active reservation exists

**Action**

Call:

release\_reservation(reservation\_id, "", actor)

**Expected**

-   error response
-   error\_code = RELEASE\_REASON\_REQUIRED

**Pass condition**

Release without reason is blocked.

**BC13 — Get active reservation for source**

**Purpose**

Verify DIA can look up authoritative reservation state.

**Preconditions**

-   active reservation exists for source record

**Action**

Call:

get\_active\_reservation\_for\_source("Demand", "DIA\_TEST\_0001")

**Expected**

-   reservation\_id returned
-   status = Active
-   amount returned
-   budget\_line\_code returned

**Pass condition**

Source-to-reservation lookup works.

**BC14 — No active reservation found returns clean null result**

**Purpose**

Verify safe lookup behavior when none exists.

**Preconditions**

-   no active reservation for source

**Action**

Call:

get\_active\_reservation\_for\_source("Demand", "NON\_EXISTENT\_SOURCE")

**Expected**

-   success response
-   reservation\_id = null
-   status = null

**Pass condition**

No false positives or exceptions for missing active reservation.

**BC15 — Reservation history by Budget Line**

**Purpose**

Verify lightweight inspection/reporting path.

**Preconditions**

-   one or more reservations exist for a Budget Line

**Action**

Call:

list\_reservations\_for\_budget\_line("BL-MOH-2026-001")

**Expected**

-   list returned
-   includes active and/or released reservation entries
-   ordered predictably (recommended: newest first)

**Pass condition**

History is readable and linked correctly.

**BC16 — Budget Line financial invariants remain valid after create/release cycle**

**Purpose**

Verify no drift in roll-up balances.

**Preconditions**

-   perform one or more create/release cycles in test

**Action**

At the end of the cycle, assert:

-   amount\_reserved >= 0
-   amount\_consumed >= 0
-   amount\_available = allocated - reserved - consumed
-   reserved + consumed <= allocated

**Pass condition**

All invariants hold after repeated operations.

**8\. Optional integration-adjacent scenarios**

These are recommended, especially before resuming DIA.

**BC17 — Source reference stored correctly on reservation**

Verify:

-   source\_doctype
-   source\_docname
-   source\_business\_id  
    are persisted exactly.

**BC18 — Reservation creation respects inactive Budget Line block**

Try to reserve against inactive line and verify:

-   BUDGET\_LINE\_INACTIVE

**BC19 — Reservation create/release leaves audit trail intact**

Verify that create/release metadata survives retrieval.

**9\. Error code coverage**

The smoke suite should explicitly cover these error codes:

-   BUDGET\_LINE\_NOT\_FOUND
-   BUDGET\_LINE\_INACTIVE
-   BUDGET\_LINE\_INVALID
-   INVALID\_AMOUNT
-   INSUFFICIENT\_BUDGET
-   DUPLICATE\_ACTIVE\_RESERVATION
-   RESERVATION\_NOT\_FOUND
-   RESERVATION\_NOT\_ACTIVE
-   RELEASE\_REASON\_REQUIRED

You do not necessarily need one dedicated test per code if some scenarios cover multiple correctly and explicitly.

**10\. Minimal acceptance gate**

Do **not** resume DIA Phase C unless all of these pass:

-   Budget Line context loads correctly
-   Available balance computes correctly
-   Sufficiency check succeeds/fails correctly
-   Reservation can be created
-   Duplicate active reservation is blocked
-   Reservation can be released
-   Release restores balances correctly
-   Core financial invariants hold after operations

That is the actual “Budget is authoritative” gate.

**11\. Cursor-ready implementation prompt**

Implement the Budget Control smoke suite exactly as specified.

This is not the full Budget module test suite.  
It is the control-layer test suite required before DIA resumes integration.

Create tests covering:

1.  Budget Line context load
2.  Inactive Budget Line blocked
3.  Available budget calculation
4.  Budget sufficiency success
5.  Budget sufficiency failure
6.  Invalid amount blocked
7.  Reservation creation success
8.  Reservation creation blocked for insufficient funds
9.  Duplicate active reservation blocked
10.  Reservation release success
11.  Release blocked for non-active reservation
12.  Release reason required
13.  Active reservation lookup by source
14.  Clean null result when no active reservation exists
15.  Reservation history listing
16.  Financial invariants after reservation lifecycle

Requirements:

-   use deterministic seeded Budget Lines
-   verify both service responses and resulting Budget Line state
-   do not add unrelated Budget UI tests
-   keep tests backend-focused and stable

At the end report:

1.  test files created
2.  seed assumptions used
3.  any gaps that still block DIA Phase C
4.  whether Budget can now be treated as authoritative for DIA

**Recommended next step**

Once this smoke contract passes, the right sequence is:

Budget control layer green

→ Budget Builder v2 refactor

→ Resume DIA Phase C