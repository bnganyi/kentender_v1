import { expect, type Page } from "@playwright/test";

/**
 * Choose a record in the shared record picker (kentender_core `RecordPicker`).
 *
 * Types `search` into the picker's field (a name, or a login: logins match, though they are never
 * shown), waits for the answer to that text (the list marks itself `is-updating` until it arrives, so
 * a stale list from the focus-open can never be clicked), and chooses the first row that can be
 * chosen. Returns the name it chose. `inputSelector` is the field's id, for example `#bop-add-member-person`.
 */
export async function pickRecord(page: Page, inputSelector: string, search: string): Promise<string> {
	const input = page.locator(inputSelector);
	await input.click();
	await input.fill(search);
	const list = page.locator('[data-testid="kt-picker-list"]');
	// the first search after a cold start can take several seconds; later ones well under one
	await expect(list).toHaveAttribute("aria-busy", "false", { timeout: 30_000 });
	const option = list.locator('[role="option"][aria-disabled="false"]').first();
	await expect(option).toBeVisible();
	const name = (await option.locator(".kt-picker-name").innerText()).trim();
	await option.click();
	await expect(input).toHaveValue(name);
	return name;
}

/** The reason a chosen record is not allowed, shown beneath the picker; null when there is none. */
export async function pickerReason(page: Page, scope = "body"): Promise<string | null> {
	const note = page.locator(`${scope} [data-testid="kt-picker-reason"]`);
	return (await note.count()) ? (await note.innerText()).trim() : null;
}

/**
 * Add a person in the picker that adds several (an inline, multiple-choice picker such as the Add members dialog's).
 *
 * Types `search` (a name, or a login), waits for the answer to that text, and presses Enter, which adds the first choosable row and
 * leaves the list and the field where they were. Returns the name it added.
 */
export async function addRecord(page: Page, inputSelector: string, search: string): Promise<string> {
	const input = page.locator(inputSelector);
	await input.fill(search);
	const list = page.locator('[data-testid="kt-picker-list"]');
	await expect(list).toHaveAttribute("aria-busy", "false", { timeout: 30_000 });
	const option = list.locator('[role="option"][aria-disabled="false"]').first();
	await expect(option).toBeVisible();
	const name = (await option.locator(".kt-picker-name").innerText()).trim();
	await input.press("Enter");
	await expect(page.locator('[role="status"][aria-live="polite"]', { hasText: `Added ${name}` })).toHaveCount(1);
	return name;
}
