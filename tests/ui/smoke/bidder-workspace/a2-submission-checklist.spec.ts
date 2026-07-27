import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * A2 Submission Checklist — Website workspace home.
 * Route: /tenders/<publication_ref>/workspace
 *
 * Seeds the lean NSSF published tender (electronic template snapshot) so the
 * checklist is authoritative and not dependent on stale /tenders cards.
 */

const CHECKLIST = '[data-testid="kt-a2-checklist-root"]';

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

test.describe("A2 Submission Checklist portal", () => {
	test("workspace checklist loads on Website with sidebar (no Desk Procurement rail)", async ({
		page,
	}) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		const publicationRef = await seedLeanNssfPublished(page);
		// Re-auth for Website host — long seed / desk session can drop portal cookies.
		await loginAsAdministrator(page);

		await page.goto(`/tenders/${publicationRef}/workspace`, {
			waitUntil: "domcontentloaded",
		});
		expect(page.url()).toMatch(/\/tenders\/[^/?#]+\/workspace/);
		expect(page.url()).not.toMatch(/\/desk\/|it-electronic-bidder-workspace/);

		await expect(page.locator(CHECKLIST)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-a2-title")).toContainText("Submission Checklist");
		await expect(page.getByTestId("kt-a2-sidebar")).toBeVisible();
		await expect(page.getByTestId("kt-a2-nav-checklist")).toBeVisible();
		await expect(page.getByTestId("kt-a2-section-checklist")).toBeVisible();
		await expect(page.getByTestId("kt-a2-section-row").first()).toBeVisible();
		await expect(page.getByTestId("kt-a2-primary-cta")).toBeVisible();

		// Lean canonical 10-section checklist (includes Tender Security + Form of Tender).
		await expect(page.getByTestId("kt-a2-section-row")).toHaveCount(10);
		await expect(page.locator(CHECKLIST)).toContainText("Form of Tender");
		await expect(page.locator(CHECKLIST)).toContainText("Tender Security");

		const countdown = page.getByTestId("kt-a2-time-remaining");
		await expect(countdown).toHaveAttribute("data-kt-countdown", "");
		await expect(countdown).toHaveAttribute("data-deadline", /.+/);
		const before = (await countdown.innerText()).trim();
		await expect
			.poll(async () => (await countdown.innerText()).trim(), { timeout: 2500 })
			.not.toBe(before);

		const body = await page.locator("body").innerText();
		expect(body).not.toMatch(/Tender Management|Tender Configurations|Evaluation and Award/i);
		await expect(page.locator("nav.navbar")).toBeHidden();

		await expect(page.getByTestId("kt-a2-progress-label")).toHaveText(/Sections complete/i);
		await expect(page.getByTestId("kt-a2-progress-tasks")).toBeVisible();

		const summary = page.getByTestId("kt-a2-kpi-summary");
		const deadline = page.getByTestId("kt-a2-kpi-deadline");
		const progress = page.getByTestId("kt-a2-kpi-progress");
		await expect(page.getByTestId("kt-a2-kpis-aside")).toHaveCount(0);
		const summaryBox = await summary.boundingBox();
		const deadlineBox = await deadline.boundingBox();
		const progressBox = await progress.boundingBox();
		expect(summaryBox).toBeTruthy();
		expect(deadlineBox).toBeTruthy();
		expect(progressBox).toBeTruthy();
		// Desktop: three KPI cards in one row (never stacked / wrapped).
		expect(summaryBox!.x + summaryBox!.width).toBeLessThanOrEqual(deadlineBox!.x + 1);
		expect(deadlineBox!.x + deadlineBox!.width).toBeLessThanOrEqual(progressBox!.x + 1);
		expect(Math.abs(summaryBox!.y - deadlineBox!.y)).toBeLessThan(8);
		expect(Math.abs(deadlineBox!.y - progressBox!.y)).toBeLessThan(8);
		expect(Math.abs(summaryBox!.height - deadlineBox!.height)).toBeLessThan(8);
	});

	test("progress KPI is Complete-only and shows in-progress secondary line", async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		const publicationRef = await seedLeanNssfPublished(page);
		await loginAsAdministrator(page);

		await page.waitForFunction(
			() => typeof (window as unknown as { frappe?: unknown }).frappe !== "undefined",
		);
		const prep = await page.evaluate(async (ref: string) => {
			// @ts-expect-error frappe on desk
			const start = await frappe.call({
				method: "kentender_procurement.tender_configurations.start_or_get_bid_workspace",
				args: { published_tender_ref: ref },
			});
			const bidId = (start.message || start).bid_id;
			// @ts-expect-error frappe on desk
			await frappe.call({
				method: "kentender_procurement.tender_configurations.acknowledge_tender_documents",
				args: { published_tender_ref: ref },
			});
			// @ts-expect-error frappe on desk
			await frappe.call({
				method: "kentender_procurement.tender_configurations.save_electronic_bid_section",
				args: {
					bid_id: bidId,
					section_key: "technical_proposal_and_implementation_plan",
					payload: { draft_answer: "wip", in_progress: true },
				},
			});
			// @ts-expect-error frappe on desk
			const checklist = await frappe.call({
				method: "kentender_procurement.tender_configurations.get_submission_checklist",
				args: { published_tender_ref: ref },
			});
			return checklist.message || checklist;
		}, publicationRef);

		expect(prep.progress_complete).toBe(1);
		expect(prep.progress_in_progress).toBe(1);
		expect(prep.progress_percent).toBe(
			Math.round((100 * prep.progress_complete) / prep.progress_total),
		);

		await page.goto(`/tenders/${publicationRef}/workspace`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(CHECKLIST)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-a2-progress-label")).toHaveText(/Sections complete/i);
		await expect(page.getByTestId("kt-a2-progress-pct")).toHaveText(
			`${prep.progress_percent}%`,
		);
		await expect(page.getByTestId("kt-a2-progress-tasks")).toContainText(
			`${prep.progress_complete} of ${prep.progress_total} required sections complete`,
		);
		await expect(page.getByTestId("kt-a2-progress-in-progress")).toContainText(
			`${prep.progress_in_progress} in progress`,
		);
	});
});
