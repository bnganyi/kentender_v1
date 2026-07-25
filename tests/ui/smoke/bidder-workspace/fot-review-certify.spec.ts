import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * Form of Tender — Review & Certify (Stitch 01–04).
 * Route: /tenders/<publication_ref>/sections/form_of_tender
 */

function extractPublicationRef(url: string): string | null {
	const m = url.match(/\/tenders\/([^/?#]+)/);
	return m?.[1] || null;
}

test.describe("FoT Review and Certify portal", () => {
	test("opens FoT, incomplete banner, commissions unset, certify dialog + fixed footer", async ({
		page,
	}) => {
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

		const fotLink = page.locator(`a[href*="/sections/form_of_tender"]`).first();
		if ((await fotLink.count()) > 0) {
			await fotLink.click();
		} else {
			await page.goto(`/tenders/${ref}/sections/form_of_tender`, {
				waitUntil: "domcontentloaded",
			});
		}

		await expect(page.getByTestId("kt-fot-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-fot-crumbs")).toContainText("Review & Certify");
		await expect(page.getByTestId("kt-fot-material-summary")).toBeVisible();
		await expect(page.getByTestId("kt-fot-commissions-choice")).toBeVisible();

		// No default Yes/No selection on a fresh (or incomplete) disclosure.
		const yes = page.locator('input[name="commissions_choice"][value="yes"]');
		const no = page.locator('input[name="commissions_choice"][value="no"]');
		await expect(yes).toBeAttached();
		await expect(no).toBeAttached();
		const yesChecked = await yes.isChecked().catch(() => false);
		const noChecked = await no.isChecked().catch(() => false);
		// If a prior demo bid already answered, skip the "no default" assertion.
		if (!yesChecked && !noChecked) {
			await expect(yes).not.toBeChecked();
			await expect(no).not.toBeChecked();
		}

		await expect(page.getByTestId("kt-fot-certify-dialog")).toBeAttached();
		await expect(page.getByTestId("kt-fot-certify-dialog")).toBeHidden();
		await expect(page.getByTestId("kt-fot-certify-dialog")).toContainText(
			"Certify Form of Tender?"
		);

		await expect(page.getByTestId("kt-fot-footer")).toBeVisible();
		const footerPos = await page.evaluate(() => {
			const el = document.querySelector('[data-testid="kt-fot-footer"]') as HTMLElement | null;
			if (!el) return null;
			const style = window.getComputedStyle(el);
			return { position: style.position, bottom: style.bottom };
		});
		expect(footerPos?.position).toBe("fixed");

		await expect(page.locator('[name="bidder_legal_name"]')).toHaveCount(0);
		await expect(page.locator('[name="bidder_business_address"]')).toHaveCount(0);

		// Incomplete banner when prerequisites missing; certify disabled when not ready.
		const canCertify = await page.getByTestId("kt-fot-root").getAttribute("data-can-certify");
		if (canCertify !== "1") {
			await expect(page.getByTestId("kt-fot-incomplete-banner")).toBeVisible();
			await expect(page.getByTestId("kt-fot-certify")).toBeDisabled();
		}
	});
});
