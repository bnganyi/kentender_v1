/**
 * Budget Revision Workflow — Playwright smoke tests (r6-smoke)
 *
 * Uses test.describe.serial: tests run in order sharing a single revision
 * document created in beforeAll. This avoids the "duplicate revision" unique
 * constraint problem when the test is run multiple times.
 *
 * Happy path covered:
 *   1. "Revise Budget" button is visible on an Active budget workbench.
 *   2. Revision workbench shows revision banner ("Revision of <predecessor>").
 *   3. Revision workbench shows "Submit Revision" button (Draft state).
 *   4. Submitting the revision shows "Approve Revision" button.
 *   5. Approving the revision: title chip shows "Active".
 */
import { expect, test, type Browser, type Page } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

// ── Helpers ───────────────────────────────────────────────────────────────────

const WORKBENCH_PATH = (name: string) =>
	`/app/budget-workbench/${encodeURIComponent(name)}`;

async function openWorkbench(page: Page, budgetName: string): Promise<void> {
	await page.goto(WORKBENCH_PATH(budgetName), { waitUntil: 'domcontentloaded' });
	await expect(page.getByTestId('kt-wbench-root')).toBeVisible({ timeout: 30_000 });
	await expect(page.getByTestId('kt-wbench-title')).not.toHaveClass(/kt-wbench-skel/, {
		timeout: 20_000,
	});
	await page.waitForFunction(
		() =>
			document.querySelector(
				"[data-testid='kt-wbench-lines-list'] .kt-wbench-lines-loading",
			) === null,
		undefined,
		{ timeout: 20_000 },
	);
}

/**
 * Find the name of the current Active budget in the BUDGET-SDT/DOE seed chain.
 * First tries original (no predecessor). On subsequent runs after approval, the
 * original becomes "Revised" and the chain's latest revision is Active — so we
 * fall back to any Active budget whose budget_name starts with BUDGET-.
 */
async function findOriginalActiveBudget(page: Page): Promise<string> {
	const name = await page.evaluate(async () => {
		const f = (window as unknown as { frappe: { call: Function } }).frappe;

		// Helper: get_list wrapper
		const getList = (filters: unknown[], fields: string[]): Promise<Array<{ name: string }>> =>
			new Promise((resolve) => {
				f.call({
					method: 'frappe.client.get_list',
					args: { doctype: 'Budget', filters, fields, order_by: 'name asc', limit: 1 },
					callback: (r: { message?: Array<{ name: string }> }) => resolve(r?.message ?? []),
				});
			});

		// 1st choice: original seed budget still Active
		let rows = await getList(
			[['status', '=', 'Active'], ['budget_name', 'like', 'BUDGET-%'], ['supersedes_budget', 'is', 'not set']],
			['name'],
		);
		if (rows[0]) return rows[0].name;

		// 2nd choice: promoted revision of a seed budget still Active
		rows = await getList(
			[['status', '=', 'Active'], ['budget_name', 'like', 'BUDGET-%']],
			['name'],
		);
		if (rows[0]) return rows[0].name;

		return null;
	});
	if (!name) throw new Error('No seed Active Budget found. Ensure BUDGET-SDT-2026 or BUDGET-DOE-2026 exists and is Active (or has an Active revision).');
	return name;
}

/**
 * Cancel any existing Draft/Submitted revision for the given predecessor budget.
 * Must be called while the page is on a Frappe page with frappe.call available.
 */
async function cancelExistingRevision(page: Page, predecessorName: string): Promise<void> {
	await page.evaluate(async (predName: string) => {
		const f = (window as unknown as { frappe: { call: Function } }).frappe;

		const existing = await new Promise<{ name: string; status: string } | null>((resolve) => {
			f.call({
				method: 'frappe.client.get_list',
				args: {
					doctype: 'Budget',
					filters: [['supersedes_budget', '=', predName], ['status', 'in', ['Draft', 'Submitted']]],
					fields: ['name', 'status'],
					limit: 1,
				},
				callback: (r: { message?: Array<{ name: string; status: string }> }) =>
					resolve(r?.message?.[0] ?? null),
			});
		});
		if (!existing) return;

		// If Submitted, return to Draft first
		if (existing.status === 'Submitted') {
			await new Promise<void>((resolve) => {
				f.call({
					method: 'kentender_budget.api.revision.return_revision',
					args: { budget_name: existing.name, reason: 'Playwright cleanup' },
					callback: () => resolve(),
					error:    () => resolve(),
				});
			});
		}

		// Cancel the Draft
		await new Promise<void>((resolve) => {
			f.call({
				method: 'kentender_budget.api.revision.cancel_revision',
				args: { budget_name: existing.name },
				callback: () => resolve(),
				error:    () => resolve(),
			});
		});
	}, predecessorName);
}

/**
 * Call request_revision for the given Active budget and return the new revision name.
 */
async function createRevision(page: Page, activeBudgetName: string): Promise<string> {
	const result = await page.evaluate(async (budgetName: string) => {
		const f = (window as unknown as { frappe: { call: Function } }).frappe;
		return new Promise<{ name: string | null; err: string | null }>((resolve) => {
			f.call({
				method: 'kentender_budget.api.revision.request_revision',
				args: { budget_name: budgetName },
				callback: (r: { message?: { name: string } }) =>
					resolve({ name: r?.message?.name ?? null, err: null }),
				error: (r: unknown) =>
					resolve({ name: null, err: JSON.stringify(r) }),
			});
		});
	}, activeBudgetName);
	if (!result.name)
		throw new Error(
			`Could not create revision for budget: ${activeBudgetName}. Error: ${result.err ?? 'unknown'}`,
		);
	return result.name;
}

// ── Shared fixture ─────────────────────────────────────────────────────────────

let sharedActiveBudget = '';
let sharedRevision     = '';

async function setupSharedFixture(browser: Browser): Promise<void> {
	const page = await browser.newPage();
	try {
		await loginAsAdministrator(page);
		sharedActiveBudget = await findOriginalActiveBudget(page);
		await cancelExistingRevision(page, sharedActiveBudget);
		sharedRevision     = await createRevision(page, sharedActiveBudget);
	} finally {
		await page.close();
	}
}

// ── Tests ─────────────────────────────────────────────────────────────────────

test.describe.serial('Budget Revision Workflow smoke (r6-smoke)', () => {

	test.beforeAll(async ({ browser }) => {
		await setupSharedFixture(browser);
	});

	// ── 1. Revise Budget button visible on Active workbench ────────────────────

	test('Revise Budget button is visible on an Active budget workbench', async ({ page }) => {
		await loginAsAdministrator(page);
		await openWorkbench(page, sharedActiveBudget);

		await expect(page.getByTestId('kt-wbench-btn-revise')).toBeVisible({ timeout: 10_000 });
	});

	// ── 2. Revision banner is shown on the revision workbench ─────────────────

	test('Revision workbench shows revision banner', async ({ page }) => {
		await loginAsAdministrator(page);
		await openWorkbench(page, sharedRevision);

		const banner = page.locator("[data-wbench='revision-banner']");
		await expect(banner).toBeVisible({ timeout: 15_000 });
		await expect(banner).toContainText('Revision of');
		await expect(banner).toContainText(sharedActiveBudget);
	});

	// ── 3. Submit Revision button visible (Draft state) ───────────────────────

	test('Revision workbench shows Submit Revision button in Draft state', async ({ page }) => {
		await loginAsAdministrator(page);
		await openWorkbench(page, sharedRevision);

		await expect(page.getByTestId('kt-wbench-btn-submit-revision')).toBeVisible({ timeout: 10_000 });
	});

	// ── 4. Submit → Approve button visible ────────────────────────────────────

	test('Submitting revision shows Approve Revision button', async ({ page }) => {
		await loginAsAdministrator(page);
		await openWorkbench(page, sharedRevision);

		await page.getByTestId('kt-wbench-btn-submit-revision').click();

		// After submit, _loadBuilderData refreshes Zone 1 → action bar rerenders
		await expect(page.getByTestId('kt-wbench-btn-approve-revision')).toBeVisible({ timeout: 15_000 });
	});

	// ── 5. Approve → revision Active ──────────────────────────────────────────

	test('Approving revision sets status chip to Active', async ({ page }) => {
		await loginAsAdministrator(page);
		await openWorkbench(page, sharedRevision);

		// Revision should be Submitted at this point (from previous test)
		await expect(page.getByTestId('kt-wbench-btn-approve-revision')).toBeVisible({ timeout: 15_000 });

		await page.getByTestId('kt-wbench-btn-approve-revision').click();

		// frappe.confirm renders a Frappe dialog, not a browser confirm dialog
		// Click the primary action button in the modal
		await page.locator('.modal-dialog .btn-primary').click({ timeout: 10_000 });

		// Status chip must update to Active
		await expect(page.getByTestId('kt-wbench-status')).toContainText('Active', {
			timeout: 15_000,
		});

		// "Revise Budget" button is back (the new Active revision can itself be revised)
		await expect(page.getByTestId('kt-wbench-btn-revise')).toBeVisible({ timeout: 10_000 });
	});
});
