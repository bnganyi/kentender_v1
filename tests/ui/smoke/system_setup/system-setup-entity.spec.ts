import { test, expect, Page } from "@playwright/test";
import { loginAsAdministrator, login } from "../../helpers/auth";
import { collectPageErrors } from "../../helpers/designFidelity";
import { asFirstRun, resetWorld, restoreSite, systemManager } from "./helpers";

/**
 * CFG-CHG-002 v0.14 §10.2/§11.1 (tracker CFG14-5A) — the Procuring entity
 * screen in a real browser, on the CONFIG world. Structure is the fidelity
 * gate's job; this proves behaviour a component test cannot: first paint,
 * a real save and its refresh, the conflict and missing-authority states
 * with focus, no Frappe pop-up, and the narrow/200% layouts.
 *
 * Writes: the entity's PPRA registration, restored at the end of its test.
 */

async function openEntity(page: Page): Promise<string[]> {
	const errors = collectPageErrors(page);
	await page.goto("/app/system-setup#procuring-entity", { waitUntil: "domcontentloaded" });
	await page.waitForSelector('[data-testid="kt-setup-pe-record"]', { timeout: 20_000 });
	return errors;
}

async function noFrappeModal(page: Page): Promise<void> {
	// The refusal is ours, inline; a stock Frappe "Message" dialog is a defect
	// (AGENTS.md §6.10). Bounded grace wait: it mounts a tick after.
	await page.waitForTimeout(400);
	await expect(page.locator(".modal.show")).toHaveCount(0);
}

test.describe.serial("System setup — Procuring entity", () => {
	test.beforeAll(() => resetWorld("reset_config"));
	test.afterAll(() => restoreSite());

	test("first paint shows the entity, its fixed code and timezone, the setup record and the approval authority", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await openEntity(page);
		await expect(page.locator("h3").first()).toHaveText("Procuring entity");
		await expect(page.locator('[data-testid="kt-setup-pe-code"]')).toBeDisabled();
		await expect(page.locator('[data-testid="kt-setup-pe-tz"]')).toHaveValue("Africa/Nairobi");
		await expect(page.locator('[data-testid="kt-setup-pe-record"]')).toContainText("Top-level organisation unit");
		await expect(page.locator('[data-testid="kt-setup-pe-approval-status"]')).not.toHaveText("");
		await expect(page.locator('[data-testid="kt-setup-pe-submit"]')).toBeDisabled();
		// Never a generic ready badge.
		await expect(page.getByText(/^Ready$/)).toHaveCount(0);
		expect(errors, "console errors").toEqual([]);
	});

	test("a saved change is re-read from the server and survives reload; the saved notice follows the form", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await openEntity(page);
		const field = page.locator('[data-testid="kt-setup-pe-ppra"]');
		const original = await field.inputValue();
		const changed = `${original || "PPRA"}-PW`;
		try {
			await field.fill(changed);
			await page.click('[data-testid="kt-setup-pe-submit"]');
			const notice = page.locator('[data-testid="kt-setup-pe-success"]');
			await expect(notice).toHaveText("Site details saved");
			// Board order: the notice comes after the Save button, with its icon.
			const after = await page.evaluate(() => {
				const button = document.querySelector('[data-testid="kt-setup-pe-submit"]')!;
				const note = document.querySelector('[data-testid="kt-setup-pe-success"]')!;
				return !!(button.compareDocumentPosition(note) & Node.DOCUMENT_POSITION_FOLLOWING);
			});
			expect(after).toBe(true);
			await expect(notice.locator(".kt-notice-icon")).toHaveCount(1);
			await expect(page.locator('[data-testid="kt-setup-pe-submit"]')).toBeDisabled();
			await page.reload({ waitUntil: "domcontentloaded" });
			await expect(page.locator('[data-testid="kt-setup-pe-ppra"]')).toHaveValue(changed, { timeout: 20_000 });
		} finally {
			await page.locator('[data-testid="kt-setup-pe-ppra"]').fill(original);
			await page.click('[data-testid="kt-setup-pe-submit"]');
			await expect(page.locator('[data-testid="kt-setup-pe-success"]')).toBeVisible();
		}
		expect(errors, "console errors").toEqual([]);
	});

	test("a county/type conflict is refused inline, directly after the county answer, and nothing is saved", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await openEntity(page);
		const before = await page.locator('[data-testid="kt-setup-pe-type"]').inputValue();
		await page.selectOption('[data-testid="kt-setup-pe-type"]', "County Government");
		await page.click('[data-testid="kt-setup-pe-submit"]');
		const conflict = page.locator('[data-testid="kt-setup-pe-county-conflict"]');
		await expect(conflict).toHaveText("Conflict. The county answer does not match the entity details.");
		const placedAfterCounty = await page.evaluate(() => {
			const county = document.querySelector('[data-testid="kt-setup-pe-county"]')!;
			return county.nextElementSibling?.getAttribute("data-testid") === "kt-setup-pe-county-conflict";
		});
		expect(placedAfterCounty).toBe(true);
		await noFrappeModal(page);
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-setup-pe-type"]')).toHaveValue(before, { timeout: 20_000 });
		expect(errors.filter((e) => !/county answer does not match|status of 417/.test(e)), "console errors").toEqual([]);
	});

	test("first run: Configure without an approval authority shows the Missing notice, focuses the field and sends nothing", async ({ page }) => {
		await loginAsAdministrator(page);
		await asFirstRun(page);
		const sent: string[] = [];
		page.on("request", (request) => {
			if (request.url().includes("configure_procuring_entity")) sent.push(request.url());
		});
		await page.goto("/app/system-setup#procuring-entity", { waitUntil: "domcontentloaded" });
		await expect(page.locator("h3").first()).toHaveText("Configure this site", { timeout: 20_000 });
		await page.click('[data-testid="kt-setup-pe-submit"]');
		await expect(page.locator('[data-testid="kt-setup-pe-route-missing"]')).toHaveText(
			"Missing. Select who approves this entity's Annual Procurement Plan."
		);
		await expect(page.locator('[data-testid="kt-setup-pe-route"]')).toBeFocused();
		await expect(page.locator('[data-testid="kt-setup-pe-route"]')).toHaveAttribute("aria-invalid", "true");
		expect(sent).toEqual([]);
		await noFrappeModal(page);
	});

	test("narrow width and 200% text keep every field reachable with no horizontal scroll", async ({ page }) => {
		await loginAsAdministrator(page);
		for (const [width, zoom] of [[400, 1], [1440, 2]] as const) {
			await page.setViewportSize({ width, height: 900 });
			await openEntity(page);
			await page.evaluate((z) => ((document.documentElement.style as any).zoom = String(z)), zoom);
			const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
			expect(overflow, `horizontal overflow at ${width}px × ${zoom}`).toBeLessThanOrEqual(1);
			await page.locator('[data-testid="kt-setup-pe-submit"]').scrollIntoViewIfNeeded();
			await expect(page.locator('[data-testid="kt-setup-pe-submit"]')).toBeInViewport();
		}
	});

	test("keyboard alone reaches every entity control in reading order", async ({ page }) => {
		await loginAsAdministrator(page);
		await openEntity(page);
		await page.locator('[data-testid="kt-setup-pe-name"]').focus();
		const order: string[] = [];
		for (let i = 0; i < 8; i += 1) {
			order.push((await page.evaluate(() => document.activeElement?.getAttribute("data-testid") || document.activeElement?.getAttribute("name") || "")) as string);
			await page.keyboard.press("Tab");
		}
		// Disabled code and timezone are skipped; the rest follow the board.
		expect(order.slice(0, 5)).toEqual([
			"kt-setup-pe-name",
			"kt-setup-pe-type",
			"kt-setup-pe-ppra",
			"kt-setup-pe-route",
			"kt-pe-county",
		]);
	});

	test("a System Manager maintains the entity too (CFG11-EX-001), with the same screen", async ({ page }) => {
		const { user, password } = systemManager();
		await login(page, user, password);
		const errors = await openEntity(page);
		await expect(page.locator('[data-testid="kt-setup-pe-name"]')).toBeEditable();
		await expect(page.locator('[data-testid="kt-setup-pe-code"]')).toBeDisabled();
		await expect(page.locator('[data-testid="kt-setup-pe-record"]')).toBeVisible();
		expect(errors, "console errors").toEqual([]);
	});
});
