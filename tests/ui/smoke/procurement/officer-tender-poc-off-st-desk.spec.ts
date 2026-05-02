/**
 * Procurement Officer Tender Configuration POC — doc 9 OFF-ST-001..009,016..018 (Desk).
 * OFF-ST-010..015: `test_officer_poc_step9_doc9_off_st_contracts.py` (API; 015 = stale after sync).
 *
 * Requires `procurement.officer@moh.test` from `seed_core_minimal` (see `.env.ui`).
 */
import { expect, test } from '@playwright/test';

import { loginAsProcurementOfficer } from '../../helpers/auth';
import {
	clickOfficerTenderConfigurationAction,
	closeVisibleHtmlModal,
	dismissFrappeMessageIfPresent,
} from '../../helpers/stdAdminConsoleDesk';
import { controlInput, controlTextScope } from '../../helpers/deskForm';

test.describe.configure({ mode: 'serial' });

test.describe('Officer POC — doc 9 OFF-ST desk bundle (001–009,016–018)', () => {
	test.setTimeout(360_000);

	test('Serial officer smoke path', async ({ page }) => {
		await loginAsProcurementOfficer(page);

		await test.step('OFF-ST-001 — entry (list + new)', async () => {
			await page.goto('/app/List/Procurement%20Tender/List', { waitUntil: 'domcontentloaded' });
			await expect(page.locator('.list-row-head, .frappe-list').first()).toBeVisible({
				timeout: 60_000,
			});
			await page
				.getByRole('button', { name: /Add\s+Procurement Tender/i })
				.first()
				.click();
			await expect(page.locator('.form-layout').first()).toBeVisible({ timeout: 60_000 });
		});

		await test.step('OFF-ST-002 — template + POC boundary', async () => {
			const initResp = page.waitForResponse(
				(r) =>
					r.url().includes('initialize_officer_tender_from_template') &&
					r.request().method() === 'POST' &&
					r.status() === 200,
				{ timeout: 120_000 },
			);
			await clickOfficerTenderConfigurationAction(page, 'Start new tender from POC STD');
			await initResp;
			await expect(page).toHaveURL(/procurement-tender\/PT-/);
			await expect(controlInput(page, 'std_template')).toHaveValue(/.+/);
			await expect(controlTextScope(page, 'html_officer_poc_boundary')).toContainText(
				/No publication|POC boundary|guided setup/i,
			);
		});

		await test.step('OFF-ST-003 — guided sections present', async () => {
			const layout = page.locator('.form-layout').first();
			await expect(layout).toContainText('30. Tender Identity');
			await expect(layout).toContainText('2. Template Reference');
			await expect(layout).toContainText('40–50. Method, Scope and Participation');
			await expect(layout).toContainText('60. Key Dates and Meetings');
			await expect(layout).toContainText('130. Configuration store (technical)');
		});

		await test.step('OFF-ST-004 — load sample + sync (no manual save; OFF-ST-015 covered in API)', async () => {
			const loadRespPromise = page.waitForResponse(
				(r) =>
					r.url().includes('load_sample_tender') &&
					r.request().method() === 'POST' &&
					r.status() === 200,
				{ timeout: 120_000 },
			);
			await clickOfficerTenderConfigurationAction(page, 'Load Sample Tender (POC)');
			const loadResp = await loadRespPromise;
			const loadBody = (await loadResp.json()) as { message?: { ok?: boolean; message?: string } };
			expect(loadBody.message?.ok, loadBody.message?.message ?? 'load_sample_tender').toBeTruthy();
			// Desk sometimes returns before the client form refresh finishes; hard reload is stable.
			await page.reload({ waitUntil: 'domcontentloaded' });
			await expect(page.locator('.form-layout').first()).toBeVisible({ timeout: 60_000 });
			await expect(controlInput(page, 'tender_title')).toHaveValue(/Construction of Ward/, {
				timeout: 120_000,
			});
			const syncResp = page.waitForResponse(
				(r) =>
					r.url().includes('sync_officer_configuration') &&
					r.request().method() === 'POST' &&
					r.status() === 200,
				{ timeout: 120_000 },
			);
			await clickOfficerTenderConfigurationAction(page, 'Sync Configuration');
			await syncResp;
		});

		await test.step('OFF-ST-005 — conditional notices panel', async () => {
			await page.waitForResponse(
				(r) =>
					r.url().includes('get_officer_conditional_state_for_tender') &&
					r.request().method() === 'POST' &&
					r.status() === 200,
				{ timeout: 60_000 },
			);
			const notices = controlTextScope(page, 'html_officer_guided_notices');
			await expect(notices.locator('.alert, .text-muted').first()).toBeAttached({
				timeout: 60_000,
			});
		});

		await test.step('OFF-ST-006 — validate (officer)', async () => {
			const valResp = page.waitForResponse(
				(r) =>
					r.url().includes('validate_officer_configuration') &&
					r.request().method() === 'POST' &&
					r.status() === 200,
				{ timeout: 120_000 },
			);
			await clickOfficerTenderConfigurationAction(page, 'Validate (officer)');
			await valResp;
			await expect(
				page.locator('.frappe-control[data-fieldname="validation_status"] .control-value').first(),
			).toHaveText('Passed', { timeout: 120_000 });
			await dismissFrappeMessageIfPresent(page);
		});

		await test.step('OFF-ST-007 — required forms (15) + checklist dialog', async () => {
			const genResp = page.waitForResponse(
				(r) =>
					r.url().includes('generate_officer_required_forms') &&
					r.request().method() === 'POST' &&
					r.status() === 200,
				{ timeout: 120_000 },
			);
			await clickOfficerTenderConfigurationAction(page, 'Generate required forms (officer)');
			await genResp;
			const dlgResp = page.waitForResponse(
				(r) =>
					r.url().includes('get_officer_required_forms_checklist') &&
					r.request().method() === 'POST' &&
					r.status() === 200,
				{ timeout: 120_000 },
			);
			await clickOfficerTenderConfigurationAction(page, 'View required forms checklist');
			await dlgResp;
			const modal = page.locator('.modal-dialog:visible').first();
			await expect(modal).toBeVisible({ timeout: 60_000 });
			const rows = modal.locator('tbody tr');
			await expect(rows).toHaveCount(15, { timeout: 30_000 });
			await closeVisibleHtmlModal(page);
		});

		await test.step('OFF-ST-008 — representative BoQ (9 rows)', async () => {
			const boqResp = page.waitForResponse(
				(r) =>
					r.url().includes('generate_officer_representative_boq') &&
					r.request().method() === 'POST' &&
					r.status() === 200,
				{ timeout: 120_000 },
			);
			await clickOfficerTenderConfigurationAction(page, 'Generate representative BoQ');
			await boqResp;
			const stResp = page.waitForResponse(
				(r) =>
					r.url().includes('get_officer_boq_status') &&
					r.request().method() === 'POST' &&
					r.status() === 200,
				{ timeout: 120_000 },
			);
			await clickOfficerTenderConfigurationAction(page, 'BoQ status');
			await stResp;
			const modal = page.locator('.modal-dialog:visible').first();
			await expect(modal).toContainText('"boq_row_count": 9', { timeout: 30_000 });
			await closeVisibleHtmlModal(page);
		});

		await test.step('OFF-ST-009 — preview + audit (officer)', async () => {
			const prevResp = page.waitForResponse(
				(r) =>
					r.url().includes('generate_officer_preview') &&
					r.request().method() === 'POST' &&
					r.status() === 200,
				{ timeout: 120_000 },
			);
			await clickOfficerTenderConfigurationAction(page, 'Generate preview (officer)');
			await prevResp;
			const audResp = page.waitForResponse(
				(r) =>
					r.url().includes('get_officer_preview_audit_summary') &&
					r.request().method() === 'POST' &&
					r.status() === 200,
				{ timeout: 120_000 },
			);
			await clickOfficerTenderConfigurationAction(page, 'Preview and audit summary (officer)');
			await audResp;
			const modal = page.locator('.modal-dialog:visible').first();
			await expect(modal).toContainText(/POC|preview|audit/i, { timeout: 60_000 });
			await closeVisibleHtmlModal(page);
		});

		await test.step('OFF-ST-016 — re-validate, preview, ready for review', async () => {
			const valResp = page.waitForResponse(
				(r) =>
					r.url().includes('validate_officer_configuration') &&
					r.request().method() === 'POST' &&
					r.status() === 200,
				{ timeout: 120_000 },
			);
			await clickOfficerTenderConfigurationAction(page, 'Validate (officer)');
			await valResp;
			await dismissFrappeMessageIfPresent(page);
			const genPrev = page.waitForResponse(
				(r) =>
					r.url().includes('generate_officer_preview') &&
					r.request().method() === 'POST' &&
					r.status() === 200,
				{ timeout: 120_000 },
			);
			await clickOfficerTenderConfigurationAction(page, 'Generate preview (officer)');
			await genPrev;
			const markResp = page.waitForResponse(
				(r) =>
					r.url().includes('mark_officer_tender_ready_for_review') &&
					r.request().method() === 'POST' &&
					r.status() === 200,
				{ timeout: 120_000 },
			);
			await clickOfficerTenderConfigurationAction(page, 'Mark ready for review');
			await markResp;
			await expect(
				page.locator('.frappe-control[data-fieldname="tender_status"] select'),
			).toHaveValue('POC Demonstrated', { timeout: 60_000 });
		});

		await test.step('OFF-ST-017 — STD POC group absent for officer', async () => {
			const stdPoc = page.locator(
				`.inner-group-button[data-label="${encodeURIComponent('STD POC')}"]`,
			);
			await expect(stdPoc).toHaveCount(0);
		});

		await test.step('OFF-ST-018 — no out-of-scope lifecycle buttons', async () => {
			await expect(page.getByRole('button', { name: /Publish Tender/i })).toHaveCount(0);
			await expect(page.getByRole('button', { name: /Invite Bidders/i })).toHaveCount(0);
			await expect(page.getByRole('button', { name: /Start Evaluation/i })).toHaveCount(0);
		});
	});
});
