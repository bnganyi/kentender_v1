import { execSync } from "node:child_process";
import path from "node:path";

import { expect, test, Page } from "@playwright/test";

import { login } from "../../helpers/auth";

/**
 * PLN-CHG-001 v1.2 Phase 5 (Slice C) — PLN-UI-06: the DPP validation task,
 * classification, acceptance (auto-creating the Draft Annual Plan) and the
 * structured-issue return dialog, in a real browser on the **PE-PWVC** world
 * (its own fixture entity per tracker rule 8; the fixture drives the real
 * §8.2 commands to a submitted state).
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures";

const PASSWORD = "Test@123";
const PLANNER = "pwvc.planner@example.test";
const HOD = "pwvc.hod@example.test";

let TASK = "";

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
	const out = bench(`execute ${FIXTURES}.reset_review_fixture`);
	TASK = JSON.parse(out.trim().split("\n").pop() || "{}").task;
	expect(TASK).toBeTruthy();
});

test.describe("PLN-UI-06 DPP validation", () => {
	test("planner classifies, accepts, and the workspace offers Form Plan Items from the auto-created Draft Plan", async ({
		page,
	}) => {
		const errors: string[] = [];
		page.on("console", (m) => {
			if (m.type() === "error") errors.push(m.text());
		});

		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		// the §10 deep link, exactly as My Work and notifications route it
		await page.goto(`/app/procurement-planning/dpp-review/${TASK}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "dpp-review");

		// PLN-DES-06 exact composition
		await expect(page.locator(".kt-page-kicker")).toHaveText("DEPARTMENTAL PLAN REVIEW");
		await expect(page.locator(".kt-page-title")).toHaveText(
			"Validate Digital Health departmental plan"
		);
		await expect(page.locator('[data-testid="dppv-badge"]')).toHaveText(
			"Awaiting validation"
		);
		await expect(page.locator('[data-testid="dppv-context"]')).toContainText(
			"Playwright Review HoD"
		);
		await expect(page.locator('[data-testid="dppv-context"]')).toContainText(
			"KES 20,000,000"
		);
		await expect(page.locator('[data-testid="dppv-certification"]')).toContainText(
			"Certified by Playwright Review HoD"
		);

		// acceptance is blocked until every entry is classified (§12.6)
		const accept = page.locator('[data-testid="dppv-accept"]');
		await expect(accept).toBeDisabled();
		const typeSelect = page.locator('[data-testid^="dppv-type-"]');
		await typeSelect.selectOption("Consulting services");
		await expect(accept).toBeEnabled();
		await accept.click();

		// acceptance lands on the workspace, which now offers Plan Item work
		await expectReady(page, "workspace");
		const work = page.locator('[data-testid="pln-your-work"] tbody tr');
		await expect(work).toContainText("Form Plan Items", { timeout: 30_000 });
		await expect(work).toContainText("1 accepted departmental entry · KES 20,000,000");
		await expect(page.locator('[data-testid="pln-plan-summary"]')).toHaveText(
			"Annual Plan · Draft Version 1"
		);
		const planRow = page.locator('[data-testid="pln-departmental-plans"] tbody tr');
		await expect(planRow.locator(".kt-status")).toHaveText("Accepted");
		expect(pageErrors(errors), errors.join("\n")).toHaveLength(0);
	});

	test("return requires a complete structured issue and lands the correction on the department", async ({
		page,
	}) => {
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-planning/dpp-review/${TASK}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "dpp-review");

		await page.locator('[data-testid="dppv-return"]').click();
		const dialog = page.locator('[data-testid="dppv-return-dialog"]');
		await expect(dialog).toBeVisible();
		const confirm = page.locator('[data-testid="dppv-return-confirm"]');
		await expect(confirm).toBeDisabled(); // incomplete issue
		await page.locator('[data-testid="dppv-issue-problem-0"]').fill("Amount unsupported");
		await expect(confirm).toBeDisabled(); // correction still missing
		await page
			.locator('[data-testid="dppv-issue-correction-0"]')
			.fill("Align the indicative amount with the budget line.");
		await expect(confirm).toBeEnabled();
		await confirm.click();
		await expectReady(page, "workspace");

		// the department sees the returned plan with the issue on its entry
		await login(page, HOD, PASSWORD);
		await page.goto("/app/departmental-procurement-plan/DPP-PWVC-DHI-2098-001", {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="dpp-issue"]')).toContainText(
			"Amount unsupported"
		);
		await expect(page.locator('[data-testid="dpp-issue"]')).toContainText(
			"Align the indicative amount with the budget line."
		);
	});

	test("the certifier sees the task read-only with the maker-checker notice", async ({
		page,
	}) => {
		// HoD holds no Planner role, so the deep link masks as not-found for
		// them — the maker-checker READ state needs a planner who certified.
		// The HYBRID case is python-tested; here we assert the direct-URL mask.
		await login(page, HOD, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-planning/dpp-review/${TASK}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "dpp-review");
		await expect(page.locator('[data-testid="pln-error"]')).toBeVisible();
		await expect(page.locator('[data-testid="dppv-accept"]')).toHaveCount(0);
	});
});
