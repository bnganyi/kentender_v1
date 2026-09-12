import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUTHOR, PASSWORD, collectConsoleErrors, expectReady, gotoRequisitions, resetFixture, restoreSite } from "./helpers";

/**
 * RUN-CHG-001 — Procurement Requisitions' editor Step 1 "Save draft"
 * (docs/mvp-1-r1/00_common/KenTender_RUN-CHG-001_Shared_Command_Runner_v1.0.md).
 *
 * Regression (latent, confirmed by the 2026-09-11 cross-module survey):
 * `onSaveDraft()` awaited `run()` and only afterwards, outside it, awaited
 * `load({ quiet: true })` — the reload that refreshes the editor's
 * `record_version` fields. `run()`'s `finally` cleared `pending` (and so
 * re-enabled "Save draft") as soon as `saveRequisitionSummary` itself
 * returned, before that reload had landed. A second Save fired in that
 * window would have read the pre-save `record_version` and been refused as
 * a stale write. The fix moves the reload to be the last thing awaited
 * inside the function passed to `run()`. This test widens the reload window
 * so the old behaviour cannot pass.
 */
type EditorState = { requisition: string };

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("Procurement Requisitions — Save draft stale-save race", () => {
	test.afterAll(() => restoreSite());

	test("a second Save right after the first is not refused as a stale write", async ({ page }) => {
		const state = resetFixture<EditorState>("reset_editor_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}`);
		await expectReady(page, "editor");
		await expect(page.locator('[data-testid="req-step-1"]')).toBeVisible();

		// The reload that repopulates record_version now lands 1.5s after the
		// save it follows.
		await page.route("**/api/method/kentender_procurement.procurement_requisitions.api.get_requisition_editor", async (route) => {
			const response = await route.fetch();
			await new Promise((resolve) => setTimeout(resolve, 1500));
			await route.fulfill({ response });
		});

		const titleField = page.locator("#req-title");
		const save = page.getByRole("button", { name: "Save draft" });
		const editorTitle = page.locator(".req-editor-title");

		// The value must genuinely differ from whatever the shared dev site
		// currently holds, or the server sees no change for an unrelated,
		// correct reason — use a fresh stamp each run.
		const stamp = Date.now();
		await titleField.fill(`Playwright drawdown package ${stamp}`);
		await save.click();

		// Old behaviour: `pending` (and so the Save button) would already have
		// cleared well inside the 1.5s reload delay.
		await expect(save).toBeDisabled();
		await page.waitForTimeout(800);
		await expect(save).toBeDisabled();
		await expect(editorTitle).toHaveText(`Playwright drawdown package ${stamp}`, { timeout: 10_000 });
		await expect(save).toBeEnabled({ timeout: 10_000 });
		await expect(page.locator('[data-testid="req-editor-error"]')).toHaveCount(0);

		// A second, genuinely different edit right after the first save's
		// reload has landed must be accepted, not refused as a stale write —
		// and the first edit must not have been silently reverted.
		await titleField.fill(`Playwright drawdown package ${stamp} v2`);
		await save.click();
		await expect(save).toBeDisabled({ timeout: 10_000 });
		await expect(editorTitle).toHaveText(`Playwright drawdown package ${stamp} v2`, { timeout: 10_000 });
		await expect(save).toBeEnabled({ timeout: 10_000 });
		await expect(page.locator('[data-testid="req-editor-error"]')).toHaveCount(0);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
