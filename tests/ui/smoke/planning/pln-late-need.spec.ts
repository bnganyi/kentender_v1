import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	HOD,
	PASSWORD,
	PLANNER,
	acceptLateNeed,
	collectConsoleErrors,
	expectReady,
	gotoPlanning,
	purgeLateNeeds,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * A Need accepted after its department's plan was accepted — owner decision
 * 26 Sep 2026 ("Visible"). Found live: NDS-MOH-2027-0005 was accepted after
 * Digital Health's plan was, and every screen called the plan finished. The
 * department is now told on the Planning workspace, the plan itself and the
 * Need's own page, and every prompt clears once the update carries the Need.
 */

test.describe.configure({ timeout: 180_000 });

type Accepted = { dpp_reference: string };

async function expectNeedReady(page, reference: string): Promise<void> {
	const shell = page.locator('[data-testid="nds-shell"]');
	await expect(shell).toHaveAttribute("data-screen", "detail", { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-reference", reference);
	await expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
}

test.describe("A Need accepted after its department's plan", () => {
	// Each test's plan must start without the previous test's late Need in it.
	test.beforeEach(() => purgeLateNeeds());
	test.afterAll(() => restoreSite());

	test("the Head of Department is sent from the workspace and the Need to Create update, and every prompt clears", async ({ page }) => {
		const state = resetFixture<Accepted>("reset_accepted_fixture");
		const late = acceptLateNeed();
		const errors = collectConsoleErrors(page);
		await login(page, HOD, PASSWORD);

		// The workspace: the department's own task, named for the Need.
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		const task = page.locator('[data-testid="pln-action"]').filter({ hasText: `Add ${late} to the departmental plan` });
		await expect(task).toHaveCount(1);
		await expect(task.locator('[data-testid="pln-action-button"]')).toHaveText("Create update");
		await task.locator('[data-testid="pln-action-button"]').click();

		// The plan: the department's turn, not "Done" — and (owner instruction
		// 28 Sep 2026) the tracker and heading agree with it.
		await expect(page).toHaveURL(new RegExp(`/departmental-procurement-plan/${state.dpp_reference}$`));
		await expectReady(page, "dpp");
		const line = page.locator('[data-testid="pln-dpp-next-step-line"]');
		await expect(line).toContainText("Your turn");
		await expect(line).toContainText(`Add ${late} to this plan`);
		await expect(page.locator(".kt-journey-stage.is-current")).toContainText("Preparation");
		await expect(page.locator('[data-testid="pln-dpp-title"]')).not.toContainText("Review");
		await expect(page.locator('[data-testid="pln-dpp-create-update"]')).toBeVisible();

		// The Need's own page says it is not in the plan, and its next step
		// (NDS-CHG-001 v1.15 §5.5) links back to the plan.
		await page.goto(`/app/departmental-needs/${late}`, { waitUntil: "domcontentloaded" });
		await expectNeedReady(page, late);
		const fact = page.locator('[data-testid="nds-departmental-plan-status"]');
		await expect(fact).toContainText("Not in the plan yet");
		await expect(fact).toContainText("was accepted before this need.");
		const guidance = page.locator('[data-testid="nds-guidance"]');
		await expect(guidance).toContainText("Your turn");
		await expect(guidance).toContainText("Add this need to");
		await guidance.locator('[data-fix="update_departmental_plan"]').click();
		await expect(page).toHaveURL(new RegExp(`/departmental-procurement-plan/${state.dpp_reference}$`));
		await expectReady(page, "dpp");
		// Back returns to the Need, not to a record the plan page's route named.
		await page.goBack();
		await expectNeedReady(page, late);
		await expect(fact).toContainText("Not in the plan yet");
		await expect(guidance).toContainText("Add this need to");
		await page.goForward();
		await expectReady(page, "dpp");

		// Create update carries the Need into a new draft; the plan's turn moves on.
		await page.locator('[data-testid="pln-dpp-create-update"]').click();
		await expect(page.locator('[data-testid="pln-dpp-create-update"]')).toHaveCount(0, { timeout: 30_000 });
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="pln-dpp-table"]')).toContainText("Late departmental requirement");
		await expect(line).not.toContainText(`Add ${late} to this plan`);

		// …and neither the workspace nor the Need still asks for it.
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-action"]').filter({ hasText: `Add ${late}` })).toHaveCount(0);
		await page.goto(`/app/departmental-needs/${late}`, { waitUntil: "domcontentloaded" });
		await expectNeedReady(page, late);
		await expect(page.locator('[data-testid="nds-departmental-plan-status"]')).toHaveCount(0);

		expect(errors).toEqual([]);
	});

	test("the Planner reads it as waiting on the department, with no Create update", async ({ page }) => {
		const state = resetFixture<Accepted>("reset_accepted_fixture");
		const late = acceptLateNeed();
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/departmental-procurement-plan/${state.dpp_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "dpp");
		const line = page.locator('[data-testid="pln-dpp-next-step-line"]');
		await expect(line).toContainText(`Waiting for the department to add ${late} to its plan`);
		await expect(page.locator('[data-testid="pln-dpp-create-update"]')).toHaveCount(0);
		expect(errors).toEqual([]);
	});
});
