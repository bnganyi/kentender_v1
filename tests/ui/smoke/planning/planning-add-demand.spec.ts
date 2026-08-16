import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohPlanningOfficer,
	preparePlanningGate04,
} from "../../helpers/planningRoles";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

const BUILDER = '[data-testid="kt-pln-ui03-root"]';
const DIALOG = '[data-testid="kt-pln-ui04-dialog"]';
const ROOT_EDITOR = '[data-testid="kt-pln-ui06-root"]';

test.describe("PLN-UI-04 Add approved Demands dialog", () => {
	test.describe.configure({ timeout: 120_000 });
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("opens eligible Demand dialog and adds to plan", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate04(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		expect(prep.eligible_demand).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-builder?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${BUILDER}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await page.getByTestId("kt-pln-ui03-add-demand").click();
		await expect(page.locator(DIALOG)).toBeVisible({ timeout: 15_000 });
		await expect(page.locator(DIALOG)).toContainText(/Add approved Demands/i);
		await expect(page.locator(DIALOG)).toContainText(
			/A Draft plan update will contain this addition\. Approved Version 1 remains active\./i,
		);
		await expect(page.locator(`${DIALOG} [data-kt-pln-elig-ou]`)).toContainText(
			/All permitted units/i,
		);
		await expect(page.locator(`${DIALOG} [data-kt-pln-elig-category]`)).toHaveCount(0);
		await expect(page.locator(`${DIALOG} [data-kt-pln-elig-remaining]`)).toBeVisible();
		await expect(page.locator(`${DIALOG} label`).filter({ hasText: /Search approved Demands/i })).toBeVisible();
		await expect(page.locator(`${DIALOG} [data-kt-pln-elig-row]`).first()).toBeVisible({
			timeout: 20_000,
		});
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-pln-ui04-dialog",
			primaryCtaTestId: "kt-pln-ui04-add",
			assertHeadline: false,
		});
		await expect(page.getByTestId("kt-pln-ui04-package")).toHaveCount(0);
		await expect(page.locator(`${DIALOG} thead`)).toContainText(/Available value/i);
		await expect(page.locator(`${DIALOG} thead`)).toContainText(/Proposed Funding/i);
		await expect(page.locator(`${DIALOG} thead`)).toContainText(/Validation Status|Status/i);
		await expect(page.locator(`${DIALOG} thead`)).not.toContainText(/Already planned/i);
		const searchPad = await page
			.locator(`${DIALOG} [data-kt-pln-elig-search]`)
			.evaluate((el) => parseFloat(getComputedStyle(el).paddingLeft));
		expect(searchPad).toBeGreaterThanOrEqual(36);
		const spacing = await page.evaluate(() => {
			const dialog = document.querySelector('[data-testid="kt-pln-ui04-dialog"] [role="dialog"]');
			if (!dialog) return null;
			const kids = Array.from(dialog.children);
			const box = (el: Element | undefined) => {
				if (!el) return null;
				const cs = getComputedStyle(el);
				return {
					pt: parseFloat(cs.paddingTop),
					pr: parseFloat(cs.paddingRight),
					pb: parseFloat(cs.paddingBottom),
					pl: parseFloat(cs.paddingLeft),
					gap: parseFloat(cs.gap) || 0,
				};
			};
			return {
				header: box(kids[0]),
				filters: box(kids[1]),
				summary: box(kids[3]),
				footer: box(kids[4]),
			};
		});
		// Stitch: px-section-gap (24) + py-gutter-md (16) on header/filters/footer;
		// summary uses p-section-gap (24).
		expect(spacing?.header?.pl).toBe(24);
		expect(spacing?.header?.pt).toBe(16);
		expect(spacing?.filters?.pt).toBe(16);
		expect(spacing?.footer?.pt).toBe(16);
		const visualContract = await page.locator(DIALOG).evaluate((root) => {
			const panel = root.querySelector('[role="dialog"]') as HTMLElement;
			const filters = root.querySelector('.kt-pln-demand-filter-grid') as HTMLElement;
			const tableWrap = root.querySelector('.kt-pln-demand-table-wrap') as HTMLElement;
			const title = root.querySelector('h2') as HTMLElement;
			const rect = panel.getBoundingClientRect();
			return {
				panelLeft: rect.left,
				panelRight: rect.right,
				panelTop: rect.top,
				panelBottom: rect.bottom,
				filterColumns: getComputedStyle(filters).gridTemplateColumns.split(' ').length,
				overflowX: getComputedStyle(tableWrap).overflowX,
				titleFamily: getComputedStyle(title).fontFamily,
				titleSize: getComputedStyle(title).fontSize,
			};
		});
		expect(visualContract.panelLeft).toBeGreaterThanOrEqual(0);
		expect(visualContract.panelRight).toBeLessThanOrEqual(1400);
		expect(visualContract.panelTop).toBeGreaterThanOrEqual(0);
		expect(visualContract.panelBottom).toBeLessThanOrEqual(900);
		expect(visualContract.filterColumns).toBe(3);
		expect(visualContract.overflowX).toMatch(/auto|scroll/);
		expect(visualContract.titleFamily).toContain('Manrope');
		expect(visualContract.titleSize).toBe('24px');
		expect(spacing?.footer?.gap).toBe(16);
		expect(spacing?.summary?.pt).toBe(24);
		expect(spacing?.summary?.pl).toBe(24);
		const rowCheck = page.locator(`${DIALOG} [data-kt-pln-elig-check]`).first();
		await rowCheck.evaluate((el: HTMLInputElement) => {
			el.checked = true;
			el.dispatchEvent(new Event("change", { bubbles: true }));
		});
		await expect(page.locator(`${DIALOG} [data-kt-pln-elig-count-label]`)).toContainText(
			/1 Approved Demand selected/i,
		);
		await expect(page.getByTestId("kt-pln-ui04-formation")).toBeHidden();
		const firstRow = page.locator(`${DIALOG} [data-kt-pln-elig-row]`).first();
		await expect(firstRow).toHaveClass(/kt-pln-selected-row/);
		const aligned = await page.evaluate(() => {
			const dialog = document.querySelector('[data-testid="kt-pln-ui04-dialog"]');
			if (!dialog) return { ok: false, reason: "no dialog" };
			const ths = Array.from(dialog.querySelectorAll("thead th"));
			const row = dialog.querySelector("[data-kt-pln-elig-row]");
			const tds = row ? Array.from(row.querySelectorAll("td")) : [];
			if (ths.length !== 8 || tds.length !== 8) {
				return { ok: false, reason: "bad column count", thCount: ths.length, tdCount: tds.length };
			}
			const drifts = ths.map((th, i) => {
				const thr = th.getBoundingClientRect();
				const tdr = tds[i].getBoundingClientRect();
				return {
					i,
					header: (th.textContent || "").trim().slice(0, 24),
					thLeft: Math.round(thr.left),
					tdLeft: Math.round(tdr.left),
					drift: Math.round(tdr.left - thr.left),
				};
			});
			const cells = tds.map((td) => td.getBoundingClientRect());
			const overlaps = cells.slice(0, -1).map((cell, i) => Math.ceil(cell.right - cells[i + 1].left));
			const ok = drifts.every((d) => Math.abs(d.drift) <= 6) && overlaps.every((overlap) => overlap <= 0);
			const moneySample = tds[4]?.textContent?.replace(/\s+/g, " ").trim() || "";
			const headers = ths.map((th) => (th.textContent || "").trim());
			return { ok, drifts, overlaps, moneySample, tdCount: tds.length, headers };
		});
		expect(aligned.tdCount, "row must have one selector plus 7 governed columns").toBe(8);
		expect(aligned.ok, `Column misaligned: ${JSON.stringify(aligned)}`).toBeTruthy();
		expect(aligned.moneySample || "").toMatch(/^KES\s[\d,]+/);
		expect(aligned.headers?.join(" ")).toMatch(/Available value/i);
		const type = await page.evaluate(() => {
			const dialog = document.querySelector('[data-testid="kt-pln-ui04-dialog"]');
			const title = dialog?.querySelector("[data-kt-pln-elig-title]");
			const money = dialog?.querySelector("[data-kt-pln-elig-row] [data-kt-pln-elig-row-amount]");
			const footer = dialog?.querySelector("[data-kt-pln-elig-amount]");
			const ou = dialog?.querySelector("[data-kt-pln-elig-ou-cell]");
			const funding = dialog?.querySelector("[data-kt-pln-elig-funding-cell]");
			const read = (el: Element | null | undefined) => {
				if (!el) return null;
				const cs = getComputedStyle(el);
				return {
					fontSize: parseFloat(cs.fontSize),
					fontWeight: parseInt(cs.fontWeight, 10),
					text: (el.textContent || "").trim(),
				};
			};
			return {
				title: read(title),
				titleColor: title ? getComputedStyle(title).color : "",
				money: read(money),
				footer: read(footer),
				ouText: (ou?.textContent || "").trim(),
				ouTruncated: !!(ou && (ou.classList.contains("truncate") || /…|\.\.\.$/.test(ou.textContent || ""))),
				fundingTruncated: !!(
					funding &&
					(funding.classList.contains("truncate") || /…|\.\.\.$/.test(funding.textContent || ""))
				),
			};
		});
		expect(type.title?.fontSize, `title size: ${JSON.stringify(type.title)}`).toBe(14);
		expect(type.title?.fontWeight || 0, "title weight").toBeGreaterThanOrEqual(500);
		expect(type.titleColor || "", "Demand title must stay on-surface (not link blue)").toMatch(
			/rgb\(\s*25,\s*28,\s*30\s*\)|#191c1e/i,
		);
		expect(type.money?.fontSize, `money size: ${JSON.stringify(type.money)}`).toBeGreaterThanOrEqual(15.5);
		expect(type.footer?.fontSize, `footer size: ${JSON.stringify(type.footer)}`).toBeGreaterThanOrEqual(15.5);
		expect(type.ouTruncated, "Organisation Unit must not be truncated").toBeFalsy();
		expect(type.fundingTruncated, "Proposed Funding must not be truncated").toBeFalsy();
		expect(type.ouText.length, "Organisation Unit must show full value").toBeGreaterThan(20);
		await page.getByTestId("kt-pln-ui04-add").click();
		await expect(page).toHaveURL(/procurement-plan-item-editor/, { timeout: 45_000 });
		await expect(page.getByTestId("kt-pln-ui06-root")).toBeVisible({ timeout: 45_000 });
		await expect(page.locator(`${ROOT_EDITOR}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page).toHaveURL(/\/procurement-plan-item-editor\/[^/?#]+$/);
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT_EDITOR}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByText("PLN_ITEM_NOT_FOUND", { exact: true })).toHaveCount(0);
		await expect(page.locator(ROOT_EDITOR)).not.toContainText("Combine in this Plan Item");
		await expect(page.locator(ROOT_EDITOR)).not.toContainText("Keep separate");
	});

	test("Combine without a reason shows an inline error, not a Message dialog", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate04(page, { eligibleCount: 2 });
		expect(prep.empty_draft_plan).toBeTruthy();
		expect(prep.eligible_demand).toBeTruthy();
		expect(prep.eligible_demand_2).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-builder?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${BUILDER}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await page.getByTestId("kt-pln-ui03-add-demand").click();
		await expect(page.locator(DIALOG)).toBeVisible({ timeout: 15_000 });
		await expect(page.locator(`${DIALOG} [data-kt-pln-elig-row]`).first()).toBeVisible({
			timeout: 20_000,
		});
		const first = page.locator(
			`${DIALOG} [data-kt-pln-elig-check][data-demand="${prep.eligible_demand}"]`,
		);
		const second = page.locator(
			`${DIALOG} [data-kt-pln-elig-check][data-demand="${prep.eligible_demand_2}"]`,
		);
		await expect(first).toBeVisible();
		await expect(second).toBeVisible();
		await first.evaluate((el: HTMLInputElement) => {
			el.checked = true;
			el.dispatchEvent(new Event("change", { bubbles: true }));
		});
		await second.evaluate((el: HTMLInputElement) => {
			el.checked = true;
			el.dispatchEvent(new Event("change", { bubbles: true }));
		});
		await expect(page.getByTestId("kt-pln-ui04-formation")).toBeVisible();
		await page.getByTestId("kt-pln-ui04-formation-combine").check();
		await expect(page.getByTestId("kt-pln-ui04-formation-reason")).toBeVisible();
		await page.getByTestId("kt-pln-ui04-add").click();
		await expect(
			page.locator(`${DIALOG} [data-kt-field-error="formation_reason"]`),
		).toBeVisible();
		await expect(page.locator(`${DIALOG} [data-kt-field-error="formation_reason"]`)).toContainText(
			/reason for combining is required/i,
		);
		await expect(page.getByRole("dialog", { name: "Message" })).toHaveCount(0);
		await expect(page.locator(DIALOG)).toBeVisible();
		await expect(page).toHaveURL(/procurement-plan-builder/);
	});

	test("mixed-OU selection disables Combine and shows the incompatibility callout", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate04(page, { eligibleCount: 2, mixedOu: true });
		expect(prep.empty_draft_plan).toBeTruthy();
		expect(prep.eligible_demand).toBeTruthy();
		expect(prep.eligible_demand_2).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-builder?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${BUILDER}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await page.getByTestId("kt-pln-ui03-add-demand").click();
		await expect(page.locator(DIALOG)).toBeVisible({ timeout: 15_000 });
		const first = page.locator(
			`${DIALOG} [data-kt-pln-elig-check][data-demand="${prep.eligible_demand}"]`,
		);
		const second = page.locator(
			`${DIALOG} [data-kt-pln-elig-check][data-demand="${prep.eligible_demand_2}"]`,
		);
		await expect(first).toBeVisible({ timeout: 20_000 });
		await expect(second).toBeVisible();
		await first.evaluate((el: HTMLInputElement) => {
			el.checked = true;
			el.dispatchEvent(new Event("change", { bubbles: true }));
		});
		await second.evaluate((el: HTMLInputElement) => {
			el.checked = true;
			el.dispatchEvent(new Event("change", { bubbles: true }));
		});
		await expect(page.getByTestId("kt-pln-ui04-formation")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui04-formation-combine")).toBeDisabled();
		await expect(page.locator(`${DIALOG} [data-kt-pln-formation-callout-copy]`)).toContainText(
			/These Demands have different owning Organisation Units and cannot be combined in MVP 1/i,
		);
		await expect(page.getByRole("dialog", { name: "Message" })).toHaveCount(0);
	});

	test("single Demand creates one Plan Item without formation radios", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate04(page, { needItemCount: 2 });
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-builder?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${BUILDER}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await page.getByTestId("kt-pln-ui03-add-demand").click();
		await expect(page.locator(DIALOG)).toBeVisible({ timeout: 15_000 });
		const rowCheck = page.locator(`${DIALOG} [data-kt-pln-elig-check]`).first();
		await rowCheck.evaluate((el: HTMLInputElement) => {
			el.checked = true;
			el.dispatchEvent(new Event("change", { bubbles: true }));
		});
		await expect(page.getByTestId("kt-pln-ui04-formation")).toBeHidden();
		await expect(page.locator(DIALOG)).toContainText(/One Plan Item will be created/i);
		await page.getByTestId("kt-pln-ui04-add").click();
		await expect(page).toHaveURL(/procurement-plan-item-editor/, { timeout: 45_000 });
		await expect(page.getByTestId("kt-pln-ui06-root")).toBeVisible({ timeout: 45_000 });
	});
});
