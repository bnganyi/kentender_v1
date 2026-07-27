import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * S600 Qualification and Capability — Stitch structure + save path.
 * Routes:
 *   /tenders/<publication_ref>/sections/qualification_and_capability
 *   /tenders/<publication_ref>/sections/qualification_and_capability/<category_key>
 */

async function seedLeanNssfPublished(page: import("@playwright/test").Page): Promise<string> {
	await page.waitForFunction(
		() => typeof (window as unknown as { frappe?: unknown }).frappe !== "undefined",
	);
	const result = await page.evaluate(async () => {
		// @ts-expect-error frappe on desk
		const r = await frappe.call({
			method: "kentender_procurement.tender_configurations.publish_e1_nssf_lean_for_tests",
			args: { clear: 1 },
		});
		return r.message || r;
	});
	const ref = (result as { publication_ref?: string }).publication_ref || "";
	if (!ref) {
		throw new Error("Lean NSSF publish seed failed: " + JSON.stringify(result));
	}
	return ref;
}

test.describe("Qualification and Capability portal", () => {
	test("overview + category screens match Stitch structure and financial save works", async ({
		page,
	}) => {
		test.setTimeout(180_000);
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		const publicationRef = await seedLeanNssfPublished(page);
		await loginAsAdministrator(page);

		await page.goto(
			`/tenders/${publicationRef}/sections/qualification_and_capability`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.getByTestId("kt-s600-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-s600-title")).toContainText(
			"Qualification and Capability",
		);
		await expect(page.getByTestId("kt-s600-progress-label")).toContainText(
			"required categories complete",
		);
		await expect(page.getByTestId("kt-s600-category-row")).toHaveCount(5);
		await expect(page.locator(".kt-s600-table thead")).toContainText("Category");
		await expect(page.locator(".kt-s600-table thead")).toContainText("Requirement summary");
		await expect(page.locator(".kt-s600-table thead")).toContainText("Progress");
		await expect(page.locator("script[src*='tailwindcss']")).toHaveCount(0);

		// Contract — disclosure tables
		await page
			.locator(
				'[data-testid="kt-s600-category-row"][data-category-key="contract_performance_and_litigation"]',
			)
			.getByTestId("kt-s600-row-action")
			.click();
		await expect(page.getByTestId("kt-s600-category-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-s600-contract")).toBeVisible();
		await expect(page.getByText("2. Non-performing Contracts")).toBeVisible();
		await expect(page.getByText("3. Pending Litigation")).toBeVisible();
		await expect(page.getByText("4. Litigation History")).toBeVisible();
		// Stitch: records table + Add appear only after Yes.
		await page.locator('input[name="non_performing"][value="yes"]').check();
		const addNonPerf = page.getByText("Add non-performing contract");
		await expect(addNonPerf).toBeVisible();
		await expect(page.locator("[data-records-table='non_performing'] thead")).toContainText(
			"Contract",
		);
		// Add… is a sibling below the bordered table wrap — not floating inside empty tbody.
		const panel = page.locator("[data-yes-panel='non_performing']");
		const tableBox = await panel.locator(".kt-s600-table-wrap").boundingBox();
		const addBox = await addNonPerf.boundingBox();
		expect(tableBox).toBeTruthy();
		expect(addBox).toBeTruthy();
		expect(addBox!.y).toBeGreaterThan(tableBox!.y + tableBox!.height - 1);
		expect(addBox!.y - (tableBox!.y + tableBox!.height)).toBeLessThan(24);
		expect(addBox!.y - (tableBox!.y + tableBox!.height)).toBeGreaterThanOrEqual(8);
		await expect(page.getByTestId("kt-s600-drawer")).toBeAttached();
		await page.getByTestId("kt-s600-cat-back").click();
		await expect(page.getByTestId("kt-s600-root")).toBeVisible({ timeout: 30_000 });

		// Financial — three tables + configured requirements
		await page
			.locator(
				'[data-testid="kt-s600-category-row"][data-category-key="financial_capability"]',
			)
			.getByTestId("kt-s600-row-action")
			.click();
		await expect(page.getByTestId("kt-s600-financial")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-s600-configured-requirements")).toBeVisible();
		await expect(
			page.getByRole("heading", { name: "Historical Financial Performance" }),
		).toBeVisible();
		await expect(page.getByTestId("kt-s600-turnover")).toBeVisible();
		await expect(page.getByTestId("kt-s600-resources")).toBeVisible();
		await expect(page.getByTestId("kt-s600-add-resource")).toBeVisible();
		await expect(page.locator("[data-testid='kt-s600-fy-body']")).toBeVisible();
		await expect(page.getByTestId("kt-s600-financial").locator("thead")).toContainText(
			"Total Assets",
		);
		await expect(page.getByTestId("kt-s600-resources").locator("thead")).toContainText(
			"Resource Type",
		);

		for (const row of await page.locator("[data-fy-row]").all()) {
			await row.locator("[data-fy='attached']").check();
			await row.locator("[data-fy='file']").fill("statement.pdf");
		}
		const toRows = page.locator("[data-to-row]");
		const toCount = await toRows.count();
		for (let i = 0; i < toCount; i++) {
			await toRows.nth(i).locator("[data-to='amount']").fill("15000000");
		}
		await page.getByTestId("kt-s600-add-resource").click();
		const resRow = page.locator("[data-res-row]").last();
		await resRow.locator("[data-res='type']").fill("Liquid assets");
		await resRow.locator("[data-res='amount']").fill("5000000");
		await resRow.locator("[data-res='currency']").fill("KES");

		await page.getByTestId("kt-s600-save-continue").click();
		await expect(page.getByTestId("kt-s600-root")).toBeVisible({ timeout: 30_000 });
		const finRow = page.locator(
			'[data-testid="kt-s600-category-row"][data-category-key="financial_capability"]',
		);
		await expect(finRow.getByTestId("kt-s600-row-status")).toHaveAttribute(
			"data-status",
			"Complete",
			{ timeout: 15_000 },
		);

		// Experience — requirements first, then dual-scope save without duplicates
		await page
			.locator('[data-testid="kt-s600-category-row"][data-category-key="experience"]')
			.getByTestId("kt-s600-row-action")
			.click();
		await expect(page.getByTestId("kt-s600-experience")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-s600-exp-config")).toBeVisible();
		await expect(page.getByTestId("kt-s600-req-min-years")).toBeVisible();
		await expect(page.getByTestId("kt-s600-req-min-specific")).toBeVisible();
		await expect(page.getByTestId("kt-s600-cat-progress")).toBeHidden();
		await expect(page.getByRole("heading", { name: "General Experience" })).toBeVisible();
		await expect(page.getByRole("heading", { name: "Specific Experience" })).toBeVisible();
		await expect(page.getByTestId("kt-s600-experience").locator("thead")).toContainText(
			"Qualifying years",
		);
		await expect(page.getByTestId("kt-s600-specific").locator("thead")).toContainText(
			"Similarity details",
		);
		await expect(page.getByTestId("kt-s600-add-project")).toBeVisible();
		await page.getByTestId("kt-s600-add-project").click();
		await expect(page.getByTestId("kt-s600-drawer")).toBeVisible();
		await expect(page.getByTestId("kt-s600-drawer-title")).toHaveText(/Add project/i);
		await expect(page.getByTestId("kt-s600-project-drawer-form")).toBeVisible();
		const drawer = page.getByTestId("kt-s600-drawer");
		await drawer.locator('[data-d="contract_id"]').fill("IFMIS Integration");
		await drawer.locator('[data-d="pe"]').fill("NSSF SPS");
		await drawer.locator('[data-d="role"]').fill("PM");
		await drawer.locator('[data-d="start_month"]').fill("1");
		await drawer.locator('[data-d="start_year"]').fill("2020");
		await drawer.locator('[data-d="end_month"]').fill("12");
		await drawer.locator('[data-d="end_year"]').fill("2025");
		await drawer.locator('[data-d="amount"]').fill("100000");
		const specificChip = drawer.locator('[data-d="specific"]');
		if (!(await specificChip.isChecked())) {
			await specificChip.check();
		}
		await expect(drawer.locator('[data-d="general"]')).toBeChecked();
		await expect(specificChip).toBeChecked();
		await page.getByTestId("kt-s600-drawer-confirm").click();
		await expect(page.getByTestId("kt-s600-drawer")).toBeHidden({ timeout: 15_000 });
		const generalRows = page.locator('[data-project-table="general"] [data-project-row]');
		const specificRows = page.locator('[data-project-table="specific"] [data-project-row]');
		await expect(generalRows).toHaveCount(1, { timeout: 15_000 });
		await expect(specificRows).toHaveCount(1);
		const sharedId = await generalRows.first().getAttribute("data-project-id");
		expect(sharedId).toBeTruthy();
		await expect(specificRows.first()).toHaveAttribute("data-project-id", sharedId!);
		await expect(generalRows.first().locator(".kt-s600-status")).toHaveAttribute(
			"data-status",
			"Complete",
			{ timeout: 15_000 },
		);
		await expect(specificRows.first().locator(".kt-s600-status")).toHaveAttribute(
			"data-status",
			"Complete",
		);
		// Edit existing specific row and save — status must flip to Complete without reload.
		await specificRows.first().locator("[data-s600-edit-project]").click();
		await expect(page.getByTestId("kt-s600-drawer")).toBeVisible();
		await page.getByTestId("kt-s600-drawer").locator('[data-d="similarity"]').fill("Similar ERP delivery");
		const saveExperienceEdit = page.waitForResponse(
			(res) => {
				const data = res.request().postData() || "";
				return data.includes("save_qualification_category") && res.status() === 200;
			},
			{ timeout: 20_000 },
		);
		await page.getByTestId("kt-s600-drawer-confirm").click();
		await expect(page.getByTestId("kt-s600-drawer")).toBeHidden({ timeout: 15_000 });
		await saveExperienceEdit;
		await expect(
			page.locator('[data-project-table="specific"] [data-project-row]').first().locator(".kt-s600-status"),
		).toHaveAttribute("data-status", "Complete", { timeout: 15_000 });
		await expect(page.getByTestId("kt-s600-specific-progress")).toContainText(/of/i);
		await page.getByTestId("kt-s600-cat-back").click();

		// Personnel — create person from Assign and assign in one step
		await page
			.locator('[data-testid="kt-s600-category-row"][data-category-key="key_personnel"]')
			.getByTestId("kt-s600-row-action")
			.click();
		await expect(page.getByTestId("kt-s600-personnel")).toBeVisible({ timeout: 30_000 });
		// In-body Completion Progress replaces the page-head status/progress KPI.
		await expect(page.getByTestId("kt-s600-cat-progress")).toBeHidden();
		await expect(page.getByTestId("kt-s600-personnel-progress")).toBeVisible();
		await expect(page.getByRole("heading", { name: "Personnel Matrix" })).toBeVisible();
		await expect(page.getByTestId("kt-s600-personnel-matrix")).toBeVisible();
		await expect(page.getByTestId("kt-s600-personnel").locator("thead")).toContainText(
			"Required Position",
		);
		await expect(page.getByTestId("kt-s600-personnel").locator("thead")).toContainText(
			"Assigned Person",
		);
		const firstAssign = page.locator("[data-s600-assign]").first();
		await firstAssign.click();
		await expect(page.getByTestId("kt-s600-drawer")).toBeVisible();
		await page.locator("[data-s600-new-person]").click();
		await expect(page.getByTestId("kt-s600-new-person-form")).toBeVisible();
		// Validation must keep the drawer open with an in-drawer error (not a silent no-op).
		await page.getByTestId("kt-s600-drawer-confirm").click();
		await expect(page.getByTestId("kt-s600-drawer")).toBeVisible();
		await expect(page.getByTestId("kt-s600-drawer-form-error")).toBeVisible();
		await expect(page.getByTestId("kt-s600-drawer-form-error")).toContainText(/full name/i);
		const waitQualSave = () =>
			page.waitForResponse(
				(res) => {
					const data = res.request().postData() || "";
					// Website frappe.call posts to `/` with cmd=...save_qualification_category
					return data.includes("save_qualification_category") && res.status() === 200;
				},
				{ timeout: 20_000 },
			);
		await page.getByTestId("kt-s600-new-person-form").locator('[data-d="name"]').fill("Ada Lovelace");
		await page.getByTestId("kt-s600-new-person-form").locator('[data-d="years"]').fill("12");
		await page.getByTestId("kt-s600-new-person-form").locator('[data-d="qual"]').fill("PMP");
		const saveAda = waitQualSave();
		await page.getByTestId("kt-s600-drawer-confirm").click();
		await expect(page.getByTestId("kt-s600-drawer")).toBeHidden({ timeout: 15_000 });
		await saveAda;
		const firstPosRow = page.locator("[data-position-row]").first();
		await expect(firstPosRow.locator("[data-assigned-name]")).toContainText("Ada Lovelace");
		await expect(firstPosRow.locator(".kt-s600-status")).toHaveAttribute("data-status", "Complete");
		await expect(page.getByTestId("kt-s600-personnel-progress-text")).toContainText("1 of", {
			timeout: 15_000,
		});
		// Duplicate assignment is blocked at assign time (not only on later Save).
		const secondAssign = page.locator("[data-s600-assign]").nth(1);
		await secondAssign.click();
		await expect(page.getByTestId("kt-s600-drawer")).toBeVisible();
		const adaCard = page.locator('[data-testid="kt-s600-person-card"]').filter({
			hasText: "Ada Lovelace",
		});
		await expect(adaCard).toContainText(/Assigned to/i);
		await expect(adaCard.locator('input[name="assign_person"]')).toBeDisabled();
		// Create+assign a second person onto Lead Developer in one Save person click.
		await page.locator("[data-s600-new-person]").click();
		await expect(page.getByTestId("kt-s600-new-person-form")).toBeVisible();
		await expect(page.getByTestId("kt-s600-new-person-form")).toHaveAttribute(
			"data-assign-position-id",
			/.+/,
		);
		await page.getByTestId("kt-s600-new-person-form").locator('[data-d="name"]').fill("Grace Hopper");
		await page.getByTestId("kt-s600-new-person-form").locator('[data-d="years"]').fill("10");
		await page.getByTestId("kt-s600-new-person-form").locator('[data-d="qual"]').fill("PhD CS");
		const saveGrace = waitQualSave();
		await page.getByTestId("kt-s600-drawer-confirm").click();
		await expect(page.getByTestId("kt-s600-drawer")).toBeHidden({ timeout: 15_000 });
		await saveGrace;
		const secondPosRow = page.locator("[data-position-row]").nth(1);
		await expect(secondPosRow.locator("[data-assigned-name]")).toContainText("Grace Hopper");
		await expect(secondPosRow.locator(".kt-s600-status")).toHaveAttribute("data-status", "Complete");
		await expect(page.getByTestId("kt-s600-personnel-progress-text")).toContainText("2 of", {
			timeout: 15_000,
		});
		// Third position: create+assign Business Analyst and persist across reload.
		const thirdAssign = page.locator("[data-s600-assign]").nth(2);
		await thirdAssign.click();
		await page.locator("[data-s600-new-person]").click();
		await page.getByTestId("kt-s600-new-person-form").locator('[data-d="name"]').fill("Katherine Johnson");
		await page.getByTestId("kt-s600-new-person-form").locator('[data-d="years"]').fill("8");
		await page.getByTestId("kt-s600-new-person-form").locator('[data-d="qual"]').fill("Mathematics");
		const saveKatherine = waitQualSave();
		await page.getByTestId("kt-s600-drawer-confirm").click();
		await expect(page.getByTestId("kt-s600-drawer")).toBeHidden({ timeout: 15_000 });
		await saveKatherine;
		const thirdPosRow = page.locator("[data-position-row]").nth(2);
		await expect(thirdPosRow.locator("[data-assigned-name]")).toContainText("Katherine Johnson");
		await expect(page.getByTestId("kt-s600-personnel-progress-text")).toContainText("3 of", {
			timeout: 15_000,
		});
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-s600-personnel")).toBeVisible({ timeout: 30_000 });
		await expect(page.locator("[data-position-row]").nth(2).locator("[data-assigned-name]")).toContainText(
			"Katherine Johnson",
		);
		await expect(page.getByTestId("kt-s600-personnel-progress-text")).toContainText("3 of");
		await page.getByTestId("kt-s600-cat-back").click();

		// Partners — provider matrix (no duplicate header KPI; radios must not look like text inputs)
		await page
			.locator('[data-testid="kt-s600-category-row"][data-category-key="delivery_partners"]')
			.getByTestId("kt-s600-row-action")
			.click();
		await expect(page.getByTestId("kt-s600-partners")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-s600-cat-progress")).toBeHidden();
		await expect(page.getByTestId("kt-s600-partners-progress")).toBeVisible();
		await expect(page.getByTestId("kt-s600-partners-progress-text")).toBeVisible();
		await expect(page.getByTestId("kt-s600-partners-matrix")).toBeVisible();
		await expect(page.getByTestId("kt-s600-partners").locator("thead")).toContainText(
			"Item or service",
		);
		await expect(page.getByTestId("kt-s600-partners").locator("thead")).toContainText(
			"Proposed organization",
		);
		await expect(page.getByText("Another organization").first()).toBeVisible();
		const providerRadio = page.locator(".kt-s600-radio-col input[type='radio']").first();
		await expect(providerRadio).toBeVisible();
		const radioBox = await providerRadio.boundingBox();
		expect(radioBox).toBeTruthy();
		expect(radioBox!.width).toBeLessThan(28);
		expect(radioBox!.height).toBeLessThan(28);
		await expect(page.locator("nav.navbar")).toBeHidden();
	});
});
