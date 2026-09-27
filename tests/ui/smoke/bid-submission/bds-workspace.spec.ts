import { expect, test } from "@playwright/test";

import { collectPortalConsoleErrors, expectNoFrappeDialog, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { bdsFixture, restoreBdsWorld } from "./bdsWorld";

/**
 * BDS-CHG-001 v0.8 §10.7 (plan Phase 11, slice 11.6) — Your bid, as the
 * representative (David) and the signatory (Mary) of Afya (Test), on the
 * Tenders test Tender. This dev site keeps the production switch off, so the
 * page names that above the tasks and offers no Submit — the real gate state
 * (BDS-DES-06-GATE), not a forced one.
 */
type World = { tender_reference: string; bid_reference: string; password: string; representative: string; signatory: string; other_user: string };

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BDS-DES-06 Your bid", () => {
	test.afterAll(() => restoreBdsWorld());

	test("an unfinished bid continues at its first open task; reached from the overview and back", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "started" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, `/tenders/${world.tender_reference}`);
		await page.getByTestId("bds-overview-action").click();
		await expect(page).toHaveURL(new RegExp(`/tenders/${world.tender_reference}/bid$`));
		const screen = page.getByTestId("bds-workspace");
		await expect(screen.locator("h1")).toHaveText("Your bid");
		await expect(page.getByTestId("bds-workspace-refs")).toContainText(`${world.tender_reference} · ${world.bid_reference} · Draft Version`);
		await expect(page.getByTestId("bds-workspace-action")).toHaveText("Continue bid");
		await expect(screen.locator(".kt-region h2")).toHaveText(["Deadline", "Current notices", "Bid tasks"]);
		await expect(page.getByTestId("bds-workspace-deadline")).toContainText(/Closes in/);
		await expect(page.locator('[data-testid^="bds-task-"]')).toHaveCount(5);
		await expect(page.getByTestId("bds-task-company")).toContainText("Continue");
		await expect(page.locator('[data-kt="next-step"]')).toBeVisible();
		await expect(page.locator("body")).not.toContainText(/Submit bid/);
		await page.goBack({ waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("bds-tender-overview")).toBeVisible();
		await page.goForward({ waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("bds-workspace")).toBeVisible();
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-workspace-action")).toHaveText("Continue bid");
		await expectNoFrappeDialog(page);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("a ready bid: David waits for Mary, Mary is told to submit; the closed switch is named with the deadline and support", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "ready" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, `/tenders/${world.tender_reference}/bid`);
		await expect(page.getByTestId("bds-workspace-action")).toHaveText("Review bid");
		await expect(page.getByTestId("bds-task-review").getByRole("link", { name: "Review bid" })).toBeVisible();
		await expect(page.getByTestId("bds-workspace-saved")).toContainText(/^Saved .* by David Ouma\.$/);
		const notice = page.getByTestId("bds-workspace-availability");
		await expect(notice).toContainText("Electronic bid submission is not available yet");
		await expect(notice).toContainText("Your bid remains saved and has not been submitted.");
		await expect(page.locator('[data-kt="next-step"]')).toContainText("Mary Wanjiku");

		await loginToPortal(page, world.signatory, world.password, `/tenders/${world.tender_reference}/bid`);
		await expect(page.getByTestId("bds-workspace-action")).toHaveText("Review bid");
		await expect(page.getByTestId("bds-workspace-availability")).toBeVisible();
		await expect(page.locator("body")).not.toContainText(/Submit bid/);
		await page.setViewportSize({ width: 390, height: 844 });
		await expect(page.getByTestId("bds-tasks-cards")).toBeVisible();
		await expectNoHorizontalOverflow(page);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("after the deadline the Draft is read-only with the trusted time and Back to My bids", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "ready" });
		bdsFixture("set_instant", { instant: "2027-06-05 11:00:01" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, `/tenders/${world.tender_reference}/bid`);
		await expect(page.getByTestId("bds-workspace-deadline")).toContainText("Trusted server time");
		await expect(page.getByTestId("bds-workspace-action")).toHaveText("Back to My bids");
		await expect(page.getByTestId("bds-workspace-availability")).toHaveCount(0);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("another organisation's person is told the bid is not found", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "ready" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.other_user, world.password, `/tenders/${world.tender_reference}/bid`);
		await expect(page.getByTestId("bds-state-bid-not-found")).toBeVisible();
		await expect(page.locator("body")).not.toContainText(world.bid_reference);
		expect(errors.filter((e) => !/404 \(Not Found\)/.test(e)), errors.join(" | ")).toEqual([]);
	});
});
