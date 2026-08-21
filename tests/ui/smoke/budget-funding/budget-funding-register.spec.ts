import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

/**
 * Register approved budget (Prompt 2 / Pack Phase 2).
 * Domain: register_budget creates Draft; Overview remains stub until next screen.
 */

test.describe.configure({ mode: "serial" });

test.describe("Budget Funding register (Prompt 2)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("register form regions and Stitch chrome", async ({ page }) => {
		await page.goto("/desk/budget-register", { waitUntil: "domcontentloaded" });
		const root = page.locator('[data-testid="kt-bud-register"][data-kt-bud-live="1"]');
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(page.getByRole("heading", { name: "Register approved budget" })).toBeVisible();
		await expect(page.getByTestId("kt-bud-register-identity")).toBeVisible();
		await expect(page.getByTestId("kt-bud-register-approval")).toBeVisible();
		await expect(page.getByTestId("kt-bud-register-info-note")).toBeVisible();
		await expect(page.getByTestId("kt-bud-create-draft")).toBeVisible();
		await expect(page.getByTestId("kt-bud-register-cancel")).toBeVisible();
		await expect(page.locator('[data-kt-bud-field="generated_reference"]')).toHaveCount(0);
		await expect(page.getByText(/Controlled import/i)).toHaveCount(0);
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-bud-register",
			primaryCtaTestId: "kt-bud-create-draft",
			secondaryCtaTestId: "kt-bud-register-cancel",
			selectSelector: '[data-kt-bud-field="fiscal_period"]',
		});
	});

	test("validation surfaces when required fields missing", async ({ page }) => {
		await page.goto("/desk/budget-register", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-bud-register"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 45_000,
		});
		await page.locator('[data-kt-bud-field="title"]').fill("");
		await page.locator('[data-kt-bud-field="budget_owner"]').fill("");
		await page.locator('[data-kt-bud-field="authoritative_reference"]').fill("");
		await page.locator('[data-kt-bud-field="external_approved_total"]').fill("");
		await page.getByTestId("kt-bud-create-draft").click();
		await expect(page.locator('[data-kt-bud-error="title"]')).toBeVisible({ timeout: 15_000 });
		// Evidence is optional — must not block Draft create.
		await expect(page.locator('[data-kt-bud-error="approval_evidence"]')).toBeHidden();
		await expect(page).toHaveURL(/\/desk\/budget-register/);
	});

	test("Cancel returns to portfolio", async ({ page }) => {
		await page.goto("/desk/budget-register", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-bud-register"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 45_000,
		});
		await page.getByTestId("kt-bud-register-cancel").click();
		await page.waitForURL(/\/desk\/budget-funding/, { timeout: 20_000 });
		await expect(page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
	});

	test("form layout is stacked (not collapsed) and round-trip keeps chrome", async ({ page }) => {
		await page.goto("/desk/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 45_000,
		});
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-bud-portfolio",
			primaryCtaTestId: "kt-bud-register-budget",
			secondaryCtaTestId: "kt-bud-open-performance",
			selectSelector: '[data-kt-bud-filter="status"]',
		});

		await page.getByTestId("kt-bud-register-budget").click();
		await page.waitForURL(/\/desk\/budget-register/, { timeout: 20_000 });
		const reg = page.locator('[data-testid="kt-bud-register"][data-kt-bud-live="1"]');
		await expect(reg).toBeVisible({ timeout: 45_000 });

		const geometry = await page.evaluate(() => {
			const identity = document.querySelector(
				'[data-testid="kt-bud-register-identity"]',
			) as HTMLElement | null;
			const approval = document.querySelector(
				'[data-testid="kt-bud-register-approval"]',
			) as HTMLElement | null;
			const note = document.querySelector(
				'[data-testid="kt-bud-register-info-note"]',
			) as HTMLElement | null;
			const form = document.querySelector(
				'[data-testid="kt-bud-register-form"]',
			) as HTMLElement | null;
			const pe = document.querySelector(
				'[data-kt-bud-field="procuring_entity_label"]',
			) as HTMLElement | null;
			const h2 = identity?.querySelector("h2") as HTMLElement | null;
			const idBox = identity?.getBoundingClientRect();
			const apBox = approval?.getBoundingClientRect();
			const noteBox = note?.getBoundingClientRect();
			const formBox = form?.getBoundingClientRect();
			const peBox = pe?.getBoundingClientRect();
			const h2Box = h2?.getBoundingClientRect();
			const noteCs = note ? getComputedStyle(note) : null;
			return {
				identityHeight: idBox?.height || 0,
				approvalTop: apBox?.top || 0,
				identityBottom: idBox?.bottom || 0,
				noteWidth: noteBox?.width || 0,
				formWidth: formBox?.width || 0,
				noteDisplay: noteCs?.display || "",
				noteFlexDir: noteCs?.flexDirection || "",
				h2Bottom: h2Box?.bottom || 0,
				peTop: peBox?.top || 0,
			};
		});

		// Sections stack vertically with real height (collapsed = ~0–40px chaos).
		expect(geometry.identityHeight).toBeGreaterThan(120);
		expect(geometry.approvalTop).toBeGreaterThan(geometry.identityBottom - 8);
		// Info note is a full-width callout under the form, not a thin right strip.
		expect(geometry.noteDisplay).toBe("flex");
		expect(geometry.noteFlexDir).toBe("row");
		expect(geometry.noteWidth).toBeGreaterThan(geometry.formWidth * 0.7);
		// Section title sits above the first field (not overlapping).
		expect(geometry.peTop).toBeGreaterThan(geometry.h2Bottom - 2);

		await assertStitchDeskChrome(page, {
			rootTestId: "kt-bud-register",
			primaryCtaTestId: "kt-bud-create-draft",
			secondaryCtaTestId: "kt-bud-register-cancel",
			selectSelector: '[data-kt-bud-field="fiscal_period"]',
		});

		await page.getByTestId("kt-bud-register-cancel").click();
		await page.waitForURL(/\/desk\/budget-funding/, { timeout: 20_000 });
		await expect(page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		// cl_shell_router must keep body.kt-cl-shell (otherwise Stitch CTA pins miss).
		await expect
			.poll(async () => page.evaluate(() => document.body.classList.contains("kt-cl-shell")))
			.toBe(true);
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-bud-portfolio",
			primaryCtaTestId: "kt-bud-register-budget",
			secondaryCtaTestId: "kt-bud-open-performance",
			selectSelector: '[data-kt-bud-filter="status"]',
		});

		// Second visit must not remount into a broken layout.
		await page.getByTestId("kt-bud-register-budget").click();
		await page.waitForURL(/\/desk\/budget-register/, { timeout: 20_000 });
		await expect(page.locator('[data-testid="kt-bud-register"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 45_000,
		});
		const again = await page.evaluate(() => {
			const identity = document.querySelector(
				'[data-testid="kt-bud-register-identity"]',
			) as HTMLElement | null;
			return identity?.getBoundingClientRect().height || 0;
		});
		expect(again).toBeGreaterThan(120);
	});

	test("create draft routes to overview stub with budget code", async ({ page }) => {
		await page.goto("/desk/budget-register", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-bud-register"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 45_000,
		});

		// Cancel any leftover Draft for this smoke period so re-runs stay idempotent.
		await page.evaluate(async () => {
			const period = "2039/40";
			await frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Budget",
					filters: { fiscal_period: period, status: ["in", ["Draft", "Submitted", "Returned", "Active"]] },
					fields: ["name"],
					limit_page_length: 20,
				},
			}).then(async (r) => {
				const rows = (r && r.message) || [];
				for (const row of rows) {
					await frappe.call({
						method: "frappe.client.delete",
						args: { doctype: "Budget", name: row.name },
					});
				}
			});
		});

		await page.locator('[data-kt-bud-field="fiscal_period"]').selectOption("2039/40");
		await page
			.locator('[data-kt-bud-field="title"]')
			.fill("Playwright Register Budget FY 2039/40");
		await page.locator('[data-kt-bud-field="budget_owner"]').fill("Director, Finance and Accounts");
		await page
			.locator('[data-kt-bud-field="authoritative_reference"]')
			.fill(`MOH-FIN-BUD-PW-${Date.now()}`);
		await page.locator('[data-kt-bud-field="approval_date"]').fill("2039-06-15");
		await page.locator('[data-kt-bud-field="external_approved_total"]').fill("125000000");
		await page.locator('[data-kt-bud-field="external_approved_total"]').blur();
		// No approval evidence — optional for Draft registration.

		await page.getByTestId("kt-bud-create-draft").click();
		await page.waitForURL(/\/desk\/budget-overview\/[A-Z0-9]+-BUD-\d{4}/, { timeout: 45_000 });
		await expect(page.getByTestId("kt-bud-stub")).toBeVisible({ timeout: 20_000 });
	});
});
