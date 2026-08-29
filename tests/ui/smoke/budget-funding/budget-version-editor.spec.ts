import { execSync } from "node:child_process";
import path from "node:path";

import { test, expect } from "@playwright/test";
import { loginAsBudgetOtherEntity, loginAsBudgetOtherEntityViewer } from "../../helpers/auth";

/**
 * BUD-CHG-001 v1.2 — BUD-UI-02 Budget Version editor (pre-creation form +
 * tabbed Draft), covering the baseline "register a new Budget" flow
 * end-to-end (verified live in the browser before writing this spec).
 *
 * Uses PE-CGKIS's *current* Financial Year (the same auto-resolved "today"
 * FY the workspace/pre-creation form both use — there is no PE/FY selector,
 * see budget_contracts._current_financial_year), reset fresh before this
 * file's own tests via kentender_budget.seeds.playwright_ui_fixtures.
 * reset_editor_create_fixture — owns the whole PE-CGKIS/current-FY slot for
 * this file alone (BUD-BR-001: one Budget per PE+FY), which is also why the
 * "No baseline" / Register-visibility assertions live here rather than in
 * budget-workspace.spec.ts.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURE_FILE = path.resolve(__dirname, "fixtures/budget-approval-evidence.png");

function resetEditorCreateFixture(): void {
	execSync(
		`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ` +
			"kentender_budget.seeds.playwright_ui_fixtures.reset_editor_create_fixture",
		{ stdio: "pipe", timeout: 120_000 },
	);
}

test.describe.configure({ mode: "serial" });

test.describe("Budget Version editor (BUD-UI-02)", () => {
	test.beforeAll(() => {
		resetEditorCreateFixture();
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
	});

	test("No baseline empty state offers Register for a scoped Officer", async ({ page }) => {
		await loginAsBudgetOtherEntity(page);
		await page.goto("/app/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("budget-no-baseline")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("budget-no-baseline")).toContainText(
			"No approved procurement budget is registered for",
		);
		await expect(page.getByTestId("budget-register-btn")).toBeVisible();
	});

	test("No baseline empty state hides Register for a Viewer", async ({ page }) => {
		await loginAsBudgetOtherEntityViewer(page);
		await page.goto("/app/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("budget-no-baseline")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("budget-register-btn")).toHaveCount(0);
	});

	test("Officer registers a Budget, adds a line and submits for review", async ({ page }) => {
		await loginAsBudgetOtherEntity(page);
		await page.goto("/app/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("budget-register-btn")).toBeVisible({ timeout: 30_000 });
		await page.getByTestId("budget-register-btn").click();
		await expect(page).toHaveURL(/\/budget-funding\/new$/, { timeout: 15_000 });

		await page
			.locator(".kt-field", { hasText: "Approval reference" })
			.locator("input")
			.fill("CGK-FIN-BUD-PW-CREATE-01");
		await page.locator(".kt-field", { hasText: "Approval date" }).locator("input").fill("2026-08-01");
		await page
			.locator(".kt-field", { hasText: "Authorised total" })
			.locator("input")
			.fill("10000000");

		await page.getByRole("button", { name: "Upload" }).click();
		const fileChooserPromise = page.waitForEvent("filechooser");
		await page.getByRole("button", { name: "My Device" }).click();
		const fileChooser = await fileChooserPromise;
		await fileChooser.setFiles(FIXTURE_FILE);
		await expect(page.getByRole("dialog").getByText("budget-approval-evidence.png")).toBeVisible({
			timeout: 15_000,
		});
		await page.getByRole("dialog").getByRole("button", { name: "Upload" }).click();
		await expect(page.getByRole("dialog")).toHaveCount(0, { timeout: 15_000 });

		await page.getByTestId("bud-editor-save-btn").click();
		await expect(page).toHaveURL(/\/budget-funding\/CGKIS-BUD-[\d-]+\/version\/1\/edit$/, { timeout: 20_000 });
		await expect(page.getByText("Draft saved")).toBeVisible({ timeout: 15_000 });

		await page.getByTestId("bud-editor-tab-lines").click();
		await expect(page.getByTestId("bud-editor-add-line-btn")).toBeVisible({ timeout: 15_000 });
		await page.getByTestId("bud-editor-add-line-btn").click();

		const row = page.getByTestId("bud-editor-lines-table").locator("tbody tr").first();
		// The line-title field is a plain <input> with no `type` attribute
		// (see BudgetVersionEditorScreen.vue) — it's the first <input> in DOM
		// order within the row, before the type="number" amount field.
		await row.locator("input").first().fill("Playwright test line");
		await row.locator("input[type=number]").fill("10000000");
		// Funding source has a real bound value the moment the row is added
		// (only one catalogue entry exists) — assert it, not just fill it.
		await expect(row.locator("select").nth(1)).toHaveValue(/.+/);

		await page.getByTestId("bud-editor-save-btn").click();
		await expect(page.getByText("Draft saved")).toBeVisible({ timeout: 15_000 });
		// Budget Line total now matches the authorised total (10,000,000);
		// Difference reads back to 0 once the two balance.
		await expect(page.getByText("Budget Line total").locator("..")).toContainText("KES 10,000,000");
		await expect(page.getByText("Difference").locator("..")).toContainText("KES 0");

		await page.getByTestId("bud-editor-submit-btn").click();
		await expect(page.getByText("Submitted for review")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByText("Submitted for approval")).toBeVisible();
		await expect(page.getByTestId("bud-editor-save-btn")).toHaveCount(0);
	});
});
