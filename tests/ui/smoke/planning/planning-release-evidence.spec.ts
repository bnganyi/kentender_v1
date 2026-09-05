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

test.describe.configure({ mode: "serial", timeout: 180_000 });

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
		await expect(page.locator('[data-testid="pln-plan-summary"]')).toHaveText("· Annual Plan · Active Version 1");
		await expect(page.locator('[data-testid="pln-schedule-health"]')).toHaveText("· 0 of 1 item behind baseline");
		await expect(page.locator('[data-testid="pln-departmental-plans"] tbody tr').first()).toContainText("Digital Health");
		await page.goto(`/app/annual-procurement-plan/${PLAN}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await expect(page.locator(".kt-page-title")).toHaveText("Ministry of Health Annual Procurement Plan 2027/28");
		await expect(page.locator('[data-testid="pln-plan-badge"]')).toHaveText("Active");
		await expect(page.locator('[data-testid="pln-active-summary-strip"]')).toContainText("KES 80,000,000");
		await expect(page.locator('[data-testid="pln-active-summary-strip"]')).toContainText("10 Dec 2026, 15:00 EAT");
		await expect(page.locator('[data-testid="pln-active-governance"]')).toContainText("Amina Hassan · 8 Dec 2026, 10:00 EAT");
		await expect(page.locator('[data-testid="pln-active-governance"]')).toContainText("9 Dec 2026, 11:00 EAT");
		await expect(page.locator('[data-testid="pln-active-governance"]')).toContainText("Acknowledged · 10 Dec 2026, 15:00 EAT");
		await page.locator('[data-testid^="pln-active-schedule-"]').first().click();
		await expect(page.locator('[data-testid="pln-schedule-invitation"] .pln-baseline-val')).toHaveText("1 May 2027");
		await expect(page.locator('[data-testid="pln-schedule-delivery_completion"] .pln-baseline-val')).toHaveText("31 Aug 2027");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Grace Wanjiku sees her accepted Digital Health plan with the Need-origin row", async ({ page }) => {
		await login(page, GRACE, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await selectSeedYear(page);
		const row = page.locator('[data-testid="pln-departmental-plans"] tbody tr', { hasText: "Digital Health" });
		await expect(row.locator(".kt-status")).toHaveText("Accepted");
		await row.locator("button").click();
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="dpp-badge"]')).toHaveText("Accepted");
		await expect(page.locator('[data-testid="dpp-entries"] tbody tr').first()).toContainText("Accepted Need · NDS-MOH-2027-0001");
		await expect(page.locator('[data-testid="dpp-entries"] tbody tr').first()).toContainText("KES 80,000,000");
		await expect(page.locator('[data-testid="dpp-add-direct"]')).toHaveCount(0);
	});

	test("Josphat, Daniel and Naomi are offered no work on the settled plan", async ({ page }) => {
		for (const persona of [JOSPHAT, DANIEL, NAOMI]) {
			await login(page, persona, PASSWORD);
			await gotoPlanning(page);
			await expectReady(page, "workspace");
			await selectSeedYear(page);
			await expect(page.locator('[data-testid="pln-actionable"]')).toHaveCount(0);
			await expect(page.locator('[data-testid="pln-forbidden"]')).toHaveCount(0);
			await expect(page.locator('[data-testid="pln-plan-summary"]')).toHaveText("· Annual Plan · Active Version 1");
		}
	});

	test("Samuel Otieno's expired assignment gets the Forbidden panel with nothing painted (PLN-AC-111)", async ({ page }) => {
		await login(page, SAMUEL, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-forbidden"] h3')).toHaveText("You do not have access to Procurement Planning");
		await expect(page.locator('[data-testid="pln-context-strip"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-departmental-plans"]')).toHaveCount(0);
	});
});
