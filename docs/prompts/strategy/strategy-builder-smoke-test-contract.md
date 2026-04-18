**Strategy Builder — Smoke Test Contract**

This is not a full end-to-end suite. It is the minimum set of tests that will tell you whether Cursor has built a usable builder or just another impressive-looking broken screen.

**Goal**

Prove that the Strategy Builder is:

- reachable
- usable
- tree-based
- editable without raw-form dependency
- structurally valid

**1\. What this smoke suite must catch**

It must fail if Cursor does any of these:

- opens a blank page
- falls back to raw Frappe forms
- renders no tree
- lets invalid hierarchy be created
- navigates away for normal editing
- does not update right pane on selection
- hides add actions in unusable places

**2\. Test file set**

Use this structure under your existing UI tests:

tests/ui/smoke/strategy-builder/

strategy-builder-route.spec.ts

strategy-builder-shell.spec.ts

strategy-builder-add-program.spec.ts

strategy-builder-add-objective.spec.ts

strategy-builder-add-target.spec.ts

strategy-builder-selection.spec.ts

strategy-builder-invalid-hierarchy.spec.ts

**3\. Required selectors / test ids**

Before you test this seriously, make Cursor add stable test ids.

**Minimum required**

data-testid="strategy-builder-page"

data-testid="strategy-tree-pane"

data-testid="strategy-editor-pane"

data-testid="add-program-button"

data-testid="add-objective-button"

data-testid="add-target-button"

data-testid="empty-tree-message"

data-testid="selected-node-type"

data-testid="node-title-input"

data-testid="node-description-input"

data-testid="target-year-input"

data-testid="target-value-input"

data-testid="target-unit-input"

data-testid="save-node-button"

data-testid="tree-node-&lt;name&gt;"

Without these, your tests will become brittle fast.

**4\. Preconditions**

Before running builder tests:

- login works
- Strategy workspace exists
- “New Strategic Plan” flow works
- at least one Strategic Plan can be created

You can either:

- seed one test plan in setup
- or create one inside the first test

For reliability, I recommend **seed once, use repeatedly**.

Example plan:

- TEST-SP-2026
- title: Test Strategic Plan 2026–2030

**5\. Smoke test 1 — Builder route opens**

**Purpose**

Confirm the custom builder page exists and loads.

**Checks**

- page loads
- tree pane visible
- editor pane visible
- not blank
- not raw DocType form

**Example**

import { test, expect } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

test('Strategy Builder route opens', async ({ page }) => {

await loginAsAdministrator(page);

await page.goto('/app/strategy-builder/TEST-SP-2026');

await page.waitForLoadState('networkidle');

await expect(page.getByTestId('strategy-builder-page')).toBeVisible();

await expect(page.getByTestId('strategy-tree-pane')).toBeVisible();

await expect(page.getByTestId('strategy-editor-pane')).toBeVisible();

await expect(page.locator('body')).not.toHaveText(/^$/);

await expect(page.getByLabel(/title/i)).toHaveCount(0);

});

The last check helps catch fallback to raw form behavior.

**6\. Smoke test 2 — Empty builder state is correct**

**Purpose**

Confirm first-time user guidance is present.

**Checks**

- empty tree guidance visible
- Add Program available
- Add Objective / Add Target disabled or hidden until valid parent selected

**Example**

test('Empty Strategy Builder shows correct first action', async ({ page }) => {

await loginAsAdministrator(page);

await page.goto('/app/strategy-builder/TEST-SP-2026');

await page.waitForLoadState('networkidle');

await expect(page.getByTestId('empty-tree-message')).toBeVisible();

await expect(page.getByTestId('add-program-button')).toBeVisible();

await expect(page.getByTestId('add-objective-button')).toBeDisabled();

await expect(page.getByTestId('add-target-button')).toBeDisabled();

});

**7\. Smoke test 3 — Add Program**

**Purpose**

Confirm root node creation works.

**Checks**

- Add Program action works
- new Program appears in tree
- selecting it populates editor pane
- no navigation away occurs

**Example**

test('Can add Program node', async ({ page }) => {

await loginAsAdministrator(page);

await page.goto('/app/strategy-builder/TEST-SP-2026');

await page.waitForLoadState('networkidle');

await page.getByTestId('add-program-button').click();

await page.getByTestId('node-title-input').fill('Healthcare Delivery');

await page.getByTestId('node-description-input').fill('Top-level program');

await page.getByTestId('save-node-button').click();

await expect(page.getByText('Healthcare Delivery')).toBeVisible();

await expect(page).toHaveURL(/strategy-builder/);

await expect(page.getByTestId('selected-node-type')).toHaveText(/Program/i);

});

**8\. Smoke test 4 — Add Objective under Program**

**Purpose**

Confirm child-node creation under correct parent.

**Checks**

- objective can only be added after Program selected
- new Objective appears nested under Program
- editor pane updates correctly

**Example**

test('Can add Objective under Program', async ({ page }) => {

await loginAsAdministrator(page);

await page.goto('/app/strategy-builder/TEST-SP-2026');

await page.waitForLoadState('networkidle');

await page.getByText('Healthcare Delivery').click();

await expect(page.getByTestId('add-objective-button')).toBeEnabled();

await page.getByTestId('add-objective-button').click();

await page.getByTestId('node-title-input').fill('Increase rural access');

await page.getByTestId('node-description-input').fill('Improve services in rural areas');

await page.getByTestId('save-node-button').click();

await expect(page.getByText('Increase rural access')).toBeVisible();

await expect(page.getByTestId('selected-node-type')).toHaveText(/Objective/i);

});

**9\. Smoke test 5 — Add Target under Objective**

**Purpose**

Confirm third-level node creation and Target-specific fields.

**Checks**

- target only allowed under Objective
- target-specific fields visible
- target saved and shown in tree

**Example**

test('Can add Target under Objective', async ({ page }) => {

await loginAsAdministrator(page);

await page.goto('/app/strategy-builder/TEST-SP-2026');

await page.waitForLoadState('networkidle');

await page.getByText('Increase rural access').click();

await expect(page.getByTestId('add-target-button')).toBeEnabled();

await page.getByTestId('add-target-button').click();

await page.getByTestId('node-title-input').fill('Expand district facilities');

await page.getByTestId('target-year-input').fill('2026');

await page.getByTestId('target-value-input').fill('25');

await page.getByTestId('target-unit-input').fill('Facilities');

await page.getByTestId('save-node-button').click();

await expect(page.getByText('Expand district facilities')).toBeVisible();

await expect(page.getByTestId('selected-node-type')).toHaveText(/Target/i);

});

**10\. Smoke test 6 — Selection updates editor pane**

**Purpose**

Catch broken tree/editor synchronization.

**Checks**

- selecting Program shows Program fields only
- selecting Objective shows Objective fields only
- selecting Target shows Target fields including target details

**Example**

test('Selecting nodes updates editor pane correctly', async ({ page }) => {

await loginAsAdministrator(page);

await page.goto('/app/strategy-builder/TEST-SP-2026');

await page.waitForLoadState('networkidle');

await page.getByText('Healthcare Delivery').click();

await expect(page.getByTestId('selected-node-type')).toHaveText(/Program/i);

await page.getByText('Increase rural access').click();

await expect(page.getByTestId('selected-node-type')).toHaveText(/Objective/i);

await page.getByText('Expand district facilities').click();

await expect(page.getByTestId('selected-node-type')).toHaveText(/Target/i);

await expect(page.getByTestId('target-year-input')).toBeVisible();

await expect(page.getByTestId('target-value-input')).toBeVisible();

});

**11\. Smoke test 7 — Invalid hierarchy is blocked**

**Purpose**

Catch the most dangerous structural regression.

**Invalid cases**

- Objective without Program
- Target without Objective
- Target under Program
- Program under Program if not intended

**Example**

test('Invalid hierarchy actions are blocked', async ({ page }) => {

await loginAsAdministrator(page);

await page.goto('/app/strategy-builder/TEST-SP-2026');

await page.waitForLoadState('networkidle');

// With no selection, objective and target must not be addable

await expect(page.getByTestId('add-objective-button')).toBeDisabled();

await expect(page.getByTestId('add-target-button')).toBeDisabled();

// Select Program, target should still not be directly addable

await page.getByText('Healthcare Delivery').click();

await expect(page.getByTestId('add-target-button')).toBeDisabled();

});

**12\. Optional smoke test 8 — No raw-form editing required**

**Purpose**

Ensure normal editing stays inside builder.

**Checks**

- no route change to /desk/strategy-node/...
- no new form page opens during normal add/edit/save

**Example**

test('Builder editing does not navigate to raw forms', async ({ page }) => {

await loginAsAdministrator(page);

await page.goto('/app/strategy-builder/TEST-SP-2026');

await page.waitForLoadState('networkidle');

await page.getByText('Healthcare Delivery').click();

await page.getByTestId('node-title-input').fill('Healthcare Delivery Updated');

await page.getByTestId('save-node-button').click();

await expect(page).toHaveURL(/strategy-builder/);

await expect(page.url()).not.toMatch(/strategy-node/);

});

**13\. Helper recommendation**

Add a dedicated helper:

tests/ui/helpers/strategyBuilder.ts

import { Page, expect } from '@playwright/test';

export async function openStrategyBuilder(page: Page, planName: string) {

await page.goto(\`/app/strategy-builder/${planName}\`);

await page.waitForLoadState('networkidle');

await expect(page.getByTestId('strategy-builder-page')).toBeVisible();

}

This keeps your tests clean.

**14\. Builder acceptance gate**

Do **not** move beyond first builder implementation unless all of these are true:

1\. Builder route loads

2\. Empty state is clear

3\. Program can be added

4\. Objective can be added under Program

5\. Target can be added under Objective

6\. Selection updates editor pane

7\. Invalid hierarchy is blocked

8\. No raw-form navigation is required

If any one fails, the builder is not ready.

**15\. Cursor instruction to support testing**

Give Cursor this alongside implementation:

When implementing the Strategy Builder, add stable data-testid attributes for all major UI elements needed by Playwright.

Required test ids:

- strategy-builder-page
- strategy-tree-pane
- strategy-editor-pane
- add-program-button
- add-objective-button
- add-target-button
- empty-tree-message
- selected-node-type
- node-title-input
- node-description-input
- target-year-input
- target-value-input
- target-unit-input
- save-node-button

Do not rely only on CSS classes or fragile text selectors.

**16\. My recommendation**

Start by implementing only these three tests first:

- builder route opens
- add Program
- invalid hierarchy blocked

That gives you fast feedback without overloading the first iteration.

Once those pass, add:

- Objective
- Target
- selection sync

That’s the right pacing.