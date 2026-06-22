/**
 * P5A-007 — No implementation-stage copy on Planning surfaces.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const PKG = 'PKG-MOH-2026-001';

const CANONICAL_ROUTES = [
	'/desk/procurement-planning',
	'/desk/procurement-planning/approved-demands',
	'/desk/procurement-planning/plans',
	'/desk/procurement-planning/packages',
	'/desk/procurement-planning/releases',
	`/desk/procurement-planning/packages?package_code=${PKG}`,
] as const;

const FORBIDDEN_IMPLEMENTATION_COPY = [
	/shell baseline/i,
	/feature content (is )?intentionally deferred/i,
	/shell-only baseline active/i,
	/9\.1 shell baseline/i,
	/\bstub content\b/i,
	/P5 surfaces completed/i,
	/this will be implemented later/i,
	/technical placeholder/i,
	/Choose a planning workspace action/i,
	/Open a planning queue from the sidebar/i,
	/Canonical PP2 rendering is active/i,
];

const SURFACE_EMPTY_MESSAGES: Record<string, RegExp> = {
	'/desk/procurement-planning/approved-demands': /No approved demands match this queue/i,
	'/desk/procurement-planning/plans': /No procurement plans match this queue/i,
	'/desk/procurement-planning/packages': /No packages match this queue/i,
	'/desk/procurement-planning/releases': /No released packages match this queue/i,
};

async function assertNoForbiddenCopy(page: import('@playwright/test').Page) {
	const bodyText = await page.locator('body').innerText();
	for (const pattern of FORBIDDEN_IMPLEMENTATION_COPY) {
		expect(bodyText).not.toMatch(pattern);
	}
}

test.describe('P5A-007 Planning implementation copy scan', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('canonical routes contain no forbidden implementation copy', async ({ page }) => {
		for (const path of CANONICAL_ROUTES) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible({ timeout: 30000 });
			await assertNoForbiddenCopy(page);
		}
	});

	test('workbench surfaces show business empty state with purpose copy', async ({ page }) => {
		const surfacePurpose: Record<string, RegExp> = {
			'/desk/procurement-planning': /Convert approved demand into tender-ready procurement packages/i,
			'/desk/procurement-planning/approved-demands': /Which approved demands can be planned now/i,
			'/desk/procurement-planning/plans': /Which plan owns this procurement work/i,
			'/desk/procurement-planning/packages': /Which packages need work, review, release, or follow-up/i,
			'/desk/procurement-planning/releases': /Which packages have left Planning, and where did they go/i,
		};
		for (const [path, purposePattern] of Object.entries(surfacePurpose)) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-page-purpose')).toHaveText(purposePattern, { timeout: 30000 });
		}
		for (const [path, messagePattern] of Object.entries(SURFACE_EMPTY_MESSAGES)) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			const emptyState = page.getByTestId('pp2-surface-empty-state');
			await expect(emptyState).toBeVisible({ timeout: 30000 });
			await expect(emptyState).toContainText(messagePattern);
		}
	});

	test('Planning Home shows purpose without workbench empty state', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-page-purpose')).toHaveText(
			/Convert approved demand into tender-ready procurement packages/i,
			{ timeout: 30000 }
		);
		await expect(page.getByTestId('pp2-planning-home-surface')).toBeVisible();
		await expect(page.getByTestId('pp2-surface-empty-state')).toHaveCount(0);
	});

	test('right panel is idle without stub next-action copy on packages', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toHaveAttribute(
			'data-right-panel-collapsed',
			'1'
		);
		const nextAction = page.getByTestId('pp2-primary-next-action-panel');
		await expect(nextAction).toHaveCount(1);
		await expect(nextAction).toHaveText('');
		await expect(nextAction).not.toContainText(/Next action/i);
	});

	test('Planning Home hides permanent right panel', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toHaveAttribute(
			'data-pp2-home-layout',
			'1',
			{ timeout: 30000 }
		);
		await expect(page.getByTestId('pp2-primary-right-panel')).toBeHidden();
	});
});
