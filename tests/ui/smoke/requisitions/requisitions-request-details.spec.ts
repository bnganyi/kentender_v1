import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUTHOR, CONTRIBUTOR, PASSWORD, collectConsoleErrors, expectReady, gotoRequisitions, resetFixture, restoreSite } from "./helpers";

/**
 * REQ-CHG-001 v1.11 slice 4c — REQ-DES-03 Request details and REQ-DES-04 Add
 * laptop request, as the lead author and as the isolated contributor.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

type World = { plan_item_id: string; requisition: string };

test.describe("REQ-DES-03 / REQ-DES-04", () => {
	test.afterAll(() => restoreSite());

	test("author: blocked footer → mismatch retained → both rows added → Request details Complete", async ({ page }) => {
		const world = resetFixture<World>("reset_draft");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");

		await expect(page.getByTestId("req-task-request_details")).toContainText("Needs attention");
		await expect(page.getByTestId("req-footer-hint")).toHaveText("Add the laptop request matching the requested quantities.");
		await expect(page.getByTestId("req-continue")).toBeDisabled();
		// Level 3 starts closed
		await expect(page.getByTestId("req-source-details")).not.toHaveAttribute("open", "");

		await page.getByTestId("req-add-laptops").first().click();
		const dialog = page.getByTestId("req-add-dialog");
		await expect(dialog).toBeVisible();
		await expect(page.getByTestId("req-add-confirm")).toHaveText("Add 2 equipment rows");
		await page.getByTestId("req-add-name").fill("Business laptops");
		const uses = page.getByTestId("req-add-use");
		for (let i = 0; i < (await uses.count()); i++) await uses.nth(i).fill("Field deployment and clinical training for department staff");
		const quantity = page.getByTestId("req-add-quantity").first();
		const wanted = await quantity.inputValue();
		await quantity.fill(String(Number(wanted) - 10));
		await page.getByTestId("req-add-confirm").click();
		await expect(page.getByTestId("req-add-mismatch")).toContainText(`is ${Number(wanted) - 10} Each but the approved requirement requests ${wanted} Each`);
		await expect(page.getByTestId("req-add-row-error")).toHaveText(`Must be ${wanted} Each`);
		await expect(page.getByTestId("req-add-confirm")).toBeDisabled();
		// every entered value is retained
		await expect(uses.first()).toHaveValue("Field deployment and clinical training for department staff");

		await quantity.fill(wanted);
		await page.getByTestId("req-add-confirm").click();
		await expect(dialog).toHaveCount(0);
		await expectReady(page, "record");
		await expect(page.getByTestId("req-equipment-row")).toHaveCount(2);
		await expect(page.getByTestId("req-task-request_details")).toContainText("Complete");
		await expect(page.getByTestId("req-task-requirements")).toContainText("Needs attention");
		await expect(page.getByTestId("req-continue")).toBeEnabled();
		await expect(page.getByTestId("req-edit-shared")).toBeVisible();

		// a reload shows the same saved state
		await page.reload();
		await expectReady(page, "record");
		await expect(page.getByTestId("req-equipment-row")).toHaveCount(2);

		await page.getByTestId("req-continue").click();
		await expect(page.getByTestId("req-task-requirements")).toHaveAttribute("aria-selected", "true");
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("author: a smaller amount offers Use full available amount; a save above what remains is refused inline", async ({ page }) => {
		const world = resetFixture<World>("reset_draft");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");
		const value = page.getByTestId("req-amount-value").first();
		const full = await value.inputValue();
		await expect(page.getByTestId("req-use-full")).toHaveCount(0);
		await value.fill("1000.00");
		await expect(page.getByTestId("req-use-full")).toHaveCount(1);
		await page.getByTestId("req-use-full").click();
		await expect(value).toHaveValue(full);

		await value.fill("999999999999.00");
		await page.getByTestId("req-save").click();
		await expectReady(page, "record");
		await expect(page.locator(".req-field-error").first()).toContainText("The amount still available from the approved purchase changed");
		await expect(value).toHaveValue("999999999999.00");
	});

	test("contributor: own row editable, the rest read-only, only Save my changes", async ({ page }) => {
		const world = resetFixture<World>("reset_review_required");
		await login(page, CONTRIBUTOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");
		await expect(page.getByTestId("req-editor")).toHaveAttribute("data-mode", "contributor");
		// Request details is already complete here, so the editor opened at Requirements.
		await page.getByTestId("req-task-request_details").click();
		await expect(page.getByTestId("req-amounts").locator("thead")).toContainText("Access");
		await expect(page.getByTestId("req-amount-row").filter({ hasText: "Editable" })).toHaveCount(1);
		await expect(page.getByTestId("req-amount-row").filter({ hasText: "Read-only" })).toHaveCount(1);
		await expect(page.getByTestId("req-field-title")).toHaveCount(0);
		await expect(page.getByTestId("req-continue")).toHaveCount(0);
		await expect(page.getByTestId("req-save")).toHaveText("Save my changes");
		await page.getByTestId("req-save").click();
		await expect(page.getByTestId("req-saved")).toHaveText("Your changes are saved in the combined requisition.");
	});
});
