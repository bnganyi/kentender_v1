\# KenTender Architecture Rules (Non-negotiable)



These rules govern all implementation across the KenTender platform.

If any rule is violated, the implementation is incorrect.



\---



\## 1. App Structure



Use only these apps:



\- kentender\_core

\- kentender\_strategy

\- kentender\_budget

\- kentender\_procurement

\- kentender\_governance

\- kentender\_compliance

\- kentender\_stores

\- kentender\_assets

\- kentender\_integrations



Do not create new apps or move responsibilities outside these.



\---



\## 2. Domain Ownership



Each app owns its domain. Do not mix responsibilities.



\- Strategy data ONLY in `kentender\_strategy`

\- Budget logic ONLY in `kentender\_budget`

\- Procurement lifecycle ONLY in `kentender\_procurement`

\- Shared infrastructure ONLY in `kentender\_core`



Do not duplicate or reimplement logic across apps.



\---



\## 3. Dependency Rules (Strict)



Allowed direction:



core → strategy → budget → procurement → stores → assets



Rules:



\- `kentender\_core` MUST NOT depend on any other app

\- `kentender\_strategy` MUST NOT depend on budget or procurement

\- `kentender\_budget` MUST NOT depend on procurement

\- Downstream apps MUST NOT push dependencies upstream

\- No deep cross-app imports (e.g. importing internal modules directly)



Cross-app interaction must use APIs or services only.



\---



\## 4. Implementation Structure



Each app MUST follow this structure:



\- doctype/ → data model + minimal validation only

\- services/ → ALL business logic

\- api/ → explicit endpoints only

\- tests/ → tests

\- utils/ → small helpers only



Rules:



\- DO NOT put business logic inside DocType controllers

\- DO NOT embed workflow logic in UI handlers

\- DO NOT create hidden coupling between modules



\---



\## 5. Business Logic Rules



\- All critical actions must go through service-layer functions

\- Examples:

&#x20; - submit\_plan()

&#x20; - approve\_plan()

&#x20; - create\_program()

&#x20; - reserve\_budget()



\- UI must call services, not implement logic itself



\---



\## 6. API Rules



Each app must expose:



\- selector APIs (for dropdowns)

\- CRUD APIs (only where needed)

\- business action APIs (submit, approve, etc.)



API rules:



\- responses must follow standard envelope:



Success:

{

&#x20; "ok": true,

&#x20; "data": {},

&#x20; "message": "Success"

}



Error:

{

&#x20; "ok": false,

&#x20; "error\_code": "ERROR\_CODE",

&#x20; "message": "Explanation"

}



\- DO NOT return large unnecessary payloads

\- DO NOT expose internal data structures



\---



\## 7. Data Rules



\- No free-text references to upstream data

\- All upstream data must be selected via selectors

\- Only ACTIVE records should be exposed downstream

\- Maintain strict parent-child hierarchy integrity

\- No orphan records allowed



\---



\## 8. Workflow Rules



\- Each major entity has its own workflow:

&#x20; - Strategic Plan

&#x20; - Budget

&#x20; - Purchase Requisition

&#x20; - etc.



\- DO NOT create cross-app workflows

\- DO NOT create hidden workflow states

\- Workflow transitions must be explicit and controlled



\---



\## 9. UX Architecture Rules



\- Workspace-first design (not DocType-first)

\- No long scrolling forms

\- Use step-based builders for complex processes

\- Tables for structured data

\- Modals/panels for data entry

\- User must always see:

&#x20; - where they are

&#x20; - what is next

&#x20; - what is missing



\---



\## 10. Cross-Cutting Controls (Core Only)



Only `kentender\_core` may implement:



\- numbering / business ID generation

\- audit logging

\- exception handling

\- file access control

\- entity scoping

\- permission helpers



Other apps must USE these, not reimplement them.



\---



\## 11. Forbidden Patterns



The following are NOT allowed:



\- business logic in DocType controllers

\- cross-app deep imports

\- duplicate services in multiple apps

\- long form-based UX for complex flows

\- hidden workflow transitions

\- free-text upstream references

\- mixing domain responsibilities



\---



\## 12. Enforcement Rule



If any implementation:



\- violates app ownership

\- breaks dependency direction

\- ignores service-layer pattern

\- breaks UX rules

\- introduces hidden coupling



→ It must be rejected and corrected.

