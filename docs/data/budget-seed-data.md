Budget Seed Data Specification v1.

Goal:  
Provide deterministic, idempotent seed data for the Budget module so the landing page, builder, and Playwright smoke tests can run against realistic records.

Dependencies:

-   Assume these already exist:
    -   seed\_core\_minimal
    -   seed\_strategy\_basic
-   Budget seed must link to existing Strategy records, not create duplicate Strategy data

Create these seed packs:

1.  seed\_budget\_empty
2.  seed\_budget\_basic
3.  seed\_budget\_extended

General rules:

1.  Seed logic must be idempotent
    -   create if missing
    -   update if exists
    -   never duplicate
2.  Use exact names and values from this spec
3.  Do not create random or placeholder records
4.  Do not include procurement, accounting, ERPNext Budget, or GL-related seed data
5.  Keep all amounts in KES
6.  All budgets belong to Procuring Entity:
    -   MOH
7.  All budgets must link to Strategic Plan:
    -   MOH Strategic Plan 2026–2030

Required records and values:

**PACK 1: seed\_budget\_empty**

Purpose:

-   support empty-state testing

Behavior:

-   ensure no Budget records exist
-   do not delete Strategy seed data
-   do not create any Budget or Budget Allocation records

Expected UI result:

-   Budget landing page shows:  
    "No budgets yet. Create one to begin."

**PACK 2: seed\_budget\_basic**

Purpose:

-   support single-budget populated testing
-   support builder testing
-   support totals validation

Create Budget 1 with these exact values:

Budget:

-   budget\_name: FY2026 Budget
-   procuring\_entity: MOH
-   fiscal\_year: 2026
-   strategic\_plan: MOH Strategic Plan 2026–2030
-   currency: KES
-   total\_budget\_amount: 8000000
-   status: Draft
-   version\_no: 1
-   is\_current\_version: 1
-   supersedes\_budget: null
-   notes: Initial budget aligned to MOH strategic plan priorities

Create these Budget Allocations for FY2026 Budget:

Allocation 1:

-   program: Healthcare Access
-   amount: 5000000
-   notes: Expansion of rural healthcare coverage and facilities
-   order\_index: 1

Allocation 2:

-   program: Workforce Development
-   amount: 3000000
-   notes: Workforce training and recruitment
-   order\_index: 2

Derived expectations for FY2026 Budget:

-   total\_budget\_amount = 8000000
-   allocated\_amount = 8000000
-   remaining\_amount = 0
-   program\_count = 2
-   allocated\_program\_count = 2
-   unallocated\_program\_count = 0

Expected builder state:

-   Healthcare Access shows allocated amount 5000000
-   Workforce Development shows allocated amount 3000000

**PACK 3: seed\_budget\_extended**

Purpose:

-   support multi-budget testing
-   support partial allocation testing
-   support selection behavior on landing page

This pack must include everything from seed\_budget\_basic, PLUS add Budget 2.

Create Budget 2 with these exact values:

Budget:

-   budget\_name: FY2027 Budget
-   procuring\_entity: MOH
-   fiscal\_year: 2027
-   strategic\_plan: MOH Strategic Plan 2026–2030
-   currency: KES
-   total\_budget\_amount: 9000000
-   status: **Submitted** (after `seed_budget_extended` runs; B5.6 approval-flow coverage — FY2026 from basic pack stays **Draft**)
-   version\_no: 1
-   is\_current\_version: 1
-   supersedes\_budget: null
-   notes: Adjusted allocations for following fiscal year

Create these Budget Allocations for FY2027 Budget:

Allocation 1:

-   program: Healthcare Access
-   amount: 6000000
-   notes: Increased infrastructure investment
-   order\_index: 1

Do NOT create an allocation for:

-   Workforce Development

Derived expectations for FY2027 Budget:

-   total\_budget\_amount = 9000000
-   allocated\_amount = 6000000
-   remaining\_amount = 3000000
-   program\_count = 2
-   allocated\_program\_count = 1
-   unallocated\_program\_count = 1

Expected builder state:

-   Healthcare Access shows allocated amount 6000000
-   Workforce Development shows "Not allocated"

**LOOKUP / LINKING RULES**

When creating Budget records:

-   link Procuring Entity by exact name/code: MOH
-   link Strategic Plan by exact name/title: MOH Strategic Plan 2026–2030

When creating Budget Allocations:

-   link Programs by exact titles:
    -   Healthcare Access
    -   Workforce Development

Do not create duplicate Programs or Strategic Plans.  
Always resolve and reuse existing Strategy seed records.

**VALIDATION EXPECTATIONS**

Seed data must satisfy:

1.  Allocation.program.strategic\_plan == Budget.strategic\_plan
2.  Allocation amounts > 0
3.  One allocation per (budget, program)
4.  Total allocations must not exceed total\_budget\_amount

**IMPLEMENTATION LOCATION**

Use a controlled seed structure such as:

kentender\_core/seeds/

-   seed\_budget\_empty.py
-   seed\_budget\_basic.py
-   seed\_budget\_extended.py

If there is already a shared seed runner pattern, follow it.

Preferred callable entrypoints:

-   run()  
    for each seed file

Optional shared wrapper:

-   run\_pack(pack\_name)

**COMMANDS TO SUPPORT**

The implementation should make it easy to run:

-   bench execute kentender\_core.seeds.seed\_budget\_empty.run
-   bench execute kentender\_core.seeds.seed\_budget\_basic.run
-   bench execute kentender\_core.seeds.seed\_budget\_extended.run

If a different command pattern is already established, keep it consistent and document it.

**ACCEPTANCE CRITERIA**

The implementation is correct only if:

1.  seed\_budget\_empty results in zero Budget records
2.  seed\_budget\_basic creates exactly one Budget:
    -   FY2026 Budget
3.  seed\_budget\_extended creates exactly two Budgets:
    -   FY2026 Budget
    -   FY2027 Budget
4.  Budget Allocations match the exact amounts and programs defined above
5.  Re-running any seed pack does not create duplicates
6.  Landing page can use these records directly
7.  Builder can use these records directly
8.  No procurement or accounting seed records are introduced

At the end provide:

1.  files created
2.  seed entrypoints
3.  idempotency strategy used
4.  exact commands to run each pack
5.  any assumptions made about lookup keys for Strategic Plan / Program records