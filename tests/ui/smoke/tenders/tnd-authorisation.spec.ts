import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AO, BOTH, PASSWORD, collectConsoleErrors, expectReady, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.8 slice 7g — TPR-DES-07 AO publication authorisation. */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-07 AO publication authorisation", () => {
	test.afterAll(() => restoreSite());

	test("the package facts, the read-only channels, View Invitation, then authorisation moves to confirmation", async ({ page }) => {
		const state = resetFixture("reset_awaiting_ao_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "authorisation");
		await expect(page.locator('[data-testid="tnd-ready-to-authorise"]')).toContainText("The Tender is shown as Published only after every required channel is confirmed.");
		await expect(page.locator('[data-testid="tnd-approval-trail"]')).toContainText("Approved by");
		await expect(page.locator('[data-testid="tnd-channel-table"] tbody tr')).toHaveCount(4);
		await expect(page.locator('[data-testid="tnd-channel-table"] .kt-status')).toHaveText(["Not started", "Not started", "Not started", "Not started"]);
		// absence: no channel selector, no edit control, no "Mark as published"
		await expect(page.locator('[data-testid="tnd-channel-table"] select, [data-testid="tnd-channel-table"] input')).toHaveCount(0);
		await expect(page.getByRole("button", { name: /Mark as published/i })).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-field-tender_title"]')).toHaveCount(0);

		await page.locator('[data-testid="tnd-view-invitation"]').click();
		await expect(page.locator('[data-testid="tnd-doc-frame"]')).toContainText(/Invitation|Tender/i, { timeout: 30_000 });
		await expect(page.locator('[data-testid="tnd-doc-name"]')).not.toHaveText("");
		await page.locator('[data-testid="tnd-doc-close"]').click();

		await page.locator('[data-testid="tnd-authorise-publication"]').click();
		await expect(page.locator('[data-testid="tnd-authorise-dialog"]')).toContainText("It does not itself publish the Tender or edit the package.");
		await page.locator('[data-testid="tnd-authorise-dialog-confirm"]').click();
		await expectReady(page, "publication");
		await expect(page.locator('[data-testid="tnd-publication-progress"]')).toContainText("0 of 4 required channels confirmed.");
		// the AO never confirms a channel
		await expect(page.locator('[data-testid="tnd-confirm-channel"]')).toHaveCount(0);
		await page.reload();
		await expectReady(page, "publication");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("segregation: the actor who prepared the package cannot authorise it", async ({ page }) => {
		const state = resetFixture("reset_segregation_fixture", { stage: "ao" });
		await login(page, BOTH, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "authorisation");
		await expect(page.locator('[data-testid="tnd-segregation"]')).toContainText("Another Accounting Officer must decide it.");
		await expect(page.locator('[data-testid="tnd-authorise-publication"]')).toHaveCount(0);
	});
});
