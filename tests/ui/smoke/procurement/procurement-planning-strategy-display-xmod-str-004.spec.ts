/**
 * XMOD-STR-004 — Planning Desk shows Demand Strategy Reference as Name (CODE).
 * Live against WORKS master via Package Wizard Step 1 (PP4 entry point).
 */
import { execSync } from "node:child_process";
import path from "node:path";

import { expect, test } from "@playwright/test";
import { loginAsProcurementPlanner } from "../../helpers/auth";

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const PLAN_CODE = "PLAN-MOH-2026";
const WORKS_DEMAND_TITLE = "District Hospital Renovation Works";
const TARGET_CODE = "MOH-TGT-AVAIL-2028";

function resetWorksMasterSeedIncludedInPlan(): void {
	// Best-effort drain when RQ is overloaded (common after dense Playwright runs).
	try {
		execSync("redis-cli -p 11000 FLUSHDB", { stdio: "pipe" });
	} catch {
		/* ignore */
	}
	let lastErr: unknown;
	for (let attempt = 1; attempt <= 3; attempt += 1) {
		try {
			execSync(
				"bench --site kentender.midas.com execute " +
					"kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master.seed_procurement_planning_works_master " +
					'--kwargs \'{"checkpoint": "INCLUDED_IN_PLAN", "force_reset": True}\'',
				{ cwd: BENCH_ROOT, stdio: "pipe", encoding: "utf8" },
			);
			return;
		} catch (e) {
			lastErr = e;
			execSync("sleep 2");
		}
	}
	throw lastErr;
}

async function tryLoginAsPlanner(page: import("@playwright/test").Page): Promise<boolean> {
	try {
		await loginAsProcurementPlanner(page);
		return true;
	} catch (e) {
		const msg = e instanceof Error ? e.message : String(e);
		if (msg.includes("Invalid Login")) {
			return false;
		}
		throw e;
	}
}

test.describe("XMOD-STR-004 Planning strategy display", () => {
	test.beforeAll(() => {
		resetWorksMasterSeedIncludedInPlan();
	});

	test.beforeEach(async ({ page }) => {
		const loggedIn = await tryLoginAsPlanner(page);
		test.skip(!loggedIn, "Procurement Planner (planner@moh.test) not configured on target site");
	});

	test("wizard demand card shows Performance Target Name (CODE)", async ({ page }) => {
		await page.goto(`/desk/procurement-planning?plan=${PLAN_CODE}&queue=draft_packages`, {
			waitUntil: "domcontentloaded",
		});

		const workbenchFrame = page.frameLocator('[data-testid="pp4-workbench-design-iframe"]');
		const placeholderRow = workbenchFrame.locator("tr[data-inclusion-code]").first();
		await expect(placeholderRow).toBeVisible({ timeout: 30_000 });
		await expect(placeholderRow).toContainText(WORKS_DEMAND_TITLE);
		await placeholderRow.click();
		await page.waitForURL(/create-package-wizard/, { timeout: 15_000 });

		const demandCard = page.locator('[data-testid="kt-pw-demand-card"]').first();
		await expect(demandCard).toBeVisible({ timeout: 20_000 });
		await expect(demandCard.locator('[data-testid="kt-pw-demand-title"]')).toContainText(
			WORKS_DEMAND_TITLE,
		);

		const strategy = demandCard.locator('[data-testid="kt-pw-demand-strategy"]');
		await expect(strategy).toBeVisible({ timeout: 10_000 });
		await expect(strategy).toContainText(TARGET_CODE);
		const text = (await strategy.innerText()).trim();
		expect(text).toMatch(/\(.+\)/);
		expect(text).not.toMatch(/^[a-z0-9]{8,14}$/);
	});
});
