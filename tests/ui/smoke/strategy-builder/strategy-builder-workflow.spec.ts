/**
 * Workflow action button smoke tests — C18.
 *
 * Verifies that the correct workflow buttons appear in the workbench header
 * based on plan status and the logged-in user's role.
 */
import { test, expect } from '@playwright/test';

import { loginAsStrategyManager, loginAsPlanningAuthority } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

const DRAFT_PLAN     = 'MOH-SP-2026-0031';       // Draft   — editable
const SUBMITTED_PLAN = 'PE-MOH-SP-2026-0078';    // Submitted
const ACTIVE_PLAN    = 'PE-MOH-SP-2026-0077';    // Active
const ARCHIVED_PLAN  = 'PE-MOH-SP-2024-0002';    // Archived

async function openWorkbench(
	page: import('@playwright/test').Page,
	planName: string,
) {
	await openStrategyLanding(page);
	const planCard = page.locator(`[data-plan-name="${planName}"]`);
	await expect(planCard).toBeVisible({ timeout: 25_000 });
	await planCard.locator('.kt-sph-card-title').first().click();
	await expect(page).toHaveURL(/strategy-builder/, { timeout: 20_000 });
	await expect(page.getByTestId('strategy-builder-page')).toBeVisible({ timeout: 60_000 });
}

// ── Draft plan — Strategy Manager sees Submit for Review ──────────────────────

test('Draft plan: Strategy Manager sees Submit for Review button', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openWorkbench(page, DRAFT_PLAN);

	const slot = page.getByTestId('swb-workflow-actions');
	await expect(slot).toBeVisible({ timeout: 15_000 });

	const submitBtn = page.getByTestId('swb-wf-submit');
	await expect(submitBtn).toBeVisible({ timeout: 10_000 });
	await expect(submitBtn).toBeEnabled();
});

test('Draft plan: no Approve / Activate buttons visible for Strategy Manager', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openWorkbench(page, DRAFT_PLAN);

	await expect(page.getByTestId('swb-workflow-actions')).toBeVisible({ timeout: 15_000 });

	await expect(page.getByTestId('swb-wf-approve')).not.toBeVisible();
	await expect(page.getByTestId('swb-wf-activate')).not.toBeVisible();
});

// ── Submitted plan — Planning Authority sees Approve + Return ─────────────────

test('Submitted plan: Planning Authority sees Approve and Return for Correction buttons', async ({ page }) => {
	await loginAsPlanningAuthority(page);
	await openWorkbench(page, SUBMITTED_PLAN);

	const slot = page.getByTestId('swb-workflow-actions');
	await expect(slot).toBeVisible({ timeout: 15_000 });

	await expect(page.getByTestId('swb-wf-approve')).toBeVisible({ timeout: 10_000 });
	await expect(page.getByTestId('swb-wf-return')).toBeVisible({ timeout: 10_000 });
});

test('Submitted plan: Strategy Manager does NOT see Approve button', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openWorkbench(page, SUBMITTED_PLAN);

	/* Strategy Manager has no PA role — no approve or return buttons rendered */
	await expect(page.getByTestId('swb-wf-approve')).not.toBeVisible({ timeout: 15_000 });
});

// ── Active plan — Planning Authority sees Archive ─────────────────────────────

test('Active plan: Planning Authority sees Archive button', async ({ page }) => {
	await loginAsPlanningAuthority(page);
	await openWorkbench(page, ACTIVE_PLAN);

	const slot = page.getByTestId('swb-workflow-actions');
	await expect(slot).toBeVisible({ timeout: 15_000 });

	await expect(page.getByTestId('swb-wf-archive')).toBeVisible({ timeout: 10_000 });
});

test('Active plan: no Submit / Approve / Activate buttons visible', async ({ page }) => {
	await loginAsPlanningAuthority(page);
	await openWorkbench(page, ACTIVE_PLAN);

	await expect(page.getByTestId('swb-workflow-actions')).toBeVisible({ timeout: 15_000 });

	await expect(page.getByTestId('swb-wf-submit')).not.toBeVisible();
	await expect(page.getByTestId('swb-wf-approve')).not.toBeVisible();
	await expect(page.getByTestId('swb-wf-activate')).not.toBeVisible();
});

// ── Archived plan — no workflow buttons ───────────────────────────────────────

test('Archived plan: no workflow action buttons visible', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openWorkbench(page, ARCHIVED_PLAN);

	/* Slot exists but should be empty — no buttons rendered for archived plans */
	await expect(page.getByTestId('strategy-builder-page')).toBeVisible({ timeout: 20_000 });
	await expect(page.getByTestId('swb-wf-submit')).not.toBeVisible();
	await expect(page.getByTestId('swb-wf-approve')).not.toBeVisible();
	await expect(page.getByTestId('swb-wf-activate')).not.toBeVisible();
	await expect(page.getByTestId('swb-wf-archive')).not.toBeVisible();
});
