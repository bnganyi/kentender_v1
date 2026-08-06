import { test, expect, Page } from "@playwright/test";
import { execSync } from "node:child_process";
import path from "node:path";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * XMOD-STR-001 — Budget Line primary Strategy Reference validate-on-save (Desk E2E).
 * Fixture: Draft MOH-BUD-0004 / MOH-BL-0006 (intentionally missing primary target).
 */

test.describe.configure({ mode: "serial" });

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";

async function openDraftLineDrawer(page: Page) {
	await page.goto("/desk/budget-lines/MOH-BUD-0004", { waitUntil: "domcontentloaded" });
	const root = page
		.locator('[data-testid="kt-bud-lines"][data-kt-bud-live="1"]')
		.filter({ visible: true });
	await expect(root).toBeVisible({ timeout: 45_000 });
	const row = root.locator('tr[data-line-code="MOH-BL-0006"]');
	await expect(row).toBeVisible({ timeout: 20_000 });
	await row.getByTestId("kt-bud-line-action").click();
	const drawer = root.getByTestId("kt-bud-line-drawer");
	await expect(drawer).toBeVisible({ timeout: 15_000 });
	await expect(drawer).toHaveAttribute("data-kt-bud-line-readonly", "0");
	await expect(root.getByTestId("kt-bud-line-save")).toBeVisible();
	return { root, drawer };
}

test.describe("Budget line strategy validate (XMOD-STR-001)", () => {
	test.beforeAll(() => {
		try {
			execSync(
				`cd "${BENCH_ROOT}" && bench --site ${SITE} execute kentender_budget.seeds.moh_mvp_v1_portfolio.upsert_moh_mvp_v1_portfolio`,
				{ stdio: "pipe", timeout: 120_000 },
			);
		} catch {
			/* portfolio may already be present */
		}
		try {
			execSync(
				`cd "${BENCH_ROOT}" && bench --site ${SITE} execute kentender_strategy.seeds.works_master_strategy_hierarchy.upsert_works_master_strategy_hierarchy`,
				{ stdio: "pipe", timeout: 120_000 },
			);
		} catch {
			/* strategy seed may already be present */
		}
		execSync(
			`cd "${BENCH_ROOT}" && bench --site ${SITE} execute kentender_budget.seeds.moh_mvp_v1_portfolio.clear_moh_bl_0006_primary_for_e2e`,
			{ stdio: "pipe", timeout: 60_000 },
		);
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("empty primary shows field error; Active select saves authoritative primary", async ({
		page,
	}) => {
		const { root, drawer } = await openDraftLineDrawer(page);

		const primary = drawer.getByTestId("kt-bud-line-primary-target");
		await expect(primary).toBeVisible();
		await expect(primary.locator("option").first()).toContainText(/Select Active target/i);

		// Picker contract: Active options present (MOH-TGT-*).
		const optionValues = await primary.locator("option").evaluateAll((opts) =>
			opts.map((o) => (o as HTMLOptionElement).value).filter(Boolean),
		);
		expect(optionValues.some((v) => /^MOH-TGT-/.test(v))).toBeTruthy();

		// Required empty → inline error surface.
		await primary.selectOption({ value: "" });
		await root.getByTestId("kt-bud-line-save").click();
		const err = drawer.getByTestId("kt-bud-line-primary-target-error");
		await expect(err).toBeVisible({ timeout: 10_000 });
		await expect(err).toContainText(/Primary strategic target is required/i);

		// Active save.
		const activeCode =
			optionValues.find((v) => v === "MOH-TGT-AVAIL-2028") ||
			optionValues.find((v) => v === "MOH-TGT-SKILLS-2029") ||
			optionValues[0];
		expect(activeCode).toBeTruthy();
		await primary.selectOption(activeCode!);
		await expect(drawer.locator('[data-kt-bud-line-field="primary_target_code"]')).toHaveText(
			activeCode!,
		);

		await root.getByTestId("kt-bud-line-save").click();
		await expect(drawer).toBeHidden({ timeout: 20_000 });

		// Re-open: authoritative code displayed (not raw hash-only).
		await root
			.locator('tr[data-line-code="MOH-BL-0006"] [data-testid="kt-bud-line-action"]')
			.click();
		await expect(drawer).toBeVisible({ timeout: 15_000 });
		await expect(drawer.locator('[data-kt-bud-line-field="primary_target_code"]')).toHaveText(
			activeCode!,
		);
		await expect(drawer.getByTestId("kt-bud-line-primary-target")).toHaveValue(activeCode!);
		const selectedLabel = await drawer
			.getByTestId("kt-bud-line-primary-target")
			.locator("option:checked")
			.textContent();
		expect(selectedLabel || "").not.toMatch(/^[a-z0-9]{8,12}$/);
		expect(selectedLabel || "").toMatch(/\S/);
	});
});
