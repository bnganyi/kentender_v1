import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { expectUi01StructuralLayout } from "../../helpers/ktClUi01LayoutContract";

/**
 * UI-01 mockup configurations — SHOWCASE + CFG-01…09 focus fixtures.
 * Seed: seed_ui01_mockups_for_tests
 */

const PAGE_SLUG = "it-tender-configuration-overview";
const ROOT = '[data-testid="kt-cl-ui01-root"]';

const CFG_FOCUS = [
	{ id: "CFG-01", ref: "TCFG-MOCK-CFG-01", status: /Not started/i },
	{ id: "CFG-02", ref: "TCFG-MOCK-CFG-02", status: /Not started/i },
	{ id: "CFG-03", ref: "TCFG-MOCK-CFG-03", status: /Needs attention/i },
	{ id: "CFG-04", ref: "TCFG-MOCK-CFG-04", status: /In progress/i },
	{ id: "CFG-05", ref: "TCFG-MOCK-CFG-05", status: /Not started/i },
	{ id: "CFG-06", ref: "TCFG-MOCK-CFG-06", status: /Not started/i },
	{ id: "CFG-07", ref: "TCFG-MOCK-CFG-07", status: /Not started/i },
	{ id: "CFG-08", ref: "TCFG-MOCK-CFG-08", status: /Not started/i },
	{ id: "CFG-09", ref: "TCFG-MOCK-CFG-09", status: /Not available yet/i },
];

async function seedMockups(page: import("@playwright/test").Page) {
	await page.waitForFunction(() => typeof (window as unknown as { frappe?: unknown }).frappe !== "undefined");
	const result = await page.evaluate(async () => {
		// @ts-expect-error frappe on desk
		const r = await frappe.call({
			method: "kentender_procurement.tender_configurations.seed_ui01_mockups_for_tests",
			args: { clear: 1 },
		});
		return r.message || r;
	});
	if (!result || !(result as { showcase_id?: string }).showcase_id) {
		throw new Error("UI-01 mockup seed failed: " + JSON.stringify(result));
	}
	return result as { showcase_id: string; by_step: Record<string, string> };
}

test.describe.configure({ mode: "serial" });

test.describe("UI-01 mockup configurations (9 CFG states + showcase)", () => {
	let showcaseId = "TCFG-MOCK-SHOWCASE";

	test.beforeAll(async ({ browser }) => {
		const page = await browser.newPage();
		await page.setViewportSize({ width: 1280, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		const seed = await seedMockups(page);
		showcaseId = seed.showcase_id || showcaseId;
		await page.close();
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1280, height: 900 });
		await loginAsAdministrator(page);
	});

	test("SHOWCASE home shows all five step statuses across nine cards", async ({ page }) => {
		await page.goto(`/desk/${PAGE_SLUG}/${encodeURIComponent(showcaseId)}`);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expectUi01StructuralLayout(page);

		const statuses = await page.evaluate(() => {
			const out: Record<string, string> = {};
			for (let i = 1; i <= 9; i++) {
				const id = `CFG-0${i}`;
				const el = document.querySelector(`[data-testid="kt-cl-ui01-step-${id}"]`);
				out[id] = el?.getAttribute("data-step-status") || "";
			}
			return out;
		});
		expect(statuses["CFG-01"]).toBe("Complete");
		expect(statuses["CFG-02"]).toBe("Complete");
		expect(statuses["CFG-03"]).toBe("Needs attention");
		expect(statuses["CFG-04"]).toBe("In progress");
		expect(statuses["CFG-05"]).toBe("Not started");
		expect(statuses["CFG-09"]).toBe("Not available yet");
		await expect(page.getByTestId("kt-cl-ui01-step-progress-CFG-04")).toBeVisible();
		const fillW = await page
			.getByTestId("kt-cl-ui01-step-progress-CFG-04")
			.locator(".kt-cl-ui01-step-progress-fill")
			.evaluate((el) => el.getBoundingClientRect().width);
		expect(fillW).toBeGreaterThan(20);
		await expect(page.getByTestId("kt-cl-ui01-progress")).toBeVisible();
		await expect(page.getByTestId("kt-cl-ui01-resources")).toBeVisible();
		await expect(page.getByTestId("kt-cl-ui01-next-label")).toContainText(/Fix IT Requirements/i);
		await expect(page.getByTestId("kt-cl-ui01-drawer")).toHaveCount(0);
		await page.getByTestId("kt-cl-ui01-step-CFG-03").click();
		await expect(page.getByTestId("kt-cl-ui01-drawer-issues")).toContainText(/Blockers/i);
	});

	for (const focus of CFG_FOCUS) {
		test(`${focus.id} mockup focuses card status`, async ({ page }) => {
			await page.goto(`/desk/${PAGE_SLUG}/${encodeURIComponent(focus.ref)}`);
			await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
			const status = await page
				.getByTestId(`kt-cl-ui01-step-${focus.id}`)
				.getAttribute("data-step-status");
			expect(status).toMatch(focus.status);
			await expect(page.getByTestId(`kt-cl-ui01-step-badge-${focus.id}`)).toBeVisible();
		});
	}
});
