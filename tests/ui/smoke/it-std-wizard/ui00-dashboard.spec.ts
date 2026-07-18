import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	expectKtClFilterBarLayout,
	expectKtClPageSizeWired,
	expectKtClQueueTableFooter,
	expectKtClToolbarChrome,
} from "../../helpers/ktClQueueContract";

/**
 * UI-00 Tender Configurations Dashboard + UI-M01 create modal (C1-M1 / C1-M2).
 * Serial + single seed: avoids Administrator session stomping when workers share Redis.
 * Shared chrome/filter/footer contracts also live in kt-cl-queue-pattern-lock.spec.ts (make ui-civic-ledger-queue-gate).
 */

const UI00 = "/desk/it-tender-configuration-dashboard";
const ROOT = '[data-testid="kt-cl-ui00-root"]';
const TABLE = '[data-testid="kt-cl-ui00-table"]';
const ISSUE_FILTER = '[data-testid="kt-cl-ui00-filter-issue_status"]';
const TAB_READY = '[data-testid="kt-cl-ui00-tab-ready_to_configure"]';
const TAB_IP = '[data-testid="kt-cl-ui00-tab-in_progress"]';
const CREATE_HEADER = '[data-testid="kt-cl-action-create-tender-config"]';
const MODAL = '[data-testid="kt-cl-uim01-modal"]';

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
	if (!result || !(result as { ready_packages?: string[] }).ready_packages) {
		throw new Error("UI-00 seed failed: " + JSON.stringify(result));
	}
}

test.describe.configure({ mode: "serial" });

test.describe("UI-00 Tender Configurations Dashboard", () => {
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

	test("toolbar trail is context; page H1 is leaf; right cluster has user meta", async ({ page }) => {
		await page.goto(UI00);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });

		await expectKtClToolbarChrome(page, {
			currentCrumb: /Tender Management/i,
			pageTitle: /Tender Configurations/i,
			ancestorLink: /Dashboard/i,
		});

		const trail = page.getByTestId("kt-cl-toolbar").getByTestId("kt-cl-breadcrumbs");
		await trail.getByRole("link", { name: /Dashboard/i }).click();
		await expect(page).toHaveURL(/Workspaces\/Procurement(%20| )Home|procurement-home/i, {
			timeout: 15_000,
		});
	});

	test("Ready tab shows package columns and Create Configuration", async ({ page }) => {
		await page.goto(UI00);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator(TAB_READY)).toBeVisible();
		await expect(page.locator(TABLE)).toBeVisible({ timeout: 15_000 });
		await expect(page.getByText("Procurement Package Ref").first()).toBeVisible();
		await expect(page.locator('[data-testid="kt-cl-ui00-create-row"]').first()).toBeVisible();
		await expect(page.getByText("Configuration Ref")).toHaveCount(0);
	});

	test("filter bar: outline-variant borders, search fills leftover space, wired filters", async ({
		page,
	}) => {
		await page.goto(UI00);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator(TABLE)).toBeVisible({ timeout: 15_000 });

		await expectKtClFilterBarLayout(page, {
			sampleFilterKey: "std_family",
			sameRowFilterKey: "procurement_method",
		});

		const bar = page.getByTestId("kt-cl-filter-bar");
		const search = bar.locator('[data-filter="search"]');
		const family = bar.locator('[data-filter="std_family"]');

		await family.selectOption({ label: "Information Technology" });
		await expect
			.poll(async () => page.locator('[data-testid="kt-cl-ui00-create-row"]').count(), {
				timeout: 15_000,
			})
			.toBeGreaterThan(0);

		await search.fill("PP-ICT-WIZARD-MODAL-001");
		await expect
			.poll(async () => page.locator('[data-testid="kt-cl-ui00-create-row"]').count(), {
				timeout: 15_000,
			})
			.toBe(1);
		await expect(page.getByText("PP-ICT-WIZARD-MODAL-001").first()).toBeVisible();
	});

	test("empty-state Refresh reloads the dashboard", async ({ page }) => {
		await page.goto(UI00);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator(TABLE)).toBeVisible({ timeout: 15_000 });

		await page.evaluate(() => {
			// @ts-expect-error desk
			window.__ktUi00DashCalls = 0;
			// @ts-expect-error desk
			const orig = frappe.call.bind(frappe);
			// @ts-expect-error desk
			frappe.call = function (opts) {
				if (String((opts && opts.method) || "").includes("get_tender_configurations_dashboard")) {
					// @ts-expect-error desk
					window.__ktUi00DashCalls += 1;
				}
				return orig(opts);
			};
		});

		const search = page.locator('[data-filter="search"]');
		await search.fill("ZZZ-NO-SUCH-PACKAGE-999");
		await expect(page.getByTestId("kt-cl-ui00-empty")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-ui00-empty-action")).toHaveText(/Refresh/i);

		const before = await page.evaluate(() => (window as unknown as { __ktUi00DashCalls: number }).__ktUi00DashCalls);
		await page.getByTestId("kt-cl-ui00-empty-action").click();
		await expect
			.poll(
				async () =>
					page.evaluate(() => (window as unknown as { __ktUi00DashCalls: number }).__ktUi00DashCalls),
				{ timeout: 15_000 }
			)
			.toBeGreaterThan(before);
		await expect(page.getByTestId("kt-cl-ui00-empty")).toBeVisible();
	});

	test("table footer: Rows per page left of pager and wired", async ({ page }) => {
		await page.goto(UI00);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator(TABLE)).toBeVisible({ timeout: 15_000 });

		await expectKtClQueueTableFooter(page);
		await expectKtClPageSizeWired(page, {
			methodIncludes: "get_tender_configurations_dashboard",
			selectValue: "10",
		});
	});

	test("In Progress tab shows configuration columns; Issue Status visible", async ({ page }) => {
		await page.goto(UI00);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator(ISSUE_FILTER)).toBeHidden();

		await page.locator(TAB_IP).click();
		await expect(page.getByText("Configuration Ref").first()).toBeVisible({ timeout: 15_000 });
		await expect(page.getByText("Next Action").first()).toBeVisible();
		await expect(page.locator(ISSUE_FILTER)).toBeVisible();
		await expect(page.locator('[data-testid="kt-cl-ui00-next-action"]').first()).toBeVisible();
	});

	test("summary KPIs reflect seeded counts", async ({ page }) => {
		await page.goto(UI00);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		const values = page.locator('[data-testid="kt-cl-queue-summary-value"]');
		await expect(values).toHaveCount(4);
		const texts = await values.allTextContents();
		expect(Number(texts[0])).toBeGreaterThanOrEqual(2);
		expect(Number(texts[1])).toBeGreaterThanOrEqual(1);
		expect(Number(texts[2])).toBeGreaterThanOrEqual(1);
		expect(Number(texts[3])).toBeGreaterThanOrEqual(1);
	});

	test("row Create Configuration opens modal with package context", async ({ page }) => {
		await page.goto(UI00);
		await expect(page.locator('[data-testid="kt-cl-ui00-create-row"]').first()).toBeVisible({
			timeout: 30_000,
		});
		await page.locator('[data-testid="kt-cl-ui00-create-row"]').first().click();
		await expect(page.locator(MODAL)).toBeVisible({ timeout: 15_000 });
		await expect(page.locator('[data-testid="kt-cl-uim01-preview"]')).toBeVisible({
			timeout: 10_000,
		});
		await page.locator('[data-testid="kt-cl-uim01-close"]').click({ force: true });
		await expect(page.locator(MODAL)).toHaveCount(0);
	});

	test("Create modal opens from header and creates configuration", async ({ page }) => {
		await page.goto(UI00);
		await expect(page.locator(CREATE_HEADER)).toBeVisible({ timeout: 30_000 });
		await page.locator(CREATE_HEADER).click();
		await expect(page.locator(MODAL)).toBeVisible({ timeout: 15_000 });
		await expect(page.getByText("Create Tender Configuration").first()).toBeVisible();

		await page.locator('[data-testid="kt-cl-uim01-package-trigger"]').click();
		const option = page.locator('[data-testid="kt-cl-uim01-option"]').first();
		await expect(option).toBeVisible({ timeout: 10_000 });
		await option.click();
		await expect(page.locator('[data-testid="kt-cl-uim01-preview"]')).toBeVisible();

		await page.locator('[data-testid="kt-cl-uim01-create"]').click();
		await expect(page.locator('[data-testid="kt-cl-ui01-stub"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator('[data-testid="kt-cl-ui01-ref"]')).not.toBeEmpty();
	});
});
