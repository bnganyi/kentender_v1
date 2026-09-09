import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { HOPF, OFFICER, PASSWORD, expectReady, gotoTenderPreparation, resetFixture, restoreSite } from "./helpers";

/**
 * TPR-CHG-001 v0.6 Phase 7 (TPR-702) — one full-page 1440×1024 screenshot
 * per artboard section, saved to docs/mvp-1-r1/07_std_configuration/
 * evidence/v0_6/ (Requisitions' own precedent). Not a correctness check —
 * every assertion is already proven by the slice and fidelity specs; this is
 * a capture pass only, kept as its own file so it never blocks a gate.
 */

const DIR = "docs/mvp-1-r1/07_std_configuration/evidence/v0_6";

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("Evidence capture", () => {
	test.afterAll(() => restoreSite());

	test("s-workspace and s-start", async ({ page }) => {
		const fixture = resetFixture<{ handoff: string }>("reset_workspace_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page);
		await expectReady(page, "workspace");
		await page.screenshot({ path: `${DIR}/s-workspace.png`, fullPage: true });
		await gotoTenderPreparation(page, `/new/${fixture.handoff}`);
		await expectReady(page, "start");
		await expect(page.locator('[data-testid="tpr-start-confirm"]')).toBeVisible();
		await page.screenshot({ path: `${DIR}/s-start.png`, fullPage: true });
	});

	test("s-task1 … s-task5, s-task2-dialog, s-review", async ({ page }) => {
		const fixture = resetFixture<{ tender: string }>("reset_complete_draft_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page, `/${fixture.tender}`);
		await expectReady(page, "editor");
		for (const n of [1, 2, 3, 4, 5]) {
			await page.locator(`[data-testid="tpr-task-${n}"]`).click();
			await expect(page.locator(`[data-testid="tpr-task-${n}"]`)).toHaveClass(/is-active/);
			await page.screenshot({ path: `${DIR}/s-task${n}.png`, fullPage: true });
			if (n === 2) {
				await page.locator('[data-testid="tpr-upstream-trigger"]').click();
				await expect(page.locator(".kt-dialog-title")).toBeVisible();
				await page.screenshot({ path: `${DIR}/s-task2-dialog.png`, fullPage: true });
				await page.locator('[data-testid="tpr-upstream-dialog"] button', { hasText: "Cancel" }).click();
			}
		}
		await page.locator('[data-testid="tpr-task-review"]').click();
		await expect(page.locator('[data-testid="tpr-readiness-summary"]')).toBeVisible();
		await page.screenshot({ path: `${DIR}/s-review.png`, fullPage: true });
	});

	test("s-approval and s-approval-dialog", async ({ page }) => {
		const fixture = resetFixture<{ task: string }>("reset_submitted_fixture");
		await login(page, HOPF, PASSWORD);
		await gotoTenderPreparation(page, `/task/${fixture.task}`);
		await expectReady(page, "task");
		await page.screenshot({ path: `${DIR}/s-approval.png`, fullPage: true });
		await page.locator('[data-testid="tpr-return"]').click();
		await expect(page.locator(".kt-dialog-title")).toBeVisible();
		await page.screenshot({ path: `${DIR}/s-approval-dialog.png`, fullPage: true });
	});

	test("s-approved and s-approved-dialog", async ({ page }) => {
		const fixture = resetFixture<{ tender: string }>("reset_approved_fixture");
		await login(page, HOPF, PASSWORD);
		await gotoTenderPreparation(page, `/${fixture.tender}/approved`);
		await expectReady(page, "approved");
		await page.screenshot({ path: `${DIR}/s-approved.png`, fullPage: true });
		await page.locator('[data-testid="tpr-reopen"]').click();
		await expect(page.locator(".kt-dialog-title")).toBeVisible();
		await page.screenshot({ path: `${DIR}/s-approved-dialog.png`, fullPage: true });
	});
});
