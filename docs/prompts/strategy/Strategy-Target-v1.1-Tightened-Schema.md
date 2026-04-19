# Strategy Target — v1.1 Tightened Schema

This is the corrected, implementation-grade target model.

**Core principle**

A Target should answer four things, cleanly:

- what is being committed
- how it is measured
- when it is due
- what baseline it is improving from

**Final field specification**

**A. Identity and hierarchy**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Req** | **Notes** |
| name | Autoname | ✓   | System ID |
| strategic_plan | Link → Strategic Plan | ✓   | Derived from Objective, not user-editable in builder |
| program | Link → Strategy Program | ✓   | Derived from Objective, not user-editable in builder |
| objective | Link → Strategy Objective | ✓   | Parent objective |
| target_title | Data | ✓   | Main target label |
| description | Text | ✗   | Optional explanatory text |
| order_index | Int | ✓   | Default 0 |

**B. Measurement semantics**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Req** | **Notes** |
| measurement_type | Select | ✓   | Enum below |
| target_value_numeric | Float | conditional | Used for numeric-style targets |
| target_value_text | Text | conditional | Used for milestone / boolean-style targets |
| target_unit | Data | conditional | Controlled text, not arbitrary free typing in UI |

**measurement_type enum**

Numeric

Percentage

Currency

Milestone

Boolean

**C. Time semantics**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Req** | **Notes** |
| target_period_type | Select | ✓   | Enum below |
| target_year | Int | conditional | Used only for Annual |
| target_due_date | Date | conditional | Used only for Milestone Date |

**target_period_type enum**

Annual

End of Plan

Milestone Date

**Important removal**

Remove this field from active use:

target_period_value

It is too generic and causes ambiguity.

You were right to be suspicious of it.

**D. Baseline**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Req** | **Notes** |
| baseline_value_numeric | Float | ✗   | For numeric / percentage / currency |
| baseline_value_text | Text | ✗   | For milestone / boolean narrative baseline |
| baseline_year | Int | ✗   | Optional reference year |

**UI-facing meaning of the schema**

**If measurement_type = Percentage**

Show:

- Target Value
- Unit = Percent auto-set, read-only

**If measurement_type = Numeric**

Show:

- Target Value
- Unit = controlled selectable text

**If measurement_type = Currency**

Show:

- Target Value
- Unit = currency code, preferably auto-set from plan/entity

**If measurement_type = Milestone**

Show:

- Completion statement / target text
- optional due date if target_period_type = Milestone Date

**If measurement_type = Boolean**

Show:

- completion condition text
- no numeric value

**Tightened builder section structure**

The Target editor should now be exactly these sections.

**1\. Target Definition**

- Target Title
- Description

**2\. Measurement**

- Measurement Type
- Target Value OR Target Statement
- Unit

**3\. Timeframe**

- Target Period Type
- Target Year OR Due Date OR derived end-of-plan note

**4\. Baseline (Optional)**

- Baseline Value / Notes
- Baseline Year

This is the final v1 layout.

**Server-side validation and guard rules**

These must live in backend validation, not just UI.

**1\. Hierarchy guards**

**Rule H1**

Target must have:

- objective
- program
- strategic_plan

**Rule H2**

target.program == target.objective.program

**Rule H3**

target.strategic_plan == target.objective.strategic_plan

**Rule H4**

Builder-created records must not allow cross-plan linking.

**2\. Measurement guards**

**Rule M1 — Numeric-like targets**

If measurement_type is one of:

Numeric

Percentage

Currency

Then:

- target_value_numeric required
- target_value_text must be empty

**Rule M2 — Text-like targets**

If measurement_type is one of:

Milestone

Boolean

Then:

- target_value_text required
- target_value_numeric must be empty

**Rule M3 — Percentage bounds**

If measurement_type = Percentage:

- 0 <= target_value_numeric <= 100
- target_unit = Percent

**Rule M4 — Currency behavior**

If measurement_type = Currency:

- numeric value required
- target_unit should default from plan/entity currency if available

**3\. Time guards**

**Rule T1 — Annual**

If target_period_type = Annual:

- target_year required
- target_due_date empty
- start_year <= target_year <= end_year

**Rule T2 — End of Plan**

If target_period_type = End of Plan:

- target_year empty
- target_due_date empty

**Rule T3 — Milestone Date**

If target_period_type = Milestone Date:

- target_due_date required
- target_year empty

**Rule T4**

Do not allow more than one active time field to be populated.

**4\. Baseline guards**

**Rule B1**

If measurement type is numeric-like:

- baseline_value_numeric may be used
- baseline_value_text should be empty

**Rule B2**

If measurement type is text-like:

- baseline_value_text may be used
- baseline_value_numeric should be empty

**Rule B3**

If baseline_year exists:

- should be <= end_year

**5\. Mutability guards**

These prevent bad edits later.

**Rule G1**

If user is not Strategy Manager or Administrator:

- no create/update/delete of Program/Objective/Target

**Rule G2**

If plan status is not Draft:

- deny mutation of hierarchy records

**Rule G3**

Planning Authority may read but not mutate in v1

**Recommended Frappe implementation pattern**

**In DocType validation methods**

Use backend validation in:

- strategy_target.py
- strategy_objective.py
- strategy_program.py

**Keep validation categories separated in code**

Use helper methods like:

- \_validate_hierarchy()
- \_validate_measurement_fields()
- \_validate_period_fields()
- \_validate_baseline_fields()
- \_validate_editable_state()

That gives structure without scattering rules conceptually.

**Cursor prompt — schema tightening**

Refactor Strategy Target schema to v1.1 and remove ambiguity.

Implement these exact changes:

1.  Keep these target fields:

- strategic_plan
- program
- objective
- target_title
- description
- order_index
- measurement_type
- target_value_numeric
- target_value_text
- target_unit
- target_period_type
- target_year
- target_due_date
- baseline_value_numeric
- baseline_value_text
- baseline_year

1.  Remove active use of:

- target_period_value

1.  measurement_type enum must be exactly:

- Numeric
- Percentage
- Currency
- Milestone
- Boolean

1.  target_period_type enum must be exactly:

- Annual
- End of Plan
- Milestone Date

1.  Keep typed hierarchy:

- Strategic Plan
- Strategy Program
- Strategy Objective
- Strategy Target

1.  Update builder UI:

- Target Definition section
- Measurement section
- Timeframe section
- Baseline section

1.  Dynamic field behavior:

- Percentage → unit auto-set to Percent, read-only
- Annual → show Target Year only
- End of Plan → hide Target Year and Due Date
- Milestone Date → show Due Date only
- Milestone/Boolean → show text value field
- Numeric/Percentage/Currency → show numeric value field

Do not redesign unrelated pages.  
Do not add reporting logic.  
Do not add indicators.

**Cursor prompt — validation and guards**

Implement strict server-side validation and mutation guards for Strategy Program, Strategy Objective, and Strategy Target.

Validation must be enforced in backend DocType validation methods, not only in UI.

Implement these rules exactly:

1.  Hierarchy validation

- Target.objective must exist
- Target.program must equal Target.objective.program
- Target.strategic_plan must equal Target.objective.strategic_plan
- Objective.program must exist
- Objective.strategic_plan must equal Objective.program.strategic_plan

1.  Measurement validation

- Numeric/Percentage/Currency:
    - target_value_numeric required
    - target_value_text must be empty
- Milestone/Boolean:
    - target_value_text required
    - target_value_numeric must be empty
- Percentage:
    - value must be between 0 and 100
    - unit must be Percent

1.  Time validation

- Annual:
    - target_year required
    - target_due_date empty
    - target_year must be within plan years
- End of Plan:
    - target_year empty
    - target_due_date empty
- Milestone Date:
    - target_due_date required
    - target_year empty

1.  Baseline validation

- Numeric-like targets use baseline_value_numeric
- Text-like targets use baseline_value_text
- baseline_year must not exceed plan end year

1.  Mutation guards

- Only Strategy Manager and Administrator may mutate Strategy hierarchy in v1
- Planning Authority is read-only
- If Strategic Plan status is not Draft, deny create/update/delete on Program/Objective/Target

1.  Error messages  
    Use clear user-facing validation errors.  
    Do not use vague messages.

Do not implement workflow approval yet.  
Do not broaden access beyond v1 permissions.

**The one thing I would change in your current builder immediately**

Before anything else, remove the simultaneous presence of:

- Target Period Type
- Period Value
- Target Year

That is the biggest current source of ambiguity.

For v1.1, the correct state is:

- Annual → Target Year
- End of Plan → no extra time field
- Milestone Date → Due Date

That one change alone will make the form feel much more intentional.

**Recommended sequence from here**

Do this in order:

1.  **Schema tighten**
2.  **Backend validation**
3.  **Builder UI refactor to match schema**
4.  **Role/mutation guards**
5.  **Playwright tests for valid vs invalid target entry**