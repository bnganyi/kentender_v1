import { execSync } from "node:child_process";
import path from "node:path";

import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { collectConsoleErrors, expectReady, gotoPlanning } from "./helpers";

/**
 * PLN-CHG-001 v1.12 Phase 7/8 — the §14 persona pass on the seeded
 * KENTENDER_MVP_V1 world (FY 2027/28): the exact personas KT-STD-001 §8.3
 * and §14.2 name, logged in for real, reading the integrated baseline the
 * seed built. Nothing here resets fixtures — the world is the seed's, and
 * the pass is release evidence, not a fixture-driven spec.
 *
 * Prerequisite: `make seed-kentender-mvp-v1` (the seed is idempotent).
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const SEED = "kentender_procurement.procurement_planning.seeds.kentender_mvp_v1";
const PASSWORD = "Test@123";
const FY = "2027-2028";

const MERCY = "mercy.kilonzo@moh.example.test";
const GRACE = "grace.wanjiku@moh.example.test";
const JOSPHAT = "josphat.mwangi@moh.example.test";
const DANIEL = "daniel.rotich@moh.example.test";
const NAOMI = "naomi.chebet@moh.example.test";
const SAMUEL = "samuel.otieno@moh.example.test";

let PLAN = "";

// Sequential, but not serial: these run on one worker because the fixtures
// are one shared world, and each test rebuilds its own. Aborting the rest of
// the file because one test failed hides every other result behind it.
test.describe.configure({ timeout: 180_000 });

test.beforeAll(() => {
	// FU-10/FU-11 — until the Strategy §14.3 seed and the Budget lines' unit
	// ownership land, the §14 world cannot exist; the seed fails loudly and
	// this pass skips with the exact missing prerequisite.
	try {
		execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ${SEED}.verify_prerequisites`, { stdio: "pipe", timeout: 300_000, encoding: "utf-8" });
	} catch (error: any) {
		const detail = (error?.stderr || error?.stdout || "").toString().split("\n").filter((l: string) => l.includes("Missing:")).pop() || "prerequisites absent";
		test.skip(true, `§14 world unavailable: ${detail.trim().slice(0, 300)}`);
		return;
	}
	const out = execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ${SEED}.upsert_planning_base --kwargs "{'commit': True}"`, {
		stdio: "pipe", timeout: 600_000, encoding: "utf-8",
	}).trim();
	const line = out.split("\n").pop() || "{}";
	PLAN = JSON.parse(line.replace(/'/g, '"').replace(/\bTrue\b/g, "true").replace(/\bFalse\b/g, "false")).plan_reference;
	expect(PLAN).toBeTruthy();
});

async function selectSeedYear(page: import("@playwright/test").Page): Promise<void> {
	const select = page.locator('[data-testid="pln-fy-select"]');
	if ((await select.inputValue()) !== FY) {
		await select.selectOption(FY);
		await expectReady(page, "workspace");
	}
}

test.describe("§14 persona pass on the seeded world", () => {
	test("Mercy Kilonzo sees the Active FY 2027/28 Plan and its schedule from the workspace", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, MERCY, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await selectSeedYear(page);
		await expect(page.locator('[data-testid="pln-plan-row-current"]')).toContainText("Current plan");
		await expect(page.locator('[data-testid="pln-plan-row-current"]')).toContainText("KES 130,000,000");
		await expect(page.locator('[data-testid="pln-departmental-table"] tbody tr').first()).toContainText("Digital Health");

		await page.goto(`/app/annual-procurement-plan/${PLAN}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="ppl-context"]')).toContainText("Ministry of Health Annual Procurement Plan 2027/28");
		await expect(page.locator('[data-testid="ppl-context"]')).toContainText("FY 2027/28");
		// §10.6 — an active plan states its own approval and publication.
		const governance = page.locator('[data-testid="ppl-governance"]');
		await expect(governance).toContainText("Amina Hassan · 8 Dec 2026, 10:00 EAT");
		await expect(governance).toContainText("9 Dec 2026, 11:00 EAT");
		await expect(governance).toContainText("Acknowledged · 10 Dec 2026, 15:00 EAT");

		// §10.13 — what has actually been procured against it.
		await page.locator('[data-testid="ppl-view-progress"]').click();
		await expectReady(page, "progress");
		await expect(page.locator('[data-testid="prg-purchase"]')).toHaveCount(2);
		await expect(page.locator('[data-testid="prg-context"]')).toContainText("FY 2027/28");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Grace Wanjiku sees her accepted Digital Health plan with the Need-origin row", async ({ page }) => {
		await login(page, GRACE, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await selectSeedYear(page);
		const row = page.locator('[data-testid="pln-departmental-table"] tbody tr', { hasText: "Digital Health" });
		await expect(row.locator(".kt-status")).toHaveText("Accepted");
		await row.locator("button").click();
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="pln-dpp-context"]')).toContainText("Accepted");
		await expect(page.locator('[data-testid="pln-dpp-table"] tbody tr').first()).toContainText("Accepted Need · NDS-MOH-2027-0001");
		await expect(page.locator('[data-testid="pln-dpp-table"] tbody tr').first()).toContainText("KES 80,000,000");
		await expect(page.locator('[data-testid="pln-dpp-add"]')).toHaveCount(0);
	});

	test("Josphat, Daniel and Naomi are offered no work on the settled plan", async ({ page }) => {
		for (const persona of [JOSPHAT, DANIEL, NAOMI]) {
			await login(page, persona, PASSWORD);
			await gotoPlanning(page);
			await expectReady(page, "workspace");
			await selectSeedYear(page);
			await expect(page.locator('[data-testid="pln-action"]')).toHaveCount(0);
			await expect(page.locator('[data-testid="pln-forbidden"]')).toHaveCount(0);
			await expect(page.locator('[data-testid="pln-plan-row-current"]')).toContainText("Current plan");
		}
	});

	test("Samuel Otieno's expired assignment gets the Forbidden panel with nothing painted (PLN-AC-111)", async ({ page }) => {
		await login(page, SAMUEL, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-forbidden"] h3')).toHaveText("You do not have access to Procurement Planning");
		await expect(page.locator('[data-testid="pln-context-strip"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-departmental-table"]')).toHaveCount(0);
	});
});
