import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const DASHBOARD_ROUTE = "/desk/it-tender-configuration-dashboard";
const OVERVIEW_ROUTE = "/desk/it-tender-configuration-overview";
const PROFILE_ROUTE = "/desk/it-tender-configuration-tender-profile";
const SEED_CODE = "ITCFG-DASH-SEED-001";
const SEED_TITLE = "Data Center Hardware Refresh";

test.describe("IT Wizard Tender Profile Desk wiring", () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test("overview tender profile card navigates to hydrated profile screen", async ({ page }) => {
		await page.goto(`${OVERVIEW_ROUTE}?configuration_id=${SEED_CODE}`);
		const overviewIframe = page.frameLocator('[data-testid="it-wizard-overview-iframe"]');
		await expect(overviewIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const profileCard = overviewIframe.locator('[data-itw-step-card][data-itw-step-code="TENDER_PROFILE"]');
		await expect(profileCard).toBeVisible();
		await profileCard.getByRole("button").click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-tender-profile/, { timeout: 15_000 });

		const profileIframe = page.frameLocator('[data-testid="it-wizard-tender-profile-iframe"]');
		await expect(profileIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(profileIframe.getByText(SEED_CODE)).toBeVisible();
		await expect(profileIframe.getByText(SEED_TITLE)).toBeVisible();
		await expect(profileIframe.getByText("PP-ICT-2024-009")).toBeVisible();
		await expect(profileIframe.getByText("National Treasury")).toBeVisible();
		await expect(profileIframe.locator("body")).not.toContainText("TNT/024/2024");
		await expect(profileIframe.locator("body")).not.toContainText("procurement@finance.go.ke");
	});

	test("profile route without configuration_id redirects to dashboard", async ({ page }) => {
		await page.goto(PROFILE_ROUTE);
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-dashboard/, { timeout: 15_000 });
	});

	test("profile Continue to TDS preserves configuration_id in URL", async ({ page }) => {
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

	test("save profile persists tender display title", async ({ page }) => {
		await page.goto(`${PROFILE_ROUTE}?configuration_id=${SEED_CODE}`);
		const profileIframe = page.frameLocator('[data-testid="it-wizard-tender-profile-iframe"]');
		await expect(profileIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const titleInput = profileIframe.locator('[data-itw-field="tender_name"]');
		await expect(titleInput).toBeVisible();
		const updatedTitle = `Playwright Profile Title ${Date.now()}`;
		await titleInput.fill(updatedTitle);
		await profileIframe.getByRole("button", { name: /^Save Profile$/i }).click();
		await expect(titleInput).toHaveValue(updatedTitle, { timeout: 15_000 });

		await page.reload();
		const reloadedIframe = page.frameLocator('[data-testid="it-wizard-tender-profile-iframe"]');
		await expect(reloadedIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(page.getByText("Tender STD Instance must be unique")).toHaveCount(0);
		await expect(page.getByText("Unable to load tender profile.")).toHaveCount(0);
		await expect(reloadedIframe.locator('[data-itw-field="tender_name"]')).toHaveValue(updatedTitle);
	});

	test("profile toggles flip on a single click", async ({ page }) => {
		await page.goto(`${PROFILE_ROUTE}?configuration_id=${SEED_CODE}`);
		const profileIframe = page.frameLocator('[data-testid="it-wizard-tender-profile-iframe"]');
		await expect(profileIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});

		const altToggle = profileIframe.locator('[data-itw-field="alternative_tenders_allowed"]');
		await expect(altToggle).toHaveAttribute("aria-checked", "false");
		await altToggle.click();
		await expect(altToggle).toHaveAttribute("aria-checked", "true");

		const jvToggle = profileIframe.locator('[data-itw-field="jv_allowed"]');
		await expect(jvToggle).toHaveAttribute("aria-checked", "true");
		await jvToggle.click();
		await expect(jvToggle).toHaveAttribute("aria-checked", "false");

		const meetingToggle = profileIframe.locator('[data-itw-field="pre_tender_meeting_required"]');
		await expect(meetingToggle).toHaveAttribute("aria-checked", "true");
		await meetingToggle.click();
		await expect(meetingToggle).toHaveAttribute("aria-checked", "false");
	});
});
