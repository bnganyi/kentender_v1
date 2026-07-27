import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * Tender Security — instrument or Tender-Securing Declaration.
 * Route: /tenders/<publication_ref>/sections/tender_security
 */

function extractPublicationRef(url: string): string | null {
	const m = url.match(/\/tenders\/([^/?#]+)/);
	return m?.[1] || null;
}

test.describe("Tender Security portal", () => {
	test("opens Tender Security shell with mode-specific chrome", async ({ page }) => {
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

		const link = page.locator(`a[href*="/sections/tender_security"]`).first();
		if ((await link.count()) === 0) {
			test.skip(true, "Tender Security not applicable on seeded tender (mode none)");
		}
		await link.click();

		await expect(page.getByTestId("kt-sec-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-sec-crumbs")).toBeVisible();
		await expect(page.getByTestId("kt-sec-footer")).toBeVisible();
		const footerPos = await page.evaluate(() => {
			const el = document.querySelector('[data-testid="kt-sec-footer"]') as HTMLElement | null;
			if (!el) return null;
			return window.getComputedStyle(el).position;
		});
		expect(footerPos).toBe("fixed");

		await expect(page.getByText("Verified", { exact: true })).toHaveCount(0);
		await expect(page.getByText("Approved", { exact: true })).toHaveCount(0);

		const mode = await page.getByTestId("kt-sec-root").getAttribute("data-mode");
		if (mode === "instrument") {
			await expect(page.getByTestId("kt-sec-requirements")).toBeVisible();
			await expect(page.getByTestId("kt-sec-req-amount")).toBeVisible();
			await expect(page.getByTestId("kt-sec-instrument-form")).toBeVisible();
			await expect(page.getByTestId("kt-sec-save")).toBeVisible();
			await expect(page.getByTestId("kt-sec-save-continue")).toBeVisible();
			await expect(page.getByTestId("kt-sec-pe-note")).toBeVisible();
			await expect(page.getByTestId("kt-sec-issuer-country")).toBeVisible();
			const currency = page.getByTestId("kt-sec-currency");
			await expect(currency).toBeVisible();
			// Single permitted/required currency must be read-only input (no empty Select).
			await expect(currency).toHaveJSProperty("tagName", "INPUT");
			await expect(currency).toHaveAttribute("readonly", "");
			await expect(currency).not.toHaveValue("");
			const amountText = (await page.getByTestId("kt-sec-req-amount").textContent()) || "";
			expect(amountText).toMatch(/[A-Z]{3}/);
			await expect(page.getByTestId("kt-sec-routes")).toBeVisible();
			await expect(page.getByText("Verified", { exact: true })).toHaveCount(0);
			await expect(page.getByText("Approved", { exact: true })).toHaveCount(0);

			// Upload chip must appear immediately after attach — not only after Save Draft.
			await page.getByTestId("kt-sec-route-upload").check();
			await expect(page.getByTestId("kt-sec-upload-block")).toBeVisible();
			const chip = page.getByTestId("kt-sec-upload-name");
			await page.getByTestId("kt-sec-file").setInputFiles({
				name: "tender-security-immediate.txt",
				mimeType: "text/plain",
				buffer: Buffer.from("tender security upload chip regression"),
			});
			await expect(chip).toBeVisible({ timeout: 15_000 });
			await expect(chip).toContainText("tender-security-immediate.txt");
			const urlVal = await page.getByTestId("kt-sec-upload-url").inputValue();
			expect(urlVal.length).toBeGreaterThan(0);
		} else if (mode === "securing_declaration") {
			await expect(page.getByTestId("kt-sec-declaration-summary")).toBeVisible();
			await expect(page.getByTestId("kt-sec-triggers")).toBeVisible();
			await expect(page.getByTestId("kt-sec-signatory")).toBeVisible();
			await expect(page.getByTestId("kt-sec-read-full")).toBeVisible();
			await page.getByTestId("kt-sec-read-full").click();
			await expect(page.getByTestId("kt-sec-terms-drawer")).toBeVisible();
			await page.getByTestId("kt-sec-terms-close").click();

			const certified =
				(await page.getByTestId("kt-sec-root").getAttribute("data-certified")) === "1";
			if (!certified) {
				await expect(page.getByTestId("kt-sec-certify")).toBeVisible();
			} else {
				await expect(page.getByTestId("kt-sec-cert-record")).toBeVisible();
			}
		} else {
			throw new Error(`Unexpected tender security mode: ${mode}`);
		}
	});
});
