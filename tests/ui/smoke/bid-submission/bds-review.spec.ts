import { expect, test } from "@playwright/test";

import { collectPortalConsoleErrors, expectNoFrappeDialog, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { bdsFixture, restoreBdsWorld } from "./bdsWorld";

/**
 * BDS-CHG-001 v0.8 §10.12 (plan Phase 11, slice 11.11) — Review bid on the
 * Tenders test Tender for Afya (Test): Mary, the Authorised Signatory, reads a
 * Ready bid whose physical original Charles recorded and is offered Submit
 * bid; with the production gate closed (the GATE world, through the test
 * controls) Submit is absent and the next step names the release operator.
 * David reads the same review without Submit; a rejected datasheet and an
 * addendum change are each linked at their task. Another organisation sees
 * nothing.
 */
type World = { tender_reference: string; bid_reference: string; password: string; representative: string; signatory: string; other_user: string };

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BDS-DES-11 Review bid", () => {
	test.afterAll(() => restoreBdsWorld());

	test("Mary reviews a ready bid and may submit it; a closed gate or David's role takes Submit away", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "review" });
		const errors = collectPortalConsoleErrors(page);
		const review = `/tenders/${world.tender_reference}/bid/review`;
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, review);
		await expect(page.getByRole("heading", { level: 1, name: "Review bid" })).toBeVisible();
		await expect(page.getByTestId("bds-review-result")).toHaveText("All required bid information is complete.");
		await expect(page.getByTestId("bds-review-security")).toContainText("Physical tender-security original recorded as received on 20 May 2027");
		await expect(page.getByTestId("bds-review-action")).toHaveText("Submit bid");
		await expect(page.getByTestId("bds-review-action")).toHaveAttribute("href", `/tenders/${world.tender_reference}/bid/submit`);
		await expect(page.getByTestId("bds-review-submit")).toBeVisible();
		await expect(page.getByTestId("bds-review-summary")).toContainText(`${world.bid_reference} · Draft Version`);
		await expect(page.getByTestId("bds-review-tasks").locator("tbody tr")).toHaveCount(5);
		await expect(page.getByTestId("bds-review-offering")).toContainText("Warranty");
		await expect(page.getByTestId("bds-review-declarations")).toContainText("accepted");

		// a task's Review link opens it; back returns to the review
		await page.getByTestId("bds-review-task-price").getByRole("link", { name: "Review" }).click();
		await expect(page).toHaveURL(new RegExp(`/bid/price$`));
		await page.goBack({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-review-result")).toBeVisible();
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-review-action")).toHaveText("Submit bid");

		// the GATE world: the production gate closed through the test controls
		bdsFixture("set_gate", { closed: true });
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-review-result")).toHaveText("All required bid information is complete.");
		await expect(page.locator(".kt-next-step-headline")).toContainText("holds the verified production-submission release.");
		await expect(page.getByText("Submit bid", { exact: true })).toHaveCount(0);
		bdsFixture("set_gate", { closed: false });

		await page.setViewportSize({ width: 390, height: 844 });
		await expect(page.getByTestId("bds-review-task-cards")).toBeVisible();
		await expectNoHorizontalOverflow(page);
		await expectNoFrappeDialog(page);
		expect(errors.filter((e) => !/404 \(Not Found\)/.test(e)), errors.join(" | ")).toEqual([]);

		// the representative: the same review, no Submit anywhere
		await page.context().clearCookies();
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, review);
		await expect(page.getByTestId("bds-review-result")).toBeVisible();
		await expect(page.locator(".kt-next-step-headline")).toContainText("must submit this bid.");
		await expect(page.getByText("Submit bid", { exact: true })).toHaveCount(0);
	});

	test("a rejected datasheet is linked at its task and opens that row", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "review-evidence" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, `/tenders/${world.tender_reference}/bid/review`);
		const row = page.getByTestId("bds-review-task-requirements");
		await expect(row.locator(".kt-status")).toHaveText("Needs attention");
		await expect(page.getByTestId("bds-review-result")).toHaveCount(0);
		await expect(page.getByText("Submit bid", { exact: true })).toHaveCount(0);
		await expect(page.getByTestId("bds-review-declarations")).toContainText("1 rejected");
		const issue = row.locator(".bds-issue-link a");
		const label = (await issue.innerText()).replace(/^Replace the rejected /, "");
		await issue.click();
		await expect(page).toHaveURL(/\/bid\/requirements\?item=/);
		await expect(page.getByTestId("bds-response-drawer").getByRole("dialog")).toContainText(new RegExp(label, "i"));
	});

	test("an addendum change is linked at its task and Review addendum opens the documents", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "review-addendum" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, `/tenders/${world.tender_reference}/bid/review`);
		await expect(page.getByTestId("bds-review-task-documents").locator(".kt-status")).toHaveText("Needs attention");
		await expect(page.locator(".bds-issue-link a").first()).toContainText("Confirm the current ");
		await expect(page.getByText("Submit bid", { exact: true })).toHaveCount(0);
		await page.getByRole("button", { name: "Review addendum" }).click();
		await expect(page).toHaveURL(new RegExp(`/tenders/${world.tender_reference}/bid/documents$`));
	});

	test("another organisation's person is told the bid is not found", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "review" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.other_user, world.password, `/tenders/${world.tender_reference}/bid/review`);
		await expect(page.getByTestId("bds-state-bid-not-found")).toBeVisible();
		await expect(page.locator("body")).not.toContainText(world.bid_reference);
	});
});
