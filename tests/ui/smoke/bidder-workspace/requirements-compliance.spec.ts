import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * Requirements Compliance — Stitch workspace + drawer + review.
 * Routes:
 *   /tenders/<publication_ref>/sections/requirements_compliance
 *   /tenders/<publication_ref>/sections/requirements_compliance/review
 */

async function seedLeanRcPublished(page: import("@playwright/test").Page): Promise<string> {
	await page.waitForFunction(
		() => typeof (window as unknown as { frappe?: unknown }).frappe !== "undefined",
	);
	const result = await page.evaluate(async () => {
		// @ts-expect-error frappe on desk
		const r = await frappe.call({
			method: "kentender_procurement.tender_configurations.publish_lean_requirements_compliance_for_tests",
			args: { clear: 1, fixture: "standard" },
		});
		return r.message || r;
	});
	const ref = (result as { publication_ref?: string }).publication_ref || "";
	if (!ref) {
		throw new Error("Lean RC publish seed failed: " + JSON.stringify(result));
	}
	return ref;
}

async function completeAllRequiredViaApi(
	page: import("@playwright/test").Page,
	publicationRef: string,
): Promise<void> {
	await page.evaluate(async (ref) => {
		const requiredIds = ["rc-cap-001", "rc-cap-002", "rc-sec-001", "rc-int-001"];
		for (const rid of requiredIds) {
			// @ts-expect-error frappe on website
			await frappe.call({
				method: "kentender_procurement.tender_configurations.save_requirement_response",
				args: {
					published_tender_ref: ref,
					section_key: "requirements_compliance",
					requirement_id: rid,
					payload: {
						compliant_yes_no: "Yes",
						compliance_statement: "Playwright complete",
						numeric_value: 100,
						acknowledged: 1,
						schedule_rows: [{ activity: "A", timing: "Week 1" }],
						evidence_uploads: [{ file_name: "e.pdf", mock: 1 }],
						addendum_reviewed: true,
					},
				},
			});
		}
	}, publicationRef);
}

test.describe("Requirements Compliance portal", () => {
	test("workspace drawer save, review Complete Section, no Desk chrome", async ({ page }) => {
		test.setTimeout(180_000);
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		const publicationRef = await seedLeanRcPublished(page);
		await loginAsAdministrator(page);

		const workspaceUrl = `/tenders/${publicationRef}/sections/requirements_compliance`;
		await page.goto(workspaceUrl, { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-rc-workspace-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-rc-title")).toBeVisible();
		await expect(page.getByTestId("kt-rc-progress-label")).toContainText(
			/required responses complete/i,
		);
		await expect(page.getByTestId("kt-rc-group-rail")).toBeVisible();
		await expect(page.getByTestId("kt-rc-requirements-table")).toBeVisible();
		expect(page.url()).not.toMatch(/\/desk\/|it-electronic-bidder-workspace/);

		const startBtn = page
			.getByTestId("kt-a4-row-action")
			.filter({ hasText: /Start|Continue|Resolve/i })
			.first();
		await expect(startBtn).toBeVisible({ timeout: 15_000 });
		await startBtn.click();
		await expect(page.getByTestId("kt-a4-drawer")).toBeVisible({ timeout: 15_000 });

		const yesBtn = page.locator('[data-testid="kt-a4-yesno"] button[data-value="Yes"]').first();
		if (await yesBtn.count()) {
			await yesBtn.click();
		}
		const explanation = page
			.locator('[data-testid="kt-a4-field-compliance_statement"], textarea[name="compliance_statement"], textarea[name="explanation"]')
			.first();
		if (await explanation.count()) {
			await explanation.fill("Playwright smoke explanation for requirements compliance.");
		}
		const boolCheck = page.locator('input[type="checkbox"][name="acknowledged"]').first();
		if (await boolCheck.count()) {
			await boolCheck.check();
		}

		await page.getByTestId("kt-a4-drawer-save").click();
		// Row status must refresh from save→applyMatrix (same path updates kt-rc-progress-*).
		await expect(page.getByTestId("kt-a4-row-status").first()).not.toHaveText(/Not Started/i, {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-rc-progress-label")).toBeVisible();
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-rc-workspace-root")).toBeVisible({ timeout: 30_000 });

		await page.goto(`${workspaceUrl}/review`, { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-rc-review-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-rc-kpi-grid")).toBeVisible();
		await expect(page.getByTestId("kt-rc-complete-btn")).toBeVisible();
		await expect(page.getByTestId("kt-rc-review-back")).toBeVisible();
		await expect(page.getByTestId("kt-rc-review-back")).toHaveAttribute(
			"href",
			new RegExp(`/tenders/${publicationRef}/sections/requirements_compliance/?$`),
		);
		await expect(page.getByTestId("kt-rc-review-save-draft")).toHaveCount(0);

		const completeEnabled = await page
			.getByTestId("kt-rc-review-root")
			.getAttribute("data-complete-enabled");
		if (completeEnabled !== "1") {
			await page.goto(workspaceUrl, { waitUntil: "domcontentloaded" });
			await expect(page.getByTestId("kt-rc-workspace-root")).toBeVisible({ timeout: 30_000 });
			await completeAllRequiredViaApi(page, publicationRef);
			await page.goto(`${workspaceUrl}/review`, { waitUntil: "domcontentloaded" });
			await expect(page.getByTestId("kt-rc-review-root")).toHaveAttribute(
				"data-complete-enabled",
				"1",
				{ timeout: 30_000 },
			);
		}

		await page.getByTestId("kt-rc-complete-btn").click();
		// Complete Section must return to the Submission Checklist (orchestrator), not loop
		// back into the Requirements Compliance matrix.
		await expect(page).toHaveURL(
			new RegExp(`/tenders/${publicationRef}/workspace/?$`),
			{ timeout: 20_000 },
		);
		await expect(page.getByTestId("kt-a2-checklist-root")).toBeVisible({ timeout: 30_000 });

		await page.goto(`${workspaceUrl}/review`, { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-rc-review-root")).toHaveAttribute("data-confirmed", "1", {
			timeout: 30_000,
		});

		await expect(page.locator(".navbar .navbar-home")).toHaveCount(0);
	});
});
