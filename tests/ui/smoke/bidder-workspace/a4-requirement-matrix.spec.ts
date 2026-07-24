import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * A4 Requirement Matrix — Website Screen D (checklist section detail).
 * Route: /tenders/<publication_ref>/sections/<section_key>
 */

const ROOT = '[data-testid="kt-a0-tenders-root"]';
const CHECKLIST = '[data-testid="kt-a2-checklist-root"]';
const MATRIX = '[data-testid="kt-a4-matrix-root"]';

function extractPublicationRef(url: string): string | null {
	const m = url.match(/\/tenders\/([^/?#]+)/);
	return m?.[1] || null;
}

test.describe("A4 Requirement Matrix portal", () => {
	test("checklist opens matrix section; drawer save updates row status", async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);

		await page.goto("/tenders", { waitUntil: "domcontentloaded" });
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });

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

		// Prefer schema-driven matrix row (portal /sections/ URL), not Desk bridge.
		const matrixLink = page.locator('[data-testid="kt-a2-section-action"][href*="/sections/"]').first();
		test.skip((await matrixLink.count()) === 0, "No requirement_matrix checklist row on this tender");

		const sectionTitleHint = await matrixLink
			.locator("xpath=ancestor::tr")
			.locator("td")
			.first()
			.innerText()
			.catch(() => "");

		await matrixLink.click();
		await page.waitForURL(/\/tenders\/[^/?#]+\/sections\/[^/?#]+/, { timeout: 30_000 });
		expect(page.url()).not.toMatch(/\/desk\/|it-electronic-bidder-workspace/);

		await expect(page.locator(MATRIX)).toBeVisible({ timeout: 30_000 });
		const title = page.getByTestId("kt-a4-title");
		await expect(title).toBeVisible();
		const titleText = (await title.innerText()).trim();
		expect(titleText.length).toBeGreaterThan(0);
		expect(titleText).not.toMatch(/^6\./);
		if (sectionTitleHint) {
			// Title comes from manifest section label (may omit checklist ordinal prefix).
			expect(sectionTitleHint.toLowerCase()).toContain(
				titleText.replace(/^\d+\.\s*/, "").toLowerCase().slice(0, 12)
			);
		}

		await expect(page.getByTestId("kt-a4-group-rail")).toBeVisible();
		await expect(page.getByTestId("kt-a4-group").first()).toBeVisible();
		await expect(page.getByTestId("kt-a4-progress-label")).toContainText("requirements complete");
		await expect(page.getByTestId("kt-a4-back-workspace")).toBeVisible();

		// Sidebar head stays compact — short label + clamped tender title.
		await expect(page.getByTestId("kt-a2-sidebar-title")).toHaveText("Bidder Workspace");
		const sidebarTender = page.getByTestId("kt-a2-sidebar-tender");
		if ((await sidebarTender.count()) > 0) {
			await expect(sidebarTender).toBeVisible();
			const box = await sidebarTender.boundingBox();
			expect(box).toBeTruthy();
			expect((box?.height || 0)).toBeLessThan(56);
		}
		// Group rail stacks title above progress/status (no single-line crush).
		const firstGroup = page.getByTestId("kt-a4-group").first();
		const groupTitleBox = await firstGroup.locator(".kt-a4-group-title").boundingBox();
		const groupMetaBox = await firstGroup.locator(".kt-a4-group-meta").boundingBox();
		expect(groupTitleBox && groupMetaBox).toBeTruthy();
		if (groupTitleBox && groupMetaBox) {
			expect(groupMetaBox.y).toBeGreaterThanOrEqual(groupTitleBox.y + groupTitleBox.height - 2);
		}

		const drawer = page.getByTestId("kt-a4-drawer");
		// Row body click must not open the drawer — only Start / Continue / Review.
		const firstRow = page.getByTestId("kt-a4-requirement-row").first();
		await expect(firstRow).toBeVisible();
		await firstRow.getByTestId("kt-a4-row-title").click();
		await expect(drawer).toBeHidden();

		// Prefer Not Started so partial-save can surface In Progress + Needs Attention.
		const notStartedAction = page
			.locator(
				'[data-testid="kt-a4-requirement-row"][data-status="Not Started"] [data-testid="kt-a4-row-action"]'
			)
			.first();
		const openAction =
			(await notStartedAction.count()) > 0
				? notStartedAction
				: page.getByTestId("kt-a4-row-action").first();
		await expect(openAction).toBeVisible();
		await openAction.click();

		await expect(drawer).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("kt-a4-drawer-title")).not.toBeEmpty({ timeout: 15_000 });
		await expect(page.getByTestId("kt-a4-drawer-description")).toBeVisible({ timeout: 15_000 });
		await expect(drawer.getByText("Description", { exact: true })).toBeVisible();
		// Description appears once — not mirrored as a second identical block under the title.
		await expect(drawer.locator('[data-testid="kt-a4-drawer-statement"]')).toHaveCount(0);
		const descText = (await page.getByTestId("kt-a4-drawer-description").locator("p").innerText()).trim();
		const headerText = (await page.getByTestId("kt-a4-drawer-title").innerText()).trim();
		expect(descText.length).toBeGreaterThan(0);
		expect(headerText).not.toBe(descText);

		const rowTitle = page.locator('[data-testid="kt-a4-requirement-row"].is-selected [data-testid="kt-a4-row-title"]');
		await expect(rowTitle).toBeVisible();
		await expect(
			page.locator('[data-testid="kt-a4-requirement-row"].is-selected .kt-a4-row-desc')
		).toHaveCount(0);

		// When the selected row has a short title, list shows title + muted detail.
		const selectedRow = page.locator('[data-testid="kt-a4-requirement-row"].is-selected');
		if ((await selectedRow.locator('[data-testid="kt-a4-row-detail"]').count()) > 0) {
			const listTitle = (await selectedRow.getByTestId("kt-a4-row-title").innerText()).trim();
			const listDetail = (await selectedRow.getByTestId("kt-a4-row-detail").innerText()).trim();
			expect(listTitle.length).toBeGreaterThan(0);
			expect(listDetail.length).toBeGreaterThan(0);
			expect(listTitle).not.toBe(listDetail);
			expect(headerText).toContain(listTitle);
			expect(descText).not.toContain(listTitle);
		}

		const yesBtn = drawer.locator(".kt-a4-yesno button[data-value='Yes']").first();
		const statement = drawer.locator('textarea[name="compliance_statement"]').first();
		const openedNotStarted = (await notStartedAction.count()) > 0;
		if (openedNotStarted && (await yesBtn.count()) > 0 && (await statement.count()) > 0) {
			// Yes only → In Progress + Needs Attention badge + under-field error.
			await yesBtn.click();
			await page.getByTestId("kt-a4-drawer-save").click();
			await expect(page.getByTestId("kt-a4-drawer-status")).toContainText("In Progress", {
				timeout: 15_000,
			});
			await expect(page.getByTestId("kt-a4-drawer-attention")).toBeVisible();
			await expect(page.getByTestId("kt-a4-drawer-attention")).toContainText("Needs Attention");
			await expect(drawer.getByTestId("kt-a4-field-error-compliance_statement")).toBeVisible();
			await statement.fill("Playwright A4 compliance statement — automated.");
		} else if ((await yesBtn.count()) > 0) {
			await yesBtn.click();
			if ((await statement.count()) > 0) {
				await statement.fill("Playwright A4 compliance statement — automated.");
			}
		} else if ((await statement.count()) > 0) {
			await statement.fill("Playwright A4 compliance statement — automated.");
		}

		const fileInput = drawer.locator('[data-testid="kt-a4-file-input"]').first();
		if ((await fileInput.count()) > 0) {
			await fileInput.setInputFiles([
				{
					name: "evidence-a.pdf",
					mimeType: "application/pdf",
					buffer: Buffer.from("%PDF-1.4 playwright-a"),
				},
				{
					name: "evidence-b.docx",
					mimeType:
						"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
					buffer: Buffer.from("PK playwright-b"),
				},
			]);
			await expect(drawer.getByTestId("kt-a4-file-chip")).toHaveCount(2, { timeout: 5_000 });
			await expect(drawer.getByTestId("kt-a4-file-name").first()).toContainText("evidence-a.pdf");
			await drawer.getByTestId("kt-a4-file-remove").first().click();
			await expect(drawer.getByTestId("kt-a4-file-chip")).toHaveCount(1);
			await expect(drawer.getByTestId("kt-a4-file-name").first()).toContainText("evidence-b.docx");
		}

		await page.getByTestId("kt-a4-drawer-save").click();
		await expect
			.poll(async () => {
				const row = page.locator('[data-testid="kt-a4-requirement-row"].is-selected');
				if ((await row.count()) === 0) return "";
				return (await row.getByTestId("kt-a4-row-status").innerText()).trim();
			}, { timeout: 20_000 })
			.toMatch(/Complete|In Progress|Needs Attention/);

		// After save, drawer refresh should still show remaining attachment chip(s).
		if ((await drawer.getByTestId("kt-a4-file-chip").count()) > 0) {
			await expect(drawer.getByTestId("kt-a4-file-chip").first()).toBeVisible();
			await expect(drawer.getByTestId("kt-a4-file-remove").first()).toBeVisible();
		}

		const body = await page.locator("body").innerText();
		expect(body).not.toMatch(/Tender Management|Tender Configurations|Evaluation and Award/i);
		await expect(page.locator("nav.navbar")).toBeHidden();

		await page.getByTestId("kt-a4-back-workspace").click();
		await page.waitForURL(/\/tenders\/[^/?#]+\/workspace/, { timeout: 20_000 });
		await expect(page.locator(CHECKLIST)).toBeVisible();
	});
});
