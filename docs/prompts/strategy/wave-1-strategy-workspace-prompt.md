# Wave 1 Strategy workspace implementation prompt

**Cursor Prompt — Strategy Workspace Wave 1**

You are implementing the Strategy module workspace shell upgrade.

You MUST follow these rules:

1.  Do not implement the full Strategy module yet.
2.  Do not create the step-based builder yet.
3.  Do not create Programs, Sub-programs, Indicators, or Targets yet.
4.  Only improve the Strategy workspace so it becomes a usable entry point.
5.  Keep implementation minimal, explicit, and testable.
6.  Do not modify unrelated modules or apps.
7.  Work only inside the Kentender custom apps.

Apply these architecture rules:

- Shared infrastructure stays in kentender_core
- Strategy workspace/UI belongs in kentender_strategy
- No cross-app deep imports
- No business logic in DocType controllers
- No hidden dependencies

Apply these Strategy UX rules:

- No long forms
- Workspace-first UX
- Clear next action
- User must understand what to do next
- Navigation must not rely on search
- Empty state must be explicit
- Keep the workspace simple and uncluttered

Implement the next Strategy workspace state with ONLY the following:

**Goal**

Turn the current placeholder Strategy workspace into a usable workspace shell.

**Required UI changes**

**1\. Primary Action**

Add a clearly visible primary action button:

- New Strategic Plan

This button may route to a placeholder/create route for now if the full plan creation flow is not implemented yet.

**2\. Main Content Sections**

Add these visible sections/cards on the Strategy workspace:

- Strategic Plans
- Programs
- Objectives

These are navigation/summary cards only for now.  
Do not implement full feature pages if they do not already exist.  
If needed, use placeholders or disabled/coming-soon style secondary actions, but the cards must exist and be visible.

**3\. Empty State**

Inside the Strategic Plans section, show an empty-state message when there are no plans yet:

- No strategic plans yet. Create one to begin.

**4\. Page Intro**

Replace the current placeholder-only message with a cleaner short intro, for example:

- Create and manage strategic plans and hierarchy.

Keep it short and professional.

**UI expectations**

- Clean layout
- No giant blank page feeling
- Primary action near the top
- Cards/sections clearly separated
- Do not overload the page
- Keep it visually consistent with Frappe/ERPNext workspace patterns

**Do NOT**

- Do not build the full strategy builder
- Do not add workflow
- Do not add complex statistics
- Do not add fake data
- Do not add hidden logic
- Do not introduce raw form-heavy UI

**Acceptance criteria**

The workspace is correct only if all of these are true:

1.  Kentender Strategy icon remains visible from Desk
2.  Clicking it opens Strategy Management
3.  The workspace shows:
    - New Strategic Plan
    - Strategic Plans
    - Programs
    - Objectives
4.  The empty state text is visible when no plans exist:
    - No strategic plans yet. Create one to begin.
5.  The page no longer feels like a dead-end placeholder
6.  No unrelated modules are modified

At the end, provide:

1.  files changed
2.  exact UI elements added
3.  routes/actions wired
4.  anything still left as placeholder

**Add this Playwright check right after implementation**

Use this as your minimum validation:

import { test, expect } from '@playwright/test';

import { loginAsAdministrator } from '../helpers/auth';

import { strategyWorkspace } from '../helpers/selectors';

test('Strategy workspace shell shows actionable entry points', async ({ page }) => {

await loginAsAdministrator(page);

await page.goto(strategyWorkspace.route);

await page.waitForLoadState('networkidle');

await expect(page.getByText(strategyWorkspace.heading).first()).toBeVisible();

await expect(page.getByRole('button', { name: 'New Strategic Plan' })).toBeVisible();

await expect(page.getByText('Strategic Plans')).toBeVisible();

await expect(page.getByText('Programs')).toBeVisible();

await expect(page.getByText('Objectives')).toBeVisible();

await expect(page.getByText('No strategic plans yet. Create one to begin.')).toBeVisible();

});

**What “good” looks like after this prompt**

You should have:

- a visible Strategy Desk icon
- a working Strategy workspace
- a visible primary entry action
- clear empty state
- a page that guides the user toward the next step

That is the right place to stop before implementing actual Strategic Plan creation.