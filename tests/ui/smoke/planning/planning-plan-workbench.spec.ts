import { execSync } from "node:child_process";
import path from "node:path";

import { expect, test, Page } from "@playwright/test";

import { login } from "../../helpers/auth";

/**
 * PLN-CHG-001 v1.2 Phase 6 (Slice D) — PLN-UI-07/08/09: the Annual Plan
 * workbench, Form Plan Items formation and the Plan Item editor, in a real
 * browser on the **PE-PWPF** world (its own fixture entity per tracker rule
 * 8; the fixture drives the real §8.2 commands to one accepted, unallocated
 * entry — PLN-DES-07's exact opening state).
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures";

const PASSWORD = "Test@123";
const PLANNER = "pwpf.planner@example.test";
const HOD = "pwpf.hod@example.test";

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
	const out = bench(`execute ${FIXTURES}.reset_plan_workbench_fixture`);
	PLAN_REFERENCE = JSON.parse(out.trim().split("\n").pop() || "{}").plan_reference;
	expect(PLAN_REFERENCE).toBeTruthy();
});

test.describe("PLN-UI-07/08/09 Annual Plan workbench and Plan Item editor", () => {
	test("single-source formation opens straight to the editor, and saving reflects on the workbench", async ({
		page,
	}) => {
		const errors: string[] = [];
		page.on("console", (m) => {
			if (m.type() === "error") errors.push(m.text());
		});

		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/annual-procurement-plan/${PLAN_REFERENCE}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "plan");

		// PLN-DES-07 exact composition
		await expect(page.locator(".kt-page-kicker")).toHaveText("ANNUAL PROCUREMENT PLAN");
		await expect(page.locator('[data-testid="pln-plan-summary-strip"]')).toContainText("KES 0");
		await expect(page.locator('[data-testid="pln-unallocated-sources"]')).toContainText(
			"National digital health infrastructure upgrade"
		);
		await expect(page.locator('[data-testid="pln-submit-consolidated"]')).toBeDisabled();

		// PLN-DES-08 dialog: one source, no formation choice, straight to editor
		await page.locator('[data-testid="pln-form-items"]').click();
		await expect(page.locator('[data-testid="pln-form-dialog"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-form-mode-each"]')).toHaveCount(0);
		await page.locator('[data-testid="pln-form-confirm"]').click();

		await expectReady(page, "plan-item");
		await expect(page.locator(".kt-page-title")).toHaveText(
			"National digital health infrastructure upgrade"
		);
		await expect(page.locator('[data-testid="ppi-source"]')).toContainText("KES 80,000,000");

		// PLN-UI-09: pick the Objective (its id is a hash — select by the
		// option's visible title text, not a literal value), save
		const objectiveSelect = page.locator('[data-testid="ppi-objective"]');
		const objectiveValue = await objectiveSelect
			.locator("option", { hasText: "PWPF Digital Objective" })
			.getAttribute("value");
		await objectiveSelect.selectOption(objectiveValue!);
		await page.locator('[data-testid="ppi-title"]').fill("Digital health infrastructure package");
		await page.locator('[data-testid="ppi-save"]').click();
		await expect(page.locator(".kt-page-title")).toHaveText("Digital health infrastructure package");

		await page.locator('[data-testid="ppi-dissolve"]').click();
		await expectReady(page, "plan");

		expect(pageErrors(errors), errors.join("\n")).toHaveLength(0);
	});

	test("dissolving a formed item returns the source to the unallocated pool", async ({ page }) => {
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/annual-procurement-plan/${PLAN_REFERENCE}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "plan");
		await page.locator('[data-testid="pln-form-items"]').click();
		await page.locator('[data-testid="pln-form-confirm"]').click();
		await expectReady(page, "plan-item");

		await page.locator('[data-testid="ppi-dissolve"]').click();
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="pln-unallocated-sources"]')).toContainText(
			"National digital health infrastructure upgrade"
		);
		await expect(page.locator('[data-testid="pln-plan-items"]')).toContainText("No Plan Items yet");
	});

	test("a non-planner deep link masks as not-found", async ({ page }) => {
		await login(page, HOD, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/annual-procurement-plan/${PLAN_REFERENCE}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="pln-error"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-form-items"]')).toHaveCount(0);
	});
});
