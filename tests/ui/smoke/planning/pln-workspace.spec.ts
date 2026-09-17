import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	AUDITOR,
	AUTHOR,
	NOBODY,
	OUTSIDER,
	OU_NAME,
	PASSWORD,
	PLANNER,
	collectConsoleErrors,
	expectFixtureYear,
	expectReady,
	gotoPlanning,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * PLN-CHG-001 v1.18 (PLN18-302) — the Procurement Planning workspace's own
 * behaviour: real §8 commands and their interactive re-render, navigation
 * (direct load, reload, back/forward), and error recovery. Structural/copy
 * fidelity against U01/U21 lives in `design-fidelity/planning-fidelity.spec.ts`
 * — this file does not re-assert landmark order or exact prose.
 *
 * Replaces the v1.12 `planning-workspace.spec.ts` (deleted with this row):
 * that file's testids (`pln-action-row`, `.pln-ready-headline`, `pln-pe-select`,
 * `pln-plan-summary`) no longer exist on the re-ported screen.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("PLN18-302 Procurement Planning workspace", () => {
	test.afterAll(() => restoreSite());

	test("author starts a departmental plan and sees the live re-render, no full reload", async ({ page }) => {
		resetFixture("reset_workspace_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expectFixtureYear(page);
		await expect(page.locator('[data-testid="pln-pe-select"]')).toHaveCount(0);

		const card = page.locator('[data-testid="pln-actionable"]');
		await expect(card).toHaveCount(1);
		await expect(card.locator(".kt-card-title")).toHaveText(/^No departmental plan yet for/);
		await expect(page.locator('[data-testid="pln-work-action-0"]')).toHaveText("Start departmental plan");
		await expect(page.locator('[data-testid="pln-count-label"]')).toHaveText("0 departmental plans");

		await page.locator('[data-testid="pln-work-action-0"]').click();
		await expect(card.locator(".kt-card-title")).toHaveText("Continue departmental plan", { timeout: 30_000 });
		await expect(page.locator('[data-testid="pln-work-action-0"]')).toHaveText("Continue");
		const planRow = page.locator('[data-testid="pln-departmental-plans"] tbody tr');
		await expect(planRow).toHaveCount(1);
		await expect(planRow).toContainText(OU_NAME);
		await expect(page.locator('[data-testid="pln-count-label"]')).toHaveText("1 departmental plan");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("planner's Continue Plan on the Annual Plan card navigates to the plan record", async ({ page }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_accepted_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");

		const button = page.locator('[data-testid="pln-plan-action-current"]');
		await expect(button).toHaveText("Continue Plan");
		await button.click();
		await expect(page).toHaveURL(new RegExp(`/annual-procurement-plan/${state.plan_reference}$`));
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("auditor reads the register but is offered no work at all", async ({ page }) => {
		resetFixture("reset_accepted_fixture");
		await login(page, AUDITOR, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-actionable"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-departmental-plans"] tbody tr')).toHaveCount(2);
		await expect(page.locator('[data-testid="pln-forbidden"]')).toHaveCount(0);
	});

	test("a responsibility-less user gets the Forbidden panel and nothing else", async ({ page }) => {
		await login(page, NOBODY, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-forbidden"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-context-strip"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-departmental-plans"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-actionable"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-annual-plan-card"]')).toHaveCount(0);
	});

	test("an author from another department sees only their own row, never the other unit's", async ({ page }) => {
		resetFixture("reset_accepted_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OUTSIDER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		const rows = page.locator('[data-testid="pln-departmental-plans"] tbody tr');
		await expect(rows).toHaveCount(1);
		await expect(rows.first()).not.toContainText(OU_NAME);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("direct load, a full reload and browser back/forward all land on the same ready workspace", async ({ page }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_accepted_fixture");
		await login(page, PLANNER, PASSWORD);

		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-annual-plan-card"]')).toBeVisible();

		await page.reload({ waitUntil: "domcontentloaded" });
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-annual-plan-card"]')).toBeVisible();

		await page.locator('[data-testid="pln-plan-action-current"]').click();
		await expect(page).toHaveURL(new RegExp(`/annual-procurement-plan/${state.plan_reference}$`));

		await page.goBack();
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-annual-plan-card"]')).toBeVisible();

		await page.goForward();
		await expect(page).toHaveURL(new RegExp(`/annual-procurement-plan/${state.plan_reference}$`));
	});

	test("a forced technical failure shows the load-error card and Try again recovers without a reload", async ({ page }) => {
		resetFixture("reset_workspace_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);

		let fail = true;
		await page.route("**/api/method/kentender_procurement.procurement_planning.api.get_planning_workspace", (route) => {
			if (fail) {
				fail = false;
				return route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ exc_type: "ValidationError" }) });
			}
			return route.continue();
		});

		await gotoPlanning(page);
		const error = page.locator('[data-testid="pln-error"]');
		await expect(error.locator("h3")).toHaveText("Procurement Planning could not be loaded");
		await expect(error).toContainText("Support reference:");

		await error.locator("button").click();
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-error"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
