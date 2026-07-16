import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const DASHBOARD_ROUTE = "/desk/it-tender-configuration-dashboard";
const OVERVIEW_ROUTE = "/desk/it-tender-configuration-overview";
const TDS_ROUTE = "/desk/it-tender-configuration-tds";
const REQUIREMENTS_ROUTE = "/desk/it-tender-configuration-it-requirements";
const SEED_CODE = "ITCFG-DASH-SEED-001";
const SEED_TITLE = "Data Center Hardware Refresh";

test.describe("IT Wizard IT Requirements Desk wiring", () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			localStorage.removeItem("_page:it-tender-configuration-it-requirements");
		});
	});

	test("overview IT_REQUIREMENTS card navigates to hydrated requirements screen", async ({ page }) => {
		await page.goto(`${OVERVIEW_ROUTE}?configuration_id=${SEED_CODE}`);
		const overviewIframe = page.frameLocator('[data-testid="it-wizard-overview-iframe"]');
		await expect(overviewIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const reqCard = overviewIframe.locator('[data-itw-step-card][data-itw-step-code="IT_REQUIREMENTS"]');
		await expect(reqCard).toBeVisible();
		await reqCard.getByRole("button").click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-it-requirements/, { timeout: 15_000 });

		const reqIframe = page.frameLocator('[data-testid="it-wizard-it-requirements-iframe"]');
		await expect(reqIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
	});

	test("TDS Continue to IT Requirements navigates with configuration_id", async ({ page }) => {
		await page.goto(`${TDS_ROUTE}?configuration_id=${SEED_CODE}`);
		const tdsIframe = page.frameLocator('[data-testid="it-wizard-tds-iframe"]');
		await expect(tdsIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await tdsIframe.locator("[data-itw-tds-actions]").getByRole("button", { name: /Continue to IT Requirements/i }).click();
		await expect(page).toHaveURL(
			new RegExp(`/desk/it-tender-configuration-it-requirements.*configuration_id=${SEED_CODE}`),
			{ timeout: 15_000 },
		);
	});

	test("direct requirements route without configuration_id redirects to dashboard", async ({ page }) => {
		await page.goto(REQUIREMENTS_ROUTE);
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-dashboard/, { timeout: 15_000 });
	});

	test("refresh preserves configuration_id and hydration", async ({ page }) => {
		await page.goto(`${REQUIREMENTS_ROUTE}?configuration_id=${SEED_CODE}`);
		const reqIframe = page.frameLocator('[data-testid="it-wizard-it-requirements-iframe"]');
		await expect(reqIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await page.reload();
		await expect(page).toHaveURL(new RegExp(`configuration_id=${SEED_CODE}`));
		await expect(page.getByText("Unable to load IT requirements.")).toHaveCount(0);
		await expect(reqIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
	});

	test("forbidden evaluation-form labels are not shown after hydration", async ({ page }) => {
		await page.goto(`${REQUIREMENTS_ROUTE}?configuration_id=${SEED_CODE}`);
		const reqIframe = page.frameLocator('[data-testid="it-wizard-it-requirements-iframe"]');
		await expect(reqIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(reqIframe.locator("body")).not.toContainText("Evidence Set");
		await expect(reqIframe.locator("body")).not.toContainText("Acceptance Set");
		await expect(reqIframe.locator("body")).not.toContainText("Scored (15%)");
		await expect(reqIframe.locator("body")).not.toContainText("Configuration Stats");
		await expect(reqIframe.locator("body")).not.toContainText(
			"technical specifications for bidder evaluation",
		);
	});

	test("seed positives appear in hydrated requirements context", async ({ page }) => {
		await page.goto(`${REQUIREMENTS_ROUTE}?configuration_id=${SEED_CODE}`);
		const reqIframe = page.frameLocator('[data-testid="it-wizard-it-requirements-iframe"]');
		await expect(reqIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(reqIframe.getByText(SEED_CODE)).toBeVisible();
		await expect(reqIframe.getByText(SEED_TITLE)).toBeVisible();
		await expect(reqIframe.locator('[data-itw-req-context]').getByText("National Treasury")).toBeVisible();
		await expect(reqIframe.locator('[data-itw-req-row][data-itw-req-code="3.1"]')).toBeVisible();
		await expect(reqIframe.locator("[data-itw-req-guidance]")).toBeVisible();
		await expect(reqIframe.locator("[data-itw-req-guidance]")).toContainText("Requirements Guidance");
	});

	test("drawer is hidden by default and opens on Edit", async ({ page }) => {
		await page.goto(`${REQUIREMENTS_ROUTE}?configuration_id=${SEED_CODE}`);
		const reqIframe = page.frameLocator('[data-testid="it-wizard-it-requirements-iframe"]');
		await expect(reqIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const drawer = reqIframe.locator("[data-itw-req-drawer]");
		await expect(drawer).toHaveAttribute("data-itw-req-drawer-hidden", "1");
		await reqIframe.locator('[data-itw-req-row][data-itw-req-code="3.1"] [data-itw-req-action="edit"]').click();
		await expect(drawer).toHaveAttribute("data-itw-req-drawer-open", "1", { timeout: 15_000 });
		await expect(reqIframe.locator('[data-itw-field="requirement_code"]')).toContainText("3.1");
	});

	test("save requirements persists drawer description after reload", async ({ page }) => {
		await page.goto(`${REQUIREMENTS_ROUTE}?configuration_id=${SEED_CODE}`);
		const reqIframe = page.frameLocator('[data-testid="it-wizard-it-requirements-iframe"]');
		await expect(reqIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await reqIframe.locator('[data-itw-req-row][data-itw-req-code="3.1"] [data-itw-req-action="edit"]').click();
		const description = reqIframe.locator('[data-itw-field="description"]');
		await expect(description).toBeVisible({ timeout: 15_000 });
		const savedText = "Playwright saved IT requirement description for 3.1.";
		await description.fill(savedText);
		await reqIframe.locator("[data-itw-req-drawer]").getByRole("button", { name: /Update Requirement/i }).click();
		await expect(description).toHaveValue(savedText, { timeout: 15_000 });

		await page.reload();
		const reloadedIframe = page.frameLocator('[data-testid="it-wizard-it-requirements-iframe"]');
		await expect(reloadedIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await reloadedIframe.locator('[data-itw-req-row][data-itw-req-code="3.1"] [data-itw-req-action="edit"]').click();
		await expect(reloadedIframe.locator('[data-itw-field="description"]')).toHaveValue(savedText, {
			timeout: 15_000,
		});
	});

	test("table row Review opens drawer with evaluation linkage summary", async ({ page }) => {
		await page.goto(`${REQUIREMENTS_ROUTE}?configuration_id=${SEED_CODE}`);
		const reqIframe = page.frameLocator('[data-testid="it-wizard-it-requirements-iframe"]');
		await expect(reqIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await reqIframe.locator('[data-itw-req-row][data-itw-req-code="3.2"] [data-itw-req-action="review"]').click();
		await expect(reqIframe.locator('[data-itw-field="evaluation_linked"]')).toContainText("Linked to Evaluation");
		await expect(reqIframe.getByText("Source: Evaluation Setup")).toBeVisible();
	});

	test("continue to implementation schedule is enabled when no blockers", async ({ page }) => {
		await page.goto(`${REQUIREMENTS_ROUTE}?configuration_id=${SEED_CODE}`);
		const reqIframe = page.frameLocator('[data-testid="it-wizard-it-requirements-iframe"]');
		await expect(reqIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const continueBtn = reqIframe.getByRole("button", { name: /Continue to Implementation Schedule/i });
		await expect(continueBtn).toBeEnabled();
	});

	test("requirements table scrolls when content exceeds viewport", async ({ page }) => {
		await page.goto(`${REQUIREMENTS_ROUTE}?configuration_id=${SEED_CODE}`);
		const reqIframe = page.frameLocator('[data-testid="it-wizard-it-requirements-iframe"]');
		await expect(reqIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const tableHost = reqIframe.locator("[data-itw-req-table-host]");
		const scrollMetrics = await tableHost.evaluate((node) => ({
			scrollHeight: node.scrollHeight,
			clientHeight: node.clientHeight,
		}));
		expect(scrollMetrics.scrollHeight).toBeGreaterThan(scrollMetrics.clientHeight);
		await tableHost.evaluate((node) => {
			node.scrollTop = node.scrollHeight;
		});
		await expect(reqIframe.locator('[data-itw-req-row][data-itw-req-code="4.1"]')).toBeVisible();
	});

	test("action footer is pinned at viewport bottom without overlaying table", async ({ page }) => {
		await page.goto(`${REQUIREMENTS_ROUTE}?configuration_id=${SEED_CODE}`);
		const reqIframe = page.frameLocator('[data-testid="it-wizard-it-requirements-iframe"]');
		await expect(reqIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const actions = reqIframe.locator("[data-itw-req-actions]");
		const tableHost = reqIframe.locator("[data-itw-req-table-host]");
		const body = reqIframe.locator("body");
		await expect(actions).toBeVisible();
		await expect(tableHost).toBeVisible();
		const layout = await reqIframe.locator("body").evaluate(() => {
			const actionsEl = document.querySelector("[data-itw-req-actions]");
			const tableEl = document.querySelector("[data-itw-req-table-host]");
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
		expect(layout!.actionsBottom).toBeCloseTo(layout!.bodyBottom, 0);
		expect(layout!.actionsTop).toBeGreaterThanOrEqual(layout!.tableBottom - 2);
		expect(layout!.tableScrollHeight).toBeGreaterThan(layout!.tableClientHeight);
	});
});
