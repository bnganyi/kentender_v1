import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

/**
 * BUD-UI-08 Budget Revisions — list tab + dedicated create page (Apply deferred to BUD-UI-09).
 */

test.describe.configure({ mode: "serial" });

test.describe("Budget Funding revisions (BUD-UI-08)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("live list shows seeded draft without in-tab create form", async ({ page }) => {
		await page.goto("/desk/budget-revisions/MOH-BUD-2027-2028", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-revisions"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-workspace-chrome")).toBeVisible();
		await expect(root.getByTestId("kt-bud-revisions-list")).toBeVisible();
		await expect(root.getByTestId("kt-bud-revisions-table")).toBeVisible();
		await expect(root.getByTestId("kt-bud-revisions-table-footer")).toContainText(/Showing/i);

		// No redundant section title or in-tab create entry.
		await expect(page.getByRole("heading", { name: /^Budget revisions$/i })).toHaveCount(0);
		await expect(root.getByTestId("kt-bud-rev-create")).toHaveCount(0);
		await expect(root.getByTestId("kt-bud-rev-create-form")).toHaveCount(0);

		const seed = root.locator('tr[data-revision-code="BR-MOH-0001"]');
		await expect(seed).toBeVisible({ timeout: 20_000 });
		await expect(seed).toContainText("Draft");
		await expect(seed).toContainText("+ KES 25,000,000");
		await expect(seed).toContainText("MOF/2027/REV-MOH-01");

		await expect(page.getByText(/next in the Budget MVP-1 build sequence/i)).toHaveCount(0);

		await assertStitchDeskChrome(page, {
			rootTestId: "kt-bud-revisions",
			primaryCtaTestId: "kt-bud-overview-primary",
			secondaryCtaTestId: "kt-bud-view-performance",
			headlineSelector: "[data-kt-bud-budget-title]",
		});
		await expect(root.getByTestId("kt-bud-overview-primary")).toContainText(/Request revision/i);
	});

	test("Request revision opens dedicated create page with Stitch form", async ({ page }) => {
		await page.goto("/desk/budget-revisions/MOH-BUD-2027-2028", {
			waitUntil: "domcontentloaded",
		});
		const list = page
			.locator('[data-testid="kt-bud-revisions"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(list).toBeVisible({ timeout: 45_000 });
		await list.getByTestId("kt-bud-overview-primary").click();
		await page.waitForURL(/budget-revision-create/, { timeout: 20_000 });

		const root = page
			.locator('[data-testid="kt-bud-revision-create"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-rev-create-form")).toBeVisible();
		await expect(root.getByTestId("kt-bud-rev-lines-table")).toBeVisible();
		await expect(root.getByTestId("kt-bud-rev-impact")).toBeVisible();
		await expect(root.getByTestId("kt-bud-rev-add-line")).toBeVisible();
		await expect(root.getByTestId("kt-bud-rev-save-draft")).toBeVisible();
		await expect(root.getByTestId("kt-bud-rev-submit")).toBeVisible();
		await expect(root.getByTestId("kt-bud-rev-cancel")).toBeVisible();
		await expect(root.getByRole("heading", { name: /Create budget revision/i })).toBeVisible();

		// Stitch 1/3 + 2/3 create grid (not stacked full-width).
		const leftBox = await root.locator(".kt-bud-rev-main-left").boundingBox();
		const rightBox = await root.locator(".kt-bud-rev-main-right").boundingBox();
		expect(leftBox).toBeTruthy();
		expect(rightBox).toBeTruthy();
		expect((rightBox?.x || 0) > (leftBox?.x || 0) + 40).toBeTruthy();
		expect((rightBox?.width || 0) > (leftBox?.width || 0)).toBeTruthy();

		await expect(root.locator("[data-kt-bud-rev-impact-before]")).toContainText("KES");
		await expect(root.locator("[data-kt-bud-rev-impact-before]")).toContainText(",");
		await expect(root.locator('tr[data-line-code="MOH-BL-DHI-2027"]')).toContainText(
			"KES 480,000,000",
		);
		await expect(root.locator('tr[data-line-code="MOH-BL-DHI-2027"]')).toContainText(
			"KES 145,000,000",
		);
		await expect(root.locator('tr[data-line-code="MOH-BL-DHI-2027"]')).toContainText(
			"KES 310,000,000",
		);

		await expect(root.locator('[data-kt-bud-field="generated_reference"]')).toHaveCount(0);

		// Date controls are stacked full-width and align with other fields (no card overflow).
		const bounds = await root.evaluate(() => {
			const card = document.querySelector('[data-testid="kt-bud-rev-details"]') as HTMLElement;
			const ext = document.querySelector(
				'[data-kt-bud-field="external_approval_reference"]',
			) as HTMLElement;
			const approval = document.querySelector(
				'[data-kt-bud-field="approval_date"]',
			) as HTMLElement;
			const effective = document.querySelector(
				'[data-kt-bud-field="effective_date"]',
			) as HTMLElement;
			const cardBox = card.getBoundingClientRect();
			const xBox = ext.getBoundingClientRect();
			const aBox = approval.getBoundingClientRect();
			const eBox = effective.getBoundingClientRect();
			const datesCols = getComputedStyle(
				document.querySelector(".kt-bud-rev-dates") as HTMLElement,
			).gridTemplateColumns;
			return {
				cardRight: cardBox.right,
				extRight: xBox.right,
				extWidth: xBox.width,
				approvalRight: aBox.right,
				effectiveRight: eBox.right,
				approvalWidth: aBox.width,
				effectiveWidth: eBox.width,
				approvalTop: aBox.top,
				effectiveTop: eBox.top,
				datesCols,
			};
		});
		expect(bounds.datesCols.split(" ").length).toBe(1);
		expect(bounds.effectiveTop).toBeGreaterThan(bounds.approvalTop + 20);
		expect(bounds.approvalRight).toBeLessThanOrEqual(bounds.cardRight + 1);
		expect(bounds.effectiveRight).toBeLessThanOrEqual(bounds.cardRight + 1);
		expect(Math.abs(bounds.approvalWidth - bounds.extWidth)).toBeLessThanOrEqual(2);
		expect(Math.abs(bounds.effectiveWidth - bounds.extWidth)).toBeLessThanOrEqual(2);
		expect(Math.abs(bounds.effectiveRight - bounds.extRight)).toBeLessThanOrEqual(2);
	});

	test("submit validation shows inline errors without Frappe Message", async ({ page }) => {
		await page.goto("/desk/budget-revision-create/MOH-BUD-2027-2028", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-revision-create"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-rev-create-form")).toBeVisible({ timeout: 20_000 });

		const change = root.locator(
			'tr[data-line-code="MOH-BL-DHI-2027"] [data-kt-bud-rev-change]',
		);
		await change.fill("1000000");
		await change.blur();

		await root.getByTestId("kt-bud-rev-submit").click();

		await expect(
			root.locator('[data-kt-bud-error="external_approval_reference"]'),
		).toBeVisible({ timeout: 15_000 });
		await expect(root.locator('[data-kt-bud-error="external_approval_reference"]')).not.toHaveText(
			"",
		);
		await expect(page.locator(".msgprint")).toHaveCount(0);
		await expect(page.getByRole("dialog", { name: /Message/i })).toHaveCount(0);
	});

	test("Save draft then Cancel returns to Revisions list", async ({ page }) => {
		await page.goto("/desk/budget-revision-create/MOH-BUD-2027-2028", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-revision-create"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-rev-create-form")).toBeVisible({ timeout: 20_000 });

		await root.locator('[data-kt-bud-field="external_approval_reference"]').fill("MOF/UI/REV-01");
		await root.locator('[data-kt-bud-field="approval_date"]').fill("2027-12-01");
		await root.locator('[data-kt-bud-field="effective_date"]').fill("2027-12-15");
		await root.locator('[data-kt-bud-field="reason"]').fill("Playwright draft revision");
		await root
			.locator('tr[data-line-code="MOH-BL-DHI-2027"] [data-kt-bud-rev-change]')
			.fill("2000000");

		await root.getByTestId("kt-bud-rev-save-draft").click();
		await expect(root.locator("[data-kt-bud-rev-saved-code]")).not.toHaveText("", {
			timeout: 20_000,
		});

		await root.getByTestId("kt-bud-rev-cancel").click();
		await page.waitForURL(/budget-revisions/, { timeout: 20_000 });
		const list = page
			.locator('[data-testid="kt-bud-revisions"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(list).toBeVisible({ timeout: 45_000 });
		await expect(list.getByTestId("kt-bud-revisions-list")).toBeVisible();
	});

	test("Request revision from Overview lands on create page", async ({ page }) => {
		await page.goto("/desk/budget-overview/MOH-BUD-2027-2028", {
			waitUntil: "domcontentloaded",
		});
		const ov = page
			.locator('[data-testid="kt-bud-overview"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(ov).toBeVisible({ timeout: 45_000 });
		const primary = ov.getByTestId("kt-bud-overview-primary");
		await expect(primary).toBeVisible();
		await expect(primary).toContainText(/revision/i);
		await primary.click();
		await page.waitForURL(/budget-revision-create/, { timeout: 20_000 });
		const root = page
			.locator('[data-testid="kt-bud-revision-create"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-rev-create-form")).toBeVisible();
		await expect(page.getByText(/next in the Budget MVP-1 build sequence/i)).toHaveCount(0);
	});
});
