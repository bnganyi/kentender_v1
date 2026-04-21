Good—this is the last piece that prevents subtle breakage later.

Below is a **strict, Cursor-ready roles & permissions prompt** for the Budget module.  
It is aligned to:

-   your domain model
-   your landing + builder UX
-   your seed data
-   your smoke tests

No ambiguity.

**🔐 Budget Module — Roles & Permissions (Cursor Prompt)**

Implement roles and permissions for the Budget module.

Goal:  
Ensure correct visibility and edit control for Budget and Budget Allocation, aligned with Strategy module roles.

Do NOT:

-   introduce new roles
-   modify Strategy role definitions
-   add workflow/approval states
-   rely only on UI hiding (must enforce backend permissions)

**ROLES (use existing)**

Use these existing roles:

1.  Strategy Manager
2.  Planning Authority
3.  Requisitioner
4.  Administrator (implicit full access)

Do NOT create new roles.

**PERMISSION MODEL**

DocTypes:

-   Budget
-   Budget Allocation

Permissions must be defined at BOTH:

1.  DocType level (Frappe permissions)
2.  Backend validation level (server-side enforcement)
3.  STRATEGY MANAGER (full access)

Capabilities:

-   View Budget workspace
-   Create Budget
-   Edit Budget
-   Delete Budget (optional but allowed in v1)
-   Open Budget Builder
-   Create / edit Budget Allocations

DocType permissions:

Budget:

-   read: yes
-   write: yes
-   create: yes
-   delete: yes

Budget Allocation:

-   read: yes
-   write: yes
-   create: yes
-   delete: yes

1.  PLANNING AUTHORITY (read-only)

Capabilities:

-   View Budget workspace
-   View Budget details
-   Open Budget Builder (read-only mode)
-   Cannot create or edit anything

DocType permissions:

Budget:

-   read: yes
-   write: no
-   create: no
-   delete: no

Budget Allocation:

-   read: yes
-   write: no
-   create: no
-   delete: no

UI requirements:

-   hide:
    -   New Budget button
    -   Edit Budget button
    -   Save Allocation button
-   builder must render but inputs must be disabled

1.  REQUISITIONER (no access)

Capabilities:

-   Must NOT see Budget module at all

Requirements:

-   Budget workspace icon NOT visible
-   direct URL access must be blocked
-   no API access to Budget data

DocType permissions:

Budget:

-   read: no
-   write: no
-   create: no
-   delete: no

Budget Allocation:

-   read: no
-   write: no
-   create: no
-   delete: no

1.  ADMINISTRATOR

Capabilities:

-   full access (default behavior)

**ENTITY-LEVEL CONSTRAINT (important)**

All Budget records belong to a Procuring Entity.

Enforce:

-   users can only see Budgets for their permitted Procuring Entity

For v1:

-   if no multi-entity system exists yet, assume all users operate under same entity (MOH)

BUT:

-   structure code so entity filtering can be added later

**BACKEND ENFORCEMENT (critical)**

Do NOT rely only on UI.

Implement server-side checks:

1.  Budget write protection

-   if user is Planning Authority:  
    reject any write/create/delete

1.  Budget Allocation write protection

-   same rule as above

1.  Cross-entity safety (future-proof)

-   validate that user has access to the Budget’s procuring\_entity

**UI VISIBILITY RULES**

Landing page:

Strategy Manager:

-   sees everything

Planning Authority:

-   sees list + detail
-   cannot see:
    -   "New Budget"
    -   "Edit Budget"

Requisitioner:

-   sees nothing

Builder:

Strategy Manager:

-   full interaction

Planning Authority:

-   can open builder
-   cannot edit:
    -   disable inputs
    -   hide Save button

Requisitioner:

-   cannot access route

**ROUTE PROTECTION**

Protect these routes:

-   /desk/budget-management
-   /desk/budget-builder/

Rules:

-   Strategy Manager → allow
-   Planning Authority → allow (read-only)
-   Requisitioner → deny (redirect or 403)

**TEST EXPECTATIONS (must support Playwright)**

Ensure the following can be tested:

1.  Strategy Manager

-   can see create button
-   can open builder
-   can save allocation

1.  Planning Authority

-   cannot see create button
-   cannot edit
-   builder loads but is read-only

1.  Requisitioner

-   cannot see Budget workspace
-   cannot access URL

**ACCEPTANCE CRITERIA**

Implementation is correct if:

1.  Strategy Manager can fully manage budgets
2.  Planning Authority can view but not edit
3.  Requisitioner cannot access Budget module at all
4.  Backend prevents unauthorized writes
5.  UI reflects permissions correctly
6.  Direct API or route access cannot bypass restrictions

**RETURN OUTPUT**

At the end, provide:

1.  DocType permission configuration (Budget, Budget Allocation)
2.  backend enforcement logic locations
3.  UI elements conditionally hidden/disabled
4.  route protection implementation
5.  any assumptions about role assignment

**🧠 Why this matters (brief but important)**

Without this:

-   your UI looks correct
-   but users can still mutate data via API or edge paths
-   or see modules they shouldn’t

👉 That’s how systems silently break in production

**✅ Where you are now**

You have:

✔ Strategy (UX + model + seeds + roles)  
✔ Budget (UX + model + seeds + roles + tests ready)

This is now a **real platform foundation**, not a prototype.