import { execSync } from "node:child_process";
import path from "node:path";

import { expect, test, Page } from "@playwright/test";

import { login } from "../../helpers/auth";

/**
 * PLN-CHG-001 v1.2 Phase 8 (Slice F) — PLN-UI-11/12: Accounting Officer
 * adoption and statutory approval, in a real browser on the **PE-PWGV**
 * world (its own fixture entity per tracker rule 8; the fixture drives the
 * real §5.1/§5.2/§8.2 commands to a submitted Plan awaiting Accounting
 * Officer adoption).
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures";

const PASSWORD = "Test@123";
const AO = "pwgv.ao@example.test";
const STATUTORY = "pwgv.statutory@example.test";
const PLANNER = "pwgv.planner@example.test";

let TASK = "";
let PLAN_REFERENCE = "";

function bench(command: string): string {
	try {
		return execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} ${command}`, {
			stdio: "pipe",
			timeout: 300_000,
			encoding: "utf-8",
		});
	} catch (error: any) {
		const stderr = (error?.stderr || "").toString().trim();
		const stdout = (error?.stdout || "").toString().trim();
		throw new Error(`bench ${command} failed\n${stderr || stdout || error?.message}`);
	}
}

async function expectReady(page: Page, screen: string): Promise<void> {
	const shell = page.locator('[data-testid="pln-shell"]');
	await expect(shell).toHaveAttribute("data-screen", screen, { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
}

function pageErrors(errors: string[]): string[] {
	return errors.filter(
		(text) => !text.includes("socket.io") && !text.includes("Failed to load resource")
	);
}

test.beforeEach(() => {
	const out = bench(`execute ${FIXTURES}.reset_governance_fixture`);
	const parsed = JSON.parse(out.trim().split("\n").pop() || "{}");
	TASK = parsed.task;
	PLAN_REFERENCE = parsed.plan_reference;
	expect(TASK).toBeTruthy();
	expect(PLAN_REFERENCE).toBeTruthy();
});

test.describe("PLN-UI-11/12 Annual Plan governance", () => {
	test("the Accounting Officer adopts, the Statutory approver approves, and the Plan is Approved — publication pending", async ({
		page,
	}) => {
		test.setTimeout(120_000); // three logins + the full AO→Statutory chain
		const errors: string[] = [];
		page.on("console", (m) => {
			if (m.type() === "error") errors.push(m.text());
		});

		await login(page, AO, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-planning/review/${TASK}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "governance");

		// PLN-DES-11 exact composition
		await expect(page.locator(".kt-page-kicker")).toContainText("ACCOUNTING OFFICER ADOPTION");
		await expect(page.locator('[data-testid="pgt-badge"]')).toHaveText("Awaiting Accounting Officer");
		await expect(page.locator('[data-testid="pgt-items"]')).toContainText(
			"National digital health infrastructure upgrade"
		);
		await expect(page.locator('[data-testid="pgt-items"]')).toContainText("1 Plan Item · KES 80,000,000");
		await expect(page.locator('[data-testid="pgt-statement"]')).toContainText("I adopt the complete");
		await expect(page.locator('[data-testid="pgt-authority"]')).toHaveCount(0);

		await page.locator('[data-testid="pgt-confirm"]').click();
		await expectReady(page, "workspace");

		// the workbench itself is Planner/Auditor scope (§6) — confirm the
		// Version moved on before following the statutory task itself
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${PLAN_REFERENCE}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="pln-plan-badge"]')).toHaveText("Awaiting statutory approval");

		// governance_task_reference is deterministic from (stage, version_reference)
		// — AOT-/SAT- share the same suffix, so the statutory task's id is derivable
		const statutoryTask = TASK.replace(/^AOT-/, "SAT-");
		await login(page, STATUTORY, PASSWORD);
		await page.goto(`/app/procurement-planning/review/${statutoryTask}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "governance");
		await expect(page.locator(".kt-page-kicker")).toContainText("STATUTORY APPROVAL");
		await expect(page.locator('[data-testid="pgt-badge"]')).toHaveText("Awaiting statutory approval");
		await expect(page.locator('[data-testid="pgt-authority"]')).toContainText(
			"Responsible Cabinet Secretary"
		);
		await expect(page.locator('[data-testid="pgt-authority"]')).toContainText(
			"Playwright Governance AO"
		);
		await page.locator('[data-testid="pgt-confirm"]').click();
		await expectReady(page, "workspace");

		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${PLAN_REFERENCE}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="pln-plan-badge"]')).toHaveText(
			"Approved — publication pending"
		);

		expect(pageErrors(errors), errors.join("\n")).toHaveLength(0);
	});

	test("Accounting Officer return preserves the submission and the workbench shows the correction Draft", async ({
		page,
	}) => {
		await login(page, AO, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-planning/review/${TASK}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "governance");

		await page.locator('[data-testid="pgt-return"]').click();
		const dialog = page.locator('[data-testid="pgt-return-dialog"]');
		await expect(dialog).toBeVisible();
		await expect(dialog).toContainText("Return Plan Version for correction?");
		const confirm = page.locator('[data-testid="pgt-return-confirm"]');
		await expect(confirm).toBeDisabled();
		await page.locator('[data-testid="pgt-return-reason"]').fill(
			"Confirm the planned contract-signing date against the delivery completion date."
		);
		await expect(confirm).toBeEnabled();
		await confirm.click();
		await expectReady(page, "workspace");

		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${PLAN_REFERENCE}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="pln-plan-badge"]')).toHaveText("Draft");
		await expect(page.locator('[data-testid="pln-plan-items"]')).toContainText(
			"National digital health infrastructure upgrade"
		);
	});

	test("a Planner's deep link to the governance review route masks as not-found", async ({ page }) => {
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-planning/review/${TASK}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "governance");
		await expect(page.locator('[data-testid="pln-error"]')).toBeVisible();
		await expect(page.locator('[data-testid="pgt-confirm"]')).toHaveCount(0);
	});
});
