import { test, expect } from "@playwright/test";

import { loginAsNdsFixtureAuthor, loginAsNdsFixtureReviewer } from "../../helpers/auth";
import {
	clearFixtures,
	collectConsoleErrors,
	expectScreen,
	gotoNeeds,
	resetFixture,
	selectContext,
} from "./helpers";

/**
 * NDS-908 — visual references at 1440 × 1024, the artboard size §11.1 fixes.
 *
 * §16.3 asks for a visual comparison for every approved artboard. This covers
 * the screens and states a regression would actually reach: layout drift, a
 * control reappearing that §1.1 removed, a status pill losing its variant.
 *
 * Baselines live beside this file in `<spec>-snapshots/` and are regenerated
 * with `--update-snapshots`. Two settings matter and are set per assertion
 * rather than globally, so a later spec cannot silently inherit them:
 *
 * - `maxDiffPixels` is an **absolute** budget, not a ratio, and that choice was
 *   forced by measurement rather than taste. A ratio scales with the shot, so a
 *   real but local change disappears into a full-screen denominator: at the 0.02
 *   ratio first tried — and still at 0.005 — adding `letter-spacing: 4px` to the
 *   page title passed unnoticed. Measured, that change moves 901 pixels, while a
 *   whole-card colour change moves 255,219. 300 sits well below a one-heading
 *   change and well above cross-machine antialiasing.
 * - `mask` covers the page rail's user identity (the logged-in actor's name)
 *   and every `[data-volatile]` value. The latter are audit instants, which are
 *   fixture-build time and so differ on every run: the NDS-DES-12a baseline
 *   failed by 477 pixels on its second run for exactly that reason. Masking the
 *   value is the honest fix — raising the pixel budget until it passed would
 *   have blinded the baseline to real changes at the same time.
 *
 * Deliberately not asserted here: the exact copy of each field. That is what
 * the functional specs check, and duplicating it in an image makes the
 * baseline churn on every wording change without adding coverage.
 *
 * NDS-CHG-001 v1.6 — every baseline is re-shot with no Procuring Entity
 * row/column anywhere (D4 removed the concept outright), and the NDS-DES-10
 * "Intake window" baseline is retired along with the screen and fixture it
 * covered: `IntakeWindowScreen.vue`, its `/intake-window` route and
 * `reset_intake_window_fixture` were all deleted in Phase 5/6 (D3 — NDS owns
 * no intake-configuration surface; "Needs submission" is a plain Open/Closed
 * flag read via `kentender_core.services.site_configuration`, not a window
 * with its own screen). Every Need reference below is read from its
 * fixture's own JSON return value, never hardcoded (FU-16/FU-17).
 */

const SHOT = { maxDiffPixels: 300, animations: "disabled" as const };

/** The rail shows the signed-in user, so mask it out of every comparison. */
function chrome(page: import("@playwright/test").Page) {
	return {
		...SHOT,
		mask: [page.locator(".kt-rail-mount"), page.locator("[data-volatile]")],
	};
}

test.describe.configure({ mode: "serial" });

test.describe("NDS-908 visual references at 1440 × 1024", () => {
	test.afterAll(() => clearFixtures());

	test("NDS-DES-01 workspace with rows", async ({ page }) => {
		resetFixture("reset_open_intake_fixture");
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page);
		await expectScreen(page, "workspace");
		await expect(page.locator('[data-testid="nds-shell"]')).toHaveScreenshot(
			"nds-des-01-workspace.png",
			chrome(page),
		);
		expect(errors).toEqual([]);
	});

	test("NDS-DES-03 need editor", async ({ page }) => {
		resetFixture("reset_open_intake_fixture");
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "/new");
		await expectScreen(page, "editor");
		await expect(page.locator('[data-testid="nds-shell"]')).toHaveScreenshot(
			"nds-des-03-editor.png",
			chrome(page),
		);
	});

	test("NDS-DES-06 departmental review task", async ({ page }) => {
		const need = resetFixture<{ need: string }>("reset_review_task_fixture").need;
		await loginAsNdsFixtureReviewer(page);
		await gotoNeeds(page, "");
		await selectContext(page);
		await expectScreen(page, "workspace");
		await page
			.locator(`[data-testid="nds-need-row"][data-reference="${need}"] [data-testid="nds-row-action"]`)
			.click();
		await expectScreen(page, "task");
		await expect(page.locator('[data-testid="nds-shell"]')).toHaveScreenshot(
			"nds-des-06-review-task.png",
			chrome(page),
		);
	});

	test("NDS-DES-12a withdrawal review, dependency blocked", async ({ page }) => {
		const need = resetFixture<{ need: string }>("reset_withdrawal_blocked_fixture").need;
		await loginAsNdsFixtureReviewer(page);
		await gotoNeeds(page, "");
		await selectContext(page);
		await expectScreen(page, "workspace");
		await page
			.locator(
				`[data-testid="nds-need-row"][data-reference="${need}"] [data-testid="nds-row-action"][data-action="withdrawal"]`,
			)
			.click();
		await expectScreen(page, "withdrawal");
		await expect(page.locator('[data-testid="nds-shell"]')).toHaveScreenshot(
			"nds-des-12a-withdrawal-blocked.png",
			chrome(page),
		);
	});

	test("NDS-DES-12b withdrawal review, dependency cleared", async ({ page }) => {
		const need = resetFixture<{ need: string }>("reset_withdrawal_cleared_fixture").need;
		await loginAsNdsFixtureReviewer(page);
		await gotoNeeds(page, "");
		await selectContext(page);
		await expectScreen(page, "workspace");
		await page
			.locator(
				`[data-testid="nds-need-row"][data-reference="${need}"] [data-testid="nds-row-action"][data-action="withdrawal"]`,
			)
			.click();
		await expectScreen(page, "withdrawal");
		await expect(page.locator('[data-testid="nds-shell"]')).toHaveScreenshot(
			"nds-des-12b-withdrawal-cleared.png",
			chrome(page),
		);
	});

	test("NDS-DES-11 reason dialog", async ({ page }) => {
		const need = resetFixture<{ need: string }>("reset_review_task_fixture").need;
		await loginAsNdsFixtureReviewer(page);
		await gotoNeeds(page, "");
		await selectContext(page);
		await expectScreen(page, "workspace");
		await page
			.locator(`[data-testid="nds-need-row"][data-reference="${need}"] [data-testid="nds-row-action"]`)
			.click();
		await expectScreen(page, "task");
		await page.locator('[data-testid="nds-decision-return"]').click();
		await expect(page.locator('[data-testid="nds-dialog-reason"]')).toBeVisible();
		// The dialog is outside the shell, so shoot the viewport for this one.
		await expect(page).toHaveScreenshot("nds-des-11-reason-dialog.png", chrome(page));
	});
});
