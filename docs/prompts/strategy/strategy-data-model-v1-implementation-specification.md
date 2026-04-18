# Strategy Data Model v1 — Implementation Specification

**1\. Scope**

This specification defines the **exact data model** for the Strategy module v1.

It is intended for:

- immediate implementation in Frappe
- direct use by Cursor (no interpretation required)
- stable foundation for UI builder and future extensions

**2\. Design Decisions (Final)**

These are **locked decisions**, not suggestions:

1.  Use **typed DocTypes**, not generic nodes:
    - Strategic Plan
    - Strategy Program
    - Strategy Objective
    - Strategy Target
2.  Hierarchy is fixed:

Strategic Plan → Program → Objective → Target

1.  Targets are **measurement-aware entities** (not generic text nodes)
2.  No Indicators layer in v1
3.  No reporting/actual tracking in v1

**3\. DocType Specifications**

**3.1 Strategic Plan**

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Req** | **Default** | **Description** | **Validation** |
| name | Data (autoname) | ✓   | naming_series | Primary key | unique |
| strategic_plan_name | Data | ✓   | —   | Human-readable name | not empty |
| procuring_entity | Link (Company) | ✓   | —   | Owning entity | must exist |
| start_year | Int | ✓   | —   | Plan start year | ≤ end_year |
| end_year | Int | ✓   | —   | Plan end year | ≥ start_year |
| status | Select | ✓   | Draft | Draft / Active / Archived | valid option |
| version_no | Int | ✓   | 1   | Version number | ≥ 1 |
| is_current_version | Check | ✓   | 1   | Active version flag | boolean |
| supersedes_plan | Link (Strategic Plan) | ✗   | —   | Previous version | same entity |

**Autoname**

format: {procuring_entity}-.SP-.YYYY-.####

**3.2 Strategy Program**

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Req** | **Default** | **Description** | **Validation** |
| name | Data (autoname) | ✓   | hash | Primary key | unique |
| strategic_plan | Link (Strategic Plan) | ✓   | —   | Parent plan | must exist |
| program_title | Data | ✓   | —   | Program name | not empty |
| program_code | Data | ✗   | —   | Optional code | unique per plan |
| description | Text | ✗   | —   | Description | —   |
| order_index | Int | ✓   | 0   | Display order | ≥ 0 |

**Constraints**

- (strategic_plan, program_code) unique if code provided

**3.3 Strategy Objective**

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Req** | **Default** | **Description** | **Validation** |
| name | Data (autoname) | ✓   | hash | Primary key | unique |
| strategic_plan | Link (Strategic Plan) | ✓   | —   | Parent plan | must match program |
| program | Link (Strategy Program) | ✓   | —   | Parent program | must exist |
| objective_title | Data | ✓   | —   | Objective name | not empty |
| objective_code | Data | ✗   | —   | Optional code | unique per program |
| description | Text | ✗   | —   | Description | —   |
| order_index | Int | ✓   | 0   | Display order | ≥ 0 |

**Constraints**

- program.strategic_plan == strategic_plan
- (program, objective_code) unique if provided

**3.4 Strategy Target**

This is the **core entity**.

**3.4.1 Core Fields**

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Req** | **Default** | **Description** | **Validation** |
| name | Data (autoname) | ✓   | hash | Primary key | unique |
| strategic_plan | Link (Strategic Plan) | ✓   | —   | Parent plan | must match objective |
| program | Link (Strategy Program) | ✓   | —   | Parent program | must match objective |
| objective | Link (Strategy Objective) | ✓   | —   | Parent objective | must exist |
| target_title | Data | ✓   | —   | Target label | not empty |
| description | Text | ✗   | —   | Optional description | —   |
| order_index | Int | ✓   | 0   | Display order | ≥ 0 |

**3.4.2 Measurement Fields**

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Req** | **Default** | **Description** | **Validation** |
| measurement_type | Select | ✓   | —   | Target type | see enum |
| target_period_type | Select | ✓   | —   | Time basis | see enum |
| target_period_value | Data | ✓   | —   | Period key | format depends on type |

**3.4.3 Value Fields**

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Req** | **Default** | **Description** | **Validation** |
| target_value_numeric | Float | conditional | —   | Numeric value | ≥ 0 |
| target_value_text | Text | conditional | —   | Text value | not empty if used |
| target_unit | Data | conditional | —   | Unit label | controlled text |

**3.4.4 Baseline Fields**

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Req** | **Default** | **Description** | **Validation** |
| baseline_value_numeric | Float | ✗   | —   | Numeric baseline | ≥ 0 |
| baseline_value_text | Text | ✗   | —   | Text baseline | —   |
| baseline_year | Int | ✗   | —   | Baseline year | ≤ plan end |

**4\. Enumerations (Strict)**

**4.1 measurement_type**

Numeric

Percentage

Currency

Milestone

Boolean

**4.2 target_period_type**

Annual

End of Plan

Quarterly

Milestone Date

**5\. Validation Rules (Consolidated — NO duplication elsewhere)**

**5.1 Hierarchy Validation**

| **Rule** |
| --- |
| Program.strategic_plan must exist |
| Objective.program must exist |
| Objective.strategic_plan == Program.strategic_plan |
| Target.objective must exist |
| Target.program == Objective.program |
| Target.strategic_plan == Objective.strategic_plan |

**5.2 Measurement Logic**

**If measurement_type ∈ {Numeric, Percentage, Currency}**

- target_value_numeric **required**
- target_value_text **must be empty**
- target_unit **required**

**If measurement_type ∈ {Milestone, Boolean}**

- target_value_text **required**
- target_value_numeric **must be empty**

**5.3 Percentage Constraint**

0 ≤ target_value_numeric ≤ 100

**5.4 Period Validation**

**If target_period_type = Annual**

target_period_value must be integer year

start_year ≤ value ≤ end_year + 5 (buffer allowed)

**5.5 Baseline Logic**

- If numeric target → baseline must be numeric if provided
- If text target → baseline must be text if provided

**6\. UI Binding Rules (Builder must follow this exactly)**

**6.1 Target Creation Flow**

Step 1 (always visible):

- Target Title
- Measurement Type
- Target Period Type

**6.2 Dynamic Fields**

**Numeric / Percentage / Currency**

Show:

- Target Value (numeric)
- Unit
- Period Value
- Baseline (optional)

**Milestone**

Show:

- Target Description (text)
- Period Value

**Boolean**

Show:

- Completion description
- Period Value

**6.3 Disabled States**

- Cannot create Objective without Program
- Cannot create Target without Objective

**6.4 Auto-behavior**

After create:

- auto-select new node
- expand parent
- scroll into view

**7\. Indexing & Performance**

Add indexes:

Strategic Plan: procuring_entity

Program: strategic_plan

Objective: program

Target: objective, program, strategic_plan

**8\. Cursor Implementation Prompt (Rewritten — strict)**

Implement Strategy Data Model v1 exactly as specified.

Create the following DocTypes:

1.  Strategic Plan
2.  Strategy Program
3.  Strategy Objective
4.  Strategy Target

Follow field definitions exactly:

- field names
- types
- required flags
- defaults
- constraints
- enumerations

Do not rename fields.

Implement validation rules strictly:

- hierarchy validation across all levels
- measurement_type conditional logic
- percentage bounds (0–100)
- period validation for Annual targets
- baseline consistency

Do not split validation logic across multiple places:

- enforce in DocType validation methods

Do not introduce additional fields.

Do not introduce Indicator or reporting logic.

Update existing Strategy Builder UI:

- bind to new typed DocTypes
- dynamically render fields based on measurement_type
- enforce creation hierarchy (Program → Objective → Target)
- auto-select and expand nodes after creation

Do not redesign UX.

Ensure existing builder continues to work with new data model.

All logic must align exactly with Strategy Data Model v1 specification.

**Final note (important)**

Now you are no longer “designing a feature.”

You are defining a **domain contract**.

From this point:

- UI must follow model
- not the other way around
- Cursor must stop guessing