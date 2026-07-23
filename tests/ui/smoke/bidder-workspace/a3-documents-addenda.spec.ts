import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * A3 Tender Documents & Addenda — Website Screen C.
 * Route: /tenders/<publication_ref>/documents
 */

const ROOT = '[data-testid="kt-a0-tenders-root"]';
const CHECKLIST = '[data-testid="kt-a2-checklist-root"]';
const DOCS = '[data-testid="kt-a3-documents-root"]';

function extractPublicationRef(url: string): string | null {
	const m = url.match(/\/tenders\/([^/?#]+)/);
	return m?.[1] || null;
}

test.describe("A3 Tender Documents & Addenda portal", () => {
	test("documents page loads from Prepare Bid; empty addenda; acknowledge enables continue", async ({
		page,
	}) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);

		await page.goto("/tenders", { waitUntil: "domcontentloaded" });
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });

		const workspaceCta = page
			.getByTestId("kt-a0-primary-action")
			.filter({ hasText: /Continue Bid|View Submitted Bid/ })
			.first();
		const viewTender = page
			.getByTestId("kt-a0-primary-action")
			.filter({ hasText: "View Tender" })
			.first();

		let ref: string | null = null;
		if ((await workspaceCta.count()) > 0) {
			const href = await workspaceCta.getAttribute("href");
			ref = href ? extractPublicationRef(href) : null;
			await page.goto(`/tenders/${ref}/workspace`, { waitUntil: "domcontentloaded" });
		} else if ((await viewTender.count()) > 0) {
			await viewTender.click();
			await page.waitForURL(/\/tenders\/[^/?#]+/, { timeout: 20_000 });
			ref = extractPublicationRef(page.url());
			await page.goto(`/tenders/${ref}/workspace`, { waitUntil: "domcontentloaded" });
		} else {
			const anyHref = await page
				.getByTestId("kt-a0-primary-action")
				.first()
				.getAttribute("href")
				.catch(() => null);
			ref = anyHref ? extractPublicationRef(anyHref) : null;
			test.skip(!ref, "No tender cards on /tenders — seed a published open tender");
			await page.goto(`/tenders/${ref}/workspace`, { waitUntil: "domcontentloaded" });
		}

		await expect(page.locator(CHECKLIST)).toBeVisible({ timeout: 30_000 });
		const prepare = page.getByTestId("kt-a2-nav-prepare");
		await expect(prepare).toBeVisible();
		await expect(prepare).toHaveAttribute("href", /\/tenders\/[^/?#]+\/documents/);
		await prepare.click();
		await page.waitForURL(/\/tenders\/[^/?#]+\/documents/, { timeout: 30_000 });

		expect(page.url()).not.toMatch(/\/desk\/|it-electronic-bidder-workspace/);
		await expect(page.locator(DOCS)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-a3-title")).toContainText("Tender Documents & Addenda");
		await expect(page.getByTestId("kt-a3-official-documents")).toBeVisible();
		await expect(page.getByTestId("kt-a3-official-addenda")).toBeVisible();
		await expect(page.getByTestId("kt-a3-addenda-empty")).toContainText(
			"No official addenda have been issued for this tender."
		);
		await expect(page.getByTestId("kt-a3-readiness-addenda")).toContainText("No addenda issued");
		await expect(page.getByTestId("kt-a3-back-checklist")).toBeVisible();

		const countdown = page.getByTestId("kt-a3-readiness-time");
		await expect(countdown).toHaveAttribute("data-kt-countdown", "");
		await expect(countdown).toHaveAttribute("data-deadline", /.+/);
		const before = (await countdown.innerText()).trim();
		await expect
			.poll(async () => (await countdown.innerText()).trim(), { timeout: 2500 })
			.not.toBe(before);

		const ack = page.getByTestId("kt-a3-acknowledge");
		if ((await ack.count()) > 0) {
			await ack.click();
			await expect(page.getByTestId("kt-a3-continue")).toBeVisible({ timeout: 30_000 });
			await expect(page.getByTestId("kt-a3-ack-status")).toContainText("Complete");
		} else {
			// Already acknowledged on this bid — continue (or disabled if sealed) still proves chrome.
			await expect(
				page.getByTestId("kt-a3-continue").or(page.getByTestId("kt-a3-continue-disabled"))
			).toBeVisible();
		}

		const body = await page.locator("body").innerText();
		expect(body).not.toMatch(/Tender Management|Tender Configurations|Evaluation and Award/i);
		await expect(page.locator("nav.navbar")).toBeHidden();
	});
});
