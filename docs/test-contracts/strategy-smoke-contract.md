**📘 Strategy Module — MVP Sanity Checklist + Smoke Test Contract**

**1\. Purpose**

The Strategy module is only considered **done for MVP** if it is:

- usable by the Strategy Manager
- understandable by the Planning Authority
- structurally correct
- stable after save/reload
- consumable by downstream modules

If any critical check fails, you do **not** move on.

**2\. MVP Sanity Checklist**

Use this as your hard gate.

**A. Navigation & Access**

**Must pass**

- Strategy workspace is visible from normal navigation
- User can open Strategy workspace without using search
- User can create a new Strategic Plan from the workspace
- User can open an existing Strategic Plan from the plan list
- No broken menu links
- No dead buttons

**Must not happen**

- hidden entry points
- reliance on CTRL+K
- raw DocType access as the only navigation path

**B. UX & Flow**

**Must pass**

- Plan opens into the step-based builder, not a long raw form
- Progress bar is visible at all times
- User can tell what step they are on
- User can move Next / Back without confusion
- Each step is focused and not overloaded
- No step requires scrolling through a giant page

**Must not happen**

- disconnected screens
- giant forms
- hidden required steps
- unclear next action

**C. Data Entry**

**Must pass**

- Strategy Manager can create:
    - 1 Strategic Plan
    - 1 Program
    - 1 Sub-program
    - 1 Indicator
    - 1 Target
- Add/Edit actions work via modal or controlled entry panel
- Parent relationships are always visible
- Required fields are obvious before save

**Must not happen**

- orphan records
- free-text hierarchy guessing
- unclear parent linkage

**D. Validation**

**Must pass**

- Cannot create Sub-program without Program
- Cannot create Indicator without Sub-program
- Cannot create Target without Indicator
- Cannot submit incomplete plan
- Validation messages are readable and specific

**Must not happen**

- vague “something went wrong”
- silent failures
- partial invalid save

**E. Workflow**

**Must pass**

- Strategic Plan can move:
    - Draft → Submitted
    - Submitted → Approved
    - Approved → Active
- Child records become non-editable after submission
- Active plan is read-only for ordinary users
- Archived plan is not selectable downstream

**Must not happen**

- extra undocumented statuses
- editing after activation
- workflow buttons missing or inconsistent

**F. Persistence & Stability**

**Must pass**

- Save → reload → data remains intact
- Switching steps does not lose entered data
- Refreshing page does not break builder state
- Counts/summaries update correctly

**Must not happen**

- disappearing rows
- broken child links after reload
- duplicate creation from repeated clicks

**G. Downstream Readiness**

**Must pass**

- Active Programs can be fetched via selector API
- Active Sub-programs can be fetched
- Active Indicators can be fetched
- Active Targets can be fetched
- Draft / Submitted / Archived items are not exposed to downstream selectors

**Must not happen**

- inactive data visible in downstream dropdowns
- missing selector endpoints
- duplicate or unreadable option labels

**H. Usability Threshold**

**Must pass**

A Strategy Manager should be able to create a minimal full hierarchy in:

< 10 minutes without explanation

A Planning Authority should be able to:

open plan → review summary → approve

without needing to inspect every record manually.

**3\. MVP Definition of Done**

The Strategy module is MVP-complete only if all of these are true:

1\. Core flow works

2\. UI is understandable

3\. Validation is strict

4\. Workflow is visible

5\. Data survives reload

6\. Downstream selectors work

7\. Smoke tests pass

If even one fails, the module is not done.

**4\. Smoke Test Contract**

This is the minimum automated test contract.  
It is intentionally small and brutal.

**Smoke Test 1 — Workspace Access**

**Goal**

Verify the module is reachable and navigable.

**Steps**

1.  Login as Strategy Manager
2.  Open main app navigation
3.  Open Strategy workspace
4.  Verify:
    - workspace loads
    - “New Strategic Plan” action exists
    - plan list/grid exists

**Expected**

- no broken route
- no blank page
- no console-breaking UI failure

**Smoke Test 2 — Create Strategic Plan**

**Goal**

Verify basic plan creation works.

**Steps**

1.  From workspace, click New Strategic Plan
2.  Fill:
    - Plan Name
    - Entity
    - Period Start
    - Period End
3.  Save

**Expected**

- plan saved successfully
- workflow state = Draft
- step builder remains usable

**Smoke Test 3 — Add Full Hierarchy**

**Goal**

Verify user can create one complete chain.

**Steps**

1.  Open Programs step
2.  Add one Program
3.  Open Sub-programs step
4.  Add one Sub-program linked to Program
5.  Open Indicators step
6.  Add one Indicator linked to Sub-program
7.  Open Targets step
8.  Add one Target linked to Indicator

**Expected**

- all records save successfully
- records appear in correct tables
- hierarchy is preserved

**Smoke Test 4 — Submission Validation**

**Goal**

Verify incomplete plans cannot be submitted.

**Steps**

1.  Create a draft plan with missing hierarchy pieces
2.  Go to Review step
3.  Attempt Submit

**Expected**

- submission blocked
- clear message identifies what is missing

**Smoke Test 5 — Submit / Approve / Activate**

**Goal**

Verify workflow progression works.

**Steps**

1.  Use complete draft plan
2.  Submit plan
3.  Login as Planning Authority
4.  Approve plan
5.  Activate plan

**Expected**

- states transition correctly
- plan becomes Active
- child records locked from editing

**Smoke Test 6 — Locking Rules**

**Goal**

Verify active plan cannot be casually edited.

**Steps**

1.  Open Active plan
2.  Attempt to edit:
    - Program
    - Sub-program
    - Indicator
    - Target

**Expected**

- editing blocked for ordinary user
- clear read-only behavior

**Smoke Test 7 — Downstream Selector Readiness**

**Goal**

Verify active strategy data is exposed correctly.

**Steps**

1.  Call or load downstream selector for:
    - Programs
    - Sub-programs
    - Indicators
    - Targets
2.  Verify only Active plan data appears

**Expected**

- active records visible
- draft/submitted/archived hidden

**5\. Manual Sanity Script (Human Test)**

This is the short real-user check before you move on.

**Strategy Manager**

- can create plan
- can complete each step
- is never unsure what to do next
- does not need search to find features

**Planning Authority**

- can open submitted plan
- can understand summary immediately
- can approve without hunting through UI

If either user struggles, the module is not ready.

**6\. Failure Conditions That Block Progress**

Do not move to the next module if any of these happen:

- workspace/menu is broken
- builder is replaced by raw form behavior
- step flow is unclear
- any hierarchy level can become orphaned
- submission allows incomplete structures
- activation does not lock data
- downstream selector data is wrong
- smoke tests are flaky

**7\. Suggested Test File Set**

When you do automate this, keep it small.

tests/ui/strategy/

workspace.spec.ts

create-plan.spec.ts

hierarchy.spec.ts

workflow.spec.ts

selectors.spec.ts

That is enough for MVP.

**8\. Windsurf Brief**

Use this Strategy MVP sanity checklist as a hard completion gate.

Do not treat the module as complete until:

1\. Strategy workspace is reachable from normal navigation

2\. Strategic Plan opens into the step-based builder

3\. User can create Program, Sub-program, Indicator, and Target

4\. Submission blocks incomplete plans

5\. Workflow transitions Draft -> Submitted -> Approved -> Active work

6\. Active plans are read-only

7\. Downstream selector endpoints expose only active records

8\. Smoke tests pass consistently

If any of these fail, stop implementation and fix Strategy before moving to the next module.

**9\. My advice before you start implementation**

Do not let Windsurf “keep going” once it gets something mostly working.

Stop after:

- workspace
- builder
- hierarchy CRUD
- workflow
- selector endpoints
- smoke tests

That is the whole Strategy MVP.

After that, freeze it and only then move on.

The next step should be the **Strategy implementation sequence**, so Windsurf builds it in the right order instead of touching everything at once.