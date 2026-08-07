import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	assertStitchDeskChrome,
	assertStitchSectionTableChrome,
} from "../../helpers/stitchDeskChrome";

/**
 * DEM-UI-02 Create/Edit Demand — Stitch Desk canvas + live bind.
 * Route: /desk/demand-form
 */

const ROOT = '[data-testid="kt-dem-ui02-root"]';

test.describe("DEM-UI-02 Demand Form", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
	});

	test("Stitch regions, sections, footer, and live bind render", async ({ page }) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator(`${ROOT}.kt-stitch-canvas`)).toBeVisible();
		await expect(page.getByRole("heading", { name: "Create demand" })).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-context")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-section-need")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-section-delivery")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-section-items")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-section-estimate")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-what")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-why")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-add-item")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-footer")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-save")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-submit")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-docs-dropzone")).toBeVisible();
		await expect(page.locator("cdn.tailwindcss.com")).toHaveCount(0);
		// Returned banner hidden on create.
		await expect(page.getByTestId("kt-dem-ui02-return-notice")).toBeHidden();
		// Form Stitch places PE/OU context above the H1 — measure to header top (not H1).
		const gap = await page.evaluate(() => {
			const header = document.querySelector('[data-testid="kt-dem-ui02-header"]');
			const toolbar = document.querySelector('[data-testid="kt-cl-toolbar"]');
			if (!header || !toolbar) return null;
			return Math.round(
				header.getBoundingClientRect().top - toolbar.getBoundingClientRect().bottom,
			);
		});
		expect(gap, "toolbar-to-form-header gap").not.toBeNull();
		expect(gap as number).toBeLessThanOrEqual(28);
		expect(gap as number).toBeGreaterThanOrEqual(0);
	});

	test("Stitch chrome resists Desk button/select bleed", async ({ page }) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-dem-ui02-root",
			primaryCtaTestId: "kt-dem-ui02-submit",
			selectSelector: '[data-kt-dem-field="demand_route"]',
		});
	});

	test("Section headers are primary-fixed blue; cards square; inputs stay rounded", async ({
		page,
	}) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		await assertStitchSectionTableChrome(page, {
			sectionTestId: "kt-dem-ui02-section-need",
			roundedControlTestId: "kt-dem-ui02-title",
		});
		// Items section embeds a table — thead must match section header chrome.
		const itemsTheadBg = await page
			.getByTestId("kt-dem-ui02-section-items")
			.evaluate((el) => {
				const row = el.querySelector("thead tr") as HTMLElement | null;
				return row ? getComputedStyle(row).backgroundColor : "";
			});
		expect(itemsTheadBg).toBe("rgb(215, 226, 255)");
	});

	test("Focused inputs use Strategy/Budget soft #7bbeff lock, not navy/black", async ({ page }) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		const title = page.getByTestId("kt-dem-ui02-title");
		await title.focus();
		await expect
			.poll(async () => {
				return title.evaluate((el) => {
					const cs = getComputedStyle(el);
					return {
						borderColor: cs.borderColor,
						boxShadow: cs.boxShadow,
						outlineStyle: cs.outlineStyle,
					};
				});
			})
			.toMatchObject({
				outlineStyle: "none",
				borderColor: "rgb(123, 190, 255)",
			});
		const focusChrome = await title.evaluate((el) => {
			const cs = getComputedStyle(el);
			return { borderColor: cs.borderColor, boxShadow: cs.boxShadow };
		});
		// App-wide lock: #7bbeff border + 1px soft halo (Budget/Strategy).
		expect(focusChrome.borderColor).toBe("rgb(123, 190, 255)");
		expect(focusChrome.boxShadow).toMatch(/0px 0px 0px 1px/);
		expect(focusChrome.boxShadow).not.toMatch(/0px 0px 0px [2-9]px/);
		expect(focusChrome.boxShadow).toMatch(/123,\s*190,\s*255/);
		// Reject Civic Ledger near-black and navy primary slabs.
		expect(focusChrome.boxShadow).not.toMatch(/0,\s*11,\s*29/);
		expect(focusChrome.borderColor).not.toBe("rgb(0, 31, 72)");
	});

	test("Stitch surface layout: full-bleed header over surface canvas", async ({ page }) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		const layout = await page.evaluate(() => {
			const root = document.querySelector('[data-testid="kt-dem-ui02-root"]') as HTMLElement;
			const header = document.querySelector('[data-testid="kt-dem-ui02-header"]') as HTMLElement;
			const canvas = document.querySelector('[data-testid="kt-dem-ui02-form-canvas"]') as HTMLElement;
			const main = document.querySelector(".kt-cl-native-canvas > main") as HTMLElement;
			if (!root || !header || !canvas || !main) return null;
			const hr = header.getBoundingClientRect();
			const mr = main.getBoundingClientRect();
			return {
				rootBg: getComputedStyle(root).backgroundColor,
				canvasBg: getComputedStyle(canvas).backgroundColor,
				headerBg: getComputedStyle(header).backgroundColor,
				headerInset: Math.round(hr.left - mr.left),
				headerWidthRatio: hr.width / mr.width,
			};
		});
		expect(layout).not.toBeNull();
		expect(layout!.rootBg).toBe("rgb(249, 249, 254)");
		expect(layout!.canvasBg).toBe("rgb(249, 249, 254)");
		expect(layout!.headerBg).toBe("rgb(255, 255, 255)");
		expect(layout!.headerInset).toBeLessThanOrEqual(2);
		expect(layout!.headerWidthRatio).toBeGreaterThan(0.98);
	});

	test("Required-by date shows one Material calendar (native date is invisible overlay)", async ({
		page,
	}) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		const wrap = page.getByTestId("kt-dem-ui02-date-wrap");
		await expect(wrap.locator("[data-kt-dem-date-icon]")).toHaveCount(1);
		await expect(wrap.locator(".material-symbols-outlined")).toHaveCount(1);
		await expect(page.getByTestId("kt-dem-ui02-required-by")).toHaveAttribute("type", "text");
		const native = page.getByTestId("kt-dem-ui02-required-by-native");
		await expect(native).toHaveAttribute("type", "date");
		const nativeOpacity = await native.evaluate((el) => getComputedStyle(el).opacity);
		expect(Number(nativeOpacity)).toBe(0);
		// Visible display field must not be a second date control with its own glyph.
		await expect(wrap.locator('input[type="date"]')).toHaveCount(1);
	});

	test("Estimate amount uses 28px mono; labels stay sentence case", async ({ page }) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		// Seed a visible total via item amount.
		await page.locator('[data-kt-dem-item="description"]').first().fill("Compute lot");
		await page.locator('[data-kt-dem-item="requester_estimate"]').first().fill("455000000");
		await page.locator('[data-kt-dem-item="requester_estimate"]').first().blur();
		const est = await page.getByTestId("kt-dem-ui02-estimate-total").evaluate((el) => {
			const cs = getComputedStyle(el);
			return {
				text: (el.textContent || "").trim(),
				fontSize: cs.fontSize,
				fontFamily: cs.fontFamily,
				fontWeight: cs.fontWeight,
			};
		});
		expect(est.text.replace(/,/g, "")).toMatch(/455000000/);
		expect(est.fontSize).toBe("28px");
		expect(est.fontFamily).toMatch(/JetBrains Mono/i);
		expect(["700", "bold"]).toContain(est.fontWeight);
		const labelTransform = await page
			.locator('[data-testid="kt-dem-ui02-section-estimate"] label')
			.first()
			.evaluate((el) => getComputedStyle(el).textTransform);
		expect(labelTransform).toBe("none");
		await expect(
			page.locator('[data-testid="kt-dem-ui02-section-estimate"] label').first(),
		).toHaveText(/Requester estimate/i);
		await expect(page.getByTestId("kt-dem-ui02-confidence")).toBeVisible();
	});

	test("Add item row and cancel returns to workspace", async ({ page }) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		const rowsBefore = await page.locator("[data-kt-dem-item-row]").count();
		await page.getByTestId("kt-dem-ui02-add-item").click();
		await expect(page.locator("[data-kt-dem-item-row]")).toHaveCount(rowsBefore + 1);
		await page.getByTestId("kt-dem-ui02-cancel").click();
		await expect(page).toHaveURL(/demands-workspace/, { timeout: 15_000 });
	});
});
