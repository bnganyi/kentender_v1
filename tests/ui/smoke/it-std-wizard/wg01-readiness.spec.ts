import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { expectConfigurationContextStrip } from "../../helpers/ktClConfigContext";

/**
 * WG-01 Readiness Check & Report (WF-01).
 * Route: /desk/it-tender-configuration-validation-report/<configuration_id>
 * Layout contract: D1-WG1 (KPI accent cards, guidance banner, checklist | findings bento).
 */

const PAGE_SLUG = "it-tender-configuration-validation-report";
const ROOT = '[data-testid="kt-cl-wf01-root"]';
const CONFIG = "TCFG-SEED-TCFG-IP";
const UNDER_REVIEW_CONFIG = "TCFG-SEED-TCFG-UR";

const FORBIDDEN = [/\bschema version\b/i, /\brule ID\b/i, /\bpublish tender\b/i];

async function seedUi00(page: import("@playwright/test").Page) {
	await page.waitForFunction(() => typeof (window as unknown as { frappe?: unknown }).frappe !== "undefined");
	const result = await page.evaluate(async () => {
		// @ts-expect-error frappe on desk
		const r = await frappe.call({
			method: "kentender_procurement.tender_configurations.seed_ui00_dashboard_for_tests",
			args: { clear: 1 },
		});
		return r.message || r;
	});
	if (!result || !(result as { configurations?: string[] }).configurations) {
		throw new Error("WG-01 seed failed: " + JSON.stringify(result));
	}
}

async function openReadiness(page: import("@playwright/test").Page, configId = CONFIG) {
	await page.goto(`/desk/${PAGE_SLUG}/${encodeURIComponent(configId)}`);
	await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
	await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${configId}`), { timeout: 15_000 });
	await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
}

test.describe.configure({ mode: "serial" });

test.describe("WG-01 Readiness Check & Report", () => {
	test.beforeAll(async ({ browser }) => {
		const page = await browser.newPage();
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await seedUi00(page);
		await page.close();
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
	});

	test("layout: strip, KPI cards, banner, bento checklist|findings, footer", async ({ page }) => {
		await openReadiness(page);
		await expectConfigurationContextStrip(page, {
			family: /Information Technology/i,
			stdDocument: /IT Standard Tender Document/i,
		});
		await expect(page.getByTestId("kt-cl-wf01-summary")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf01-card-overall")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf01-card-blockers")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf01-card-warnings")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf01-card-last-checked")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf01-guidance")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf01-layout")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf01-checklist")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf01-findings")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf01-footer")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf01-run-check")).toHaveText(/Re-run Check/i);
		await expect(page.getByTestId("kt-cl-wf01-export")).toHaveText(/Export Report/i);
		await expect(page.getByTestId("kt-cl-wf01-back")).toHaveText(/Return to Configuration Home/i);
		await expect(page.getByTestId("kt-cl-breadcrumb-current")).toHaveText(/Readiness Check & Report/i);

		// Bento: checklist precedes findings in DOM (left col then right).
		const layout = page.getByTestId("kt-cl-wf01-layout");
		const checklistBox = await layout.getByTestId("kt-cl-wf01-checklist").boundingBox();
		const findingsBox = await layout.getByTestId("kt-cl-wf01-findings").boundingBox();
		expect(checklistBox && findingsBox).toBeTruthy();
		if (checklistBox && findingsBox) {
			expect(checklistBox.x).toBeLessThan(findingsBox.x);
		}

		const body = await page.locator(ROOT).innerText();
		for (const re of FORBIDDEN) {
			expect(body, String(re)).not.toMatch(re);
		}
		// Guidance must not repeat the same sentence twice.
		expect(body.match(/Review the warnings before submitting for review/gi)?.length || 0).toBeLessThan(2);
	});

	test("Re-run Check updates summary cards", async ({ page }) => {
		await openReadiness(page);
		await page.getByTestId("kt-cl-wf01-run-check").click();
		await expect(page.getByTestId("kt-cl-wf01-card-overall")).not.toHaveText(/Check Not Run/i, {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-cl-wf01-card-blockers")).toHaveText(/BLOCKERS\s*\d{2}/i);
		await expect(page.locator(".kt-cl-wf01-check-row").first()).toBeVisible();

		// Checklist rows must stack vertically (not Desk inline button chrome).
		const styles = await page.evaluate(() => {
			const row = document.querySelector(".kt-cl-wf01-check-row");
			const list = document.querySelector(".kt-cl-wf01-checklist-list");
			if (!row || !list) {
				return null;
			}
			const rs = getComputedStyle(row);
			const ls = getComputedStyle(list);
			return {
				rowDisplay: rs.display,
				rowBorder: rs.borderTopWidth,
				listDir: ls.flexDirection,
			};
		});
		expect(styles).toBeTruthy();
		expect(styles?.rowDisplay).toBe("flex");
		expect(styles?.listDir).toBe("column");
		expect(styles?.rowBorder).toBe("0px");
	});

	test("reload preserves configuration route", async ({ page }) => {
		await openReadiness(page);
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${CONFIG}`));
		await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
	});

	test("returned corrections panel: Mark as fixed clears open gate", async ({ page }) => {
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await seedUi00(page);
		// Seed can invalidate the desk sid; re-auth before preparer fixture + navigation.
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await page.waitForFunction(
			() => typeof (window as unknown as { frappe?: unknown }).frappe !== "undefined"
		);
		const prep = await page.evaluate(async () => {
			try {
				// @ts-expect-error frappe on desk
				const user = frappe.session?.user || "";
				// @ts-expect-error frappe on desk
				const r = await frappe.call({
					method:
						"kentender_procurement.tender_configurations.prepare_wg01_returned_corrections_for_tests",
				});
				return { ok: true, user, message: r.message || r };
			} catch (e) {
				const err = e as {
					message?: string;
					exc?: string;
					_server_messages?: string;
					httpStatus?: number;
				};
				return {
					ok: false,
					error: [
						err?.message,
						err?.exc,
						err?._server_messages,
						String(err?.httpStatus || ""),
						Object.prototype.toString.call(e),
					]
						.filter(Boolean)
						.join(" || "),
				};
			}
		});
		expect(prep, JSON.stringify(prep)).toMatchObject({ ok: true });
		const resolvedFindingId = String(
			((prep as { message?: { finding_id?: string } }).message || {}).finding_id || ""
		);
		expect(resolvedFindingId, JSON.stringify(prep)).toMatch(/^FIN-/);

		await openReadiness(page, UNDER_REVIEW_CONFIG);
		await expect(page.getByTestId("kt-cl-wf01-corrections")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-wf01-guidance")).toContainText(/returned for correction/i);
		await expect(page.getByTestId("kt-cl-wf01-fix-corrections")).toBeVisible();
		await expect(page.getByTestId(`kt-cl-wf01-correction-${resolvedFindingId}`)).toBeVisible();
		await expect(page.getByTestId(`kt-cl-wf01-corr-fix-${resolvedFindingId}`)).toBeVisible();

		await page.getByTestId(`kt-cl-wf01-corr-fix-${resolvedFindingId}`).click();
		await expect(page.getByTestId(`kt-cl-wf01-corr-fix-${resolvedFindingId}`)).toHaveCount(0, {
			timeout: 15_000,
		});
		await expect(page.getByTestId(`kt-cl-wf01-correction-${resolvedFindingId}`)).toContainText(
			/Fixed|Resolved/i
		);
		await expect(page.getByTestId("kt-cl-wf01-corrections")).toContainText(/0\s*OPEN/i);
	});
});
