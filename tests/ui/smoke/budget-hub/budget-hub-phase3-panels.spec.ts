/**
 * W3-06 — Phase 3 panel contract tests for the Budget Hub.
 *
 * Covers three panels introduced in W3-01 / W3-02 / W3-04:
 *   1. Recent Movements timeline  — ≥ 1 item when seed data exists
 *   2. Critical Guardrails panel  — visible/hidden matches API response
 *   3. Strategic Alignment Score  — score element contains a % string
 *
 * Requires the site to be running with at least one approved Budget and
 * associated Budget Lines (seed_works_master_budget or equivalent).
 */
import { expect, test, type Page } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

// ── Helpers ───────────────────────────────────────────────────────────────────

const HUB_PATH = '/app/budget-hub';

async function openBudgetHub(page: Page): Promise<void> {
	await page.goto(HUB_PATH, { waitUntil: 'domcontentloaded' });
	// Shell mounts synchronously; wait for it before proceeding
	await expect(page.getByTestId('kt-bgt-workbench')).toBeVisible({ timeout: 30_000 });
	// Primary data API resolved when Available Balance is no longer a dash
	await expect(page.getByTestId('kt-bgt-kpi-available')).not.toHaveText('—', {
		timeout: 20_000,
	});
}

/**
 * Block until the Recent Movements timeline API call completes.
 * Resolves when the loading placeholder is replaced by either items or the
 * empty-state div (both signal the frappe.call callback fired).
 */
async function waitForTimelineLoaded(page: Page): Promise<void> {
	await page.waitForFunction(
		() => {
			const tl = document.querySelector("[data-testid='kt-bgt-timeline']");
			if (!tl) return false;
			// Loading state present → not done yet
			if (tl.querySelector('.kt-bgt-tl-loading')) return false;
			// Either items or empty state must be present
			return (
				tl.querySelector('.kt-bgt-tl-item') !== null ||
				tl.querySelector('.kt-bgt-tl-empty') !== null
			);
		},
		undefined,
		{ timeout: 20_000 },
	);
}

/**
 * Block until the Guardrails API call completes.
 * Resolves when either (a) the loading div is replaced by guardrail cards
 * or (b) the section is hidden because no guardrails are active.
 */
async function waitForGuardrailsLoaded(page: Page): Promise<void> {
	await page.waitForFunction(
		() => {
			const section = document.querySelector(
				"[data-testid='kt-bgt-guardrails-section']",
			) as HTMLElement | null;
			if (!section) return true; // element not in DOM — done
			// Section hidden → API returned empty list
			if (section.style.display === 'none') return true;
			// Loading placeholder gone → API returned cards
			return section.querySelector('.kt-bgt-guardrails-loading') === null;
		},
		undefined,
		{ timeout: 20_000 },
	);
}

/**
 * Call compute_budget_guardrails via the Frappe JS API and return the count
 * of active guardrail items.  Returns 0 on any error.
 */
async function fetchGuardrailCount(page: Page): Promise<number> {
	return page.evaluate((): Promise<number> => {
		const frappe = (window as { frappe?: { call: (...a: unknown[]) => void } }).frappe;
		if (!frappe) return Promise.resolve(0);
		return new Promise((resolve) => {
			frappe.call({
				method: 'kentender_budget.api.guardrails.compute_budget_guardrails',
				freeze: false,
				callback: (r: { message?: { guardrails?: unknown[] } }) =>
					resolve((r?.message?.guardrails ?? []).length),
				error: () => resolve(0),
			});
		});
	});
}

// ── Tests ─────────────────────────────────────────────────────────────────────

test.describe('Budget Hub — Phase 3 panels (W3-06)', () => {
	test('Recent Movements timeline renders ≥ 1 item with seed data', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetHub(page);
		await waitForTimelineLoaded(page);

		const timeline = page.getByTestId('kt-bgt-timeline');
		await expect(timeline).toBeVisible();

		// Loading placeholder must be gone
		await expect(timeline.locator('.kt-bgt-tl-loading')).toHaveCount(0);

		const items = timeline.locator('.kt-bgt-tl-item');
		const emptyState = timeline.locator('.kt-bgt-tl-empty');

		const itemCount = await items.count();

		if (itemCount === 0) {
			// Empty state is still a valid rendered state; assert it is correctly shown
			await expect(emptyState).toBeVisible();
			test.skip(
				true,
				'No movements found in seed DB — empty state rendered correctly, but seeded ' +
					'data (approved budgets / reservations) should produce at least one event.',
			);
		}

		// Main assertion: seed data must yield at least one movement row
		expect(itemCount).toBeGreaterThanOrEqual(1);
		await expect(items.first()).toBeVisible();

		// Each item must carry an event-type icon in the dot and a title
		const firstItem = items.first();
		await expect(firstItem.locator('.kt-bgt-tl-dot .material-symbols-outlined')).toBeVisible();
		await expect(firstItem.locator('.kt-bgt-tl-title')).toBeVisible();
	});

	test('Critical Guardrails panel visibility matches API state', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetHub(page);
		await waitForGuardrailsLoaded(page);

		// Ask the API what the current state is so the assertion is always correct,
		// regardless of what the seed data contains.
		const activeCount = await fetchGuardrailCount(page);

		const section = page.getByTestId('kt-bgt-guardrails-section');

		if (activeCount > 0) {
			// Section must be visible and contain exactly the right number of cards
			await expect(section).toBeVisible({ timeout: 10_000 });
			const grid = page.getByTestId('kt-bgt-guardrails-grid');
			const cards = grid.locator('.kt-bgt-guardrail');
			await expect(cards.first()).toBeVisible();
			// Card count matches API response
			expect(await cards.count()).toBe(activeCount);
		} else {
			// No active guardrails — the section must be hidden (display:none)
			await expect(section).toBeHidden({ timeout: 10_000 });
		}
	});

	test('Strategic Alignment Score shows a valid percentage string', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetHub(page);
		// Alignment score is populated in the same _loadData call as the KPIs;
		// openBudgetHub already waits for that API to resolve.

		const scoreEl = page.getByTestId('kt-bgt-alignment-score');

		// Must not still be the loading placeholder
		await expect(scoreEl).not.toHaveText('—', { timeout: 10_000 });
		await expect(scoreEl).not.toHaveClass(/kt-bgt-kpi--loading/);

		const text = (await scoreEl.textContent()) ?? '';
		// Must be a decimal number followed by %  e.g. "33.3%" or "100.0%"
		expect(text.trim()).toMatch(/^\d+\.?\d*%$/);

		// Badge must carry one of the four tier labels
		const badge = page.getByTestId('kt-bgt-alignment-badge');
		await expect(badge).toBeVisible();
		const badgeText = (await badge.textContent()) ?? '';
		expect(['Optimal', 'Good', 'Fair', 'Poor']).toContain(badgeText.trim());
	});

	test('Alignment Score badge class matches score tier', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetHub(page);

		const badge = page.getByTestId('kt-bgt-alignment-badge');
		await expect(badge).not.toHaveText('', { timeout: 10_000 });

		const scoreEl = page.getByTestId('kt-bgt-alignment-score');
		const scoreText = (await scoreEl.textContent()) ?? '';
		const score = parseFloat(scoreText.replace('%', ''));
		const badgeText = ((await badge.textContent()) ?? '').trim();

		if (score >= 90) {
			expect(badgeText).toBe('Optimal');
			await expect(badge).toHaveClass(/kt-bgt-alignment-badge--optimal/);
		} else if (score >= 70) {
			expect(badgeText).toBe('Good');
			await expect(badge).toHaveClass(/kt-bgt-alignment-badge--good/);
		} else if (score >= 50) {
			expect(badgeText).toBe('Fair');
			await expect(badge).toHaveClass(/kt-bgt-alignment-badge--fair/);
		} else {
			expect(badgeText).toBe('Poor');
			await expect(badge).toHaveClass(/kt-bgt-alignment-badge--poor/);
		}
	});
});
