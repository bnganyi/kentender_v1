# Strategy Workspace UI Fix Prompt

Use this as the **Cursor prompt**.

It is intentionally narrow: bind the Strategy workspace to real Strategic Plan data and make it usable as a master-detail landing page.

Implement the Strategy workspace as a data-bound master-detail landing page.

Goal:  
When Strategic Plans exist, the workspace must show them instead of a false empty state.

Scope:  
Only update the Strategy workspace UI and its client-side data binding.  
Do not redesign the builder.  
Do not change the Strategy data model.  
Do not add workflow.

Requirements:

1.  Fetch Strategic Plans

- Query Strategic Plan records from Frappe
- Use fields:
    - name
    - strategic_plan_name
    - start_year
    - end_year
    - status
    - modified
- Order by newest first

1.  Replace static empty state

- If no plans exist:
    - show:  
        "No strategic plans yet. Create one to begin."
- If plans exist:
    - do NOT show the empty-state message

1.  Render a Strategic Plans list

- Show the plans in the workspace under "Strategic Plans"
- Each row/card must show:
    - strategic_plan_name
    - years as start_year–end_year
    - status
- Each plan must be clickable
- Clicking a plan must select it in the workspace, not navigate away immediately

1.  Render selected plan detail in the same workspace  
    For the currently selected plan, show:

- strategic_plan_name
- status
- years
- actions:
    - Open Strategy Builder
    - Edit Plan

1.  Open Strategy Builder

- "Open Strategy Builder" must route to:  
    /app/strategy-builder/&lt;plan_name&gt;

1.  Edit Plan

- "Edit Plan" must route to the Strategic Plan document route for that record

1.  Default selection

- When plans exist, automatically select the first plan returned

1.  Counts  
    For the selected plan, show counts:

- Programs
- Objectives
- Targets

If there is no hierarchy data yet, show 0  
If records exist, count them correctly

1.  UI behavior

- Keep layout simple and clean
- Avoid giant blank space
- Make the workspace feel like a real landing page
- No raw JSON or debug output
- No search dependency
- No fake data

1.  Suggested layout  
    Use a two-column workspace content layout:

Left:

- Strategic Plans list

Right:

- Selected Plan detail
- Actions
- Counts

1.  Acceptance criteria  
    The implementation is correct only if:

- Creating a Strategic Plan makes it appear in the workspace
- Empty state disappears when plans exist
- A plan can be selected
- Selected plan details are shown
- Open Strategy Builder works
- Edit Plan works
- Counts render without errors

Implementation notes:

- Keep this as workspace/page JS logic
- Do not modify unrelated modules
- Do not redesign the full workspace framework
- Use existing Frappe APIs / frappe.call / frappe.db calls appropriately

At the end provide:

1.  files changed
2.  data-fetch method used
3.  render structure used
4.  routes wired
5.  any placeholders still remaining

And add this **Playwright smoke test** right after it:

import { test, expect } from '@playwright/test';

import { loginAsAdministrator } from '../helpers/auth';

import { strategyWorkspace } from '../helpers/selectors';

test('Strategy workspace shows created plans and selected-plan actions', async ({ page }) => {

await loginAsAdministrator(page);

await page.goto(strategyWorkspace.route);

await page.waitForLoadState('networkidle');

await expect(page.getByText('Strategic Plans')).toBeVisible();

// Replace with your actual seeded plan title

await expect(page.getByText('test')).toBeVisible();

await page.getByText('test').click();

await expect(page.getByRole('button', { name: /Open Strategy Builder/i })).toBeVisible();

await expect(page.getByRole('button', { name: /Edit Plan/i })).toBeVisible();

await expect(page.getByText(/Programs:/i)).toBeVisible();

await expect(page.getByText(/Objectives:/i)).toBeVisible();

await expect(page.getByText(/Targets:/i)).toBeVisible();

});

And update your selectors helper with at least:

export const strategyWorkspace = {

heading: 'Strategy Management',

route: '/app/strategy-management',

};

One important note: for the seeded plan title, use the **actual field shown in the workspace**. If the UI shows strategic_plan_name, the test should look for that exact text, not the document name.