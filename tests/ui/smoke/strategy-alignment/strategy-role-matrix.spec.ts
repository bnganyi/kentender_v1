import { execSync } from "node:child_process";
import path from "node:path";

import { test, expect } from "@playwright/test";
import {
	loginAsStrategyManager,
	loginAsStrategyOfficer,
	loginAsStrategyViewer,
	loginAsStrategyViewerOtherPe,
} from "../../helpers/auth";

/**
 * STR-SUP-005 wave 2 — Strategy role Desk evidence (not full §12 matrix).
 * Viewer: Performance RO; create-plan denied.
 * Officer: Performance export hidden; Manager: kt-str-perf-export visible.
 * OTHER-PE Viewer: cannot live-load MOH Performance.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const STRATEGY_PLAN_CODE = "MOH-SP-0001";

function seedStrategyRoleFixtures(): void {
	try {
		execSync("redis-cli -p 11000 FLUSHDB", { stdio: "pipe" });
	} catch {
		/* ignore */
	}
	execSync(
		`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ` +
			"kentender_strategy.seeds.works_master_strategy_hierarchy.upsert_works_master_strategy_hierarchy",
		{ stdio: "pipe", timeout: 180_000 },
	);
	execSync(
		`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ` +
			"kentender_strategy.seeds.strategy_role_users.upsert_strategy_role_users",
		{ stdio: "pipe", timeout: 120_000 },
	);
	execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} clear-cache`, {
		stdio: "pipe",
		timeout: 60_000,
	});
}

test.describe.configure({ mode: "serial" });

test.describe("Strategy role matrix (STR-SUP-005 wave)", () => {
	test.beforeAll(() => {
		seedStrategyRoleFixtures();
	});

	test("Viewer opens Strategy Performance without create-plan (STR-AC-024 sample)", async ({
		page,
	}) => {
		test.setTimeout(120_000);
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsStrategyViewer(page);
		await page.goto("/desk/strategy-performance", { waitUntil: "domcontentloaded" });
		await expect(
			page.locator('[data-testid="kt-str-performance"][data-kt-str-live="1"]'),
		).toBeVisible({ timeout: 45_000 });
		await expect(page.getByRole("heading", { name: "Strategy Performance" })).toBeVisible();
		await expect(page.locator('[data-kt-str-action="create-plan"]')).toHaveCount(0);
		await expect(page.getByTestId("kt-str-create-plan")).toHaveCount(0);
	});

	test("Viewer cannot use create-plan surface (STR-AC-024)", async ({ page }) => {
		test.setTimeout(120_000);
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsStrategyViewer(page);
		await page.goto("/desk/strategy-plan-create", { waitUntil: "domcontentloaded" });
		// Page roles are Officer/Manager only — Viewer must not get a live create surface.
		await expect(page.getByTestId("kt-str-create-plan")).toHaveCount(0, { timeout: 20_000 });
		await expect(page.getByTestId("kt-str-create-plan-submit")).toHaveCount(0);
		await page.waitForFunction(() => !!(window as any).frappe?.call, null, {
			timeout: 30_000,
		});
		const ctx = await page.evaluate(async () => {
			try {
				const r = await (window as any).frappe.call({
					method: "kentender_strategy.api.strategy_api.get_create_plan_context",
				});
				return { ok: true, message: r.message };
			} catch (e: any) {
				return { ok: false, error: String(e?.message || e) };
			}
		});
		expect(ctx.ok).toBeFalsy();
	});

	test("Manager opens Strategy Alignment portfolio", async ({ page }) => {
		test.setTimeout(120_000);
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsStrategyManager(page);
		await page.goto("/desk/strategy-alignment", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-str-portfolio")).toBeVisible({ timeout: 45_000 });
		await expect(page.locator('[data-kt-str-live="1"]').first()).toBeVisible({
			timeout: 30_000,
		});
	});

	test("Officer hides Performance export; Manager shows kt-str-perf-export", async ({
		page,
	}) => {
		test.setTimeout(180_000);
		await page.setViewportSize({ width: 1440, height: 1000 });

		await loginAsStrategyOfficer(page);
		await page.goto("/desk/strategy-performance", { waitUntil: "domcontentloaded" });
		await expect(
			page.locator('[data-testid="kt-str-performance"][data-kt-str-live="1"]'),
		).toBeVisible({ timeout: 45_000 });
		const officerExport = page.getByTestId("kt-str-perf-export");
		await expect(officerExport).toBeHidden();

		await loginAsStrategyManager(page);
		await page.goto("/desk/strategy-performance", { waitUntil: "domcontentloaded" });
		await expect(
			page.locator('[data-testid="kt-str-performance"][data-kt-str-live="1"]'),
		).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId("kt-str-perf-export")).toBeVisible();
	});

	test("OTHER-PE Viewer cannot live-load MOH Performance (STR-AC-018/030 UI)", async ({
		page,
	}) => {
		test.setTimeout(120_000);
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsStrategyViewerOtherPe(page);
		await page.goto("/desk/strategy-performance", { waitUntil: "domcontentloaded" });
		await page.waitForFunction(() => !!(window as any).frappe?.call, null, {
			timeout: 30_000,
		});
		const api = await page.evaluate(async (planCode) => {
			try {
				const r = await (window as any).frappe.call({
					method: "kentender_strategy.api.strategy_api.get_strategy_performance",
					args: { plan_code: planCode },
				});
				return { ok: true, message: r.message };
			} catch (e: any) {
				const msg =
					e?.message ||
					e?._server_messages ||
					(typeof e === "string" ? e : JSON.stringify(e));
				return { ok: false, error: String(msg) };
			}
		}, STRATEGY_PLAN_CODE);
		expect(api.ok).toBeFalsy();
		expect(String(api.error || "")).toMatch(/not permitted|Permission|procuring entity/i);

		const liveMoh = page.locator(
			`[data-testid="kt-str-performance"][data-kt-str-live="1"]:has-text("${STRATEGY_PLAN_CODE}")`,
		);
		await expect(liveMoh).toHaveCount(0);
	});
});
