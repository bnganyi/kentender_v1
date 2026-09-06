import { expect, test } from "@playwright/test";

import { login, loginAsAdministrator } from "../../helpers/auth";
import {
	PASSWORD,
	PLANNER,
	collectConsoleErrors,
	expectReady,
	gotoPlanning,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * PLN-CHG-001 v1.12 Phase 6 (Slice D) — PLN-UI-13/14: the Active Plan with
 * its three-tier schedule, the cascade reforecast dialog (PLN-DES-14A), the
 * publication result (PLN-DES-13) with the technical retry, Prepare plan
 * update, and the daily CheckApproachingMilestones job proven live.
 */

type ActiveState = { plan_reference: string; plan_item_id: string; publication: string };

test.describe.configure({ mode: "serial", timeout: 180_000 });

async function gotoPlan(page: import("@playwright/test").Page, reference: string): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto(`/app/annual-procurement-plan/${reference}`, { waitUntil: "domcontentloaded" });
	await expectReady(page, "plan");
}

test.describe("PLN-UI-13/14 Active Plan, cascade and publication", () => {
	test.afterAll(() => restoreSite());

	test("the Active Plan shows PLN-DES-14 and a cascade shift moves every later forecast with one reason", async ({ page }) => {
		const state = resetFixture<ActiveState>("reset_active_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlan(page, state.plan_reference);

		await expect(page.locator('[data-testid="pln-plan-badge"]')).toHaveText("Active");
		await expect(page.locator('[data-testid="pln-active-summary-strip"] label')).toHaveText(["Plan Items", "Approved value", "Departments", "Schedule health", "Activated"]);
		await expect(page.locator('[data-testid="pln-active-health"]')).toHaveText("0 of 1 item behind baseline");
		const row = page.locator(`[data-testid="pln-active-row-${state.plan_item_id}"]`);
		await expect(row).toContainText("Digital health infrastructure package");
		await expect(row).toContainText("1 each · KES 80,000,000");
		await expect(page.locator('[data-testid="pln-active-governance"]')).toContainText("Acknowledged ·");

		// the schedule card: baseline = forecast, em-dash actuals, Shift on six rows
		await page.locator(`[data-testid="pln-active-schedule-${state.plan_item_id}"]`).click();
		const card = page.locator('[data-testid="pln-schedule-card"]');
		await expect(card).toBeVisible();
		await expect(card.locator("tbody tr")).toHaveCount(7);
		const bid = page.locator('[data-testid="pln-schedule-bid_opening"]');
		await expect(bid.locator(".pln-baseline-val")).toHaveText("22 Sep 2098");
		await expect(bid.locator(".pln-forecast-val")).toHaveText("22 Sep 2098");
		await expect(bid.locator(".pln-actual-val")).toHaveText("—");
		await expect(page.locator('[data-testid^="pln-shift-"]')).toHaveCount(6);
		await expect(page.locator('[data-testid="pln-shift-delivery_completion"]')).toHaveCount(0);

		// PLN-DES-14A — the server proposes every later row; one reason; confirm
		await page.locator('[data-testid="pln-shift-bid_opening"]').click();
		const dialog = page.locator('[data-testid="pln-shift-dialog"]');
		await expect(dialog).toBeVisible();
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Shift schedule from here — Bid opening");
		await page.locator('[data-testid="pln-shift-date"]').fill("2098-10-06");
		await expect(page.locator('[data-testid="pln-shift-row-bid_opening"]')).toContainText("6 Oct 2098");
		await expect(page.locator('[data-testid="pln-shift-row-evaluation_completion"]')).toContainText("5 Nov 2098");
		await expect(dialog.locator("tbody tr")).toHaveCount(6);
		await expect(page.locator('[data-testid="pln-shift-confirm"]')).toBeDisabled();
		await page.locator('[data-testid="pln-shift-reason"]').fill("Tender Preparation confirmed the issue date will slip two weeks pending template release.");
		await page.locator('[data-testid="pln-shift-confirm"]').click();
		await expect(dialog).toHaveCount(0, { timeout: 30_000 });

		// the interactive re-render (the card stays open): forecasts moved, baseline untouched, health counts one behind
		await expect(bid.locator(".pln-forecast-val")).toHaveText("6 Oct 2098");
		await expect(bid.locator(".pln-baseline-val")).toHaveText("22 Sep 2098");
		await expect(page.locator('[data-testid="pln-schedule-contract_signing"] .pln-forecast-val')).toHaveText("26 Nov 2098");
		await expect(page.locator('[data-testid="pln-active-health"]')).toHaveText("1 of 1 item behind baseline");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Prepare plan update opens the sole Draft successor and the predecessor stays Active", async ({ page }) => {
		const state = resetFixture<ActiveState>("reset_active_fixture");
		await login(page, PLANNER, PASSWORD);
		await gotoPlan(page, state.plan_reference);
		await page.locator('[data-testid="pln-begin-update"]').click();
		await expect(page.locator('[data-testid="pln-plan-badge"]')).toHaveText("Draft", { timeout: 30_000 });
		await expect(page.locator(".pln-quiet-ref")).toContainText("Version 2");
		await expect(page.locator('[data-testid="pln-plan-items"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="pln-begin-update"]')).toHaveCount(0);
		// the workspace still reports the Active version's schedule health
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-schedule-health"]')).toHaveText("· 0 of 1 item behind baseline");
	});

	test("the publication result reads the acknowledged attempt; a failed attempt is recovered by a technical retry", async ({ page }) => {
		const acknowledged = resetFixture<ActiveState>("reset_active_fixture");
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page, `/publication/${acknowledged.publication}`);
		await expectReady(page, "publication");
		await expect(page.locator(".kt-page-title")).toHaveText("Publication result");
		await expect(page.locator('[data-testid="pub-badge"]')).toHaveText("Acknowledged");
		await expect(page.locator('[data-testid="pub-approved-plan"]')).toContainText("FY 2098/99");
		await expect(page.locator('[data-testid="pub-approved-plan"]')).toContainText("Cabinet Secretary");
		await expect(page.locator('[data-testid="pub-result"]')).toHaveText("Acknowledged");
		await expect(page.locator('[data-testid="pub-retry"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pub-quiet-notice"]')).toContainText("without a business-role control");

		const failed = resetFixture<ActiveState>("reset_publication_failed_fixture");
		await gotoPlan(page, failed.plan_reference);
		await expect(page.locator('[data-testid="pln-publication-failed"] h3')).toHaveText("Publication was not acknowledged");
		await page.locator('[data-testid="pln-open-publication"]').click();
		await expectReady(page, "publication");
		await expect(page.locator('[data-testid="pub-badge"]')).toHaveText("Publication failed");
		// the Planner never sees the retry (§11.15)
		await expect(page.locator('[data-testid="pub-retry"]')).toHaveCount(0);

		await loginAsAdministrator(page);
		await gotoPlanning(page, `/publication/${failed.publication}`);
		await expectReady(page, "publication");
		await page.locator('[data-testid="pub-retry"]').click();
		await expect(page.locator('[data-testid="pub-badge"]')).toHaveText("Acknowledged", { timeout: 30_000 });
		await expect(page.locator('[data-testid="pub-result"]')).toHaveText("Acknowledged");
		await expect(page.locator('[data-testid="pub-failed"]')).toHaveCount(0);
	});

	test("the daily CheckApproachingMilestones job raises once per milestone per day (§8.3)", async ({ page }) => {
		resetFixture<ActiveState>("reset_active_fixture");
		const result = resetFixture<{ raised: string[][]; raised_again: string[][]; notifications: number }>("run_milestone_check", { today: "2098-08-25" });
		expect(result.raised.some(([, milestone]) => milestone === "invitation")).toBe(true);
		// the second run of the same day considers the same milestone but raises
		// no second notification (PLN-AC-130): exactly one log row for the Planner
		expect(result.raised_again).toEqual(result.raised);
		expect(result.notifications).toBe(1);
		// and the job mutates nothing on the Active plan
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-schedule-health"]')).toHaveText("· 0 of 1 item behind baseline");
	});
});
