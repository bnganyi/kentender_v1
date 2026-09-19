import path from "node:path";

import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AO, HOPF, PASSWORD, collectConsoleErrors, expectReady, expectSettled, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.8 slice 7h — TPR-DES-08 Publication confirmation. */

const EVIDENCE = path.resolve(__dirname, "fixtures/evidence.png");

test.describe.configure({ mode: "serial", timeout: 300_000 });

/** Frappe's own uploader: My Device → file chooser → Upload. */
async function uploadEvidence(page: import("@playwright/test").Page, chooseSelector: string) {
	const [chooser] = await Promise.all([page.waitForEvent("filechooser"), page.locator(chooseSelector).click().then(() => page.locator(".modal.show").getByRole("button", { name: "My Device" }).click())]);
	await chooser.setFiles(EVIDENCE);
	await page.locator(".modal.show .btn-modal-primary, .modal.show button.btn-primary").click();
	await expect(page.locator(".modal.show")).toHaveCount(0);
}

test.describe("TPR-DES-08 Publication confirmation", () => {
	test.afterAll(() => restoreSite());

	test("the HoPF confirms a channel with evidence; dialog checks are inline; View confirmation", async ({ page }) => {
		const state = resetFixture("reset_publication_fixture", { confirmed: 2 });
		const errors = collectConsoleErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/publication`);
		await expectReady(page, "publication");
		await expect(page.locator('[data-testid="tnd-publication-progress"]')).toContainText("2 of 4 required channels confirmed.");
		await expect(page.locator('[data-testid="tnd-channel-STATE_PORTAL"] .kt-status')).toHaveText("Confirmed");
		await expect(page.locator('[data-testid="tnd-confirm-channel"]')).toHaveCount(2);

		await page.locator('[data-testid="tnd-channel-STATE_PORTAL"] [data-testid="tnd-view-confirmation"]').click();
		await expect(page.locator('[data-testid="tnd-confirmation-view"]')).toContainText("REF-STATE_PORTAL");
		await page.locator('[data-testid="tnd-cv-close"]').click();

		await page.locator('[data-testid="tnd-channel-NOTICE_BOARD"] [data-testid="tnd-confirm-channel"]').click();
		const dialog = page.locator('[data-testid="tnd-channel-dialog"]');
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Confirm notice-board publication");
		await expect(dialog.locator('[data-testid="tnd-ch-url"]')).toHaveCount(0);
		await dialog.locator('[data-testid="tnd-ch-confirm"]').click();
		await expect(dialog.locator('[data-testid="tnd-ch-error-available_at"]')).toBeVisible();
		await expect(dialog.locator('[data-testid="tnd-ch-error-evidence_file"]')).toHaveText("Attach the publication evidence file.");
		await expect(page.locator(".modal.show")).toHaveCount(0);

		await dialog.locator('[data-testid="tnd-ch-available"]').fill("2027-05-15T08:15");
		await dialog.locator('[data-testid="tnd-ch-reference"]').fill("NB-MOH-2027-033");
		await uploadEvidence(page, '[data-testid="tnd-ch-choose-file"]');
		await expect(dialog.locator('[data-testid="tnd-ch-filename"]')).toHaveText("evidence.png");
		await dialog.locator("label.kt-checkbox").click();
		await dialog.locator('[data-testid="tnd-ch-confirm"]').click();
		await expectSettled(page);
		await expect(dialog).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-publication-progress"]')).toContainText("3 of 4 required channels confirmed.");
		await expect(page.locator('[data-testid="tnd-channel-NOTICE_BOARD"] .kt-status')).toHaveText("Confirmed");
		await page.reload();
		await expectReady(page, "publication");
		await expect(page.locator('[data-testid="tnd-channel-NOTICE_BOARD"] .kt-status')).toHaveText("Confirmed");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("invalid evidence and an already-confirmed channel render as notices, never a Frappe dialog", async ({ page }) => {
		const state = resetFixture("reset_publication_fixture", { confirmed: 2 });
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/publication`);
		await expectReady(page, "publication");
		for (const [code, testid] of [["TND_PUBLICATION_EVIDENCE_INVALID", "tnd-invalid-evidence"], ["TND_PUBLICATION_ALREADY_CONFIRMED", "tnd-already-confirmed"]]) {
			await page.route("**/api/method/kentender_procurement.tenders.api.confirm_publication_channel", async (route) => {
				await route.fulfill({ status: 417, contentType: "application/json", body: JSON.stringify({ exc_type: "TendersError", kt_error_code: code, kt_error_message: "refused" }) });
				await page.unroute("**/api/method/kentender_procurement.tenders.api.confirm_publication_channel");
			});
			await page.locator('[data-testid="tnd-channel-NATIONAL_NEWSPAPERS"] [data-testid="tnd-confirm-channel"]').click();
			const dialog = page.locator('[data-testid="tnd-channel-dialog"]');
			await dialog.locator('[data-testid="tnd-ch-available"]').fill("2027-05-15T08:20");
			await dialog.locator('[data-testid="tnd-ch-reference"]').fill("NP-MOH-2027-033");
			await uploadEvidence(page, '[data-testid="tnd-ch-choose-file"]');
			await dialog.locator("label.kt-checkbox").click();
			await dialog.locator('[data-testid="tnd-ch-confirm"]').click();
			await expectSettled(page);
			await expect(page.locator(`[data-testid="${testid}"]`)).toBeVisible();
			await expect(page.locator(".modal.show")).toHaveCount(0);
		}
	});

	test("the AO may withdraw only before any confirmation; the Tender returns to Approved", async ({ page }) => {
		const state = resetFixture("reset_publication_fixture", { confirmed: 0 });
		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/publication`);
		await expectReady(page, "publication");
		await page.locator('[data-testid="tnd-withdraw-authorisation"]').click();
		await page.locator('[data-testid="tnd-withdraw-dialog-reason"]').fill("The notice period was set before the corrected budget figure was confirmed.");
		await page.locator('[data-testid="tnd-withdraw-dialog-confirm"]').click();
		await expectReady(page, "authorisation");
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Awaiting publication authorisation");
	});
});
