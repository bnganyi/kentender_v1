import { test, expect } from "@playwright/test";
import {
	loginAsAdministrator,
	loginAsProcurementApprover,
} from "../../helpers/auth";
import {
	assertStitchDeskChrome,
	assertStitchSectionTableChrome,
} from "../../helpers/stitchDeskChrome";

/**
 * DEM-UI-05 / DEM-UI-05A — Procurement enrichment + Strategy assign drawer.
 * Route: /desk/demand-review/<name>
 */

const ROOT = '[data-testid="kt-dem-ui04-root"]';

async function prepareEnrichmentDemand(
	page: import("@playwright/test").Page,
): Promise<string> {
	await loginAsAdministrator(page);
	await page.goto("/desk", { waitUntil: "domcontentloaded" });
	const demandName = await page.evaluate(async () => {
		const r = await (
			window as unknown as {
				frappe: {
					call: (o: { method: string }) => Promise<{
						message?: { demand?: string; ok?: boolean };
					}>;
				};
			}
		).frappe.call({
			method: "kentender_procurement.demands.api.prepare_enrichment_ui05",
		});
		return r.message?.demand || "";
	});
	expect(demandName).toBeTruthy();
	return demandName;
}

test.describe("DEM-UI-05 Procurement Enrichment", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("Stitch regions, Assign drawer, Save, Send readiness", async ({ page }) => {
		const demandName = await prepareEnrichmentDemand(page);
		await page.context().clearCookies();
		await loginAsProcurementApprover(page);
		await page.goto(`/desk/demand-review/${demandName}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator(ROOT)).toHaveAttribute(
			"data-kt-dem-review-stage",
			"Procurement Enrichment",
		);
		await expect(page.getByTestId("kt-dem-record-header")).toBeVisible();
		await expect(page.getByTestId("kt-dem-stage")).toContainText(
			/Procurement enrichment/i,
		);
		await expect(page.getByTestId("kt-dem-stage")).toContainText(/Current/i);
		await expect(page.getByTestId("kt-dem-business-host")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui05-root")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05-section-business")).toBeVisible();
		// Stitch: Business Request is always expanded (not collapsible).
		await expect(page.getByTestId("kt-dem-ui05-business-body")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05-business-toggle")).toHaveCount(0);
		await expect(page.getByTestId("kt-dem-ui05-business-teaser")).toHaveCount(0);
		await expect(page.getByTestId("kt-dem-ui05-section-classify")).toBeVisible();
		// App-wide primary-fixed section heads + square cards (not muted drab bands).
		await assertStitchSectionTableChrome(page, {
			sectionTestId: "kt-dem-ui05-section-classify",
			roundedControlTestId: "kt-dem-ui05-category",
		});
		await assertStitchSectionTableChrome(page, {
			sectionTestId: "kt-dem-ui05-section-business",
		});
		await expect(page.getByTestId("kt-dem-ui05-category")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05-confirmed-estimate")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05-role-banner")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui05-section-items")).toBeVisible();
		// Stitch estimate band: underline Confirmed Estimate (not a white boxed input).
		const confirmedChrome = await page.getByTestId("kt-dem-ui05-confirmed-estimate").evaluate((el) => {
			const cs = getComputedStyle(el);
			const wrap = el.closest(".kt-dem-ui05-confirmed-estimate") as HTMLElement | null;
			const wcs = wrap ? getComputedStyle(wrap) : null;
			return {
				inputBorder: cs.borderWidth,
				inputBg: cs.backgroundColor,
				wrapBorderBottom: wcs?.borderBottomWidth || "",
				wrapBorderBottomColor: wcs?.borderBottomColor || "",
			};
		});
		expect(confirmedChrome.inputBorder === "0px" || confirmedChrome.inputBorder === "").toBe(true);
		expect(confirmedChrome.inputBg).toMatch(/rgba?\(0,\s*0,\s*0,\s*0\)|transparent/);
		expect(parseFloat(confirmedChrome.wrapBorderBottom || "0")).toBeGreaterThanOrEqual(2);
		expect(confirmedChrome.wrapBorderBottomColor).toMatch(/rgb\(0,\s*31,\s*72\)/);
		// Need Items edit rules (DIA-FR-046): Description/Qty/Unit/Unit Est. editable;
		// Total Est. computed. Soft rows — no number spinners; descriptions not clipped.
		const itemsBody = page.getByTestId("kt-dem-ui05-items-body");
		await expect(itemsBody.locator("tr")).toHaveCount(2, { timeout: 10_000 });
		const firstRow = itemsBody.locator("tr").first();
		const descInput = firstRow.locator('[data-kt-dem-enrich-item="description"]');
		await expect(descInput).toHaveValue(/High-performance compute cluster/i);
		const descOverflow = await descInput.evaluate((el: HTMLInputElement) => {
			return el.scrollWidth <= el.clientWidth + 2;
		});
		expect(descOverflow, "description must not clip in the cell").toBe(true);
		await expect(firstRow.locator('[data-kt-dem-enrich-item="confirmed_quantity"]')).toHaveValue(
			"2",
		);
		await expect(firstRow.locator('[data-kt-dem-enrich-item="confirmed_quantity"]')).toHaveAttribute(
			"type",
			"text",
		);
		// Editable affordance: white boxed fields at rest; navy focus ring when active.
		const desc = firstRow.locator('[data-kt-dem-enrich-item="description"]');
		const editChromeRest = await desc.evaluate((el: HTMLInputElement) => {
			const rest = getComputedStyle(el);
			return {
				restBg: rest.backgroundColor,
				restBorder: rest.borderTopColor,
				restBorderW: rest.borderTopWidth,
			};
		});
		expect(editChromeRest.restBg).toMatch(/rgb\(255,\s*255,\s*255\)/);
		expect(parseFloat(editChromeRest.restBorderW || "0")).toBeGreaterThanOrEqual(1);
		expect(editChromeRest.restBorder).toMatch(/rgb\(195,\s*198,\s*209\)/);
		await desc.click();
		await expect(desc).toBeFocused();
		const editChromeFocus = await desc.evaluate((el: HTMLInputElement) => {
			const focus = getComputedStyle(el);
			return {
				focusBorder: focus.borderTopColor,
				focusShadow: focus.boxShadow,
				focusBorderW: focus.borderTopWidth,
			};
		});
		// System restrained blue focus (#7bbeff family) — not heavy navy/black slab.
		const focusRgb = editChromeFocus.focusBorder.match(
			/rgb\((\d+),\s*(\d+),\s*(\d+)\)/,
		);
		expect(focusRgb).toBeTruthy();
		const fr = Number(focusRgb![1]);
		const fg = Number(focusRgb![2]);
		const fb = Number(focusRgb![3]);
		expect(fb).toBeGreaterThan(180);
		expect(fr).toBeLessThan(200);
		expect(fr + fg + fb).toBeGreaterThan(350);
		expect(parseFloat(editChromeFocus.focusBorderW || "0")).toBeGreaterThanOrEqual(1);
		expect(editChromeFocus.focusShadow).not.toBe("none");
		await expect(firstRow.locator('[data-kt-dem-enrich-item="unit_estimate"]')).toBeVisible();
		await expect(firstRow.locator('[data-kt-dem-enrich-item="unit_estimate"]')).toHaveValue(
			/100,?000,?000/,
		);
		// Unit Est.: single input border (KES prefix outside) — no nested double outline.
		const unitEst = firstRow.locator('[data-kt-dem-enrich-item="unit_estimate"]');
		await unitEst.click();
		const moneyChrome = await unitEst.evaluate((el: HTMLInputElement) => {
			const wrap = el.closest(".kt-dem-ui05-item-unit-est-wrap") as HTMLElement | null;
			const ics = getComputedStyle(el);
			const wcs = wrap ? getComputedStyle(wrap) : null;
			return {
				inputBorder: ics.borderTopColor,
				inputBorderW: ics.borderTopWidth,
				wrapBorderW: wcs?.borderTopWidth || "0px",
				wrapBoxShadow: wcs?.boxShadow || "none",
			};
		});
		const moneyRgb = moneyChrome.inputBorder.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
		expect(moneyRgb).toBeTruthy();
		expect(Number(moneyRgb![3])).toBeGreaterThan(200);
		expect(Number(moneyRgb![1])).toBeLessThan(180);
		expect(parseFloat(moneyChrome.inputBorderW || "0")).toBe(1);
		expect(parseFloat(moneyChrome.wrapBorderW || "0")).toBe(0);
		expect(moneyChrome.wrapBoxShadow === "none" || moneyChrome.wrapBoxShadow === "").toBe(true);
		await expect(firstRow.locator("[data-kt-dem-enrich-item-total]")).toContainText(
			/KES\s*200,?000,?000/,
		);
		// Changing unit estimate recalculates line total.
		await firstRow.locator('[data-kt-dem-enrich-item="unit_estimate"]').fill("150,000,000");
		await expect(firstRow.locator("[data-kt-dem-enrich-item-total]")).toContainText(
			/KES\s*300,?000,?000/,
		);
		await firstRow.locator('[data-kt-dem-enrich-item="unit_estimate"]').fill("100,000,000");
		await expect(page.getByTestId("kt-dem-ui05-items-table")).toContainText(/Unit Est\./i);
		await expect(page.getByTestId("kt-dem-ui05-items-total")).toContainText(
			/KES\s*455,?000,?000/,
		);
		await expect(page.getByTestId("kt-dem-ui05-section-strategy")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05-section-pvc")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05-section-duplication")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05-footer")).toBeVisible();
		// DEM-UI-02/03 footer contract: Return left, Save + Send right (not a centered cluster).
		const footerLayout = await page.getByTestId("kt-dem-ui05-footer").evaluate((footer) => {
			const inner = footer.querySelector(".kt-dem-enrichment-footer-inner") as HTMLElement | null;
			const ret = footer.querySelector('[data-testid="kt-dem-ui05-return"]') as HTMLElement | null;
			const save = footer.querySelector('[data-testid="kt-dem-ui05-save"]') as HTMLElement | null;
			const send = footer.querySelector('[data-testid="kt-dem-ui05-send"]') as HTMLElement | null;
			if (!inner || !ret || !save || !send) {
				return null;
			}
			const ir = inner.getBoundingClientRect();
			const rr = ret.getBoundingClientRect();
			const sr = save.getBoundingClientRect();
			const er = send.getBoundingClientRect();
			const saveCs = getComputedStyle(save);
			return {
				returnLeftOfSave: rr.right <= sr.left + 1,
				saveLeftOfSend: sr.right <= er.left + 1,
				spreadGap: sr.left - rr.right,
				returnNearInnerLeft: rr.left - ir.left < 24,
				sendNearInnerRight: ir.right - er.right < 24,
				saveBg: saveCs.backgroundColor,
			};
		});
		expect(footerLayout).toBeTruthy();
		expect(footerLayout!.returnLeftOfSave).toBe(true);
		expect(footerLayout!.saveLeftOfSend).toBe(true);
		expect(footerLayout!.spreadGap).toBeGreaterThan(80);
		expect(footerLayout!.returnNearInnerLeft).toBe(true);
		expect(footerLayout!.sendNearInnerRight).toBe(true);
		// Save must be outline secondary (white), not filled muted grey/lavender.
		expect(footerLayout!.saveBg).toMatch(/rgb\(255,\s*255,\s*255\)/);
		await expect(page.getByTestId("kt-dem-ui05-strategy-pill")).toContainText(
			/Not assigned/i,
		);
		await expect(page.getByTestId("kt-dem-ui05-send")).toBeDisabled();
		// No procurement-method / tender chrome on Enrichment canvas
		// (Final Approval fixture may still mention method as Planning handoff copy).
		const enrichRoot = page.getByTestId("kt-dem-ui05-root");
		await expect(enrichRoot.getByText(/procurement method/i)).toHaveCount(0);
		await expect(enrichRoot.getByText(/tender method/i)).toHaveCount(0);
		await expect(page.locator("cdn.tailwindcss.com")).toHaveCount(0);

		const category = page.getByTestId("kt-dem-ui05-category");
		await category.selectOption({ label: "ICT infrastructure and services" });
		await expect(category).toHaveValue(/ICT|infrastructure/i);
		const route = page.getByTestId("kt-dem-ui05-route");
		await route.selectOption({ label: "Standard" });
		await expect(route).toHaveValue("Standard");
		await page.getByTestId("kt-dem-ui05-confirmed-estimate").fill("455,000,000");
		await page.getByTestId("kt-dem-ui05-estimate-basis").fill(
			"Market research and infrastructure assessment",
		);

		await page.getByTestId("kt-dem-ui05-assign-strategy").click();
		const drawer = page.getByTestId("kt-dem-ui05a-drawer");
		await expect(drawer).toBeVisible({ timeout: 10_000 });
		await expect(drawer).not.toHaveAttribute("hidden", "");
		await expect(page.getByTestId("kt-dem-ui05a-search")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05a-plan-filter")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05a-period-filter")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05a-suggestions")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05a-none")).toBeVisible({ timeout: 15_000 });
		const firstOption = page.getByTestId("kt-dem-ui05a-option-0");
		await expect(firstOption).toBeVisible({ timeout: 15_000 });
		// DEM-UI-05A card chrome: hierarchy path on each target card.
		await expect(page.getByTestId("kt-dem-ui05a-card-0")).toBeVisible();
		await firstOption.check();
		await expect(firstOption).toBeChecked();
		await expect(page.getByTestId("kt-dem-ui05a-add-supporting-0")).toBeVisible();
		await page.getByTestId("kt-dem-ui05a-reason").fill("Primary alignment with digital health target");
		await expect(page.getByTestId("kt-dem-ui05a-assign")).toBeEnabled();
		await Promise.all([
			page.waitForResponse(
				(r) =>
					r.url().includes("enrich_demand_form") && r.status() === 200,
				{ timeout: 20_000 },
			).catch(() => null),
			page.getByTestId("kt-dem-ui05a-assign").click(),
		]);
		await expect(drawer).toBeHidden({ timeout: 20_000 });
		await expect(page.getByTestId("kt-dem-ui05-strategy-pill")).toContainText(
			/Assigned/i,
			{ timeout: 15_000 },
		);
		await expect(page.getByTestId("kt-dem-ui05-strategy-assigned")).toBeVisible();
		// Plan must show Name (CODE) — never Strategic Plan document hash.
		const planLabel = page.getByTestId("kt-dem-ui05-primary-plan");
		await expect(planLabel).toBeVisible();
		await expect(planLabel).not.toHaveText(/^—$/);
		await expect(planLabel).not.toHaveText(/^[a-z0-9]{8,12}$/);
		await expect(planLabel).toContainText(/\(/);

		await page.getByTestId("kt-dem-ui05-save").click();
		await expect(page.getByText(/Enrichment saved/i)).toBeVisible({
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-dem-ui05-send")).toBeEnabled({
			timeout: 15_000,
		});

		await assertStitchDeskChrome(page, {
			rootTestId: "kt-dem-ui04-root",
			primaryCtaTestId: "kt-dem-ui05-send",
		});

		await page.getByTestId("kt-dem-ui05-send").click();
		await expect(page).toHaveURL(/demands-workspace/, { timeout: 20_000 });
	});

	test("Return for correction uses Stitch reason modal at Enrichment stage", async ({
		page,
	}) => {
		const demandName = await prepareEnrichmentDemand(page);
		await page.context().clearCookies();
		await loginAsProcurementApprover(page);
		await page.goto(`/desk/demand-review/${demandName}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});
		await page.getByTestId("kt-dem-ui05-return").click();
		const modal = page.getByTestId("kt-dem-ui04-reason-modal");
		await expect(modal).toBeVisible({ timeout: 10_000 });
		await expect(page.locator(".frappe-dialog:visible, .modal-dialog:visible")).toHaveCount(
			0,
		);
		await page.getByTestId("kt-dem-ui04-reason-confirm").click();
		await expect(page.getByTestId("kt-dem-ui04-reason-error")).toContainText(/required/i);
		await page
			.getByTestId("kt-dem-ui04-reason-comment")
			.fill("Revise confirmed quantities before enrichment");
		await page.getByTestId("kt-dem-ui04-reason-confirm").click();
		await expect(page).toHaveURL(/demands-workspace/, { timeout: 20_000 });
	});
});
