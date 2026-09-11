import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	AUTHOR,
	HOPF,
	OUTSIDER,
	PASSWORD,
	collectConsoleErrors,
	expectReady,
	gotoRequisitions,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * REQ-CHG-001 v1.6 Slice 3b — REQ-DES-02 Start Requisition, including the
 * unsupported-product and open-exists states.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("REQ-DES-02 Start IT-equipment Requisition", () => {
	test.afterAll(() => restoreSite());

	test("author sees the Planning source detail and prepares a Draft", async ({ page }) => {
		const state = resetFixture<{ plan_item_id: string; plan_reference: string }>("reset_eligible_item_world");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/new/${state.plan_item_id}`);
		await expectReady(page, "start");

		await expect(page.locator(".req-start-title")).toHaveText("Prepare Requisition from approved Plan Item");
		await expect(page.locator('[data-testid="req-planning-source"]')).toContainText(state.plan_item_id);
		await expect(page.locator('[data-testid="req-product-panel"]')).toContainText("IT Equipment");
		await expect(page.locator('[data-testid="req-allocations"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="req-prepare-requisition"]')).toBeVisible();

		await page.locator('[data-testid="req-prepare-requisition"]').click();
		await expectReady(page, "editor");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("a HoPF (not a departmental role) is not offered Prepare on an otherwise eligible item", async ({ page }) => {
		const state = resetFixture<{ plan_item_id: string }>("reset_eligible_item_world");
		await login(page, HOPF, PASSWORD);
		await gotoRequisitions(page, `/new/${state.plan_item_id}`);
		await expectReady(page, "start");
		await expect(page.locator('[data-testid="req-prepare-requisition"]')).toHaveCount(0);
	});

	test("an outsider author with no responsibility over this item's unit gets a masked not-found, never the projection", async ({ page }) => {
		const state = resetFixture<{ plan_item_id: string }>("reset_eligible_item_world");
		await login(page, OUTSIDER, PASSWORD);
		await gotoRequisitions(page, `/new/${state.plan_item_id}`);
		await expectReady(page, "start");
		// Planning's own `get_requisition_eligible_plan_item`'s
		// `_authorise_requisition_reader` gate refuses a reader with no
		// responsibility over THIS item's contributing units (masked
		// not-found, never a disclosing Forbidden message) — the Start
		// screen's own error card is what a masked read failure renders as.
		await expect(page.locator('[data-testid="req-start-error"]')).toBeVisible();
		await expect(page.locator('[data-testid="req-start-error"]')).toContainText("Procurement Requisitions could not be loaded.");
		await expect(page.locator('[data-testid="req-prepare-requisition"]')).toHaveCount(0);
	});

	test("starting on an already-open Requisition's Plan Item offers Open it, not a second Prepare", async ({ page }) => {
		const state = resetFixture<{ plan_item_id: string; requisition: string }>("reset_editor_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/new/${state.plan_item_id}`);
		await expectReady(page, "start");

		await expect(page.locator('[data-testid="req-start-open-exists"]')).toBeVisible();
		await expect(page.locator('[data-testid="req-prepare-requisition"]')).toHaveCount(0);
		await page.locator('[data-testid="req-start-open-existing"]').click();
		await expectReady(page, "editor");
		await expect(page).toHaveURL(new RegExp(`/procurement-requisitions/${state.requisition}$`));
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
