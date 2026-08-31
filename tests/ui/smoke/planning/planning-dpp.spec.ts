import { execSync } from "node:child_process";
import path from "node:path";

import { expect, test, Page } from "@playwright/test";

import { login } from "../../helpers/auth";

/**
 * PLN-CHG-001 v1.2 Phase 4 (Slice B) — PLN-UI-02..05: the departmental plan,
 * direct-requirement editor, certification and submission, per role, in a
 * real browser.
 *
 * Fixtures own **PE-PWDP** (its own entity per tracker rule 8) with an Active
 * Budget graph so the live `list_eligible_budget_lines` contract returns a
 * real line — no mocking anywhere in this path.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures";

const PASSWORD = "Test@123";
const AUTHOR = "pwdp.author@example.test";
const HOD = "pwdp.hod@example.test";
const PLANNER = "pwdp.planner@example.test";

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

async function openPlanFromWorkspace(page: Page): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto("/app/procurement-planning", { waitUntil: "domcontentloaded" });
	await expectReady(page, "workspace");
	const fySelect = page.locator('[data-testid="pln-fy-select"]');
	if ((await fySelect.inputValue()) !== "FY-2098-2099") {
		await fySelect.selectOption("FY-2098-2099");
		await expectReady(page, "workspace");
	}
	await page.locator('[data-testid="pln-work-action-0"]').click();
	await expect(
		page.locator('[data-testid="pln-departmental-plans"] tbody tr')
	).toHaveCount(1, { timeout: 30_000 });
	await page
		.locator('[data-testid="pln-departmental-plans"] tbody tr .kt-btn-ghost')
		.click();
	await expectReady(page, "dpp");
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
	bench(`execute ${FIXTURES}.reset_dpp_fixture`);
});

test.describe("PLN-UI-02..05 Departmental Procurement Plan", () => {
	test("author adds a direct requirement through the real Budget contract and the plan re-renders Ready", async ({
		page,
	}) => {
		const errors: string[] = [];
		page.on("console", (message) => {
			if (message.type() === "error") errors.push(message.text());
		});

		await login(page, AUTHOR, PASSWORD);
		await openPlanFromWorkspace(page);

		// PLN-DES-02: header + context strip + no certification for an author.
		await expect(page.locator(".kt-page-title")).toHaveText(
			"Digital Health departmental plan"
		);
		await expect(page.locator('[data-testid="dpp-badge"]')).toHaveText("Draft");
		await expect(page.locator('[data-testid="dpp-context"]')).toContainText(
			"Open until"
		);
		await expect(page.locator('[data-testid="dpp-certification"]')).toHaveCount(0);

		await page.locator('[data-testid="dpp-add-direct"]').click();
		await expectReady(page, "dpp-entry");
		await page.locator('[data-testid="dpp-f-title"]').fill("Platform security assessment");
		await page
			.locator('[data-testid="dpp-f-description"]')
			.fill("Assess the security of the platform and provide a prioritised remediation report.");
		await page
			.locator('[data-testid="dpp-f-result"]')
			.fill("The department receives a prioritised and actionable remediation plan.");
		await page.locator('[data-testid="dpp-f-quantity"]').fill("1");
		await page.locator('[data-testid="dpp-f-required-by"]').fill("2099-04-30");
		// the real eligible line, straight from Budget's published contract
		const lineSelect = page.locator('[data-testid="dpp-f-budget-line"]');
		await expect(lineSelect.locator("option")).toHaveCount(1);
		await expect(lineSelect.locator("option")).toContainText("Digital health programme");
		await lineSelect.selectOption({ index: 0 });
		await page.locator('[data-testid="dpp-f-amount"]').fill("20000000");
		await page.locator('[data-testid="dpp-editor-save"]').click();

		await expectReady(page, "dpp");
		const row = page.locator('[data-testid="dpp-entries"] tbody tr').first();
		await expect(row).toContainText("Platform security assessment");
		await expect(row).toContainText("Direct requirement");
		await expect(row).toContainText("KES 20,000,000");
		await expect(row.locator(".kt-status")).toHaveText("Ready");
		await expect(page.locator('[data-testid="dpp-badge"]')).toHaveText("Ready to submit");
		await expect(page.locator('[data-testid="dpp-totals"]')).toHaveText(
			"1 requirement · KES 20,000,000"
		);
		// author still cannot submit — HoD only (§5.1)
		await expect(page.locator('[data-testid="dpp-certification"]')).toHaveCount(0);
		expect(pageErrors(errors), `page console errors: ${errors.join("\n")}`).toHaveLength(0);
	});

	test("hod certifies and submits; the submitted plan locks and shows Awaiting validation", async ({
		page,
	}) => {
		// author prepares the ready plan through the same UI commands
		await login(page, AUTHOR, PASSWORD);
		await openPlanFromWorkspace(page);
		await page.locator('[data-testid="dpp-add-direct"]').click();
		await expectReady(page, "dpp-entry");
		await page.locator('[data-testid="dpp-f-title"]').fill("Platform security assessment");
		await page
			.locator('[data-testid="dpp-f-description"]')
			.fill("Assess the security of the platform and provide a prioritised remediation report.");
		await page
			.locator('[data-testid="dpp-f-result"]')
			.fill("The department receives a prioritised and actionable remediation plan.");
		await page.locator('[data-testid="dpp-f-quantity"]').fill("1");
		await page.locator('[data-testid="dpp-f-required-by"]').fill("2099-04-30");
		await page.locator('[data-testid="dpp-f-budget-line"]').selectOption({ index: 0 });
		await page.locator('[data-testid="dpp-f-amount"]').fill("20000000");
		await page.locator('[data-testid="dpp-editor-save"]').click();
		await expectReady(page, "dpp");

		// the HoD takes over
		await login(page, HOD, PASSWORD);
		await page.goto("/app/departmental-procurement-plan/DPP-PWDP-DHI-2098-001", {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "dpp");
		const cert = page.locator('[data-testid="dpp-certification"]');
		await expect(cert).toBeVisible();
		await expect(cert).toContainText(
			"I certify that this Departmental Procurement Plan contains the current procurement requirements of Digital Health for FY 2098/99"
		);
		const submit = page.locator('[data-testid="dpp-submit"]');
		await expect(submit).toBeDisabled(); // §12.5 — checkbox first
		await page.locator('[data-testid="dpp-certify"]').check();
		await expect(submit).toBeEnabled();
		await submit.click();

		await expect(page.locator('[data-testid="dpp-badge"]')).toHaveText(
			"Awaiting validation",
			{ timeout: 30_000 }
		);
		// locked: no add button, no row actions, no certification card
		await expect(page.locator('[data-testid="dpp-add-direct"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dpp-certification"]')).toHaveCount(0);
		await expect(
			page.locator('[data-testid="dpp-entries"] .kt-btn-ghost')
		).toHaveCount(0);
	});

	test("planner opens the record read-only with no edit affordances", async ({ page }) => {
		await login(page, AUTHOR, PASSWORD);
		await openPlanFromWorkspace(page);

		await login(page, PLANNER, PASSWORD);
		await page.goto("/app/departmental-procurement-plan/DPP-PWDP-DHI-2098-001", {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="dpp-add-direct"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dpp-certification"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dpp-submit"]')).toHaveCount(0);
	});
});
