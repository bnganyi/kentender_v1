import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { expectConfigurationContextStrip } from "../../helpers/ktClConfigContext";
import {
	expectUi01NineCards,
	expectUi01StructuralLayout,
} from "../../helpers/ktClUi01LayoutContract";

/**
 * UI-01 Tender Configuration Home (C1-M3).
 * Route contract: /desk/it-tender-configuration-overview/<configuration_id>
 */

const PAGE_SLUG = "it-tender-configuration-overview";
const UI01 = `/desk/${PAGE_SLUG}`;
const ROOT = '[data-testid="kt-cl-ui01-root"]';
const NA_CONFIG = "TCFG-SEED-TCFG-NA";

const CFG_TITLES = [
	"Tender Profile",
	"Tender Data Sheet",
	"IT Requirements",
	"Implementation Schedule",
	"System Inventory & Bidder Background",
	"Price Schedule",
	"Evaluation Setup",
	"Forms & Evidence",
	"Contract Values",
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
		throw new Error("UI-01 seed failed: " + JSON.stringify(result));
	}
}

async function openHome(page: import("@playwright/test").Page, configId = NA_CONFIG) {
	await page.goto(`${UI01}/${encodeURIComponent(configId)}`);
	await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
	await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${configId}`), { timeout: 15_000 });
}

test.describe.configure({ mode: "serial" });

test.describe("UI-01 Tender Configuration Home", () => {
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

	test("C1-M3 layout: structural contract + nine cards + pack copy", async ({ page }) => {
		await openHome(page);
		await expectUi01StructuralLayout(page);
		await expectUi01NineCards(page, CFG_TITLES);
		await expectConfigurationContextStrip(page, {
			family: /Information Technology/i,
			status: /Needs attention/i,
			issues: /Blockers/i,
			stdDocument: /IT Standard Tender Document/i,
		});
		await expect(page.getByTestId("kt-cl-ui01-next-label")).toContainText(/Next step:/i);
		const startBorder = await page
			.getByTestId("kt-cl-ui01-step-action-CFG-01")
			.evaluate((el) => getComputedStyle(el).borderStyle);
		expect(startBorder === "none" || startBorder === "").toBeTruthy();

		/* Affordance: filled navy CTA with back icon (not a ghost/outline text control). */
		const back = page.getByTestId("kt-cl-ui01-back");
		await expect(back.locator(".kt-cl-ui01-back-icon")).toBeVisible();
		const backLook = await back.evaluate((el) => {
			const cs = getComputedStyle(el);
			return {
				bg: cs.backgroundColor,
				color: cs.color,
				display: cs.display,
				weight: cs.fontWeight,
			};
		});
		expect(backLook.bg).toMatch(/rgb\(0,\s*34,\s*68\)/);
		expect(backLook.color).toMatch(/rgb\(255,\s*255,\s*255\)/);
		expect(backLook.display).toContain("flex");
		expect(Number.parseInt(backLook.weight, 10)).toBeGreaterThanOrEqual(600);
	});

	test("refresh keeps the same configuration (route segment)", async ({ page }) => {
		await openHome(page);
		await expect(page.getByTestId("kt-cl-ui01-next-action")).toBeVisible();
		await expect(page.getByTestId("kt-cl-config-context-strip")).toBeVisible();

		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${NA_CONFIG}`));
		await expect(page.getByTestId("kt-cl-ui01-empty-hint")).toHaveCount(0);
		await expect(page.getByText(/Select a tender configuration from the dashboard/i)).toHaveCount(0);
		await expect(page.getByTestId("kt-cl-ui01-next-action")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-config-context-strip")).toBeVisible();
		await expect(page.getByTestId("kt-cl-ui01-handoff")).toBeVisible();
	});

	test("step card navigates to step form; details opens drawer; Review matches card", async ({
		page,
	}) => {
		await openHome(page);

		await page.getByTestId("kt-cl-ui01-step-details-CFG-03").click();
		await expect(page.getByTestId("kt-cl-ui01-drawer")).toBeVisible({ timeout: 10_000 });
		await expect(page.getByTestId("kt-cl-ui01-drawer-title")).toHaveText(/IT Requirements/i);
		await expect(page.getByTestId("kt-cl-ui01-drawer-issues")).toContainText(/Blockers/i);
		await expect(page.getByTestId("kt-cl-ui01-drawer-will")).not.toBeEmpty();
		await expect(page.getByTestId("kt-cl-ui01-drawer-wont")).not.toBeEmpty();

		const drawerGeom = await page.evaluate(() => {
			const overlay = document.querySelector(
				'[data-testid="kt-cl-ui01-drawer-overlay"]'
			) as HTMLElement | null;
			const panel = document.querySelector('[data-testid="kt-cl-ui01-drawer"]') as HTMLElement | null;
			const home = document.querySelector('[data-testid="kt-cl-ui01-root"]') as HTMLElement | null;
			if (!overlay || !panel || !home) {
				return { ok: false, reason: "missing nodes" };
			}
			const ocs = getComputedStyle(overlay);
			const pcs = getComputedStyle(panel);
			const or = overlay.getBoundingClientRect();
			const pr = panel.getBoundingClientRect();
			return {
				ok: true,
				overlayFixed: ocs.position === "fixed",
				overlayFull: or.width >= window.innerWidth - 2 && or.height >= window.innerHeight - 2,
				panelOnRight: pr.right >= window.innerWidth - 4 && pr.left > window.innerWidth * 0.35,
				panelNarrow: pr.width <= 480,
				homeStillPresent: !!home.offsetParent || home.getClientRects().length > 0,
				panelFlex: pcs.display.includes("flex"),
			};
		});
		expect(drawerGeom.ok, JSON.stringify(drawerGeom)).toBe(true);
		expect(drawerGeom.overlayFixed, JSON.stringify(drawerGeom)).toBe(true);
		expect(drawerGeom.overlayFull, JSON.stringify(drawerGeom)).toBe(true);
		expect(drawerGeom.panelOnRight, JSON.stringify(drawerGeom)).toBe(true);
		expect(drawerGeom.panelNarrow, JSON.stringify(drawerGeom)).toBe(true);

		await page.getByTestId("kt-cl-ui01-drawer-close").click();
		await expect(page.getByTestId("kt-cl-ui01-drawer")).toHaveCount(0);

		await page.getByTestId("kt-cl-ui01-step-CFG-01").locator(".kt-cl-ui01-step-title").click();
		await expect(page).toHaveURL(/it-tender-configuration-tender-profile/, { timeout: 15_000 });
		await expect(page.locator('[data-testid="kt-cl-cfg01-root"]')).toBeVisible({
			timeout: 20_000,
		});
		await expect(page.getByTestId("kt-cl-ui01-drawer")).toHaveCount(0);

		await openHome(page);
		await page.getByTestId("kt-cl-ui01-step-details-CFG-01").click();
		await expect(page.getByTestId("kt-cl-ui01-drawer")).toBeVisible({ timeout: 10_000 });
		await page.getByTestId("kt-cl-ui01-drawer-action").click();
		await expect(page).toHaveURL(/it-tender-configuration-tender-profile/, { timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-ui01-drawer")).toHaveCount(0);
		await expect(page.locator('[data-testid="kt-cl-cfg01-root"]')).toBeVisible({
			timeout: 20_000,
		});

		await openHome(page);
		await page.getByTestId("kt-cl-ui01-step-action-CFG-01").click();
		await expect(page).toHaveURL(/it-tender-configuration-tender-profile/, { timeout: 15_000 });
	});
});

