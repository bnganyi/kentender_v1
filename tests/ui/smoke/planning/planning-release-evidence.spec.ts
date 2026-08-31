import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

import { expect, test, Page } from "@playwright/test";

import { login } from "../../helpers/auth";

/**
 * PLN-CHG-001 v1.2 Phase 12 — §15.1(6) journeys and the §16.3 evidence pack.
 *
 * Captures every reachable PLN-DES artboard screen at 1440×1024 into
 * docs/mvp-1-r1/04_planning/evidence/ while asserting the journeys §15.1(6)
 * names: direct-only DPP (the PE-PWDP suite already owns that journey),
 * accepted-Need DPP, mixed DPP, integrated Active Plan, Finance shortfall,
 * governance return and publication retry. PLN-DES-13 (Publication Result)
 * is deliberately not captured: that screen was deliberately not built
 * (tracker PLN-902) — the sandbox destination's only reachable outcome is
 * already surfaced on DES-14's governance card.
 *
 * Tests run serially (workers=1) and the LAST test restores the §14
 * integrated MOH baseline, since several profiles rebuild the MOH world.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const SEED = "kentender_procurement.procurement_planning.seeds.kentender_mvp_v1";
const FIXTURES = "kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures";
const EVIDENCE = "docs/mvp-1-r1/04_planning/evidence";

const PASSWORD = "Test@123";
const MERCY = "mercy.kilonzo@moh.example.test";
const GRACE = "grace.wanjiku@moh.example.test";
const PETER = "peter.kimani@moh.example.test";
const MOH_BUDGET = "moh.budget.officer@example.test";

function bench(command: string): string {
	try {
		return execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} ${command}`, {
			stdio: "pipe",
			timeout: 600_000,
			encoding: "utf-8",
		});
	} catch (error: any) {
		const stderr = (error?.stderr || "").toString().trim();
		const stdout = (error?.stdout || "").toString().trim();
		throw new Error(`bench ${command} failed\n${stderr || stdout || error?.message}`);
	}
}

function benchJson(command: string): any {
	const out = bench(command);
	return JSON.parse(out.trim().split("\n").pop() || "{}");
}

async function expectReady(page: Page, screen: string): Promise<void> {
	const shell = page.locator('[data-testid="pln-shell"]');
	await expect(shell).toHaveAttribute("data-screen", screen, { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
}

async function capture(page: Page, name: string): Promise<void> {
	await page.screenshot({ path: `${EVIDENCE}/${name}.png`, fullPage: true });
}

test.beforeAll(() => {
	fs.mkdirSync(EVIDENCE, { recursive: true });
});

test.describe.configure({ mode: "serial" });

test.describe("PLN §15.1(6) journeys and §16.3 evidence", () => {
	test("mixed DPP journey + DES-02/03/04/05 (the §14.7 direct profile)", async ({ page }) => {
		test.setTimeout(240_000);
		const profile = benchJson(`execute ${SEED}.seed_direct_profile --kwargs "{'commit': True}"`);
		const ref = profile.dpp_reference;
		expect(profile.need_entry_id).toBeTruthy();

		await page.setViewportSize({ width: 1440, height: 1024 });
		await login(page, GRACE, PASSWORD);
		await page.goto(`/app/departmental-procurement-plan/${ref}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "dpp");
		// the mixed DPP: both origins present (§15.1(6) "mixed DPP")
		await expect(page.locator('[data-testid="dpp-entries"]')).toContainText(
			"National digital health infrastructure upgrade"
		);
		await expect(page.locator('[data-testid="dpp-entries"]')).toContainText(
			"Digital health platform security assessment"
		);
		await capture(page, "PLN-DES-02");

		await page.goto(`/app/departmental-procurement-plan/${ref}/entry/${profile.need_entry_id}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "dpp-entry");
		await capture(page, "PLN-DES-03");

		await page.goto(`/app/departmental-procurement-plan/${ref}/entry/${profile.entry_id}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "dpp-entry");
		await capture(page, "PLN-DES-04");

		// DES-05: the HoD's submission view — certification statement present
		await login(page, PETER, PASSWORD);
		await page.goto(`/app/departmental-procurement-plan/${ref}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="dpp-certification"]')).toBeVisible();
		await capture(page, "PLN-DES-05");
	});

	test("DES-06 DPP validation task (PE-PWVC)", async ({ page }) => {
		test.setTimeout(240_000);
		const world = benchJson(`execute ${FIXTURES}.reset_review_fixture`);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await login(page, "pwvc.planner@example.test", PASSWORD);
		await page.goto(`/app/procurement-planning/dpp-review/${world.task}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "dpp-review");
		await capture(page, "PLN-DES-06");
	});

	test("DES-07/08 workbench and formation dialog (PE-PWPF)", async ({ page }) => {
		test.setTimeout(240_000);
		const world = benchJson(`execute ${FIXTURES}.reset_plan_workbench_fixture`);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await login(page, "pwpf.planner@example.test", PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${world.plan_reference}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "plan");
		await capture(page, "PLN-DES-07");
		await page.locator('[data-testid="pln-form-items"]').click();
		await expect(page.locator('[data-testid="pln-form-dialog"]')).toBeVisible();
		await capture(page, "PLN-DES-08");
	});

	test("Finance shortfall journey + DES-09/10 (the shortfall profile)", async ({ page }) => {
		test.setTimeout(240_000);
		const profile = benchJson(`execute ${SEED}.seed_shortfall_profile --kwargs "{'commit': True}"`);

		await page.setViewportSize({ width: 1440, height: 1024 });
		await login(page, MERCY, PASSWORD);
		await page.goto(`/app/procurement-plan-item/${profile.plan_item}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "plan-item");
		await capture(page, "PLN-DES-09");

		await login(page, MOH_BUDGET, PASSWORD);
		await page.goto(`/app/procurement-planning/finance/${profile.finance_task}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "finance");
		// §15.1(6) "Finance shortfall": the required amount exceeds the line
		await expect(page.locator("body")).toContainText("150,000,000");
		await capture(page, "PLN-DES-10");
	});

	test("DES-09A combined Plan Item editor (the §14.8 combined profile)", async ({ page }) => {
		test.setTimeout(240_000);
		const profile = benchJson(`execute ${SEED}.seed_combined_profile --kwargs "{'commit': True}"`);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await login(page, MERCY, PASSWORD);
		await page.goto(`/app/procurement-plan-item/${profile.plan_item}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "plan-item");
		await expect(page.locator("body")).toContainText("2 sources");
		await capture(page, "PLN-DES-09A");
	});

	test("governance return journey + DES-11/12/15 (PE-PWGV)", async ({ page }) => {
		test.setTimeout(300_000);
		const world = benchJson(`execute ${FIXTURES}.reset_governance_fixture`);
		await page.setViewportSize({ width: 1440, height: 1024 });

		await login(page, "pwgv.ao@example.test", PASSWORD);
		await page.goto(`/app/procurement-planning/review/${world.task}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "governance");
		await capture(page, "PLN-DES-11");

		// DES-15: the return dialog (§15.1(6) "governance return")
		await page.locator('[data-testid="pgt-return"]').click();
		await expect(page.locator('[data-testid="pgt-return-dialog"]')).toBeVisible();
		await capture(page, "PLN-DES-15");
		await page.locator('[data-testid="pgt-return-dialog"] button:has-text("Cancel")').click();
		await expect(page.locator('[data-testid="pgt-return-dialog"]')).toHaveCount(0);

		// adopt, then the statutory stage (DES-12)
		await page.locator('[data-testid="pgt-confirm"]').click();
		await expectReady(page, "workspace");
		const statutoryTask = world.task.replace(/^AOT-/, "SAT-");
		await login(page, "pwgv.statutory@example.test", PASSWORD);
		await page.goto(`/app/procurement-planning/review/${statutoryTask}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "governance");
		await capture(page, "PLN-DES-12");
	});

	test("DES-16 common page states (PE-PWPL no-scope card)", async ({ page }) => {
		test.setTimeout(240_000);
		bench(`execute ${FIXTURES}.reset_workspace_fixture`);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await login(page, "pwpl.outsider@example.test", PASSWORD);
		await page.goto("/app/procurement-planning", { waitUntil: "domcontentloaded" });
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-no-scope"]')).toBeVisible();
		await capture(page, "PLN-DES-16");
	});

	test("publication retry journey (the publication-failure profile)", async ({ page }) => {
		test.setTimeout(300_000);
		const profile = benchJson(
			`execute ${SEED}.seed_publication_failure_profile --kwargs "{'commit': True}"`
		);
		expect(profile.publication).toBeTruthy();

		// §12.11: retry is System-Manager-only with no business-role trigger —
		// executed as the administrative principal, exactly the §12.11 shape.
		const retried = benchJson(
			`execute kentender_procurement.procurement_planning.services.plan_publication.retry_publication ` +
				`--kwargs "{'publication': '${profile.publication}', 'idempotency_key': 'pln-evidence-retry-${Date.now()}'}"`
		);
		expect(retried.result).toBe("Acknowledged");  // bench execute auto-commits

		await page.setViewportSize({ width: 1440, height: 1024 });
		await login(page, MERCY, PASSWORD);
		await page.goto("/app/annual-procurement-plan/PLN-MOH-2027-001", {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="pln-plan-badge"]')).toHaveText("Active");
	});

	test("integrated Active Plan + accepted-Need DPP journeys + DES-01/14 (baseline restored)", async ({
		page,
	}) => {
		test.setTimeout(300_000);
		bench(`execute ${SEED}.reset_planning_seed --kwargs "{'commit': True}"`);
		const base = benchJson(`execute ${SEED}.upsert_planning_base --kwargs "{'commit': True}"`);
		expect(base.publication_result).toBe("Acknowledged");

		await page.setViewportSize({ width: 1440, height: 1024 });
		await login(page, MERCY, PASSWORD);
		await page.goto("/app/procurement-planning", { waitUntil: "domcontentloaded" });
		await expectReady(page, "workspace");
		await expect(page.locator("body")).toContainText("Annual Plan · Active Version 1");
		await capture(page, "PLN-DES-01");

		// §15.1(6) "integrated Active Plan" — the §16.3 scripted click-through
		await page.goto("/app/annual-procurement-plan/PLN-MOH-2027-001", {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="pln-plan-badge"]')).toHaveText("Active");
		await expect(page.locator('[data-testid="pln-active-summary-strip"]')).toContainText(
			"KES 80,000,000"
		);
		await expect(page.locator('[data-testid="pln-active-governance"]')).toContainText(
			"Acknowledged · 10 Dec 2026, 15:00 EAT"
		);
		await capture(page, "PLN-DES-14");

		// §15.1(6) "accepted-Need DPP": Grace's departmental plan carries the
		// projected Need-origin entry
		const dppRef = bench(
			`execute frappe.client.get_value --kwargs "{'doctype': 'Departmental Plan', 'filters': {'procuring_entity': 'PE-MOH'}, 'fieldname': 'dpp_reference'}"`
		);
		const parsed = JSON.parse(dppRef.trim().split("\n").pop() || "{}");
		await login(page, GRACE, PASSWORD);
		await page.goto(`/app/departmental-procurement-plan/${parsed.dpp_reference}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="dpp-entries"]')).toContainText(
			"National digital health infrastructure upgrade"
		);
		await expect(page.locator('[data-testid="dpp-badge"]')).toHaveText("Accepted");
	});
});
