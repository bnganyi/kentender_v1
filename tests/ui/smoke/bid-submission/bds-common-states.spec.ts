import { expect, test } from "@playwright/test";

import { collectPortalConsoleErrors, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { bdsFixture, restoreBdsWorld } from "./bdsWorld";

/**
 * BDS-CHG-001 v0.8 §10.17 BDS-DES-16 and §11.5 View status (plan Phase 11,
 * slice 11.15), live on the Tenders test Tender for Afya (Test): a pending
 * attempt reads Confirmation pending and offers no new Submit; another
 * person's change shows Stale Draft in place of the confirmation until
 * Reload; a failed read shows Bid could not be loaded with Try again; after
 * the deadline the Submit page is Deadline passed.
 */
type World = { tender_reference: string; bid_reference: string; password: string; representative: string; signatory: string; other_user: string };

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BDS-DES-16 common states", () => {
	test.afterAll(() => restoreBdsWorld());

	test("a pending attempt is Confirmation pending on the Submit page and in View status", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "pending" });
		const errors = collectPortalConsoleErrors(page);
		const base = `/tenders/${world.tender_reference}/bid`;
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, `${base}/submit`);
		await expect(page.getByTestId("bds-submit-pending")).toBeVisible();
		await expect(page.getByTestId("bds-submit-open")).toHaveCount(0);
		await page.getByTestId("bds-submit-pending").getByRole("link", { name: "View status" }).click();
		await expect(page).toHaveURL(new RegExp(`${base}/status$`));
		const state = page.getByTestId("bds-state-confirmation-pending");
		await expect(state.locator("h1")).toHaveText("Submission confirmation is still pending. Do not submit again.");
		await expect(state).toContainText("Correlation COR-BDS-");
		await state.getByRole("button", { name: "View status" }).click(); // reads again, changes nothing
		await expect(page.getByTestId("bds-state-confirmation-pending")).toBeVisible();
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-state-confirmation-pending")).toBeVisible();
		await page.setViewportSize({ width: 390, height: 844 });
		await expectNoHorizontalOverflow(page);
		expect(errors.filter((e) => !/404 \(Not Found\)/.test(e)), errors.join(" | ")).toEqual([]);
	});

	test("another person's change shows Stale Draft in place of the confirmation until Reload", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "review" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, `/tenders/${world.tender_reference}/bid/submit`);
		await expect(page.getByTestId("bds-submit-decision")).toBeVisible();
		bdsFixture("change_bid_as_representative", { bid_reference: world.bid_reference });
		await page.getByTestId("bds-submit-decision").locator("label.kt-checkbox").click();
		await page.getByTestId("bds-submit-open").click();
		await page.getByTestId("bds-submit-confirm").click();
		const stale = page.getByTestId("bds-state-stale-draft");
		await expect(stale).toContainText("Another person changed this bid. Reload before continuing.");
		await expect(page.getByTestId("bds-submit-decision")).toHaveCount(0);
		await stale.getByRole("button", { name: "Reload" }).click();
		await expect(page.getByTestId("bds-state-stale-draft")).toHaveCount(0);
		await expect(page.getByTestId("bds-submit-decision")).toBeVisible();
	});

	test("a failed read is Bid could not be loaded, and Try again reads it", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "review" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, "/my-bids");
		let fail = true;
		await page.route("**/api/method/kentender_procurement.bid_submission.api.get_bid_task**", (route) => (fail ? route.fulfill({ status: 500, body: "{}" }) : route.continue()));
		await page.getByTestId(`bds-bid-row-${world.bid_reference}`).getByRole("link").first().click();
		const state = page.getByTestId("bds-state-load-failure");
		await expect(state.locator("h1")).toHaveText("Bid could not be loaded");
		fail = false;
		await state.getByRole("button", { name: "Try again" }).click();
		await expect(page.getByTestId("bds-state-load-failure")).toHaveCount(0);
	});

	test("after the deadline the Submit page is Deadline passed", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "review" });
		bdsFixture("set_instant", { instant: "2027-06-05 11:00:01" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, `/tenders/${world.tender_reference}/bid/submit`);
		const state = page.getByTestId("bds-state-deadline-passed");
		await expect(state.locator("h1")).toHaveText("The submission deadline has passed. This bid was not submitted.");
		await expect(state).toContainText("trusted server time 5 Jun 2027, 11:00:01 EAT");
		await expect(state.getByRole("link", { name: "Back to My bids" })).toHaveAttribute("href", "/my-bids");
	});
});
