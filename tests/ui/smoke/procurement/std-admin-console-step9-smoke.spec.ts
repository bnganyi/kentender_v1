/**
 * Admin Console Step 9 — serial smoke path (spec §9, AC-ST-001–015).
 * One journey; keep order stable for Desk reload timing.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { childTableDataRows } from '../../helpers/deskForm';
import {
	STD_ADMIN_TEMPLATE_CODE,
	clickStdAdminAction,
	clickStdDemoAction,
	clickStdPocAction,
	closeVisibleHtmlModal,
	dismissFrappeMessageIfPresent,
	expectStdAdminGroupVisible,
	hideFrappeCurDialog,
	submitFrappePromptSelect,
	submitFrappePromptString,
} from '../../helpers/stdAdminConsoleDesk';

test.describe.configure({ mode: 'serial' });

test.describe('STD Administration Console — Step 9 smoke (Desk)', () => {
	test.setTimeout(300_000);

	test('§9 smoke: template through primary demo path, inspectors, blocked variant', async ({ page }) => {
		await loginAsAdministrator(page);

		// --- STD Template: viewer + validation + traces (AC-ST-001..007) ---
		const summaryResp = page.waitForResponse(
			(resp) =>
				resp.url().includes('get_template_package_summary') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);
		await page.goto(`/app/std-template/${encodeURIComponent(STD_ADMIN_TEMPLATE_CODE)}`, {
			waitUntil: 'domcontentloaded',
		});
		await summaryResp;

		await expect(page).toHaveURL(new RegExp(encodeURIComponent(STD_ADMIN_TEMPLATE_CODE)));
		await expectStdAdminGroupVisible(page);

		const viewer = page.locator('.std-admin-pkg-viewer');
		await expect(viewer).toBeVisible({ timeout: 120_000 });
		await expect(viewer.getByText('POC Administration View')).toBeVisible();
		await expect(viewer.getByRole('heading', { name: 'Package structure (counts)' })).toBeVisible();
		await expect(viewer.getByText('Raw JSON (read-only technical fallback)')).toBeVisible();

		// AC-ST-014: package JSON field is not a free-edit textarea on the form.
		const pkgJsonControl = page.locator('.frappe-control[data-fieldname="package_json"]').first();
		await expect(pkgJsonControl.locator('textarea')).toHaveCount(0);

		const validateResp = page.waitForResponse(
			(resp) =>
				resp.url().includes('validate_std_package') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);
		await clickStdAdminAction(page, 'Validate Package');
		await validateResp;
		const valDlg = page.locator('.modal-dialog:visible').first();
		await expect(valDlg.locator('.std-admin-validation-report')).toBeVisible({ timeout: 120_000 });
		await expect(valDlg.getByText(/Overall status:\s*(PASSED|PASSED_WITH_WARNINGS)/)).toBeVisible();
		await closeVisibleHtmlModal(page);

		const tracePrimaryResp = page.waitForResponse(
			(resp) =>
				resp.url().includes('trace_std_rules_for_sample') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);
		await clickStdAdminAction(page, 'Trace Primary Sample Rules');
		await tracePrimaryResp;
		const tracePrimaryDlg = page.locator('.modal-dialog:visible').first();
		await expect(tracePrimaryDlg.getByText(/Trace source:\s*PRIMARY_SAMPLE/)).toBeVisible();
		await expect(tracePrimaryDlg.locator('.std-admin-rule-trace-report')).toBeVisible();
		await expect(tracePrimaryDlg).toContainText('FORM_TENDER_SECURITY');
		await closeVisibleHtmlModal(page);

		const variantCases: { code: string; expectSubstr: RegExp }[] = [
			{ code: 'VARIANT-TENDER-SECURING-DECLARATION', expectSubstr: /FORM_TENDER_SECURING_DECLARATION/i },
			{ code: 'VARIANT-INTERNATIONAL', expectSubstr: /FORM_FOREIGN_TENDERER_LOCAL_INPUT/i },
			{ code: 'VARIANT-MISSING-SITE-VISIT-DATE', expectSubstr: /MISSING|BLOCKER|blocker|ERROR|validation/i },
			{ code: 'VARIANT-MISSING-ALTERNATIVE-SCOPE', expectSubstr: /MISSING|BLOCKER|blocker|ERROR|validation/i },
		];
		for (const { code, expectSubstr } of variantCases) {
			await clickStdAdminAction(page, 'Trace Variant Rules');
			const traceVarResp = page.waitForResponse(
				(resp) =>
					resp.url().includes('trace_std_rules_for_sample') &&
					resp.request().method() === 'POST' &&
					resp.status() === 200,
				{ timeout: 120_000 },
			);
			await submitFrappePromptString(page, code);
			await traceVarResp;
			const vDlg = page.locator('.modal-dialog:visible').first();
			await expect(vDlg.locator('.std-admin-rule-trace-report')).toBeVisible({ timeout: 120_000 });
			await expect(vDlg).toContainText(expectSubstr);
			await closeVisibleHtmlModal(page);
		}

		// --- Demo tender + primary path (AC-ST-008..012) ---
		const createResp = page.waitForResponse(
			(resp) =>
				resp.url().includes('create_or_open_std_demo_tender') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);
		await clickStdAdminAction(page, 'Create/Open Demo Tender');
		await createResp;
		await expect(page).toHaveURL(/procurement-tender\//, { timeout: 120_000 });
		await expect(page.locator('.std-demo-workspace-banner')).toContainText('POC Demo Workspace', {
			timeout: 120_000,
		});

		const rLoad = page.waitForResponse(
			(resp) =>
				resp.url().includes('load_sample_tender') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);
		await clickStdPocAction(page, 'Load Sample Tender');
		await rLoad;
		await dismissFrappeMessageIfPresent(page);
		await page.waitForTimeout(1_000);

		const rBoq = page.waitForResponse(
			(resp) =>
				resp.url().includes('generate_sample_boq') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);
		await clickStdPocAction(page, 'Generate Sample BoQ');
		await rBoq;
		await dismissFrappeMessageIfPresent(page);
		await page.waitForTimeout(1_000);

		const rVal = page.waitForResponse(
			(resp) =>
				resp.url().includes('validate_tender_configuration') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);
		await clickStdPocAction(page, 'Validate Configuration');
		await rVal;
		await dismissFrappeMessageIfPresent(page);
		await page.waitForTimeout(1_000);

		const rForms = page.waitForResponse(
			(resp) =>
				resp.url().includes('generate_required_forms') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);
		await clickStdPocAction(page, 'Generate Required Forms');
		await rForms;
		await dismissFrappeMessageIfPresent(page);
		await page.waitForTimeout(1_000);

		const rPreview = page.waitForResponse(
			(resp) =>
				resp.url().includes('generate_tender_pack_preview') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);
		await clickStdPocAction(page, 'Generate Tender Pack Preview');
		await rPreview;
		await dismissFrappeMessageIfPresent(page);
		await page.waitForTimeout(1_000);

		await expect(page.locator('.std-admin-demo-workspace')).toContainText(/Passed|Validation status/i, {
			timeout: 120_000,
		});
		await expect(childTableDataRows(page, 'required_forms')).toHaveCount(15, { timeout: 120_000 });
		await expect(childTableDataRows(page, 'boq_items')).toHaveCount(9, { timeout: 120_000 });

		await clickStdDemoAction(page, 'Required forms inspector');
		const formsDlg = page.locator('.modal-dialog:visible').first();
		await expect(formsDlg.locator('.std-admin-forms-inspector')).toBeVisible({ timeout: 120_000 });
		await expect(formsDlg).toContainText('15');
		await closeVisibleHtmlModal(page);

		await clickStdDemoAction(page, 'BoQ inspector');
		const boqDlg = page.locator('.modal-dialog:visible').first();
		await expect(boqDlg.locator('.std-admin-boq-inspector')).toBeVisible({ timeout: 120_000 });
		await expect(boqDlg).toContainText('9');
		await closeVisibleHtmlModal(page);

		await clickStdDemoAction(page, 'Preview and audit viewer');
		const prevDlg = page.locator('.modal-dialog:visible').first();
		await expect(prevDlg.locator('.std-admin-preview-audit-viewer')).toBeVisible({ timeout: 120_000 });
		await expect(prevDlg).toContainText(/Generated|Preview status/i);
		const iframeAudit = prevDlg.locator('iframe.std-preview-audit-iframe');
		await expect(iframeAudit).toBeVisible();
		await expect(iframeAudit).toHaveAttribute('sandbox', '');
		await closeVisibleHtmlModal(page);

		// --- Blocked variant tender (AC-ST-013) ---
		const summary2 = page.waitForResponse(
			(resp) =>
				resp.url().includes('get_template_package_summary') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);
		await page.goto(`/app/std-template/${encodeURIComponent(STD_ADMIN_TEMPLATE_CODE)}`, {
			waitUntil: 'domcontentloaded',
		});
		await summary2;
		await expectStdAdminGroupVisible(page);

		await clickStdAdminAction(page, 'Create Demo Tender (variant)');
		const createVarResp = page.waitForResponse(
			(resp) =>
				resp.url().includes('create_or_open_std_demo_tender') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);
		await submitFrappePromptSelect(
			page,
			'variant_code',
			'VARIANT-MISSING-SITE-VISIT-DATE',
			'Create',
		);
		await createVarResp;
		await expect(page).toHaveURL(/procurement-tender\//, { timeout: 120_000 });
		await expect(page.locator('.modal.fade.show')).toHaveCount(0, { timeout: 60_000 });

		const rValNeg = page.waitForResponse(
			(resp) =>
				resp.url().includes('validate_tender_configuration') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);
		await clickStdPocAction(page, 'Validate Configuration');
		await rValNeg;
		await dismissFrappeMessageIfPresent(page);
		await hideFrappeCurDialog(page);
		// Hard refresh clears msgprint modals that still block the STD POC dropdown.
		await page.reload({ waitUntil: 'domcontentloaded' });
		await expect(page.locator('.std-demo-workspace-banner')).toBeVisible({ timeout: 120_000 });

		const rPreviewNeg = page.waitForResponse(
			(resp) =>
				resp.url().includes('generate_tender_pack_preview') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);
		await clickStdPocAction(page, 'Generate Tender Pack Preview');
		await rPreviewNeg;

		await expect(
			page.getByText(/Tender-pack preview was not generated|validation blocks generation/i),
		).toBeVisible({ timeout: 60_000 });
		await hideFrappeCurDialog(page);
		await page.reload({ waitUntil: 'domcontentloaded' });
		await expect(page.locator('.std-demo-workspace-banner')).toBeVisible({ timeout: 120_000 });

		await clickStdDemoAction(page, 'Preview and audit viewer');
		const blockedDlg = page.locator('.modal-dialog:visible').first();
		await expect(blockedDlg).toContainText(/Blocked|Not Generated/i, { timeout: 120_000 });
		await closeVisibleHtmlModal(page);
	});
});
