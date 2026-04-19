# Strategy Builder Refactor

# What’s good (don’t lose this)

**1\. The hierarchy builder itself is solid**

- Left tree: Program → Objective → Target ✅
- Clear nesting and navigation ✅
- Counts and readiness at top ✅

This is the hard part — and you got it right.

**2\. The right-hand panel is technically complete**

All required fields exist:

- measurement type
- period type
- value
- unit
- baseline

So you’re not missing functionality — just **presentation and constraints**.

# What’s wrong (and will hurt you later)

**1\. The form is cognitively flat**

Everything is just a vertical list of fields.

That forces the user to:

- mentally group fields
- remember relationships
- guess what matters

That’s how bad data gets created.

**2\. No separation between “definition” vs “measurement”**

Right now:

- title sits next to numeric inputs
- description sits next to unit fields

These are **different concepts**:

- WHAT is the target
- HOW it is measured

They must be visually separated.

**3\. Period logic is unclear**

You have:

- Target Period Type
- Period Value
- Target Year

This is dangerous:

- ambiguous
- redundant
- conflicting inputs possible

This is exactly the kind of thing that silently corrupts data.

**4\. Measurement Type is passive**

You show:

Percentage

…but it doesn’t _drive the form_.

It should:

- constrain units
- influence input formatting
- control validation

Right now it’s just decorative.

**5\. Unit is free text (still risky)**

Even though you improved it, it still behaves like uncontrolled input.

You need:

- controlled vocabulary
- or derived units

**6\. No visual grouping → no confidence**

A user looking at this form does not feel:

“I understand what I’m entering”

They feel:

“I’m filling random fields”

That’s the difference between:

- system adoption
- silent data decay

# What this SHOULD look like

You need **3 sections**. No more, no less.

**SECTION 1 — Target Definition**

What are we trying to achieve?

Fields:

- Title
- Description

**SECTION 2 — Measurement**

How is success measured?

Fields:

- Measurement Type (select)
- Target Value (numeric)
- Target Unit (derived or controlled)

Behavior:

- If Percentage → unit auto = %
- If Count → unit = selectable (facilities, people, etc)

**SECTION 3 — Timeframe**

When is this expected?

Fields:

- Target Period Type (select)
    - Annual
    - End of Plan
- Conditional:
    - If Annual → Target Year required
    - If End of Plan → auto derive from plan

REMOVE ambiguity:

- Do NOT show both Period Value and Target Year blindly

**SECTION 4 — Baseline (optional)**

Where are we starting from?

Fields:

- Baseline Value (numeric)
- Baseline Notes (text)

**The real issue (not just UI)**

You’re still letting the UI expose **data model ambiguity**.

This is the deeper correction:

👉 UI should **enforce the model**, not reflect it loosely.

# Cursor Prompts

Refactor the Target form in the Strategy Builder to improve structure, clarity, and data integrity.

Do not change the underlying data model yet. Focus on UI structure and constraints.

Make the following changes:

1.  Introduce clear form sections

Group fields into 4 sections with headings:

SECTION 1: Target Definition

- Title (required)
- Description (optional)

SECTION 2: Measurement

- Measurement Type (required, select)
- Target Value (numeric, required)
- Target Unit (controlled, not free text)

SECTION 3: Timeframe

- Target Period Type (required, select: Annual, End of Plan)
- If Annual:
    - show Target Year (integer, required)
- If End of Plan:
    - hide Target Year
    - derive period from Strategic Plan

Remove ambiguity:

- Do not show both Period Value and Target Year at the same time
- Remove or hide Period Value field if redundant

SECTION 4: Baseline (optional)

- Baseline Value (numeric)
- Baseline Notes (text)

1.  Add dynamic behavior

- When Measurement Type = Percentage:
    - auto-set Target Unit = "Percent"
    - disable editing of unit
- When Measurement Type = Count:
    - allow unit selection from controlled list

1.  Improve layout

- Use card or section containers with clear spacing
- Add section headings and subtle dividers
- Ensure fields within a section are visually grouped

1.  Improve labels

- "Target Value (numeric)" → "Target Value"
- "Target Unit" → "Unit"
- "Baseline (text, optional)" → "Baseline Notes"

1.  Do not change persistence logic yet

- Keep backend unchanged
- Only restructure UI and conditional rendering

Acceptance criteria:

- Form is clearly divided into logical sections
- Users can understand what they are entering without guessing
- Period inputs cannot conflict
- Measurement type influences available inputs

**One more important correction (don’t skip this)**

You said earlier:

“This is because we have not correctly defined the model yet”

That’s still true.

What you just built is:

a UI compensating for a partially-defined model

This fix stabilizes UX, but soon you’ll need:

- strict enum definitions (measurement type, unit)
- removal of redundant fields (period_value vs year)
- enforced constraints at DocType level

**Bottom line**

Current state:

Builder hierarchy: strong

Builder data entry: weak

Risk of bad data: high if unchanged

Fix complexity: moderate

Impact of fix: very high

You’re at the exact point where most systems fail quietly.

Fix this now, and everything downstream (procurement, budgeting, reporting) becomes reliable.