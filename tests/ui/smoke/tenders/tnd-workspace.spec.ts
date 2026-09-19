import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AO, AUDITOR, HOPF, NOBODY, OFFICER, OUTSIDER, PASSWORD, collectConsoleErrors, expectReady, failNextCall, gotoTenders, resetFixture, restoreSite } from "./helpers";

/**
 * TPR-CHG-001 v0.8 slice 7a — TPR-DES-01 Tenders workspace per role, in a
 * real browser on the Tenders Playwright world.
 */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-01 Tenders workspace", () => {
	test.afterAll(() => restoreSite());

	test("officer: Ready to start count, the Start Tender row, filters, direct load and reload", async ({ page }) => {
		const state = resetFixture("reset_start_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page);
		await expectReady(page, "workspace");

		await expect(page.locator(".tnd-h1")).toHaveText("Tenders");
		await expect(page.locator('[data-testid="tnd-count-ready"] .kt-kpi-value')).toHaveText("1");
		await expect(page.locator('[data-testid="tnd-count-ready"]')).toHaveClass(/is-live/);
		const row = page.locator('[data-testid="tnd-row-ready"]');
		await expect(row).toHaveCount(1);
		await expect(row.locator(".kt-status")).toHaveText("Ready to start");
		await expect(row.locator('[data-testid="tnd-action-start"]')).toHaveText("Start Tender");
		// absence: no template/manifest selector, no Procuring Entity switcher
		await expect(page.locator("select#tnd-status option")).toContainText(["All statuses"]);
		await expect(page.getByText("Template", { exact: true })).toHaveCount(0);

		// filters revalidate in place (no skeleton) and the empty result carries its own Clear filters
		await page.locator('[data-testid="tnd-filter-search"]').fill("nothing-matches-this");
		await expect(page.locator('[data-testid="tnd-empty"]')).toContainText("No Tenders match these filters.");
		await page.locator('[data-testid="tnd-empty"] button').click();
		await expect(page.locator('[data-testid="tnd-row-ready"]')).toHaveCount(1);

		await page.reload();
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="tnd-row-ready"]')).toHaveCount(1);
		await row.locator('[data-testid="tnd-action-start"]').click();
		await expectReady(page, "start");
		await expect(page).toHaveURL(new RegExp(`/tenders/new/${state.handoff}$`));
		await page.goBack();
		await expectReady(page, "workspace");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("HoPF: Awaiting your approval row with Review; AO: Awaiting your publication decision", async ({ page }) => {
		resetFixture("reset_awaiting_hopf_fixture");
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="tnd-count-awaiting_approval"] .kt-kpi-value')).toHaveText("1");
		const row = page.locator('[data-testid="tnd-row-awaiting_approval"]');
		await expect(row.locator(".kt-status")).toHaveText("Awaiting your approval");
		await expect(row.locator('[data-testid="tnd-action-review"]')).toHaveText("Review");
		await expect(page.locator('[data-testid="tnd-action-start"]')).toHaveCount(0);
		await row.locator('[data-testid="tnd-action-review"]').click();
		await expectReady(page, "approval");
	});

	test("AO sees the publication decision row and no Start action", async ({ page }) => {
		resetFixture("reset_awaiting_ao_fixture");
		await login(page, AO, PASSWORD);
		await gotoTenders(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="tnd-count-approved"] .kt-kpi-value')).toHaveText("1");
		const row = page.locator('[data-testid="tnd-row-approved"]');
		await expect(row.locator(".kt-status")).toHaveText("Awaiting your publication decision");
		await expect(row.locator('[data-testid="tnd-action-review_publication"]')).toHaveText("Review publication");
		await expect(page.locator('[data-testid="tnd-count-ready"]')).toHaveCount(0);
	});

	test("auditor reads the register with no counts and only View; outsider sees no row; nobody is Forbidden", async ({ page }) => {
		resetFixture("reset_published_fixture");
		await login(page, AUDITOR, PASSWORD);
		await gotoTenders(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="tnd-counts"]')).toHaveCount(0);
		const published = page.locator('[data-testid="tnd-row-published"]');
		expect(await published.count()).toBeGreaterThanOrEqual(1);
		await expect(published.first().locator('[data-testid="tnd-action-view"]')).toHaveText("View");
		await expect(page.locator('[data-testid="tnd-action-start"]')).toHaveCount(0);

		await login(page, OUTSIDER, PASSWORD);
		await gotoTenders(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="tnd-state-forbidden"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-queue"] tbody tr')).toHaveCount(0);

		await login(page, NOBODY, PASSWORD);
		await gotoTenders(page);
		await expectReady(page, "forbidden");
		const card = page.locator('[data-testid="tnd-state-forbidden"]');
		await expect(card).toContainText("You do not have access to Tenders");
		await expect(card).toContainText("Ask your KenTender administrator to assign one in System setup.");
		await expect(page.locator('[data-testid="tnd-queue"]')).toHaveCount(0);
	});

	test("a forced load failure shows the Load failure state with Try again, and recovers", async ({ page }) => {
		resetFixture("reset_start_fixture");
		await login(page, OFFICER, PASSWORD);
		await failNextCall(page, "get_tenders_workspace");
		await gotoTenders(page);
		await expectReady(page, "failure");
		await expect(page.locator('[data-testid="tnd-state-failure"]')).toContainText("Tenders could not be loaded");
		await page.locator('[data-testid="tnd-state-action"]').click();
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="tnd-row-ready"]')).toHaveCount(1);
	});
});
