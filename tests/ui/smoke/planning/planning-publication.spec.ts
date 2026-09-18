import { expect, test } from "@playwright/test";

import { login, loginAsAdministrator } from "../../helpers/auth";
import {
	ACCOUNTING_OFFICER,
	PASSWORD,
	PLANNER,
	collectConsoleErrors,
	expectReady,
	gotoPlanning,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * PLN-CHG-001 v1.23 §10.12–§10.13 — what happens to an approved plan: the
 * publication result and its recovery paths, the plan update that succeeds it,
 * and the procurement progress recorded against the plan in force.
 *
 * Two whole tests from the v1.12 version of this file are gone rather than
 * retargeted, because what they proved no longer exists: the forecast cascade
 * dialog and the daily approaching-milestone job were both removed with the
 * forecast facility (PLN23-CHG-001). Keeping a retargeted shell of them would
 * assert that a deleted feature still behaves.
 */

type ActiveState = { plan_reference: string; plan_item_id: string; publication: string };

test.describe.configure({ mode: "serial", timeout: 180_000 });

async function gotoPlan(page: import("@playwright/test").Page, reference: string): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto(`/app/annual-procurement-plan/${reference}`, { waitUntil: "domcontentloaded" });
	await expectReady(page, "plan");
}

test.describe("Publication, recovery and the plan in force", () => {
	test.afterAll(() => restoreSite());

	test("an active plan states its approval and publication, and offers the progress against it", async ({ page }) => {
		const state = resetFixture<ActiveState>("reset_active_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlan(page, state.plan_reference);

		// §10.6 — once a version is in force, its approval and publication are
		// facts about it rather than steps still to take.
		const governance = page.locator('[data-testid="ppl-governance"]');
		await expect(governance).toContainText("Acknowledged");
		await expect(governance).toContainText("Adopted by the Accounting Officer");

		await page.locator('[data-testid="ppl-view-progress"]').click();
		await expectReady(page, "progress");
		// §10.13 — planned, covered and started; quantity and value together.
		const purchase = page.locator('[data-testid="prg-purchase"]').first();
		await expect(purchase).toContainText("Digital health infrastructure package");
		await expect(purchase).toContainText("KES 80,000,000");
		await expect(purchase).toContainText("Not started");
		// PLN22-AC-009 / PLN23-CHG-001 — the absence is the acceptance criterion.
		await expect(page.locator(".kt-pln .kt-shell")).not.toContainText("Completion");
		await expect(page.locator(".kt-pln .kt-shell")).not.toContainText("Forecast");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("preparing an update opens one draft successor, and the plan in force stays in force", async ({ page }) => {
		const state = resetFixture<ActiveState>("reset_active_fixture");
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");

		// §5.2.3 — the guarded successor start, from the workspace.
		await page.locator('[data-testid="pln-prepare-update"]').click();
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="ppl-context"]')).toContainText("Version 2");
		await expect(page.locator('[data-testid="ppl-context"]')).toContainText("Draft");
		await expect(page.locator('[data-testid="ppl-purchase-row"]')).toHaveCount(1);

		await gotoPlanning(page);
		await expectReady(page, "workspace");
		// The plan in force and its candidate are two rows, and the start
		// control is gone rather than disabled while one exists (§10.3).
		await expect(page.locator('[data-testid="pln-plan-row-current"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-plan-row-candidate"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-prepare-update"]')).toHaveCount(0);
	});

	test("an acknowledged publication offers no recovery; a failed one offers it to the technical operator alone", async ({ page }) => {
		const acknowledged = resetFixture<ActiveState>("reset_active_fixture");
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/publication/${acknowledged.publication}`);
		await expectReady(page, "publication");

		// §10.12 — four facts, four rows, none proving another.
		const rows = page.locator('[data-testid="pub-status-row"]');
		await expect(rows).toHaveCount(4);
		await expect(rows.nth(2)).toContainText("Published");
		await expect(page.locator('[data-testid="pub-retry"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pub-reconcile"]')).toHaveCount(0);

		const failed = resetFixture<ActiveState>("reset_publication_failed_fixture");
		await gotoPlan(page, failed.plan_reference);
		await page.locator('[data-testid="pln-open-publication"]').click();
		await expectReady(page, "publication");
		await expect(page.locator('[data-testid="pub-context"]')).toContainText("Publication failed");
		// The business actor never sees the technical recovery (§10.12).
		await expect(page.locator('[data-testid="pub-retry"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pub-responsible"]')).toContainText("Authorised technical operator");

		await loginAsAdministrator(page);
		await gotoPlanning(page, `/publication/${failed.publication}`);
		await expectReady(page, "publication");
		await page.locator('[data-testid="pub-retry"]').click();
		await expect(page.locator('[data-testid="pub-status-row"]').nth(2)).toContainText("Published", { timeout: 30_000 });
	});

	test("the Accounting Officer asks for a withdrawal; the approving authority decides it", async ({ page }) => {
		const failed = resetFixture<ActiveState>("reset_publication_failed_fixture");
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/publication/${failed.publication}`);
		await expectReady(page, "publication");

		await page.locator('[data-testid="pub-request-withdrawal"]').click();
		const dialog = page.locator('[data-testid="pub-withdrawal-dialog"]');
		await expect(dialog).toBeVisible();
		await expect(page.locator('[data-testid="pub-withdrawal-confirmation"]')).toHaveText("Confirmed not published");
		// A reason someone can act on, or no request.
		await expect(page.locator('[data-testid="pub-withdrawal-confirm"]')).toBeDisabled();
		await page.locator('[data-testid="pub-withdrawal-reason"]').fill(
			"A material defect was found in the approved content before it reached the destination."
		);
		await page.locator('[data-testid="pub-withdrawal-confirm"]').click();

		// The AO has asked; there is nothing more for them to do but wait.
		await expect(page.locator('[data-testid="pub-withdrawal-state"]')).toBeVisible({ timeout: 30_000 });
		await expect(page.locator('[data-testid="pub-request-withdrawal"]')).toHaveCount(0);
	});
});
