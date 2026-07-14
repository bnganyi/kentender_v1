import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const DASHBOARD_ROUTE = "/desk/it-tender-configuration-dashboard";
const OVERVIEW_ROUTE = "/desk/it-tender-configuration-overview";
const PROFILE_ROUTE = "/desk/it-tender-configuration-tender-profile";
const TDS_ROUTE = "/desk/it-tender-configuration-tds";
const SEED_CODE = "ITCFG-DASH-SEED-001";
const SEED_TITLE = "Data Center Hardware Refresh";
const SEED_TENDER_NAME = "Supply and Commissioning of Data Center Hardware Refresh 2024";

test.describe("IT Wizard Tender Data Sheet Desk wiring", () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			localStorage.removeItem("_page:it-tender-configuration-tds");
		});
	});

	test("overview TDS card navigates to hydrated TDS screen", async ({ page }) => {
		await page.goto(`${OVERVIEW_ROUTE}?configuration_id=${SEED_CODE}`);
		const overviewIframe = page.frameLocator('[data-testid="it-wizard-overview-iframe"]');
		await expect(overviewIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const tdsCard = overviewIframe.locator('[data-itw-step-card][data-itw-step-code="TDS"]');
		await expect(tdsCard).toBeVisible();
		await tdsCard.getByRole("button").click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-tds/, { timeout: 15_000 });

		const tdsIframe = page.frameLocator('[data-testid="it-wizard-tds-iframe"]');
		await expect(tdsIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
	});

	test("profile Continue to Tender Data Sheet navigates with configuration_id", async ({ page }) => {
		await page.goto(`${PROFILE_ROUTE}?configuration_id=${SEED_CODE}`);
		const profileIframe = page.frameLocator('[data-testid="it-wizard-tender-profile-iframe"]');
		await expect(profileIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await profileIframe.getByRole("button", { name: /Continue to Tender Data Sheet/i }).click();
		await expect(page).toHaveURL(
			new RegExp(`/desk/it-tender-configuration-tds.*configuration_id=${SEED_CODE}`),
			{ timeout: 15_000 },
		);
	});

	test("direct TDS route without configuration_id redirects to dashboard", async ({ page }) => {
		await page.goto(TDS_ROUTE);
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-dashboard/, { timeout: 15_000 });
	});

	test("refresh preserves configuration_id and hydration", async ({ page }) => {
		await page.goto(`${TDS_ROUTE}?configuration_id=${SEED_CODE}`);
		const tdsIframe = page.frameLocator('[data-testid="it-wizard-tds-iframe"]');
		await expect(tdsIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await page.reload();
		await expect(page).toHaveURL(new RegExp(`configuration_id=${SEED_CODE}`));
		await expect(page.getByText("Unable to load tender data sheet.")).toHaveCount(0);
		await expect(page.getByText("Tender STD Instance must be unique")).toHaveCount(0);
		await expect(tdsIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
	});

	test("mock residue negatives are not shown after hydration", async ({ page }) => {
		await page.goto(`${TDS_ROUTE}?configuration_id=${SEED_CODE}`);
		const tdsIframe = page.frameLocator('[data-testid="it-wizard-tds-iframe"]');
		await expect(tdsIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(tdsIframe.locator("body")).not.toContainText("KNICTA/T/04/2023-2024");
		await expect(tdsIframe.locator("body")).not.toContainText("Ministry of Finance");
	});

	test("seed positives appear in hydrated TDS context", async ({ page }) => {
		await page.goto(`${TDS_ROUTE}?configuration_id=${SEED_CODE}`);
		const tdsIframe = page.frameLocator('[data-testid="it-wizard-tds-iframe"]');
		await expect(tdsIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(tdsIframe.locator('[data-itw-field="tender_number"]')).toHaveValue("NT/T/ICT/2024-009");
		await expect(tdsIframe.locator('[data-itw-field="tender_name"]')).toHaveValue(SEED_TENDER_NAME);
		await expect(tdsIframe.getByText(SEED_TITLE)).toBeVisible();
		await expect(tdsIframe.getByText("PP-ICT-2024-009")).toBeVisible();
		await expect(tdsIframe.getByText("National Treasury")).toBeVisible();
	});

	test("save TDS persists tender security amount after reload", async ({ page }) => {
		await page.goto(`${TDS_ROUTE}?configuration_id=${SEED_CODE}`);
		const tdsIframe = page.frameLocator('[data-testid="it-wizard-tds-iframe"]');
		await expect(tdsIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const securityInput = tdsIframe.locator('[data-itw-field="tender_security_amount"]');
		await expect(securityInput).toBeVisible();
		const savedAmount = "750000";
		await securityInput.fill(savedAmount);
		const deadlineInput = tdsIframe.locator('[data-itw-field="submission_deadline_at"]');
		await deadlineInput.fill("2026-08-20T17:00");
		const openingInput = tdsIframe.locator('[data-itw-field="opening_at"]');
		await openingInput.fill("2026-08-21T10:00");
		const validityInput = tdsIframe.locator('[data-itw-field="tender_validity_days"]');
		await validityInput.fill("120");
		const issuerSelect = tdsIframe.locator('[data-itw-field="security_issuer_type"]');
		await issuerSelect.selectOption({ label: "Commercial Bank" });
		await tdsIframe.getByRole("button", { name: /Save TDS/i }).click();
		await expect(securityInput).toHaveValue(savedAmount, { timeout: 15_000 });

		await page.reload();
		const reloadedIframe = page.frameLocator('[data-testid="it-wizard-tds-iframe"]');
		await expect(reloadedIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(reloadedIframe.locator('[data-itw-field="tender_security_amount"]')).toHaveValue(savedAmount);
	});

	test("alternative tenders select changes on single interaction", async ({ page }) => {
		await page.goto(`${TDS_ROUTE}?configuration_id=${SEED_CODE}`);
		const tdsIframe = page.frameLocator('[data-testid="it-wizard-tds-iframe"]');
		await expect(tdsIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const altSelect = tdsIframe.locator('[data-itw-field="alternative_tenders_allowed"]');
		await expect(altSelect).toHaveValue("No");
		await altSelect.selectOption("Yes");
		await expect(altSelect).toHaveValue("Yes");
	});

	test("readonly envelope marking stays non-editable", async ({ page }) => {
		await page.goto(`${TDS_ROUTE}?configuration_id=${SEED_CODE}`);
		const tdsIframe = page.frameLocator('[data-testid="it-wizard-tds-iframe"]');
		await expect(tdsIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const envelopeInput = tdsIframe.locator('[data-itw-field="envelope_marking"]');
		await expect(envelopeInput).toHaveAttribute("readonly", "");
		await expect(envelopeInput).toHaveValue("ELECTRONIC_ONLY");
	});

	test("submission deadline loses mock error highlight after hydration", async ({ page }) => {
		await page.goto(`${TDS_ROUTE}?configuration_id=${SEED_CODE}`);
		const tdsIframe = page.frameLocator('[data-testid="it-wizard-tds-iframe"]');
		await expect(tdsIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const deadlineInput = tdsIframe.locator('[data-itw-field="submission_deadline_at"]');
		await expect(deadlineInput).not.toHaveClass(/border-error/);
		await expect(deadlineInput).toHaveClass(/border-outline-variant/);
	});
});
