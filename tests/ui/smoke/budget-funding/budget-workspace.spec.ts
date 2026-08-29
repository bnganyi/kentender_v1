import { execSync } from "node:child_process";
import path from "node:path";

import { test, expect } from "@playwright/test";
import { loginAsBudgetOfficer, loginAsBusinessApprover } from "../../helpers/auth";

/**
 * The "No baseline" / Register-button-visibility states for PE-CGKIS's
 * current-FY slot are exercised in budget-version-editor.spec.ts instead of
 * here — that spec owns the full lifecycle of PE-CGKIS's current-FY Budget
 * (reset -> register -> submit), and running that reset from two files
 * would race across parallel workers on the same (PE, FY) slot (BUD-BR-001:
 * one Budget per PE+FY).
 */

/**
 * BUD-CHG-001 v1.2 — BUD-UI-01 Budget & Funding workspace (/app/budget-funding).
 *
 * get_budget_workspace() auto-resolves "current" Financial Year from real
 * nowdate() — there is no PE/FY selector (documented stopgap, see
 * budget_contracts._current_financial_year). The canonical MOH-BUD-2027-001
 * baseline only renders here while wall-clock time falls inside FY-2027-2028
 * (Jul 2027 - Jun 2028), so this spec exercises the Active state through a
 * dedicated Playwright fixture (BUD-PW-CURRENT) that is always positioned in
 * whatever Financial Year covers "today" — see
 * kentender_budget.seeds.playwright_ui_fixtures.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";

function seedCurrentBaseline(): void {
	execSync(
		`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ` +
			"kentender_budget.seeds.playwright_ui_fixtures.upsert_playwright_current_baseline",
		{ stdio: "pipe", timeout: 120_000 },
	);
}

test.describe.configure({ mode: "serial" });

test.describe("Budget & Funding workspace (BUD-UI-01)", () => {
	test.beforeAll(() => {
		seedCurrentBaseline();
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
	});

	test("Active state shows the current-FY baseline, positions and lines preview", async ({ page }) => {
		await loginAsBudgetOfficer(page);
		await page.goto("/app/budget-funding", { waitUntil: "domcontentloaded" });

		await expect(page.getByRole("heading", { name: "Budget & Funding", exact: true })).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.getByTestId("budget-summary-card")).toBeVisible({ timeout: 20_000 });
		await expect(page.getByTestId("budget-summary-card")).toContainText("Ministry of Health procurement budget");
		await expect(page.getByTestId("budget-summary-card")).toContainText("Active");
		await expect(page.getByTestId("budget-summary-card")).toContainText("BUD-PW-CURRENT");

		const positions = page.getByTestId("budget-position-cards");
		await expect(positions).toContainText("KES 50,000,000"); // Approved
		await expect(positions).toContainText("KES 0"); // Reserved / Committed

		const linesPreview = page.getByTestId("budget-lines-preview");
		await expect(linesPreview).toContainText("Playwright current-baseline test line");
		await expect(linesPreview).toContainText("BUD-PW-CURRENT-L1");

		await page.getByTestId("budget-view-btn").click();
		await expect(page).toHaveURL(/\/budget-funding\/BUD-PW-CURRENT$/, { timeout: 15_000 });
		await expect(page.getByTestId("budget-detail-header")).toBeVisible({ timeout: 20_000 });
	});

	test("workspace lines preview View link opens Budget Line detail", async ({ page }) => {
		await loginAsBudgetOfficer(page);
		await page.goto("/app/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("budget-lines-preview")).toBeVisible({ timeout: 30_000 });
		await page.getByTestId("budget-lines-preview").getByRole("link", { name: "View" }).click();
		await expect(page).toHaveURL(/\/budget-funding\/line\/BUD-PW-CURRENT-L1$/, { timeout: 15_000 });
		await expect(page.getByTestId("bud-line-header")).toBeVisible({ timeout: 20_000 });
	});

	test("Forbidden state for a user with no Budget role", async ({ page }) => {
		await loginAsBusinessApprover(page);
		await page.goto("/app/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(
			page.getByText("You do not have access to this Budget & Funding context."),
		).toBeVisible({ timeout: 30_000 });
	});
});
