import { expect, test } from "@playwright/test";

import { collectPortalConsoleErrors, expectNoFrappeDialog, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { bdsFixture, restoreBdsWorld } from "./bdsWorld";

/**
 * BDS-CHG-001 v0.8 §10.8 (plan Phase 11, slice 11.7) — Tender documents,
 * clarifications and addenda, as David of Afya (Test) on the Tenders test
 * Tender: first before any addendum (read the documents, ask a question,
 * continue), then after the Tenders world issues its addendum with the
 * notice still queued (the bid moves to the current Tender and the
 * acknowledgement saves).
 */
type World = { tender_reference: string; bid_reference: string; password: string; representative: string; other_user: string };

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BDS-DES-07 Tender documents, clarifications and addenda", () => {
	test.afterAll(() => restoreBdsWorld());

	test("before any addendum: read the documents, ask a question, continue to the next task", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "started" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, `/tenders/${world.tender_reference}/bid`);
		await page.getByTestId("bds-task-documents").getByRole("link").click();
		await expect(page).toHaveURL(new RegExp(`/tenders/${world.tender_reference}/bid/documents$`));
		const screen = page.getByTestId("bds-documents-task");
		await expect(screen.locator("h1")).toHaveText("Tender documents, clarifications and addenda");
		await expect(page.getByTestId("bds-documents-badge")).toHaveCount(0);
		await expect(page.getByTestId("bds-task-no-addenda")).toHaveText("No addenda have been issued.");
		const view = page.getByTestId("bds-task-documents-table").getByRole("link", { name: "View" }).first();
		const document = await page.request.get((await view.getAttribute("href")) || "");
		expect(document.status()).toBe(200);
		await page.getByTestId("bds-task-ask").click();
		const dialog = page.getByTestId("bds-question-dialog");
		await dialog.getByTestId("bds-question-text").fill("Can the laptops be delivered in two lots before the latest delivery date?");
		await dialog.getByTestId("bds-question-send").click();
		await expect(dialog.getByTestId("bds-question-sent")).toContainText(/^Question received /);
		await dialog.getByTestId("bds-question-close").click();
		await expect(page.getByTestId("bds-documents-save")).toBeEnabled();
		await page.getByTestId("bds-documents-save").click();
		await expect(page).toHaveURL(new RegExp(`/tenders/${world.tender_reference}/bid/company$`));
		await page.goBack({ waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("bds-documents-task")).toBeVisible();
		await page.getByTestId("bds-documents-back").click();
		await expect(page.getByTestId("bds-workspace")).toBeVisible();
		await expectNoFrappeDialog(page);
		expect(errors.filter((e) => !/404 \(Not Found\)/.test(e)), errors.join(" | ")).toEqual([]);
	});

	test("an issued addendum: its queued notice informs, Save and continue waits, then the bid moves and the acknowledgement saves", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "addendum" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, `/tenders/${world.tender_reference}/bid/documents`);
		await expect(page.getByTestId("bds-documents-badge")).toHaveText("Needs attention");
		const notice = page.locator('[data-testid^="bds-addendum-notice-"]');
		await expect(notice).toContainText("Queued");
		await expect(notice).toContainText("This notice is waiting to be sent. You can read the current Tender information here now.");
		const save = page.getByTestId("bds-documents-save");
		await expect(save).toBeDisabled();
		await expect(page.getByTestId("bds-documents-blocked")).toHaveText("Acknowledge the addendum to continue.");
		await page.locator('[data-testid^="bds-acknowledge-"]').click(); // the label; the Industry checkbox draws its own box
		await expect(save).toBeEnabled();
		await save.click();
		await expect(page).toHaveURL(new RegExp(`/tenders/${world.tender_reference}/bid/company$`));
		await page.goto(`/tenders/${world.tender_reference}/bid/documents`, { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-documents-badge")).toHaveText("Complete");
		await expect(page.locator('[data-testid^="bds-acknowledge-"] input')).toBeChecked();
		await expect(page.getByTestId("bds-acknowledged")).toContainText("Acknowledged by David Ouma on ");
		await page.setViewportSize({ width: 390, height: 844 });
		await expect(page.getByTestId("bds-task-addenda-cards")).toBeVisible();
		await expectNoHorizontalOverflow(page);
		await expectNoFrappeDialog(page);
		expect(errors.filter((e) => !/404 \(Not Found\)/.test(e)), errors.join(" | ")).toEqual([]);
	});

	test("another organisation's person is told the bid is not found", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "started" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.other_user, world.password, `/tenders/${world.tender_reference}/bid/documents`);
		await expect(page.getByTestId("bds-state-bid-not-found")).toBeVisible();
		await expect(page.locator("body")).not.toContainText(world.bid_reference);
	});
});
