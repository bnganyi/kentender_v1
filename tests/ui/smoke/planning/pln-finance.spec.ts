import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	AUDITOR,
	AUTHOR,
	FINANCE,
	OUTSIDER,
	PASSWORD,
	PLANNER,
	collectConsoleErrors,
	expectReady,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * PLN-CHG-001 v1.18 (PLN18-306) — the Finance task screen's (U10) own real
 * commands and their interactive re-render: Josphat (the fixture's Finance
 * Confirmation Officer persona) confirming and returning a plan, and the
 * same commands over an Active Version's own reassessment (U10-reassess-
 * return, U10-history — no separate route, §9's own table names one U10
 * Finance route for both). Structural/copy fidelity against U10's own
 * frames lives in `design-fidelity/planning-fidelity.spec.ts` — this file
 * does not re-assert landmark order or exact prose.
 */

type FinanceState = { task: string; plan_reference: string };

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("PLN18-306 Finance task", () => {
	test.afterAll(() => restoreSite());

	test("Finance reaches the task from the Annual Plan record (FU-14)", async ({ page }) => {
		const state = resetFixture<FinanceState>("reset_finance_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, FINANCE, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await page.locator('[data-testid="pln-open-task"]').click();
		await expectReady(page, "finance");
		await expect(page).toHaveURL(new RegExp(`/procurement-planning/finance/${state.task}$`));
		await expect(page.locator('[data-testid="fnt-badge"]')).toHaveText("Awaiting Finance");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the requesting Planner reads the task without decision controls (segregation of duties)", async ({ page }) => {
		const state = resetFixture<FinanceState>("reset_finance_fixture");
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/procurement-planning/finance/${state.task}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "finance");
		await expect(page.locator('[data-testid="fnt-affordability"]')).toBeVisible();
		await expect(page.locator('[data-testid="fnt-confirm"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="fnt-return"]')).toHaveCount(0);
	});

	test("Finance confirms plan funding and the decision footer disappears", async ({ page }) => {
		const state = resetFixture<FinanceState>("reset_finance_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, FINANCE, PASSWORD);
		await page.goto(`/app/procurement-planning/finance/${state.task}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "finance");

		await expect(page.locator('[data-testid="fnt-confirm"]')).toBeVisible();
		await page.locator('[data-testid="fnt-confirm"]').click();
		await page.waitForURL(/procurement-planning$/);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);

		await page.goto(`/app/procurement-planning/finance/${state.task}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "finance");
		await expect(page.locator('[data-testid="fnt-confirm"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="fnt-return"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="fnt-history"] tbody tr')).toHaveCount(1);
	});

	test("Finance returns a plan to the planner with a reason", async ({ page }) => {
		const state = resetFixture<FinanceState>("reset_finance_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, FINANCE, PASSWORD);
		await page.goto(`/app/procurement-planning/finance/${state.task}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "finance");

		await page.locator('[data-testid="fnt-return"]').click();
		await expect(page.locator('[data-testid="fnt-return-dialog"]')).toBeVisible();
		await expect(page.locator('[data-testid="fnt-return-dialog"] .kt-dialog-title')).toHaveText("Return for correction?");
		await page.locator('[data-testid="fnt-return-reason"]').fill("Reduce the planned amount or obtain an approved Budget revision for the Digital Health line.");
		await page.locator('[data-testid="fnt-return-confirm"]').click();
		await page.waitForURL(/procurement-planning$/);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Finance reassesses funding for an Active Version and confirms it again", async ({ page }) => {
		const state = resetFixture<FinanceState>("reset_finance_reassessment_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, FINANCE, PASSWORD);
		await page.goto(`/app/procurement-planning/finance/${state.task}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "finance");

		await expect(page.locator("h1")).toHaveText("Reassess funding for Active Plan Version 1");
		await expect(page.locator('[data-testid="fnt-history"] tbody tr')).toHaveCount(2);
		await page.locator('[data-testid="fnt-confirm"]').click();
		await page.waitForURL(/procurement-planning$/);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("auditor reads with no decision controls", async ({ page }) => {
		const state = resetFixture<FinanceState>("reset_finance_fixture");
		await login(page, AUDITOR, PASSWORD);
		await page.goto(`/app/procurement-planning/finance/${state.task}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "finance");
		await expect(page.locator('[data-testid="fnt-confirm"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="fnt-return"]')).toHaveCount(0);
	});

	test("a departmental Author has no route to the Finance task", async ({ page }) => {
		const state = resetFixture<FinanceState>("reset_finance_fixture");
		await login(page, AUTHOR, PASSWORD);
		await page.goto(`/app/procurement-planning/finance/${state.task}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "finance");
		await expect(page.locator('[data-testid="pln-error"] h3')).toHaveText("This record isn't available to you");
	});

	test("an unrelated Author (Outsider) is masked the same way", async ({ page }) => {
		const state = resetFixture<FinanceState>("reset_finance_fixture");
		await login(page, OUTSIDER, PASSWORD);
		await page.goto(`/app/procurement-planning/finance/${state.task}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "finance");
		await expect(page.locator('[data-testid="pln-error"] h3')).toHaveText("This record isn't available to you");
	});
});
