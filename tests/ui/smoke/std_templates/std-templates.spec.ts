import { execSync } from "node:child_process";
import { expect, Page, test } from "@playwright/test";

import { login } from "../../helpers/auth";

/**
 * STD-TPL-001 v0.10 §11 / STD-TPL-IMP-001 v1.0 §11 — STD Templates in a real
 * browser, as real personas, against the installed IT-EQUIPMENT-OPEN-V1 1.1,
 * switched On (`make std-release-install`; owner decision OD5 — a release is an
 * On/Off switch on a site). Covers the switch itself, the list, filters and their
 * refresh, the detail sections, coverage/change panels with paging, refresh
 * and Back/Forward, Report concern (invalid then valid, no Frappe modal), the
 * access matrix, a forced read failure, keyboard use and 390 px cards.
 */

const BENCH = process.env.BENCH_ROOT || "/home/midasuser/frappe-bench";
const SITE = process.env.UI_SITE || "kentender.midas.com";
const PASSWORD = process.env.UI_TND_OFFICER_PASSWORD || "Test@123";
const OFFICER = process.env.UI_TND_OFFICER_USER || "brian.wafula@moh.example.test";
const HOPF = process.env.UI_TND_HOPF_USER || "charles.mutiso@moh.example.test";
const AUDITOR = process.env.UI_TND_AUDITOR_USER || "naomi.chebet@moh.example.test";
const RELEASE = "stdr-0e81b40c-d548-498c-855a-d4f80764af40";
const ROW = '[data-testid="stdt-row-IT-EQUIPMENT-OPEN-V1-1.1"]';

function purgeConcerns() {
	execSync(`bench --site ${SITE} execute kentender_procurement.std_templates.tests.playwright_fixtures.purge_playwright_concerns`, { cwd: BENCH, stdio: "pipe" });
}

function setSwitch(state: "On" | "Off") {
	execSync(
		`bench --site ${SITE} execute kentender_procurement.std_templates.services.lifecycle.switch --kwargs "{'release_id': '${RELEASE}', 'state': '${state}', 'actor': 'Playwright'}"`,
		{ cwd: BENCH, stdio: "pipe" },
	);
}

function pageErrors(page: Page) {
	const errors: string[] = [];
	page.on("pageerror", (e) => errors.push(String(e)));
	return errors;
}

async function openList(page: Page, hash = "") {
	await page.goto(`/app/std-templates${hash}`, { waitUntil: "domcontentloaded" });
	await page.waitForSelector('[data-testid="stdt-list-table"], [data-testid="stdt-list-filtered-empty"], [data-testid="stdt-state-forbidden"]');
}

async function openDetail(page: Page, hash = "") {
	await page.goto(`/app/std-templates/${RELEASE}${hash}`, { waitUntil: "domcontentloaded" });
	await page.waitForSelector('[data-testid="stdt-detail"], [data-testid="stdt-state-not-found"], [data-testid="stdt-detail-failure"]');
}

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("STD Templates", () => {
	test.beforeAll(() => setSwitch("On"));
	test.afterAll(() => {
		setSwitch("On");
		purgeConcerns();
	});

	test("officer: list row, status filter, filtered empty, refresh keeps the filter", async ({ page }) => {
		const errors = pageErrors(page);
		await login(page, OFFICER, PASSWORD);
		await openList(page);
		await expect(page.locator(".kt-page-title")).toHaveText("STD Templates");
		const row = page.locator(ROW);
		await expect(row.locator(".kt-status")).toHaveText("Available");
		await expect(row).not.toContainText("cannot be used");
		await expect(page.locator('[data-testid="stdt-clear-filters"]')).toHaveCount(0);
		for (const forbidden of ["Add", "Edit", "Activate", "Approve", "Upload", "Replace", "Repair"]) {
			await expect(page.getByRole("button", { name: forbidden, exact: true })).toHaveCount(0);
		}

		await page.selectOption('[data-testid="stdt-filter-status"]', "Withdrawn");
		await expect(page.locator('[data-testid="stdt-list-filtered-empty"]')).toContainText("No STD Templates match these filters.");
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="stdt-list-filtered-empty"]')).toBeVisible();
		await expect(page.locator('[data-testid="stdt-filter-status"]')).toHaveValue("Withdrawn");
		await page.locator('[data-testid="stdt-list-filtered-empty"] button').click();
		await expect(page.locator(ROW)).toBeVisible();
		expect(errors).toEqual([]);
	});

	test("officer: detail sections, panels, refresh and Back/Forward keep the state", async ({ page }) => {
		const errors = pageErrors(page);
		await login(page, OFFICER, PASSWORD);
		await openList(page);
		await page.click('[data-testid="stdt-view-IT-EQUIPMENT-OPEN-V1-1.1"]');
		await expect(page.locator('[data-testid="stdt-detail"]')).toBeVisible();
		await expect(page.locator('[data-testid="stdt-detail-status"]')).toHaveText("Available");
		await expect(page.locator('[data-testid="stdt-consequence"]')).toHaveText("This release may be used only for the supported procurements below.");
		await expect(page.locator('[data-testid="stdt-blockers"]')).toContainText("No blockers.");
		await expect(page.locator(".kt-rail-mount")).toContainText("STD Templates");
		await expect(page.locator(".kt-rail-mount")).toContainText("IT Equipment Open Tender");
		for (const section of ["overview", "content", "bid", "coverage", "verification"]) {
			await expect(page.locator(`[data-testid="stdt-section-${section}"] h2`)).toBeVisible();
		}
		await expect(page.locator('[data-testid="stdt-verification-table"] tbody tr')).toHaveCount(8);
		await expect(page.locator('[data-testid="stdt-verification-table"] tbody tr').last()).toContainText("Site switch");
		await expect(page.locator('[data-testid="stdt-verification-table"] tbody tr').last()).toContainText("On");
		await expect(page.locator('[data-testid="stdt-detail"]')).not.toContainText("APPROVE EXACT MANIFEST");
		await expect(page.locator('[data-testid="stdt-treatments"]')).toContainText("296");
		// digests stay inside Technical details
		await expect(page.locator("#stdt-technical-body")).toHaveCount(0);

		await page.click('[data-testid="stdt-coverage-disclosure"] button');
		await expect(page.locator('[data-testid="stdt-coverage-row-COV-001"]')).toBeVisible();
		await page.selectOption('[data-testid="stdt-coverage-treatment"]', "Excluded with reason");
		await expect(page.locator('[data-testid="stdt-coverage-pager"]')).toContainText("Page 1 of");
		await page.locator('[data-testid="stdt-coverage-pager"] button', { hasText: "Next" }).click();
		await expect(page.locator('[data-testid="stdt-coverage-pager"]')).toContainText("Page 2 of");
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="stdt-coverage-pager"]')).toContainText("Page 2 of");
		await expect(page.locator('[data-testid="stdt-coverage-treatment"]')).toHaveValue("Excluded with reason");

		await page.click('[data-testid="stdt-changes-disclosure"] button');
		await page.selectOption('[data-testid="stdt-change-category"]', "Response rules");
		await expect(page.locator('[data-testid="stdt-change-details"] tbody tr').first()).toContainText("Response rules");
		await expect(page.locator('[data-testid="stdt-change-details"]')).not.toContainText("{");

		await page.click('[data-testid="stdt-technical"] button');
		await expect(page.locator("#stdt-technical-body")).toContainText(RELEASE);

		await page.click('[data-testid="stdt-back"]');
		await expect(page.locator('[data-testid="stdt-list-table"]')).toBeVisible();
		await page.goBack();
		await expect(page.locator('[data-testid="stdt-detail"]')).toBeVisible();
		await expect(page.locator("#stdt-technical-body")).toBeVisible();
		await expect(page.locator('[data-testid="stdt-change-category"]')).toHaveValue("Response rules");
		await page.goForward();
		await expect(page.locator('[data-testid="stdt-list-table"]')).toBeVisible();
		expect(errors).toEqual([]);
	});

	test("switched off: Unavailable with the switch as its one blocker; switching on restores it", async ({ page }) => {
		const errors = pageErrors(page);
		await login(page, OFFICER, PASSWORD);
		setSwitch("Off");
		try {
			await openList(page);
			await expect(page.locator(ROW).locator(".kt-status")).toHaveText("Unavailable");
			await expect(page.locator(ROW)).toContainText("This release cannot be used to publish a Tender. Open it to see why.");
			await openDetail(page);
			await expect(page.locator('[data-testid="stdt-detail-status"]')).toHaveText("Unavailable");
			await expect(page.locator('[data-testid="stdt-blockers"] li')).toHaveCount(1);
			await expect(page.locator('[data-testid="stdt-blockers"]')).toContainText("This release is switched off on this site.");
			await expect(page.locator('[data-testid="stdt-verification-table"] tbody tr').last()).toContainText("Off");
		} finally {
			setSwitch("On");
		}
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="stdt-detail-status"]')).toHaveText("Available");
		expect(errors).toEqual([]);
	});

	test("officer: direct load on a section lands on it", async ({ page }) => {
		await login(page, OFFICER, PASSWORD);
		await openDetail(page, "#section=verification");
		await expect(page.locator("#stdt-verification")).toBeInViewport();
	});

	test("officer: Report concern — inline errors, no Frappe modal, then a recorded concern that changes nothing", async ({ page }) => {
		const errors = pageErrors(page);
		await login(page, OFFICER, PASSWORD);
		await openDetail(page);
		await page.click('[data-testid="stdt-report-concern"]');
		await expect(page.locator('[data-testid="stdt-rc-category"]')).toBeFocused();
		await page.click('[data-testid="stdt-rc-submit"]');
		await expect(page.locator(".stdt-dialog .kt-field-error")).toHaveCount(3);
		await expect(page.locator(".modal.show")).toHaveCount(0);
		await page.selectOption('[data-testid="stdt-rc-category"]', "Source treatment");
		await page.fill('[data-testid="stdt-rc-locator"]', "STD row 184");
		await page.fill('[data-testid="stdt-rc-summary"]', "Playwright: confirm exclusion reason");
		await page.fill('[data-testid="stdt-rc-description"]', "Browser check: the exclusion reason for this row should name its source basis.");
		await page.click('[data-testid="stdt-rc-submit"]');
		await expect(page.locator('[data-testid="stdt-concern-reported"]')).toContainText("does not change this release's availability");
		await expect(page.locator('[data-testid="stdt-own-concerns"]')).toContainText("Playwright: confirm exclusion reason");
		await expect(page.locator('[data-testid="stdt-detail-status"]')).toHaveText("Available");
		expect(errors).toEqual([]);
	});

	test("Escape closes the concern dialog; keyboard reaches the section links", async ({ page }) => {
		await login(page, OFFICER, PASSWORD);
		await openDetail(page);
		await page.click('[data-testid="stdt-report-concern"]');
		await page.keyboard.press("Escape");
		await expect(page.locator('[data-testid="stdt-concern-dialog"]')).toHaveCount(0);
		await page.locator('[data-testid="stdt-back"]').focus();
		let reached = false;
		for (let i = 0; i < 40 && !reached; i += 1) {
			await page.keyboard.press("Tab");
			reached = await page.evaluate(() => document.activeElement?.getAttribute("data-testid") === "stdt-nav-overview");
		}
		expect(reached).toBe(true);
		await page.keyboard.press("Enter");
		await expect(page).toHaveURL(/section=overview/);
	});

	test("head of procurement function reads the release", async ({ page }) => {
		await login(page, HOPF, process.env.UI_TND_HOPF_PASSWORD || PASSWORD);
		await openDetail(page);
		await expect(page.locator('[data-testid="stdt-detail"]')).toBeVisible();
	});

	test("auditor: forbidden list, masked detail, no menu item", async ({ page }) => {
		await login(page, AUDITOR, process.env.UI_TND_AUDITOR_PASSWORD || PASSWORD);
		await openList(page);
		await expect(page.locator('[data-testid="stdt-state-forbidden"]')).toContainText("You do not have access to STD Templates");
		await openDetail(page);
		await expect(page.locator('[data-testid="stdt-state-not-found"]')).toContainText("STD Template not found");
		await expect(page.locator('.sidebar-item-label', { hasText: "STD Templates" })).toHaveCount(0);
		const preview = await page.request.get(`/api/method/kentender_procurement.std_templates.api.preview_std_template_document?release_id=${RELEASE}&output_id=invitation`);
		expect(preview.status()).toBe(404);
	});

	test("a read failure says so and recovers with Try again", async ({ page }) => {
		await login(page, OFFICER, PASSWORD);
		await page.route("**/api/method/kentender_procurement.std_templates.api.get_std_template*", (route) => route.fulfill({ status: 500, body: "{}" }));
		await openDetail(page);
		await expect(page.locator('[data-testid="stdt-detail-failure"]')).toContainText("STD Template details could not be loaded. Try again.");
		await page.unroute("**/api/method/kentender_procurement.std_templates.api.get_std_template*");
		await page.click('[data-testid="stdt-detail-retry"]');
		await expect(page.locator('[data-testid="stdt-detail"]')).toBeVisible();
	});

	test("390 px: the list becomes labelled cards without horizontal scrolling", async ({ page }) => {
		await page.setViewportSize({ width: 390, height: 844 });
		await login(page, OFFICER, PASSWORD);
		await openList(page);
		const overflow = await page.evaluate(() => {
			const root = document.querySelector(".kt-stdt .kt-page") as HTMLElement;
			return root.scrollWidth - root.clientWidth;
		});
		expect(overflow).toBeLessThanOrEqual(1);
		const label = await page.locator(`${ROW} td[data-label="Status"]`).evaluate((el) => getComputedStyle(el, "::before").content);
		expect(label).toContain("Status");
		await openDetail(page, "#section=verification");
		const cardLabel = await page.locator('[data-testid="stdt-verification-table"] td[data-label="Result"]').first().evaluate((el) => getComputedStyle(el, "::before").content);
		expect(cardLabel).toContain("Result");
	});
});
