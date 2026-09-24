import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUTHOR, HOD, PASSWORD, collectConsoleErrors, expectReady, gotoRequisitions, resetFixture, restoreSite } from "./helpers";

/**
 * REQ-CHG-001 v1.11 slices 4d/4e — REQ-DES-05 Requirements and REQ-DES-06
 * Review and submit, as the lead author and as the direct HoD.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

type World = { plan_item_id: string; requisition: string; department_task?: string };

test.describe("REQ-DES-05 / REQ-DES-06", () => {
	test.afterAll(() => restoreSite());

	test("author: review the standard package, clear one suggestion, use it once → Reviewed → review → send", async ({ page }) => {
		const world = resetFixture<World>("reset_review_required");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");

		await expect(page.getByTestId("req-task-requirements")).toHaveAttribute("aria-selected", "true");
		await expect(page.getByTestId("req-requirements-issue")).toHaveText("Review the standard laptop requirements before continuing.");
		await expect(page.getByTestId("req-review-state")).toHaveText("Review required");
		await expect(page.getByTestId("req-technical-row")).toHaveCount(11);
		await expect(page.getByTestId("req-acceptance-row")).toHaveCount(5);
		await expect(page.getByTestId("req-footer-hint")).toHaveText("Review and use the selected standard requirements.");
		await expect(page.getByTestId("req-continue")).toBeDisabled();

		// edit one suggested value in the review copy, clear another
		await page.getByTestId("req-technical-row").filter({ hasText: "Memory" }).getByTestId("req-technical-edit").click();
		await page.getByTestId("req-technical-value").fill("32");
		await page.getByTestId("req-technical-confirm").click();
		await expect(page.getByTestId("req-technical-row").filter({ hasText: "Memory" })).toContainText("32");
		await page.getByTestId("req-technical-row").filter({ hasText: "Storage type" }).getByTestId("req-technical-clear").click();

		await page.getByTestId("req-use-selected").click();
		await expectReady(page, "record");
		await expect(page.getByTestId("req-review-state")).toHaveText("Reviewed");
		await expect(page.getByTestId("req-requirements-issue")).toHaveCount(0);
		await expect(page.getByText("Review required")).toHaveCount(0);
		await expect(page.getByTestId("req-technical-row")).toHaveCount(10);
		await expect(page.getByTestId("req-technical-row").filter({ hasText: "Memory" })).toContainText("32");
		await expect(page.getByTestId("req-task-requirements")).toContainText("Complete");

		await page.reload();
		await expectReady(page, "record");
		await expect(page.getByTestId("req-review-state")).toHaveText("Reviewed");

		await page.getByTestId("req-continue").click();
		await expect(page.getByTestId("req-task-review_submit")).toHaveAttribute("aria-selected", "true");
		await expect(page.getByTestId("req-review-result")).toHaveText("Ready to send for department approval");
		await expect(page.getByTestId("req-review-amounts")).toHaveAttribute("data-open", "false");
		await page.getByTestId("req-review-show-amounts").click();
		await expect(page.getByTestId("req-review-amounts")).toHaveAttribute("data-open", "true");
		await expect(page.getByTestId("req-review-services")).toContainText("None requested");

		await page.getByTestId("req-send").click();
		await expectReady(page, "record");
		await expect(page.getByTestId("req-editor")).toHaveCount(0);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("direct HoD: Submit to Procurement, quiet Other actions, Withdraw needs a reason", async ({ page }) => {
		const world = resetFixture<World>("reset_direct_hod_draft");
		await login(page, HOD, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");
		await page.getByTestId("req-task-review_submit").click();
		await expect(page.getByTestId("req-send")).toHaveText("Submit to Procurement");
		await page.getByTestId("req-other-actions").click();
		await expect(page.getByTestId("req-action-planning")).toBeVisible();
		await page.getByTestId("req-action-withdraw").click();
		const dialog = page.getByTestId("req-withdraw-dialog");
		await expect(dialog).toContainText("The requisition will close without using approved-plan amounts or reserving funding.");
		await page.getByTestId("req-withdraw-dialog-confirm").click();
		await expect(dialog).toContainText("Enter 20–1,000 characters.");
		await page.keyboard.press("Escape");
		await expect(dialog).toHaveCount(0);
	});
});
