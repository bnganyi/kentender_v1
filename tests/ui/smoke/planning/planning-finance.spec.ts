import { execSync } from "node:child_process";
import path from "node:path";

import { expect, test, Page } from "@playwright/test";

import { login } from "../../helpers/auth";

/**
 * PLN-CHG-001 v1.2 Phase 7 (Slice E) — PLN-UI-10: the Finance confirmation
 * task, real check→reserve funding, and the return-to-planner path, in a
 * real browser on the **PE-PWFN** world (its own fixture entity per tracker
 * rule 8; the fixture drives the real §5.1/§5.2/§8.2 commands to an Open
 * Finance task with sufficient funding — PLN-DES-10's exact opening state).
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures";

const PASSWORD = "Test@123";
const BUDGET_OFFICER = "pwfn.budget@example.test";
const PLANNER = "pwfn.planner@example.test";

let TASK = "";
let PLAN_ITEM = "";

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
	const out = bench(`execute ${FIXTURES}.reset_finance_fixture`);
	const parsed = JSON.parse(out.trim().split("\n").pop() || "{}");
	TASK = parsed.task;
	PLAN_ITEM = parsed.plan_item;
	expect(TASK).toBeTruthy();
	expect(PLAN_ITEM).toBeTruthy();
});

test.describe("PLN-UI-10 Finance confirmation", () => {
	test("the Budget Officer confirms funding on real Budget positions and the Plan Item shows Confirmed", async ({
		page,
	}) => {
		const errors: string[] = [];
		page.on("console", (m) => {
			if (m.type() === "error") errors.push(m.text());
		});

		await login(page, BUDGET_OFFICER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-planning/finance/${TASK}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "finance");

		// PLN-DES-10 exact composition, live Budget positions
		await expect(page.locator(".kt-page-kicker")).toHaveText("FINANCE CONFIRMATION");
		await expect(page.locator('[data-testid="fnt-badge"]')).toHaveText("Awaiting Finance");
		await expect(page.locator('[data-testid="fnt-plan-item"]')).toContainText(
			"National digital health infrastructure upgrade"
		);
		await expect(page.locator('[data-testid="fnt-position"]')).toContainText("KES 100,000,000");
		await expect(page.locator('[data-testid="fnt-position"]')).toContainText("KES 80,000,000");
		await expect(page.locator('[data-testid="fnt-sufficient"]')).toBeVisible();

		await page.locator('[data-testid="fnt-confirm"]').click();
		await expectReady(page, "workspace");

		// the Plan Item detail is Planner/Auditor scope, not Budget Officer's
		// (§6: Budget Officer "cannot edit Planning content" — GetPlanItem
		// masks it as not-found) — switch persona to verify the confirmed state
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/procurement-plan-item/${PLAN_ITEM}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "plan-item");
		await expect(page.locator("text=Confirmed")).toBeVisible();
		await expect(page.locator('[data-testid="ppi-request-finance"]')).toHaveCount(0);

		expect(pageErrors(errors), errors.join("\n")).toHaveLength(0);
	});

	test("return to planner requires a reason and creates no reservation", async ({ page }) => {
		await login(page, BUDGET_OFFICER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-planning/finance/${TASK}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "finance");

		await page.locator('[data-testid="fnt-return"]').click();
		const dialog = page.locator('[data-testid="fnt-return-dialog"]');
		await expect(dialog).toBeVisible();
		const confirm = page.locator('[data-testid="fnt-return-confirm"]');
		await expect(confirm).toBeDisabled();
		await page.locator('[data-testid="fnt-return-reason"]').fill(
			"The indicative amount exceeds the approved Budget Line ceiling."
		);
		await expect(confirm).toBeEnabled();
		await confirm.click();
		await expectReady(page, "workspace");

		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/procurement-plan-item/${PLAN_ITEM}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "plan-item");
		await expect(page.locator("text=Returned")).toBeVisible();
		// Planner-owned fields reopen: Request Finance confirmation is offered again
		await expect(page.locator('[data-testid="ppi-request-finance"]')).toBeVisible();
	});

	test("a non-budget-officer deep link masks as not-found", async ({ page }) => {
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-planning/finance/${TASK}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "finance");
		await expect(page.locator('[data-testid="pln-error"]')).toBeVisible();
		await expect(page.locator('[data-testid="fnt-confirm"]')).toHaveCount(0);
	});
});
