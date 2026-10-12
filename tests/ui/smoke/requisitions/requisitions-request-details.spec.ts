import { expect, test, Page } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUTHOR, CONTRIBUTOR, PASSWORD, collectConsoleErrors, expectReady, gotoRequisitions, resetFixture, restoreSite } from "./helpers";

/**
 * REQ-CHG-001 v1.15 — REQ-DES-03 Request details (Items, then Request summary)
 * and REQ-DES-04 Add item, as the lead author and as the isolated contributor.
 *
 * The flow the owner asked for: the quantity is typed ONCE, on the item rows;
 * the requested quantity is derived and read-only; the requester enters ONE
 * estimated total cost for each approved requirement; the item dialog opens from
 * the draft on screen and keeps unsaved page edits; the footer hint always
 * refers to the saved draft; nothing outside the chosen category says "laptop".
 *
 * Fixtures: `reset_draft` (nothing requested), `reset_items_added` (items
 * entered, no estimated total cost yet) and `reset_review_required`.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

type World = { plan_item_id: string; requisition: string };

const NOTHING_YET = "Add at least one item and enter its estimated total cost.";

const whole = (text: string) => Number(text.replace(/[^\d]/g, ""));

/** Open Add item and fill the shared details for a printer purchase; leave the quantities to the caller. */
async function openAddItem(page: Page) {
	await page.getByTestId("req-add-item").first().click();
	const dialog = page.getByTestId("req-add-dialog");
	await expect(dialog).toBeVisible();
	return dialog;
}

async function fillShared(page: Page, name: string) {
	await page.getByTestId("req-add-category").selectOption("Printer");
	await page.getByTestId("req-add-name").fill(name);
}

test.describe("REQ-DES-03 / REQ-DES-04", () => {
	test.afterAll(() => restoreSite());

	test("author: nothing requested at the start → quantity typed once → estimate entered once → Continue saves and checks the whole draft", async ({ page }) => {
		const world = resetFixture<World>("reset_draft");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");

		await expect(page.getByTestId("req-task-request_details")).toContainText("Needs attention");
		// Level 3 starts closed
		await expect(page.getByTestId("req-source-details")).not.toHaveAttribute("open", "");
		// no default and no second quantity control: the items are the only place a quantity is typed
		await expect(page.getByTestId("req-amount-quantity")).toHaveCount(0);
		await expect(page.getByTestId("req-use-full")).toHaveCount(0);
		await expect(page.getByText("Use full available amount")).toHaveCount(0);
		const estimates = page.getByTestId("req-amount-value");
		await expect(estimates).toHaveCount(2);
		for (let i = 0; i < 2; i++) await expect(estimates.nth(i)).toHaveValue("");
		await expect(page.getByTestId("req-requested-quantity").first()).toHaveText("0 Each");
		await expect(page.getByText("Add each item and enter its quantity here. You enter a quantity only once.")).toBeVisible();
		await expect(page.getByText("No items added.")).toBeVisible();
		await expect(page.getByTestId("req-attention-item")).toHaveText(NOTHING_YET);
		await expect(page.getByTestId("req-footer-status")).toHaveText("Fix what needs attention above to continue.");
		await expect(page.getByTestId("req-continue")).toBeDisabled();
		const pageLocation = await page.getByTestId("req-field-location").inputValue();

		// Add item: neutral wording, nothing prefilled, the page's own location
		const dialog = await openAddItem(page);
		await expect(dialog).toContainText("Add item");
		await expect(dialog).toContainText("Enter the shared item details once, then enter the quantity and intended use for each department.");
		await expect(dialog).toContainText("The standard requirements for the chosen category will be ready for review in the next task.");
		// A product name may appear only as a value of the chosen category (the category list itself), never in the dialog's own wording.
		const wording = await dialog.evaluate((el) => {
			const copy = el.cloneNode(true) as HTMLElement;
			copy.querySelectorAll("select").forEach((select) => select.remove());
			return copy.textContent || "";
		});
		expect(wording).not.toMatch(/laptop/i);
		await expect(page.getByTestId("req-add-category")).toHaveValue("");
		await expect(page.getByTestId("req-add-location")).toHaveValue(pageLocation);
		const quantities = page.getByTestId("req-add-quantity");
		await expect(quantities).toHaveCount(2);
		for (let i = 0; i < 2; i++) await expect(quantities.nth(i)).toHaveValue("");
		await expect(page.getByTestId("req-add-confirm")).toBeDisabled();

		// one department asks for 20 Each, typed once; the other is left out
		await fillShared(page, "Office printers");
		await quantities.first().fill("20");
		await page.getByTestId("req-add-use").first().fill("Printing for the department office staff");
		await page.getByTestId("req-add-row").nth(1).locator("label.kt-checkbox").click();
		await expect(page.getByTestId("req-add-confirm")).toHaveText("Add item");
		await page.getByTestId("req-add-confirm").click();
		await expect(dialog).toHaveCount(0);
		await expectReady(page, "record");

		// the requested quantity is derived from the item, shown read-only; the estimate is still the requester's to enter
		await expect(page.getByTestId("req-equipment-row")).toHaveCount(1);
		await expect(page.getByTestId("req-requested-quantity").first()).toHaveText("20 Each");
		await expect(estimates.first()).toHaveValue("");
		await expect(page.getByTestId("req-attention-item")).toContainText("Enter the estimated total cost for");
		await expect(page.getByTestId("req-continue")).toBeDisabled();

		// an unsaved estimate is marked as unsaved and the footer does not speak for it
		await estimates.first().fill("3000000");
		await expect(page.getByTestId("req-footer-status")).toHaveText("Unsaved changes. Save to check this request.");
		await expect(page.getByTestId("req-continue")).toBeEnabled();

		// Continue saves the whole draft, checks it and moves on: no quantity-mismatch message at any step
		await page.getByTestId("req-continue").click();
		await expect(page.locator('li[aria-current="step"]')).toContainText("Requirements");
		await expect(page.getByText(/Must be [\d,]+ Each|Requested equipment quantity/)).toHaveCount(0);

		// a reload shows every value that was entered, delivery location included
		await page.reload();
		await expectReady(page, "record");
		await page.getByTestId("req-task-request_details").click();
		await expect(page.getByTestId("req-field-location")).toHaveValue(pageLocation);
		await expect(page.getByTestId("req-equipment-row")).toHaveCount(1);
		await expect(page.getByTestId("req-requested-quantity").first()).toHaveText("20 Each");
		await expect(page.getByTestId("req-amount-value").first()).toHaveValue("3,000,000.00");
		await expect(page.locator('[data-state="unsaved"]')).toHaveCount(0);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("author: the item dialog opens from the draft on screen and keeps unsaved page edits", async ({ page }) => {
		const world = resetFixture<World>("reset_draft");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");

		const title = page.getByTestId("req-field-title");
		const latest = page.locator("#req-latest");
		const revisedTitle = `${await title.inputValue()} (phase 1)`;
		const saved = new Date(`${await latest.inputValue()}T00:00:00Z`);
		saved.setUTCDate(saved.getUTCDate() - 3);
		const earlier = saved.toISOString().slice(0, 10);
		await title.fill(revisedTitle);
		await latest.fill(earlier);
		await expect(page.locator('[data-state="unsaved"]')).toBeVisible();

		await openAddItem(page);
		// the dialog starts from what is on the page, saved or not
		await expect(page.locator("#req-add-latest")).toHaveValue(earlier);
		await fillShared(page, "Office printers");
		await page.getByTestId("req-add-quantity").first().fill("10");
		await page.getByTestId("req-add-use").first().fill("Printing for the department office staff");
		await page.getByTestId("req-add-row").nth(1).locator("label.kt-checkbox").click();
		await page.getByTestId("req-add-confirm").click();
		await expect(page.getByTestId("req-add-dialog")).toHaveCount(0);
		await expectReady(page, "record");

		// adding the item reloaded the page but did not clobber what was typed
		await expect(title).toHaveValue(revisedTitle);
		await expect(latest).toHaveValue(earlier);
		await expect(page.locator('[data-state="unsaved"]')).toBeVisible();
		await expect(page.getByTestId("req-footer-status")).toHaveText("Unsaved changes. Save to check this request.");

		// Save draft makes it saved: the marker goes, and a reload shows exactly what was entered
		await page.getByTestId("req-save").click();
		await expectReady(page, "record");
		await expect(page.locator('[data-state="unsaved"]')).toHaveCount(0);
		await page.reload();
		await expectReady(page, "record");
		await expect(page.getByTestId("req-field-title")).toHaveValue(revisedTitle);
		await expect(page.locator("#req-latest")).toHaveValue(earlier);
		await expect(page.getByTestId("req-equipment-row")).toHaveCount(1);
	});

	test("author: an item quantity above what remains, and an estimate above the allowance, are refused with the real limit and keep what was typed", async ({ page }) => {
		const world = resetFixture<World>("reset_draft");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");

		const dialog = await openAddItem(page);
		await fillShared(page, "Office printers");
		const quantities = page.getByTestId("req-add-quantity");
		const uses = page.getByTestId("req-add-use");
		const room = Number(await quantities.nth(1).getAttribute("placeholder"));
		await quantities.first().fill("5");
		await uses.first().fill("Printing for the department office staff");
		await quantities.nth(1).fill(String(room + 10));
		await uses.nth(1).fill("Printing for the second department staff");
		await page.getByTestId("req-add-confirm").click();
		// said once, beside its own row, naming the department and the real limit
		const refusal = page.getByTestId("req-add-row-error");
		await expect(refusal).toHaveCount(1);
		await expect(refusal).toHaveText(new RegExp(`can request at most ${room.toLocaleString("en-US")} Each for this requirement; you entered ${(room + 10).toLocaleString("en-US")}\\.$`));
		await expect(page.getByTestId("req-add-confirm")).toBeDisabled();
		// every value is kept and nothing was created
		await expect(quantities.nth(1)).toHaveValue(String(room + 10));
		await expect(uses.first()).toHaveValue("Printing for the department office staff");
		await dialog.getByRole("button", { name: "Cancel" }).click();
		await expect(dialog).toHaveCount(0);
		await expectReady(page, "record");
		await expect(page.getByTestId("req-equipment-row")).toHaveCount(0);

		// a valid item, then an estimate above the allowance
		await openAddItem(page);
		await fillShared(page, "Office printers");
		await page.getByTestId("req-add-quantity").first().fill("5");
		await page.getByTestId("req-add-use").first().fill("Printing for the department office staff");
		await page.getByTestId("req-add-row").nth(1).locator("label.kt-checkbox").click();
		await page.getByTestId("req-add-confirm").click();
		await expect(page.getByTestId("req-add-dialog")).toHaveCount(0);
		await expectReady(page, "record");

		const estimate = page.getByTestId("req-amount-value").first();
		await estimate.fill("999999999999.00");
		// Leaving the field reads it with separators; going back into it leaves the text as it is. Display only.
		await estimate.blur();
		await expect(estimate).toHaveValue("999,999,999,999.00");
		await estimate.focus();
		await expect(estimate).toHaveValue("999,999,999,999.00");
		await page.getByTestId("req-save").click();
		await expectReady(page, "record");
		await expect(page.getByTestId("req-amount-error")).toHaveText(/can enter at most KES [\d,]+\.\d\d for this requirement; you entered KES 999,999,999,999\.00\./);
		await expect(estimate).toHaveValue("999,999,999,999.00");

		// excess decimal places are refused, never rounded
		await estimate.fill("100.123");
		await page.getByTestId("req-save").click();
		await expectReady(page, "record");
		await expect(page.getByTestId("req-amount-error")).toContainText("exact amount in KES with at most 2 decimal places");
		await expect(estimate).toHaveValue("100.123");
	});

	test("author: editing an item recomputes the requested quantity; an item above what remains is refused beside its quantity", async ({ page }) => {
		const world = resetFixture<World>("reset_items_added");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");

		const itemQuantities = async () => {
			const rows = page.getByTestId("req-equipment-row");
			const out: number[] = [];
			for (let i = 0; i < (await rows.count()); i++) out.push(whole(await rows.nth(i).locator("td").nth(1).innerText()));
			return out;
		};
		const requested = async () => {
			const cells = page.getByTestId("req-requested-quantity");
			const out: number[] = [];
			for (let i = 0; i < (await cells.count()); i++) out.push(whole(await cells.nth(i).innerText()));
			return out;
		};
		const sum = (values: number[]) => values.reduce((a, b) => a + b, 0);
		const before = await itemQuantities();
		expect(before.length).toBeGreaterThan(0);
		// each line's requested quantity is exactly the sum of its items
		expect(sum(await requested())).toBe(sum(before));

		await page.getByTestId("req-edit-item").first().click();
		await page.getByTestId("req-item-quantity").fill("1000000");
		await page.getByTestId("req-item-dialog-confirm").click();
		await expect(page.getByTestId("req-item-quantity-error")).toHaveText(/can request at most [\d,]+ Each for this requirement; you entered 1,000,000\./);
		await expect(page.getByTestId("req-item-quantity")).toHaveValue("1000000");

		await page.getByTestId("req-item-quantity").fill(String(before[0] - 1));
		await page.getByTestId("req-item-dialog-confirm").click();
		await expect(page.getByTestId("req-item-dialog")).toHaveCount(0);
		await expectReady(page, "record");
		const after = await itemQuantities();
		expect(after[0]).toBe(before[0] - 1);
		expect(sum(await requested())).toBe(sum(after));
	});

	test("contributor: own estimate editable, the rest read-only (derived quantity included), only Save my changes", async ({ page }) => {
		const world = resetFixture<World>("reset_review_required");
		await login(page, CONTRIBUTOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");
		await expect(page.getByTestId("req-editor")).toHaveAttribute("data-mode", "contributor");
		// Request details is already complete here, so the editor opened at Requirements.
		await page.getByTestId("req-task-request_details").click();
		await expect(page.getByTestId("req-amounts").locator("thead")).toContainText("Estimated total cost");
		await expect(page.getByTestId("req-amounts").locator("thead")).toContainText("Access");
		await expect(page.getByTestId("req-amount-row").filter({ hasText: "Editable" })).toHaveCount(1);
		await expect(page.getByTestId("req-amount-row").filter({ hasText: "Read-only" })).toHaveCount(1);
		await expect(page.getByTestId("req-amount-value")).toHaveCount(1);
		await expect(page.getByTestId("req-amount-row").filter({ hasText: "Read-only" }).getByTestId("req-requested-quantity")).toContainText("Each");
		await expect(page.getByTestId("req-field-title")).toHaveCount(0);
		await expect(page.getByTestId("req-continue")).toHaveCount(0);
		await expect(page.getByTestId("req-save")).toHaveText("Save my changes");
		await page.getByTestId("req-save").click();
		await expect(page.getByTestId("req-saved")).toHaveText("Your changes are saved in the combined requisition.");
	});

	test("narrow layout: the estimated total cost can still be entered, in the row card", async ({ page }) => {
		const world = resetFixture<World>("reset_items_added");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await page.setViewportSize({ width: 390, height: 900 });
		await expectReady(page);
		const cardInputs = page.getByTestId("req-amount-value-card");
		await expect(cardInputs).toHaveCount(2);
		await expect(cardInputs.first()).toBeVisible();
		await expect(page.getByTestId("req-amount-value").first()).toBeHidden();
		await cardInputs.first().fill("12500000");
		await cardInputs.last().fill("9000000");
		await expect(page.locator('[data-state="unsaved"]')).toBeVisible();
		await page.getByTestId("req-save").click();
		await expect(page.locator('[data-state="unsaved"]')).toHaveCount(0);
		await expect(page.getByTestId("req-footer-status")).toHaveCount(0);
		await page.reload();
		await expectReady(page);
		await expect(page.getByTestId("req-amount-value-card").first()).toHaveValue(/12,?500,?000/);
	});

	test("a brand name in an item is named, beside the item, so \"Needs attention\" says what and where", async ({ page }) => {
		const world = resetFixture<World>("reset_draft");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");
		const dialog = await openAddItem(page);
		await page.getByTestId("req-add-category").selectOption("Printer");
		await page.getByTestId("req-add-name").fill("Dell XPS");
		const quantities = page.getByTestId("req-add-quantity");
		await quantities.first().fill("20");
		await page.getByTestId("req-add-use").first().fill("Printing for the department office staff");
		await page.getByTestId("req-add-row").nth(1).locator("label.kt-checkbox").click();
		await page.getByTestId("req-add-confirm").click();
		await expect(dialog).toHaveCount(0);
		await expectReady(page, "record");
		// said once, in the attention panel: the word and the item it is in; the item itself carries only a marker
		const items = page.getByTestId("req-attention-item");
		const brand = items.filter({ hasText: "“Dell” in the item “Dell XPS” is a brand or restrictive term." });
		await expect(brand).toHaveCount(1);
		await expect(brand).toContainText("Use supplier-neutral wording");
		await expect(page.getByTestId("req-item-flag").first()).toHaveText("Needs attention");
		await expect(page.getByTestId("req-equipment-row").first()).toHaveClass(/is-flagged/);
		// and the other thing that is missing is listed beside it, not scattered
		await expect(items.filter({ hasText: "Enter the estimated total cost for" })).toHaveCount(1);
		await expect(page.getByTestId("req-footer-status")).toHaveText("Fix what needs attention above to continue.");
		// choosing the finding goes to the item
		await brand.locator(".req-attention-link").click();
		await expect(page.getByTestId("req-equipment-row").first()).toBeInViewport();
	});
	test("a request with two kinds of item shows each kind as its own block, and either can be renamed and recategorised", async ({ page }) => {
		const world = resetFixture<World>("reset_draft");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");

		// printers for the first approved requirement only
		await openAddItem(page);
		await fillShared(page, "Office printers");
		await page.getByTestId("req-add-quantity").first().fill("10");
		await page.getByTestId("req-add-use").first().fill("Printing for the department office staff");
		await page.getByTestId("req-add-row").nth(1).locator("label.kt-checkbox").click();
		await page.getByTestId("req-add-confirm").click();
		await expect(page.getByTestId("req-add-dialog")).toHaveCount(0);
		await expectReady(page, "record");
		await expect(page.getByTestId("req-item-group")).toHaveCount(1);

		// monitors for the second one
		await openAddItem(page);
		await page.getByTestId("req-add-category").selectOption("Monitor");
		await page.getByTestId("req-add-name").fill("Office monitors");
		await page.getByTestId("req-add-row").first().locator("label.kt-checkbox").click();
		await page.getByTestId("req-add-quantity").nth(1).fill("5");
		await page.getByTestId("req-add-use").nth(1).fill("Displays for the records office");
		await page.getByTestId("req-add-confirm").click();
		await expect(page.getByTestId("req-add-dialog")).toHaveCount(0);
		await expectReady(page, "record");

		const groups = page.getByTestId("req-item-group");
		await expect(groups).toHaveCount(2);
		await expect(groups.nth(0).getByTestId("req-group-title")).toContainText("Office printers");
		await expect(groups.nth(1).getByTestId("req-group-title")).toContainText("Office monitors");

		// the second kind has its own Edit shared details; the first is untouched
		await groups.nth(1).getByTestId("req-edit-shared").click();
		await expect(page.getByTestId("req-shared-scope")).toContainText("1 approved requirement");
		await expect(page.getByTestId("req-add-name")).toHaveValue("Office monitors");
		await page.getByTestId("req-add-name").fill("Desktop monitors");
		await page.getByTestId("req-add-confirm").click();
		await expect(page.getByTestId("req-add-dialog")).toHaveCount(0);
		await expectReady(page, "record");
		await expect(groups.nth(0).getByTestId("req-group-title")).toContainText("Office printers");
		await expect(groups.nth(1).getByTestId("req-group-title")).toContainText("Desktop monitors");
		expect(errors, errors.join(" | ")).toEqual([]);
	});
});
