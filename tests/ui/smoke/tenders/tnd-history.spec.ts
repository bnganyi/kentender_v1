import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUDITOR, HOPF, PASSWORD, collectConsoleErrors, expectReady, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.8 slice 7l — the history route (plan D22, no board). */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("Tender history", () => {
	test.afterAll(() => restoreSite());

	test("versions, decisions, documents, publication, open period and events; auditors see event detail", async ({ page }) => {
		const state = resetFixture("reset_published_fixture", { with_inquiry: true });
		const errors = collectConsoleErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/history`);
		await expectReady(page, "history");
		await expect(page.locator('[data-testid="tnd-history-versions"] tbody tr')).toHaveCount(1);
		expect(await page.locator('[data-testid="tnd-history-decisions"] tbody tr').count()).toBeGreaterThanOrEqual(3);
		expect(await page.locator('[data-testid="tnd-history-documents"] tbody tr').count()).toBeGreaterThanOrEqual(2);
		await expect(page.locator('[data-testid="tnd-history-channels"] tbody tr')).toHaveCount(4);
		await expect(page.locator('[data-testid="tnd-history-addenda"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="tnd-history-inquiries"] tbody tr')).toHaveCount(1);
		expect(await page.locator('[data-testid="tnd-history-events"] tbody tr').count()).toBeGreaterThanOrEqual(8);
		await expect(page.locator('[data-testid="tnd-history-events"] thead')).not.toContainText("Detail");
		await page.locator('[data-testid="tnd-back"]').click();
		await expectReady(page, "published");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);

		await login(page, AUDITOR, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/history`);
		await expectReady(page, "history");
		await expect(page.locator('[data-testid="tnd-history-events"] thead')).toContainText("Detail");
	});
});
