import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { expectConfigurationContextStrip } from "../../helpers/ktClConfigContext";

/**
 * WG-02 Review & Approval (WF-02).
 * Route: /desk/it-tender-configuration-review-and-approval/<configuration_id>
 * Layout contract: D1-WG2 (summary | sections, checklist | findings, footer).
 */

const PAGE_SLUG = "it-tender-configuration-review-and-approval";
const ROOT = '[data-testid="kt-cl-wf02-root"]';
const REVIEW_CONFIG = "TCFG-SEED-TCFG-UR";

const FORBIDDEN = [/\bpublish tender\b/i];

async function seedUi00(page: import("@playwright/test").Page) {
	await page.waitForFunction(() => typeof (window as unknown as { frappe?: unknown }).frappe !== "undefined");
	const result = await page.evaluate(async () => {
		// @ts-expect-error frappe on desk
		const r = await frappe.call({
			method: "kentender_procurement.tender_configurations.seed_ui00_dashboard_for_tests",
			args: { clear: 1 },
		});
		return r.message || r;
	});
	if (!result || !(result as { configurations?: string[] }).configurations) {
		throw new Error("WG-02 seed failed: " + JSON.stringify(result));
	}
}

async function openReview(page: import("@playwright/test").Page, configId = REVIEW_CONFIG) {
	await page.goto(`/desk/${PAGE_SLUG}/${encodeURIComponent(configId)}`);
	await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
	await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${configId}`), { timeout: 15_000 });
	await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
}

test.describe.configure({ mode: "serial" });

test.describe("WG-02 Review & Approval", () => {
	test.beforeAll(async ({ browser }) => {
		const page = await browser.newPage();
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await seedUi00(page);
		await page.close();
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
	});

	test("layout: strip, summary, sections, checklist, findings, footer", async ({ page }) => {
		await openReview(page);
		await expectConfigurationContextStrip(page, {
			family: /Information Technology/i,
			stdDocument: /IT Standard Tender Document/i,
		});
		await expect(page.getByTestId("kt-cl-wf02-summary")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf02-card-steps")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf02-card-readiness")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf02-sections")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf02-checklist")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf02-findings")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf02-decision")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf02-approve")).toHaveText(/Approve for Document Preview/i);
		await expect(page.getByTestId("kt-cl-wf02-return")).toHaveText(/Return for Correction/i);
		await expect(page.getByTestId("kt-cl-wf02-add-finding")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf02-close")).toHaveText(/Close/i);
		await expect(page.getByTestId("kt-cl-breadcrumb-current")).toHaveText(/Review & Approval/i);

		// Bento: summary left of sections.
		const layout = page.getByTestId("kt-cl-wf02-layout");
		const summaryBox = await layout.getByTestId("kt-cl-wf02-summary").boundingBox();
		const sectionsBox = await layout.getByTestId("kt-cl-wf02-sections").boundingBox();
		expect(summaryBox && sectionsBox).toBeTruthy();
		if (summaryBox && sectionsBox) {
			expect(summaryBox.x).toBeLessThan(sectionsBox.x);
		}

		const body = await page.locator(ROOT).innerText();
		for (const re of FORBIDDEN) {
			expect(body, String(re)).not.toMatch(re);
		}
	});

	test("reviewer checklist has ten items", async ({ page }) => {
		await openReview(page);
		const checks = page.locator('[data-testid^="kt-cl-wf02-checkbox-"]');
		await expect(checks).toHaveCount(10);
	});

	test("checking a checklist item preserves scroll position", async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 560 });
		await openReview(page);
		const checkbox = page.locator('[data-testid^="kt-cl-wf02-checkbox-"]').nth(4);
		await checkbox.evaluate((el) => {
			el.setAttribute("data-scroll-probe", "1");
			(window as unknown as { __wf02Probe?: Element }).__wf02Probe = el;
		});
		const scrollBefore = await page.evaluate(() => {
			const scroller = document.querySelector(".main-section") as HTMLElement | null;
			const checklist = document.querySelector(
				'[data-testid="kt-cl-wf02-checklist"]',
			) as HTMLElement | null;
			if (scroller && checklist) {
				const top =
					checklist.getBoundingClientRect().top -
					scroller.getBoundingClientRect().top +
					scroller.scrollTop;
				scroller.scrollTop = Math.max(80, top - 16);
				return scroller.scrollTop;
			}
			return 0;
		});
		expect(scrollBefore).toBeGreaterThan(0);
		const wasChecked = await checkbox.isChecked();
		await checkbox.click();
		await expect(checkbox).toBeChecked({ checked: !wasChecked });
		await page.waitForTimeout(800);
		const after = await page.evaluate(() => {
			const scroller = document.querySelector(".main-section") as HTMLElement | null;
			const el = document.querySelector("[data-scroll-probe='1']");
			return {
				scrollTop: scroller ? scroller.scrollTop : 0,
				sameNode: !!(el && el === (window as unknown as { __wf02Probe?: Element }).__wf02Probe),
			};
		});
		expect(Math.abs(after.scrollTop - scrollBefore)).toBeLessThan(48);
		expect(after.sameNode).toBe(true);
	});

	test("Return stays disabled until a Correction Required finding exists", async ({ page }) => {
		await openReview(page);
		const returnBtn = page.getByTestId("kt-cl-wf02-return");
		await expect(returnBtn).toBeVisible();
		await expect(returnBtn).toBeDisabled();
		await expect(returnBtn).toHaveText(/Return for Correction/i);

		await page.getByTestId("kt-cl-wf02-add-finding").click();
		await expect(page.getByTestId("kt-cl-wf02-finding-drawer")).toBeVisible();
		await page.getByTestId("kt-cl-wf02-finding-section").selectOption({ index: 1 });
		await page.getByTestId("kt-cl-wf02-finding-title").fill("Scope summary incomplete");
		await page.getByTestId("kt-cl-wf02-finding-action").fill("Expand the short scope summary.");
		await page.getByTestId("kt-cl-wf02-finding-save").click();
		await expect(page.getByTestId("kt-cl-wf02-finding-drawer")).toHaveCount(0);
		await expect(returnBtn).toBeEnabled({ timeout: 10_000 });
	});

	test("Return confirm modal lists findings and does not re-ask for reason", async ({ page }) => {
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await seedUi00(page);
		await loginAsAdministrator(page);
		await openReview(page);
		await page.getByTestId("kt-cl-wf02-add-finding").click();
		await page.getByTestId("kt-cl-wf02-finding-section").selectOption({ index: 1 });
		await page.getByTestId("kt-cl-wf02-finding-title").fill("Confirm-return finding");
		await page.getByTestId("kt-cl-wf02-finding-action").fill("Fix before resubmit.");
		await page.getByTestId("kt-cl-wf02-finding-save").click();
		await expect(page.getByTestId("kt-cl-wf02-return")).toBeEnabled({ timeout: 10_000 });

		await page.getByTestId("kt-cl-wf02-return").click();
		await expect(page.getByTestId("kt-cl-wf02-return-modal")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf02-return-confirm-body")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf02-return-count")).toContainText(/Correction Required finding/i);
		await expect(page.getByTestId("kt-cl-wf02-return-finding-list")).toContainText(/Confirm-return finding/i);
		await expect(page.getByTestId("kt-cl-wf02-return-section")).toHaveCount(0);
		await expect(page.getByTestId("kt-cl-wf02-return-reason")).toHaveCount(0);
		await page.getByTestId("kt-cl-wf02-return-cancel").click();
		await expect(page.getByTestId("kt-cl-wf02-return-modal")).toHaveCount(0);
	});

	test("add finding drawer saves a finding card", async ({ page }) => {
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await seedUi00(page);
		await loginAsAdministrator(page);
		await openReview(page);
		await page.getByTestId("kt-cl-wf02-add-finding").click();
		await expect(page.getByTestId("kt-cl-wf02-finding-drawer")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf02-finding-drawer-panel")).toBeVisible();

		// Fields must stack vertically (label above control), not Desk side-by-side.
		const stacked = await page.evaluate(() => {
			const control = document.querySelector(
				'[data-testid="kt-cl-wf02-finding-title"]',
			) as HTMLElement | null;
			const field = control?.closest(".kt-cl-wf02-field") as HTMLElement | null;
			const label = field?.querySelector("label") as HTMLElement | null;
			if (!field || !label || !control) {
				return null;
			}
			const fs = getComputedStyle(field);
			return {
				flexDir: fs.flexDirection,
				labelY: label.getBoundingClientRect().top,
				controlY: control.getBoundingClientRect().top,
				hostExists: !!document.getElementById("kt-cl-wf02-modal-host"),
			};
		});
		expect(stacked, "finding title field should be present").toBeTruthy();
		expect(stacked?.flexDir).toBe("column");
		expect((stacked?.controlY || 0) - (stacked?.labelY || 0)).toBeGreaterThan(8);

		await page.getByTestId("kt-cl-wf02-finding-section").selectOption({ index: 1 });
		await page.getByTestId("kt-cl-wf02-finding-title").fill("Align certification language");
		await page.getByTestId("kt-cl-wf02-finding-action").fill("Clarify ISO 27001 mandatory vs preferred.");
		await page.getByTestId("kt-cl-wf02-finding-save").click();
		await expect(page.getByTestId("kt-cl-wf02-finding-drawer")).toHaveCount(0);
		await expect(page.getByTestId("kt-cl-wf02-findings")).toContainText(/Align certification language/i, {
			timeout: 10_000,
		});
	});

	test("approve modal validates checkbox inline without Frappe msgprint", async ({ page }) => {
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await seedUi00(page);
		await loginAsAdministrator(page);
		// Clear findings + complete checklist so Approve is enabled.
		await page.evaluate(async (id) => {
			// @ts-expect-error frappe on desk
			const review = await frappe.call({
				method: "kentender_procurement.tender_configurations.get_tender_configuration_review",
				args: { configuration_id: id },
			});
			const checklist = ((review.message || review).checklist || []).map(function (item) {
				return { id: item.id, label: item.label, checked: 1 };
			});
			// @ts-expect-error frappe on desk
			await frappe.call({
				method: "kentender_procurement.tender_configurations.save_tender_configuration_review",
				args: { configuration_id: id, payload: { checklist: checklist, findings: [] } },
			});
		}, REVIEW_CONFIG);

		await openReview(page);
		await expect(page.getByTestId("kt-cl-wf02-approve")).toBeEnabled({ timeout: 10_000 });
		await page.getByTestId("kt-cl-wf02-approve").click();
		await expect(page.getByTestId("kt-cl-wf02-approve-modal")).toBeVisible();
		await page.getByTestId("kt-cl-wf02-approve-confirm-btn").click();
		await expect(page.getByTestId("kt-cl-wf02-approve-confirm-error")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf02-approve-confirm-error")).toContainText(
			/Confirm the approval statement/i
		);
		// No stacked Frappe Message dialog.
		await expect(page.locator(".msgprint, .modal-title:has-text('Message')")).toHaveCount(0);
		await expect(page.getByTestId("kt-cl-wf02-approve-modal")).toBeVisible();
	});

	test("approve flow routes to document preview when checklist complete", async ({ page }) => {
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await page.evaluate(async (id) => {
			// @ts-expect-error frappe on desk
			const review = await frappe.call({
				method: "kentender_procurement.tender_configurations.get_tender_configuration_review",
				args: { configuration_id: id },
			});
			const checklist = ((review.message || review).checklist || []).map(function (item) {
				return { id: item.id, label: item.label, checked: 1 };
			});
			// @ts-expect-error frappe on desk
			await frappe.call({
				method: "kentender_procurement.tender_configurations.save_tender_configuration_review",
				args: { configuration_id: id, payload: { checklist: checklist, findings: [] } },
			});
			// @ts-expect-error frappe on desk
			await frappe.call({
				method: "kentender_procurement.tender_configurations.approve_tender_configuration_for_preview",
				args: { configuration_id: id, payload: { confirm_preview_only: 1 } },
			});
		}, REVIEW_CONFIG);
		await page.goto(`/desk/it-tender-configuration-render-preview/${encodeURIComponent(REVIEW_CONFIG)}`);
		await expect(page.getByTestId("kt-cl-wf03-root")).toBeVisible({ timeout: 30_000 });
		await expect(page).toHaveURL(/it-tender-configuration-render-preview/, { timeout: 15_000 });
	});
});
