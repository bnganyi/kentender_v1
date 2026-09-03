import { execSync } from "node:child_process";
import path from "node:path";

import { test, expect } from "@playwright/test";
import { loginAsBudgetViewer } from "../../helpers/auth";

/**
 * BUD-CHG-001 v1.2 — BUD-UI-05 Budget Line detail
 * (/app/budget-funding/line/{budget_line_id}). BUD-DES-06 (empty state) is
 * exercised against the canonical MOH-BL-HWD-2027 line (no reservations);
 * BUD-DES-06A (reservations table) against the isolated
 * BUD-SC-FIN-SINGLE-L1 Finance profile (see kentender_budget.seeds.
 * kentender_mvp_v1_portfolio.upsert_isolated_finance_profiles — reset here
 * so its 80m reservation precondition is always present).
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";

function seedIsolatedFinanceProfiles(): void {
	execSync(
		`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ` +
			"kentender_budget.seeds.kentender_mvp_v1_portfolio.upsert_isolated_finance_profiles",
		{ stdio: "pipe", timeout: 120_000 },
	);
}

test.describe.configure({ mode: "serial" });

test.describe("Budget Line detail (BUD-UI-05)", () => {
	test.beforeAll(() => {
		seedIsolatedFinanceProfiles();
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsBudgetViewer(page);
	});

	test("BUD-DES-06 empty state for a line with no active reservations", async ({ page }) => {
		await page.goto("/app/budget-funding/line/MOH-BL-HWD-2027", { waitUntil: "domcontentloaded" });

		await expect(page.getByTestId("bud-line-header")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("bud-line-header")).toContainText("Digital health workforce development");
		const positions = page.getByTestId("bud-line-position-cards");
		await expect(positions).toContainText("KES 60,000,000"); // Approved
		await expect(page.getByTestId("bud-line-reservations-empty")).toBeVisible();
		await expect(page.getByText("No active reservations")).toBeVisible();
	});

	test("BUD-DES-06A reservations table for a line with an active reservation", async ({ page }) => {
		await page.goto("/app/budget-funding/line/BUD-SC-FIN-SINGLE-L1", { waitUntil: "domcontentloaded" });

		await expect(page.getByTestId("bud-line-header")).toBeVisible({ timeout: 30_000 });
		const positions = page.getByTestId("bud-line-position-cards");
		await expect(positions).toContainText("KES 100,000,000"); // Approved
		await expect(positions).toContainText("KES 80,000,000"); // Reserved
		await expect(positions).toContainText("KES 20,000,000"); // Available

		const table = page.getByTestId("bud-line-reservations-table");
		await expect(table).toBeVisible();
		await expect(table).toContainText("KES 80,000,000");
		await expect(table).toContainText("Active");
		await expect(table.getByRole("link", { name: "View Plan Item" })).toBeVisible();
	});

	test("Unknown Budget Line code shows the not-found state", async ({ page }) => {
		await page.goto("/app/budget-funding/line/NO-SUCH-LINE-XYZ", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("bud-line-not-found")).toBeVisible({ timeout: 30_000 });
	});
});
