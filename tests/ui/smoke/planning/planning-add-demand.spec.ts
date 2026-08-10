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

test.describe("PLN-UI-04 Add approved Demand dialog", () => {
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
		await expect(page.locator(DIALOG)).toContainText(/Add approved demand/i);
		await expect(page.locator(`${DIALOG} [data-kt-pln-elig-row]`).first()).toBeVisible({
			timeout: 20_000,
		});
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-pln-ui04-dialog",
			primaryCtaTestId: "kt-pln-ui04-add",
			assertHeadline: false,
		});
		// Pack v1.3: no packaging radios on normal UI-04.
		await expect(page.getByTestId("kt-pln-ui04-package")).toHaveCount(0);
		await expect(page.locator(DIALOG)).toContainText(/Add Demand and continue/i);
		// Stitch: search icon sits in absolute inset-y wrapper; pl-10 must leave room.
		const searchPad = await page
			.locator(`${DIALOG} [data-kt-pln-elig-search]`)
			.evaluate((el) => parseFloat(getComputedStyle(el).paddingLeft));
		expect(searchPad).toBeGreaterThanOrEqual(36);
		const rowCheck = page.locator(`${DIALOG} [data-kt-pln-elig-check]`).first();
		await rowCheck.evaluate((el: HTMLInputElement) => {
			el.checked = true;
			el.dispatchEvent(new Event("change", { bubbles: true }));
		});
		await expect(page.locator(`${DIALOG} [data-kt-pln-elig-count-label]`)).toContainText(
			/1 Approved Demand selected/i,
		);
		await expect(page.locator(DIALOG)).toContainText(/End of available demands/i);
		const firstRow = page.locator(`${DIALOG} [data-kt-pln-elig-row]`).first();
		await expect(firstRow).toHaveClass(/is-selected/);
		// Column alignment: Demand title must sit under DEMAND header (not Organisation Unit).
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
			const ok = drifts.every((d) => Math.abs(d.drift) <= 6);
			const moneySample = tds[3]?.textContent?.replace(/\s+/g, " ").trim() || "";
			return { ok, drifts, moneySample, tdCount: tds.length };
		});
		expect(aligned.tdCount, "row must have exactly 8 columns").toBe(8);
		expect(aligned.ok, `Column misaligned: ${JSON.stringify(aligned)}`).toBeTruthy();
		expect(aligned.moneySample || "").toMatch(/^KES\s[\d,]+/);
		const type = await page.evaluate(() => {
			const dialog = document.querySelector('[data-testid="kt-pln-ui04-dialog"]');
			const title = dialog?.querySelector("[data-kt-pln-elig-title]");
			const money = dialog?.querySelector("[data-kt-pln-elig-row] td:nth-child(4) .font-data-md");
			const footer = dialog?.querySelector("[data-kt-pln-elig-amount]");
			const ou = dialog?.querySelector("[data-kt-pln-elig-ou-cell]");
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
				money: read(money),
				footer: read(footer),
				ouText: (ou?.textContent || "").trim(),
				ouTruncated: !!(ou && (ou.classList.contains("truncate") || /…|\.\.\.$/.test(ou.textContent || ""))),
			};
		});
		expect(type.title?.fontSize, `title size: ${JSON.stringify(type.title)}`).toBeGreaterThanOrEqual(15.5);
		expect(type.title?.fontWeight || 0, "title weight").toBeGreaterThanOrEqual(600);
		expect(type.money?.fontSize, `money size: ${JSON.stringify(type.money)}`).toBeGreaterThanOrEqual(15.5);
		expect(type.footer?.fontSize, `footer size: ${JSON.stringify(type.footer)}`).toBeGreaterThanOrEqual(15.5);
		expect(type.ouTruncated, "Organisation Unit must not be truncated").toBeFalsy();
		expect(type.ouText.length, "Organisation Unit must show full value").toBeGreaterThan(20);
		await page.getByTestId("kt-pln-ui04-add").click();
		await expect(page).toHaveURL(/procurement-plan-item-editor/, { timeout: 45_000 });
		await expect(page.getByTestId("kt-pln-ui06-root")).toBeVisible({ timeout: 45_000 });
		await expect(page.locator(`${ROOT_EDITOR}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.locator(ROOT_EDITOR)).not.toContainText("Combine in this Plan Item");
		await expect(page.locator(ROOT_EDITOR)).not.toContainText("Keep separate");
	});

	test("multi–Need Item Demand: default continue opens editor; separate link visible", async ({
		page,
	}) => {
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
		await expect(page.getByTestId("kt-pln-ui04-plan-separately")).toBeVisible({
			timeout: 10_000,
		});
		await expect(page.locator(DIALOG)).toContainText(/2 Need Items/i);
		await expect(page.getByTestId("kt-pln-ui04-package")).toHaveCount(0);
		await page.getByTestId("kt-pln-ui04-add").click();
		await expect(page).toHaveURL(/procurement-plan-item-editor/, { timeout: 45_000 });
		await expect(page.getByTestId("kt-pln-ui06-root")).toBeVisible({ timeout: 45_000 });
	});

	test("multi–Need Item Demand: Plan Need Items separately + reason → builder with N rows", async ({
		page,
	}) => {
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
		await page.getByTestId("kt-pln-ui04-plan-separately").click();
		await expect(page.getByTestId("kt-pln-ui04-separation-reason")).toBeVisible({
			timeout: 10_000,
		});
		await page.getByTestId("kt-pln-ui04-separation-reason").fill(
			"Distinct delivery scopes require separate packages.",
		);
		await page.getByTestId("kt-pln-ui04-add").click();
		await expect(page.locator(DIALOG)).toBeHidden({ timeout: 45_000 });
		await expect(page.locator(`${BUILDER}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.locator(`${BUILDER} [data-kt-pln-item-row]`)).toHaveCount(2, {
			timeout: 30_000,
		});
	});
});
