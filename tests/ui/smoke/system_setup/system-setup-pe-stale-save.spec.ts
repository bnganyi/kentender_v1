import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { collectPageErrors } from "../../helpers/designFidelity";

/**
 * RUN-CHG-001 — System Setup's Procuring entity tab (docs/mvp-1-r1/00_common/
 * KenTender_RUN-CHG-001_Shared_Command_Runner_v1.0.md).
 *
 * Regression (confirmed live 2026-09-11, not previously reported): `submit()`
 * emitted "updated" without awaiting it, and `SystemSetup.vue`'s `refreshSite()`
 * handler is async but fire-and-forget from a plain Vue emit — so `busy`
 * cleared and re-enabled "Save changes" before the parent's `site` prop (and
 * therefore `pe.value.expected_version`, a computed over that prop) had been
 * repopulated. A second Save fired in that window would have sent the
 * pre-save `expected_version` and been refused as a stale write. The fix
 * threads `refreshSite` in as an awaited `onUpdated` prop so `run()`'s
 * pending flag — bound to the Save button — cannot clear until the refresh
 * that carries the fresh stamp has landed. This test widens that window so
 * the old behaviour cannot pass.
 */
test.describe("System setup — Procuring entity stale-save race", () => {
	test("a second Save right after the first is not refused as a stale write", async ({ page }) => {
		/**
		 * "Save changes" disables itself once there is nothing dirty to save
		 * (by design — CFG-DES-01), so a completed save with no further edit
		 * legitimately leaves it disabled; that is not evidence either way for
		 * this regression. The actual defect was that `busy` (the pending
		 * guard) could clear *before* the post-save reload landed, so a second
		 * Save fired inside that window read `expected_version` off the still-
		 * stale `site` prop and would have been refused as a stale write. This
		 * test makes a second, genuinely different edit only after the first
		 * save's reload has visibly completed (the success notice) and
		 * confirms that second save is accepted.
		 */
		const errors = collectPageErrors(page);
		await loginAsAdministrator(page);
		await page.goto("/app/system-setup#procuring-entity", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="kt-setup-pe-submit"]', { timeout: 20_000 });

		// The reload that repopulates `expected_version` now lands 1.5s after
		// the save it follows.
		await page.route(
			"**/api/method/kentender_core.api.site_configuration_api.get_system_setup_workspace",
			async (route) => {
				const response = await route.fetch();
				await new Promise((resolve) => setTimeout(resolve, 1500));
				await route.fulfill({ response });
			}
		);

		const nameField = page.locator('[data-testid="kt-setup-pe-name"]');
		const submit = page.locator('[data-testid="kt-setup-pe-submit"]');
		const success = page.locator('[data-testid="kt-setup-pe-success"]');

		// The value must genuinely differ from whatever the shared dev site
		// currently holds, or `dirty` stays false for an unrelated, correct
		// reason — use a fresh stamp each run.
		const stamp = Date.now();
		await nameField.fill(`Ministry of Health — RUN-CHG-001 check ${stamp}`);
		await submit.click();

		// Old behaviour: `busy` (and so the button) would already have
		// cleared well inside the 1.5s reload delay.
		await expect(submit).toBeDisabled();
		await page.waitForTimeout(800);
		await expect(submit).toBeDisabled();
		await expect(success).toBeVisible({ timeout: 10_000 });

		await nameField.fill(`Ministry of Health — RUN-CHG-001 check ${stamp} v2`);
		await expect(submit).toBeEnabled();
		await submit.click();

		// A refused stale write leaves the button enabled (the form still
		// disagrees with the rejected server state) with the error banner
		// shown instead. Accepted, it re-disables once the round trip lands.
		await expect(submit).toBeDisabled({ timeout: 10_000 });
		await expect(page.locator('[data-testid="kt-setup-pe-error"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
