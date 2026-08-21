import { test, expect, Locator, Page } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohPlanningOfficer,
	loginAsMohPlanningReviewer,
	preparePlanningGate03,
	preparePlanningGate04,
	preparePlanningGate05Approval,
} from "../../helpers/planningRoles";

/**
 * PLN-NFR-004 — labelled controls, keyboard, visible focus, error association.
 * Not a WCAG 2.1 AA / axe-core certification.
 */

async function visibleFocusChrome(locator: Locator) {
	const chrome = await locator.evaluate((el) => {
		const cs = getComputedStyle(el);
		return {
			borderColor: cs.borderColor,
			outlineStyle: cs.outlineStyle,
			boxShadow: cs.boxShadow,
		};
	});
	expect(
		chrome.borderColor !== "rgba(0, 0, 0, 0)" ||
			chrome.outlineStyle !== "none" ||
			(chrome.boxShadow !== "none" && chrome.boxShadow !== ""),
	).toBeTruthy();
}

async function assertAssociatedError(page: Page, field: string, root: string) {
	const ctrl = page.locator(`${root} [data-kt-field="${field}"]`).first();
	const slot = page.locator(`${root} [data-kt-field-error="${field}"]`).first();
	await expect(slot).toBeVisible({ timeout: 15_000 });
	await expect(ctrl).toHaveAttribute("aria-invalid", "true");
	const describedBy = await ctrl.getAttribute("aria-describedby");
	expect(describedBy).toBeTruthy();
	const slotId = await slot.getAttribute("id");
	expect(slotId).toBeTruthy();
	expect(describedBy!.split(/\s+/)).toContain(slotId);
	await expect(page.getByRole("dialog", { name: /^Message$/i })).toHaveCount(0);
}

test.describe("PLN-NFR-004 Planning a11y", () => {
	test.describe.configure({ timeout: 120_000 });
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("UI-01: labeled filters, keyboard reach, visible focus", async ({ page }) => {
		await loginAsAdministrator(page);
		await page.waitForFunction(
			() =>
				Boolean(
					(window as unknown as { frappe?: { call?: unknown } }).frappe &&
						(window as unknown as { frappe?: { call?: unknown } }).frappe?.call,
				),
			{ timeout: 30_000 },
		);
		await preparePlanningGate03(page);
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto("/desk/planning-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-pln-ui01-root"][data-kt-pln-live="1"]')).toBeVisible({
			timeout: 45_000,
		});

		const pe = page.locator("#kt-pln-filter-pe");
		const fy = page.locator("#kt-pln-filter-fy");
		await expect(page.locator('label[for="kt-pln-filter-pe"]')).toBeVisible();
		await expect(page.locator('label[for="kt-pln-filter-fy"]')).toBeVisible();
		await expect(pe).toHaveAttribute("aria-label", /Procuring Entity/i);
		await expect(fy).toHaveAttribute("aria-label", /Financial Year/i);

		const openPlan = page.getByTestId("kt-pln-ui01-primary-action");
		await openPlan.focus();
		await expect(openPlan).toBeFocused();
		await visibleFocusChrome(openPlan);
		await page.keyboard.press("Tab");
		const focused = await page.evaluate(() => {
			const el = document.activeElement as HTMLElement | null;
			return el
				? {
						tag: el.tagName,
						id: el.id || "",
						testid: el.getAttribute("data-testid") || "",
				  }
				: null;
		});
		expect(focused).not.toBeNull();
		expect(["A", "BUTTON", "INPUT", "SELECT", "TEXTAREA"]).toContain(focused!.tag);
	});

	test("UI-02: titled inputs; empty submit associates inline error", async ({ page }) => {
		await loginAsAdministrator(page);
		await page.waitForFunction(
			() =>
				Boolean(
					(window as unknown as { frappe?: { call?: unknown } }).frappe &&
						(window as unknown as { frappe?: { call?: unknown } }).frappe?.call,
				),
			{ timeout: 30_000 },
		);
		await preparePlanningGate03(page);
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto("/desk/procurement-plan-register", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-pln-ui02-root"][data-kt-pln-live="1"]')).toBeVisible({
			timeout: 45_000,
		});

		const title = page.getByTestId("kt-pln-ui02-title");
		await expect(page.locator('label[for="kt-pln-reg-title"]')).toBeVisible();
		await expect(page.locator('label[for="kt-pln-reg-ou"]')).toBeVisible();
		await title.focus();
		await expect(title).toBeFocused();
		await visibleFocusChrome(title);

		await page.locator('[data-kt-field="coordinating_org_unit"]').evaluate((el) => {
			(el as HTMLSelectElement).value = "";
		});
		await page.getByTestId("kt-pln-ui02-submit").click();
		await assertAssociatedError(
			page,
			"coordinating_org_unit",
			'[data-testid="kt-pln-ui02-root"]',
		);
	});

	test("UI-06: required override error is associated", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate04(page, { withPlanItem: true });
		expect(prep.plan_item).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-item-editor?plan_item=${encodeURIComponent(prep.plan_item || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator('[data-testid="kt-pln-ui06-root"][data-kt-pln-live="1"]')).toBeVisible({
			timeout: 45_000,
		});

		await page.locator('[data-testid="kt-pln-ui06-root"] [data-kt-pln-field="procurement_method"]').selectOption(
			"Restricted tender",
		);
		await page.locator('[data-kt-field="method_override_grounds"]').fill("");
		await page.locator('[data-kt-field="method_override_reason"]').fill("");
		await page.locator('[data-kt-field="method_override_evidence"]').fill("");
		await page.getByTestId("kt-pln-ui06-save-draft").click();
		await assertAssociatedError(page, "method_override_grounds", '[data-testid="kt-pln-ui06-root"]');
	});

	test("UI-08: status text visible; return comment error associated", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningReviewer(page);
		await page.goto(
			`/desk/procurement-plan-review?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator('[data-testid="kt-pln-ui08-root"]')).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByText("Finance Confirmed", { exact: true })).toBeVisible();
		await expect(page.locator('label[for="kt-pln-decision-comment"]')).toBeVisible();

		await page.getByTestId("kt-pln-ui08-return").click();
		await assertAssociatedError(page, "decision_comment", '[data-testid="kt-pln-ui08-root"]');
	});
});
