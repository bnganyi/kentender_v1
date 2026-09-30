import { expect, test } from "@playwright/test";

import { collectPortalConsoleErrors, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { PASSWORD, evaluationWorld, restoreEvlWorld } from "./evlWorld";

/**
 * EVL-CHG-001 v0.4 §9.7 — the supplier's reply in the portal (boards
 * D06-SUPPLIER → D06-RECEIVED), phase 12, at 390 px. The supplier reaches
 * the question from their Tender page, saves a private draft that survives a
 * reload, sends the reply once, and then sees only their own receipt. One
 * fixture entity: the Playwright Tender's evaluation, from the "sent" world.
 */

test.describe.configure({ mode: "serial", timeout: 600_000 });

test.describe("EVL supplier reply", () => {
	test.afterAll(() => restoreEvlWorld());

	test("from the Tender page to a received reply, with a private draft on the way", async ({ page }) => {
		const world = evaluationWorld("sent");
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 390, height: 844 });
		await loginToPortal(page, world.people.supplier, PASSWORD, `/tenders/${world.tender_reference}`);
		await waitForPortal(page);

		// the Tender page names the question and links to it
		const link = page.locator(`a[href="/tenders/${world.tender_reference}/bid/evaluation-clarifications/${world.clarification}"]`);
		await expect(link).toBeVisible({ timeout: 30_000 });
		await link.click();
		const screen = page.locator('[data-testid="evl-supplier"]');
		await expect(screen).toHaveAttribute("data-state", "Sent", { timeout: 30_000 });
		await expect(screen.locator('[data-testid="evl-next-step-headline"]')).toHaveText(/^Reply by /);
		await expect(screen).toContainText("Please identify the page and section");
		await expect(screen).not.toContainText(/Meets|Needs review|Position|ranked/);
		await expectNoHorizontalOverflow(page);
		await page.screenshot({ path: "docs/mvp-1-r1/15_bid_evaluation/evidence/v0_4/D06-SUPPLIER.png", fullPage: true });

		// a draft is private and survives a reload
		await screen.locator('[data-testid="evl-field-body"]').fill("The service address is on page 2, section 3 of Kenya service-centre details.");
		await screen.locator('[data-testid="evl-action-save-draft"]').click();
		await expect(screen).toHaveAttribute("data-pending", "false");
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(screen.locator('[data-testid="evl-field-body"]')).toHaveValue("The service address is on page 2, section 3 of Kenya service-centre details.", { timeout: 30_000 });

		// the reply is sent once; the page then shows the receipt, and nothing to send
		await screen.locator('[data-testid="evl-action-send-reply"]').click();
		await expect(screen.locator('[data-testid="evl-next-step-headline"]')).toHaveText("Your reply has been received for committee review.", { timeout: 30_000 });
		await expect(screen.locator('[data-testid="evl-action-send-reply"]')).toHaveCount(0);
		await expect(screen).toContainText("Reply received");
		await page.screenshot({ path: "docs/mvp-1-r1/15_bid_evaluation/evidence/v0_4/D06-RECEIVED.png", fullPage: true });
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
