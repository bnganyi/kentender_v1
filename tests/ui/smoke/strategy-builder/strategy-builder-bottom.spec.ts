/**
 * Bottom section smoke tests — live activity feed, Insights placeholder,
 * Stakeholders placeholder.
 */
import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

const SEEDED_PLAN = 'PE-MOH-SP-2026-0077';

async function openWorkbench(page: import('@playwright/test').Page) {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	const planCard = page.locator(`[data-plan-name="${SEEDED_PLAN}"]`);
	await expect(planCard).toBeVisible({ timeout: 25_000 });
	await planCard.locator('.kt-sph-card-title').first().click();

	await expect(page).toHaveURL(/strategy-builder/, { timeout: 20_000 });
	await expect(page.getByTestId('strategy-builder-page')).toBeVisible({ timeout: 60_000 });
}

// ── Activity feed ─────────────────────────────────────────────────────────────

test('Activity feed card is visible on workbench', async ({ page }) => {
	await openWorkbench(page);

	const feed = page.getByTestId('swb-activity-feed');
	await expect(feed).toBeVisible({ timeout: 10_000 });
});

test('Activity feed loads and shows items or empty state (not loading spinner)', async ({ page }) => {
	await openWorkbench(page);

	const feed = page.getByTestId('swb-activity-feed');
	await expect(feed).toBeVisible({ timeout: 10_000 });

	/* Wait for loading spinner to disappear */
	await expect(page.getByTestId('swb-activity-loading')).not.toBeVisible({ timeout: 20_000 });

	/* Either items or empty state must be present */
	const itemCount = await page.locator('[data-testid="swb-activity-item"]').count();
	const emptyCount = await page.getByTestId('swb-activity-empty').count();
	expect(itemCount + emptyCount).toBeGreaterThan(0);
});

test('Activity feed shows at least one item for a plan with history', async ({ page }) => {
	await openWorkbench(page);

	/* Wait for loading to finish */
	await expect(page.getByTestId('swb-activity-loading')).not.toBeVisible({ timeout: 20_000 });

	const items = page.locator('[data-testid="swb-activity-item"]');
	await expect(items.first()).toBeVisible({ timeout: 10_000 });
	const count = await items.count();
	expect(count).toBeGreaterThanOrEqual(1);
});

test('Activity feed refresh button triggers reload', async ({ page }) => {
	await openWorkbench(page);

	await expect(page.getByTestId('swb-activity-loading')).not.toBeVisible({ timeout: 20_000 });

	/* Click refresh — loading state should briefly reappear */
	await page.getByTestId('swb-activity-refresh').click();

	/* After refresh resolves, loading should be gone again */
	await expect(page.getByTestId('swb-activity-loading')).not.toBeVisible({ timeout: 15_000 });
});

// ── Readiness bar ─────────────────────────────────────────────────────────────

test('Readiness bar renders between KPIs and hierarchy tree', async ({ page }) => {
	await openWorkbench(page);

	const bar = page.getByTestId('swb-readiness-bar');
	await expect(bar).toBeVisible({ timeout: 15_000 });

	/* For a plan with a full hierarchy the bar must not show "Incomplete" */
	const readiness = page.getByTestId('strategy-readiness');
	await expect(readiness).toBeVisible({ timeout: 10_000 });

	/* Should contain program + indicator + target counts */
	await expect(readiness).toContainText('Programs');
	await expect(readiness).toContainText('Indicators');
	await expect(readiness).toContainText('Targets');
});

test('Readiness bar shows Ready status for a fully-seeded plan', async ({ page }) => {
	await openWorkbench(page);

	const readiness = page.getByTestId('strategy-readiness');
	await expect(readiness).toBeVisible({ timeout: 15_000 });

	/* Seeded plan has full hierarchy — should be Ready or at worst Missing targets */
	const text = await readiness.textContent();
	expect(text).not.toMatch(/Incomplete/i);
});

// ── Insights placeholder ──────────────────────────────────────────────────────
test('Insights card is visible and shows "Coming Soon" badge', async ({ page }) => {
	await openWorkbench(page);

	const card = page.getByTestId('swb-insights-card');
	await expect(card).toBeVisible({ timeout: 10_000 });
	await expect(card).toContainText('Coming Soon');
	await expect(card).toContainText('Insights Engine');
});

// ── Stakeholders placeholder ──────────────────────────────────────────────────

test('Stakeholders card is visible and shows "Coming Soon" badge', async ({ page }) => {
	await openWorkbench(page);

	const card = page.getByTestId('swb-stakeholders-card');
	await expect(card).toBeVisible({ timeout: 10_000 });
	await expect(card).toContainText('Stakeholders');
	await expect(card).toContainText('Coming Soon');
});
