import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { expectConfigurationContextStrip } from "../../helpers/ktClConfigContext";

/**
 * CFG-02 Tender Data Sheet (C2-CFG2).
 * Route: /desk/it-tender-configuration-tds/<configuration_id>
 */

const PAGE_SLUG = "it-tender-configuration-tds";
const CFG02 = `/desk/${PAGE_SLUG}`;
const ROOT = '[data-testid="kt-cl-cfg02-root"]';
const CONFIG = "TCFG-SEED-TCFG-IP";

const FORBIDDEN = [
	/\bEdit ITT\b/i,
	/\bClause Configuration\b/i,
	/\bRule Matrix\b/i,
	/\bSTD Parameter Editor\b/i,
	/\bTender Shell\b/i,
	/\bFinalize\b/i,
	/\bPublish\b/i,
	/\bschema version\b/i,
	/\bclause ID\b/i,
	/\bhash\b/i,
];

const SECTIONS = [
	"communication",
	"key_dates",
	"submission",
	"eligibility",
	"security",
	"preferences",
	"bid_opening",
] as const;

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
		throw new Error("CFG-02 seed failed: " + JSON.stringify(result));
	}
}

async function openTds(page: import("@playwright/test").Page, configId = CONFIG) {
	await page.goto(`${CFG02}/${encodeURIComponent(configId)}`);
	await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
	await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${configId}`), { timeout: 15_000 });
	await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
}

async function expectCfg02Layout(page: import("@playwright/test").Page) {
	const layout = page.getByTestId("kt-cl-cfg02-layout");
	await expect(layout).toBeVisible();
	await expect(page.getByTestId("kt-cl-cfg02-main")).toBeVisible();
	await expect(page.getByTestId("kt-cl-cfg02-side")).toBeVisible();
	const geometry = await page.evaluate(() => {
		const main = document.querySelector('[data-testid="kt-cl-cfg02-main"]') as HTMLElement | null;
		const side = document.querySelector('[data-testid="kt-cl-cfg02-side"]') as HTMLElement | null;
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

/** Guidance rail should float (sticky) while the form sections scroll (code.html top-20). */
async function expectGuidanceFloatsOnScroll(page: import("@playwright/test").Page) {
	const before = await page.evaluate(() => {
		const side = document.querySelector('[data-testid="kt-cl-cfg02-side"]') as HTMLElement | null;
		const scroller = document.querySelector(
			'.kt-cl-native-canvas > main'
		) as HTMLElement | null;
		if (!side || !scroller) {
			return { ok: false, reason: "missing side/scroller" };
		}
		const pos = getComputedStyle(side).position;
		return {
			ok: true,
			position: pos,
			topBefore: side.getBoundingClientRect().top,
			scrollTopBefore: scroller.scrollTop,
		};
	});
	expect(before.ok, JSON.stringify(before)).toBe(true);
	expect(before.position).toBe("sticky");

	const after = await page.evaluate(() => {
		const side = document.querySelector('[data-testid="kt-cl-cfg02-side"]') as HTMLElement | null;
		const scroller = document.querySelector(
			'.kt-cl-native-canvas > main'
		) as HTMLElement | null;
		const bid = document.querySelector(
			'[data-testid="kt-cl-cfg02-section-bid_opening"]'
		) as HTMLElement | null;
		if (!side || !scroller || !bid) {
			return { ok: false, reason: "missing nodes after scroll" };
		}
		/* Scroll the CFG-02 page scrollport (not the window). */
		bid.scrollIntoView({ block: "start", inline: "nearest" });
		scroller.scrollTop = Math.max(scroller.scrollTop, bid.offsetTop - 24);
		const sr = side.getBoundingClientRect();
		const br = bid.getBoundingClientRect();
		const mainBox = scroller.getBoundingClientRect();
		return {
			ok: true,
			scrollTop: scroller.scrollTop,
			sideTop: sr.top,
			bidTop: br.top,
			mainTop: mainBox.top,
			/* Stuck near the top of the scrollport (allow padding / sticky offset). */
			stuckNearTop: sr.top <= mainBox.top + 56 && sr.top >= mainBox.top - 8,
			/* Form content moved; rail still visible in the scrollport. */
			formScrolledPastRail: scroller.scrollTop > 80,
			sideVisible: sr.bottom > mainBox.top && sr.top < mainBox.bottom,
		};
	});
	expect(after.ok, JSON.stringify(after)).toBe(true);
	expect(after.scrollTop, JSON.stringify(after)).toBeGreaterThan(40);
	expect(after.stuckNearTop, JSON.stringify(after)).toBe(true);
	expect(after.formScrolledPastRail, JSON.stringify(after)).toBe(true);
	expect(after.sideVisible, JSON.stringify(after)).toBe(true);
}

async function fillCompleteTds(page: import("@playwright/test").Page) {
	await page.getByTestId("kt-cl-cfg02-contact_officer").fill("Jane Doe");
	await page.getByTestId("kt-cl-cfg02-contact_email").fill("procurement@example.go.ke");
	await page.getByTestId("kt-cl-cfg02-clarification_submission_method").selectOption("E-Procurement Portal");
	await page.getByTestId("kt-cl-cfg02-clarification_deadline").fill("2026-08-01T12:00");
	await page.locator('input[name="kt-cl-cfg02-pre_tender_meeting"][value="No"]').check();
	await page.getByTestId("kt-cl-cfg02-tender_submission_deadline").fill("2026-08-15T17:00");
	await page.getByTestId("kt-cl-cfg02-tender_opening_datetime").fill("2026-08-15T17:30");
	await page.getByTestId("kt-cl-cfg02-bid_validity_period").fill("120");
	await page.getByTestId("kt-cl-cfg02-submission_channel").selectOption("E-Procurement Portal");
	await page.getByTestId("kt-cl-cfg02-submission_language").selectOption("English");
	await page.getByTestId("kt-cl-cfg02-tender_currency").selectOption("KES");
	await page.locator('input[name="kt-cl-cfg02-alternative_tenders_allowed"][value="No"]').check();
	await page.locator('input[name="kt-cl-cfg02-joint_ventures_allowed"][value="Yes"]').check();
	await page.getByTestId("kt-cl-cfg02-eligible_tenderers").selectOption("Open to all eligible tenderers");
	await page.locator('input[name="kt-cl-cfg02-reserved_procurement"][value="No"]').check();
	await page.locator('input[name="kt-cl-cfg02-tender_security_required"][value="No"]').check();
	await page.locator('input[name="kt-cl-cfg02-margin_of_preference_applies"][value="No"]').check();
	await page.getByTestId("kt-cl-cfg02-opening_method").selectOption("Electronic Opening");
	await page.getByTestId("kt-cl-cfg02-opening_location").fill("KenTender portal");
	await page.locator('input[name="kt-cl-cfg02-opening_attendance_allowed"][value="Yes"]').check();
}

test.describe.configure({ mode: "serial" });

test.describe("CFG-02 Tender Data Sheet", () => {
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

	test("layout: strip, 7 sections, guidance, footer CTAs, no forbidden terms", async ({ page }) => {
		await openTds(page);
		await expectConfigurationContextStrip(page, {
			family: /Information Technology/i,
			stdDocument: /IT Standard Tender Document/i,
		});
		await expectCfg02Layout(page);
		await expectGuidanceFloatsOnScroll(page);
		for (const key of SECTIONS) {
			await expect(page.getByTestId(`kt-cl-cfg02-section-${key}`)).toBeVisible();
		}
		await expect(page.getByTestId("kt-cl-cfg02-guidance")).toContainText(
			/Tender Data Sheet Guidance/i
		);
		await expect(page.getByTestId("kt-cl-cfg02-back")).toHaveText(/Back to Configuration Home/i);
		await expect(page.getByTestId("kt-cl-cfg02-save")).toHaveText(/Save Tender Data Sheet/i);
		await expect(page.getByTestId("kt-cl-cfg02-run-check")).toHaveText(/Run Check/i);
		await expect(page.getByTestId("kt-cl-cfg02-continue")).toHaveText(
			/Continue to IT Requirements/i
		);
		await expect(page.getByTestId("kt-cl-cfg02-continue")).toBeDisabled();

		// Not-started form: do not dump every missing required into a wall of red text.
		await expect(page.getByTestId("kt-cl-cfg02-blockers")).toHaveClass(/hidden/);
		await expect(page.getByTestId("kt-cl-cfg02-issues-toggle")).toHaveCount(0);
		await expect(page.locator(ROOT)).not.toContainText(/Add a contact officer before continuing/i);

		const body = await page.locator(ROOT).innerText();
		for (const re of FORBIDDEN) {
			expect(body, String(re)).not.toMatch(re);
		}
	});

	test("issues panel stays compact until work starts; expands on demand", async ({ page }) => {
		await openTds(page);
		await expect(page.getByTestId("kt-cl-cfg02-blockers")).toHaveClass(/hidden/);

		await page.getByTestId("kt-cl-cfg02-contact_officer").fill("Jane Doe");
		await page.getByTestId("kt-cl-cfg02-save").click();
		await expect(page.locator(".desk-alert .alert-message")).toContainText(/saved successfully/i, {
			timeout: 15_000,
		});

		const issues = page.getByTestId("kt-cl-cfg02-blockers");
		await expect(issues).toBeVisible();
		await expect(issues).not.toHaveClass(/hidden/);
		await expect(page.getByTestId("kt-cl-cfg02-issues-toggle")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg02-issues-summary")).toContainText(
			/items need attention|item needs attention/i
		);
		// Collapsed by default — detail list not shown.
		await expect(page.getByTestId("kt-cl-cfg02-issues-list")).toBeHidden();

		await page.getByTestId("kt-cl-cfg02-issues-toggle").click();
		await expect(page.getByTestId("kt-cl-cfg02-issues-list")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg02-issues-list")).toContainText(
			/contact email|submission deadline|opening location/i
		);

		await page.getByTestId("kt-cl-cfg02-issues-toggle").click();
		await expect(page.getByTestId("kt-cl-cfg02-issues-list")).toBeHidden();
	});

	test("conditional fields: meeting details and security appear when Yes", async ({ page }) => {
		await openTds(page);
		await expect(page.getByTestId("kt-cl-cfg02-pre_tender_meeting_details")).toBeHidden();
		await page.locator('input[name="kt-cl-cfg02-pre_tender_meeting"][value="Yes"]').check();
		await expect(page.getByTestId("kt-cl-cfg02-pre_tender_meeting_details")).toBeVisible();

		await expect(page.getByTestId("kt-cl-cfg02-tender_security_type")).toBeHidden();
		await page.locator('input[name="kt-cl-cfg02-tender_security_required"][value="Yes"]').check();
		await expect(page.getByTestId("kt-cl-cfg02-tender_security_type")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg02-tender_security_amount")).toBeVisible();
	});

	test("Save toast, Run Check refreshes issues, Continue enabled when complete", async ({
		page,
	}) => {
		await openTds(page);
		await fillCompleteTds(page);
		await expect(page.getByTestId("kt-cl-cfg02-save")).toBeEnabled();
		await page.getByTestId("kt-cl-cfg02-save").click();
		await expect(page.locator(".desk-alert .alert-message")).toContainText(
			/Tender Data Sheet saved successfully/i,
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-cl-cfg02-continue")).toBeEnabled({ timeout: 15_000 });

		await page.getByTestId("kt-cl-cfg02-run-check").click();
		await expect(page.locator(".desk-alert .alert-message")).toContainText(/Check complete/i, {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-cl-cfg02-blockers")).toHaveClass(/hidden/);
	});

	test("refresh keeps configuration id; lots allowed is read-only", async ({ page }) => {
		await openTds(page);
		await expect(page.getByTestId("kt-cl-cfg02-lots_allowed")).toHaveAttribute("readonly", "");
		await page.getByTestId("kt-cl-cfg02-contact_officer").fill("Refresh Officer");
		await page.getByTestId("kt-cl-cfg02-save").click();
		await expect(page.locator(".desk-alert .alert-message")).toContainText(/saved successfully/i, {
			timeout: 15_000,
		});
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${CONFIG}`), { timeout: 15_000 });
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-cl-cfg02-contact_officer")).toHaveValue("Refresh Officer");
	});

	test("CFG-01 Continue lands on live TDS page", async ({ page }) => {
		await page.goto(`/desk/it-tender-configuration-tender-profile/${encodeURIComponent(CONFIG)}`);
		await expect(page.getByTestId("kt-cl-cfg01-root")).toBeVisible({ timeout: 30_000 });
		await page.getByTestId("kt-cl-cfg01-title").fill("ERP Implementation Services");
		await page.getByTestId("kt-cl-cfg01-scope").fill(
			"Procurement of ERP software licences, implementation, training, and support for national treasury systems."
		);
		await page.getByTestId("kt-cl-cfg01-lot-single").check();
		await page.getByTestId("kt-cl-cfg01-continue").click();
		await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${CONFIG}`), { timeout: 20_000 });
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
	});
});
