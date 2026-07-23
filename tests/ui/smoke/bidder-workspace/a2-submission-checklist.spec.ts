import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * A2 Submission Checklist — Website workspace home.
 * Route: /tenders/<publication_ref>/workspace
 *
 * Logged-in users often see Continue Bid / View Submitted Bid (→ workspace)
 * instead of View Tender (→ overview). Prefer those; fall back to overview → workspace.
 */

const ROOT = '[data-testid="kt-a0-tenders-root"]';
const OVERVIEW = '[data-testid="kt-a1w-overview-root"]';
const CHECKLIST = '[data-testid="kt-a2-checklist-root"]';

function extractPublicationRef(url: string): string | null {
	const m = url.match(/\/tenders\/([^/?#]+)/);
	return m?.[1] || null;
}

test.describe("A2 Submission Checklist portal", () => {
	test("workspace checklist loads on Website with sidebar (no Desk Procurement rail)", async ({
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

		if ((await workspaceCta.count()) > 0) {
			await workspaceCta.click();
			await page.waitForURL(/\/tenders\/[^/?#]+\/workspace/, { timeout: 30_000 });
		} else if ((await viewTender.count()) > 0) {
			await viewTender.click();
			await page.waitForURL(/\/tenders\/[^/?#]+/, { timeout: 20_000 });
			await expect(page.locator(OVERVIEW)).toBeVisible({ timeout: 30_000 });
			const ref = extractPublicationRef(page.url());
			expect(ref).toBeTruthy();

			const startBid = page.getByTestId("kt-a1w-primary-cta");
			const label = (await startBid.getAttribute("data-action-label")) || "";
			if (["Start Bid", "Continue Bid"].includes(label)) {
				await startBid.click();
				await page.waitForURL(/\/tenders\/[^/?#]+\/workspace/, { timeout: 30_000 });
			} else {
				await page.goto(`/tenders/${ref}/workspace`, { waitUntil: "domcontentloaded" });
			}
		} else {
			// Last resort: any card href with a publication ref.
			const anyHref = await page
				.getByTestId("kt-a0-primary-action")
				.first()
				.getAttribute("href")
				.catch(() => null);
			const ref = anyHref ? extractPublicationRef(anyHref) : null;
			test.skip(!ref, "No tender cards on /tenders — seed a published open tender");
			await page.goto(`/tenders/${ref}/workspace`, { waitUntil: "domcontentloaded" });
		}

		expect(page.url()).toMatch(/\/tenders\/[^/?#]+\/workspace/);
		expect(page.url()).not.toMatch(/\/desk\/|it-electronic-bidder-workspace/);

		await expect(page.locator(CHECKLIST)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-a2-title")).toContainText("Submission Checklist");
		await expect(page.getByTestId("kt-a2-sidebar")).toBeVisible();
		await expect(page.getByTestId("kt-a2-nav-checklist")).toBeVisible();
		await expect(page.getByTestId("kt-a2-section-checklist")).toBeVisible();
		await expect(page.getByTestId("kt-a2-section-row").first()).toBeVisible();
		await expect(page.getByTestId("kt-a2-primary-cta")).toBeVisible();

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
	});
});
