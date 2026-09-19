import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { OFFICER, PASSWORD, collectConsoleErrors, expectReady, gotoTenders, resetFixture, restoreSite } from "./helpers";

/**
 * TPR-CHG-001 v0.8 slice 7a — TPR-DES-14 Common states as full inline
 * states: Not found, Source unavailable, Already started, Stale write.
 */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-14 Common states", () => {
	test.afterAll(() => restoreSite());

	test("Not found for an unknown Tender; Source unavailable for an unknown handoff; both return to Tenders", async ({ page }) => {
		resetFixture("reset_start_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, "/TND-MOH-0000-000");
		await expectReady(page, "not-found");
		await expect(page.locator('[data-testid="tnd-state-not-found"]')).toContainText("Tender not found");
		await page.locator('[data-testid="tnd-state-action"]').click();
		await expectReady(page, "workspace");

		await gotoTenders(page, "/new/RQH-nothing");
		await expectReady(page, "source-unavailable");
		await expect(page.locator('[data-testid="tnd-state-source-unavailable"]')).toContainText("Authorised requisition unavailable");
		await expect(page.locator('[data-testid="tnd-start-dialog"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Already started links to the existing Tender; a stale write shows Tender changed with Reload", async ({ page }) => {
		const state = resetFixture("reset_draft_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/new/${state.handoff}`);
		await expectReady(page, "already-started");
		await expect(page.locator('[data-testid="tnd-state-already-started"]')).toContainText(`This requisition is linked to ${state.tender_reference}`);
		await page.locator('[data-testid="tnd-state-action"]').click();
		await expectReady(page, "details");

		// another user's write between load and save: the server refuses with
		// TND_STALE_VERSION and the screen shows the Stale write state.
		await page.route("**/api/method/kentender_procurement.tenders.api.save_tender_draft", async (route) => {
			await route.fulfill({ status: 417, contentType: "application/json", body: JSON.stringify({ exc_type: "TendersError", kt_error_code: "TND_STALE_VERSION", kt_error_message: "Another user changed this Tender. Reload before continuing." }) });
			await page.unroute("**/api/method/kentender_procurement.tenders.api.save_tender_draft");
		});
		await page.locator('[data-testid="tnd-save-draft"]').click();
		await expectReady(page, "stale");
		await expect(page.locator('[data-testid="tnd-state-stale"]')).toContainText("Tender changed");
		await expect(page.locator(".modal.show")).toHaveCount(0);
		await page.locator('[data-testid="tnd-state-action"]').click();
		await expectReady(page, "details");
	});
});
