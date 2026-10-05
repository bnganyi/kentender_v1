import { expect, test } from "@playwright/test";

import { collectPortalConsoleErrors, expectNoFrappeDialog, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { bdsFixture, restoreBdsWorld } from "./bdsWorld";

/**
 * BDS-CHG-001 v0.8 §10.14–10.15 (plan Phase 11, slices 11.13–11.14) — the
 * receipt, replacement and withdrawal on the Tenders test Tender for Afya
 * (Test), with the Test Trust Service and Test Tender Box. Mary reads her
 * receipt and replaces the bid (the new receipt names the Version it
 * superseded); in a second world she withdraws it and starts again from the
 * acknowledgement. David only reads; after the deadline nothing can change;
 * another organisation sees nothing.
 */
type World = { tender_reference: string; bid_reference: string; receipt_reference: string; password: string; representative: string; signatory: string; other_user: string };

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BDS-DES-13 receipt / BDS-DES-14 replacement and withdrawal", () => {
	test.afterAll(() => restoreBdsWorld());

	test("Mary reads her receipt, replaces the bid, and the new receipt names what it superseded", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "submitted" });
		const errors = collectPortalConsoleErrors(page);
		const base = `/tenders/${world.tender_reference}/bid`;
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, `${base}/receipt/${world.receipt_reference}`);
		await expect(page.getByRole("heading", { level: 1, name: "Bid submitted" })).toBeVisible();
		await expect(page.getByTestId("bds-receipt-badge")).toHaveText("Submitted");
		await expect(page.getByTestId("bds-receipt-facts")).toContainText(world.receipt_reference);
		await expect(page.getByTestId("bds-receipt-facts")).toContainText("Mary Wanjiku");
		await expect(page.getByTestId("bds-receipt-sentence")).toContainText("remains valid until a replacement is accepted");
		const pdf = await page.request.get((await page.getByTestId("bds-receipt-download").getAttribute("href")) || "");
		expect([pdf.status(), pdf.headers()["content-type"]]).toEqual([200, expect.stringContaining("pdf")]);
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-receipt-withdraw")).toBeVisible();

		// Prepare replacement → Create replacement Draft → the bid, with Version 1 still current
		await page.getByTestId("bds-receipt-prepare_replacement").click();
		await expect(page).toHaveURL(new RegExp(`${base}/replace$`));
		await expect(page.getByTestId("bds-replacement-notice")).toContainText(`Receipt ${world.receipt_reference} remains current`);
		await page.getByTestId("bds-replacement-create").click();
		await expect(page).toHaveURL(new RegExp(`${base}$`));
		await page.goBack({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-replacement-continue")).toBeVisible();

		// submit the replacement
		await page.goto(`${base}/submit`, { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await page.getByTestId("bds-submit-decision").locator("label.kt-checkbox").click();
		await page.getByTestId("bds-submit-open").click();
		await page.getByTestId("bds-submit-confirm").click();
		await expect(page).toHaveURL(new RegExp(`${base}/receipt/RCPT-`), { timeout: 60_000 });
		await expect(page.getByRole("heading", { level: 1, name: "Replacement bid submitted" })).toBeVisible();
		const lineage = page.getByTestId("bds-receipt-lineage");
		await expect(lineage).toContainText("Version 1 superseded");
		await lineage.getByRole("link").click();
		await expect(page).toHaveURL(new RegExp(`${base}/receipt/${world.receipt_reference}$`));
		await expect(page.getByTestId("bds-receipt-badge")).toHaveText("Superseded");
		await expect(page.getByTestId("bds-receipt-withdraw")).toHaveCount(0);
		await page.setViewportSize({ width: 390, height: 844 });
		await expectNoHorizontalOverflow(page);
		await expectNoFrappeDialog(page);
		expect(errors.filter((e) => !/404 \(Not Found\)/.test(e)), errors.join(" | ")).toEqual([]);
	});

	test("Mary withdraws with a reason and starts again from the acknowledgement; David only reads", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "submitted" });
		const base = `/tenders/${world.tender_reference}/bid`;
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, `${base}/receipt/${world.receipt_reference}`);
		await expect(page.getByTestId("bds-receipt-actions").locator(".btn")).toHaveText(["Print receipt"]);
		await page.context().clearCookies();

		await loginToPortal(page, world.signatory, world.password, base);
		await page.getByRole("button", { name: "Withdraw bid" }).click(); // the bid page's next step leads to the receipt's dialog
		const dialog = page.getByRole("dialog", { name: "Withdraw this bid?" });
		await expect(dialog).toBeVisible();
		await dialog.getByLabel("Reason for withdrawal").fill("Too short");
		await dialog.getByTestId("bds-withdraw-confirm").click();
		await expect(dialog.getByTestId("bds-withdraw-error")).toBeVisible();
		await dialog.getByLabel("Reason for withdrawal").fill("Our pricing changed; we will submit a corrected bid.");
		await dialog.getByTestId("bds-withdraw-confirm").click();
		await expect(page).toHaveURL(new RegExp(`${base}/receipt/WD-`));
		await expect(page.getByRole("heading", { level: 1, name: "Bid withdrawn" })).toBeVisible();
		const ack = await page.request.get((await page.getByTestId("bds-acknowledgement-download").getAttribute("href")) || "");
		expect(ack.status()).toBe(200);
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await page.getByTestId("bds-start-replacement").click();
		await expect(page).toHaveURL(new RegExp(`${base}$`));
	});

	test("after the deadline the receipt only reads; another organisation is told it is not found", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "submitted" });
		bdsFixture("set_instant", { instant: "2027-06-05 11:00:01" });
		const receipt = `/tenders/${world.tender_reference}/bid/receipt/${world.receipt_reference}`;
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, receipt);
		await expect(page.getByTestId("bds-receipt-actions").locator(".btn")).toHaveText(["Print receipt"]);
		await expect(page.getByTestId("bds-receipt-sentence")).toContainText("Submission changes closed on ");
		await page.context().clearCookies();
		await loginToPortal(page, world.other_user, world.password, receipt);
		await expect(page.getByTestId("bds-state-receipt-not-found")).toBeVisible();
		await expect(page.locator("body")).not.toContainText(world.bid_reference);
	});
});
