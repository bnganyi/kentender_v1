import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { ADMIN, expectScreen as expectBudgetScreen, gotoBudget, login as loginBudget } from "../budget/helpers";
import { AO, HOPF, PASSWORD, collectConsoleErrors, expectReady, expectSettled, gotoTenders, resetFixture, restoreSite } from "./helpers";

/**
 * TPR-CHG-001 v0.21 §10.18 / REQ-CHG-001 v1.20 §13.15 / PLN-CHG-001 v1.32 §10.19 — the unused allowance and funding after the Tender was
 * cancelled, walked as the real people through the real screens: the Accounting Officer's own cancellation registers the recovery (Pending),
 * the worker carries it out (the test site runs no scheduler, so the fixture runs it as the scheduler would), and every owner screen then says
 * the same thing in its own words. Nothing on any screen restores or releases anything by itself.
 */

test.describe.configure({ mode: "serial", timeout: 300_000 });

const PLN_PLANNER = "pw.req.pln.planner@example.test";

type Facts = { tender: string; tender_reference: string; recovery: string; requisition: string; requisition_reference: string; plan_item_id: string; plan_reference: string; recovery_status?: string; reason?: string };

test.describe("Cancellation recovery — the four screens", () => {
	test.afterAll(() => restoreSite());

	test("the AO's own cancellation shows Pending, and after the worker runs every screen says restored", async ({ page }) => {
		const state = resetFixture<Facts>("reset_cancel_fixture", { recommended: true });
		const errors = collectConsoleErrors(page);
		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/cancel`);
		await expectReady(page, "cancel");
		await expect(page.locator('[data-testid="tnd-cancel-warning"]')).toContainText("KenTender will restore its unused planning allowance");
		await page.locator('[data-testid="tnd-cancel-ground"]').selectOption("INADEQUATE_BUDGET");
		await page.locator('[data-testid="tnd-cancel-reason"]').fill("The confirmed budget available for this procurement is insufficient to proceed.");
		await page.locator('[data-testid="tnd-cancel-open-dialog"]').click();
		await page.locator('[data-testid="tnd-cancel-dialog-confirm"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Cancelled");
		const section = page.locator('[data-testid="tnd-resource-recovery"]');
		await expect(section).toHaveAttribute("data-status", "Pending");
		await expect(section.locator("h2")).toHaveText("Unused allowance and funding");
		await expect(page.locator('[data-testid="tnd-resource-recovery-label"]')).toHaveText("Restoring unused allowance and funding");
		await expect(page.locator('[data-testid="tnd-resource-recovery-explanation"]')).toContainText("cannot be used until restoration is complete");
		await expect(page.locator('[data-testid="tnd-resource-recovery-next"]')).toHaveCount(0);
		// identifiers stay under Technical details, collapsed
		await expect(page.locator('[data-testid="tnd-resource-recovery-technical"]')).not.toHaveAttribute("open", "");
		await page.reload();
		await expectReady(page, "cancel");
		await expect(page.locator('[data-testid="tnd-resource-recovery"]')).toHaveAttribute("data-status", "Pending");

		// Budget: the reservation is still held, and says so, until the whole recovery commits
		const pending = resetFixture<Facts & { budget_line: string }>("cancellation_recovery_facts", { tender: state.tender });
		await loginBudget(page, ADMIN);
		await gotoBudget(page, `/line/${pending.budget_line}`);
		await expectBudgetScreen(page, "line");
		await expect(page.locator('[data-testid="bud-line-reservation-recovery"]').first()).toHaveText("Being released after tender cancellation");
		await expect(page.locator('[data-testid="bud-line-recovery"]').first()).toContainText("Nothing is released from this screen.");
		await expect(page.locator('[data-testid="bud-line-cancellation-releases"]')).toHaveCount(0);

		// the Requisition and Planning say the same while it waits: held, restoring, nothing to start yet
		await login(page, HOPF, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-requisitions/${pending.requisition}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="req-resource-recovery"]')).toHaveAttribute("data-status", "Pending", { timeout: 30_000 });
		await expect(page.locator('[data-testid="req-resource-recovery-label"]')).toHaveText("Restoring unused allowance and funding");
		await expect(page.locator('[data-testid="req-resource-recovery-next"]')).toHaveCount(0);
		await login(page, PLN_PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${pending.plan_reference}/progress`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="prg-recovery"]').first()).toHaveAttribute("data-status", "Pending", { timeout: 30_000 });
		await expect(page.locator('[data-testid="prg-recovery-label"]').first()).toHaveText("Restoring unused allowance");
		await expect(page.locator('[data-testid="prg-recovery-next"]')).toHaveCount(0);

		const facts = resetFixture<Facts>("run_cancellation_recovery", { tender: state.tender });
		expect(facts.recovery_status).toBe("Completed");
		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/cancel`);
		await expectReady(page, "cancel");
		await expect(page.locator('[data-testid="tnd-resource-recovery"]')).toHaveAttribute("data-status", "Completed");
		await expect(page.locator('[data-testid="tnd-resource-recovery-label"]')).toHaveText("Unused allowance and funding restored");
		await expect(page.locator('[data-testid="tnd-resource-recovery-rows"] tbody tr')).toHaveCount(2);  // the fixture's requisition draws from two source departments
		await expect(page.locator('[data-testid="tnd-resource-recovery-rows"] tbody')).toContainText("KES");

		// the Requisition: authorised, its handoff used, and the same story in its own words
		await login(page, HOPF, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-requisitions/${facts.requisition}`, { waitUntil: "domcontentloaded" });
		const req = page.locator('[data-testid="req-resource-recovery"]');
		await expect(req).toHaveAttribute("data-status", "Completed", { timeout: 30_000 });
		await expect(page.locator('[data-testid="req-resource-recovery-label"]')).toHaveText("Unused allowance and funding restored");
		await expect(page.locator('[data-testid="req-resource-recovery-next"]')).toBeVisible();

		// Budget: the reservation is released and the line records the release, with its amount
		await loginBudget(page, ADMIN);
		await gotoBudget(page, `/line/${(facts as Facts & { budget_line: string }).budget_line}`);
		await expectBudgetScreen(page, "line");
		await expect(page.locator('[data-testid="bud-line-cancellation-release"]').first()).toBeVisible();
		await expect(page.locator('[data-testid="bud-line-cancellation-releases"]')).toContainText("KES");
		await expect(page.locator('[data-testid="bud-line-recovery"]')).toHaveCount(0);

		// Planning: the purchase's own row on the progress screen
		await login(page, PLN_PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${facts.plan_reference}/progress`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="pln-shell"]')).toHaveAttribute("data-screen", "progress", { timeout: 30_000 });
		await expect(page.locator('[data-testid="prg-recovery"]').first()).toHaveAttribute("data-status", "Completed", { timeout: 30_000 });
		await expect(page.locator('[data-testid="prg-recovery-label"]').first()).toHaveText("Unused allowance restored after tender cancellation");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("when an owner's records do not support the recovery, every screen says so with the real reason and offers no way round it", async ({ page }) => {
		const state = resetFixture<Facts>("reset_cancelled_recovery_fixture");
		const errors = collectConsoleErrors(page);
		const facts = resetFixture<Facts>("run_cancellation_recovery", { tender: state.tender, other_reason: true });
		expect(facts.recovery_status).toBe("Needs attention");
		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/cancel`);
		await expectReady(page, "cancel");
		const section = page.locator('[data-testid="tnd-resource-recovery"]');
		await expect(section).toHaveAttribute("data-status", "Needs attention");
		await expect(page.locator('[data-testid="tnd-resource-recovery-label"]')).toHaveText("Unused allowance and funding need attention");
		await expect(page.locator('[data-testid="tnd-resource-recovery-reason"]')).toContainText("released for another reason");
		await expect(page.locator('[data-testid="tnd-resource-recovery-next"]')).toHaveCount(0);
		await expect(section.locator("button")).toHaveCount(0);  // nothing here restores or releases anything

		await login(page, HOPF, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-requisitions/${facts.requisition}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="req-resource-recovery"]')).toHaveAttribute("data-status", "Needs attention", { timeout: 30_000 });
		await expect(page.locator('[data-testid="req-resource-recovery-reason"]')).toContainText("released for another reason");
		await expect(page.locator('[data-testid="req-resource-recovery-next"]')).toHaveCount(0);

		await login(page, PLN_PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${facts.plan_reference}/progress`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="pln-shell"]')).toHaveAttribute("data-screen", "progress", { timeout: 30_000 });
		await expect(page.locator('[data-testid="prg-recovery"]').first()).toHaveAttribute("data-status", "Needs attention", { timeout: 30_000 });
		await expect(page.locator('[data-testid="prg-recovery-label"]').first()).toHaveText("Unused allowance could not be restored");
		// the Plan Item itself says the same, so the Planner sees why the purchase cannot be drawn on
		await page.goto(`/app/procurement-plan-item/${facts.plan_item_id}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="pln-shell"]')).toHaveAttribute("data-screen", "plan-item", { timeout: 30_000 });
		await expect(page.locator('[data-testid="ppi-recovery"]').first()).toHaveAttribute("data-status", "Needs attention", { timeout: 30_000 });
		await expect(page.locator('[data-testid="ppi-recovery-label"]').first()).toHaveText("Unused allowance could not be restored");
		await expect(page.locator('[data-testid="ppi-recovery-next"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
