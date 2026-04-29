import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

test.describe('STD-CURSOR-1001 workbench shell', () => {
	test('std workbench route renders required shell test ids', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto('/app/std-engine');
		await page.waitForLoadState('domcontentloaded');

		await expect(page).toHaveURL(/\/(app|desk)\/std-engine/i, { timeout: 45_000 });
		await expect(page.getByTestId('std-workbench-page')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('std-page-title')).toContainText('STD Engine');
		await expect(page.getByTestId('std-kpi-strip')).toBeVisible();
		await expect(page.getByTestId('std-scope-tabs')).toBeVisible();
		await expect(page.getByTestId('std-queue-bar')).toBeVisible();
		await expect(page.getByTestId('std-search-input')).toBeVisible();
		await expect(page.getByTestId('std-filter-panel')).toBeVisible();
		await expect(page.getByTestId('std-object-list')).toBeVisible();
		await expect(page.getByTestId('std-object-detail')).toBeVisible();
		await expect(page.getByTestId('std-action-bar')).toBeVisible();
		await expect(page.getByTestId('std-blockers-panel')).toBeVisible();

		// Acceptance: this is a custom workbench shell, not raw DocType list.
		await expect(page.locator('.list-row-container')).toHaveCount(0);
		await expect(page.getByRole('button', { name: /^Upload STD$/i })).toHaveCount(0);
	});

	test('std workbench keeps procurement sidebar after hard refresh', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto('/desk/std-engine');
		await page.waitForLoadState('domcontentloaded');
		await expect(page).toHaveURL(/\/(app|desk)\/std-engine/i, { timeout: 45_000 });
		await expect(page.getByTestId('std-workbench-page')).toBeVisible({ timeout: 45_000 });

		await page.reload({ waitUntil: 'domcontentloaded' });
		await expect(page).toHaveURL(/\/(app|desk)\/std-engine/i, { timeout: 45_000 });
		await expect(page.getByTestId('std-workbench-page')).toBeVisible({ timeout: 45_000 });

		await expect(page.getByRole('link', { name: 'Procurement Home', exact: true }).first()).toBeVisible();
		await expect(page.getByRole('link', { name: /Demand Intake/i }).first()).toBeVisible();
		await expect(page.getByRole('link', { name: 'Procurement Planning', exact: true }).first()).toBeVisible();
		await expect(page.getByRole('link', { name: 'STD Engine', exact: true }).first()).toBeVisible();
		await expect(page.getByRole('link', { name: 'Supplier Management', exact: true }).first()).toBeVisible();
	});

	test('std kpi strip renders interactive risk cards', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto('/app/std-engine');
		await page.waitForLoadState('domcontentloaded');

		const draft = page.getByTestId('std-kpi-draft-versions');
		const blocked = page.getByTestId('std-kpi-validation-blocked');
		const legal = page.getByTestId('std-kpi-legal-review-pending');
		const policy = page.getByTestId('std-kpi-policy-review-pending');
		const active = page.getByTestId('std-kpi-active-versions');
		const instancesBlocked = page.getByTestId('std-kpi-instances-blocked');
		const failures = page.getByTestId('std-kpi-generation-failures');
		const addendum = page.getByTestId('std-kpi-addendum-impact-pending');

		await expect(draft).toBeVisible({ timeout: 45_000 });
		await expect(blocked).toBeVisible();
		await expect(legal).toBeVisible();
		await expect(policy).toBeVisible();
		await expect(active).toBeVisible();
		await expect(instancesBlocked).toBeVisible();
		await expect(failures).toBeVisible();
		await expect(addendum).toBeVisible();

		await expect(blocked).toHaveClass(/kt-std-kpi-card--high-risk/);
		await expect(failures).toHaveClass(/kt-std-kpi-card--high-risk/);
		await expect(addendum).toHaveClass(/kt-std-kpi-card--high-risk/);

		await failures.click();
		await expect(failures).toHaveClass(/is-active/);
		await expect(page.getByTestId('std-active-queue-state')).toContainText('generation_failed');
	});

	test('std scope tabs and queue bar are complete and interactive', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto('/app/std-engine');
		await page.waitForLoadState('domcontentloaded');

		await expect(page.getByTestId('std-scope-my-work')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('std-scope-templates')).toBeVisible();
		await expect(page.getByTestId('std-scope-active-versions')).toBeVisible();
		await expect(page.getByTestId('std-scope-std-instances')).toBeVisible();
		await expect(page.getByTestId('std-scope-generation-jobs')).toBeVisible();
		await expect(page.getByTestId('std-scope-addendum-impacts')).toBeVisible();
		await expect(page.getByTestId('std-scope-audit-view')).toBeVisible();

		await page.getByTestId('std-scope-generation-jobs').click();
		await expect(page.getByTestId('std-scope-generation-jobs')).toHaveClass(/is-active|btn-primary/);
		await expect(page.getByTestId('std-queue-generation-failed')).toBeVisible();
		await page.getByTestId('std-queue-generation-failed').click();
		await expect(page.getByTestId('std-active-queue-state')).toContainText('generation_failed');

		await page.getByTestId('std-kpi-policy-review-pending').click();
		await expect(page.getByTestId('std-scope-templates')).toHaveClass(/is-active|btn-primary/);
		await expect(page.getByTestId('std-queue-policy-review')).toHaveClass(/is-active|btn-primary/);
		await expect(page.getByTestId('std-active-queue-state')).toContainText('policy_review');
	});

	test('std search and filters show chips and combine with queue state', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto('/app/std-engine');
		await page.waitForLoadState('domcontentloaded');

		await page.getByTestId('std-scope-templates').click();
		await page.getByTestId('std-queue-policy-review').click();
		await expect(page.getByTestId('std-active-queue-state')).toContainText('policy_review');

		await page.getByTestId('std-filter-toggle').click();
		await page.locator('[data-std-filter="object_type"]').selectOption('Template Version');
		await page.locator('[data-std-filter="assigned_to_me"]').check();
		await expect(page.getByTestId('std-filter-chip-object-type')).toBeVisible();
		await expect(page.getByTestId('std-filter-chip-assigned-to-me')).toBeVisible();

		await page.getByTestId('std-search-input').fill('STD');
		await expect(page.getByTestId('std-object-list')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('std-active-queue-state')).toContainText('policy_review');
	});

	test('std object list shows business rows and click loads detail panel', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto('/app/std-engine');
		await page.waitForLoadState('domcontentloaded');

		await page.getByTestId('std-scope-active-versions').click();
		await page.getByTestId('std-queue-active').click();
		await page.getByTestId('std-search-input').fill('STD');
		const rows = page.locator('[data-testid^="std-row-"]');
		const count = await rows.count();
		if (count === 0) {
			await expect(page.getByTestId('std-search-results-empty')).toBeVisible({ timeout: 45_000 });
			return;
		}
		const row = rows.first();
		await expect(row).toBeVisible({ timeout: 45_000 });
		await row.click();
		await expect(page.getByTestId('std-selected-object-code')).toBeVisible();
		await expect(page.getByTestId('std-object-detail')).toContainText(/Template|Instance|Output|Generation|Addendum|Readiness/i);
	});

	test('std detail panel and action bar load from server availability (1006)', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto('/app/std-engine');
		await page.waitForLoadState('domcontentloaded');

		await page.getByTestId('std-scope-active-versions').click();
		await page.getByTestId('std-queue-active').click();
		await page.getByTestId('std-search-input').fill('STD');
		const rows = page.locator('[data-testid^="std-row-"]');
		const count = await rows.count();
		if (count === 0) {
			await expect(page.getByTestId('std-search-results-empty')).toBeVisible({ timeout: 45_000 });
			return;
		}
		await rows.first().click();
		await expect(page.getByTestId('std-detail-header')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('std-detail-selected-title')).toBeVisible();
		await expect(page.getByTestId('std-detail-state-cards')).toBeVisible();
		await expect(page.getByTestId('std-detail-tab-overview').or(page.getByTestId('std-tab-template-overview'))).toBeVisible();
		await expect(
			page.getByTestId('std-detail-tab-placeholder').or(page.getByTestId('std-template-summary-loading')).or(page.getByTestId('std-overview-object-type')),
		).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('std-action-host')).toBeVisible();
		const openBtn = page.getByTestId('std-action-open-in-desk');
		await expect(openBtn).toBeVisible({ timeout: 45_000 });
		const disabled = await openBtn.isDisabled();
		if (disabled) {
			const t = await openBtn.getAttribute('title');
			expect(t && t.length > 3).toBeTruthy();
		} else {
			await expect(openBtn).toBeEnabled();
		}
	});

	test('std object list preserves scroll context on deep row selection', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto('/app/std-engine');
		await page.waitForLoadState('domcontentloaded');
		await expect(page.getByTestId('std-object-list')).toBeVisible({ timeout: 45_000 });
		await page.getByTestId('std-scope-active-versions').click();
		await page.getByTestId('std-queue-active').click();
		await page.getByTestId('std-search-input').fill('STD');

		const rows = page.locator('[data-testid^="std-row-"]');
		const count = await rows.count();
		test.skip(count < 6, 'Not enough rows to validate deep scroll selection.');
		const list = page.locator('.kt-std-results-list');
		await expect(list).toBeVisible({ timeout: 45_000 });

		const metrics = await list.evaluate((el) => ({
			scrollHeight: el.scrollHeight,
			clientHeight: el.clientHeight,
		}));
		test.skip(metrics.scrollHeight <= metrics.clientHeight, 'List is not scrollable in this dataset.');

		const before = await list.evaluate((el) => {
			el.scrollTop = Math.max(0, el.scrollHeight - el.clientHeight - 32);
			return el.scrollTop;
		});
		const targetIndex = Math.max(0, count - 2);
		const target = rows.nth(targetIndex);
		await target.click();
		await expect(target).toHaveClass(/is-active/);

		const after = await list.evaluate((el) => el.scrollTop);
		expect(after).toBeGreaterThan(0);
		expect(Math.abs(after - before)).toBeLessThan(140);
	});

	test('STD-CURSOR-1007: template version row shows ten template tabs and overview badges when active', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto('/app/std-engine');
		await page.waitForLoadState('domcontentloaded');

		await page.getByTestId('std-scope-active-versions').click();
		await page.getByTestId('std-queue-active').click();
		await page.getByTestId('std-search-input').fill('');
		await expect
			.poll(
				async () =>
					(await page.locator('[data-testid^="std-row-"]').count()) +
					((await page.getByTestId('std-search-results-empty').count()) > 0 ? 1 : 0),
				{ timeout: 45_000 },
			)
			.toBeGreaterThan(0);
		const rows = page.locator('[data-testid^="std-row-"]');
		const rowCount = await rows.count();
		if (rowCount === 0) {
			await expect(page.getByTestId('std-search-results-empty')).toBeVisible({ timeout: 45_000 });
		}
		test.skip(rowCount === 0, 'No STD workbench rows for active versions queue on this site.');
		const tvRow = rows.first();
		await expect(tvRow).toBeVisible({ timeout: 45_000 });
		await expect(tvRow).toHaveAttribute('data-std-object-type', 'Template Version');
		await tvRow.click();

		const tabIds = [
			'std-tab-template-overview',
			'std-tab-template-structure',
			'std-tab-template-parameters',
			'std-tab-template-forms',
			'std-tab-works-configuration',
			'std-tab-mappings',
			'std-tab-readiness-rules',
			'std-tab-reviews-approval',
			'std-tab-usage',
			'std-tab-template-audit-evidence',
		];
		for (const id of tabIds) {
			await expect(page.getByTestId(id)).toBeVisible({ timeout: 45_000 });
		}

		await expect(page.getByTestId('std-overview-object-type')).toContainText('Template Version', { timeout: 45_000 });
		const readOnly = page.getByTestId('std-template-read-only');
		const status = page.getByTestId('std-template-version-status');
		if (await status.isVisible()) {
			const st = (await status.textContent())?.trim() ?? '';
			if (st === 'Active') {
				await expect(readOnly).toBeVisible();
			}
		}
		await page.getByTestId('std-tab-template-structure').click();
		await expect(page.getByTestId('std-template-panel-structure')).toBeVisible();
		await expect(page.getByTestId('std-structure-tree')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('std-structure-node-section').first()).toBeVisible({ timeout: 45_000 });
		await page.getByTestId('std-structure-node-section').first().click();
		await expect(page.getByTestId('std-structure-detail-editability')).toBeVisible();
		const lockedWarn = page.getByTestId('std-structure-locked-section-warning');
		if ((await lockedWarn.count()) > 0) {
			await expect(lockedWarn).toContainText(/locked standard text/i);
		}

		await page.getByTestId('std-tab-template-parameters').click();
		await expect(page.getByTestId('std-template-panel-parameters')).toBeVisible({ timeout: 45_000 });
		await expect
			.poll(
				async () =>
					(await page.locator('[data-testid^="std-param-group-"]').count()) +
					((await page.getByTestId('std-parameters-catalogue-empty').count()) > 0 ? 1 : 0) +
					((await page.getByTestId('std-parameters-catalogue-error').count()) > 0 ? 1 : 0),
				{ timeout: 45_000 },
			)
			.toBeGreaterThan(0);
		const paramsError = page.getByTestId('std-parameters-catalogue-error');
		if ((await paramsError.count()) > 0) {
			await expect(paramsError).toBeVisible();
		}
		if ((await page.locator('[data-testid^="std-param-group-"]').count()) > 0) {
			await expect(page.locator('[data-testid^="std-param-group-"]').first()).toBeVisible({ timeout: 45_000 });
		}
		const paramsReadOnly = page.getByTestId('std-parameters-read-only');
		if ((await paramsReadOnly.count()) > 0) {
			await expect(paramsReadOnly).toBeVisible();
		}

		await page.evaluate(() => {
			const btn = document.querySelector('[data-testid="std-tab-template-forms"]') as HTMLElement | null;
			btn?.click();
		});
		await expect(page.getByTestId('std-template-panel-forms')).toBeVisible({ timeout: 45_000 });
		await expect
			.poll(
				async () =>
					(await page.getByTestId('std-forms-table').count()) +
					((await page.getByTestId('std-forms-catalogue-empty').count()) > 0 ? 1 : 0) +
					((await page.getByTestId('std-forms-catalogue-error').count()) > 0 ? 1 : 0),
				{ timeout: 45_000 },
			)
			.toBeGreaterThan(0);
		const formsError = page.getByTestId('std-forms-catalogue-error');
		if ((await formsError.count()) > 0) {
			await expect(formsError).toBeVisible();
			return;
		}
		const formsEmpty = page.getByTestId('std-forms-catalogue-empty');
		if (await formsEmpty.isVisible().catch(() => false)) {
			return;
		}
		await expect(page.getByTestId('std-forms-category-sidebar')).toBeVisible();
		await expect(page.getByTestId('std-forms-table')).toBeVisible();
		await expect(page.getByTestId('std-forms-detail-drawer')).toBeVisible();
		await expect(page.getByTestId('std-forms-model-preview-readonly')).toBeVisible();
		const sectionIv = page.getByTestId('std-forms-category-section-iv-forms');
		if ((await sectionIv.count()) > 0) {
			await expect(sectionIv).toBeVisible();
		}
		const contractForms = page.getByTestId('std-forms-category-contract-forms');
		if ((await contractForms.count()) > 0) {
			await expect(contractForms).toBeVisible();
		}
		const dsmImpact = page.getByTestId('std-forms-required-supplier-dsm-impact');
		if ((await dsmImpact.count()) > 0) {
			await expect(dsmImpact).toContainText(/drives dsm/i);
		}

		await page.evaluate(() => {
			const btn = document.querySelector('[data-testid="std-tab-works-configuration"]') as HTMLElement | null;
			btn?.click();
		});
		await expect(page.getByTestId('std-template-panel-works-configuration')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('std-works-profile-selector')).toBeVisible();
		await expect(page.getByTestId('std-works-profile-details')).toBeVisible();
		await expect(page.getByTestId('std-works-boq-definition')).toBeVisible();
		await expect(page.getByTestId('std-works-arithmetic-correction-stage')).toContainText(/Evaluation/i);
		await expect(page.getByTestId('std-works-boq-warning')).toContainText(/Evaluation Model/i);
		await expect(page.getByTestId('std-works-contract-price-warning')).toContainText(/Evaluation\/Award/i);
		await expect(page.getByTestId('std-works-evaluation-rule-templates')).toBeVisible();
		await expect(page.getByTestId('std-works-contract-carry-forward-templates')).toBeVisible();
		await expect(page.getByTestId('std-works-readiness-rules')).toBeVisible();

		await page.evaluate(() => {
			const btn = document.querySelector('[data-testid="std-tab-mappings"]') as HTMLElement | null;
			btn?.click();
		});
		await expect(page.getByTestId('std-template-panel-mappings')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('std-mappings-target-tabs')).toBeVisible();
		await expect
			.poll(
				async () =>
					(await page.getByTestId('std-mappings-table').count()) +
					((await page.getByTestId('std-mappings-tab-empty').count()) > 0 ? 1 : 0) +
					((await page.getByTestId('std-mappings-catalogue-error').count()) > 0 ? 1 : 0),
				{ timeout: 45_000 },
			)
			.toBeGreaterThan(0);
		const mapErr = page.getByTestId('std-mappings-catalogue-error');
		if ((await mapErr.count()) > 0) {
			await expect(mapErr).toBeVisible();
			return;
		}
		await expect(page.getByTestId('std-mappings-missing')).toBeVisible();
		await expect(page.getByTestId('std-mappings-highlight-iv-dsm')).toBeVisible();
		await expect(page.getByTestId('std-mappings-highlight-iii-dem')).toBeVisible();
		const mapReadOnly = page.getByTestId('std-mappings-read-only-banner');
		if ((await mapReadOnly.count()) > 0) {
			await expect(mapReadOnly).toContainText(/read-only/i);
		}
		await page.evaluate(() => {
			const btn = document.querySelector('[data-testid="std-mappings-target-dsm"]') as HTMLElement | null;
			btn?.click();
		});
		await expect(page.getByTestId('std-mappings-target-dsm')).toHaveClass(/btn-primary|is-active/);

		await page.evaluate(() => {
			const btn = document.querySelector('[data-testid="std-tab-reviews-approval"]') as HTMLElement | null;
			btn?.click();
		});
		await expect(page.getByTestId('std-template-panel-reviews-approval')).toBeVisible({ timeout: 45_000 });
		await expect
			.poll(
				async () =>
					(await page.getByTestId('std-reviews-checklist-table').count()) +
					((await page.getByTestId('std-reviews-catalogue-error').count()) > 0 ? 1 : 0),
				{ timeout: 45_000 },
			)
			.toBeGreaterThan(0);
		const revErr = page.getByTestId('std-reviews-catalogue-error');
		if ((await revErr.count()) > 0) {
			await expect(revErr).toBeVisible();
			return;
		}
		await expect(page.getByTestId('std-reviews-summary')).toBeVisible();
		await expect(page.getByTestId('std-reviews-checklist-table')).toBeVisible();
		await expect(page.getByTestId('std-reviews-activation-legal-warning')).toBeVisible();
		await expect(page.getByTestId('std-reviews-activate-version')).toBeDisabled();

		await page.evaluate(() => {
			const btn = document.querySelector('[data-testid="std-tab-template-audit-evidence"]') as HTMLElement | null;
			btn?.click();
		});
		await expect(page.getByTestId('std-template-panel-audit-evidence')).toBeVisible({ timeout: 45_000 });
		await expect
			.poll(
				async () =>
					(await page.getByTestId('std-audit-timeline-table').count()) +
					((await page.getByTestId('std-audit-timeline-empty').count()) > 0 ? 1 : 0) +
					((await page.getByTestId('std-audit-catalogue-error').count()) > 0 ? 1 : 0),
				{ timeout: 45_000 },
			)
			.toBeGreaterThan(0);
		const audErr = page.getByTestId('std-audit-catalogue-error');
		if ((await audErr.count()) > 0) {
			await expect(audErr).toBeVisible();
			return;
		}
		await expect(page.getByTestId('std-audit-timeline-section')).toBeVisible();
		await expect(page.getByTestId('std-audit-export-csv')).toBeVisible();
		await expect(page.getByTestId('std-audit-export-csv')).toBeEnabled();
	});

	test('STD-CURSOR-1101/1102: STD Instance tabs, overview shell, and parameters panel', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto('/app/std-engine');
		await page.waitForLoadState('domcontentloaded');

		await page.getByTestId('std-scope-std-instances').click();
		const instanceQueues = [
			'std-queue-draft-instances',
			'std-queue-instance-ready',
			'std-queue-published-locked',
			'std-queue-instance-blocked',
		];
		let instRow = page.locator('[data-testid^="std-row-"][data-std-object-type="STD Instance"]').first();
		for (const qid of instanceQueues) {
			const q = page.getByTestId(qid);
			if ((await q.count()) === 0) {
				continue;
			}
			await q.click();
			await page.getByTestId('std-search-input').fill('');
			await expect
				.poll(
					async () =>
						(await page.locator('[data-testid^="std-row-"]').count()) +
						((await page.getByTestId('std-search-results-empty').count()) > 0 ? 1 : 0),
					{ timeout: 45_000 },
				)
				.toBeGreaterThan(0);
			instRow = page.locator('[data-testid^="std-row-"][data-std-object-type="STD Instance"]').first();
			if ((await instRow.count()) > 0) {
				break;
			}
		}
		test.skip((await instRow.count()) === 0, 'No STD Instance rows in instances scope on this site.');
		await expect(instRow).toBeVisible({ timeout: 45_000 });
		await instRow.click();

		const tabIds = [
			'std-tab-instance-overview',
			'std-tab-instance-parameters',
			'std-tab-instance-works-requirements',
			'std-tab-instance-boq',
			'std-tab-generated-outputs',
			'std-tab-instance-readiness',
			'std-tab-addendum-impact',
			'std-tab-downstream-contracts',
			'std-tab-instance-audit-evidence',
		];
		for (const id of tabIds) {
			await expect(page.getByTestId(id)).toBeVisible({ timeout: 45_000 });
		}

		await expect(page.getByTestId('std-overview-object-type')).toContainText('STD Instance', { timeout: 45_000 });
		await expect(page.getByTestId('std-instance-status')).toBeVisible();
		await expect(page.getByTestId('std-instance-template-version-code')).toBeVisible();

		await page.getByTestId('std-tab-instance-parameters').click();
		await expect(page.getByTestId('std-instance-panel-parameters')).toBeVisible({ timeout: 45_000 });
		await expect
			.poll(
				async () =>
					(await page.locator('[data-testid^="std-param-group-"]').count()) +
					((await page.getByTestId('std-instance-parameters-loading').count()) > 0 ? 1 : 0) +
					((await page.getByTestId('std-instance-parameters-error').count()) > 0 ? 1 : 0),
				{ timeout: 45_000 },
			)
			.toBeGreaterThan(0);
		await page.getByTestId('std-tab-instance-overview').click();
		await expect(page.getByTestId('std-instance-status')).toBeVisible();
	});
});

test.describe('STD-CURSOR-1206 smoke contract UI', () => {
	test('workbench, template ITT/GCC badges, instance BOQ/previews/readiness, no Upload STD', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto('/app/std-engine');
		await page.waitForLoadState('domcontentloaded');
		await expect(page.getByTestId('std-workbench-page')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('std-page-title')).toBeVisible();
		await expect(page.getByRole('button', { name: /^Upload STD$/i })).toHaveCount(0);

		await page.getByTestId('std-scope-active-versions').click();
		await page.getByTestId('std-queue-active').click();
		await page.getByTestId('std-search-input').fill('STDTV-WORKS-BUILDING');
		await expect
			.poll(
				async () =>
					(await page.locator('[data-testid^="std-row-"]').count()) +
					((await page.getByTestId('std-search-results-empty').count()) > 0 ? 1 : 0),
				{ timeout: 45_000 },
			)
			.toBeGreaterThan(0);
		const buildingTv = page
			.locator('[data-testid^="std-row-"][data-std-object-type="Template Version"]')
			.filter({ hasText: 'STDTV-WORKS-BUILDING-REV-APR-2022' })
			.first();
		if ((await buildingTv.count()) > 0) {
			await buildingTv.click();
			await expect(page.getByTestId('std-selected-object-code')).toContainText('STDTV-WORKS-BUILDING', {
				timeout: 45_000,
			});
			await page.getByTestId('std-tab-template-structure').click();
			await expect(page.getByTestId('std-template-panel-structure')).toBeVisible({ timeout: 45_000 });
			const tree = page.getByTestId('std-structure-tree');
			await expect(tree).toBeVisible({ timeout: 45_000 });
			await expect(tree.locator('span.badge').filter({ hasText: /^ITT$/ }).first()).toBeVisible({
				timeout: 45_000,
			});
			await expect(tree.locator('span.badge').filter({ hasText: /^GCC$/ }).first()).toBeVisible({
				timeout: 45_000,
			});
		} else {
			await page.getByTestId('std-search-input').fill('');
			await expect
				.poll(
					async () =>
						(await page.locator('[data-testid^="std-row-"][data-std-object-type="Template Version"]').count()) +
						((await page.getByTestId('std-search-results-empty').count()) > 0 ? 1 : 0),
					{ timeout: 45_000 },
				)
				.toBeGreaterThan(0);
			const anyTv = page.locator('[data-testid^="std-row-"][data-std-object-type="Template Version"]').first();
			test.skip((await anyTv.count()) === 0, 'No Template Version row on this site.');
			await anyTv.click();
			await page.getByTestId('std-tab-template-structure').click();
			await expect(page.getByTestId('std-template-panel-structure')).toBeVisible({ timeout: 45_000 });
			await expect(page.getByTestId('std-structure-tree')).toBeVisible({ timeout: 45_000 });
			await expect(page.getByTestId('std-structure-node-section').first()).toBeVisible({ timeout: 45_000 });
		}

		await page.getByTestId('std-scope-std-instances').click();
		const instanceQueues = [
			'std-queue-draft-instances',
			'std-queue-instance-ready',
			'std-queue-published-locked',
			'std-queue-instance-blocked',
		];
		let instRow = page.locator('[data-testid^="std-row-"][data-std-object-type="STD Instance"]').first();
		for (const qid of instanceQueues) {
			const q = page.getByTestId(qid);
			if ((await q.count()) === 0) {
				continue;
			}
			await q.click();
			await page.getByTestId('std-search-input').fill('');
			await expect
				.poll(
					async () =>
						(await page.locator('[data-testid^="std-row-"]').count()) +
						((await page.getByTestId('std-search-results-empty').count()) > 0 ? 1 : 0),
					{ timeout: 45_000 },
				)
				.toBeGreaterThan(0);
			instRow = page.locator('[data-testid^="std-row-"][data-std-object-type="STD Instance"]').first();
			if ((await instRow.count()) > 0) {
				break;
			}
		}
		test.skip((await instRow.count()) === 0, 'No STD Instance rows in instances scope on this site.');
		await instRow.click();
		await page.getByTestId('std-tab-instance-boq').click();
		await expect(page.getByTestId('std-instance-panel-boq')).toBeVisible({ timeout: 45_000 });
		await expect
			.poll(
				async () =>
					(await page.getByTestId('std-boq-summary-bar').count()) +
					((await page.getByTestId('std-boq-validation-panel').count()) > 0 ? 1 : 0),
				{ timeout: 45_000 },
			)
			.toBeGreaterThan(0);
		if ((await page.getByTestId('std-boq-summary-bar').count()) > 0) {
			await expect(page.getByTestId('std-boq-item-grid')).toBeVisible({ timeout: 45_000 });
		}

		await page.getByTestId('std-tab-generated-outputs').click();
		await expect(page.getByTestId('std-instance-panel-generated-outputs')).toBeVisible({ timeout: 45_000 });
		await expect
			.poll(
				async () =>
					(await page.getByTestId('std-preview-dsm').count()) +
					((await page.getByTestId('std-preview-dom').count()) > 0 ? 1 : 0) +
					((await page.getByTestId('std-preview-dem').count()) > 0 ? 1 : 0) +
					((await page.getByTestId('std-preview-dcm').count()) > 0 ? 1 : 0) +
					((await page.getByTestId('std-instance-output-jobs').count()) > 0 ? 1 : 0),
				{ timeout: 45_000 },
			)
			.toBeGreaterThan(0);

		await page.getByTestId('std-tab-instance-readiness').click();
		await expect(page.getByTestId('std-instance-panel-readiness')).toBeVisible({ timeout: 45_000 });
		await expect
			.poll(
				async () =>
					(await page.getByTestId('std-instance-readiness-findings').count()) +
					((await page.getByTestId('std-instance-readiness-run').count()) > 0 ? 1 : 0) +
					((await page.getByTestId('std-instance-readiness-summary').count()) > 0 ? 1 : 0),
				{ timeout: 45_000 },
			)
			.toBeGreaterThan(0);
	});
});
