import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const DASHBOARD_ROUTE = "/desk/it-tender-configuration-dashboard";
const OVERVIEW_ROUTE = "/desk/it-tender-configuration-overview";
const REQUIREMENTS_ROUTE = "/desk/it-tender-configuration-it-requirements";
const SCHEDULE_ROUTE = "/desk/it-tender-configuration-implementation-schedule";
const SEED_CODE = "ITCFG-DASH-SEED-001";
const SEED_TITLE = "Data Center Hardware Refresh";
const SEED_TENDER_REF = "NT/T/ICT/2024-009";

test.describe("IT Wizard Implementation Schedule Desk wiring", () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			localStorage.removeItem("_page:it-tender-configuration-implementation-schedule");
		});
	});

	test("overview IMPLEMENTATION_SCHEDULE card navigates to hydrated schedule screen", async ({ page }) => {
		await page.goto(`${OVERVIEW_ROUTE}?configuration_id=${SEED_CODE}`);
		const overviewIframe = page.frameLocator('[data-testid="it-wizard-overview-iframe"]');
		await expect(overviewIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const schedCard = overviewIframe.locator(
			'[data-itw-step-card][data-itw-step-code="IMPLEMENTATION_SCHEDULE"]',
		);
		await expect(schedCard).toBeVisible();
		await schedCard.getByRole("button").click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-implementation-schedule/, { timeout: 15_000 });

		const schedIframe = page.frameLocator('[data-testid="it-wizard-implementation-schedule-iframe"]');
		await expect(schedIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
	});

	test("IT Requirements Continue to Implementation Schedule navigates with configuration_id", async ({
		page,
	}) => {
		await page.goto(`${REQUIREMENTS_ROUTE}?configuration_id=${SEED_CODE}`);
		const reqIframe = page.frameLocator('[data-testid="it-wizard-it-requirements-iframe"]');
		await expect(reqIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await reqIframe
			.locator("[data-itw-req-actions]")
			.getByRole("button", { name: /Continue to Implementation Schedule/i })
			.click();
		await expect(page).toHaveURL(
			new RegExp(`/desk/it-tender-configuration-implementation-schedule.*configuration_id=${SEED_CODE}`),
			{ timeout: 15_000 },
		);
	});

	test("direct schedule route without configuration_id redirects to dashboard", async ({ page }) => {
		await page.goto(SCHEDULE_ROUTE);
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-dashboard/, { timeout: 15_000 });
	});

	test("refresh preserves configuration_id and hydration", async ({ page }) => {
		await page.goto(`${SCHEDULE_ROUTE}?configuration_id=${SEED_CODE}`);
		const schedIframe = page.frameLocator('[data-testid="it-wizard-implementation-schedule-iframe"]');
		await expect(schedIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await page.reload();
		await expect(page).toHaveURL(new RegExp(`configuration_id=${SEED_CODE}`));
		await expect(page.getByText("Unable to load implementation schedule.")).toHaveCount(0);
		await expect(schedIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
	});

	test("seed positives appear in hydrated schedule context and phase table", async ({ page }) => {
		await page.goto(`${SCHEDULE_ROUTE}?configuration_id=${SEED_CODE}`);
		const schedIframe = page.frameLocator('[data-testid="it-wizard-implementation-schedule-iframe"]');
		await expect(schedIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		// Context strip "Tender Ref" shows the tender number, not the internal configuration id.
		const context = schedIframe.locator("[data-itw-sched-context]");
		await expect(context.getByText(SEED_TENDER_REF)).toBeVisible();
		await expect(context.getByText("Tender Ref")).toBeVisible();
		await expect(schedIframe.getByText(SEED_TITLE)).toBeVisible();
		await expect(context.getByText("National Treasury")).toBeVisible();
		await expect(
			schedIframe.locator('[data-itw-sched-row][data-itw-sched-code="PHASE_1"]'),
		).toBeVisible();
		await expect(schedIframe.locator("[data-itw-sched-guidance]")).toBeVisible();
		await expect(schedIframe.locator("[data-itw-sched-guidance]")).toContainText("Schedule Guidance");
	});

	test("drawer is hidden by default and opens on Edit", async ({ page }) => {
		await page.goto(`${SCHEDULE_ROUTE}?configuration_id=${SEED_CODE}`);
		const schedIframe = page.frameLocator('[data-testid="it-wizard-implementation-schedule-iframe"]');
		await expect(schedIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const drawer = schedIframe.locator("[data-itw-sched-drawer]");
		await expect(drawer).toHaveAttribute("data-itw-sched-drawer-hidden", "1");
		await schedIframe
			.locator('[data-itw-sched-row][data-itw-sched-code="PHASE_2"] [data-itw-sched-action="edit"]')
			.click();
		await expect(drawer).toHaveAttribute("data-itw-sched-drawer-open", "1", { timeout: 15_000 });
		await expect(schedIframe.locator('[data-itw-field="phase_code"]')).toContainText("PHASE_2");
	});

	test("save drawer deliverables persists after reload", async ({ page }) => {
		await page.goto(`${SCHEDULE_ROUTE}?configuration_id=${SEED_CODE}`);
		const schedIframe = page.frameLocator('[data-testid="it-wizard-implementation-schedule-iframe"]');
		await expect(schedIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await schedIframe
			.locator('[data-itw-sched-row][data-itw-sched-code="PHASE_2"] [data-itw-sched-action="edit"]')
			.click();
		const deliverables = schedIframe.locator('[data-itw-field="deliverables"]');
		await expect(deliverables).toBeVisible({ timeout: 15_000 });
		const savedText = "Playwright saved deliverables summary for PHASE_2.";
		await deliverables.fill(savedText);
		await schedIframe.locator("[data-itw-sched-drawer]").getByRole("button", { name: /Save Changes/i }).click();
		await expect(deliverables).toHaveValue(savedText, { timeout: 15_000 });

		await page.reload();
		const reloadedIframe = page.frameLocator('[data-testid="it-wizard-implementation-schedule-iframe"]');
		await expect(reloadedIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await reloadedIframe
			.locator('[data-itw-sched-row][data-itw-sched-code="PHASE_2"] [data-itw-sched-action="edit"]')
			.click();
		await expect(reloadedIframe.locator('[data-itw-field="deliverables"]')).toHaveValue(savedText, {
			timeout: 15_000,
		});
	});

	test("drawer duration is editable and phase code stays read-only", async ({ page }) => {
		await page.goto(`${SCHEDULE_ROUTE}?configuration_id=${SEED_CODE}`);
		const schedIframe = page.frameLocator('[data-testid="it-wizard-implementation-schedule-iframe"]');
		await expect(schedIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await schedIframe
			.locator('[data-itw-sched-row][data-itw-sched-code="PHASE_1"] [data-itw-sched-action="edit"]')
			.click();
		const duration = schedIframe.locator('[data-itw-field="duration_label"]');
		await expect(duration).toBeVisible({ timeout: 15_000 });
		await expect(duration).toBeEditable();
		await expect(schedIframe.locator('[data-itw-sched-source="duration_label"]')).toContainText(
			"Standard IT Schedule Template",
		);
		const drawer = schedIframe.locator("[data-itw-sched-drawer]");
		await expect(drawer.getByRole("button", { name: "Edit" })).toBeVisible();
		await expect(drawer.getByRole("button", { name: "Reset to Template" })).toBeVisible();
		await expect(drawer.getByRole("button", { name: "Override" })).toBeVisible();
		await expect(schedIframe.locator('[data-itw-field="phase_code"]')).toHaveText("PHASE_1");
		await expect(schedIframe.locator('[data-itw-sched-source="phase_code"]')).toContainText(
			"System-generated phase identifier",
		);
	});

	test("reset to template restores expected duration", async ({ page }) => {
		await page.goto(`${SCHEDULE_ROUTE}?configuration_id=${SEED_CODE}`);
		const schedIframe = page.frameLocator('[data-testid="it-wizard-implementation-schedule-iframe"]');
		await expect(schedIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await schedIframe
			.locator('[data-itw-sched-row][data-itw-sched-code="PHASE_1"] [data-itw-sched-action="edit"]')
			.click();
		const drawer = schedIframe.locator("[data-itw-sched-drawer]");
		const duration = drawer.locator('[data-itw-field="duration_label"]');
		await expect(duration).toBeVisible({ timeout: 15_000 });
		const original = await duration.inputValue();
		await duration.fill("12 Months");
		const resetBtn = drawer.locator(
			'[data-itw-sched-field-action="reset"][data-itw-sched-field-key="duration_label"]',
		);
		await expect(resetBtn).toBeVisible();
		await resetBtn.click();
		await expect(duration).toHaveValue(original, { timeout: 15_000 });
	});

	test("single turnkey replaces phases, persists fields, and switching back restores phases", async ({ page }) => {
		await page.goto(`${SCHEDULE_ROUTE}?configuration_id=${SEED_CODE}`);
		const schedIframe = page.frameLocator('[data-testid="it-wizard-implementation-schedule-iframe"]');
		await expect(schedIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});

		await schedIframe.locator('[data-itw-field="implementation_model"][value="SINGLE_TURNKEY"]').check();
		await expect(page.getByRole("dialog")).toContainText("Switch to Single Turnkey Delivery");
		await page.getByRole("button", { name: "Switch to Single Delivery" }).click();

		await expect(schedIframe.locator('[data-itw-sched-mode-host="single-turnkey"]')).toBeVisible();
		await expect(schedIframe.locator('[data-itw-sched-mode-host="phased"]')).toBeHidden();
		await expect(schedIframe.locator("[data-itw-sched-add-phase]")).toBeHidden();

		const deliverables = schedIframe.locator('[data-itw-turnkey-field="key_deliverables"]');
		const savedText = "Playwright unified turnkey delivery package.";
		await deliverables.fill(savedText);
		await schedIframe.locator("[data-itw-sched-actions]").getByRole("button", { name: /Save Schedule/i }).click();
		await page.reload();
		const reloaded = page.frameLocator('[data-testid="it-wizard-implementation-schedule-iframe"]');
		await expect(reloaded.locator('[data-itw-sched-mode-host="single-turnkey"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(reloaded.locator('[data-itw-turnkey-field="key_deliverables"]')).toHaveValue(savedText);

		await reloaded.locator('[data-itw-field="implementation_model"][value="PHASED"]').check();
		await expect(reloaded.locator('[data-itw-sched-mode-host="phased"]')).toBeVisible();
		await expect(reloaded.locator('[data-itw-sched-row][data-itw-sched-code="PHASE_1"]')).toBeVisible();
	});

	test("phase table scrolls when content exceeds viewport", async ({ page }) => {
		await page.setViewportSize({ width: 1280, height: 560 });
		await page.goto(`${SCHEDULE_ROUTE}?configuration_id=${SEED_CODE}`);
		const schedIframe = page.frameLocator('[data-testid="it-wizard-implementation-schedule-iframe"]');
		await expect(schedIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const tableHost = schedIframe.locator("[data-itw-sched-table-host]");
		const scrollMetrics = await tableHost.evaluate((node) => ({
			scrollHeight: node.scrollHeight,
			clientHeight: node.clientHeight,
		}));
		expect(scrollMetrics.scrollHeight).toBeGreaterThan(scrollMetrics.clientHeight);
		await tableHost.evaluate((node) => {
			node.scrollTop = node.scrollHeight;
		});
		await expect(schedIframe.locator('[data-itw-sched-row][data-itw-sched-code="PHASE_3"]')).toBeVisible();
	});

	test("action footer is pinned at viewport bottom without overlaying table", async ({ page }) => {
		await page.goto(`${SCHEDULE_ROUTE}?configuration_id=${SEED_CODE}`);
		const schedIframe = page.frameLocator('[data-testid="it-wizard-implementation-schedule-iframe"]');
		await expect(schedIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const actions = schedIframe.locator("[data-itw-sched-actions]");
		const tableHost = schedIframe.locator("[data-itw-sched-table-host]");
		await expect(actions).toBeVisible();
		await expect(tableHost).toBeVisible();
		const layout = await schedIframe.locator("body").evaluate(() => {
			const actionsEl = document.querySelector("[data-itw-sched-actions]");
			const tableEl = document.querySelector("[data-itw-sched-table-host]");
			const bodyEl = document.body;
			if (!actionsEl || !tableEl || !bodyEl) {
				return null;
			}
			const actionsRect = actionsEl.getBoundingClientRect();
			const tableRect = tableEl.getBoundingClientRect();
			const bodyRect = bodyEl.getBoundingClientRect();
			return {
				actionsBottom: actionsRect.bottom,
				bodyBottom: bodyRect.bottom,
				tableBottom: tableRect.bottom,
				actionsTop: actionsRect.top,
				tableScrollHeight: tableEl.scrollHeight,
				tableClientHeight: tableEl.clientHeight,
			};
		});
		expect(layout).not.toBeNull();
		if (layout) {
			expect(layout.actionsBottom).toBeLessThanOrEqual(layout.bodyBottom + 2);
			expect(layout.tableBottom).toBeLessThanOrEqual(layout.actionsTop + 2);
			expect(layout.tableScrollHeight).toBeGreaterThan(layout.tableClientHeight);
		}
	});
});
