# Strategy Workspace Refactor

# What is good

**1\. The core structure is correct**

You now have:

- plan list
- selected plan detail
- actions
- counts

That is exactly what the landing page should do.

**2\. The selected-plan state is clear enough**

The highlighted row and right-hand summary make the page understandable.

**3\. “Open Strategy Builder” is correctly prominent**

That is the most important action after plan creation.

**4\. The page is no longer a dead shell**

This is now a usable product surface, not a placeholder.

# What is still wrong

**1\. The layout balance is off**

The left list is visually heavy and boxed, while the right detail pane is too sparse.

Result:

- left side feels crowded
- right side feels unfinished
- bottom CTA feels detached from both

**2\. “New Strategic Plan” is in the wrong place**

Right now it is sitting at the bottom like a footer action.

That is not how users think.

The create action should sit:

- above the plans list, or
- in the top-right of the page header

It should not be below the list/detail region.

**3\. The intro text is misplaced**

“Create and manage strategic plans and hierarchy.” is floating below the list, which makes the page feel stitched together.

That text belongs near the top, under the page title.

**4\. The plan rows need better information hierarchy**

Each row currently shows:

- title
- years
- status

That is fine, but the visual grouping is weak.

A better row would make:

- title dominant
- years secondary
- status as a badge/chip

Right now status reads like loose text.

**5\. The selected-detail panel is too bare**

It should feel like a proper “overview card” for the chosen plan.

Right now it only shows:

- title
- status
- years
- counts

It needs one more level of structure:

- plan metadata grouped together
- actions grouped together
- counts grouped together

**6\. Duplicate / noisy data will become a problem**

You already have multiple similarly named plans in the list.

As the list grows, this view will become hard to scan unless you add:

- stronger row spacing
- better selected highlight
- maybe modified date or version later

**7\. Status handling is visually weak**

“Draft” and “Active” should not look the same.

Use badges:

- Draft = neutral
- Active = green
- Archived later = muted

# What it should look like

## Recommended layout

**Header area**

- Strategy Management
- short intro directly below it
- New Strategic Plan action at top-right or just above the list

**Main content**

Two-column split:

**Left column**

**Strategic Plans**

- search/filter later
- plan list
- selected row clearly highlighted

**Right column**

**Selected Plan Overview**

- title
- status badge
- years
- counts
- actions:
    - Open Strategy Builder
    - Edit Plan

## Cursor Prompts

Tell Cursor to make only these changes:

Refine the Strategy landing page layout without changing functionality.

Keep the existing master-detail structure, but improve the information hierarchy and action placement.

Make these exact changes:

1.  Move the page intro text

- Place "Create and manage strategic plans and hierarchy." directly below the page title at the top
- Remove it from the lower part of the page

1.  Move the "New Strategic Plan" action

- Place it at the top of the Strategic Plans section or top-right of the page header
- Do not leave it as a detached bottom action

1.  Improve the Strategic Plans list rows

- Make plan title visually dominant
- Make years secondary text
- Render status as a badge/chip, not plain loose text
- Keep selected-row highlight clear

1.  Improve the selected-plan panel

- Group selected plan information into a cleaner overview area
- Show:
    - plan title
    - status badge
    - years
- Then actions:
    - Open Strategy Builder
    - Edit Plan
- Then counts:
    - Programs
    - Objectives
    - Targets

1.  Reduce visual imbalance

- Make left and right panes feel like parts of the same layout
- Avoid the current effect where the left side is visually dense and the right side looks unfinished

1.  Keep functionality unchanged

- Do not change data fetching
- Do not change routes
- Do not change builder logic

Acceptance criteria:

- The landing page feels like a coherent master-detail workspace
- "New Strategic Plan" is in a natural creation position
- Intro text is at the top where users expect it
- Selected-plan summary is clearer and more structured

**What I would accept after that**

Then the page will be good enough to serve as the Strategy landing surface for MVP.

After that, I would not spend more time polishing this page yet. The next real value would be:

- role visibility
- read-only behavior for Planning Authority
- builder refinement under real seeded data

# Bottom line

Current status:

Landing page architecture: correct

Landing page UX polish: not yet finished

Ready to refine: yes

Ready to leave untouched forever: no

If you want, the next thing I can do is give you a **tight Playwright contract for this exact landing page**, including:

- populated state
- selection behavior
- action visibility
- role-based visibility.