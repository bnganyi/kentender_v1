import { expect, type Page } from "@playwright/test";

/**
 * Shared wizard context strip contract (UI-01 + future CFG/WF pages).
 * Visual: 8 cells — Package Ref, Title, Entity, Method, STD Family, STD Document, Status+dot, Issues.
 */
export async function expectConfigurationContextStrip(
	page: Page,
	expected?: {
		packageRef?: string | RegExp;
		title?: string | RegExp;
		entity?: string | RegExp;
		method?: string | RegExp;
		family?: string | RegExp;
		stdDocument?: string | RegExp;
		status?: string | RegExp;
		issues?: string | RegExp;
	}
) {
	const strip = page.getByTestId("kt-cl-config-context-strip");
	await expect(strip).toBeVisible({ timeout: 15_000 });

	await expect(strip.getByTestId("kt-cl-config-context-package_ref")).toContainText(
		/Procurement Package Ref/i
	);
	await expect(strip.getByTestId("kt-cl-config-context-title")).toContainText(/Procurement Title/i);
	await expect(strip.getByTestId("kt-cl-config-context-entity")).toContainText(/Procuring Entity/i);
	await expect(strip.getByTestId("kt-cl-config-context-method")).toContainText(/Procurement Method/i);
	await expect(strip.getByTestId("kt-cl-config-context-family")).toContainText(/STD Family/i);
	await expect(strip.getByTestId("kt-cl-config-context-std_document")).toContainText(
		/Standard Tender Document/i
	);
	await expect(strip.getByTestId("kt-cl-config-context-status")).toContainText(/Configuration Status/i);
	await expect(strip.getByTestId("kt-cl-config-context-issues")).toContainText(/Issues/i);

	const cellCount = await strip.locator(".kt-cl-config-context-cell").count();
	expect(cellCount).toBe(8);

	const statusDot = strip.locator(".kt-cl-config-status-dot");
	await expect(statusDot).toBeVisible();

	if (expected?.packageRef) {
		await expect(strip.getByTestId("kt-cl-config-context-package_ref")).toContainText(
			expected.packageRef
		);
	}
	if (expected?.title) {
		await expect(strip.getByTestId("kt-cl-config-context-title")).toContainText(expected.title);
	}
	if (expected?.entity) {
		await expect(strip.getByTestId("kt-cl-config-context-entity")).toContainText(expected.entity);
	}
	if (expected?.method) {
		await expect(strip.getByTestId("kt-cl-config-context-method")).toContainText(expected.method);
	}
	if (expected?.family) {
		await expect(strip.getByTestId("kt-cl-config-context-family")).toContainText(expected.family);
	}
	if (expected?.stdDocument) {
		await expect(strip.getByTestId("kt-cl-config-context-std_document")).toContainText(
			expected.stdDocument
		);
	}
	if (expected?.status) {
		await expect(strip.getByTestId("kt-cl-config-context-status")).toContainText(expected.status);
	}
	if (expected?.issues) {
		await expect(strip.getByTestId("kt-cl-config-context-issues")).toContainText(expected.issues);
	}

	const issuesValue = strip.getByTestId("kt-cl-config-context-issues").locator(".kt-cl-config-issues-value");
	const issuesText = await issuesValue.innerText();
	if (/Blockers/i.test(issuesText)) {
		await expect(issuesValue).toHaveClass(/is-alert/);
		const issuesColor = await issuesValue.evaluate((el) => getComputedStyle(el).color);
		expect(issuesColor).toMatch(/rgb\(186,\s*26,\s*26\)/);
	}
}
