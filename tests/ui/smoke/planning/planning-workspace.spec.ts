import { execSync } from "node:child_process";
import path from "node:path";

import { expect, test, Page } from "@playwright/test";

import { login } from "../../helpers/auth";

/**
 * PLN-CHG-001 v1.2 Phase 3 (Slice A) — PLN-UI-01 workspace, context and
 * common states, per role, in a real browser.
 *
 * Fixtures come from `procurement_planning.seeds.playwright_ui_fixtures`,
 * which owns records under **PE-PWPL** — never the §14 demo world and never
 * the Python tests' PE-PLNT (tracker rule 8: this spec file owns its fixture
 * entity, so it can run alongside other modules' files). Every reset clears
 * the actors' server-side context preferences (CTX-CHG-001).
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures";

const PASSWORD = "Test@123";
const AUTHOR = "pwpl.author@example.test";
const PLANNER = "pwpl.planner@example.test";
const AUDITOR = "pwpl.auditor@example.test";
const OUTSIDER = "pwpl.outsider@example.test";

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

async function gotoPlanning(page: Page): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto("/app/procurement-planning", { waitUntil: "domcontentloaded" });
}

async function expectReady(page: Page): Promise<void> {
	const shell = page.locator('[data-testid="pln-shell"]');
	await expect(shell).toHaveAttribute("data-screen", "workspace", { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
}

async function selectFinancialYear(page: Page, fy = "FY-2098-2099"): Promise<void> {
	const select = page.locator('[data-testid="pln-fy-select"]');
	if ((await select.inputValue()) !== fy) {
		await select.selectOption(fy);
		await expectReady(page);
	}
}

function pageErrors(errors: string[]): string[] {
	// §16.3 demands zero PAGE-SPECIFIC console errors. The dev bench's
	// realtime (socket.io) transport flaps independently of the page under
	// test; its polling noise is excluded, nothing else is.
	return errors.filter(
		(text) => !text.includes("socket.io") && !text.includes("Failed to load resource")
	);
}

test.beforeEach(() => {
	bench(`execute ${FIXTURES}.reset_workspace_fixture`);
});

test.describe("PLN-UI-01 Procurement Planning workspace", () => {
	test("author selects the year, opens the departmental plan and sees the live re-render", async ({
		page,
	}) => {
		await login(page, AUTHOR, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page);

		// PLN-DES-01 masthead, exact copy; no header action button.
		await expect(page.locator(".kt-page-kicker")).toHaveText("PROCUREMENT PLANNING");
		await expect(page.locator(".kt-page-title")).toHaveText("Annual procurement planning");
		await expect(page.locator(".pln-masthead button")).toHaveCount(0);

		await selectFinancialYear(page);

		// The one offered action for an empty department (window open).
		const workRow = page.locator('[data-testid="pln-your-work"] tbody tr');
		await expect(workRow).toHaveCount(1);
		await expect(workRow).toContainText("Open departmental plan");
		await expect(page.locator('[data-testid="pln-count-label"]')).toHaveText(
			"0 departmental plans"
		);

		// A real §8.2 command from the button, then the interactive re-render.
		await page.locator('[data-testid="pln-work-action-0"]').click();
		await expect(workRow).toContainText("Continue departmental plan", { timeout: 30_000 });
		const planRow = page.locator('[data-testid="pln-departmental-plans"] tbody tr');
		await expect(planRow).toHaveCount(1);
		await expect(planRow).toContainText("Digital Health");
		await expect(planRow.locator(".kt-status")).toHaveText("Draft");
		await expect(page.locator('[data-testid="pln-count-label"]')).toHaveText(
			"1 departmental plan"
		);
	});

	test("auditor reads the register but is offered no work at all", async ({ page }) => {
		await login(page, AUDITOR, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page);
		await selectFinancialYear(page);

		// Absence assertions (the NDS lesson): nothing decidable is offered.
		await expect(page.locator('[data-testid="pln-your-work"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-departmental-plans"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-no-scope"]')).toHaveCount(0);
	});

	test("an actor without a Procuring Entity permission fails closed on the exact state card", async ({
		page,
	}) => {
		await login(page, OUTSIDER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page);

		const card = page.locator('[data-testid="pln-no-scope"]');
		await expect(card.locator("h3")).toHaveText("Procurement Planning is not available");
		await expect(card).toContainText(
			"You do not have an assigned Procuring Entity scope, or no configured Financial Year is available for Planning."
		);
		// Nothing else renders: no strip, no tables, no work.
		await expect(page.locator('[data-testid="pln-context-strip"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-departmental-plans"]')).toHaveCount(0);
	});

	test("planner sees the departmental register with zero console errors", async ({ page }) => {
		const errors: string[] = [];
		page.on("console", (message) => {
			if (message.type() === "error") errors.push(message.text());
		});
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page);
		await selectFinancialYear(page);
		await expect(page.locator('[data-testid="pln-departmental-plans"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-your-work"]')).toHaveCount(0);
		expect(pageErrors(errors), `page console errors: ${errors.join("\n")}`).toHaveLength(0);
	});
});
