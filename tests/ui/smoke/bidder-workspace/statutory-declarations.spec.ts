import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * Statutory Declarations — Review & Certify (Stitch 01–04).
 * Route: /tenders/<publication_ref>/sections/statutory_declarations
 */

function extractPublicationRef(url: string): string | null {
	const m = url.match(/\/tenders\/([^/?#]+)/);
	return m?.[1] || null;
}

test.describe("Statutory Declarations portal", () => {
	test("opens Statutory Declarations shell, footer chrome, certify/cancel or certified hover", async ({
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

		const link = page.locator(`a[href*="/sections/statutory_declarations"]`).first();
		if ((await link.count()) > 0) {
			await link.click();
		} else {
			await page.goto(`/tenders/${ref}/sections/statutory_declarations`, {
				waitUntil: "domcontentloaded",
			});
		}

		await expect(page.getByTestId("kt-stat-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-stat-crumbs")).toBeVisible();
		await expect(page.getByTestId("kt-stat-declarant")).toBeVisible();
		await expect(page.getByTestId("kt-stat-footer")).toBeVisible();
		const footerPos = await page.evaluate(() => {
			const el = document.querySelector('[data-testid="kt-stat-footer"]') as HTMLElement | null;
			if (!el) return null;
			return window.getComputedStyle(el).position;
		});
		expect(footerPos).toBe("fixed");
		await expect(page.locator('[name="witness_name"]')).toHaveCount(0);
		await expect(page.locator('[name="declarant_name"]')).toHaveCount(0);

		const certified =
			(await page.getByTestId("kt-stat-root").getAttribute("data-certified")) === "1" ||
			(await page.getByTestId("kt-stat-return-checklist").count()) > 0;

		if (certified) {
			await expect(page.getByTestId("kt-stat-cert-record")).toBeVisible();
			const returnBtn = page.getByTestId("kt-stat-return-checklist");
			await expect(returnBtn).toBeVisible();
			await returnBtn.hover();
			const hover = await returnBtn.evaluate((el) => {
				const cs = getComputedStyle(el);
				return { bg: cs.backgroundColor, color: cs.color };
			});
			expect(hover.bg).toMatch(/rgb\(\s*0,\s*0,\s*0\s*\)/);
			expect(hover.color).toMatch(/rgb\(\s*255,\s*255,\s*255\s*\)/);
			return;
		}

		await expect(page.getByTestId("kt-stat-independent-choice")).toBeVisible();
		const independent = page.locator(
			'input[name="independent_tender_choice"][value="independent"]'
		);
		const disclosed = page.locator(
			'input[name="independent_tender_choice"][value="disclosed"]'
		);
		await expect(independent).toBeAttached();
		await expect(disclosed).toBeAttached();
		const indChecked = await independent.isChecked().catch(() => false);
		const discChecked = await disclosed.isChecked().catch(() => false);
		if (!indChecked && !discChecked) {
			await expect(independent).not.toBeChecked();
			await expect(disclosed).not.toBeChecked();
		}

		await expect(page.getByTestId("kt-stat-certify-dialog")).toBeAttached();
		await expect(page.getByTestId("kt-stat-certify-dialog")).toBeHidden();
		await expect(page.getByTestId("kt-stat-certify-dialog")).toContainText(
			"Certify Statutory Declarations?"
		);

		const prereqsMet = await page.getByTestId("kt-stat-root").getAttribute("data-prereqs-met");
		if (prereqsMet !== "1") {
			// CBQ/declarant incomplete — Certify correctly stays gated.
			await expect(page.getByTestId("kt-stat-certify")).toBeDisabled();
			return;
		}

		const certify = page.getByTestId("kt-stat-certify");
		// Selecting the independent answer must enable Certify without Save draft.
		if (!(await independent.isChecked())) {
			await expect(certify).toBeDisabled();
			await independent.check({ force: true });
		}
		await expect(certify).toBeEnabled({ timeout: 5_000 });
		await expect(page.getByTestId("kt-stat-status-chip")).toHaveText(/Ready to certify/i);
		await expect(page.getByTestId("kt-stat-root")).toHaveAttribute("data-can-certify", "1");

		// Save draft then Certify must not show Updated elsewhere / KT_STAT_CONFLICT.
		const tokenBeforeSave = await page
			.getByTestId("kt-stat-root")
			.getAttribute("data-bid-modified");
		await page.getByTestId("kt-stat-save").click();
		await expect
			.poll(async () => page.getByTestId("kt-stat-root").getAttribute("data-bid-modified"), {
				timeout: 15_000,
			})
			.not.toBe(tokenBeforeSave);
		await expect(certify).toBeEnabled();
		await expect(page.getByRole("heading", { name: "KT_STAT_CONFLICT" })).toHaveCount(0);
		await expect(page.getByRole("heading", { name: "Updated elsewhere" })).toHaveCount(0);

		// Certify → Cancel → Certify again must not throw conflict.
		const tokenBefore = await page.getByTestId("kt-stat-root").getAttribute("data-bid-modified");
		await certify.click();
		await expect(page.getByTestId("kt-stat-certify-dialog")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByRole("heading", { name: "KT_STAT_CONFLICT" })).toHaveCount(0);
		await expect(page.getByRole("heading", { name: "Updated elsewhere" })).toHaveCount(0);
		const tokenAfterOpen = await page
			.getByTestId("kt-stat-root")
			.getAttribute("data-bid-modified");
		expect(tokenAfterOpen).toBeTruthy();
		if (tokenBefore) {
			expect(tokenAfterOpen).not.toBe(tokenBefore);
		}
		await page.getByTestId("kt-stat-certify-cancel").click();
		await expect(page.getByTestId("kt-stat-certify-dialog")).toBeHidden();
		await certify.click();
		await expect(page.getByTestId("kt-stat-certify-dialog")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByRole("heading", { name: "KT_STAT_CONFLICT" })).toHaveCount(0);
		await page.getByTestId("kt-stat-certify-cancel").click();
	});
});
