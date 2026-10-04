import { expect, test } from "@playwright/test";

import { collectPortalConsoleErrors, expectNoFrappeDialog, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { bdsFixture, restoreBdsWorld } from "./bdsWorld";

/**
 * BDS-CHG-001 v0.8 §4.4.4, §10.3, §10.7 (plan Phase 13; TPR-CHG-001 v0.13,
 * approved 28 Sep 2026) — a published Tender whose bound template release is
 * superseded or withdrawn, on the Tenders test Tender with Afya (Test) and
 * Kisiwa (Test). Superseded: Peter can still start. Withdrawn: Mary keeps her
 * receipt and may withdraw but not replace; David's Draft is kept for reading
 * and waits on the Tender's Procurement Officer; Peter cannot start. The
 * installed release is never changed — the test controls force its state.
 */
type MyBidsWorld = { tender_reference: string; bid_reference: string; receipt_reference: string; password: string; representative: string; signatory: string; other_user: string };
type OverviewWorld = { tender_reference: string; bid_reference: string; password: string; afya_user: string; kisiwa_user: string };

const WITHDRAWN = "The current Tender documents and any existing bid receipt remain available. You cannot start or submit a bid against this format. An existing submitted bid has not been automatically withdrawn.";
const SUPERSEDED = "This published Tender remains on its existing format. You can read the current documents and, while the Tender is open and the format verifies, start or continue a bid. Check the deadline and addenda.";

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BDS-DES-02 / BDS-DES-06 on a superseded or withdrawn Tender format", () => {
	test.afterAll(() => restoreBdsWorld());

	test("superseded: the Tender says it stays on its format and Peter can still start a bid", async ({ page }) => {
		const world = bdsFixture<OverviewWorld>("reset_overview_fixture", { started: false });
		bdsFixture("set_bound_release", { state: "Superseded" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.kisiwa_user, world.password, `/tenders/${world.tender_reference}`);
		const notice = page.getByTestId("bds-overview-release");
		await expect(notice).toHaveText(SUPERSEDED);
		await expect(notice).not.toHaveClass(/is-warning/);
		await expect(page.getByTestId("bds-overview-action")).toHaveText("Start bid");
		await expectNoFrappeDialog(page);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("withdrawn: Mary keeps her receipt and may withdraw, but not replace; Peter cannot start", async ({ page }) => {
		const world = bdsFixture<MyBidsWorld>("reset_my_bids_fixture", { state: "submitted" });
		bdsFixture("set_bound_release", { state: "Withdrawn" });
		const errors = collectPortalConsoleErrors(page);
		const base = `/tenders/${world.tender_reference}`;
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, base);
		await expect(page.getByTestId("bds-overview-release")).toHaveText(WITHDRAWN);
		await expect(page.locator(".kt-page-actions .kt-btn")).toHaveText(["View Tender documents", "View receipt", "Withdraw bid"]);
		await expect(page.getByTestId("bds-overview-status")).toHaveCount(0);
		await page.getByRole("link", { name: "View Tender documents" }).click();
		await expect(page).toHaveURL(new RegExp(`${base}#bds-tender-documents$`));
		await expect(page.locator("#bds-tender-documents")).toBeInViewport();
		// Withdraw bid opens the withdrawal on the receipt; Prepare replacement is gone
		await page.getByRole("link", { name: "Withdraw bid" }).click();
		await expect(page).toHaveURL(new RegExp(`${base}/bid/receipt/${world.receipt_reference}`));
		await expect(page.getByTestId("bds-withdraw-dialog")).toBeVisible();
		await page.keyboard.press("Escape");
		await expect(page.getByTestId("bds-receipt-withdraw")).toBeVisible();
		await expect(page.getByTestId("bds-receipt-prepare_replacement")).toHaveCount(0);
		await page.setViewportSize({ width: 390, height: 844 });
		await page.goto(base, { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expectNoHorizontalOverflow(page);
		await expectNoFrappeDialog(page);
		expect(errors, errors.join(" | ")).toEqual([]);

		// another supplier reads the Tender and is offered no Start bid
		await page.context().clearCookies();
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.other_user, world.password, base);
		await expect(page.getByTestId("bds-overview-release")).toHaveText(WITHDRAWN);
		await expect(page.locator(".kt-page-actions .kt-btn")).toHaveText(["View Tender documents"]);
	});

	test("withdrawn: David's Draft is kept for reading and waits on the Tender's Procurement Officer", async ({ page }) => {
		const world = bdsFixture<MyBidsWorld>("reset_my_bids_fixture", { state: "ready" });
		bdsFixture("set_bound_release", { state: "Withdrawn" });
		const errors = collectPortalConsoleErrors(page);
		const bid = `/tenders/${world.tender_reference}/bid`;
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, bid);
		await expect(page.locator('[data-kt="next-step"]')).toContainText("holds the governed Tender resolution; this Draft is saved but cannot be submitted against the withdrawn format.");
		await expect(page.locator('[data-kt="next-step"]')).toContainText("Waiting on someone");
		await expect(page.getByTestId("bds-guidance-links").getByRole("link")).toHaveText(["View current Tender", "Supplier support"]);
		await expect(page.getByTestId("bds-workspace-action")).toHaveCount(0);
		await expect(page.getByTestId("bds-tasks-table").locator("tbody td a")).toHaveText(["View", "View", "View", "View", "View"]);
		// a task opens read-only: no Save and continue, rows open to View
		await page.getByTestId("bds-task-requirements").getByRole("link", { name: "View" }).click();
		await expect(page).toHaveURL(new RegExp(`${bid}/requirements$`));
		await expect(page.getByTestId("bds-technical-table")).toBeVisible();
		await expect(page.getByTestId("bds-requirements-save")).toHaveCount(0);
		await expect(page.getByTestId("bds-technical-table").getByRole("button", { name: "Edit" })).toHaveCount(0);
		// My bids offers View bid, not Continue
		await page.goto("/my-bids", { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId(`bds-bid-row-${world.bid_reference}`)).toContainText("View bid");
		await expect(page.getByTestId(`bds-bid-row-${world.bid_reference}`)).not.toContainText("Continue bid");
		await page.setViewportSize({ width: 390, height: 844 });
		await page.goto(bid, { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expectNoHorizontalOverflow(page);
		await expectNoFrappeDialog(page);
		expect(errors.filter((e) => !/404 \(Not Found\)/.test(e)), errors.join(" | ")).toEqual([]);
	});
});
