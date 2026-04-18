# Strategy Workspace Fix

Short answer: **what you’re seeing is expected given your current implementation—but it’s not acceptable UX.** Right now your workspace is just a static shell. It’s not _bound to data_, so creating a Strategic Plan does nothing visually.

Let me show you what it **should look like** and what’s missing.

**What Your Workspace Should Become**

**1\. Current State (yours)**

- “No strategic plans yet” → ❌ incorrect (you created one)
- No list, no navigation, no selection
- Programs/Objectives = “Coming soon”

👉 This is a **dead dashboard**, not a working module.

**2\. Expected MVP State (after creating 1 plan)**

**Strategy Workspace (correct behavior)**

**Layout should shift to:**

**A. Strategic Plans List (LEFT or TOP)**

Strategic Plans

\[ + New Strategic Plan \]

• MOH Strategic Plan 2026–2030 ← selected

• County Health Plan 2025–2029

**B. Selected Plan Detail (MAIN PANEL)**

MOH Strategic Plan 2026–2030

Status: Draft | Years: 2026–2030

\[ Open Strategy Builder \]

\[ Edit \]

\[ Archive \]

Programs: 0

Objectives: 0

Targets: 0

**C. Replace “No strategic plans yet”**

Instead:

1 Strategic Plan found

**Why Your Current UI Fails**

Let’s be blunt:

👉 You built **navigation**  
👉 You did NOT build **state-driven UI**

Right now:

- Workspace is static text
- No query to fetch plans
- No rendering logic
- No selection model

So the system **has data**, but the UI **ignores it**

**What You Need to Implement (exactly)**

**1\. Fetch Plans**

In workspace JS:

frappe.call({

method: "frappe.client.get_list",

args: {

doctype: "Strategic Plan",

fields: \["name", "strategic_plan_name", "start_year", "end_year", "status"\],

order_by: "creation desc"

},

callback: function(r) {

render_plans(r.message);

}

});

**2\. Replace Empty State Logic**

**Current (wrong):**

"No strategic plans yet"

**Correct:**

if (plans.length === 0) {

show_empty_state();

} else {

render_plan_list(plans);

select_first_plan();

}

**3\. Render Plan List**

Each item:

• {strategic_plan_name} ({start_year}–{end_year})

Clickable → loads detail panel

**4\. Detail Panel Binding**

When plan selected:

function select_plan(plan) {

current_plan = plan;

render_plan_header(plan);

render_plan_stats(plan);

}

**5\. Add “Open Strategy Builder” CTA**

Critical:

\[ Open Strategy Builder \]

This bridges:

👉 Workspace → Builder (your working feature)

**Minimum Acceptance Criteria (you must enforce this)**

Before moving forward, your Strategy workspace must:

**Data Visibility**

- Created plans are visible immediately
- No false “empty state”

**Navigation**

- Can select a plan
- Selection updates UI

**Actions**

- Can open builder from workspace
- Can create new plan

**Feedback**

- Shows counts (even if 0)

**Hard Truth**

Right now your app is doing this:

“I stored your data successfully… but I won’t show it to you.”

That’s exactly the kind of UX problem that caused your earlier frustration.

**What I Recommend Next (very important)**

Do NOT move forward yet.

👉 Fix this workspace binding FIRST

Then we do:

1.  Workspace reflects plans
2.  Builder reflects hierarchy
3.  Data model enforces structure

Only then do we move to:  
👉 Programs/Objectives UI inside workspace

If you want, next I can give you:

**A drop-in Frappe workspace JS template that implements this cleanly (no trial-and-error)**