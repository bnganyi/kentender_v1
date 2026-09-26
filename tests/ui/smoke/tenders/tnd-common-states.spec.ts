import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AO, OFFICER, PASSWORD, collectConsoleErrors, expectReady, gotoTenders, resetFixture, restoreSite } from "./helpers";

/**
 * TPR-CHG-001 v0.12 slice I — TPR-DES-14 Common states (§10.15) as full
 * inline states with no journey or next step: Not found, Source
 * unavailable, Already started, Stale write, Publication not configured.
 * The bound-release states need a superseded or withdrawn installed release,
 * which would change the whole site's Tender format; they are covered by
 * test_template_binding and the component tests instead.
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
		await expect(page.locator('[data-kt="journey"]')).toHaveCount(0);
		await page.locator('[data-testid="tnd-state-action-back"]').click();
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
		await page.locator('[data-testid="tnd-state-action-open-tender"]').click();
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
		await page.locator('[data-testid="tnd-state-action-reload"]').click();
		await expectReady(page, "details");
	});

	test("Publication not configured: a routine reader is told a System Manager must configure it", async ({ page }) => {
		const state = resetFixture("reset_awaiting_ao_fixture");
		await login(page, AO, PASSWORD);
		// the publication read answers as it does when no governed rule applies
		await page.route("**/api/method/kentender_procurement.tenders.api.get_tender_publication*", async (route) => {
			const response = await route.fetch();
			const body = await response.json();
			body.message = { ...body.message, rule_error: "TND_PUBLICATION_RULE_UNAVAILABLE", rule: null, can_configure: false };
			await route.fulfill({ response, json: body });
		});
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "rule-unavailable");
		await expect(page.locator('[data-testid="tnd-state-text"]')).toHaveText("The publication rule is not configured for this Tender. A System Manager must configure it.");
		await expect(page.locator('[data-testid="tnd-state-rule-unavailable"] button')).toHaveText(["Back to Tenders"]);
		await expect(page.locator('[data-testid="tnd-authorise-publication"]')).toHaveCount(0);
	});
});
