# Strategy Tree Builder implementation design

**Strategy Tree Builder — Implementation Design**

**1\. Goal**

Build a **custom Strategy Builder page** for one Strategic Plan, with:

- left pane: hierarchy tree
- right pane: selected node editor
- controlled add/edit/delete flow
- no raw linked forms as the primary UX

This is the UI for:

- Programs
- Objectives
- Targets

**2\. Recommended model**

Do **not** build separate primary editing UIs for Program, Objective, and Target first.

Use:

**A. Strategic Plan**

Top-level document.

Fields:

- name
- strategic_plan_name
- description
- status
- version_no
- is_active
- owner_entity

**B. Strategy Node**

Single hierarchy DocType.

Fields:

- name
- strategic_plan (Link to Strategic Plan) — required
- parent_strategy_node (Link to Strategy Node) — nullable
- node_type (Select) — required  
    Values:
    - Program
    - Objective
    - Target
- node_title (Data) — required
- node_description (Small Text / Text Editor)
- order_index (Int)
- is_group (Check)
- status (Select: Draft / Active / Archived) if needed later, otherwise omit now
- target_value (Float) — only used for Target
- target_unit (Data / Link) — only used for Target
- target_year (Int) — only used for Target
- objective_code / program_code / target_code — optional later, not now

**Validation rules**

- Program: parent must be null
- Objective: parent must be Program
- Target: parent must be Objective
- All nodes must belong to the same Strategic Plan as their parent
- order_index required for stable rendering

This is the simplest structure that supports the UX.

**3\. Why one Strategy Node DocType is better**

Because it gives you:

- one tree source
- one API shape
- one renderer
- easier drag/reorder later
- easier validation
- less UI branching

If you model Program / Objective / Target as three separate fully edited forms now, Cursor will produce linked-form ERP chaos.

**4\. Page architecture**

Create a **custom page**, not a DocType form.

Suggested route:

/app/strategy-builder/&lt;strategic-plan-name&gt;

Suggested page name:

strategy-builder

**5\. UX layout**

**6\. Left pane behavior**

The left pane is the working map.

**It must:**

- render the full hierarchy for the selected Strategic Plan
- show nesting clearly
- allow selection of one node
- visually highlight the selected node
- expose contextual add buttons

**It must not:**

- open raw forms
- navigate away on selection
- require search
- mix unrelated metadata into the tree

**Tree display labels**

Use concise labels:

- Program: Program — Healthcare Delivery
- Objective: Objective — Increase rural access
- Target: Target — 2026: 25 facilities

**7\. Right pane behavior**

The right pane edits the currently selected node.

**If no node selected**

Show:

- “Select a node from the left, or create a new Program to begin.”

**If node selected**

Show only relevant fields for that type.

**Program fields**

- Program Title
- Description

**Objective fields**

- Objective Title
- Description

**Target fields**

- Target Title
- Description
- Target Year
- Target Value
- Target Unit

**Important**

Do not show fields irrelevant to the node type.

That is where form bloat begins.

**8\. Add-node flow**

Do not use raw “New Strategy Node” forms.

Use **contextual add actions**.

**Rules**

**Add Program**

Available always.  
Creates root node.

**Add Objective**

Available only when:

- a Program is selected

**Add Target**

Available only when:

- an Objective is selected

**UX pattern**

When user clicks add:

- create temporary node or open a lightweight modal
- after creation, auto-select the new node in the editor pane

This feels guided.

**9\. Delete behavior**

Keep it strict.

**Rules**

- Cannot delete a node with children unless user confirms cascade delete
- For MVP, safer option:
    - block delete if children exist
    - show message: “Delete child nodes first.”

That is easier and safer than recursive delete for now.

**10\. Save behavior**

There are two save layers:

**A. Save Node**

Saves only the currently edited node.

**B. Save Plan**

Optional top-level save if you maintain plan-level metadata on the page.

For MVP:

- node saves are enough
- plan header save can stay on the plan form or top banner later

**Important**

Never make the user wonder whether edits are saved.

Show toast:

- “Program saved”
- “Objective saved”
- “Target saved”

**11\. Submission readiness**

Do not implement full submission yet, but prepare for it.

Add a lightweight panel or banner:

Readiness

\- Programs: 2

\- Objectives: 5

\- Targets: 9

Later this becomes full validation.

For now, enough to support awareness.

**12\. Backend API design**

Create explicit methods in kentender_strategy/api/strategy_builder.py or equivalent.

**APIs**

**1\. get_strategy_tree(plan_name)**

Returns tree JSON.

Response shape:

{

"plan": {

"name": "SP-0001",

"title": "MOH Strategic Plan 2026-2030",

"status": "Draft"

},

"nodes": \[

{

"name": "NODE-001",

"parent": null,

"node_type": "Program",

"title": "Healthcare Delivery",

"order_index": 1

},

{

"name": "NODE-002",

"parent": "NODE-001",

"node_type": "Objective",

"title": "Increase rural access",

"order_index": 1

}

\]

}

**2\. create_strategy_node(plan_name, parent_name, node_type, initial_data)**

Creates a node with validation.

**3\. update_strategy_node(node_name, data)**

Updates editable fields.

**4\. delete_strategy_node(node_name)**

Deletes node if allowed.

**5\. reorder_strategy_node(node_name, new_parent, new_order_index)**

Optional later, not required first pass.

**13\. Service layer**

Keep business logic out of page JS.

Create service functions in kentender_strategy/services/strategy_builder.py:

- build_tree(plan_name)
- validate_new_node(plan_name, parent_name, node_type)
- create_node(...)
- update_node(...)
- delete_node(...)

Cursor must not place this logic in DocType JS or page handlers.

**14\. Validation matrix**

**Allowed parent-child combinations**

| **Child** | **Allowed Parent** |
| --- | --- |
| Program | none |
| Objective | Program |
| Target | Objective |

Anything else: reject.

**15\. Cursor implementation brief**

Use this with Cursor.

Implement a custom Strategy Builder page for one Strategic Plan.

Goal:  
Replace raw linked-form editing of Programs/Objectives/Targets with a two-pane hierarchy builder.

Architecture rules:

- Use kentender_strategy only
- No cross-app imports
- Business logic in services/, not page handlers
- Use explicit API methods
- Do not fall back to raw DocType forms as the primary UX

Data model:

1.  Strategic Plan (already exists)
2.  Strategy Node DocType with fields:
    - strategic_plan
    - parent_strategy_node
    - node_type (Program | Objective | Target)
    - node_title
    - node_description
    - order_index
    - target_value
    - target_unit
    - target_year

Validation:

- Program must have no parent
- Objective parent must be Program
- Target parent must be Objective
- Parent and child must belong to same strategic plan

UI:

- Create custom page route: /app/strategy-builder/
- Left pane = tree
- Right pane = selected node editor
- Add Program / Add Objective / Add Target actions must be contextual
- No long forms
- No navigation away from builder while editing
- If no node selected, show guidance message
- Show toasts after save

API methods:

- get_strategy_tree(plan_name)
- create_strategy_node(...)
- update_strategy_node(...)
- delete_strategy_node(...)

Do not implement drag-drop reorder yet.  
Do not implement workflow yet.  
Do not implement separate Program/Objective/Target forms as the primary UX.  
Keep the first version minimal but structurally correct.

Acceptance criteria:

1.  User can open a Strategy Builder for a plan
2.  User can add a Program
3.  User can add an Objective under a Program
4.  User can add a Target under an Objective
5.  Selecting nodes updates the right editor pane
6.  No raw form navigation is required for tree editing

**16\. Recommended implementation sequence**

Do not build everything at once.

**Step 1**

Create Strategy Node DocType + validations.

**Step 2**

Create get_strategy_tree API.

**Step 3**

Create custom strategy-builder page with left tree only.

**Step 4**

Add right editor pane for selected node.

**Step 5**

Add create/save node actions.

**Step 6**

Add delete protections.

Only after that do you think about:

- reorder
- submission
- approval
- versioning

**17\. What not to do**

Do not let Cursor:

- create three separate major CRUD flows for Program/Objective/Target first
- route users into default forms for normal editing
- use Frappe TreeView as the primary UX
- put tree state logic in random files
- add 20 fields now “for future use”

**18\. My recommendation**

This is the right backbone for Strategy.

If you implement this well, you will reuse the same pattern later for:

- budget structure
- procurement plan grouping
- template grouping

This is a real platform move, not just a one-off screen.

If you want, next I’ll give you the **Playwright smoke contract for the Strategy Builder**, so you can validate it the moment Cursor generates the first version.