import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { OFFICER, PASSWORD, collectConsoleErrors, expectNoMessageDialog, expectReady, gotoTenderPreparation, resetFixture, restoreSite } from "./helpers";

/**
 * TPR-DES-03 · Task 3, Task 4 and Task 5 (TPR-CHG-001 v0.6 §8.3–§8.5,
 * §13.5), slice 5d: the generated price schedule with no officer input, the
 * finite evaluation controls with their conditional fields, the generated
 * evidence table plus one additional officer row (add and remove), the
 * contract-term controls whose Links offer Active governed records only, and
 * Review Tender running readiness into the review screen.
 */

test.describe.configure({ mode: "serial", timeout: 240_000 });

type Draft = { tender: string; tender_reference: string };

test.describe("Tender Preparation — editor Task 3, Task 4 and Task 5", () => {
	test.afterAll(() => restoreSite());

	test("Task 3 is generated with no officer input and never copies the authorised value", async ({ page }) => {
		const fixture = resetFixture<Draft>("reset_draft_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page, `/${fixture.tender}`);
		await expectReady(page, "editor");
		await page.locator('[data-testid="tpr-task-3"]').click();
		const main = page.locator(".tpr-task-main");
		await expect(main.locator("input, select, textarea")).toHaveCount(0);
		await expect(main.locator('[data-testid="tpr-price-schedule"] tbody tr')).toHaveCount(1);
		await expect(main.locator('[data-testid="tpr-price-schedule"] th')).toHaveText(["Item", "Qty", "Unit", "Unit price", "Tax", "Line total"]);
		await expect(main).toContainText("The authorised internal value is not copied into this schedule.");
		await expect(main.locator('[data-testid="tpr-price-schedule"] tfoot')).toContainText("Tender total");
		await expect(page.locator('[data-testid="tpr-task-3"] .tpr-tag')).toContainText("Generated from 1 item");
		await expect(page.locator('[data-testid="tpr-save-draft"]')).toBeDisabled();
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Task 4 reveals conditional controls, adds and removes an additional evidence row linked to a visible requirement", async ({ page }) => {
		const fixture = resetFixture<Draft>("reset_draft_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page, `/${fixture.tender}`);
		await expectReady(page, "editor");
		await page.locator('[data-testid="tpr-task-4"]').click();
		await expect(page.locator("#tpr-min-contracts")).toHaveCount(0);
		await page.locator('.tpr-seg[aria-label="Past supply experience required"] label', { hasText: "Yes" }).click();
		await expect(page.locator("#tpr-min-contracts")).toBeVisible();
		await page.locator("#tpr-min-contracts").selectOption("2");
		await page.locator("#tpr-exp-years").selectOption("5");
		await page.locator('.tpr-seg[aria-label="Manufacturer authorisation required"] label', { hasText: "Yes" }).click();
		await page.locator('.tpr-seg[aria-label="Product datasheets or brochures required"] label', { hasText: "Yes" }).click();
		await page.locator('.tpr-seg[aria-label="After-sales support evidence required"] label', { hasText: "Yes" }).click();
		await expect(page.locator("#tpr-as-evidence")).toBeVisible();
		await page.locator("#tpr-as-evidence").selectOption({ index: 1 });
		await expect(page.locator("#tpr-as-evidence option")).not.toHaveCount(1); // finite listed values only
		await page.locator('[data-testid="tpr-save-draft"]').click();
		await expect(page.locator('[data-testid="tpr-task-4"] .tpr-tag')).toHaveText("Complete");
		await expectNoMessageDialog(page);

		const generatedRows = await page.locator('[data-testid="tpr-evidence"] tbody tr').count();
		expect(generatedRows).toBeGreaterThan(0);
		await expect(page.locator('[data-testid="tpr-evidence"] tbody tr').first().locator("td").nth(4)).not.toHaveText("");
		await page.locator('[data-testid="tpr-add-evidence"]').click();
		const dialog = page.locator('[data-testid="tpr-evidence-dialog"]');
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Add additional evidence");
		await dialog.locator("#tpr-ev-label").fill("Local service-centre letter");
		await dialog.locator("#tpr-ev-link-type").selectOption("Technical requirement");
		await expect(dialog.locator("#tpr-ev-link option").nth(1)).toContainText("TECH-");
		await dialog.locator("#tpr-ev-link").selectOption({ index: 1 });
		await dialog.locator('[data-testid="tpr-evidence-confirm"]').click();
		await expect(dialog).toHaveCount(0);
		const added = page.locator('[data-testid="tpr-evidence"] tbody tr', { hasText: "Local service-centre letter" });
		await expect(added).toHaveCount(1);
		await expect(added).toContainText("Additional officer evidence");
		await expect(page.locator('[data-testid="tpr-evidence"] tbody tr')).toHaveCount(generatedRows + 1);
		await added.locator("a", { hasText: "Remove" }).click();
		await expect(page.locator('[data-testid="tpr-evidence"] tbody tr')).toHaveCount(generatedRows);
		await expectNoMessageDialog(page);
	});

	test("Task 5 offers Active locations and offices only, saves, and Review Tender runs readiness into the review screen", async ({ page }) => {
		const fixture = resetFixture<Draft>("reset_draft_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page, `/${fixture.tender}`);
		await expectReady(page, "editor");
		await page.locator('[data-testid="tpr-task-5"]').click();
		await expect(page.locator(".tpr-section").first().locator(".kt-card-title")).toHaveText("Read-only summaries");
		await expect(page.locator(".tpr-section").first().locator("input, select")).toHaveCount(0);
		await expect(page.locator("#tpr-inspection option", { hasText: "Playwright — Requisitions Delivery Location" })).toHaveCount(1);
		await expect(page.locator("#tpr-office option", { hasText: "Playwright — Tender Preparation Contact Office" })).toHaveCount(1);
		await expect(page.locator("#tpr-inspection option").first()).toHaveText("Select an Active location");
		await page.locator("#tpr-inspection").selectOption({ label: "Playwright — Requisitions Delivery Location" });
		await page.locator("#tpr-payment").selectOption("30");
		// the percentage is conditional on the Yes/No switch (§8.5): No hides it, Yes reveals it
		await page.locator('.tpr-seg[aria-label="Performance security required"] label', { hasText: "No" }).click();
		await expect(page.locator("#tpr-ps-pct")).toHaveCount(0);
		await page.locator('.tpr-seg[aria-label="Performance security required"] label', { hasText: "Yes" }).click();
		await expect(page.locator("#tpr-ps-pct")).toBeVisible();
		await page.locator("#tpr-ps-pct").fill("10");
		await page.locator("#tpr-dd").fill("0.5");
		await page.locator("#tpr-dd-max").fill("10");
		await page.locator("#tpr-office").selectOption({ label: "Playwright — Tender Preparation Contact Office" });
		await page.locator('[data-testid="tpr-save-draft"]').click();
		await expect(page.locator('[data-testid="tpr-task-5"] .tpr-tag')).toHaveText("Complete");
		await expect(page.locator('[data-testid="tpr-continue"]')).toHaveText("Review Tender");
		await page.locator('[data-testid="tpr-continue"]').click();
		// Task 1 is still empty in this fixture: readiness ran and reports Blocking findings routed back to Task 1
		await expect(page.locator(".kt-page-title", { hasText: "Review Tender" })).toBeVisible();
		await expect(page.locator('[data-testid="tpr-readiness-counts"]')).not.toContainText("0 Blocking");
		await expect(page.locator('[data-testid="tpr-readiness-summary"] tbody tr')).toHaveCount(8);
		await expect(page.locator('[data-testid="tpr-submit"]')).toBeDisabled();
		const task1Finding = page.locator('[data-testid="tpr-finding"]', { hasText: "Open Task 1" }).first();
		await expect(task1Finding).toContainText("Blocking");
		await task1Finding.locator("a", { hasText: "Open Task 1" }).click();
		await expect(page.locator('[data-testid="tpr-task-1"]')).toHaveClass(/is-active/);
		await expectNoMessageDialog(page);
	});
});
