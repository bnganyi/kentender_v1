import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * Preliminary Requirements and Evidence — two-group checklist + response drawer.
 * Route: /tenders/<publication_ref>/sections/preliminary_requirements_and_evidence
 */

function extractPublicationRef(url: string): string | null {
	const m = url.match(/\/tenders\/([^/?#]+)/);
	return m?.[1] || null;
}

test.describe("Preliminary Requirements portal", () => {
	test("opens two-group shell, drawer, Continue footer; no evaluator outcomes", async ({
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

		const link = page
			.locator(`a[href*="/sections/preliminary_requirements_and_evidence"]`)
			.first();
		test.skip((await link.count()) === 0, "Preliminary Requirements not on checklist");
		await link.click();

		await expect(page.getByTestId("kt-prelim-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-prelim-crumbs")).toBeVisible();
		await expect(page.getByTestId("kt-prelim-progress")).toBeVisible();
		await expect(page.getByTestId("kt-prelim-evidence-group")).toBeVisible();
		await expect(page.getByTestId("kt-prelim-linked-group")).toBeVisible();
		await expect(page.getByTestId("kt-prelim-footer")).toBeVisible();
		await expect(page.getByTestId("kt-prelim-continue")).toHaveText(/Continue/);
		await expect(page.getByText("Save & Continue")).toHaveCount(0);
		await expect(page.getByText("Passed", { exact: true })).toHaveCount(0);
		await expect(page.getByText("Failed", { exact: true })).toHaveCount(0);
		await expect(page.getByText("Approved", { exact: true })).toHaveCount(0);

		const footerPos = await page.evaluate(() => {
			const el = document.querySelector(
				'[data-testid="kt-prelim-footer"]',
			) as HTMLElement | null;
			if (!el) return null;
			return window.getComputedStyle(el).position;
		});
		expect(footerPos).toBe("fixed");

		const startAction = page.getByTestId("kt-prelim-row-action").first();
		if ((await startAction.count()) > 0) {
			await startAction.click();
			await expect(page.getByTestId("kt-prelim-drawer")).toBeVisible();
			await expect(page.getByTestId("kt-prelim-drawer-title")).not.toBeEmpty();
			await expect(page.getByTestId("kt-prelim-drawer-save")).toBeDisabled();
			await page.getByTestId("kt-prelim-drawer-cancel").click();
			await expect(page.getByTestId("kt-prelim-drawer")).toBeHidden();
		}
	});

	test("rejects disallowed file type immediately in the drawer", async ({ page }) => {
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

		await page.goto(
			`/tenders/${ref}/sections/preliminary_requirements_and_evidence`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.getByTestId("kt-prelim-root")).toBeVisible({ timeout: 30_000 });

		const taxRow = page
			.getByTestId("kt-prelim-row")
			.filter({ hasText: "Tax compliance certificate" })
			.first();
		test.skip((await taxRow.count()) === 0, "Tax compliance criterion not on this tender");
		await taxRow.getByTestId("kt-prelim-row-action").click();

		await expect(page.getByTestId("kt-prelim-drawer")).toBeVisible();
		const fileInput = page.getByTestId("kt-prelim-file");
		await expect(fileInput).toBeVisible();
		const accept = (await fileInput.getAttribute("accept")) || "";
		expect(accept).toMatch(/\.pdf/i);

		await fileInput.setInputFiles({
			name: "Tender Security.docx",
			mimeType:
				"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
			buffer: Buffer.from("not-a-valid-tax-certificate"),
		});

		await expect(page.getByTestId("kt-prelim-drawer-issue")).toBeVisible();
		await expect(page.getByTestId("kt-prelim-drawer-issue")).toContainText(/not accepted/i);
		await expect(page.getByTestId("kt-prelim-drawer-save")).toBeDisabled();
		await expect(page.getByText("KT_PRELIM_FILE_TYPE")).toHaveCount(0);
		// Selection must not stick as an attached chip after rejection.
		await expect(page.getByTestId("kt-prelim-upload-chip")).toBeHidden();
	});
});
