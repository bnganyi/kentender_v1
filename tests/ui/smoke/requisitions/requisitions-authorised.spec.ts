import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUDITOR, HOPF, PASSWORD, collectConsoleErrors, expectReady, gotoRequisitions, resetFixture, restoreSite } from "./helpers";

/**
 * REQ-CHG-001 v1.6 Slice 3f — REQ-DES-10 Authorised Requisition, the Revoke
 * dialog, and Auditor read access, on the REQ-402 world.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("REQ-DES-10 Authorised Requisition", () => {
	test.afterAll(() => restoreSite());

	test("a read-only Auditor sees the full authorised handoff but no Revoke action", async ({ page }) => {
		const state = resetFixture<{ requisition: string; handoff: string }>("reset_authorised_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, AUDITOR, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}/authorised`);
		await expectReady(page, "authorised");

		await expect(page.locator(".req-eyebrow, .kt-eyebrow").first()).toContainText("AUTHORISED REQUISITION");
		await expect(page.locator(".kt-status", { hasText: "Authorised for Tender Preparation" })).toBeVisible();
		await expect(page.locator('[data-testid="req-reservations-table"] tbody tr')).toHaveCount(1);
		await expect(page.getByText("Not yet consumed")).toBeVisible();
		await expect(page.locator('[data-testid="req-revoke"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("HoPF revokes the unconsumed authorisation with a reason and the workspace reflects Revoked", async ({ page }) => {
		const state = resetFixture<{ requisition: string }>("reset_authorised_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}/authorised`);
		await expectReady(page, "authorised");

		await expect(page.locator('[data-testid="req-revoke"]')).toBeVisible();
		await page.locator('[data-testid="req-revoke"]').click();
		const dialog = page.locator('[data-testid="req-revoke-dialog"]');
		await expect(dialog).toBeVisible();
		await expect(dialog).toContainText("Revoke unconsumed authorisation?");
		await page.locator("#revoke-reason").fill("Playwright fixture: reverting this authorisation for a later test run.");
		await page.locator('[data-testid="req-revoke-dialog-confirm"]').click();
		await expect(dialog).toHaveCount(0);
		await expectReady(page, "workspace");
		const row = page.locator('[data-testid="req-your-requisitions"] tbody tr', { hasText: "Revoked" });
		expect(await row.count()).toBeGreaterThanOrEqual(1);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
