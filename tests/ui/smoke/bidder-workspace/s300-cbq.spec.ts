import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * S300 Confidential Business Questionnaire — Stitch 5-step wizard.
 * Route: /tenders/<publication_ref>/sections/confidential_business_questionnaire
 *
 * IMPORTANT: This smoke hits shared demo bids. Never persist blanked required
 * step-1 fields — probe incompleteness in the DOM only, then restore before any save/continue.
 */

function extractPublicationRef(url: string): string | null {
	const m = url.match(/\/tenders\/([^/?#]+)/);
	return m?.[1] || null;
}

test.describe("S300 CBQ portal", () => {
	test("opens CBQ wizard, shows stepper, save draft, continue to step 2", async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);

		await page.goto("/tenders", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-a0-tenders-root")).toBeVisible({ timeout: 30_000 });

		const secondaryContinue = page
			.getByTestId("kt-a0-secondary-action")
			.filter({ hasText: "Continue Bid" })
			.first();
		const viewTender = page
			.getByTestId("kt-a0-primary-action")
			.filter({ hasText: "View Tender" })
			.first();

		let ref: string | null = null;
		if ((await secondaryContinue.count()) > 0) {
			const href = await secondaryContinue.getAttribute("href");
			ref = href ? extractPublicationRef(href) : null;
		} else if ((await viewTender.count()) > 0) {
			const href = await viewTender.getAttribute("href");
			ref = href ? extractPublicationRef(href) : null;
		}
		test.skip(!ref, "No tender cards on /tenders — seed a published open tender");

		await page.goto(`/tenders/${ref}/workspace`, { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-a2-checklist-root")).toBeVisible({ timeout: 30_000 });

		const cbqLink = page
			.locator(`a[href*="/sections/confidential_business_questionnaire"]`)
			.first();
		if ((await cbqLink.count()) > 0) {
			await cbqLink.click();
		} else {
			await page.goto(
				`/tenders/${ref}/sections/confidential_business_questionnaire`,
				{ waitUntil: "domcontentloaded" }
			);
		}

		await expect(page.getByTestId("kt-s300-cbq-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-s300-stepper")).toBeVisible();
		await expect(page.getByTestId("kt-s300-step-1")).toBeVisible();
		await expect(page.getByTestId("kt-s300-save-draft")).toBeVisible();
		await expect(page.getByTestId("kt-a2-sidebar")).toBeVisible();
		await expect(page.getByTestId("kt-s300-tender-aside")).toBeVisible();
		// Stitch footer: viewport-fixed, full width of main canvas (not inset card).
		const footerBox = await page.evaluate(() => {
			const el = document.querySelector('[data-testid="kt-s300-footer"]') as HTMLElement | null;
			if (!el) return null;
			const cs = getComputedStyle(el);
			const r = el.getBoundingClientRect();
			return {
				position: cs.position,
				bottom: Math.round(r.bottom),
				left: Math.round(r.left),
				right: Math.round(r.right),
				vh: window.innerHeight,
				vw: window.innerWidth,
			};
		});
		expect(footerBox).toBeTruthy();
		expect(footerBox!.position).toBe("fixed");
		expect(Math.abs(footerBox!.bottom - footerBox!.vh)).toBeLessThanOrEqual(2);
		expect(Math.abs(footerBox!.right - footerBox!.vw)).toBeLessThanOrEqual(2);
		expect(footerBox!.left).toBeGreaterThanOrEqual(250);
		expect(footerBox!.left).toBeLessThanOrEqual(270);
		await expect(page.getByTestId("kt-s300-tender-info")).toContainText("Tender Details");
		await expect(page.locator('[data-testid="kt-s300-verified-profile"]')).toHaveCount(0);
		await expect(page.locator('script[src*="cdn.tailwindcss.com"]')).toHaveCount(0);
		await expect(page.locator(".kt-s300-entity-tabs.is-visible")).toHaveCount(0);
		// Custom page toast host must not exist — Frappe show_alert only.
		await expect(page.locator('[data-testid="kt-s300-toast"]')).toHaveCount(0);
		// Certification: dialog owns certifier fields; form has review + certified record only.
		await expect(page.getByTestId("kt-s300-certify-dialog")).toBeAttached();
		await expect(page.getByTestId("kt-s300-certify-dialog")).toBeHidden();
		await expect(page.getByTestId("kt-s300-certify-dialog")).toContainText(
			"Certify this questionnaire?"
		);
		await expect(page.getByTestId("kt-s300-certify-dialog-fields")).toBeAttached();
		await expect(
			page.getByTestId("kt-s300-certify-dialog").locator('[data-cert="certifier_name"]')
		).toHaveCount(1);
		await expect(
			page.getByTestId("kt-s300-step-5").locator('[data-cert="certifier_name"]')
		).toHaveCount(0);
		await expect(page.locator('[data-testid="kt-s300-cert-form"]')).toHaveCount(0);
		await expect(page.getByTestId("kt-s300-step-5")).toContainText("Submission Review");
		await expect(page.getByTestId("kt-s300-step5-tender-meta")).toBeAttached();
		await expect(page.getByTestId("kt-s300-review-card")).toBeAttached();
		await expect(page.locator(".kt-s300-step-connector")).toHaveCount(4);
		await expect(page.getByTestId("kt-s300-cert-record")).toBeAttached();
		await expect(page.getByTestId("kt-s300-cert-record")).toBeHidden();
		await expect(page.getByTestId("kt-s300-cert-record")).toContainText("Questionnaire certified");
		await expect(page.getByTestId("kt-s300-amend")).toBeAttached();
		await expect(page.getByTestId("kt-s300-amend-dialog")).toBeAttached();
		await expect(page.getByTestId("kt-s300-amend-dialog")).toBeHidden();
		await expect(page.getByTestId("kt-s300-amend-dialog")).toContainText(
			"Amend this questionnaire?"
		);
		await expect(page.getByTestId("kt-s300-return-checklist")).toBeAttached();
		await expect(page.locator('[data-testid="kt-s300-cert-done"]')).toHaveCount(0);
		await expect(page.locator("body")).not.toContainText("Questionnaire complete —");

		const noHorizontalOverflow = await page.evaluate(() => {
			const root = document.documentElement;
			return root.scrollWidth <= root.clientWidth + 1;
		});
		expect(noHorizontalOverflow).toBeTruthy();

		const legal = page.locator('[data-field="legal_name"]');
		const country = page.locator('[data-answer="country"]');
		const contactPerson = page.locator('[data-answer="contact_person"]');
		const contactEmail = page.locator('[data-answer="contact_email"]');

		const snap = {
			legal_name: await legal.inputValue(),
			country: await country.inputValue(),
			contact_person: await contactPerson.inputValue(),
			contact_email: await contactEmail.inputValue(),
		};

		await page.getByTestId("kt-s300-save-draft").click();
		const frappeToast = page.locator("#alert-container .desk-alert.green .alert-message");
		await expect(frappeToast).toBeVisible({ timeout: 15_000 });
		await expect(frappeToast).toContainText("Draft saved");

		// Probe incomplete stepper in the DOM only — do not Save/Continue while blanked
		// (that previously wiped shared demo drafts: country / contact person / email).
		await legal.fill("");
		await country.selectOption({ value: "" });
		await contactPerson.fill("");
		await contactEmail.fill("");
		const probe = await page.evaluate(() => {
			const root = document.querySelector('[data-testid="kt-s300-cbq-root"]') as HTMLElement & {
				__ktS300ProbeIncompleteStep1?: () => boolean;
			};
			if (root && typeof root.__ktS300ProbeIncompleteStep1 === "function") {
				return root.__ktS300ProbeIncompleteStep1();
			}
			const filled = (sel: string) => {
				const el = document.querySelector(sel) as HTMLInputElement | HTMLSelectElement | null;
				return !!(el && String(el.value || "").trim());
			};
			return !(
				filled('[data-field="legal_name"]') &&
				filled('[data-answer="country"]') &&
				filled('[data-answer="contact_person"]') &&
				filled('[data-answer="contact_email"]')
			);
		});
		expect(probe).toBeTruthy();

		// Restore DOM before any navigation/save that would persist blanks.
		await legal.fill(snap.legal_name);
		if (snap.country) {
			await country.selectOption({ value: snap.country });
		} else {
			await country.selectOption({ value: "" });
		}
		await contactPerson.fill(snap.contact_person);
		await contactEmail.fill(snap.contact_email);

		await page.getByTestId("kt-s300-continue").click();
		await expect(page.getByTestId("kt-s300-step-2")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("kt-s300-crumb-step")).toContainText("Business Details");
		await expect(page.getByTestId("kt-s300-tender-aside")).toBeVisible();
		await expect(page).toHaveURL(/[?&]step=2\b/);
		// Step change clears Frappe toasts (not a sticky banner).
		await expect(page.locator("#alert-container .desk-alert")).toHaveCount(0, {
			timeout: 5_000,
		});

		// After continue with restored values: step 1 is complete only if snap had required fields.
		const step1 = page.locator('[data-step-indicator="1"]');
		if (
			snap.legal_name.trim() &&
			snap.country.trim() &&
			snap.contact_person.trim() &&
			snap.contact_email.trim()
		) {
			await expect(step1).toHaveAttribute("data-step-state", "complete");
			await expect(step1).toHaveClass(/is-done/);
		} else {
			await expect(step1).toHaveAttribute("data-step-state", "incomplete");
			await expect(step1).toHaveClass(/is-incomplete/);
			await expect(step1).not.toHaveClass(/is-done/);
		}

		// Completeness is data-driven: a filled later step is green before the user opens it.
		await page.goto(
			`/tenders/${ref}/sections/confidential_business_questionnaire?step=3`,
			{ waitUntil: "domcontentloaded" }
		);
		await expect(page.getByTestId("kt-s300-step-3")).toBeVisible({ timeout: 30_000 });
		const step4AlreadyComplete = await page.evaluate(() => {
			const root = document.querySelector('[data-testid="kt-s300-cbq-root"]');
			if (!root) return false;
			const pe = root.querySelector('input[name="pe_interest"]:checked') as HTMLInputElement | null;
			if (!pe || !pe.value) return false;
			if (pe.value === "yes") {
				const rows = root.querySelectorAll(
					'[data-testid="kt-s300-pe-people-table"] tbody tr input'
				);
				let named = false;
				rows.forEach((el, i) => {
					if (i % 3 === 0 && String((el as HTMLInputElement).value || "").trim()) named = true;
				});
				if (!named) return false;
			}
			const keys = [
				"q1_common_ownership",
				"q2_subsidy_from_tenderer",
				"q3_same_legal_representative",
				"q4_influence_relationship",
				"q5_affiliate_preparing_specs",
				"q6_conflicting_supply_role",
				"q7_relationship_prep_eval_staff",
				"q8_relationship_impl_supervision_staff",
				"q9_conflict_resolved",
			];
			return keys.every((key) => {
				const ans = root.querySelector(
					`input[data-conflict-answer="${key}"]:checked`
				) as HTMLInputElement | null;
				if (!ans) return false;
				if (ans.value === "yes") {
					const det = root.querySelector(
						`[data-conflict-details-input="${key}"]`
					) as HTMLTextAreaElement | null;
					if (!det || !String(det.value || "").trim()) return false;
				}
				return true;
			});
		});
		if (step4AlreadyComplete) {
			const step4 = page.locator('[data-step-indicator="4"]');
			await expect(step4).toHaveAttribute("data-step-state", "complete");
			await expect(step4).toHaveClass(/is-done/);
		}

		// Stepper jump + refresh must stay on the chosen step (not reset to step 1).
		await page.getByTestId("kt-s300-step-btn-4").click();
		await expect(page.getByTestId("kt-s300-step-4")).toBeVisible({ timeout: 15_000 });
		await expect(page).toHaveURL(/[?&]step=4\b/);
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-s300-cbq-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-s300-step-4")).toBeVisible({ timeout: 30_000 });
		await expect(page).toHaveURL(/[?&]step=4\b/);

		// Reload without wiping required fields (shared demo bid).
		await expect(page.locator('[data-field="legal_name"]')).toHaveValue(snap.legal_name, {
			timeout: 15_000,
		});
		await expect(page.locator('[data-answer="contact_person"]')).toHaveValue(snap.contact_person);
		await expect(page.locator('[data-answer="contact_email"]')).toHaveValue(snap.contact_email);

		// step_5_3: Review and Certify chrome + certified layout (probe; no persist).
		await page.goto(
			`/tenders/${ref}/sections/confidential_business_questionnaire?step=5`,
			{ waitUntil: "domcontentloaded" }
		);
		await expect(page.getByTestId("kt-s300-step-5")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-s300-cbq-instructions")).toHaveText("Review and Certify");
		await expect(page.getByTestId("kt-s300-step5-tender-meta")).toBeVisible();
		const alreadyCertified = await page.getByTestId("kt-s300-cert-record").isVisible();
		if (alreadyCertified) {
			await expect(page.getByTestId("kt-s300-review-card")).toBeHidden();
			await expect(page.getByTestId("kt-s300-tender-aside")).toBeHidden();
			await expect(page.locator(".kt-s300-layout")).toHaveClass(/is-certified-view/);
			await expect(page.getByTestId("kt-s300-step-btn-5")).toContainText("Certified");
		} else {
			await expect(page.getByTestId("kt-s300-review-card")).toBeVisible();
			await expect(page.getByTestId("kt-s300-tender-aside")).toBeVisible();
			const probed = await page.evaluate(() => {
				const root = document.querySelector(
					'[data-testid="kt-s300-cbq-root"]'
				) as HTMLElement & {
					__ktS300ProbeStep5CertifiedLayout?: () => Record<string, unknown>;
				};
				if (!root || typeof root.__ktS300ProbeStep5CertifiedLayout !== "function") {
					return null;
				}
				return root.__ktS300ProbeStep5CertifiedLayout();
			});
			expect(probed).toBeTruthy();
			expect(probed).toMatchObject({
				reviewHidden: true,
				asideHidden: true,
				metaVisible: true,
				recordVisible: true,
				layoutCertified: true,
				instructions: "Review and Certify",
				stepLabel: "Certified",
			});
			// Probe restores prior step — return to step 5 for overflow check.
			await page.getByTestId("kt-s300-step-btn-5").click();
			await expect(page.getByTestId("kt-s300-step-5")).toBeVisible({ timeout: 15_000 });
		}

		const stillNoOverflow = await page.evaluate(() => {
			const root = document.documentElement;
			return root.scrollWidth <= root.clientWidth + 1;
		});
		expect(stillNoOverflow).toBeTruthy();
	});
});
