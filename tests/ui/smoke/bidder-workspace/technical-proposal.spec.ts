import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * Technical Proposal and Implementation Plan — Stitch structure + save path.
 * Routes:
 *   /tenders/<publication_ref>/sections/technical_proposal_and_implementation_plan
 *   /tenders/<publication_ref>/sections/technical_proposal_and_implementation_plan/<subsection_key>
 *   /tenders/<publication_ref>/sections/technical_proposal_and_implementation_plan/review
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

test.describe("Technical Proposal and Implementation Plan portal", () => {
	test("overview KPI, org save, work-plan drawer, review confirm persist", async ({ page }) => {
		test.setTimeout(180_000);
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		const publicationRef = await seedLeanNssfPublished(page);
		await loginAsAdministrator(page);

		const overviewUrl = `/tenders/${publicationRef}/sections/technical_proposal_and_implementation_plan`;
		await page.goto(overviewUrl, { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-tp-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-tp-title")).toContainText(
			"Technical Proposal and Implementation Plan",
		);
		await expect(page.getByTestId("kt-tp-progress-label")).toContainText(
			"required subsections complete",
		);
		await expect(page.getByTestId("kt-tp-progress-percent")).toBeVisible();
		await expect(page.getByTestId("kt-tp-kpi")).toBeVisible();
		await expect(page.locator(".kt-tp-progress-card__bar")).toBeVisible();
		await expect(page.locator(".kt-s600-table thead")).toContainText("Subsection");
		await expect(page.locator(".kt-s600-table thead")).toContainText("What to provide");
		await expect(page.locator(".kt-s600-table thead")).toContainText("Status");
		await expect(page.locator("script[src*='tailwindcss']")).toHaveCount(0);
		await expect(page.getByTestId("kt-tp-subsection-row").first()).toBeVisible();

		// Org & coordination — narratives + tables
		await page
			.locator(
				'[data-testid="kt-tp-subsection-row"][data-subsection-key="project_organization_and_coordination"]',
			)
			.getByTestId("kt-tp-row-action")
			.click();
		await expect(page.getByTestId("kt-tp-subsection-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-tp-org-narratives")).toBeVisible();
		await expect(page.getByTestId("kt-tp-roles")).toBeVisible();
		await expect(page.getByTestId("kt-tp-coordination-matrix")).toBeVisible();

		const texts = page.locator("[data-question]");
		const count = await texts.count();
		for (let i = 0; i < count; i++) {
			await texts.nth(i).fill(`Automated response ${i + 1} for org narrative.`);
		}
		await page.getByTestId("kt-tp-add-role").click();
		const roleRow = page.locator("[data-records-body='resource_roles'] [data-record-row]").last();
		await roleRow.locator("[data-r='project_role']").fill("Project Manager");
		await roleRow.locator("[data-r='providing_org']").fill("Lead bidder");
		await roleRow.locator("[data-r='delivery_responsibility']").fill("Overall delivery");
		await roleRow.locator("[data-r='decision_authority']").fill("Yes");
		// Person select may be empty if Qualification personnel not seeded — use name fallback via typed option if present
		const personSelect = roleRow.locator("[data-r='person_id']");
		const options = await personSelect.locator("option").count();
		if (options > 1) {
			await personSelect.selectOption({ index: 1 });
		} else {
			// Domain accepts person_name when person_id empty — inject via evaluate for smoke
			await page.evaluate(() => {
				const row = document.querySelector(
					"[data-records-body='resource_roles'] [data-record-row]:last-child",
				);
				if (!row) return;
				let hidden = row.querySelector("input[data-r='person_name']") as HTMLInputElement | null;
				if (!hidden) {
					hidden = document.createElement("input");
					hidden.setAttribute("data-r", "person_name");
					hidden.type = "hidden";
					row.appendChild(hidden);
				}
				hidden.value = "Ada Lovelace";
			});
		}

		await page.getByTestId("kt-tp-add-matrix-row").click();
		const matrixRow = page
			.locator("[data-records-body='coordination_matrix'] [data-record-row]")
			.last();
		await matrixRow.locator("[data-r='activity_or_deliverable']").fill("Kick-off workshop");
		await matrixRow.locator("[data-r='bidder_responsibility']").fill("Facilitate");
		await matrixRow.locator("[data-r='pe_responsibility']").fill("Provide venue");
		await page.getByTestId("kt-tp-save").click();
		await expect(page.getByTestId("kt-tp-toast")).toBeVisible({ timeout: 15_000 });

		await page.getByTestId("kt-tp-sub-back").click();
		await expect(page.getByTestId("kt-tp-root")).toBeVisible({ timeout: 30_000 });

		// Work plan — drawer + completion week
		const workPlanRow = page.locator(
			'[data-testid="kt-tp-subsection-row"][data-subsection-key="implementation_work_plan"]',
		);
		if (await workPlanRow.count()) {
			await workPlanRow.getByTestId("kt-tp-row-action").click();
			await expect(page.getByTestId("kt-tp-work-plan")).toBeVisible({ timeout: 30_000 });
			await page.getByTestId("kt-tp-add-activity").click();
			await expect(page.getByTestId("kt-tp-drawer")).toBeVisible();
			await page.locator("[data-d='activity']").fill("Solution design");
			await page.locator("[data-d='start_week']").fill("1");
			await page.locator("[data-d='duration_weeks']").fill("4");
			await page.locator("[data-d='project_role']").fill("Project Manager");
			const preview = page.getByTestId("kt-tp-completion-preview");
			if (await preview.count()) {
				await expect(preview).toContainText("4");
			}
			await page.getByTestId("kt-tp-drawer-confirm").click();
			await expect(page.getByTestId("kt-tp-drawer")).toBeHidden({ timeout: 10_000 });
			await page.getByTestId("kt-tp-save").click();
			await expect(page.getByTestId("kt-tp-toast")).toBeVisible({ timeout: 15_000 });
			await page.reload({ waitUntil: "domcontentloaded" });
			await expect(page.getByTestId("kt-tp-work-plan-body").locator("[data-record-row]")).toHaveCount(
				1,
				{ timeout: 30_000 },
			);
			await page.getByTestId("kt-tp-sub-back").click();
		}

		// Transition handover — checkbox ticks must persist after save + reload.
		const transitionRow = page.locator(
			'[data-testid="kt-tp-subsection-row"][data-subsection-key="transition_and_handover"]',
		);
		if (await transitionRow.count()) {
			await transitionRow.getByTestId("kt-tp-row-action").click();
			await expect(page.getByTestId("kt-tp-handover")).toBeVisible({ timeout: 30_000 });
			const narratives = page.locator("[data-question]");
			const nNarr = await narratives.count();
			for (let i = 0; i < nNarr; i++) {
				await narratives.nth(i).fill(`Handover narrative ${i + 1}.`);
			}
			const checks = page.locator("[data-handover-provided]");
			await checks.nth(0).check();
			await checks.nth(1).check();
			await page.getByTestId("kt-tp-save").click();
			await expect(page.getByTestId("kt-tp-toast")).toContainText(/Saved/i, { timeout: 15_000 });
			await page.reload({ waitUntil: "domcontentloaded" });
			await expect(page.getByTestId("kt-tp-handover")).toBeVisible({ timeout: 30_000 });
			await expect(checks.nth(0)).toBeChecked();
			await expect(checks.nth(1)).toBeChecked();
			// Visible checked chrome (not appearance:none blank boxes).
			const bg = await checks.nth(0).evaluate((el) => getComputedStyle(el).backgroundImage);
			expect(bg).toMatch(/url\(|svg/i);
			await page.getByTestId("kt-tp-sub-back").click();
			await expect(page.getByTestId("kt-tp-root")).toBeVisible({ timeout: 30_000 });
		}

		// Testing stages — Status cell must precede Action (delete must not sit under Status).
		const testingRow = page.locator(
			'[data-testid="kt-tp-subsection-row"][data-subsection-key="testing_and_quality_assurance"]',
		);
		if (await testingRow.count()) {
			await testingRow.getByTestId("kt-tp-row-action").click();
			await expect(page.getByTestId("kt-tp-test-stages")).toBeVisible({ timeout: 30_000 });
			await page.getByTestId("kt-tp-add-stage").click();
			const stageRow = page.locator("[data-records-body='test_stages'] [data-record-row]").last();
			await expect(stageRow.locator("[data-tp-status-cell]")).toBeVisible();
			await expect(stageRow.locator("[data-row-status-badge]")).toContainText(/Started|Progress|Complete/i);
			await expect(stageRow.locator("[data-tp-action-cell] [data-tp-remove-row]")).toBeVisible();
			// Delete must not be the only content of the Status column.
			await expect(stageRow.locator("[data-tp-status-cell] [data-tp-remove-row]")).toHaveCount(0);
			await page.getByTestId("kt-tp-sub-back").click();
			await expect(page.getByTestId("kt-tp-root")).toBeVisible({ timeout: 30_000 });
		}

		// Review + integration confirm (does not seal)
		await page.goto(
			`/tenders/${publicationRef}/sections/technical_proposal_and_implementation_plan/review`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.getByTestId("kt-tp-review-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-tp-review-kpi")).toBeVisible();
		await expect(page.getByTestId("kt-tp-review-progress-percent")).toBeVisible();
		await expect(page.getByTestId("kt-tp-consolidated-summary")).toBeVisible();
		await expect(page.getByTestId("kt-tp-confirm-checkbox")).toBeVisible();
		await expect(page.getByTestId("kt-tp-save-draft")).toBeVisible();
		const root = page.getByTestId("kt-tp-review-root");
		const alreadyConfirmed = (await root.getAttribute("data-confirmed")) === "1";
		if (!alreadyConfirmed) {
			await page.getByTestId("kt-tp-confirm-checkbox").check();
			await expect(page.getByTestId("kt-tp-save-draft")).toBeEnabled();
			await page.getByTestId("kt-tp-save-draft").click();
			await expect(page.getByTestId("kt-tp-review-toast")).toContainText(/Confirmation saved|already/i, {
				timeout: 15_000,
			});
			await expect(root).toHaveAttribute("data-confirmed", "1");
			await page.reload({ waitUntil: "domcontentloaded" });
			await expect(page.getByTestId("kt-tp-review-root")).toHaveAttribute("data-confirmed", "1", {
				timeout: 30_000,
			});
			await expect(page.getByTestId("kt-tp-confirm-checkbox")).toBeChecked();
		}
		// Complete Section must leave review for the section overview.
		await page.getByTestId("kt-tp-confirm-btn").click();
		await expect(page).toHaveURL(
			new RegExp(`/tenders/${publicationRef}/sections/technical_proposal_and_implementation_plan/?$`),
			{ timeout: 20_000 },
		);
		await expect(page.getByTestId("kt-tp-root")).toBeVisible({ timeout: 30_000 });

		// Desk chrome should stay hidden on Website portal
		await expect(page.locator(".navbar .navbar-home")).toHaveCount(0);
	});
});
