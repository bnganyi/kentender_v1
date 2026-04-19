**Strategy Landing Page — Playwright Contract**

**Scope**

This contract validates the Strategy landing page as a **master-detail workspace**.

It must prove:

- Strategy workspace is reachable
- plans are shown when they exist
- empty state works when no plans exist
- selected plan details are rendered
- actions are visible and routed correctly
- role-based visibility behaves correctly

It must not yet try to validate:

- approvals
- version workflow
- builder internals beyond entry action
- deep hierarchy editing

**Required test ids**

Before relying on brittle text selectors, make Cursor add these stable test ids.

**Landing page container**

- strategy-landing-page
- strategy-page-title
- strategy-page-intro

**Plan list**

- strategic-plans-section
- strategic-plan-create-button
- strategic-plan-list
- strategic-plan-row-&lt;plan_name&gt;
- strategic-plan-row-title-&lt;plan_name&gt;
- strategic-plan-row-years-&lt;plan_name&gt;
- strategic-plan-row-status-&lt;plan_name&gt;
- strategic-plan-row-selected-&lt;plan_name&gt;

**Selected plan panel**

- selected-plan-panel
- selected-plan-title
- selected-plan-status
- selected-plan-years
- selected-plan-program-count
- selected-plan-objective-count
- selected-plan-target-count
- selected-plan-open-builder
- selected-plan-edit-plan

**Empty state**

- strategic-plans-empty-state

**Optional role/visibility hooks**

- strategy-workspace-link

**Test file structure**

tests/ui/smoke/strategy-landing/

strategy-landing-empty.spec.ts

strategy-landing-populated.spec.ts

strategy-landing-selection.spec.ts

strategy-landing-actions.spec.ts

strategy-landing-role-visibility.spec.ts

**Seed assumptions**

These tests assume the seed packs from the seed specification exist.

**For empty-state tests**

Use:

- seed_core_minimal
- seed_strategy_empty

**For populated tests**

Use:

- seed_core_minimal
- seed_strategy_basic

**For multi-plan selection tests**

Use:

- seed_core_minimal
- seed_strategy_extended

**User assumptions**

Use these seeded users:

- strategy.manager@moh.test
- planning.authority@moh.test
- requisitioner@moh.test

Administrator may still be used for setup or fallback, but these tests should stop relying on Administrator as the main actor.

**Helper recommendation**

Add a helper:

tests/ui/helpers/strategyLanding.ts

import { Page, expect } from '@playwright/test';

export async function openStrategyLanding(page: Page) {

await page.goto('/desk/strategy-management');

await page.waitForLoadState('networkidle');

await expect(page.getByTestId('strategy-landing-page')).toBeVisible();

}

**Test 1 — Empty state is correct**

**File**

strategy-landing-empty.spec.ts

**Purpose**

Verify that when no plans exist, the page shows the correct empty state and create action.

**Contract**

- page loads
- Strategic Plans section visible
- empty-state message visible
- no selected-plan panel content
- create button visible for Strategy Manager
- no plan rows visible

**Example**

import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';

import { openStrategyLanding } from '../../helpers/strategyLanding';

test('Strategy landing shows correct empty state when no plans exist', async ({ page }) => {

await loginAsStrategyManager(page);

await openStrategyLanding(page);

await expect(page.getByTestId('strategic-plans-section')).toBeVisible();

await expect(page.getByTestId('strategic-plans-empty-state')).toContainText(

'No strategic plans yet. Create one to begin.'

);

await expect(page.getByTestId('strategic-plan-create-button')).toBeVisible();

await expect(page.locator('\[data-testid^="strategic-plan-row-"\]')).toHaveCount(0);

});

**Test 2 — Populated state shows plans**

**File**

strategy-landing-populated.spec.ts

**Purpose**

Verify that seeded plans appear and empty state disappears.

**Contract**

- plans list visible
- seeded plan appears
- empty state not shown
- selected plan panel visible
- counts render

**Example**

import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';

import { openStrategyLanding } from '../../helpers/strategyLanding';

test('Strategy landing shows seeded plans when plans exist', async ({ page }) => {

await loginAsStrategyManager(page);

await openStrategyLanding(page);

await expect(page.getByTestId('strategic-plan-list')).toBeVisible();

await expect(page.getByText('MOH Strategic Plan 2026–2030')).toBeVisible();

await expect(page.getByTestId('strategic-plans-empty-state')).toHaveCount(0);

await expect(page.getByTestId('selected-plan-panel')).toBeVisible();

await expect(page.getByTestId('selected-plan-title')).toBeVisible();

await expect(page.getByTestId('selected-plan-program-count')).toBeVisible();

await expect(page.getByTestId('selected-plan-objective-count')).toBeVisible();

await expect(page.getByTestId('selected-plan-target-count')).toBeVisible();

});

**Test 3 — Default selection works**

**File**

strategy-landing-selection.spec.ts

**Purpose**

Verify that when plans exist, one plan is selected by default.

**Contract**

- first plan auto-selected
- selected-plan panel reflects selected row
- selected style marker exists

**Example**

import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';

import { openStrategyLanding } from '../../helpers/strategyLanding';

test('Strategy landing auto-selects a plan by default', async ({ page }) => {

await loginAsStrategyManager(page);

await openStrategyLanding(page);

await expect(page.getByTestId('selected-plan-panel')).toBeVisible();

await expect(page.getByTestId('selected-plan-title')).not.toHaveText('');

});

If you have deterministic sorting and a stable selected row id, tighten this later.

**Test 4 — Changing selection updates the detail panel**

**File**

strategy-landing-selection.spec.ts

**Purpose**

Verify master-detail interaction.

**Contract**

- click another plan
- selected panel updates
- selection highlight moves

**Example**

test('Selecting another plan updates the detail panel', async ({ page }) => {

await loginAsStrategyManager(page);

await openStrategyLanding(page);

await page.getByText('MOH Service Delivery Improvement Plan 2027–2031').click();

await expect(page.getByTestId('selected-plan-title')).toContainText(

'MOH Service Delivery Improvement Plan 2027–2031'

);

});

With test ids, this should be based on row ids rather than plain text.

**Test 5 — Open Strategy Builder action works**

**File**

strategy-landing-actions.spec.ts

**Purpose**

Verify that selected plan can open the builder.

**Contract**

- action button visible
- click routes correctly
- builder route contains selected plan id or name

**Example**

import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';

import { openStrategyLanding } from '../../helpers/strategyLanding';

test('Open Strategy Builder action routes correctly', async ({ page }) => {

await loginAsStrategyManager(page);

await openStrategyLanding(page);

await page.getByTestId('selected-plan-open-builder').click();

await expect(page).toHaveURL(/strategy-builder/);

});

If builder page has a test id like strategy-builder-page, add that assertion too.

**Test 6 — Edit Plan action works**

**File**

strategy-landing-actions.spec.ts

**Purpose**

Verify that selected plan can open its plan form.

**Contract**

- edit button visible
- click routes to Strategic Plan document
- expected heading visible

**Example**

test('Edit Plan action routes correctly', async ({ page }) => {

await loginAsStrategyManager(page);

await openStrategyLanding(page);

await page.getByTestId('selected-plan-edit-plan').click();

await expect(page).toHaveURL(/strategic-plan/);

await expect(page.getByText(/Strategic Plan/i).first()).toBeVisible();

});

**Test 7 — Counts are correct for seeded basic plan**

**File**

strategy-landing-populated.spec.ts

**Purpose**

Verify that counts reflect seeded data.

**Contract**

Using seed_strategy_basic, selected seeded plan should show:

- Programs: 2
- Objectives: 3
- Targets: 4

**Example**

test('Selected plan shows correct seeded counts', async ({ page }) => {

await loginAsStrategyManager(page);

await openStrategyLanding(page);

await expect(page.getByTestId('selected-plan-title')).toContainText('MOH Strategic Plan 2026–2030');

await expect(page.getByTestId('selected-plan-program-count')).toContainText('2');

await expect(page.getByTestId('selected-plan-objective-count')).toContainText('3');

await expect(page.getByTestId('selected-plan-target-count')).toContainText('4');

});

**Test 8 — Strategy Manager sees create action**

**File**

strategy-landing-role-visibility.spec.ts

**Purpose**

Validate mutation visibility for Strategy Manager.

**Contract**

- Strategy workspace visible
- create button visible
- builder action visible
- edit action visible

**Example**

import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';

import { openStrategyLanding } from '../../helpers/strategyLanding';

test('Strategy Manager sees Strategy landing and mutation actions', async ({ page }) => {

await loginAsStrategyManager(page);

await openStrategyLanding(page);

await expect(page.getByTestId('strategic-plan-create-button')).toBeVisible();

await expect(page.getByTestId('selected-plan-open-builder')).toBeVisible();

await expect(page.getByTestId('selected-plan-edit-plan')).toBeVisible();

});

**Test 9 — Planning Authority sees Strategy landing but not create/edit**

**File**

strategy-landing-role-visibility.spec.ts

**Purpose**

Validate read-only review behavior.

**Contract**

- Strategy workspace visible
- plans visible
- create action hidden
- edit action hidden
- builder visible only if review mode is allowed

**Example**

import { test, expect } from '@playwright/test';

import { loginAsPlanningAuthority } from '../../helpers/auth';

import { openStrategyLanding } from '../../helpers/strategyLanding';

test('Planning Authority sees Strategy landing in review mode', async ({ page }) => {

await loginAsPlanningAuthority(page);

await openStrategyLanding(page);

await expect(page.getByTestId('strategic-plan-list')).toBeVisible();

await expect(page.getByTestId('strategic-plan-create-button')).toHaveCount(0);

await expect(page.getByTestId('selected-plan-edit-plan')).toHaveCount(0);

// Keep or remove depending on final read-only builder policy

await expect(page.getByTestId('selected-plan-open-builder')).toBeVisible();

});

**Test 10 — Requisitioner cannot see Strategy workspace**

**File**

strategy-landing-role-visibility.spec.ts

**Purpose**

Validate that non-Strategy roles are excluded.

**Contract**

- Strategy workspace link not visible in normal navigation
- direct route should fail gracefully or deny access depending on implementation

**Example**

import { test, expect } from '@playwright/test';

import { loginAsRequisitioner } from '../../helpers/auth';

test('Requisitioner does not see Strategy workspace', async ({ page }) => {

await loginAsRequisitioner(page);

await page.goto('/desk');

await page.waitForLoadState('networkidle');

await expect(page.getByText('Strategy')).toHaveCount(0);

});

And if you want direct-route denial tested:

test('Requisitioner cannot access Strategy landing directly', async ({ page }) => {

await loginAsRequisitioner(page);

await page.goto('/desk/strategy-management');

await page.waitForLoadState('networkidle');

await expect(page.locator('body')).not.toContainText('Strategy Management');

});

Adjust depending on how access denial is implemented.

**Test 11 — Create action leads to new Strategic Plan form**

**File**

strategy-landing-actions.spec.ts

**Purpose**

Validate entry point from landing page.

**Contract**

- create button routes to create form
- expected fields visible

**Example**

test('New Strategic Plan action opens create form', async ({ page }) => {

await loginAsStrategyManager(page);

await openStrategyLanding(page);

await page.getByTestId('strategic-plan-create-button').click();

await expect(page).toHaveURL(/strategic-plan\\/new-/);

await expect(page.getByText(/Strategic Plan Name/i)).toBeVisible();

});

**Minimum acceptance gate**

Do not move forward unless these pass:

1\. Empty state works when no plans exist

2\. Plans appear when seeded plans exist

3\. Default selection works

4\. Selection updates detail panel

5\. Open Strategy Builder works

6\. Edit Plan works

7\. Strategy Manager sees mutation actions

8\. Planning Authority sees review-only view

9\. Requisitioner does not see Strategy

That is the correct MVP confidence level for this landing page.

**Cursor prompt to support testing**

Use this to force the UI to become testable.

Refine the Strategy landing page implementation to be Playwright-testable.

Add stable data-testid attributes for:

- strategy-landing-page
- strategy-page-title
- strategy-page-intro
- strategic-plans-section
- strategic-plan-create-button
- strategic-plan-list
- selected-plan-panel
- selected-plan-title
- selected-plan-status
- selected-plan-years
- selected-plan-program-count
- selected-plan-objective-count
- selected-plan-target-count
- selected-plan-open-builder
- selected-plan-edit-plan
- strategic-plans-empty-state

Also add stable row ids for each plan:

- strategic-plan-row-&lt;plan_name&gt;
- strategic-plan-row-title-&lt;plan_name&gt;
- strategic-plan-row-years-&lt;plan_name&gt;
- strategic-plan-row-status-&lt;plan_name&gt;

Do not change behavior unless needed to expose stable test hooks.  
Do not remove current functionality.

**Recommended next move**

After this contract is implemented and passing, the next high-value step is:

**role-aware testing of the Strategy Builder itself**

- Strategy Manager = mutate
- Planning Authority = read-only
- Requisitioner = denied

That is where the system stops being a developer prototype and starts behaving like a governed product.