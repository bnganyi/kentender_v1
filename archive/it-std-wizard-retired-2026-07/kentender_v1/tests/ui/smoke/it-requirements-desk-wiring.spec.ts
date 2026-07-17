import { test, expect, type Page } from "@playwright/test";

import { loginAsAdministrator } from "../../helpers/auth";
import {
	ITW_OVERVIEW_ROUTE,
	openNativeItRequirements,
	openNativeOverview,
} from "../../helpers/itWizardDesk";

const REQUIREMENTS_ROUTE = "/desk/it-tender-configuration-it-requirements";
const SEED_CODE = "ITCFG-DASH-SEED-001";
const SEED_TITLE = "Data Center Hardware Refresh";

test.describe.serial("IT Wizard IT Requirements Desk wiring", () => {
	let page: Page;

	test.beforeAll(async ({ browser }) => {
		page = await browser.newPage();
		await loginAsAdministrator(page);
	});

	test.afterAll(async () => {
		await page.close();
	});

	test("overview IT_REQUIREMENTS step navigates to native requirements screen", async () => {
		await openNativeOverview(page, SEED_CODE);
		const reqCard = page.locator('[data-itw-step-card][data-itw-step-code="IT_REQUIREMENTS"]');
		await expect(reqCard).toBeVisible();
		await reqCard.getByRole("button").click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-it-requirements/, { timeout: 15_000 });
		await expect(page.locator('[data-testid="it-wizard-it-requirements"]')).toHaveAttribute(
			"data-itw-native-loaded",
			"1",
			{ timeout: 30_000 },
		);
	});

	test("direct requirements route without configuration_id redirects to dashboard", async () => {
		await page.goto(REQUIREMENTS_ROUTE);
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-dashboard/, { timeout: 15_000 });
	});

	test("forbidden evaluation-form labels are not shown on native screen", async () => {
		await openNativeItRequirements(page, SEED_CODE);
		const root = page.locator('[data-testid="it-wizard-it-requirements"]');
		await expect(root).not.toContainText("Evidence Set");
		await expect(root).not.toContainText("Acceptance Set");
		await expect(root).not.toContainText("Scored (15%)");
		await expect(root).not.toContainText("Edit in Evaluation Setup");
	});

	test("seed configuration context and requirement row appear", async () => {
		await openNativeItRequirements(page, SEED_CODE);
		const root = page.locator('[data-testid="it-wizard-it-requirements"]');
		await expect(root.getByText(SEED_CODE)).toBeVisible();
		await expect(root.getByText(SEED_TITLE)).toBeVisible();
		await expect(root.locator('[data-itw-req-context]').getByText("National Treasury")).toBeVisible();
		await expect(root.locator('[data-itw-req-row][data-itw-req-code="3.1"]')).toBeVisible();
		await expect(root.locator("[data-itw-req-guidance]")).toContainText("Requirements Guidance");
		await expect(root.getByText("Define what bidders must supply, deliver, integrate, support, or prove.")).toBeVisible();
	});

	test("drawer edit and save persists description after reload", async () => {
		await openNativeItRequirements(page, SEED_CODE);
		const root = page.locator('[data-testid="it-wizard-it-requirements"]');
		await root.locator('[data-itw-req-row][data-itw-req-code="3.1"] [data-itw-req-action="edit"]').click();
		const drawer = root.locator("[data-itw-req-drawer]");
		await expect(drawer).toHaveAttribute("data-itw-req-drawer-open", "1", { timeout: 15_000 });
		const description = drawer.locator('[data-itw-field="description"]');
		const savedText = "Playwright saved IT requirement description for 3.1.";
		await description.fill(savedText);
		await drawer.locator("[data-itw-req-drawer-save]").click();
		await expect(page.getByText("Requirements saved")).toBeVisible({ timeout: 15_000 });

		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page).toHaveURL(new RegExp(`configuration_id=${SEED_CODE}`));
		await expect(page.locator('[data-testid="it-wizard-it-requirements"]')).toHaveAttribute(
			"data-itw-native-loaded",
			"1",
			{ timeout: 30_000 },
		);
		await page.locator('[data-itw-req-row][data-itw-req-code="3.1"] [data-itw-req-action="edit"]').click();
		await expect(page.locator('[data-itw-field="description"]')).toHaveValue(savedText, { timeout: 15_000 });
	});

	test("continue to implementation schedule is enabled for seed configuration", async () => {
		await openNativeItRequirements(page, SEED_CODE);
		const continueBtn = page.locator("[data-itw-req-continue]");
		await expect(continueBtn).toBeEnabled();
	});
});
