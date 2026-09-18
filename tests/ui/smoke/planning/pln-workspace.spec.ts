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
 * PLN-CHG-001 v1.23 — the Procurement Planning workspace's own behaviour: real
 * commands and their interactive re-render, navigation (direct load, reload,
 * back/forward), and error recovery. Structural and copy fidelity against the
 * artboards lives in `design-fidelity/planning-fidelity.spec.ts`; this file
 * does not re-assert landmark order or exact prose.
 *
 * Retargeted for v1.23: a departmental actor's own plan is its own section
 * rather than an entry in "Your actions", the plan card is a row per version,
 * and there is no Procuring Entity selector — the site is the entity.
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
		await expect(page.locator('[data-testid="pln-fy-select"]')).toBeVisible();

		// §10.3 U01-DEPARTMENT-AUTHOR — a departmental actor's page leads with
		// their own plan, so the empty state is that section, not a work item.
		const own = page.locator('[data-testid="pln-own-plan"]');
		await expect(own.locator('[data-testid="pln-own-plan-empty"]')).toHaveText("No departmental plan yet");
		await expect(page.locator('[data-testid="pln-start-departmental-plan"]')).toHaveText("Start departmental plan");
		await expect(page.locator('[data-testid="pln-count-label"]')).toHaveText("0 departmental plans");

		await page.locator('[data-testid="pln-start-departmental-plan"]').click();
		// The command runs and the page re-renders in place — no full reload.
		await expect(own.locator('[data-testid="pln-own-plan-action"]')).toHaveText("Continue departmental plan", { timeout: 30_000 });
		await expect(own).toContainText(OU_NAME);
		await expect(page.locator('[data-testid="pln-own-plan-empty"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("planner's Continue Plan on the Annual Plan card navigates to the plan record", async ({ page }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_accepted_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");

		const button = page.locator('[data-testid="pln-plan-action-current"]');
		await expect(button).toHaveText(/Continue plan|Continue Plan/);
		await button.click();
		await expect(page).toHaveURL(new RegExp(`/annual-procurement-plan/${state.plan_reference}$`));
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("auditor reads the register but is offered no work at all", async ({ page }) => {
		resetFixture("reset_accepted_fixture");
		await login(page, AUDITOR, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-action"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-departmental-table"] tbody tr')).toHaveCount(2);
		await expect(page.locator('[data-testid="pln-forbidden"]')).toHaveCount(0);
	});

	test("a responsibility-less user gets the Forbidden panel and nothing else", async ({ page }) => {
		await login(page, NOBODY, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-forbidden"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-context-strip"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-departmental-table"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-action"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-plan-row-current"]')).toHaveCount(0);
	});

	test("an author from another department sees only their own row, never the other unit's", async ({ page }) => {
		resetFixture("reset_accepted_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OUTSIDER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		const rows = page.locator('[data-testid="pln-departmental-table"] tbody tr');
		await expect(rows).toHaveCount(1);
		await expect(rows.first()).not.toContainText(OU_NAME);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("direct load, a full reload and browser back/forward all land on the same ready workspace", async ({ page }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_accepted_fixture");
		await login(page, PLANNER, PASSWORD);

		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-plan-row-current"]')).toBeVisible();

		await page.reload({ waitUntil: "domcontentloaded" });
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-plan-row-current"]')).toBeVisible();

		await page.locator('[data-testid="pln-plan-action-current"]').click();
		await expect(page).toHaveURL(new RegExp(`/annual-procurement-plan/${state.plan_reference}$`));

		await page.goBack();
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-plan-row-current"]')).toBeVisible();

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
