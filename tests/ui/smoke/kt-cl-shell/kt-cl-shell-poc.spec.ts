import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	expectKtClShellChrome,
	gotoKtClShellPoc,
	KT_CL_BENTO,
	KT_CL_CALENDAR,
	KT_CL_CALENDAR_ITEM,
	KT_CL_DATA_TABLE,
	KT_CL_KPI_CARD,
	KT_CL_NAV_CHILD,
	KT_CL_NAV_GROUP,
	KT_CL_SIDEBAR_BRAND,
	KT_CL_SIDENAV,
	KT_CL_STATUS_CHIP,
	KT_CL_TABLE_FILTER,
	KT_CL_TABLE_FOOTER,
	KT_CL_TABLE_ROW,
	KT_CL_TOOLBAR,
	KT_CL_TOOLBAR_TITLE,
} from "../../helpers/ktClShell";

test.describe("Civic Ledger shell POC", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1280, height: 720 });
		await loginAsAdministrator(page);
	});

	test("renders full code.html chrome (sidebar + top bar + header)", async ({ page }) => {
		await gotoKtClShellPoc(page);
		await expectKtClShellChrome(page);
	});

	test("sidenav reproduces the curated mock IA", async ({ page }) => {
		await gotoKtClShellPoc(page);
		const nav = page.locator(KT_CL_SIDENAV);
		await expect(nav).toHaveClass(/w-64/);
		await expect(page.locator(KT_CL_SIDEBAR_BRAND)).toContainText(/Public Sector/i);

		// 7 top-level links + 2 collapsible groups = 9 items.
		await expect(nav.locator('[data-testid="kt-cl-nav-item"]')).toHaveCount(7);
		await expect(nav.locator(KT_CL_NAV_GROUP)).toHaveCount(2);

		for (const label of [
			"Procurement Home",
			"Analytics",
			"Strategy Alignment",
			"Budget & Funding",
			"Demand Intake & Approval",
			"Contract Management",
			"Supplier Management",
			"Tender Management",
			"STD Administration",
		]) {
			await expect(nav.getByText(label, { exact: true }).first()).toBeVisible();
		}

		// Active state on Procurement Home.
		await expect(nav.getByText("Procurement Home", { exact: true }).first()).toBeVisible();
		await expect(nav.locator("a.border-r-4.border-primary").first()).toContainText("Procurement Home");

		await expect(page.getByTestId("kt-cl-sidebar-settings")).toBeVisible();
		await expect(page.getByTestId("kt-cl-sidebar-support")).toBeVisible();
	});

	test("collapsible group toggles its children", async ({ page }) => {
		await gotoKtClShellPoc(page);
		const nav = page.locator(KT_CL_SIDENAV);
		// Tender Management group has 7 children, STD Administration has 4 = 11 total, expanded by default.
		await expect(nav.locator(KT_CL_NAV_CHILD)).toHaveCount(11);
		await expect(nav.getByText("Procurement Packages", { exact: true })).toBeVisible();

		// Collapse Tender Management.
		await nav.locator('[data-kt-cl-section="Tender Management"]').click();
		await expect(nav.getByText("Procurement Packages", { exact: true })).toBeHidden();
	});

	test("two-level children render with a refined connector + indentation + hover", async ({ page }) => {
		await gotoKtClShellPoc(page);
		const nav = page.locator(KT_CL_SIDENAV);

		// The children list draws a single tree connector line, aligned to the
		// RIGHT edge of the parent icon (36px), not a flat list.
		const childrenList = nav.locator('[data-kt-cl-nested="Tender Management"]');
		const listStyle = await childrenList.evaluate((el) => {
			const cs = getComputedStyle(el);
			return { border: cs.borderLeftWidth, style: cs.borderLeftStyle, marginLeft: cs.marginLeft };
		});
		expect(listStyle.border).toBe("1px");
		expect(listStyle.style).toBe("solid");
		expect(Math.round(parseFloat(listStyle.marginLeft))).toBe(36);

		// Child text is indented (aligned under the parent label at 48px).
		const child = childrenList.locator("a.kt-cl-nav-child").first();
		const paddingLeft = await child.evaluate((el) => getComputedStyle(el).paddingLeft);
		expect(Math.round(parseFloat(paddingLeft))).toBe(12);

		// Hover raises the child to the primary colour.
		await child.hover();
		await expect
			.poll(async () => child.evaluate((el) => getComputedStyle(el).color))
			.toBe("rgb(0, 11, 29)");
	});

	test("root nav links use the design highlight, not a link underline", async ({ page }) => {
		await gotoKtClShellPoc(page);
		const nav = page.locator(KT_CL_SIDENAV);
		const rootLink = nav.locator('[data-testid="kt-cl-nav-item"] a').first();

		// No underline at rest or on hover (Frappe's global a:hover underline must
		// be suppressed inside the rail).
		const restDecoration = await rootLink.evaluate((el) => getComputedStyle(el).textDecorationLine);
		expect(restDecoration).toBe("none");
		await rootLink.hover();
		await expect
			.poll(async () => rootLink.evaluate((el) => getComputedStyle(el).textDecorationLine))
			.toBe("none");
	});

	test("content area matches code.html blocks", async ({ page }) => {
		await gotoKtClShellPoc(page);

		// Bento: 3 KPI cards (2 metric + 1 progress).
		await expect(page.locator(KT_CL_BENTO)).toBeVisible();
		await expect(page.locator(KT_CL_KPI_CARD)).toHaveCount(3);
		await expect(page.locator('[data-testid="kt-cl-kpi-card"][data-variant="progress"]')).toHaveCount(1);
		await expect(page.locator(KT_CL_KPI_CARD).first()).toContainText("1,245");

		// Calendar: 3 upcoming tenders.
		await expect(page.locator(KT_CL_CALENDAR)).toBeVisible();
		await expect(page.locator(KT_CL_CALENDAR_ITEM)).toHaveCount(3);

		// Data table: 5 rows, filter, footer, and status chips.
		await expect(page.locator(KT_CL_DATA_TABLE)).toBeVisible();
		await expect(page.locator(KT_CL_TABLE_ROW)).toHaveCount(5);
		await expect(page.locator(KT_CL_TABLE_FILTER)).toBeVisible();
		await expect(page.locator(KT_CL_TABLE_FOOTER)).toContainText(/Showing 1-5 of 42 entries/i);
		await expect(page.locator(KT_CL_STATUS_CHIP)).toHaveCount(5);
		await expect(page.locator(`${KT_CL_STATUS_CHIP}[data-tone="approved"]`)).toHaveCount(2);
		await expect(page.locator(`${KT_CL_STATUS_CHIP}[data-tone="rejected"]`)).toHaveCount(1);
	});

	test("computed design tokens match the mock", async ({ page }) => {
		await gotoKtClShellPoc(page);

		// Sidebar width 256px (w-64).
		const sidebarWidth = await page.locator(KT_CL_SIDENAV).evaluate((el) => el.getBoundingClientRect().width);
		expect(Math.round(sidebarWidth)).toBe(256);

		// Toolbar height 48px (h-12).
		const toolbarHeight = await page.locator(KT_CL_TOOLBAR).evaluate((el) => el.getBoundingClientRect().height);
		expect(Math.round(toolbarHeight)).toBe(48);

		// Primary color #000b1d on the active nav link text.
		const color = await page
			.locator("a.border-r-4.border-primary")
			.first()
			.evaluate((el) => getComputedStyle(el).color);
		expect(color).toBe("rgb(0, 11, 29)");

		// Public Sans body font applied under the scoped shell.
		const fontFamily = await page
			.locator(KT_CL_TOOLBAR_TITLE)
			.evaluate((el) => getComputedStyle(el).fontFamily);
		expect(fontFamily.toLowerCase()).toContain("public sans");
	});

	test("toolbar stays visible with the custom sidenav mounted", async ({ page }) => {
		await gotoKtClShellPoc(page);
		await expect(page.locator(KT_CL_TOOLBAR)).toBeVisible();
		await expect(page.locator(KT_CL_SIDENAV)).toBeVisible();
	});
});
