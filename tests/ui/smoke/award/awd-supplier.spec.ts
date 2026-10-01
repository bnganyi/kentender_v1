import { expect, test } from "@playwright/test";

import { collectPortalConsoleErrors, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { DAVID, EVIDENCE, MARY, PASSWORD, awardWorld, closeSession, restoreAwardWorld } from "./awdWorld";

/**
 * AWD-CHG-001 v0.4 slice 6 (boards D04, X01, V13, X11, V14, V22; tracker
 * AWD4-604), at 390 px in the supplier portal: the Authorised Signatory
 * accepts the exact notice; the representative can read and ask for an
 * explanation but not respond; an unsuccessful bidder sees only their own
 * result; a late response is kept and labelled.
 */

test.describe.configure({ mode: "serial", timeout: 300_000 });

async function openNotice(page, user: string, notice: string) {
	await page.setViewportSize({ width: 390, height: 844 });
	await loginToPortal(page, user, PASSWORD, `/supplier/awards/${notice}`);
	await waitForPortal(page);
	const portal = page.locator('[data-testid="awd-portal"]');
	await expect(portal.locator('[data-testid="awd-next-step-headline"]')).toBeVisible({ timeout: 30_000 });
	return portal;
}

test.describe("Award — the supplier's notice", () => {
	test.afterAll(async () => {
		await closeSession();
		restoreAwardWorld();
	});

	test("Mary accepts the exact notice; David cannot", async ({ browser }) => {
		const world = awardWorld("notified");
		let context = await browser.newContext({ baseURL: process.env.UI_BASE_URL || "http://127.0.0.1:8000" });
		let page = await context.newPage();
		const errors = collectPortalConsoleErrors(page);
		let portal = await openNotice(page, DAVID, world.notice);
		await expect(portal).toHaveAttribute("data-screen", "supplier-representative");
		await expect(portal.locator('[data-testid="awd-next-step-headline"]')).toHaveText("Your tender was successful.");
		await expect(portal).toContainText("Mary Wanjiku must respond for Afya Digital Supplies Limited.");
		await expect(portal.getByRole("button", { name: "Accept award" })).toHaveCount(0);
		await expectNoHorizontalOverflow(page);
		await page.screenshot({ path: `${EVIDENCE}/V13.png`, fullPage: true });
		await portal.getByRole("button", { name: "Request explanation" }).click();
		await portal.locator('[data-testid="awd-dialog-field-dlg_request"]').fill("Please explain the recorded award result.");
		await portal.locator('[data-testid="awd-dialog-send-request"]').click();
		await expect(portal.locator('[data-testid="awd-dialog"]')).toHaveCount(0, { timeout: 30_000 });
		await context.close();

		context = await browser.newContext({ baseURL: process.env.UI_BASE_URL || "http://127.0.0.1:8000" });
		page = await context.newPage();
		portal = await openNotice(page, MARY, world.notice);
		await expect(portal).toHaveAttribute("data-screen", "supplier-notice");
		await expect(portal).toContainText("Accepting this award does not create a contract.");
		await expect(portal.locator('[data-testid="awd-fact-reply-by"]')).toHaveText("24 Jun 2027, 17:00 EAT");
		await expectNoHorizontalOverflow(page);
		await page.screenshot({ path: `${EVIDENCE}/D04.png`, fullPage: true });
		await portal.locator('[data-testid="awd-action-accept-award"]').click();
		const dialog = portal.locator('[data-testid="awd-dialog"]');
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Accept this award?");
		await expect(dialog.locator('[data-testid="awd-dialog-body"]')).toHaveText("I accept Award notice 1 on behalf of Afya Digital Supplies Limited.");
		await page.screenshot({ path: `${EVIDENCE}/X01.png`, fullPage: true });
		await dialog.locator('[data-testid="awd-dialog-accept-award"]').click();
		await expect(portal.locator('[data-testid="awd-next-step-headline"]')).toHaveText("You accepted this award.", { timeout: 30_000 });
		await expect(portal.getByRole("button", { name: "Accept award" })).toHaveCount(0);
		expect(errors, errors.join(" | ")).toEqual([]);
		await context.close();
	});

	test("the unsuccessful bidder sees their own result only", async ({ browser }) => {
		const world = awardWorld("unsuccessful");
		const context = await browser.newContext({ baseURL: process.env.UI_BASE_URL || "http://127.0.0.1:8000" });
		const page = await context.newPage();
		const portal = await openNotice(page, MARY, world.notices["Afya Digital Supplies Limited"]);
		await expect(portal.locator('[data-testid="awd-next-step-headline"]')).toHaveText("Your tender was unsuccessful.");
		await expect(portal.locator('[data-testid="awd-fact-successful-supplier"]')).toHaveText("Jirani Office Supplies Limited");
		await expect(portal.locator('[data-testid="awd-def-reason"]')).toHaveText("Your tender met the requirements. Another responsive tender had a lower evaluated price.");
		await page.screenshot({ path: `${EVIDENCE}/V14.png`, fullPage: true });
		await page.goto(`/supplier/awards/${world.notices["Jirani Office Supplies Limited"]}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator("body")).toContainText(/Not found|does not exist/i);
		await context.close();
	});

	test("a late response is kept and labelled", async ({ browser }) => {
		const world = awardWorld("late-response");
		const context = await browser.newContext({ baseURL: process.env.UI_BASE_URL || "http://127.0.0.1:8000" });
		const page = await context.newPage();
		const portal = await openNotice(page, MARY, world.notice);
		await expect(portal.locator('[data-testid="awd-next-step-headline"]')).toHaveText("Your response was received after the deadline. It cannot be used to proceed with this award.");
		await expect(portal.locator('[data-testid="awd-fact-received"]')).toHaveText("24 Jun 2027, 17:01 EAT");
		await page.screenshot({ path: `${EVIDENCE}/V22.png`, fullPage: true });
		await context.close();
	});
});
