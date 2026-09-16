import { execSync } from "node:child_process";
import path from "node:path";
import { test, expect, Page } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { collectPageErrors } from "../../helpers/designFidelity";

/**
 * CFG-CHG-002 v0.11 §10.3/§11.3 (C02) / CFG11-CHG-003–004 (tracker
 * CFG11-302) — behaviour the design-fidelity gate does not cover: the
 * cross-year replacement notice naming the exact affected year, an expired
 * intake reading as Closed without any scheduled job running inside the
 * test, and a stale control token recovering through "Review latest
 * settings" rather than a raw error.
 *
 * The replacement scenario reads the live canonical Fiscal Years (2027/28
 * open, 2026/27 closed) and stops at the notice — nothing is submitted, so
 * the platform's one canonical open year is never touched here (every other
 * module's own fixtures depend on it staying open). Expiry and the stale
 * write use `reset_fiscal_year_edge_cases`'s isolated, far-future years
 * instead, and exercise the **disposal-plan** activity: intake is
 * one-year-at-a-time per module key, so driving `needs` on a fixture year
 * would close the canonical year's own flag.
 */
const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";

interface EdgeCaseFixture {
	expired_fiscal_year: string;
	expired_label: string;
	stale_fiscal_year: string;
	stale_label: string;
}

function resetEdgeCases(): EdgeCaseFixture {
	const output = execSync(
		`cd "${BENCH_ROOT}" && bench --site ${SITE} execute kentender_core.seeds.playwright_ui_fixtures.reset_fiscal_year_edge_cases`,
		{ stdio: "pipe", timeout: 120_000, encoding: "utf-8" }
	);
	const line = output.trim().split("\n").pop() || "";
	return JSON.parse(line) as EdgeCaseFixture;
}

async function openYear(page: Page, fiscalYear: string, ready: string) {
	await page.goto(`/app/system-setup#fiscal-years/year/${fiscalYear}`, { waitUntil: "domcontentloaded" });
	await page.waitForSelector(ready, { timeout: 20_000 });
}

test.describe("System setup — Financial years behaviour", () => {
	test("opening a closed year's needs intake shows the cross-year replacement notice naming the currently open year; nothing is submitted", async ({ page }) => {
		const errors = collectPageErrors(page);
		await loginAsAdministrator(page);
		await openYear(page, "2026-2027", '[data-testid="kt-setup-fy-detail-card"]');

		await page.click('[data-testid="kt-fy-open-needs"]');
		await page.waitForSelector('[data-testid="kt-fy-intake-replaces"]');
		await expect(page.locator('[data-testid="kt-fy-intake-replaces"]')).toContainText("This will close FY 2027/28");
		await expect(page.locator('[data-testid="kt-fy-intake-replaces"]')).toContainText(
			"Departmental plan and Disposal plan submissions will stay as they are."
		);
		await page.click('[data-testid="kt-fy-intake"] .kt-btn-secondary');
		await expect(page.locator('[data-testid="kt-fy-intake"]')).toHaveCount(0);

		// Refused before any submit: reloading shows the canonical year untouched.
		await page.reload({ waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="kt-setup-fy-detail-card"]');
		await expect(page.locator('[data-testid="kt-fy-activity-needs"]')).toContainText("Closed");
		expect(errors, "console errors").toEqual([]);
	});

	test("an intake whose closing instant has passed reads as Closed with no closing date shown, without any scheduled job running", async ({ page }) => {
		const fixture = resetEdgeCases();
		const errors = collectPageErrors(page);
		await loginAsAdministrator(page);
		await openYear(page, fixture.expired_fiscal_year, '[data-testid="kt-setup-fy-detail-card"]');

		const row = page.locator('[data-testid="kt-fy-activity-disposal_plan"]');
		await expect(row).toContainText("Closed");
		await expect(row).toContainText("Not set");
		await expect(page.locator('[data-testid="kt-fy-open-disposal_plan"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-fy-close-disposal_plan"]')).toHaveCount(0);
		expect(errors, "console errors").toEqual([]);
	});

	test("a stale control token shows the recoverable notice, and Review latest settings loads the concurrent change", async ({ page, context }) => {
		const fixture = resetEdgeCases();
		const errors = collectPageErrors(page);
		await loginAsAdministrator(page);
		await openYear(page, fixture.stale_fiscal_year, '[data-testid="kt-setup-fy-detail-card"]');

		// Tab A opens the deadline form and holds it — its `expected_version`
		// is now the pre-concurrent-write stamp.
		await page.click('[data-testid="kt-fy-deadline-disposal_plan"]');
		await page.waitForSelector('[data-testid="kt-fy-intake-closes"]');

		// Tab B (same session) makes a real, independent change first.
		const page2 = await context.newPage();
		await openYear(page2, fixture.stale_fiscal_year, '[data-testid="kt-setup-fy-detail-card"]');
		await page2.click('[data-testid="kt-fy-deadline-disposal_plan"]');
		await page2.waitForSelector('[data-testid="kt-fy-intake-closes"]');
		await page2.fill('[data-testid="kt-fy-intake-closes"]', "2099-08-15T12:00");
		await page2.fill('[data-testid="kt-fy-intake-reason"]', "Tab B: the winning concurrent change.");
		await page2.click('[data-testid="kt-fy-intake-confirm"]');
		await expect(page2.locator('[data-testid="kt-fy-intake"]')).toHaveCount(0);
		await page2.close();

		// Tab A submits next, still holding the stale stamp.
		await page.fill('[data-testid="kt-fy-intake-reason"]', "Tab A: the losing concurrent change.");
		await page.click('[data-testid="kt-fy-intake-confirm"]');

		const stale = page.locator('[data-testid="kt-fy-intake-stale"]');
		await expect(stale).toBeVisible({ timeout: 10_000 });
		await expect(stale).toContainText("These submission settings have changed since you opened them.");
		await expect(page.locator('[data-testid="kt-fy-intake"] .kt-inline-error')).toHaveCount(0);

		await stale.locator("a").click();
		await expect(page.locator('[data-testid="kt-fy-intake"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="kt-fy-activity-disposal_plan"]')).toContainText("15 Aug 2099");

		// The deliberate refusal is the one expected console line: Frappe echoes
		// the server's ConfigurationError traceback for the 417 in developer
		// mode (same allowance as the C01-conflict fidelity test).
		expect(
			errors.filter((e) => !e.includes("This record changed after you opened it") && !/status of 417/.test(e)),
			"console errors"
		).toEqual([]);
	});
});
