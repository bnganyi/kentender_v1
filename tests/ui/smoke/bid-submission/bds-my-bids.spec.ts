import { expect, test } from "@playwright/test";

import { collectPortalConsoleErrors, expectNoFrappeDialog, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { bdsFixture, restoreBdsWorld } from "./bdsWorld";

/**
 * BDS-CHG-001 v0.8 §10.6 / §10.20 (plan Phase 11, slice 11.5) — My bids and
 * Receipts, as the organisation's representative (David) and signatory
 * (Mary), and as another organisation's person (Peter). Each world is built
 * through the real commands on the Tenders test Tender.
 */
type World = { state: string; tender_reference: string; bid_reference: string; receipt_reference: string; acknowledgement_reference: string; organisation: string; password: string; representative: string; signatory: string; other_user: string };

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BDS-DES-05 My bids / BDS-DES-17 Receipts", () => {
	test.afterAll(() => restoreBdsWorld());

	test("with no bid, My bids offers View Tenders and Receipts says there are none", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "empty" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, "/my-bids");
		await expect(page.getByTestId("bds-bids-empty")).toContainText("No bids yet. Find a Tender to start your first bid.");
		await expect(page.getByTestId("bds-bids-view-tenders")).toHaveAttribute("href", "/tenders");
		await page.goto("/account/receipts", { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-receipts-empty")).toContainText("No submission or withdrawal receipts for this organisation.");
		await expectNoFrappeDialog(page);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("a ready bid offers Review bid; the status filter lives in the address and survives reload and back", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "ready" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, "/my-bids");
		const row = page.getByTestId(`bds-bid-row-${world.bid_reference}`);
		await expect(row).toContainText("Ready to submit");
		await expect(row).toContainText(/Draft Version \d+/);
		await expect(row.getByTestId("bds-bid-action-0")).toHaveText("Review bid");
		await expect(row.getByTestId("bds-bid-action-0")).toHaveAttribute("href", `/tenders/${world.tender_reference}/bid/review`);
		await expect(page.getByTestId("bds-bids-count")).toHaveText("1 bid");
		await expect(page.locator('[data-kt="journey"]')).toHaveCount(0);
		await page.getByTestId("bds-bids-status").selectOption("Submitted");
		await expect(page).toHaveURL(/status=Submitted/);
		await expect(page.getByTestId("bds-bids-empty")).toContainText("No bids match these filters.");
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-bids-status")).toHaveValue("Submitted");
		await expect(page.getByTestId("bds-bids-empty")).toBeVisible();
		await page.getByTestId("bds-bids-empty").getByRole("button", { name: "Clear filters" }).click();
		await expect(row).toBeVisible();
		await expect(page).not.toHaveURL(/status=/);
		await expectNoFrappeDialog(page);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("a withdrawn bid: the signatory may start a replacement, the representative only reads; Receipts lists both records", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "withdrawn" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, "/my-bids");
		const row = page.getByTestId(`bds-bid-row-${world.bid_reference}`);
		await expect(row).toContainText("Withdrawn");
		await expect(row.getByTestId("bds-bid-action-0")).toHaveText("View acknowledgement");
		await expect(row.getByTestId("bds-bid-action-0")).toHaveAttribute("href", `/tenders/${world.tender_reference}/bid/receipt/${world.acknowledgement_reference}`);
		await expect(row.getByTestId("bds-bid-action-1")).toHaveCount(0);

		await page.goto("/account/receipts", { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId(`bds-receipt-row-${world.receipt_reference}`)).toContainText("Submitted");
		await expect(page.getByTestId(`bds-receipt-row-${world.acknowledgement_reference}`)).toContainText("Withdrawn");
		await expect(page.getByTestId("bds-receipts-count")).toHaveText("2 records");
		await expect(page.getByTestId("bds-receipts")).not.toContainText(/KES|Start replacement|Withdraw bid/);
		await page.setViewportSize({ width: 390, height: 844 });
		await expect(page.getByTestId("bds-receipts-cards")).toBeVisible();
		await expectNoHorizontalOverflow(page);
		await page.setViewportSize({ width: 1440, height: 1024 });

		await loginToPortal(page, world.signatory, world.password, "/my-bids");
		await expect(row.getByTestId("bds-bid-action-1")).toHaveText("Start replacement");
		await row.getByTestId("bds-bid-action-1").click();
		await expect(page).toHaveURL(new RegExp(`/tenders/${world.tender_reference}/bid$`));
		await page.goto("/my-bids", { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(row).not.toContainText("Withdrawn");
		await expect(row.getByTestId("bds-bid-action-0")).toHaveText(/Continue bid|Review bid/);
		await expectNoFrappeDialog(page);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("another organisation's person sees none of these bids or receipts", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "submitted" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.other_user, world.password, "/my-bids");
		await expect(page.locator("body")).not.toContainText(world.bid_reference);
		await page.goto(`/account/receipts?organisation=${world.organisation}`, { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-state-not-found")).toBeVisible();
		await expect(page.locator("body")).not.toContainText(world.receipt_reference);
		expect(errors.filter((e) => !/404 \(Not Found\)/.test(e)), errors.join(" | ")).toEqual([]);
	});
});
