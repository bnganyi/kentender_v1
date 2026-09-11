import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { OFFICER, PASSWORD, collectConsoleErrors, expectReady, gotoTenderPreparation, resetFixture, restoreSite } from "./helpers";

/**
 * RUN-CHG-001 — Tender Preparation's editor: Save draft followed immediately
 * by Review and readiness
 * (docs/mvp-1-r1/00_common/KenTender_RUN-CHG-001_Shared_Command_Runner_v1.0.md).
 *
 * Regression (latent, confirmed by the 2026-09-11 cross-module survey):
 * `saveCurrentTask()` and `onEnterReview()` both awaited `run()` and only
 * afterwards, outside it, awaited `load({ quiet: true })` — the reload that
 * refreshes `editor.value.tender.record_version`. `run()`'s `finally`
 * cleared `pending` (re-enabling "Save draft") as soon as `save_tender_draft`
 * itself returned, before that reload had landed. Clicking "Review and
 * readiness" in that window would have sent the pre-save `record_version`
 * and been refused as a stale write with nobody else editing. The fix moves
 * each reload to be the last thing awaited inside the function passed to
 * `run()`. This test widens the reload window so the old behaviour cannot
 * pass.
 */
type Draft = { tender: string };

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("Tender Preparation — Save then Readiness stale-save race", () => {
	test.afterAll(() => restoreSite());

	test("Review and readiness right after Save draft is not refused as a stale write", async ({ page }) => {
		const fixture = resetFixture<Draft>("reset_draft_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page, `/${fixture.tender}`);
		await expectReady(page, "editor");
		await expect(page.locator('[data-testid="tpr-task-1"]')).toHaveClass(/is-active/);

		// Every editor reload now lands 1.5s after the save/readiness command it
		// follows.
		await page.route("**/api/method/kentender_procurement.tender_preparation.api.get_tender_editor", async (route) => {
			const response = await route.fetch();
			await new Promise((resolve) => setTimeout(resolve, 1500));
			await route.fulfill({ response });
		});

		const titleField = page.locator("#tpr-tender-title");
		const save = page.locator('[data-testid="tpr-save-draft"]');
		const reviewTab = page.locator('[data-testid="tpr-task-review"]');

		// The value must genuinely differ from whatever the shared dev site
		// currently holds, or the server sees no change for an unrelated,
		// correct reason — use a fresh stamp each run.
		const stamp = Date.now();
		await titleField.fill(`Playwright readiness race ${stamp}`);
		await save.click();

		// Old behaviour: `pending` (and so "Save draft") would already have
		// cleared well inside the 1.5s reload delay.
		await expect(save).toBeDisabled();
		await page.waitForTimeout(800);
		await expect(save).toBeDisabled();
		await expect(titleField).toHaveValue(`Playwright readiness race ${stamp}`, { timeout: 10_000 });
		await expect(save).toBeEnabled({ timeout: 10_000 });
		await expect(page.locator('[data-testid="tpr-editor-inline-error"]')).toHaveCount(0);

		// Review and readiness, clicked the instant Save re-enables: the old
		// behaviour would send the pre-save record_version and the server
		// would refuse it as a stale write, leaving the editor on Task 1 with
		// an inline error instead of entering the review screen.
		await reviewTab.click();
		await expect(page.locator('[data-testid="tpr-readiness-summary"]')).toBeVisible({ timeout: 10_000 });
		await expect(page.locator('[data-testid="tpr-editor-inline-error"]')).toHaveCount(0);

		// The edit made just before Readiness must not have been silently
		// reverted by the delayed reload either — reload from the server
		// (Task 1 is the default landing task) and confirm the persisted
		// value, not just client-side state.
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectReady(page, "editor");
		await expect(titleField).toHaveValue(`Playwright readiness race ${stamp}`, { timeout: 10_000 });

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
