**📘 Strategy Module — Implementation Sequence (Controlled Build Plan)**

**🎯 Core Principle**

Build thin vertical slices, not wide partial systems

Each phase must result in something:

- usable
- testable
- stable

**🧩 Phase 0 — Environment & Baseline (MANDATORY)**

**Goal**

Create a stable foundation before any feature work.

**Tasks**

- Create fresh app / module: strategy
- Define clean namespace (no leftover code)
- Create test site / database
- Set up minimal roles:
    - Strategy Manager
    - Planning Authority
- Ensure login works
- Confirm navigation can be modified safely

**Deliverable**

User can log in and see a placeholder Strategy workspace

**Sanity Check**

- No console errors
- No broken routes
- Clean app boot

🚫 Do NOT create data models yet

**🧩 Phase 1 — Workspace & Navigation**

**Goal**

Make Strategy discoverable and navigable.

**Tasks**

- Create **Strategy Management workspace**
- Add to sidebar/menu
- Add:
    - “New Strategic Plan” button
    - empty plan list placeholder

**Deliverable**

User can navigate:

Menu → Strategy → Workspace

**Sanity Check**

- Workspace opens reliably
- No need for search (CTRL+K)
- Buttons visible and clickable

🚫 Do NOT implement full forms yet

**🧩 Phase 2 — Strategic Plan (Core Entity Only)**

**Goal**

Create and persist Strategic Plan (header only)

**Tasks**

- Implement Strategic Plan DocType / model
- Minimal fields:
    - plan_name
    - entity
    - period_start
    - period_end
    - workflow_state (Draft only)
- Create simple create/save UI

**Deliverable**

User can create and save a Strategic Plan (Draft)

**Sanity Check**

- Save works
- Reload works
- Plan appears in list

🚫 No Programs yet  
🚫 No workflow transitions yet

**🧩 Phase 3 — Step-Based Builder Skeleton**

**Goal**

Replace raw form with guided UX

**Tasks**

- Implement Plan Workspace view
- Add:
    - Header
    - Progress bar
    - Step navigation

Steps visible (empty):

- Plan Info
- Programs
- Sub-programs
- Indicators
- Targets
- Review

**Deliverable**

User can open a plan and see step-based builder UI

**Sanity Check**

- Steps clickable
- Next/Back works
- No long scrolling form

🚫 No data tables yet  
🚫 No validation yet

**🧩 Phase 4 — Program Layer**

**Goal**

Implement first level of hierarchy

**Tasks**

- Create Program model
- Add Program table to Programs step
- Add modal:
    - program_code
    - program_name
    - national_objective_ref
- Implement CRUD

**Deliverable**

User can add/edit/delete Programs inside a plan

**Sanity Check**

- Program persists after reload
- Table updates correctly
- No orphan Program possible

🚫 No Sub-program yet

**🧩 Phase 5 — Sub-program Layer**

**Goal**

Extend hierarchy one level deeper

**Tasks**

- Create Sub-program model
- Add Sub-program table
- Link to Program (dropdown)
- Add filter by Program

**Deliverable**

User can add Sub-programs linked to Programs

**Sanity Check**

- Cannot create Sub-program without Program
- Parent linkage always visible
- Filter works

🚫 No Indicators yet

**🧩 Phase 6 — Indicator Layer**

**Goal**

Add measurable layer

**Tasks**

- Create Output Indicator model
- Add Indicator table
- Fields:
    - indicator_code
    - name
    - unit
    - baseline
- Link to Sub-program

**Deliverable**

User can add Indicators linked to Sub-programs

**Sanity Check**

- Cannot create Indicator without Sub-program
- Unit required
- Data persists

🚫 No Targets yet

**🧩 Phase 7 — Target Layer**

**Goal**

Complete hierarchy

**Tasks**

- Create Performance Target model
- Add Target table
- Fields:
    - year
    - target_value
    - department
- Link to Indicator

**Deliverable**

User can create full hierarchy:

Program → Sub-program → Indicator → Target

**Sanity Check**

- Cannot create Target without Indicator
- Numeric validation works
- Time-series visible

**🧩 Phase 8 — Review & Validation Engine**

**Goal**

Make system self-checking

**Tasks**

- Implement Review step
- Show:
    - counts
    - validation issues
- Block submission if:
    - any level missing
    - orphan detected

**Deliverable**

User sees clear issues before submission

**Sanity Check**

- Missing items clearly listed
- Clicking issue leads to fix
- Cannot bypass validation

**🧩 Phase 9 — Workflow (Plan Only)**

**Goal**

Enable lifecycle control

**Tasks**

- Implement transitions:
    - Draft → Submitted
    - Submitted → Approved
    - Approved → Active
- Lock editing based on state

**Deliverable**

Plan moves through full lifecycle and locks correctly

**Sanity Check**

- Cannot edit after submission
- Cannot activate incomplete plan
- Status visible in header

**🧩 Phase 10 — Selector APIs (Downstream Readiness)**

**Goal**

Expose clean data to other modules

**Tasks**

Create endpoints:

- active programs
- active sub-programs
- active indicators
- active targets

**Deliverable**

Other modules can fetch strategy data cleanly

**Sanity Check**

- Only Active plan data returned
- No duplicates
- Clean labels

**🧩 Phase 11 — Smoke Tests**

**Goal**

Automate sanity

**Tasks**

- Implement:
    - workspace test
    - create plan test
    - hierarchy test
    - workflow test
    - selector test

**Deliverable**

All smoke tests pass consistently

**Sanity Check**

- Tests are deterministic
- No flaky behavior

**🧩 Phase 12 — UX Polish (ONLY NOW)**

**Goal**

Refine usability AFTER stability

**Tasks**

- Improve labels
- Improve spacing
- Improve minor interactions

**Deliverable**

UI feels smooth but behavior unchanged

🚫 Do NOT change logic here

**🚨 Hard Stop Rule**

Do not start next phase until current phase passes sanity checks

**🧠 Why this sequence works**

**Prevents:**

- premature complexity
- hidden bugs
- UI fragmentation
- dependency chaos

**Ensures:**

- each layer is stable
- hierarchy is enforced early
- UX evolves progressively
- debugging is localized

**💥 What will break you if you ignore this**

If Windsurf:

- adds indicators before sub-programs are stable
- adds workflow before validation works
- builds full UI before model stabilizes

👉 you will rebuild again

**🚀 Your next move**

Start with:

Phase 0 → Phase 1 → Phase 2

Stop there.

Test.

Then continue.

If you want, next I can give you:

👉 **Windsurf prompt pack for each phase (so it doesn’t overbuild or drift)**