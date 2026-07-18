import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { expectConfigurationContextStrip } from "../../helpers/ktClConfigContext";

/**
 * CFG-01 Tender Profile (C2-CFG1).
 * Route: /desk/it-tender-configuration-tender-profile/<configuration_id>
 */

const PAGE_SLUG = "it-tender-configuration-tender-profile";
const CFG01 = `/desk/${PAGE_SLUG}`;
const ROOT = '[data-testid="kt-cl-cfg01-root"]';
const CONFIG = "TCFG-SEED-TCFG-IP";

const FORBIDDEN = [
	/\bFinalize\b/i,
	/\bPublish\b/i,
	/\bCreate Tender\b/i,
	/\bSubmit for Review\b/i,
	/\bTender Shell\b/i,
	/\bPlanning Pkg Ref\b/i,
	/\bschema version\b/i,
	/\bclause ID\b/i,
	/\bhash\b/i,
];

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
		throw new Error("CFG-01 seed failed: " + JSON.stringify(result));
	}
}

async function openProfile(page: import("@playwright/test").Page, configId = CONFIG) {
	await page.goto(`${CFG01}/${encodeURIComponent(configId)}`);
	await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
	await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${configId}`), { timeout: 15_000 });
}

async function expectCfg01Layout(page: import("@playwright/test").Page) {
	const layout = page.getByTestId("kt-cl-cfg01-layout");
	await expect(layout).toBeVisible();
	await expect(page.getByTestId("kt-cl-cfg01-main")).toBeVisible();
	await expect(page.getByTestId("kt-cl-cfg01-side")).toBeVisible();
	const geometry = await page.evaluate(() => {
		const main = document.querySelector('[data-testid="kt-cl-cfg01-main"]') as HTMLElement | null;
		const side = document.querySelector('[data-testid="kt-cl-cfg01-side"]') as HTMLElement | null;
		if (!main || !side) {
			return { ok: false, reason: "missing panes" };
		}
		const mr = main.getBoundingClientRect();
		const sr = side.getBoundingClientRect();
		if (window.innerWidth >= 1024 && mr.right > sr.left + 8) {
			return { ok: false, reason: "main not left of side", mr: mr.right, sr: sr.left };
		}
		return { ok: true };
	});
	expect(geometry.ok, JSON.stringify(geometry)).toBe(true);
}

test.describe.configure({ mode: "serial" });

test.describe("CFG-01 Tender Profile", () => {
	test.beforeAll(async ({ browser }) => {
		const page = await browser.newPage();
		await page.setViewportSize({ width: 1280, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await seedUi00(page);
		await page.close();
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1280, height: 900 });
		await loginAsAdministrator(page);
	});

	test("layout: strip, sections, footer labels, no forbidden terms", async ({ page }) => {
		await openProfile(page);
		await expectConfigurationContextStrip(page, {
			family: /Information Technology/i,
			stdDocument: /IT Standard Tender Document/i,
		});
		await expectCfg01Layout(page);
		await expect(page.getByTestId("kt-cl-cfg01-section-identity")).toContainText(/Tender Identity/i);
		await expect(page.getByTestId("kt-cl-cfg01-section-lots")).toContainText(/Lot Structure/i);
		await expect(page.getByTestId("kt-cl-cfg01-section-std")).toContainText(/STD Context/i);
		await expect(page.getByTestId("kt-cl-cfg01-section-notes")).toContainText(/Notes/i);
		await expect(page.getByTestId("kt-cl-cfg01-back")).toHaveText(/Back to Configuration Home/i);
		await expect(page.getByTestId("kt-cl-cfg01-save")).toHaveText(/Save Profile/i);
		await expect(page.getByTestId("kt-cl-cfg01-continue")).toHaveText(
			/Continue to Tender Data Sheet/i
		);

		const footerGeom = await page.evaluate(() => {
			const footer = document.querySelector('[data-testid="kt-cl-cfg01-footer"]') as HTMLElement | null;
			const back = document.querySelector('[data-testid="kt-cl-cfg01-back"]') as HTMLElement | null;
			const cont = document.querySelector(
				'[data-testid="kt-cl-cfg01-continue"]'
			) as HTMLElement | null;
			if (!footer || !back || !cont) {
				return { ok: false, reason: "missing footer controls" };
			}
			const fr = footer.getBoundingClientRect();
			const br = back.getBoundingClientRect();
			const cr = cont.getBoundingClientRect();
			const backOnLeft = br.left < fr.left + fr.width * 0.4;
			const continueOnRight = cr.right > fr.left + fr.width * 0.55;
			const contColor = getComputedStyle(cont).color;
			return { ok: true, backOnLeft, continueOnRight, contColor };
		});
		expect(footerGeom.ok, JSON.stringify(footerGeom)).toBe(true);
		expect(footerGeom.backOnLeft, JSON.stringify(footerGeom)).toBe(true);
		expect(footerGeom.continueOnRight, JSON.stringify(footerGeom)).toBe(true);
		expect(footerGeom.contColor).toMatch(/rgb\(255,\s*255,\s*255\)/);

		const body = await page.locator(ROOT).innerText();
		for (const re of FORBIDDEN) {
			expect(body, String(re)).not.toMatch(re);
		}
		await expect(page.getByText(/Run Readiness Check/i)).toHaveCount(0);
	});

	test("single → multiple lots shows table; Continue gated until complete", async ({ page }) => {
		await openProfile(page);
		await expect(page.getByTestId("kt-cl-cfg01-continue")).toBeDisabled();
		await expect(page.getByTestId("kt-cl-cfg01-lots")).toHaveClass(/hidden/);

		await page.getByTestId("kt-cl-cfg01-title").fill("ERP Implementation Services");
		await page.getByTestId("kt-cl-cfg01-scope").fill(
			"Procurement of ERP software licences, implementation, training, and support for national treasury systems."
		);
		await page.getByTestId("kt-cl-cfg01-lot-multiple").check();
		await expect(page.getByTestId("kt-cl-cfg01-lots")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg01-lots-table")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg01-continue")).toBeDisabled();

		await page.locator('[data-lot-field="lot_title"]').first().fill("Licences and Implementation");
		await expect(page.getByTestId("kt-cl-cfg01-continue")).toBeEnabled();

		await page.getByTestId("kt-cl-cfg01-lot-single").check();
		await expect(page.getByTestId("kt-cl-cfg01-lots")).toHaveClass(/hidden/);
		await expect(page.getByTestId("kt-cl-cfg01-continue")).toBeEnabled();
	});

	test("Save Profile shows success alert then persists; refresh keeps configuration id", async ({
		page,
	}) => {
		await openProfile(page);
		const title = "Data Center Hardware Refresh";
		const scope =
			"Procurement of server, storage, networking, installation, configuration, warranty, and support services for the data center refresh.";
		await page.getByTestId("kt-cl-cfg01-title").fill(title);
		await page.getByTestId("kt-cl-cfg01-scope").fill(scope);
		await page.getByTestId("kt-cl-cfg01-lot-single").check();
		await expect(page.getByTestId("kt-cl-cfg01-save")).toBeEnabled();
		await page.getByTestId("kt-cl-cfg01-save").click();
		await expect(page.locator(".desk-alert .alert-message")).toContainText(
			/Tender Profile saved successfully/i,
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-cl-cfg01-save")).toBeDisabled({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-cfg01-continue")).toBeEnabled();

		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${CONFIG}`), { timeout: 15_000 });
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-cl-cfg01-title")).toHaveValue(title);
		await expect(page.getByTestId("kt-cl-cfg01-scope")).toHaveValue(scope);
	});

	test("Continue navigates to TDS route when complete", async ({ page }) => {
		await openProfile(page);
		await page.getByTestId("kt-cl-cfg01-title").fill("ERP Implementation Services");
		await page.getByTestId("kt-cl-cfg01-scope").fill(
			"Procurement of ERP software licences, implementation, training, and support for national treasury systems."
		);
		await page.getByTestId("kt-cl-cfg01-lot-na").check();
		await page.getByTestId("kt-cl-cfg01-continue").click();
		await expect(page).toHaveURL(
			new RegExp(`it-tender-configuration-tds/${CONFIG}`),
			{ timeout: 20_000 }
		);
	});
});
